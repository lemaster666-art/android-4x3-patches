"""Installer safety and portability checks; no game files or network needed."""
from __future__ import annotations

import hashlib
import importlib.util
import io
from pathlib import Path
import sys
import tarfile
import zipfile

import pytest

HERE = Path(__file__).resolve().parents[1] / "games/marvel-cosmic-invasion"


def module():
    spec = importlib.util.spec_from_file_location("marvel_local_build_test", HERE / "local_build.py")
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def test_existing_working_patch_files_are_unchanged():
    m = module()
    for name, expected in m.PATCH_FILES.items():
        assert m.sha(HERE / name) == expected


def test_valid_cache_does_not_download_and_corrupt_cache_fails(tmp_path, monkeypatch):
    m = module()
    cache = tmp_path / "cached.jar"
    cache.write_bytes(b"synthetic verified tool")
    expected = m.sha(cache)
    def forbidden(*args):
        pytest.fail("A valid or corrupt cached file must not trigger a network request")
    monkeypatch.setattr(m.urllib.request, "build_opener", forbidden)
    assert m.download("https://example.invalid/tool", cache, expected) == cache
    cache.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="Cached checksum mismatch"):
        m.download("https://example.invalid/tool", cache, expected)
    assert cache.read_bytes() == b"tampered"


def test_failed_download_is_not_installed(tmp_path, monkeypatch):
    m = module()
    class Opener:
        def open(self, *args, **kwargs):
            return io.BytesIO(b"wrong artifact")
    monkeypatch.setattr(m.urllib.request, "build_opener", lambda *args: Opener())
    dest = tmp_path / "tool.jar"
    with pytest.raises(ValueError, match="Download checksum mismatch"):
        m.download("https://example.invalid/tool", dest, "0" * 64)
    assert not dest.exists()
    assert not dest.with_suffix(".jar.partial").exists()


def test_https_is_required_including_redirects(tmp_path):
    m = module()
    with pytest.raises(ValueError, match="HTTPS"):
        m.download("http://example.invalid/tool", tmp_path / "tool", "0" * 64)
    with pytest.raises(ValueError, match="non-HTTPS"):
        m.HTTPSOnly().redirect_request(None, None, 302, "redirect", {}, "http://example.invalid/tool")


def test_archive_cannot_escape_tool_directory(tmp_path):
    m = module()
    bad = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(bad, "w") as z:
        z.writestr("../outside", b"bad")
    with pytest.raises(ValueError, match="Unsafe tool archive"):
        m.extract(bad, tmp_path / "tools")
    assert not (tmp_path / "outside").exists()
    tar = tmp_path / "unsafe.tar"
    with tarfile.open(tar, "w") as z:
        info = tarfile.TarInfo("../../outside")
        info.size = 3
        z.addfile(info, io.BytesIO(b"bad"))
    with pytest.raises(tarfile.FilterError):
        m.extract(tar, tmp_path / "tools")


def test_wrong_apk_is_rejected_before_tool_install(tmp_path, monkeypatch):
    m = module()
    apk = tmp_path / "wrong input.apk"
    apk.write_bytes(b"synthetic unsupported input")
    monkeypatch.setattr(sys, "argv", ["local_build.py", str(apk)])
    monkeypatch.setattr(m.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(m.platform, "machine", lambda: "arm64")
    def forbidden(*args):
        pytest.fail("Wrong input must be rejected before downloading tools")
    monkeypatch.setattr(m, "ensure_tools", forbidden)
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        m.main()


def test_existing_output_is_not_overwritten(tmp_path, monkeypatch):
    m = module()
    apk, output = tmp_path / "synthetic original.apk", tmp_path / "keep.apk"
    apk.write_bytes(b"synthetic original")
    output.write_bytes(b"existing output")
    monkeypatch.setattr(m, "ORIGINAL_SHA", m.sha(apk))
    monkeypatch.setattr(sys, "argv", ["local_build.py", str(apk), "--output", str(output)])
    with pytest.raises(ValueError, match="already exists"):
        m.main()
    assert output.read_bytes() == b"existing output"


def test_pinned_tool_classpath_excludes_unverified_extra_jars(tmp_path, monkeypatch):
    m = module()
    archive = tmp_path / "sdk.zip"
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("android-16/zipalign", b"synthetic tool")
        z.writestr("android-16/apksigner", b"synthetic tool")
    monkeypatch.setattr(m, "download", lambda url, dest, checksum: archive)
    monkeypatch.setattr(m, "ensure_java", lambda *args: tmp_path / "java/bin")
    env = m.ensure_tools(tmp_path / "cache", "Darwin", "arm64")
    assert "*" not in env["SMALI_CLASSPATH"]
    assert len(env["SMALI_CLASSPATH"].split(m.os.pathsep)) == len(m.JARS)
    assert "android-sdk-macosx/build-tools/android-16" in env["PATH"]
    assert env["ANDROID_SDK_ROOT"].endswith("android-sdk-macosx")
