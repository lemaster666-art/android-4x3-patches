---
name: startup-exit-issue
description: Use when the user invokes STARTUP&EXIT ISSUE or ordinary capitalization, spacing and punctuation variations. Investigate Android startup/splash/loading transitions and Exit, preserve original developer logos and working aspect patches, and deliver a verified local Mac builder.
---

# STARTUP&EXIT ISSUE

Read [the shared repair workshop](../../../workshop/repairs/README.md),
[the validated Marvel reference](../../../workshop/repairs/MARVEL_REFERENCE.md)
and the [Exit workflow](../exit-issues/SKILL.md). Announce use of this combined
skill; include the Exit investigation once. Apply the intake, privacy, guard,
testing and local-delivery requirements there. Do not invoke `4:3 time` unless
combined/requested; preserve an existing working aspect patch.

## Map startup before changing it

1. Identify the Android system launch/icon screen, theme/window background,
   custom Android splash View, static artwork, video, engine-rendered logos and
   distributor toast/other overlays separately. Text may be drawn in code rather
   than embedded in an image. Inspect the actual package/resources and call path.
2. Build a timeline: Activity displayed is not first game-rendered frame. Separate
   essential initialization, deliberate minimum display time, cosmetic fades,
   black gaps and engine logo animation. Covering loading is not speeding it up.
3. Preserve the complete original developer logo image/sound/animation sequence
   unless the owner explicitly requests a change. Show replacement PNG only in
   the authorized custom splash. Do not hide running logos underneath artwork.
4. Determine the earliest safe artwork display and a reliable loading/rendering
   callback for dismissal. In Marvel a pre-presentation callback holds the game
   while the UI finishes its fade, then resets elapsed game time. Verify another
   engine's contract independently, including audio timing. A callback/signature
   in an upstream source tree does not prove that the APK executes it.
5. Keep handoffs bounded and fail open to the game's diagnostics when startup or
   rendering integration fails. Test paused/detached views, resume, cancellation,
   unknown fields and unavailable runtimes. A recovery timeout is not readiness.

## Validated technique: prevent a show-bars request at its source

