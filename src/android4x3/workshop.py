"""Shared, conservative inspection and local-build contracts for 4:3 time."""
from __future__ import annotations

from dataclasses import asdict
import fnmatch
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import struct
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import zipfile

from .apk import (_is_v1_signature, _stdlib_core_repack, extract_entries,
                  inspect_apk, resolve_entries, verify_zip)
from .errors import PatchError
from .manifest import _chunks, _string_pool
from .registry import Registry
from . import signing

TARGET = {"device": "Retroid Pocket Classic", "android_api": 34,
          "display": [1240, 1080], "picture": [1240, 930],
          "borders_top_bottom": [75, 75], "mode": "stretch", "crop": False}
SHA = re.compile(r"^[0-9a-f]{64}$")
GAME_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PROHIBITED = {".apk", ".apks", ".apkm", ".xapk", ".aab", ".dex", ".dll", ".so",
              ".dylib", ".blob", ".obb", ".iso", ".p12", ".pfx", ".jks", ".keystore", ".key"}
CODE_SUFFIXES = {".py", ".json", ".smali", ".c", ".h", ".S", ".cs", ".gml", ".hex", ".ld", ".sh"}


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def safe_name(name: str) -> bool:
    p = PurePosixPath(name)
    return bool(name) and p.as_posix() == name.rstrip("/") and not p.is_absolute() and ".." not in p.parts and "\\" not in name and ":" not in name


def source_path(repo: Path, name: str) -> Path:
    if not isinstance(name, str) or not safe_name(name):
        raise PatchError("Invalid repository-relative source path")
    path = (repo / name).resolve()
    if not path.is_relative_to(repo.resolve()) or not path.is_file():
        raise PatchError(f"Source file missing or escapes the checkout: {name}")
    return path


def outside(repo: Path, path: Path) -> Path:
    path = path.expanduser().resolve()
    if path.is_relative_to(repo.resolve()):
        raise PatchError("Private APKs, reports, caches and keys must stay outside the checkout")
    return path


def manifest_attributes(data: bytes) -> list[tuple[str, dict]]:
    """Read SDK/permission metadata without executing the APK or needing aapt."""
    if data.lstrip().startswith(b"<"):
        root = ET.fromstring(data)
        return [(e.tag.rsplit("}", 1)[-1], {k.rsplit("}", 1)[-1]: v for k, v in e.attrib.items()}) for e in root.iter()]
    chunks = list(_chunks(data, 8, struct.unpack_from("<I", data, 4)[0]))
    pools = [c for c in chunks if c[0] == 1]
    if len(pools) != 1:
        raise PatchError("Manifest string pool is ambiguous")
    strings = _string_pool(data, pools[0][1], pools[0][2])
    result = []
    for kind, offset, size in chunks:
        if kind != 0x102:
            continue
        if size < 36:
            raise PatchError("Truncated manifest element")
        name = struct.unpack_from("<I", data, offset + 20)[0]
        start, stride, count = struct.unpack_from("<HHH", data, offset + 24)
        if name >= len(strings) or stride < 20 or offset + 16 + start + stride * count > offset + size:
            raise PatchError("Malformed manifest attributes")
        attrs = {}
        for i in range(count):
            _, key, raw, _, _, typ, value = struct.unpack_from("<IIIHBBI", data, offset + 16 + start + i * stride)
            if key >= len(strings):
                raise PatchError("Invalid manifest attribute name")
            index = raw if raw != 0xFFFFFFFF else value
            attrs[strings[key]] = strings[index] if (raw != 0xFFFFFFFF or typ == 3) and index < len(strings) else value
        result.append((strings[name], attrs))
    return result


def archive_preflight(apk: Path) -> None:
    with zipfile.ZipFile(apk) as packed:
        entries = packed.infolist()
        if len(entries) > 100000 or sum(e.file_size for e in entries) > 16 * 1024**3:
            raise PatchError("Archive exceeds inspection resource limits; review it privately")
        if any(not safe_name(e.filename) for e in entries):
            raise PatchError("Unsafe archive member path")
        if any(e.file_size > 4 * 1024**3 for e in entries):
            raise PatchError("Oversized archive member")
    verify_zip(apk, full=True, allow_signatures=True)


