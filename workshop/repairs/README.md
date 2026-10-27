# Android Startup & Exit Repair Workshop

In a Codex chat attached to this repository, type `EXIT issues` or
`STARTUP&EXIT ISSUE`, optionally followed by your original-APK download link.
The root [AGENTS.md](../../AGENTS.md) routes to persistent project skills:

| Command | Scope | Skill |
|---|---|---|
| `EXIT issues` | Quit, saves, audio and Android shutdown | [exit-issues](../../.agents/skills/exit-issues/SKILL.md) |
| `STARTUP&EXIT ISSUE` | Splash/loading/logo transitions plus Exit | [startup-exit-issue](../../.agents/skills/startup-exit-issue/SKILL.md) |
| `4:3 time` | Existing aspect workshop | [four-three-time](../../.agents/skills/four-three-time/SKILL.md) |

Capitalization, repeated spaces and ordinary punctuation are normalized.
`exit-issues!`, `startup & exit issue`, `STARTUP/EXIT ISSUES` and
`Startup and Exit Issues` work. Combine commands as
`4:3 time + STARTUP&EXIT ISSUE https://example.com/original.apk`.
The agent performs one intake and integrated repair. A standalone Exit run does
not implicitly add 4:3 or PNG changes. These are project chat commands, not
Terminal aliases or a globally installed plugin. New sessions discover them
through `AGENTS.md`; an explicit fallback is to ask Codex to read the skill file.

## Run contract

1. Reuse supplied links/hashes/versions and earlier reports before asking again.
   Download/inspect outside Git with `tools/workshop.py inspect`: ZIP/CRC,
   signature, manifest, SDK/ABI and engine/runtime hints. Compare the owner's
   checksum first. Never execute the APK or site scripts in the cloud. Integrity
   does not establish publisher trust. Preserve the original and private signer.
2. Trace the actual Activity/bootstrap, game-loop, saves, graphics and audio.
   Distinguish Android launch icon, custom splash View, engine logos, videos and
   toast/overlay windows. Normal desktop loop return need not close Android.
3. Choose verified, minimally scoped hooks. Keep failed-startup diagnostics and
   existing aspect patches. Preserve complete developer-logo sound/animation
   unless authorized otherwise. Use the [Marvel technical reference](MARVEL_REFERENCE.md)
   for reasoning, not universal fields/offsets. Inspect style transitions before
   repeated immersive hiding, observers or arbitrary timing adjustments.
4. Implement per-game adapters with semantic/context guards, original/patched/
   unsupported recognition and exact archive allowlists. Respect narrower user
   approval constraints; normal invocation covers development/checks/code-only
   delivery. Report significant signing/protection/ABI problems before invasive
   alternatives. Do not bypass protection or weaken browser/device security.
5. Test lifecycle order, startup failure, audio/save outcomes, duplicate callbacks,
   source/version mismatch and member integrity with authored fixtures. Run
   required real compiler/assembler/native checks. Host doubles are not Android.
6. Reproduce privately; verify source/original pins, ZIP, alignment, signatures,
   identity, unrelated-member equality and original/key preservation. Do not edit
   a validated reference merely to make it fit a new shared abstraction.
7. Publish only code/tests/configuration/docs and give one Mac source-download/
   build command using the owner's local APK. Do not transfer large cloud APKs.
8. Record static, host, cloud, Mac and owner-reported device evidence separately.
   Hardware success is scoped to the tested game/build/device.

## Shared infrastructure and environment reuse

| Need | Reuse |
|---|---|
| Private APK preflight and engine/runtime hints | `tools/workshop.py inspect`; `src/android4x3/workshop.py` |
| Repack, manifest, CRC, member comparisons | `src/android4x3/apk.py`, `manifest.py`, `workshop.py` |
| Alignment/signing/certificate verification | `src/android4x3/signing.py` |
| Generic guarded game modules/profiles | `tools/workshop.py profile/build`; `tools/workshop-build.sh` |
| Pinned Python/Java/Android/smali caches | Existing workshop bootstrap and unchanged Marvel installer |
| Specialized .NET/Zig/Android headers | Unchanged optional Marvel experiment installer |
| Source-only Mac command generation | `src/android4x3/delivery.py`; `tools/repair-workshop.py command` |
| Routing and immutable reference pins | `repair_workshop.py`; `workshop/repairs/*.json` |
| Engine-neutral lifecycle test assertions | `validate_exit_trace` in `repair_workshop.py` |
| Authored Java/managed/JNI/audio harnesses | `tests/test_marvel_enhancements.py`; `tests/fixtures/marvel_enhancements/` |
| Focused installed-build capture | Preserved `capture-status-bar.sh` and its ADB tests |

