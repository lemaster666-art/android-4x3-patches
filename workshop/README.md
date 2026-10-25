# 4:3 time — Android modification workshop

In a Codex session attached to **this repository**, type:

```text
4:3 time
```

Codex reads the root `AGENTS.md` and the project skill at
[`.agents/skills/four-three-time/SKILL.md`](../.agents/skills/four-three-time/SKILL.md).
It asks for your private/public original-APK download link if you have not already
provided one. You can also type `4:3 time` followed by the link in the same message.
If a client does not list project skills until a new session, the `AGENTS.md`
entry point still tells Codex to read the skill. This does not install a global
shell alias or cloud plugin. An explicit fallback is to ask Codex to read and use
that skill file in this project.

The workflow is an automated workshop run by Codex: it investigates the actual
game, writes and tests a defensible patch, and prepares a local build command.
It is **not** a universal binary patcher. Some games will be unsupported or need
information/access that cannot be inferred; Codex must report that honestly.

## Your default result

Retroid Pocket Classic, Android 14, **1240×1080** display; the complete original
picture stretched into a centred **1240×930** area with **75-pixel borders above
and below**. Vertical distortion is acceptable. Preserve the whole image without
cropping. Investigate existing Android display-scaling code first, then settings,
the final graphics presentation, and only then game-specific rendering logic.

The successful Marvel patch is the reference for a compositor approach, not
evidence that another game uses the same surface, backbuffer or patch targets.
Its existing game folder and local launcher remain unchanged by this workshop.

## What a run does

1. **Private intake:** download your linked original outside Git, check its hash,
   ZIP integrity, signature, manifest, SDK/ABI compatibility and provenance. A
   supplied reference hash must match. Do not execute downloaded site scripts or
   the APK. A valid distributor signature is not proof of safety or authenticity.
2. **Investigation:** identify engine/backend and actual layout/presentation code,
   existing aspect settings, overlays, input mapping and protection constraints.
   Distinguish library-name hints from verified call paths and visual evidence.
3. **Game-specific development:** implement guarded original/patched-state
   recognition and transformation code in `games/<game-id>/`. Preserve the source
   APK and unrelated behavior. Stop before invasive protection/security workarounds
   if a significant problem arises. No routine approval pause is needed for the
   normal workflow unless you impose one in the session.
4. **Testing and reproduction:** run synthetic tests and actual rebuild, alignment,
   signature and post-patch checks where supported. Independently compare every
   non-signature APK member; only declared entries/additions may differ.
5. **Code-only delivery:** push only reviewed patch/build code, synthetic tests,
   configuration and docs. Give you one pasteable Mac Terminal command. The Mac
   selects your local original, installs/reuses dependencies privately, builds and
   verifies a separate signed APK, and reveals it in Downloads.
6. **Device result:** keep experimental/reproduced/device-tested claims separate.
   After your report, document the exact device, OS, menus/session coverage and
   remaining limitations. Do not treat host-side checks as hardware proof.

No manual large-APK transfer between cloud and Mac is part of delivery. Cloud
analysis and optional reproduction use the APK obtained from your supplied link;
the final user build always starts from your own Mac's local original.

## Shared tools

Run from the checkout, using its already-prepared Python/SDK environment:

```sh
# Read-only private preflight. Report and APK must be outside the checkout.
python tools/workshop.py inspect /private/Original.apk --out /private/inspection.json

# After implementing/auditing a game, create a source-pinned build profile.
python tools/workshop.py profile GAME-ID --apk /private/Original.apk \
  --allow-change classes2.dex

# Build locally; a Mac opens an original-APK picker if --apk is omitted.
bash tools/workshop-build.sh GAME-ID

# Cloud/Linux reproduction, reusing prepared tools rather than installing again.
python tools/workshop.py build GAME-ID --apk /private/Original.apk \
  --output /private/New-experimental.apk

# Generate the exact Mac delivery command, preferably at a published commit.
python tools/workshop.py command GAME-ID --ref FULL-PUBLISHED-COMMIT-SHA

# Scan actual staged blobs before publishing code. Review them manually too.
python tools/workshop.py audit
```

The inspector reports signature checks as **unrun** if no Android tools are
active. Reuse the environment's existing initialization, for example sourcing
`/workspace/.tools/activate-android4x3.sh` when present, before declaring a missing
tool. The actual builder requires original and output signature verification.
It fails on unknown profiles, input/source mismatches, ambiguous/unsupported
targets, undeclared changes, changed package/version, failed postconditions or
existing output files. It does not silently enable optional branding cleanup.

`profile` creates metadata only; it does not discover or implement a patch.
It requires an existing game module/config and never overwrites an existing
profile. The generated evidence is explicitly experimental. Review/update it
after actual reproduction and device results. Existing profiles must be
deliberately refreshed when audited source files change, never weakened to make
an unexplained mismatch pass.

