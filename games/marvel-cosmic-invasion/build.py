"""Build this exact experimental APK without touching branding/protection code."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import os
import shutil
import sys
import tempfile
import zipfile

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from android4x3.apk import _is_v1_signature, _stdlib_core_repack, inspect_apk, verify_zip
from android4x3.signing import align_apk, sign_apk, verify_alignment
from android4x3.errors import PatchError


def file_hash(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def verify_members(original: Path, patched: Path, dex: bytes) -> int:
    """Every original member must survive byte-identically except classes2.dex."""
    with zipfile.ZipFile(original) as source, zipfile.ZipFile(patched) as output:
        original_names = {n for n in source.namelist() if not _is_v1_signature(n)}
        final_names = {n for n in output.namelist() if not _is_v1_signature(n)}
        if original_names != final_names:
            raise PatchError("Marvel: unexpected added/removed archive members")
        unchanged = 0
        for name in original_names:
            with source.open(name) as a, output.open(name) as b:
                left = hashlib.file_digest(a, "sha256").hexdigest()
                right = hashlib.file_digest(b, "sha256").hexdigest()
            if name == "classes2.dex":
                if right != hashlib.sha256(dex).hexdigest():
                    raise PatchError("Marvel: rebuilt display shim mismatch")
            elif left != right:
                raise PatchError(f"Marvel: unrelated member changed: {name}")
            else:
                unchanged += 1
        return unchanged


def build(original: Path, output: Path) -> dict:
    original, output = original.resolve(), output.resolve()
    if output.is_relative_to(REPO) or output == original:
        raise PatchError("Keep the original and output separate; output must be outside this repository")
    if output.exists():
        raise PatchError("Refusing to overwrite an existing output")
    spec = importlib.util.spec_from_file_location("marvel_display", Path(__file__).with_name("patch_impl.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if file_hash(original) != module.ORIGINAL_APK_SHA256:
        raise PatchError("Original APK SHA-256 mismatch; stopping before modification")
    verify_zip(original, full=True, allow_signatures=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="marvel-build-", dir=output.parent) as temp:
        work = Path(temp)
        with zipfile.ZipFile(original) as archive:
            extracted = {}
            for name in module.REQUIRED_ENTRIES:
                path = work / name
                path.write_bytes(archive.read(name))
                extracted[name] = path
        replacements = module.apply(extracted, work / "replacement")
        dex = replacements[module.DEX].read_bytes()
        unsigned, aligned, signed = [work / name for name in ("unsigned.apk", "aligned.apk", "signed.apk")]
        # Deliberately bypass optional branding/protection transformations.
        _stdlib_core_repack(original, unsigned, replacements)
        align_apk(unsigned, aligned)
        sign_apk(aligned, signed)
        verify_alignment(signed)
        verify_zip(signed, full=True, allow_signatures=True)
        if inspect_apk(original) != inspect_apk(signed):
            raise PatchError("Marvel: manifest identity changed")
        unchanged = verify_members(original, signed, dex)
        if file_hash(original) != module.ORIGINAL_APK_SHA256:
            raise PatchError("Original changed during build")
        # The completed output appears only after all integrity checks pass.
        shutil.copyfile(signed, output)
        os.chmod(output, 0o600)
    report = {"output": str(output), "sha256": file_hash(output), "bytes": output.stat().st_size,
              "original_unchanged": True, "unchanged_members": unchanged,
              "changed_members": [module.DEX], "experimental": True,
              "runtime_tested": False, "can_update_original_signature": False}
    output.with_suffix(".json").write_text(json.dumps(report, indent=2) + "\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(build(args.original, args.output), indent=2))
    except (PatchError, OSError, ValueError) as exc:
        parser.exit(2, f"error: {exc}\n")
