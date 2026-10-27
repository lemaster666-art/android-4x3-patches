---
name: exit-issues
description: Use when the user invokes EXIT issues, ignoring ordinary capitalization, spacing or punctuation variations. Investigate and repair an Android game's Quit/Exit lifecycle, preserve saves and working presentation, and deliver a source-only one-command local Mac builder.
---

# EXIT issues

Read [the shared repair workshop](../../../workshop/repairs/README.md),
[the validated Marvel reference](../../../workshop/repairs/MARVEL_REFERENCE.md)
and relevant game documentation. Announce this skill's use. This is an
investigation/development workflow, not a universal Exit patch.

## Intake and scope

- Ask for a private/public original-APK link only if not already supplied. Reuse
  the current session's version, checksum, symptoms and earlier diagnostics.
- Inspect/download outside Git using the shared inspector. Preserve the original
  and check supplied hashes, signature, ZIP, SDK, ABI and package/version. Never
  execute the game or site scripts in the cloud. Distinguish integrity from trust.
- Default hardware context is Retroid Pocket Classic, Android 14 / API 34.
  Exit-only invocation does not authorize adding a new aspect or splash patch.
  Preserve existing working 4:3, artwork and logo behavior.
- Invocation authorizes normal private investigation, defensible game-specific
  development, testing, reproduction and code-only publication/local delivery.
  Respect narrower current instructions. Report significant protection, ABI,
  signing or compatibility problems before an invasive alternative; do not bypass
  protection or weaken browser/device security to obtain or run a build.

## Trace the real shutdown path

1. Identify engine/runtime, Android activity/protected bootstrap, graphics thread,
   audio backend and save workers. Library names alone are hints.
2. Follow Quit/Exit selection through the fade or menu action, engine Exit event,
   save cleanup, game-loop return, audio disposal and Android activity teardown.
   A black picture, Home press, Recents removal or later process kill is not
   evidence of normal Exit. A normal desktop loop return need not close Android.
3. Establish a reliable **successful** completion signal and an error path that
   retains startup diagnostics. Determine which thread may safely touch each
   resource. Do not use pixel tests, elapsed timers or a generic forced kill as
   successful-exit detection.
4. Use existing logs first. If static inspection is insufficient, collect the
   smallest focused private capture with clear steps and known ADB path. Check
   earlier reports/builds before repeating questions/captures. Separate sampled
   lifecycle data from actual visible frames and audio observations.
5. Specify cleanup ordering before coding. Saves/workers must settle before
   closing; audio handles may need capture while live if disposal drops a
   singleton. Use backend-specific stop/flush/release only when audited.
6. Close the intended Activity on the UI thread after success. Some ports need
   process termination for disposed singletons: Marvel waits for destruction of
   that exact Activity, then exits. This is a per-port decision, not a default
   requirement for every Android app. No arbitrary process-kill timeout.

## Implement, verify and deliver

- Put new adapters in separate per-game folders. Use semantic/context guards,
  original/patched/unsupported recognition and explicit archive allowlists.
  Never copy Marvel's fields, offsets, Mono APIs or FMOD calls into another game
  without independently verifying them. Preserve the working Marvel reference.
- Reuse the shared APK inspector, repacker/signing modules and cached toolchain.
  Adapt authored lifecycle/audio fixtures, not proprietary game assemblies. The
  shared `validate_exit_trace` checks ordering of engine-neutral host-test markers;
  it is not a real-device or save-integrity proof.
- Test success, failed startup, incomplete save cleanup, missing/invalid audio,
  duplicate completion, unrelated Activity destruction and re-launch. Exercise
  actual required compilers/assemblers/signing tools; report unavailable tests.
- Verify original/source pins, unchanged unrelated APK entries, approved additions,
  CRCs, alignment, signatures, package identity and key reuse. Run the full relevant
  suite including native checks. Do not weaken a guard to make an unknown APK pass.
- Follow the shared Mac delivery contract: published source ZIP, verified cached
  dependencies, local original-APK picker, new Downloads APK/report, stable private
  signer. An Exit-only builder has no PNG picker unless artwork is independently
  requested. Never transfer the cloud APK as the delivery method.
- Record static/host/reproduction/Mac/device evidence separately. Device checklist:
  Quit returns to launcher; audio stops; no hang/force-close; saves survive; relaunch
  and repeated Exit work. Record only the checks actually reported.

If combined with `4:3 time`, read its skill and reuse the intake/environment;
produce one coherent game-specific build while preserving authorized changes.