Reuse `APK4X3_CACHE`, initialized Java/smali/SDK paths and verified compiler
archives; do not duplicate installers or reinstall working dependencies. Source
`/workspace/.tools/activate-android4x3.sh` in the prepared cloud when available.
Use .NET/Zig only when the actual repair requires them. Keep caches outside Git.

`validate_exit_trace` accepts markers from one synthetic exit attempt:
`exit_intent_confirmed`, `saves_settled`, `game_returned_success`,
`audio_cleanup_complete`, `activity_finish_requested`, `activity_destroyed` and
optionally `process_exit`. Saves, successful return and audio cleanup must precede
finish; process exit must follow destruction. Failed startup must retain its
Activity/process. Audio cleanup may occur inside or after the game loop. Each
adapter must establish the real meaning of its markers; this assertion helper
does not parse arbitrary logs or prove real saves/audio completed.

## Audited Mac delivery profiles

`workshop/repairs/NAME.json` records a source-pinned, implemented launcher,
workflow (`exit` or `startup-exit`), artwork requirement, bundled aspect changes,
original hashes, APK allowlists, signing policy and evidence. A profile is not a
patch implementation. The launcher must enforce its actual source/version guards,
private inputs, key reuse and build postconditions; metadata does not replace
those runtime checks. Command generation checks pins before publishing a command.

New registered game modules can reuse `tools/workshop-build.sh` with an explicit
game argument and ordinary audited workshop profile. Specialized repairs may
provide their own pinned launcher while reusing existing bootstrap/installers.
Each must support the original-APK picker, optional PNG picker, new Downloads
APK/report and Mac CPU architectures where its tools permit. State precise
OS/CPU limitations. Never silently bundle extra changes in an Exit-only profile.

Marvel delegates to its **unchanged combined launcher**, including 4:3 + PNG/
startup + Exit and requiring its existing signer. It is not an Exit-only adapter:
`--workflow exit` against that profile fails rather than applying extra changes.
The profile pins 28 preserved source/test files. An unexplained mismatch stops
delivery; do not automatically repin a working implementation.

```bash
python tools/repair-workshop.py route '4:3 time + STARTUP&EXIT ISSUE'
python tools/repair-workshop.py verify marvel-cosmic-invasion
python tools/repair-workshop.py command marvel-cosmic-invasion \
  --workflow startup-exit --ref FULL-PUBLISHED-COMMIT-SHA
```

Aspect and repair command generation share safe ref/path validation, shell
quoting and HTTPS source-ZIP delivery. Prefer a published full revision and check
that its archive contains the tested profile, source and launcher. The Mac uses
its own original APK, independently of cloud inspection. Compatible tools/caches
are reused; missing pinned tools install privately. Only repairs requiring custom
art open a second picker. No game download or cloud-APK transfer occurs on Mac.

Keep the existing private signing identity. Same-key/package updates work; a
different signer cannot update the distributor APK. Do not automatically uninstall,
erase saves, rename packages, reset credentials or alter protection.

## Privacy, hardware checklist and limits

Never commit APKs, proprietary extracted code/assets, artwork, captures or keys.
Use synthetic fixtures and private scratch storage. Run `tools/workshop.py audit`
on staged blobs and manually inspect provenance/content. Delete private review
media after use when requested; user originals/conversation attachments are separate.

Device checklist: cold launch, stable PNG, no bar flash, original logo timing/
sound, loading/gameplay resume, Quit, stopped audio, return to launcher, preserved
saves, relaunch and repeat Quit. Record only actual coverage. Covering a black gap
is not faster loading; cosmetic fades/holds add deliberate time. New build reports
correctly remain unverified until that specific output is physically tested.

Protected/obfuscated runtimes, unsupported ABIs, split APKs, missing assets and
uncertain audio ownership can prevent a defensible repair. Do not invent a passing
patch, force a timed process kill or transplant Marvel's ARM64 Mono/FMOD hooks
into Unity, Godot or another SDL port without investigating that build.
