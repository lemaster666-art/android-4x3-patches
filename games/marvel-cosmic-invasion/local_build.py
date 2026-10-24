"""Private, checksum-pinned tool setup for the existing Marvel APK builder."""
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
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from urllib.parse import urlsplit
import zipfile

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ORIGINAL_SHA = "d0c9587575f5bba17a5ac2f5ea3e56700b362f658aaaff84ae11c9b67eae18c9"
# These existing patch files are deliberately not edited by this launcher.
PATCH_FILES = {
    "patch_impl.py": "2720501889e260fc2b165a61439407919ea19d6799d86cb410258c30716e2895",
    "transform.smali": "8386f60dcc0d7c2fcf9bd55a95be2edc26c4a4575bd6f98fd802b140b18e1202",
    "StretchWatcher.smali": "ba73be3b3605fb06392591746b20b6462a386585c23b1e0b480d73fa7f28e3bf",
    "build.py": "bf647a2370a9a1cbdc8d66fa38d5214ee7c5d311328a0eb53a8874640ca2d7c8",
}
JARS = [
    ("org.smali", "smali", "2.5.2", "136c5c4653d6531bd7b6f10f35f8691cb96432e727d30b4d5579826ee01e9419"),
    ("org.smali", "baksmali", "2.5.2", "1ed236266d7dc4907aade0b19a34f77efac25342b63c8ace52e579039941b389"),
    ("org.smali", "dexlib2", "2.5.2", "5a5c8982d8bd7d6e3bb1a0713049e3c78b719ec32b20f6b619885cec30a0dd61"),
    ("org.smali", "util", "2.5.2", "4f580a9cff3ebb83cb3fd20bec88e37e4f183796ca652732992611620282daea"),
    ("org.antlr", "antlr", "3.5.2", "5ac36c2acfb0a0f3d37dafe20b5b570f2643e2d000c648d44503c2738be643df"),
    ("org.antlr", "antlr-runtime", "3.5.2", "ce3fc8ecb10f39e9a3cddcbb2ce350d272d9cd3d0b1e18e6fe73c3b9389c8734"),
    ("org.antlr", "stringtemplate", "3.2.1", "f66ce72e965e5301cb0f020e54d2ba6ad76feb91b3cbfc30dbbf00c06a6df6d7"),
    ("com.beust", "jcommander", "1.64", "156be736199c990321d9ff77090b199629cfc9865e2d6c13f7cd291bb1641817"),
    ("com.google.guava", "guava", "27.1-android", "686404f2d1d4d221911f96bd627ff60dac2226a5dfa6fb8ba517073eb97ec0ef"),
    ("com.google.code.findbugs", "jsr305", "3.0.2", "766ad2a0783f2687962c8ad74ceecc38a28b9f72a2d085ee438b7813e928d0c7"),
]
SDK = {
    "Darwin": ("macosx", "04e7f3a72044de4926fa038fa0e251a37bba1e1c3fb8beab6f8401bfd9eb4bf3"),
    "Linux": ("linux", "5d9ac77fb6ff43d9da518a337b4fcf8f9097113df531d99ccefe80ef7ce8250b"),
}
JDK = {
    ("Darwin", "arm64"): ("aarch64_mac", "bf036b35b071bfb2f54f2c0af8ee8d88afa95ee6eb3dce02c0f94cfc2524d04a"),
    ("Darwin", "x86_64"): ("x64_mac", "9aa1d1c17ae5467a022679e7e0af5c00797d94ac462ed1a46f4db07a8a34a6dd"),
    ("Linux", "x86_64"): ("x64_linux", "d7f5d5cf865a2902b70ff549b97586a7d3f234e016f041ab447ea740c7d66d1c"),
}


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


