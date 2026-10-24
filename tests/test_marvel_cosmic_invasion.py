"""Proprietary-free tests for the compositor helper and guarded DEX workflow."""
from __future__ import annotations
import hashlib
import importlib.util
from pathlib import Path
import re
import struct
import zlib
import pytest

from android4x3.errors import PatchError
from android4x3.registry import Registry

ROOT = Path(__file__).resolve().parents[1]


def module():
    registry = Registry(ROOT / "games")
    return registry.module(registry.by_id["marvel-cosmic-invasion"])


def dex_fixture():
    data = bytearray(112)
    data[:8] = b"dex\n038\0"
    struct.pack_into("<I", data, 32, len(data))
    data[12:32] = hashlib.sha1(data[32:]).digest()
    struct.pack_into("<I", data, 8, zlib.adler32(data[12:]) & 0xFFFFFFFF)
    return bytes(data)


def test_guards_reject_unknown_corrupt_and_wrong_identity(tmp_path, text_manifest, monkeypatch):
    m = module()
    manifest, dex = tmp_path / "manifest", tmp_path / "shim"
    manifest.write_bytes(text_manifest(m.PACKAGE, m.VERSION, 2))
    good = dex_fixture()
    dex.write_bytes(good)
    files = {m.MANIFEST: manifest, m.DEX: dex}
    assert m.probe(files)["state"] == "unsupported"
    monkeypatch.setattr(m, "ORIGINAL_DEX_SHA256", m.digest(good))
    assert m.probe(files)["state"] == "original"
    manifest.write_bytes(text_manifest(m.PACKAGE, m.VERSION, 3))
    assert m.probe(files)["state"] == "unsupported"
    manifest.write_bytes(text_manifest("other.package", m.VERSION, 2))
    assert m.probe(files)["state"] == "unsupported"
    with pytest.raises(PatchError, match="SHA-1"):
        m.check_dex(good[:-1] + b"x")
    with pytest.raises(PatchError, match="Adler32"):
        m.check_dex(good[:8] + bytes([good[8] ^ 1]) + good[9:])


def test_recognized_patched_state_is_idempotent(monkeypatch, tmp_path, text_manifest):
    m = module()
    data = dex_fixture()
    monkeypatch.setattr(m, "PATCHED_DEX_SHA256", m.digest(data))
    assert m.patch_dex(data) == data
    manifest, dex = tmp_path / "manifest", tmp_path / "shim"
    manifest.write_bytes(text_manifest(m.PACKAGE, m.VERSION, 2))
    dex.write_bytes(data)
    assert m.apply({m.MANIFEST: manifest, m.DEX: dex}, tmp_path / "output") == {}


def synthetic_smali(m):
    # Authored fixture with only the two integration contexts and a sentinel.
    return f""".class public final {m.DISPLAY}
.super Ljava/lang/Object;
{m.FIT}
    .registers 8
    const/4 p0, 0x0
    return-void
.end method
.method public static install(Landroid/app/Activity;)V
    .registers 6
    invoke-virtual {{p0}}, Landroid/app/Activity;->getWindow()Landroid/view/Window;
    move-result-object v1
    const/4 v0, 0x0
    const/4 v2, 0x0
{m.GLOBAL_LISTENER}
    return-void
.end method
.method private static surface(Landroid/view/View;)Landroid/view/SurfaceView;
    .registers 1
    const/4 v0, 0x0
    return-object v0
.end method
.method public static untouched()V
    .registers 0
    return-void
.end method
"""


def test_transform_preserves_original_fit_and_unrelated_methods():
    m = module()
    source = synthetic_smali(m)
    result = m.transform_smali(source)
    before, after = m.method_blocks(source), m.method_blocks(result)
    assert before[m.FIT].replace(m.FIT, m.ORIGINAL_FIT) == after[m.ORIGINAL_FIT]
    sentinel = ".method public static untouched()V"
    assert before[sentinel] == after[sentinel]
    assert after[m.FIT].count("invoke-static") == 2
    assert "addOnPreDrawListener" in after[".method public static install(Landroid/app/Activity;)V"]
    with pytest.raises(PatchError):
        m.transform_smali(result)
    with pytest.raises(PatchError):
        m.transform_smali(source.replace(m.GLOBAL_LISTENER, ""))


class View:
    def __init__(self, width, height, left=0, top=0, parent=None):
        self.width, self.height, self.left, self.top, self.parent = width, height, left, top, parent
        self.values = {}


