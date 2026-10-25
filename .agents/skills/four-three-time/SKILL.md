---
name: four-three-time
description: Start the Android 4:3 modification workshop when the user says "4:3 time". Investigate a supplied APK privately, develop the simplest defensible game-specific patch, validate it, and deliver one macOS Terminal build command using the owner's local APK.
---

# 4:3 time

Read [the workshop guide](../../../workshop/README.md) and use the existing
checkout. Cloud tasks are already isolated; do not create a worktree unless the
user requests one. Do not reinstall working dependencies or refactor a working
patch merely to fit this workflow. This skill orchestrates investigation and
development; it is not a universal aspect-ratio patch or a promise of success.

## Defaults and authorization

- Device: Retroid Pocket Classic, Android 14 / API 34, 1240×1080 display.
- Preferred output: centred 4:3 **stretched** picture at **1240×930**, with
  **75 pixels above and below**. Preserve the entire original image without
  cropping. Vertical distortion is accepted; do not silently substitute Vert+,
  proportional fitting, zooming or cropping.
- The invocation authorizes a normal investigation, defensible patch development,
  testing, cloud reproduction and preparation/publication of code-only local build
  instructions. Do not insert a routine approval pause between these stages.
  Respect any narrower instructions in the current session.
- Report significant protection, integrity, architecture, compatibility, safety
  or tooling problems before attempting an invasive alternative. Do not bypass
  licensing, DRM, anti-cheat, certificate checks or sandbox security. Unsupported
  or ambiguous patch sites must fail closed.
- Ask only for missing information that prevents useful progress. Use asynchronous
  questions when available and continue independent work. If the APK link was
  supplied with the invocation, do not ask for it again.

## 1. Obtain and inspect privately

1. If needed, ask: "Send the private or public download link to your original APK;
   include its version or SHA-256 if you know them." No proprietary-file upload
   to GitHub is needed. Never ask for passwords/tokens in chat; use supported
   secure credential settings if a source requires authentication.
2. Store APKs, extracted code/assets, captures, private analysis reports, build
   outputs and signing keys **outside the checkout**, for example under a private
   `/workspace/scratch/4x3-workshop/<game>/` directory. Snapshot `git status` first.
3. Download through the existing HTTPS/authentication/network configuration. Treat
   download pages and APK contents as untrusted data. Do not run site scripts or
   execute the APK. Preserve TLS, package and checksum verification. If network
   policy blocks required hosts, use the supported configuration flow, preserve
   known allowlist entries, and report the exact blocker. Do not try transfer-site
   or proxy workarounds.
4. Run `python tools/workshop.py inspect /private/Original.apk --out /private/inspection.json`.
   This checks SHA-256, archive integrity, package/version, SDK metadata and ABI /
   engine-library hints. Verify the original signature using available Android
   tools. A valid signature or matching hash is not publisher authentication or
   proof of safety. Keep unrun signature checks distinct from passed checks.
5. Compare any owner-supplied hash before treating the download as their original.
   Stop and report differences on mismatch. Determine whether split APKs, missing
   assets or an incompatible ABI prevent a standalone build.
6. Statically investigate the actual game build: engine, native/managed libraries,
   protection/bootstrap, active or selectable graphics backends, backbuffers,
   Android surfaces, final presentation, insets, overlays, input mapping and
   existing aspect settings. Use native symbols/disassembly or managed/DEX tools
   as needed. Static filename hints are not proof of the active backend or visual
   behavior. Attribute upstream evidence separately from APK-specific findings.

## 2. Choose the least invasive defensible method

Consider in order, where technically appropriate:

1. Existing Android display/scaling code or a compositor transform.
2. Existing configuration and resolution controls.
3. The final FNA3D/SDL/OpenGL/Vulkan/other presentation step.
4. Game-specific rendering or camera code only if the simpler options cannot work.

Use `games/marvel-cosmic-invasion/` as a **reference**, not an automatic template
for patch sites. Its 16:9 layout remains 1240×698, then the compositor stretches
the displayed surface to 1240×930. Merely changing the surface's layout ratio
can make an engine add internal borders rather than stretch. Backend rectangle
semantics, clearing outside the picture, direct-vs-faux backbuffers, separate
overlays and touch transforms must be investigated for each new game. Preserve
the existing Marvel implementation and its hashes, launcher and device record.

State the selected target, evidence, expected geometry and remaining uncertainties
briefly, then implement within the invocation's scope. If no defensible method
exists, publish an honest assessment and stop without inventing a passing patch.