Marvel reference commit:
[`6cbe39a7f5ad14911f1d2dc3f4a82ee35cb7c82c`](https://github.com/lemaster666-art/android-4x3-patches/commit/6cbe39a7f5ad14911f1d2dc3f4a82ee35cb7c82c).
Status: **hardware validated: status-bar flash eliminated**, Retroid Pocket
Classic / Android 14, owner confirmation on 2026-10-27.

- Inspect fullscreen/windowed commands, first surface creation, focus changes,
  bar/insets ownership and any existing delayed re-hide **before** layering on
  immersive-mode requests, observers or timing changes.
- The audited Android Java window-style handler could show bars for a windowed
  request; the original shim re-hid them about 150 ms later. A private video caught
  a roughly 0.17-second return of the actual clock/battery bar after PNG appeared.
  Periodic window snapshots and screenshots missed the event. Do not contradict
  a visible report solely because samples say the bar was hidden.
- The validated transformation inserts a call to authored
  `EnhancedUi.splashWindowStyle(int)` in
  `SDLActivity$SDLCommandHandler.handleMessage`, after valid Integer unboxing and
  before the existing fullscreen/windowed decision. While PNG is active and
  startup has not failed, zero becomes one, using the original fullscreen branch.
  Nonzero values and all commands outside the splash retain original behavior.
- Preserve failure/detachment/dismissal guards, one-per-splash private diagnostic,
  strict original/context checks and unrelated handler instructions. No extra
  immersive observer/re-hide loop or native SDL/FNA modification is needed here.
- Inspect the corresponding path for each new APK. Do not blindly patch every
  windowed command, assume a specific command number or apply Marvel labels/offsets
  to another handler. Scope any guard to its actual custom splash lifecycle.

## Validated technique: animate inside the existing splash drawing path

Marvel animation reference:
[`0aa257e003090fcf0f08b110b36c55775a814908`](https://github.com/lemaster666-art/android-4x3-patches/commit/0aa257e003090fcf0f08b110b36c55775a814908).
Status: **hardware validated: loading icon works as intended**, owner confirmation
on 2026-11-02, Retroid Pocket Classic / Android 14. The owner reported success in
its intended operation; this is not a frame-by-frame timing measurement or a
separate confirmation of every pause/resume and failure case. Preserve this
working implementation alongside the validated status-bar and Exit repairs.

- Extend the existing custom splash Canvas path rather than adding a window,
  Activity, fullscreen controller or native rendering hook. Decode the approved
  transparent sprite sheet once as ARGB_8888 with density scaling disabled.
  Reuse source/destination rectangles and a separate Paint with bitmap filtering
  explicitly disabled. Do not decode/crop bitmaps per draw, premultiply twice or
  add another pulse/glow already baked into the asset.
- In Marvel, 40 row-major 160px cells (8 columns by 5 rows) use monotonic uptime
  in 50ms steps, wrapping every two seconds. Continue lightweight redraws during
  steady loading after fade-in, skipping missed frames. Map reference pixels
  through the centered 4:3 destination rectangle, including its offset. The
  owner's final frame position is (1104,800) on a 1280x960 reference; do not
  confuse it with the kit's earlier (1104,784) or with Android dp/window bounds.
- Draw only for the current attached splash, with an available sheet, no startup
  failure and `fading == false`. The existing UI-thread readiness handoff sets
  `fading=true`; the first subsequent redraw contains neither icon nor halo.
  Do not fade the icon with the artwork, finish its loop or impose minimum
  visibility. Keep fade-in, readiness, fade-out, black hold, recovery bounds and
  original developer-logo handoff unchanged.
- Hiding the icon must not clear the splash reference, finish the splash,
  release the handoff latch or disable the fullscreen guard. The guard continues
  through fade and black hold. Existing cleanup paths recycle the sheet; missing,
  invalid or unavailable animation assets disable only the icon. Late callbacks
  must not restore it after fading, failure or detachment.
- Keep kit/artwork private. Reuse the local Mac picker for original APK, clean
  splash PNG and kit ZIP, preserving the existing signing key. Read only the
  bounded checksum-pinned sheet; never execute kit scripts or package previews.
  Retain the authored animation tests, fullscreen/handoff tests and exact APK
  member checks. See [the implementation and validation record](../../../experiments/marvel-startup-exit/LOADING_ANIMATION.md).
- Other games need their own verified splash lifecycle and fade-start call path;
  this validation does not establish universal engine/device compatibility.

## Artwork, comparison and delivery

- Let the user select the original PNG locally on Mac. Verify format/bounds,
  preserve the complete intended image and stable layout. User artwork stays
  private; use synthetic artwork in cloud tests when necessary.
- Default device remains Retroid Pocket Classic / Android 14. Preserve the known
  1240×930 picture and 75-pixel borders when the game already has that 4:3 patch.
  Do not introduce crop, stretch or camera changes under a startup-only request.
- Confirm the last known successful revision from existing conversation/device
  records. Compare exact sources and change one relevant behavior at a time.
  Reverting an entire APK may also revert working Exit: disclose that consequence
  and prefer isolated tests. Do not keep asking for transient screenshots once
  they fail to catch the event; use one targeted short clip when genuinely needed.
- Delete downloaded private review video/frames after review when requested;
  retain written findings only. Never publish captures or extracted game content.
- Keep the Exit repair and current fade timing unchanged when investigating a
  bar regression. Test the specific cause and distinguish candidates from the
  hardware-validated result. The Marvel guard is now a validated reference.
- Deliver through the shared one-command Mac source/build workflow. Add a PNG
  picker only for a repair needing custom artwork. Keep signing identity and
  report any update conflict without uninstalling or clearing data automatically.
