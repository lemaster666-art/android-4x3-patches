# Codex workflow entry points

Recognize explicit project commands case-insensitively. Normalize ordinary
spacing/punctuation; `STARTUP&EXIT ISSUE`, `startup & exit issue`,
`Startup-and-Exit Issues` and `startup/exit issue` select the same workflow.
`EXIT issues`, `exit-issues` and `Exit Issues!` select the Exit-only workflow.
These are Codex chat commands, not shell aliases or installed cloud plugins.

| Command | Read and follow |
|---|---|
| `4:3 time` | [.agents/skills/four-three-time/SKILL.md](.agents/skills/four-three-time/SKILL.md) |
| `EXIT issues` | [.agents/skills/exit-issues/SKILL.md](.agents/skills/exit-issues/SKILL.md) |
| `STARTUP&EXIT ISSUE` | [.agents/skills/startup-exit-issue/SKILL.md](.agents/skills/startup-exit-issue/SKILL.md) |

Commands may be combined, e.g. `4:3 time + STARTUP&EXIT ISSUE`, with an APK
link in the same message. Read all selected skills, reuse one private intake and
environment, and plan one coherent patch/build. The combined startup/Exit skill
already includes Exit; do not run duplicate Exit investigations. Do not add an
aspect-ratio change to an Exit-only request unless authorized or already part of
the working patch being preserved. Routing can be checked with
`python tools/repair-workshop.py route 'EXIT issues'`.

When the user enters **`4:3 time`** (optionally followed by an APK link), read and
follow [.agents/skills/four-three-time/SKILL.md](.agents/skills/four-three-time/SKILL.md).
This is a project-local workflow, not a shell command. If no APK link was given,
ask for a private or publicly accessible download link, then continue when supplied.

Do not start this workflow for unrelated requests. Preserve the existing working
Marvel patch and its local launcher. Follow the skill's private-file boundaries,
per-game validation, and local Mac delivery requirements.

For the repair workflows, read [workshop/repairs/README.md](workshop/repairs/README.md)
and the [validated Marvel reference](workshop/repairs/MARVEL_REFERENCE.md).
Use existing links/evidence in the session before asking again. Inspect exact
revision boundaries before repeated captures or speculative builds. Preserve
the reference at `6cbe39a7f5ad14911f1d2dc3f4a82ee35cb7c82c`;
`python tools/repair-workshop.py verify marvel-cosmic-invasion` checks its pins.
Never publish APKs, extracted game files, private logs/video, artwork or keys.

## Owner preference: include USB installation with every new build

Whenever delivering a new APK build or Mac build command, also include a separate,
paste-once Bash block for installing the locally built APK over USB. Do not wait
for the owner to ask. Use the known Mac ADB path below, a Downloads file picker
and `install -r`; adapt the prompt to the game when useful:

```bash
apk4x3_install=$(osascript -e 'POSIX path of (choose file with prompt "Select your NEW locally built APK" default location (path to downloads folder))') &&
"$HOME/Downloads/platform-tools/adb" install -r "$apk4x3_install"
```

Briefly remind the owner to close the game, connect USB, enable USB debugging,
accept authorization if prompted, select the new local output and wait for
`Success`. Same-package, same-key updates preserve saved data. If signing differs,
report the conflict; never automatically uninstall or clear data. This is an
assistant delivery preference, not a change to any working patch or build script.
