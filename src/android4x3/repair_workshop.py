"""Project command routing and audited repair delivery; no generic game hooks."""
from __future__ import annotations

import json
from pathlib import Path
import re
import unicodedata

from .delivery import mac_source_command
from .errors import PatchError
from . import workshop as w

REFERENCE = "6cbe39a7f5ad14911f1d2dc3f4a82ee35cb7c82c"
SKILLS = {
    "aspect": ".agents/skills/four-three-time/SKILL.md",
    "exit": ".agents/skills/exit-issues/SKILL.md",
    "startup-exit": ".agents/skills/startup-exit-issue/SKILL.md",
}


def route_invocation(text: str) -> dict:
    """Recognize explicit commands, not arbitrary discussion of startup/exit."""
    links = list(dict.fromkeys(re.findall(r"https?://[^\s<>\])]+", text)))
    words = re.sub(r"\[[^\]]*\]\(https?://[^)]+\)", " ", text)
    words = re.sub(r"https?://\S+", " ", words)
    tokens = re.findall(r"[a-z]+|[0-9]+", unicodedata.normalize("NFKC", words).casefold())
    found = set()
    while tokens:
        if tokens[:3] == ["4", "3", "time"]:
            found.add("aspect"); del tokens[:3]
        elif tokens[:2] in (["exit", "issue"], ["exit", "issues"]):
            found.add("exit"); del tokens[:2]
        elif (tokens[:3] in (["startup", "exit", "issue"], ["startup", "exit", "issues"])
              or tokens[:4] in (["startup", "and", "exit", "issue"], ["startup", "and", "exit", "issues"])):
            count = 4 if tokens[1] == "and" else 3
            found.add("startup-exit"); del tokens[:count]
        else:
            raise PatchError("Use an explicit workshop command; ordinary discussion does not start a run")
        while tokens and tokens[0] in {"and", "with", "plus", "then"}:
            del tokens[0]
            if not tokens:
                raise PatchError("Incomplete combined workshop command")
    if not found:
        raise PatchError("No workshop command supplied")
    if "startup-exit" in found:
        found.discard("exit")  # One integrated investigation, not duplicate Exit runs.
    modes = [k for k in SKILLS if k in found]
    return {"workflows": modes, "skills": [SKILLS[k] for k in modes], "apk_links": links}


def load_repair_profile(repo: Path, name: str) -> dict:
    if not w.GAME_ID.fullmatch(name):
        raise PatchError("Invalid repair profile ID")
    path = w.source_path(repo, f"workshop/repairs/{name}.json")
    profile = json.loads(path.read_text())
    if (not isinstance(profile, dict) or profile.get("schema_version") != 1
            or profile.get("repair_id") != name or profile.get("workflow") not in {"exit", "startup-exit"}):
        raise PatchError("Unsupported or mismatched repair profile")
    sources = profile.get("source_checksums")
    if not isinstance(sources, dict) or not sources:
        raise PatchError("Repair profile needs source checksums")
    for file, expected in sources.items():
        source = w.source_path(repo, file)
        if source.suffix not in w.CODE_SUFFIXES | {".java"} or not isinstance(expected, str) or not w.SHA.fullmatch(expected):
            raise PatchError("Repair profile may pin source code only, with SHA-256 checksums")
        if w.sha(source) != expected:
            raise PatchError(f"Validated repair source changed: {file}")
    launcher = profile.get("launcher")
    if launcher not in sources:
        raise PatchError("Repair launcher must be source-pinned")
    args = profile.get("launcher_arguments", [])
    if not isinstance(args, list) or any(not isinstance(arg, str) or not w.GAME_ID.fullmatch(arg) for arg in args):
        raise PatchError("Launcher arguments must be explicit safe game IDs")
    mac_source_command(launcher, "main", "owner/repo", tuple(args))
    hashes = profile.get("original_apk_sha256")
    if not isinstance(hashes, list) or not hashes or any(not isinstance(v, str) or not w.SHA.fullmatch(v) for v in hashes):
        raise PatchError("Repair profile needs audited original APK hashes")
    if profile.get("signing_policy") != "reuse-existing":
        raise PatchError("Repair updates must preserve the existing signing identity")
    if not isinstance(profile.get("artwork_required"), bool) or not isinstance(profile.get("includes_aspect_patch"), bool):
        raise PatchError("Declare artwork and bundled aspect requirements explicitly")
    for key in ["allowed_changes", "allowed_additions"]:
        entries = profile.get(key)
        if not isinstance(entries, list) or any(not isinstance(n, str) or not w.safe_name(n) or any(c in n for c in "*?[") or n.startswith("META-INF/") for n in entries):
            raise PatchError("Declare exact non-signature APK member allowlists")
    if not profile["allowed_changes"] or set(profile["allowed_changes"]) & set(profile["allowed_additions"]):
        raise PatchError("Repair must declare disjoint changes/additions")
    return profile


def repair_mac_command(repo: Path, name: str, ref: str, repository: str,
                       *, workflow: str | None = None) -> str:
    profile = load_repair_profile(repo, name)
    if workflow is not None and workflow != profile["workflow"]:
        raise PatchError("This profile bundles a different workflow; do not silently apply additional repairs")
    return mac_source_command(profile["launcher"], ref, repository,
                              tuple(profile.get("launcher_arguments", [])))


def validate_exit_trace(events: list[str], *, successful: bool,
                        process_exit_expected: bool = False) -> None:
    """Reusable host-test contract for ONE exit attempt; adapters supply verified markers.

    Audio may finish before or after the game loop returns, depending on engine.
    This checks ordering, not that a marker truthfully represents real cleanup.
    """
    terminal = ["activity_finish_requested", "activity_destroyed", "process_exit"]
    if not successful:
        if any(e in events for e in terminal):
            raise PatchError("Failed startup must retain diagnostics, not close the activity/process")
        return
    required = ["exit_intent_confirmed", "saves_settled", "game_returned_success",
                "audio_cleanup_complete", "activity_finish_requested", "activity_destroyed"]
    if any(e not in events for e in required):
        raise PatchError("Incomplete successful Exit evidence")
    if any(events.count(e) > 1 for e in terminal):
        raise PatchError("Duplicate activity/process termination")
    finish = events.index("activity_finish_requested")
    if any(events.index(e) >= finish for e in required[:4]):
        raise PatchError("Activity closed before confirmed Exit, save, game or audio cleanup")
    if events.index("activity_destroyed") <= finish:
        raise PatchError("Activity destruction must follow the finish request")
    if process_exit_expected and "process_exit" not in events:
        raise PatchError("Expected lifecycle-coordinated process exit is missing")
    if "process_exit" in events and events.index("process_exit") <= events.index("activity_destroyed"):
        raise PatchError("Process exited before Activity destruction")