class HTTPSOnly(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if urlsplit(newurl).scheme != "https":
            raise ValueError("Refusing non-HTTPS redirect")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def download(url: str, dest: Path, checksum: str) -> Path:
    if dest.exists():
        if sha(dest) != checksum:
            raise ValueError(f"Cached checksum mismatch: {dest}; remove this file and retry")
        return dest
    if urlsplit(url).scheme != "https":
        raise ValueError("HTTPS downloads only")
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {dest.name}...", flush=True)
    temp = dest.with_suffix(dest.suffix + ".partial")
    try:
        with urllib.request.build_opener(HTTPSOnly()).open(url, timeout=180) as source, temp.open("wb") as target:
            shutil.copyfileobj(source, target, 1024 * 1024)
        if sha(temp) != checksum:
            raise ValueError(f"Download checksum mismatch: {dest.name}")
        temp.replace(dest)
    finally:
        temp.unlink(missing_ok=True)
    return dest


def extract(archive: Path, dest: Path) -> None:
    """Extract verified tool archives, rejecting paths/links escaping the destination."""
    dest.mkdir(parents=True, exist_ok=True)
    if zipfile.is_zipfile(archive):
        with zipfile.ZipFile(archive) as packed:
            for member in packed.infolist():
                target = (dest / member.filename).resolve()
                if not target.is_relative_to(dest.resolve()) or (member.external_attr >> 16) & 0o170000 == 0o120000:
                    raise ValueError("Unsafe tool archive member")
            packed.extractall(dest)
    else:
        with tarfile.open(archive) as packed:
            packed.extractall(dest, filter="data")


def java_usable(java: Path) -> bool:
    if not java.is_file():
        return False
    result = subprocess.run([str(java), "-version"], capture_output=True, text=True)
    version = re.search(r'version "(\d+)', result.stdout + result.stderr)
    return result.returncode == 0 and version is not None and int(version[1]) >= 17


def ensure_java(cache: Path, system: str, machine: str) -> Path:
    if os.environ.get("MARVEL_FORCE_PRIVATE_JAVA") != "1":
        candidates = []
        if os.environ.get("JAVA_HOME"):
            candidates.append(Path(os.environ["JAVA_HOME"]) / "bin/java")
        found = shutil.which("java")
        if system == "Darwin" and found == "/usr/bin/java":
            # Apple's launcher is present even without a JDK; avoid its install prompt.
            home = subprocess.run(["/usr/libexec/java_home", "-v", "17+"], capture_output=True, text=True)
            if home.returncode == 0:
                candidates.append(Path(home.stdout.strip()) / "bin/java")
        elif found:
            candidates.append(Path(found))
        for candidate in candidates:
            if java_usable(candidate):
                return candidate.resolve().parent
    flavor, checksum = JDK[(system, machine)]
    name = f"OpenJDK21U-jdk_{flavor}_hotspot_21.0.13_9.tar.gz"
    archive = download(f"https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.13%2B9/{name}", cache / "downloads" / name, checksum)
    root = cache / f"jdk-21.0.13-{flavor}"
    if not root.exists():
        extract(archive, root)
    candidates = sorted(root.glob("**/bin/java"))
    java = next((p for p in candidates if java_usable(p)), None)
    if java is None:
        raise ValueError("The installed Java runtime could not run on this host")
    return java.parent


def ensure_tools(cache: Path, system: str, machine: str) -> dict[str, str]:
    java_bin = ensure_java(cache, system, machine)
    smali = cache / "smali-2.5.2"
    for group, name, version, checksum in JARS:
        leaf = f"{name}-{version}.jar"
        download(f"https://repo.maven.apache.org/maven2/{group.replace('.', '/')}/{name}/{version}/{leaf}", smali / leaf, checksum)
    flavor, checksum = SDK[system]
    archive = download(f"https://dl.google.com/android/repository/build-tools_r36_{flavor}.zip", cache / "downloads" / f"build-tools-36-{flavor}.zip", checksum)
    sdk = cache / f"android-sdk-{flavor}"
    tools = sdk / "build-tools" / "android-16"
    # Extract on every run from the verified cache to refresh executable tools.
    extract(archive, sdk / "build-tools")
    for name in ("zipalign", "apksigner"):
        (tools / name).chmod(0o700)
    # A deterministic, exact classpath: no unverified extra jars in a wildcard.
    classpath = os.pathsep.join(str(smali / f"{name}-{version}.jar") for _, name, version, _ in JARS)
    return {"PATH": str(java_bin) + os.pathsep + str(tools) + os.pathsep + os.environ.get("PATH", ""),
            "JAVA_HOME": str(java_bin.parent),
            "ANDROID_SDK_ROOT": str(sdk), "SMALI_CLASSPATH": classpath}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original", nargs="?", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    system, machine = platform.system(), platform.machine()
    if (system, machine) not in JDK:
        raise ValueError("Supported hosts: Apple Silicon/Intel macOS and x86_64 Linux")
    original = args.original
    if original is None:
        if system != "Darwin":
            parser.error("Supply the path to your original APK")
        selection = subprocess.run(["/usr/bin/osascript", "-e", 'POSIX path of (choose file with prompt "Choose your ORIGINAL Marvel Cosmic Invasion APK")'], check=True, capture_output=True, text=True)
        original = Path(selection.stdout.strip())
    original = original.expanduser().resolve()
    if not original.is_file() or sha(original) != ORIGINAL_SHA:
        raise ValueError("This is not the supported original APK (SHA-256 mismatch). Nothing was patched.")
    for name, checksum in PATCH_FILES.items():
        if sha(HERE / name) != checksum:
            raise ValueError(f"The audited patch file has changed: {name}; refusing to alter the working patch")
    output = args.output or Path.home() / "Downloads" / ("Marvel-4x3-" + datetime.now().strftime("%Y%m%d-%H%M%S")) / "Marvel-Cosmic-Invasion-stretched-4x3-experimental.apk"
    output = output.expanduser().resolve()
    cache = Path(os.environ.get("MARVEL_BUILD_CACHE", str(Path.home() / "Library/Caches/android-4x3-marvel"))).expanduser().resolve()
    if cache.is_relative_to(REPO) or output.is_relative_to(REPO) or output == original:
        raise ValueError("Keep cache, signing material and APK outputs outside the repository")
    if output.exists():
        raise ValueError("Output already exists; choose a new --output path")
    cache.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.environ.update(ensure_tools(cache, system, machine))
    # Keep a stable, private signing identity across runs and source-code refreshes.
    # XDG_DATA_HOME can be set explicitly to reuse an existing patcher key.
    if "XDG_DATA_HOME" not in os.environ:
        base = Path.home() / ("Library/Application Support" if system == "Darwin" else ".local/share")
        os.environ["XDG_DATA_HOME"] = str(base)
    print("Building the unchanged compositor patch; the original stays untouched...", flush=True)
    spec = importlib.util.spec_from_file_location("marvel_existing_builder", HERE / "build.py")
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    report = builder.build(original, output)
    # sign_apk creates signatures; explicitly verify them as well as content/alignment.
    from android4x3.signing import find_android_tool
    verification = subprocess.run([str(find_android_tool("apksigner")), "verify", "--verbose", "--print-certs", str(output)], check=True, capture_output=True, text=True)
    (output.parent / "signature-verification.txt").write_text(verification.stdout)
    with zipfile.ZipFile(output) as packed:
        dex_sha = hashlib.sha256(packed.read("classes2.dex")).hexdigest()
    if dex_sha != "0accefb0c85def38839d3e3015d130967a21b7545869f6cefcd7efc23bcc2fe1":
        raise ValueError("Final patch-content checksum mismatch")
    report.update({"patched_dex_sha256": dex_sha, "signature_verified": True,
                   "patch_files_unchanged": True, "host": system, "host_architecture": machine})
    output.with_suffix(".json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"\nSUCCESS — your test APK is ready:\n{output}\nSHA-256: {report['sha256']}")
    print("The original package identity is retained. Uninstall the differently signed distributor build before testing.")
    print("Hardware startup and display behavior remain experimental. No installation or upload was attempted.")
    if system == "Darwin":
        subprocess.run(["/usr/bin/open", "-R", str(output)], check=False)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        raise SystemExit(f"Build stopped: {exc}")
