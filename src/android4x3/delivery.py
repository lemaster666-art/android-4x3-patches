"""Safe source-only macOS delivery, shared by aspect and lifecycle workshops."""
from __future__ import annotations

from pathlib import PurePosixPath
import re
import shlex

from .errors import PatchError


def mac_source_command(launcher: str, ref: str, repository: str,
                       arguments: tuple[str, ...] = ()) -> str:
    if not re.fullmatch(r"(?:main|[0-9a-f]{40})", ref):
        raise PatchError("Use main or a full published commit SHA")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise PatchError("Repository must be owner/name without credentials")
    path = PurePosixPath(launcher)
    if (not re.fullmatch(r"[A-Za-z0-9_./-]+\.sh", launcher)
            or path.is_absolute() or ".." in path.parts or path.as_posix() != launcher):
        raise PatchError("Launcher must be a safe repository-relative shell script")
    owner, name = repository.split("/")
    suffix = "refs/heads/main" if ref == "main" else ref
    url = f"https://codeload.github.com/{owner}/{name}/zip/{suffix}"
    tail = "".join(" " + shlex.quote(arg) for arg in arguments)
    return (" && " + chr(92) + chr(10)).join([
        "apk4x3_code=$(mktemp -d)",
        f"curl --proto '=https' --proto-redir '=https' -fL {shlex.quote(url)} -o \"$apk4x3_code/tools.zip\"",
        "ditto -x -k \"$apk4x3_code/tools.zip\" \"$apk4x3_code\"",
        f'bash "$apk4x3_code/{name}-{ref}/{launcher}"{tail}',
    ])