def execute_helper(surface):
    """Interpret the authored smali, exercising its real branches and arithmetic.

    Android setters are mocked; this checks geometry and guards, not SurfaceFlinger
    or Dalvik verification. Assembly/disassembly is tested separately below.
    """
    m = module()
    lines = []
    for line in (m.DIRECTORY / "transform.smali").read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if line and not line.startswith("."):
            lines.append(line)
    labels = {line: i for i, line in enumerate(lines) if line.startswith(":")}
    registers = {"p0": object()}
    result = None
    pc = 0
    def f32(x):
        return struct.unpack("<f", struct.pack("<f", x))[0]
    while pc < len(lines):
        line = lines[pc]; pc += 1
        if line.startswith(":"): continue
        op, _, args = line.partition(" ")
        args = args.strip()
        if op == "return-void": return
        if op.startswith("invoke-"):
            match = re.match(r"\{([^}]*)\}, (.+)->([^ (]+)\(", args)
            regs, owner, name = match.groups()
            values = [registers[r.strip()] for r in regs.split(",") if r.strip()]
            if name == "findViewById": result = surface
            elif name == "surface": result = surface
            elif name == "min": result = min(values)
            elif name.startswith("get"):
                result = getattr(values[0], name[3:].lower())
            elif name.startswith("set"):
                values[0].values[name[3:]] = values[1]
            else: raise AssertionError(line)
            continue
        parts = [p.strip() for p in args.split(",")]
        if op.startswith("move-result"):
            registers[parts[0]] = result
        elif op.startswith("const"):
            value = int(parts[1], 0)
            registers[parts[0]] = struct.unpack("<f", struct.pack("<I", value & 0xFFFFFFFF))[0] if value == 0x40000000 else value
        elif op == "instance-of": registers[parts[0]] = isinstance(registers[parts[1]], View)
        elif op == "check-cast": pass
        elif op.startswith("if-"):
            value = registers[parts[0]]
            if (not value if op == "if-eqz" else value <= 0): pc = labels[parts[1]]
        elif op == "int-to-float": registers[parts[0]] = f32(registers[parts[1]])
        elif op.startswith(("div-", "mul-", "sub-", "add-")):
            a = registers[parts[0] if "/2addr" in op else parts[1]]
            b = registers[parts[1]] if "/2addr" in op else (int(parts[2], 0) if "/lit" in op else registers[parts[2]])
            kind = op.split("-", 1)[0]
            value = {"div": lambda: a / b, "mul": lambda: a * b, "sub": lambda: a - b, "add": lambda: a + b}[kind]()
            registers[parts[0]] = int(value) if "-int" in op else f32(value)
        else: raise AssertionError(line)
    raise AssertionError("Helper did not return")


def bounds(view):
    s = view.values
    left = view.left + s["TranslationX"] + s["PivotX"] * (1 - s["ScaleX"])
    top = view.top + s["TranslationY"] + s["PivotY"] * (1 - s["ScaleY"])
    return left, top, left + view.width * s["ScaleX"], top + view.height * s["ScaleY"]


def test_exact_retroid_geometry_reapplies_after_reset_without_resizing():
    parent = View(1240, 1080)
    surface = View(1240, 698, 0, 191, parent)
    execute_helper(surface)
    assert bounds(surface) == pytest.approx((0, 75, 1240, 1005), abs=0.0001)
    assert (surface.width, surface.height) == (1240, 698)
    assert parent.values["BackgroundColor"] == -16777216
    original = surface.values.copy()
    execute_helper(surface)
    assert surface.values == original
    surface.values.update(ScaleY=1, TranslationY=0)
    execute_helper(surface)
    assert surface.values == original


@pytest.mark.parametrize("size,layout", [((1080, 1240), (1080, 608)), ((1920, 1080), (1920, 1080)), ((1241, 1081), (1241, 698))])
def test_parent_resize_keeps_full_picture_inside_parent(size, layout):
    parent = View(*size)
    surface = View(*layout, 0, 0, parent)
    execute_helper(surface)
    left, top, right, bottom = bounds(surface)
    assert left >= -0.001 and top >= -0.001
    assert right <= size[0] + 0.001 and bottom <= size[1] + 0.001
    assert (right - left) / (bottom - top) == pytest.approx(4 / 3)


def test_unlaid_out_or_missing_surface_is_safe():
    execute_helper(None)
    surface = View(0, 0, parent=View(1240, 1080))
    execute_helper(surface)
    assert surface.values == {}


def test_synthetic_dex_assembly_round_trip(tmp_path):
    m = module()
    if not Path("/workspace/.tools/smali-2.5.2/smali-2.5.2.jar").exists():
        pytest.skip("Optional smali/baksmali 2.5.2 toolchain unavailable")
    tree = tmp_path / "source"
    target = tree / m.DISPLAY_CLASS
    target.parent.mkdir(parents=True)
    target.write_text(m.transform_smali(synthetic_smali(m)))
    watcher = tree / "android4x3/marvel/StretchWatcher.smali"
    watcher.parent.mkdir(parents=True)
    watcher.write_bytes((m.DIRECTORY / "StretchWatcher.smali").read_bytes())
    dex = tmp_path / "synthetic.dex"
    m.smali_command("org.jf.smali.Main", "assemble", "--api", "26", str(tree), "-o", str(dex))
    m.check_dex(dex.read_bytes())
    decoded = tmp_path / "decoded"
    m.smali_command("org.jf.baksmali.Main", "disassemble", "--api", "26", str(dex), "-o", str(decoded))
    body = (decoded / m.DISPLAY_CLASS).read_text()
    assert "->setScaleY(F)V" in body
    assert "->setLayoutParams" not in body
    assert "->fit16x9(Landroid/app/Activity;)V" in body
    assert "->addOnPreDrawListener" in body