def verify_signature(apk: Path, *, required: bool) -> dict:
    try:
        tool = signing.find_android_tool("apksigner")
    except PatchError:
        if required:
            raise
        return {"state": "unrun", "reason": "Android apksigner not installed"}
    command = [str(tool), "verify", "--verbose", "--print-certs", str(apk)]
    output = signing._run(command)
    return {"state": "passed", "details": output.strip()}


def inspect(apk: Path, *, repo: Path) -> dict:
    apk = outside(repo, apk)
    archive_preflight(apk)
    identity = inspect_apk(apk)
    with zipfile.ZipFile(apk) as packed:
        names = packed.namelist()
        attrs = manifest_attributes(packed.read("AndroidManifest.xml"))
        sdk = next((a for tag, a in attrs if tag == "uses-sdk"), {})
        app = next((a for tag, a in attrs if tag == "application"), {})
        abis = sorted({n.split("/")[1] for n in names if n.startswith("lib/") and n.count("/") >= 2})
        hints = []
        for label, patterns in [("FNA/FNA3D", ["*/libFNA3D.so", "*/FNA.dll"]),
                                ("SDL3", ["*/libSDL3.so"]), ("SDL2", ["*/libSDL2.so"]),
                                ("Unity", ["*/libunity.so", "*/libil2cpp.so", "assets/bin/Data/*"]),
                                ("GameMaker", ["*/libyoyo.so", "*.droid"]),
                                ("Godot", ["*/libgodot*.so", "assets/*.pck"]),
                                ("Unreal", ["*/libUE4.so", "*/libUnreal.so"])]:
            matches = [n for n in names if any(fnmatch.fnmatchcase(n, p) for p in patterns)]
            if matches:
                hints.append({"hint": label, "entries": matches[:12]})
        min_sdk = sdk.get("minSdkVersion")
        try:
            sdk_result = "incompatible" if int(min_sdk) > 34 else "minimum SDK compatible"
        except (ValueError, TypeError):
            sdk_result = "minimum SDK unknown"
        return {"identity": asdict(identity), "bytes": apk.stat().st_size, "sha256": sha(apk),
                "zip_integrity": "passed", "signature": verify_signature(apk, required=False),
                "min_sdk": min_sdk, "target_sdk": sdk.get("targetSdkVersion"), "abis": abis,
                "android_14_sdk_check": sdk_result,
                "abi_check": "arm64-v8a present" if "arm64-v8a" in abis else "needs ABI investigation",
                "permissions": [a.get("name") for tag, a in attrs if tag.startswith("uses-permission")],
                "allow_backup": app.get("allowBackup"), "debuggable": app.get("debuggable"),
                "library_hints": hints, "archive_members": len(names),
                "rendering_backend": "unverified; inspect actual call paths",
                "aspect_behavior": "unverified; static hints do not establish presentation",
                "target": TARGET, "safety": "Integrity/signature checks do not establish publisher authenticity or safety"}


def profile_path(repo: Path, game: str) -> Path:
    if not GAME_ID.fullmatch(game):
        raise PatchError("Invalid game ID")
    per_game = repo / "games" / game / "workshop.json"
    return per_game if per_game.is_file() else repo / "workshop/profiles" / (game + ".json")


def load_profile(repo: Path, game: str) -> dict:
    path = profile_path(repo, game)
    if not path.is_file():
        raise PatchError(f"No audited workshop profile for {game}; investigate and create one first")
    if not path.resolve().is_relative_to(repo.resolve()):
        raise PatchError("Build profile escapes the checkout")
    return validate_profile(repo, game, json.loads(path.read_text()))


