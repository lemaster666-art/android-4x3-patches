#!/usr/bin/env python3
"""Inspection, audited profiles and local Mac delivery for the 4:3 time skill."""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from android4x3.errors import PatchError
from android4x3.registry import Registry
from android4x3 import workshop as w
from android4x3.delivery import mac_source_command


def reference_tools():
    """Reuse the validated installer without modifying or invoking its Marvel build."""
    path = REPO / "games/marvel-cosmic-invasion/local_build.py"
    spec = importlib.util.spec_from_file_location("workshop_pinned_toolchain", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def install_dependencies(profile: dict, cache: Path) -> str:
    """Optional per-game Python environment and audited native-tool setup hook."""
    deps = profile.get("dependencies", {})
    requirements = deps.get("python_requirements", [])
    python = sys.executable
    if requirements:
        required_hashes = {name: profile["source_checksums"][name] for name in requirements}
        key = hashlib.sha256((sys.version + platform.machine() + json.dumps(required_hashes, sort_keys=True)).encode()).hexdigest()[:20]
        env = cache / "python-envs" / key
        python = str(env / "bin/python")
        ready = env / ".requirements-ready"
        if not ready.exists():
            subprocess.run([sys.executable, "-m", "venv", str(env)], check=True)
            for name in requirements:
                subprocess.run([python, "-m", "pip", "install", "--disable-pip-version-check", "-r", str(w.source_path(REPO, name))], check=True)
            subprocess.run([python, "-m", "pip", "check"], check=True)
            ready.write_text("verified installation\n")
    if deps.get("setup_script"):
        script = w.source_path(REPO, deps["setup_script"])
        result = subprocess.run([python, str(script), "--cache", str(cache), "--system", platform.system(), "--arch", platform.machine()], check=True, capture_output=True, text=True)
        updates = json.loads(result.stdout)
        if not isinstance(updates, dict) or any(not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", k) or not isinstance(v, str) for k, v in updates.items()):
            raise PatchError("Game setup hook must return a JSON object of non-secret tool environment paths")
        # Environment is confined to this process, not the user's shell configuration.
        os.environ.update(updates)
    return python


def mac_command(game: str, ref: str, repository: str) -> str:
    if not w.GAME_ID.fullmatch(game) or not re.fullmatch(r"(?:main|[0-9a-f]{40})", ref):
        raise PatchError("Command needs a safe game ID and main or a full published commit SHA")
    return mac_source_command("tools/workshop-build.sh", ref, repository, (game,))


def audit_staged() -> dict:
    """Check the exact Git index blobs, including ignored files force-added by mistake."""
    result = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z"], cwd=REPO, capture_output=True, check=True)
    names = [n.decode() for n in result.stdout.split(b"\0") if n]
    rejected = []
    for name in names:
        path = Path(name)
        data = subprocess.run(["git", "show", ":" + name], cwd=REPO, capture_output=True, check=True).stdout
        if (path.suffix.lower() in w.PROHIBITED | {".zip", ".mp4", ".unity3d", ".bundle"}
                or path.name in {"signing-password.txt", "signing-key-password.txt", ".env"}
                or data.startswith((b"dex\n", b"\x7fELF", b"MZ", b"XALZ", b"PK\x03\x04"))
                or re.search(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", data)
                or re.search(rb"\bgh[pousr]_[A-Za-z0-9]{30,}\b", data)):
            rejected.append(name)
    if rejected:
        raise PatchError("Refusing prohibited files/secrets in Git index: " + ", ".join(rejected))
    return {"staged_files_checked": len(names), "prohibited_artifact_scan": "passed",
            "note": "Also review source/provenance manually; a scanner cannot identify every proprietary fragment or secret"}


def local_build(args) -> None:
    profile = w.load_profile(REPO, args.game)
    system, machine = platform.system(), platform.machine()
    if (system, machine) not in {("Darwin", "arm64"), ("Darwin", "x86_64"), ("Linux", "x86_64")}:
        raise PatchError("Supported local hosts: Intel/Apple Silicon macOS or x86_64 Linux")
    config = Registry(REPO / "games").by_id[args.game]
    original = args.apk
    if original is None:
        if system != "Darwin":
            raise PatchError("Supply --apk on non-macOS hosts")
        script = 'on run argv\nreturn POSIX path of (choose file with prompt (item 1 of argv))\nend run'
        result = subprocess.run(["/usr/bin/osascript", "-e", script, f"Choose your ORIGINAL {config.display_name} APK"], check=True, capture_output=True, text=True)
        original = Path(result.stdout.strip())
    original = w.outside(REPO, original)
    if not original.is_file() or w.sha(original) not in profile["original_apk_sha256"]:
        raise PatchError("Selected APK SHA-256 does not match an audited original; nothing was patched")
    cache = w.outside(REPO, Path(os.environ.get("APK4X3_CACHE", str(Path.home() / "Library/Caches/android-4x3-workshop")))).resolve()
    output = args.output or Path.home() / "Downloads" / (args.game + "-4x3-" + datetime.now().strftime("%Y%m%d-%H%M%S-%f")) / config.output_name
    output = w.outside(REPO, output)
    if output.exists() or output == original:
        raise PatchError("Choose a separate, new output file")
    cache.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.environ.update(reference_tools().ensure_tools(cache, system, machine))
    # Reuse the same signing folder as the successful local Marvel launcher.
    if "XDG_DATA_HOME" not in os.environ:
        os.environ["XDG_DATA_HOME"] = str(Path.home() / ("Library/Application Support" if system == "Darwin" else ".local/share"))
    w.outside(REPO, Path(os.environ["XDG_DATA_HOME"]))
    python = install_dependencies(profile, cache)
    # Build in the per-game dependency environment if one was needed.
    subprocess.run([python, str(Path(__file__).resolve()), "build", args.game,
                    "--apk", str(original), "--output", str(output)], check=True)
    print(f"\nSUCCESS — verified local APK:\n{output}", flush=True)
    print("The original is unchanged. A different signing key prevents updating the distributor's APK.")
    print("Device gameplay remains unverified by this build; see the game documentation for reported tests.")
    if system == "Darwin":
        subprocess.run(["/usr/bin/open", "-R", str(output)], check=False)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser("inspect", help="Read-only private APK preflight; no game execution")
    inspect.add_argument("apk", type=Path)
    inspect.add_argument("--out", type=Path)
    inspect.add_argument("--expected-sha256", help="Owner-supplied original hash; reject mismatch before inspection")
    profile = commands.add_parser("profile", help="Create a source-pinned profile after game targets are audited")
    profile.add_argument("game")
    profile.add_argument("--apk", type=Path, required=True)
    profile.add_argument("--allow-change", action="append", default=[])
    profile.add_argument("--allow-addition", action="append", default=[])
    profile.add_argument("--requirements", action="append", default=[])
    profile.add_argument("--setup-script")
    profile.add_argument("--out", type=Path)
    for name in ("local-build", "build"):
        build = commands.add_parser(name)
        build.add_argument("game")
        build.add_argument("--apk", type=Path, required=name == "build")
        build.add_argument("--output", type=Path, required=name == "build")
    command = commands.add_parser("command", help="Print one pasteable macOS command for a published profile")
    command.add_argument("game")
    command.add_argument("--ref", default="main")
    command.add_argument("--repository", default="lemaster666-art/android-4x3-patches")
    commands.add_parser("audit", help="Reject staged APKs, native/managed binaries, keys and common secrets")
    args = parser.parse_args()
    if args.command == "inspect":
        if args.expected_sha256:
            if not w.SHA.fullmatch(args.expected_sha256.lower()) or w.sha(args.apk) != args.expected_sha256.lower():
                raise PatchError("Owner-supplied APK SHA-256 mismatch; do not treat this download as the original")
        result = w.inspect(args.apk, repo=REPO)
        text = json.dumps(result, indent=2)
        if args.out:
            dest = w.outside(REPO, args.out)
            dest.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            with dest.open("x") as stream:
                stream.write(text + "\n")
            dest.chmod(0o600)
        print(text)
    elif args.command == "profile":
        result = w.make_profile(REPO, args.game, args.apk, args.allow_change, args.allow_addition, args.requirements, args.setup_script)
        dest = args.out or REPO / "games" / args.game / "workshop.json"
        dest = dest.resolve()
        if dest.suffix != ".json":
            raise PatchError("Profile output must be JSON code metadata")
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("x") as stream:
            json.dump(result, stream, indent=2)
            stream.write("\n")
        # Validate before allowing this profile to be used for a build.
        print(f"Created {dest}; review allowed entries, dependency setup and evidence before publication.")
    elif args.command == "command":
        w.load_profile(REPO, args.game)
        print(mac_command(args.game, args.ref, args.repository))
    elif args.command == "audit":
        print(json.dumps(audit_staged(), indent=2))
    elif args.command == "local-build":
        local_build(args)
    else:
        result = w.build(REPO, args.game, args.apk, args.output)
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (PatchError, OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        raise SystemExit(f"Workshop stopped: {exc}")