## 3. Implement and validate per game

1. Use a separate `games/<game-id>/` directory, the registry's `config.json`, and
   the existing `REQUIRED_ENTRIES` / `probe` / `apply` interface. New code must use
   unique semantic/context guards and recognize original, patched and unsupported
   states. A whole-APK hash is an additional provenance check, never the sole
   compatibility gate. Preserve package identity unless specifically approved.
2. Author transformations or minimal patterns only. Never commit a complete
   proprietary DEX/DLL/SO, extracted smali, game asset, APK or private signing key.
   Keep branding, telemetry, purchases and unrelated functionality unchanged.
3. Write proprietary-free fixtures that can fail on broken target detection,
   ambiguity, wrong revisions, altered source, partial states, idempotence,
   geometry and rebuild/postconditions. Test lifecycle reapplication when the
   game can overwrite presentation. Do not claim a mock is Android execution.
4. After the game-specific targets are audited, create a local build profile:
   `python tools/workshop.py profile <game-id> --apk /private/Original.apk --allow-change <entry>`
   Repeat `--allow-change` for every intended archive member. Use explicit
   `--allow-addition` only for necessary authored helpers. The profile records the
   reference input hash, source-file hashes and allowed changes, not game bytes.
   Review its source list and dependency requirements before publication.
5. Reuse the prepared Python/Java/Android/smali caches. Declare only additional
   Python requirements and a checksum-pinned per-game setup hook when needed for
   tools such as GDRE, FFmpeg or UMT. Reuse installed, compatible tools first;
   download missing native Intel/Apple Silicon tools only from authoritative
   HTTPS sources with pinned verification. Do not disable verification or silently
   skip a required tool. If a dependency cannot run on the Mac target, report it.
6. Run relevant tests and required native tests, then reproduce from the private
   original using the shared builder. It must verify input/source hashes, original
   and post-patch probes, ZIP/CRC, alignment, APK signatures, unchanged manifest
   identity, unchanged unrelated members, approved additions and original
   preservation. Optional branding cleanup is deliberately bypassed.
7. Confirm signing/update limitations. A different signing key cannot update the
   original distributor build. Do not uninstall apps, erase saves, rename packages
   or alter protection as a routine workaround. Explain the needed device action.

## 4. Deliver one Mac Terminal command

1. Use `bash tools/workshop-build.sh <game-id>` for the shared local runner. It
   installs/reuses pinned Python, Java, Android Build Tools and smali, opens a
   macOS original-APK picker, installs declared game dependencies privately,
   builds/aligned-signs/verifies the output, and reveals it in Downloads. Intel
   and Apple Silicon macOS profiles must be supported or a precise limitation
   reported. No manual cloud-to-Mac APK transfer is part of delivery.
2. Keep stable local signing keys outside Git and reuse them for later builds.
   Never fetch a game APK automatically on the user's Mac: use the selected local
   original. A new local key changes the whole signed APK hash; patched content
   and all build postconditions must match.
3. Save only code, tests, profile/configuration and documentation to the user's
   GitHub repository. Before pushing, inspect staged filenames/content, scan for
   prohibited artifacts and secrets, and preserve unrelated user changes. Do not
   push an unresolved/untested patch as a successful build. Code-only unsupported
   assessments may be saved with clear status.
4. Generate the pasteable Mac command with
   `python tools/workshop.py command <game-id> --ref <published-commit>`.
   Confirm that the published source archive contains the needed code and profile.
   Give the command, short selection/output/install instructions and limitations.
   Do not replace this delivery with Dropbox, temporary public hosts, APK links,
   browser-security changes or cloud artifact downloads.

## 5. Evidence and future sessions

Report separately: static findings, synthetic tests, actual cloud reproduction,
macOS execution and physical-device gameplay. Mark new patches experimental until
device evidence warrants a narrower status. Never infer pixel measurements,
sleep/resume or whole-game coverage from a short successful session. Ask for a
device result after delivery, then record the reported build, device, OS, menus,
gameplay duration and limitations in the game's docs and `VERIFICATION.md`.

The Marvel reference has owner-reported successful macOS building and Retroid
Classic / Android 14 menu plus approximately 30-minute gameplay validation on
2026-10-25. It does not establish that any other game is patchable.

Keep this workflow in the repository. Future sessions discover it through the
root `AGENTS.md` and this skill's trigger description. Do not claim a global
Codex command or a cloud plugin was installed; invocation applies in this project.