## Per-game profile contract

New games normally use `games/<game-id>/workshop.json`. Protected legacy examples
can use `workshop/profiles/<game-id>.json` so their working folders stay untouched.
The Marvel reference uses the latter. Required fields:

| Field | Meaning |
|---|---|
| `schema_version` | Currently `1` |
| `game_id` | Registered game slug, e.g. `marvel-cosmic-invasion` |
| `original_apk_sha256` | Explicit accepted original hashes; additional to semantic target guards |
| `source_checksums` | SHA-256 of the game module/config/helpers and all dependency setup inputs |
| `allowed_changes` | Exact original archive entries permitted to change; no wildcards |
| `allowed_additions` | Exact necessary authored helper entries, empty by default |
| `dependencies.python_requirements` | Repository-relative pinned requirement files, empty if unnecessary |
| `dependencies.setup_script` | Optional audited Python native-tool setup hook, otherwise `null` |
| `target` | Device/geometry preference; describes intent, not a measured result |
| `evidence` | Honest static, reproduction and reported hardware evidence |

The game still implements the repository's normal `REQUIRED_ENTRIES`, `probe`
and `apply` contract. Returning a replacement does not authorize it: the shared
builder validates it against the profile, performs an independent contents
comparison, and requires the final probe to recognize the patched state.

An optional setup hook receives `--cache PATH --system Darwin|Linux --arch ARCH`
and prints only a JSON object of non-secret environment paths, such as
`{"GDRE_TOOLS": "/private/cache/gdre_tools"}`. It must reuse compatible installed
tools first, use pinned authoritative HTTPS downloads otherwise, keep caches
outside Git, preserve verification and fail clearly on unsupported hosts. Its
own source and supporting files must be pinned in `source_checksums`. This is
audited repository code, never code obtained from an APK download site. Do not
add an unrelated package manager/system modification to force a dependency to run.

Python requirement installations use a cached per-requirements/Python/CPU virtual
environment. Use the repository's pinned requirements/lockfiles. Include every
referenced constraints/requirements file in the profile's source pins. No package
installation is needed for the stdlib-only Marvel patch.

## Mac behavior and reuse

The shared bootstrap supports **Intel and Apple Silicon macOS** and x86_64 Linux
for cloud verification. It reuses the pinned Python 3.12.15, Java 21.0.13,
Android Build Tools 36.0.0 and smali 2.5.2 setup from the validated Marvel installer
without invoking or editing its game-specific launcher. Existing compatible Python
and Java are reused. Missing tools are downloaded with HTTPS and fixed checksums;
no Homebrew or administrator access is required for the base toolchain. Additional
engine dependencies must be implemented and tested per profile.

On Macs that already used the Marvel launcher, its verified cache is reused.
Otherwise tools go to `~/Library/Caches/android-4x3-workshop/`.
`APK4X3_CACHE` can select another private cache outside the checkout. Signing keys
reuse `~/Library/Application Support/android-4x3-patches/`, preserving the signing
identity from earlier locally built patches. Keep this directory private. A
different local key cannot update a distributor-signed app; warn about installation
and save implications without uninstalling or clearing anything automatically.

Outputs go to a new dated game folder under **Downloads**, with the verified APK
and a private JSON integrity/signature report. A locally generated signing key
usually changes the full APK checksum relative to a cloud build. Compare patched
content and postconditions as well as the reported local APK hash.

Example for the existing reference profile, without changing its old launcher:

```sh
bash tools/workshop-build.sh marvel-cosmic-invasion
```

For stable delivery, `command --ref <commit>` produces a source-ZIP download
command that opens the picker and builds from that exact published code revision.
The command's `ditto`, `curl` and file picker are macOS tools. It is safe to paste
paths containing spaces because the generated command quotes them and passes the
picker prompt as an argument rather than interpolating it into AppleScript.

## Validation scope

Automated tests cover input/source guards, path escapes, exact allowlists,
unrelated-content tampering, authored additions, failed post-probes, original
preservation, no-overwrite behavior, private outputs, safe command generation,
Mac picker arguments and staged binary rejection. A real synthetic APK is
aligned, signed, rebuilt and verified using Android tools; this is not a mock.

The shared runner also reproduced the existing Marvel signed APK byte-for-byte
in Linux using the same signing identity. The previously validated Marvel game
folder and launcher were not modified. All **298 repository tests passed** with
required native tests enabled in the prepared cloud environment. Its macOS
workflow and Retroid menus plus
approximately 30-minute gameplay result are owner-reported on 2026-10-25; the
new shared picker/setup is covered by mocks and host-side tests, not a new Mac or
Retroid run. The skill cannot automatically prove an arbitrary game is patchable,
and a fresh Codex session's reasoning is not an automated test result.
