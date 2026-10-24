"""Compositor-only experimental stretch for the audited JayElDragon display shim.

No game/native binaries are bundled. Applying requires Java and smali/baksmali
2.5.2 (SMALI_CLASSPATH); inspection of an original/patched APK does not.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile
import zlib

from android4x3.errors import PatchError
from android4x3.manifest import parse_manifest

DIRECTORY = Path(__file__).resolve().parent
MANIFEST = "AndroidManifest.xml"
DEX = "classes2.dex"
REQUIRED_ENTRIES = (MANIFEST, DEX)
# The distributor's native protection/bootstrap has not been runtime-audited.
# Optional branding transformations must not touch it during this experiment.
PRESERVE_UNRELATED_ENTRIES = True
PACKAGE = "com.jayeldragon.marvelcosmic.preview"
VERSION = "1.0-jayeldragon-display"
ORIGINAL_APK_SHA256 = "d0c9587575f5bba17a5ac2f5ea3e56700b362f658aaaff84ae11c9b67eae18c9"
ORIGINAL_DEX_SHA256 = "d2b2bb961b0f7723e9027fd5f82d74694ec25d12dcca6de2a075aece2da6dd9f"
PATCHED_DEX_SHA256 = "0accefb0c85def38839d3e3015d130967a21b7545869f6cefcd7efc23bcc2fe1"
DISPLAY_CLASS = "com/jayeldragon/marvelfix/DisplayFix.smali"
DISPLAY = "Lcom/jayeldragon/marvelfix/DisplayFix;"
WATCHER = "Landroid4x3/marvel/StretchWatcher;"
FIT = ".method private static fit(Landroid/app/Activity;)V"
ORIGINAL_FIT = ".method private static fit16x9(Landroid/app/Activity;)V"
GLOBAL_LISTENER = (
    "    invoke-virtual {v0, v2}, Landroid/view/ViewTreeObserver;"
    "->addOnGlobalLayoutListener(Landroid/view/ViewTreeObserver$OnGlobalLayoutListener;)V"
)
WRAPPER = f"""{FIT}
    .locals 0
    invoke-static {{p0}}, {DISPLAY}->fit16x9(Landroid/app/Activity;)V
    invoke-static {{p0}}, {DISPLAY}->applyStretch4x3(Landroid/app/Activity;)V
    return-void
.end method
"""
WATCH_REGISTRATION = f"""
    new-instance v2, {WATCHER}
    invoke-direct {{v2, p0}}, {WATCHER}-><init>(Landroid/app/Activity;)V
    invoke-virtual {{v0, v2}}, Landroid/view/ViewTreeObserver;->addOnPreDrawListener(Landroid/view/ViewTreeObserver$OnPreDrawListener;)V
"""


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def check_dex(data: bytes) -> None:
    if len(data) < 112 or data[:8] != b"dex\n038\0":
        raise PatchError("Marvel: expected standard DEX 038")
    if struct.unpack_from("<I", data, 32)[0] != len(data):
        raise PatchError("Marvel: invalid DEX length")
    if data[12:32] != hashlib.sha1(data[32:]).digest():
        raise PatchError("Marvel: DEX SHA-1 mismatch")
    if struct.unpack_from("<I", data, 8)[0] != zlib.adler32(data[12:]) & 0xFFFFFFFF:
        raise PatchError("Marvel: DEX Adler32 mismatch")


def dex_state(data: bytes) -> str:
    check_dex(data)
    checksum = digest(data)
    if checksum == ORIGINAL_DEX_SHA256:
        return "original"
    if checksum == PATCHED_DEX_SHA256:
        return "patched"
    raise PatchError("Marvel: unknown display-shim revision or unrelated DEX modification")


def probe(extracted: dict[str, Path]) -> dict:
    try:
        identity = parse_manifest(extracted[MANIFEST].read_bytes())
        if (identity.package, identity.version_name, identity.version_code) != (PACKAGE, VERSION, 2):
            raise PatchError("Marvel: expected preview package, display version, version code 2")
        state = dex_state(extracted[DEX].read_bytes())
        return {"state": state, "targets": [
            {"name": "audited display-shim DEX", "state": state},
            {"name": "16:9 layout with centred compositor stretch and pre-draw reapply", "state": state},
        ]}
    except (KeyError, OSError, ValueError, PatchError) as exc:
        return {"state": "unsupported", "detail": str(exc), "targets": []}


def smali_command(main: str, *args: str) -> None:
    java = shutil.which("java")
    classpath = os.environ.get("SMALI_CLASSPATH", "/workspace/.tools/smali-2.5.2/*")
    if not java:
        raise PatchError("Marvel: Java and smali/baksmali 2.5.2 are required to apply")
    result = subprocess.run([java, "-cp", classpath, main, *args],
                            capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode:
        raise PatchError("Marvel: smali tool failed: " + result.stdout[-2000:] + result.stderr[-2000:])


def method_blocks(source: str) -> dict[str, str]:
    blocks = re.findall(r"(?m)^\.method [^\n]+\n.*?^\.end method", source, re.S)
    result = {block.splitlines()[0]: block for block in blocks}
    if len(result) != len(blocks):
        raise PatchError("Marvel: duplicate smali method definitions")
    return result


def transform_smali(source: str) -> str:
    """Preserve the original fit body and all unrelated methods verbatim."""
    if source.count(FIT + "\n") != 1 or "fit16x9(" in source or "applyStretch4x3(" in source:
        raise PatchError("Marvel: missing, duplicate or previously changed fit method")
    methods = method_blocks(source)
    install = methods.get(".method public static install(Landroid/app/Activity;)V", "")
    if install.count(GLOBAL_LISTENER) != 1 or ".registers 6" not in install:
        raise PatchError("Marvel: changed install listener/register context")
    modified_install = install.replace(GLOBAL_LISTENER, GLOBAL_LISTENER + WATCH_REGISTRATION)
    result = source.replace(install, modified_install).replace(FIT + "\n", ORIGINAL_FIT + "\n")
    return result.rstrip() + "\n\n" + WRAPPER + "\n" + (DIRECTORY / "transform.smali").read_text()


def patch_dex(data: bytes) -> bytes:
    state = dex_state(data)
    if state == "patched":
        return data
    with tempfile.TemporaryDirectory(prefix="marvel-display-") as temp:
        root = Path(temp)
        original, output, tree = root / "original.dex", root / "patched.dex", root / "smali"
        original.write_bytes(data)
        smali_command("org.jf.baksmali.Main", "disassemble", "--api", "26", str(original), "-o", str(tree))
        display = tree / DISPLAY_CLASS
        display.write_text(transform_smali(display.read_text()), encoding="utf-8")
        watcher = tree / "android4x3/marvel/StretchWatcher.smali"
        watcher.parent.mkdir(parents=True, exist_ok=True)
        watcher.write_bytes((DIRECTORY / "StretchWatcher.smali").read_bytes())
        smali_command("org.jf.smali.Main", "assemble", "--api", "26", "--jobs", "1", str(tree), "-o", str(output))
        patched = output.read_bytes()
        check_dex(patched)
        if dex_state(patched) != "patched":
            raise PatchError("Marvel: unexpected assembled DEX; use audited smali 2.5.2")
        return patched


def apply(extracted: dict[str, Path], output_dir: Path) -> dict[str, Path]:
    initial = probe(extracted)
    if initial["state"] == "unsupported":
        raise PatchError(initial["detail"])
    if initial["state"] == "patched":
        return {}
    output = output_dir / DEX
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(patch_dex(extracted[DEX].read_bytes()))
    return {DEX: output}