def validate_profile(repo: Path, game: str, p: dict) -> dict:
    if not isinstance(p, dict):
        raise PatchError("Build profile must be a JSON object")
    if p.get("schema_version") != 1 or p.get("game_id") != game:
        raise PatchError("Unsupported or mismatched build profile")
    hashes = p.get("original_apk_sha256")
    if not isinstance(hashes, list) or not hashes or any(not isinstance(h, str) or not SHA.fullmatch(h) for h in hashes):
        raise PatchError("Profile needs explicit reference APK SHA-256 values")
    sources = p.get("source_checksums")
    if not isinstance(sources, dict) or not sources:
        raise PatchError("Profile needs patch-source checksums")
    for name in (f"games/{game}/patch_impl.py", f"games/{game}/config.json"):
        if name not in sources:
            raise PatchError(f"Profile must pin {name}")
    for name, expected in sources.items():
        file = source_path(repo, name)
        if file.suffix.lower() in PROHIBITED or not isinstance(expected, str) or not SHA.fullmatch(expected):
            raise PatchError("Profile contains a prohibited source or invalid checksum")
        if sha(file) != expected:
            raise PatchError(f"Audited patch source changed: {name}")
    for key in ("allowed_changes", "allowed_additions"):
        values = p.get(key, [])
        if not isinstance(values, list) or any(not isinstance(n, str) or not safe_name(n) or _is_v1_signature(n) or any(c in n for c in "*?[") for n in values):
            raise PatchError(f"{key} must list exact, safe, non-signature archive names")
    if not p.get("allowed_changes") and not p.get("allowed_additions"):
        raise PatchError("Profile declares no patch targets")
    deps = p.setdefault("dependencies", {})
    if not isinstance(deps, dict) or not isinstance(deps.get("python_requirements", []), list):
        raise PatchError("Malformed dependencies")
    for file in deps.get("python_requirements", []) + ([deps["setup_script"]] if deps.get("setup_script") else []):
        if not isinstance(file, str):
            raise PatchError("Dependency paths must be strings")
        if file not in sources:
            raise PatchError("Dependency files must also be checksum-pinned")
        source_path(repo, file)
    return p


def make_profile(repo: Path, game: str, apk: Path, changes: list[str], additions: list[str], requirements: list[str], setup: str | None) -> dict:
    if not GAME_ID.fullmatch(game):
        raise PatchError("Invalid game ID")
    apk = outside(repo, apk)
    archive_preflight(apk)
    registry = Registry(repo / "games")
    config = registry.by_id[game]
    if inspect_apk(apk).package not in config.package_names:
        raise PatchError("Original package does not match the game")
    sources = {}
    for file in sorted(config.directory.rglob("*")):
        if not file.is_file() or "__pycache__" in file.parts or file.name == "workshop.json":
            continue
        if file.suffix.lower() in PROHIBITED:
            raise PatchError("Proprietary files/signing material must not be in the game directory")
        if file.suffix in CODE_SUFFIXES:
            name = file.relative_to(repo).as_posix()
            sources[name] = sha(source_path(repo, name))
    for name in requirements + ([setup] if setup else []):
        sources[name] = sha(source_path(repo, name))
    result = {"schema_version": 1, "game_id": game, "original_apk_sha256": [sha(apk)],
            "source_checksums": sources, "allowed_changes": sorted(set(changes)),
            "allowed_additions": sorted(set(additions)),
            "dependencies": {"python_requirements": requirements, "setup_script": setup},
            "target": TARGET,
            "evidence": "Experimental profile; record actual static, synthetic, reproduction and device evidence in game documentation"}
    return validate_profile(repo, game, result)


def probe(module, extracted: dict[str, Path]) -> dict:
    result = module.probe(extracted)
    if not isinstance(result, dict) or result.get("state") not in {"original", "patched", "unsupported", "ambiguous"}:
        raise PatchError("Game probe returned an invalid state")
    return result


def compare_members(original: Path, final: Path, p: dict) -> dict:
    """Compare actual contents, not ZIP offsets/CRC alone or the module's claims."""
    with zipfile.ZipFile(original) as a, zipfile.ZipFile(final) as b:
        left = {n for n in a.namelist() if not _is_v1_signature(n)}
        right = {n for n in b.namelist() if not _is_v1_signature(n)}
        additions, removed = right - left, left - right
        if removed or not additions.issubset(p.get("allowed_additions", [])):
            raise PatchError("Unexpected added or removed content members")
        changed, unchanged = [], 0
        for name in sorted(left):
            with a.open(name) as s, b.open(name) as t:
                same = hashlib.file_digest(s, "sha256").digest() == hashlib.file_digest(t, "sha256").digest()
            if same:
                unchanged += 1
            elif name not in p["allowed_changes"]:
                raise PatchError(f"Unrelated APK content changed: {name}")
            else:
                changed.append(name)
        return {"changed_members": changed, "added_members": sorted(additions), "unchanged_members": unchanged}


