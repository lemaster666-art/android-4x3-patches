"""Proprietary-free workshop contracts and real signed synthetic round trips."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

import pytest

from android4x3 import signing, workshop as w
from android4x3.errors import PatchError

ROOT = Path(__file__).resolve().parents[1]
ENTRY = "assets/patch state.bin"


def cli():
    spec = importlib.util.spec_from_file_location("four_three_workshop_cli_test", ROOT / "tools/workshop.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def project(tmp_path, make_synthetic_game, make_apk, text_manifest, monkeypatch):
    repo = tmp_path / "repo"
    game = make_synthetic_game(repo)
    original = make_apk(tmp_path / "private/original.apk", manifest=text_manifest("example.synthetic.game"),
                        entries=[(ENTRY, b"ORIGINAL", zipfile.ZIP_STORED),
                                 ("assets/untouched.bin", b"keep exactly", zipfile.ZIP_STORED)])
    def save():
        profile = w.make_profile(repo, "synthetic-game", original, [ENTRY], [], [], None)
        (game / "workshop.json").write_text(json.dumps(profile))
        return profile
    save()
    monkeypatch.setattr(w, "verify_signature", lambda *args, **kwargs: {"state": "passed", "details": "unit-test mock"})
    monkeypatch.setattr(signing, "_state_dir", lambda: tmp_path / "private/keys")
    monkeypatch.setattr(signing, "align_apk", lambda a, b: shutil.copyfile(a, b))
    monkeypatch.setattr(signing, "sign_apk", lambda a, b: shutil.copyfile(a, b))
    monkeypatch.setattr(signing, "verify_alignment", lambda path: None)
    return repo, game, original, tmp_path / "private/output.apk", save


def test_inspect_is_read_only_and_does_not_claim_backend_or_gameplay(project):
    repo, _, original, _, _ = project
    checksum = w.sha(original)
    report = w.inspect(original, repo=repo)
    assert report["identity"]["package"] == "example.synthetic.game"
    assert report["zip_integrity"] == "passed"
    assert "unverified" in report["rendering_backend"]
    assert report["target"]["picture"] == [1240, 930]
    assert report["target"]["crop"] is False
    assert w.sha(original) == checksum


@pytest.mark.parametrize("name", ["../escape", "/absolute", "assets//alias", "assets/./alias", "C:/file", "a\\b"])
def test_unsafe_paths_rejected(name):
    assert not w.safe_name(name)


def test_path_and_hash_guards_precede_patch_execution(project):
    repo, game, original, output, _ = project
    original.write_bytes(b"changed input")
    with pytest.raises(PatchError, match="SHA-256 mismatch"):
        w.build(repo, "synthetic-game", original, output)
    assert not output.exists()
    marker = output.parent / "must-not-execute"
    with (game / "patch_impl.py").open("a") as stream:
        stream.write(f"\nopen({str(marker)!r}, 'w').write('bad')\n")
    with pytest.raises(PatchError, match="source changed"):
        w.build(repo, "synthetic-game", original, output)
    assert not marker.exists()


def test_source_paths_cannot_escape_or_pin_proprietary_binaries(project, tmp_path):
    repo, game, _, _, _ = project
    p = json.loads((game / "workshop.json").read_text())
    p["source_checksums"]["../outside.py"] = "0" * 64
    with pytest.raises(PatchError):
        w.validate_profile(repo, "synthetic-game", p)
    outside = tmp_path / "outside.py"
    outside.write_text("pass\n")
    try:
        (game / "symlink.py").symlink_to(outside)
    except OSError:
        pytest.skip("Host does not permit creating a symlink for this path-escape check")
    with pytest.raises(PatchError, match="escapes"):
        w.source_path(repo, "games/synthetic-game/symlink.py")


def test_build_postconditions_and_unrelated_bytes(project):
    repo, _, original, output, _ = project
    before = w.sha(original)
    result = w.build(repo, "synthetic-game", original, output)
    assert result["changed_members"] == [ENTRY]
    assert result["unchanged_members"] == 2
    assert result["post_state"] == "patched"
    assert result["device_tested_this_run"] is False
    with zipfile.ZipFile(output) as archive:
        assert archive.read(ENTRY) == b"PATCHED"
        assert archive.read("assets/untouched.bin") == b"keep exactly"
    assert w.sha(original) == before
    with pytest.raises(PatchError, match="overwrite"):
        w.build(repo, "synthetic-game", original, output)


def test_undeclared_changes_stop_before_publishing(project):
    repo, game, original, output, _ = project
    p = json.loads((game / "workshop.json").read_text())
    p["allowed_changes"] = ["assets/some-other-file"]
    (game / "workshop.json").write_text(json.dumps(p))
    with pytest.raises(PatchError, match="undeclared"):
        w.build(repo, "synthetic-game", original, output)
    assert not output.exists()


def test_unrelated_change_detection_is_independent_of_module_claims(project, tmp_path):
    repo, _, original, _, _ = project
    changed = tmp_path / "unrelated.apk"
    with zipfile.ZipFile(original) as source, zipfile.ZipFile(changed, "w") as dest:
        for info in source.infolist():
            dest.writestr(info, b"tampered" if info.filename == "assets/untouched.bin" else source.read(info))
    with pytest.raises(PatchError, match="Unrelated"):
        w.compare_members(original, changed, {"allowed_changes": [ENTRY]})


def test_failed_post_probe_never_publishes_apk(project):
    repo, game, original, output, save = project
    path = game / "patch_impl.py"
    path.write_text(path.read_text().replace('destination.write_bytes(b"PATCHED")', 'destination.write_bytes(b"BROKEN")'))
    save()
    with pytest.raises(PatchError, match="Post-patch"):
        w.build(repo, "synthetic-game", original, output)
    assert not output.exists()


def test_explicit_authored_addition_is_preserved_and_verified(project):
    repo, game, original, output, _ = project
    path = game / "patch_impl.py"
    path.write_text(path.read_text().replace('return {ENTRY: destination}',
        'helper = Path(output_dir) / "helper.txt"\n    helper.write_text("authored helper")\n    return {ENTRY: destination, "assets/helper.txt": helper}'))
    profile = w.make_profile(repo, "synthetic-game", original, [ENTRY], ["assets/helper.txt"], [], None)
    (game / "workshop.json").write_text(json.dumps(profile))
    result = w.build(repo, "synthetic-game", original, output)
    assert result["added_members"] == ["assets/helper.txt"]
    assert result["changed_members"] == [ENTRY]


def test_private_outputs_and_reports_cannot_enter_checkout(project):
    repo, _, original, _, _ = project
    with pytest.raises(PatchError, match="outside"):
        w.build(repo, "synthetic-game", original, repo / "bad.apk")


def test_profile_requires_pinned_dependency_files(project):
    repo, game, _, _, _ = project
    p = json.loads((game / "workshop.json").read_text())
    p["dependencies"]["setup_script"] = "tools/unpinned.py"
    with pytest.raises(PatchError, match="checksum-pinned"):
        w.validate_profile(repo, "synthetic-game", p)


def test_delivery_command_is_safe_complete_and_shell_parseable():
    tool = cli()
    commit = "a" * 40
    command = tool.mac_command("new-game", commit, "owner/repo")
    assert command.count("\n") == 3
    assert f"/zip/{commit}" in command
    assert "repo-" + commit + "/tools/workshop-build.sh" in command
    assert command.endswith("new-game")
    subprocess.run(["bash", "-n"], input=command, text=True, check=True)
    for game, ref, repository in [("$(bad)", "main", "owner/repo"), ("new-game", "main;bad", "owner/repo"), ("new-game", "main", "https://token@host/repo")]:
        with pytest.raises(PatchError):
            tool.mac_command(game, ref, repository)


def test_dependency_environment_reused_when_only_patch_code_changes(project, tmp_path, monkeypatch):
    repo, _, _, _, _ = project
    requirements = repo / "requirements.txt"
    requirements.write_text("# synthetic dependency fixture\n")
    tool = cli()
    monkeypatch.setattr(tool, "REPO", repo)
    calls = []
    def run(argv, **kwargs):
        calls.append(argv)
        if argv[1:3] == ["-m", "venv"]:
            Path(argv[3]).mkdir(parents=True)
        return subprocess.CompletedProcess(argv, 0)
    monkeypatch.setattr(tool.subprocess, "run", run)
    p = {"dependencies": {"python_requirements": ["requirements.txt"]},
         "source_checksums": {"requirements.txt": w.sha(requirements), "game.py": "a" * 64}}
    first = tool.install_dependencies(p, tmp_path / "cache")
    assert len(calls) == 3
    p["source_checksums"]["game.py"] = "b" * 64
    assert tool.install_dependencies(p, tmp_path / "cache") == first
    assert len(calls) == 3


def test_owner_hash_mismatch_precedes_read_only_analysis(tmp_path, monkeypatch):
    tool = cli()
    apk = tmp_path / "different.apk"
    apk.write_bytes(b"synthetic mismatch")
    monkeypatch.setattr(sys, "argv", ["workshop.py", "inspect", str(apk), "--expected-sha256", "a" * 64])
    def forbidden(*args, **kwargs): pytest.fail("Mismatched download must not be inspected as the original")
    monkeypatch.setattr(w, "inspect", forbidden)
    with pytest.raises(PatchError, match="Owner-supplied"):
        tool.main()


def test_mac_picker_uses_argument_not_interpolated_applescript(project, monkeypatch):
    repo, _, original, output, _ = project
    tool = cli()
    monkeypatch.setattr(tool, "REPO", repo)
    monkeypatch.setattr(tool.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(tool.platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(tool.os, "environ", dict(os.environ, APK4X3_CACHE=str(output.parent / "cache")))
    class Tools:
        def ensure_tools(self, *args): return {}
    monkeypatch.setattr(tool, "reference_tools", lambda: Tools())
    monkeypatch.setattr(tool, "install_dependencies", lambda *args: sys.executable)
    calls = []
    def run(argv, **kwargs):
        calls.append(argv)
        return subprocess.CompletedProcess(argv, 0, stdout=str(original) + "\n")
    monkeypatch.setattr(tool.subprocess, "run", run)
    class Args:
        game = "synthetic-game"
        apk = None
    args = Args()
    args.output = output
    tool.local_build(args)
    picker = calls[0]
    assert picker[0] == "/usr/bin/osascript"
    assert "item 1 of argv" in picker[2]
    assert picker[3] == "Choose your ORIGINAL Synthetic Game APK"
    assert any("build" in argv and str(original) in argv for argv in calls)


def test_staged_artifact_scan_reads_index_and_rejects_binaries(tmp_path, monkeypatch):
    tool = cli()
    monkeypatch.setattr(tool, "REPO", tmp_path)
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "patch.py").write_text("# newly authored patch\n")
    subprocess.run(["git", "-C", str(tmp_path), "add", "patch.py"], check=True)
    assert tool.audit_staged()["staged_files_checked"] == 1
    (tmp_path / "disguised.txt").write_bytes(b"dex\n038\0proprietary fixture marker")
    subprocess.run(["git", "-C", str(tmp_path), "add", "disguised.txt"], check=True)
    with pytest.raises(PatchError, match="disguised.txt"):
        tool.audit_staged()


def test_reference_game_files_remain_exactly_pinned():
    p = w.load_profile(ROOT, "marvel-cosmic-invasion")
    assert p["allowed_changes"] == ["classes2.dex"]
    assert p["target"]["borders_top_bottom"] == [75, 75]
    # The old, device-tested launchers are present and source-pinned, not replaced.
    assert "games/marvel-cosmic-invasion/build-local.sh" in p["source_checksums"]


def test_real_synthetic_signed_roundtrip(tmp_path, monkeypatch, make_synthetic_game, make_apk, binary_manifest):
    try:
        signing.find_android_tool("zipalign")
        signing.find_android_tool("apksigner")
        if not shutil.which("keytool"): raise PatchError("keytool missing")
    except PatchError as exc:
        if os.environ.get("ANDROID4X3_REQUIRE_NATIVE_TESTS"):
            pytest.fail(str(exc))
        pytest.skip(str(exc))
    repo = tmp_path / "repo"
    game = make_synthetic_game(repo)
    monkeypatch.setattr(signing, "_state_dir", lambda: tmp_path / "private keys")
    raw = make_apk(tmp_path / "raw.apk", manifest=binary_manifest("example.synthetic.game", "1.0", 1),
                   entries=[(ENTRY, b"ORIGINAL", zipfile.ZIP_STORED),
                            ("assets/untouched.bin", b"synthetic unchanged content", zipfile.ZIP_STORED)])
    aligned, original = tmp_path / "aligned.apk", tmp_path / "original signed.apk"
    signing.align_apk(raw, aligned)
    signing.sign_apk(aligned, original)
    p = w.make_profile(repo, "synthetic-game", original, [ENTRY], [], [], None)
    (game / "workshop.json").write_text(json.dumps(p))
    result = w.build(repo, "synthetic-game", original, tmp_path / "finished.apk")
    assert result["signature_verified"] and result["alignment_verified"]
    assert result["output_signature"]["state"] == "passed"
    assert result["post_state"] == "patched"
    assert result["changed_members"] == [ENTRY]