def build(repo: Path, game: str, original: Path, output: Path) -> dict:
    repo, original, output = repo.resolve(), outside(repo, original), outside(repo, output)
    if original == output or output.exists() or output.with_suffix(".json").exists():
        raise PatchError("Refusing to overwrite input, output or report")
    p = load_profile(repo, game)
    before = sha(original)
    if before not in p["original_apk_sha256"]:
        raise PatchError("Original APK SHA-256 mismatch; nothing was patched")
    archive_preflight(original)
    original_signature = verify_signature(original, required=True)
    outside(repo, signing._state_dir())
    identity = inspect_apk(original)
    registry = Registry(repo / "games")
    config = registry.by_id.get(game)
    if config is None or identity.package not in config.package_names:
        raise PatchError("Original package does not match the selected game")
    module = registry.module(config)
    if getattr(module, "REQUIRED_ENTRIES", None) is None:
        raise PatchError("Missing game entry contract")
    selected = resolve_entries(original, config.required_entries, config.preferred_entries)
    output.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with tempfile.TemporaryDirectory(prefix="four-three-", dir=output.parent) as directory:
        work = Path(directory)
        extracted = extract_entries(original, selected, work / "original")
        initial = probe(module, extracted)
        if initial["state"] == "unsupported" and config.entry_globs:
            more = resolve_entries(original, config.required_entries, config.entry_globs)
            extracted.update(extract_entries(original, [n for n in more if n not in extracted], work / "original"))
            initial = probe(module, extracted)
        if initial["state"] != "original":
            raise PatchError(f"Expected uniquely recognized original targets, got {initial['state']}: {initial.get('detail', '')}")
        replacements = module.apply(extracted, work / "patched")
        if not isinstance(replacements, dict) or not replacements:
            raise PatchError("Patch returned no replacement files")
        with zipfile.ZipFile(original) as packed:
            existing = set(packed.namelist())
        allowed = set(p["allowed_changes"]) | set(p.get("allowed_additions", []))
        for name, file in replacements.items():
            if name not in allowed or not safe_name(name) or not Path(file).is_file():
                raise PatchError(f"Patch attempted an undeclared or invalid change: {name}")
            if name not in existing and name not in p.get("allowed_additions", []):
                raise PatchError("New archive entries require explicit approval in the profile")
        unsigned, aligned, signed = [work / n for n in ("unsigned.apk", "aligned.apk", "signed.apk")]
        _stdlib_core_repack(original, unsigned, {n: Path(f) for n, f in replacements.items() if n in existing})
        added = {n: Path(f) for n, f in replacements.items() if n not in existing}
        if added:
            with zipfile.ZipFile(unsigned, "a", allowZip64=False) as packed:
                for name, file in sorted(added.items()):
                    packed.writestr(zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0)), file.read_bytes())
        signing.align_apk(unsigned, aligned)
        signing.sign_apk(aligned, signed)
        signing.verify_alignment(signed)
        verify_zip(signed, full=True, allow_signatures=True)
        final_signature = verify_signature(signed, required=True)
        if inspect_apk(signed) != identity:
            raise PatchError("Package identity/version changed")
        changes = compare_members(original, signed, p)
        final_entries = sorted(set(extracted) | set(replacements))
        final = extract_entries(signed, final_entries, work / "verify")
        if probe(module, final)["state"] != "patched":
            raise PatchError("Post-patch target verification failed")
        if sha(original) != before:
            raise PatchError("The original APK changed during the build")
        # Recheck the pinned source after game/dependency code has run.
        load_profile(repo, game)
        report = {"game_id": game, "package": identity.package, "original_sha256": before,
                  "original_unchanged": True, "sha256": sha(signed), "bytes": signed.stat().st_size,
                  "signature_verified": True, "alignment_verified": True, "post_state": "patched",
                  "original_signature": original_signature, "output_signature": final_signature,
                  "target": p.get("target", TARGET), "device_tested_this_run": False,
                  "repository_status": config.status, "profile_evidence": p.get("evidence", "Not recorded"),
                  **changes}
        # Exclusive creation avoids replacing a file that appeared during a long build.
        descriptor = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(descriptor, "wb") as dest, signed.open("rb") as source:
                shutil.copyfileobj(source, dest, 1024 * 1024)
            if sha(output) != report["sha256"]:
                raise PatchError("Final local copy checksum mismatch")
            report_fd = os.open(output.with_suffix(".json"), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(report_fd, "w") as stream:
                stream.write(json.dumps(report, indent=2) + "\n")
        except Exception:
            output.unlink(missing_ok=True)
            raise
        return report
