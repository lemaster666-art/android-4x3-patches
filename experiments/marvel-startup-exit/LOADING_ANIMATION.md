# Optional purple-neon loading icon — candidate

**Awaiting handheld validation.** The underlying status-bar repair remains
**hardware validated: status-bar flash eliminated**, reference
`6cbe39a7f5ad14911f1d2dc3f4a82ee35cb7c82c`, Retroid Pocket Classic / Android 14.
This animation has host regression and private APK packaging checks; those are
not a physical test of its appearance or disappearance timing.

## What changes

The existing `EnhancedUi.draw` Canvas path draws the kit's transparent production
sheet. No new window, Activity, fullscreen controller, native hook or glow effect
is added. The sheet is decoded once at attachment, ARGB_8888 with `inScaled=false`.
Drawing reuses a source Rect, destination RectF and separate unfiltered Paint;
it does not decode images or create cropped bitmaps per frame. Android's default
premultiplied bitmap blending handles transparency normally.

Forty row-major 160×160 cells (8 columns, 5 rows) advance using monotonic uptime:
`((now - attachedAt) / 50) % 40`. A steady-loading redraw is requested at the next
50 ms frame boundary after the initial fade-in. Existing fade redraws remain in
place. Missed frames are skipped; there is no catch-up loop or minimum icon time.

The complete frame maps `(1104,800)–(1264,960)` on a 1280×960 reference through the
existing centered 4:3 destination rectangle. On the Retroid's 1240×1080 window the
frame is `(1069.5,850)–(1224.5,1005)`, size 155×155. The padded 128-pixel core
keeps a 32-reference-pixel right margin and 16-reference-pixel bottom margin.
This follows the owner’s second placement preview: 16 reference pixels lower
than the kit’s original frame position, with size and horizontal placement retained.
These are content coordinates, not dp or whole-window placement. Nearest sampling preserves the
pixel-art character; fractional panel scaling is unavoidable at 1240 pixels.

The icon and halo draw only for the current attached splash, with available
assets, no startup failure and `fading == false`. The **unchanged existing UI
handoff** sets `fading=true`, so the first subsequent draw has neither icon nor
halo, even when fade-out alpha is still 255. No delayed visibility callback can
restore it. The current splash reference, handoff latch and fullscreen guard
remain active through the existing fade and black hold.

**No startup timing changes:** 500 ms fade-in; existing actual first-logo-frame
readiness trigger; 2000 ms fade-out; 500 ms black hold from its first actual black
draw; original developer-logo handoff. The 4000 ms fade-recovery, 4500 ms game
wait and 60-second startup-recovery bounds are unchanged. No rotation/pulse
completion wait, minimum icon display duration or extra logo delay is imposed.
The small one-time asset decode is initialization work, not a new timing gate.

Missing, null, wrong-sized or out-of-memory animation decoding disables only
the icon. The PNG, readiness, fullscreen guard and Exit continue normally.
Existing dismissal, failure and detachment cleanup recycle the animation sheet.
Queued invalidations cannot draw a stale splash or revive an icon after fading.

## Build locally on Mac

Keep the original APK, your existing splash PNG and `xmen-purple-loading-kit.zip`
on your Mac. The kit is private input, never a repository download. It need not
be unzipped. Use the existing builder with **`--loading-animation`**:

```bash
marvel_tools=$(mktemp -d) &&
curl --proto '=https' --proto-redir '=https' -fL https://codeload.github.com/lemaster666-art/android-4x3-patches/zip/refs/heads/main -o "$marvel_tools/tools.zip" &&
ditto -x -k "$marvel_tools/tools.zip" "$marvel_tools" &&
bash "$marvel_tools/android-4x3-patches-main/experiments/marvel-startup-exit/build-local.sh" --loading-animation
```

Choose the **original APK**, **existing splash PNG**, then **loading kit ZIP**.
The same cached tools, private signing key and Downloads output folder are used.
The builder reads only the approved sheet from the kit; it never executes its
scripts or extracts its other files. The GIF/APNG are previews, not APK payloads.
The command uploads nothing. For a reviewed candidate, pin the source ZIP to its
full published commit instead of `main`; Codex supplies that exact command.

For noninteractive invocation, pass `--loading-kit /private/path/to/kit.zip` with
the existing `--apk`, `--artwork` and optional `--output` arguments. Omit both
animation flags to retain the plain-PNG build without an animation asset/picker.
Do not uninstall or clear data: use the usual same-key `adb install -r` update.
A signing conflict must stop installation rather than deleting the working app.

## Integrity and validation

Approved sheet SHA-256:
`3b92064ab579b3cd746718e3409f2b669f92c19cdbc7b4007b37a2f363d4139a`.
The bounded ZIP reader rejects missing/duplicate entries, unexpected sheet bytes
and oversized input before tool installation. Only that sheet is read; no path
in the ZIP is extracted. The kit and original APK are checked unchanged afterward.

In addition to the existing four authored payloads, an animation-enabled APK adds
exactly `assets/android4x3/xmen-neon-sheet.png`. Original archive changes remain
only `classes.dex` and `classes2.dex`; all 3238 other original non-signature
members stay identical. The guarded window-style transformation and 4:3 DEX
output remain unchanged. ZIP CRC, identity/version, alignment, signatures,
payload bytes and existing-key/original-art preservation checks still apply.

The repair profile retains the original 28 reference hashes separately as
`validated_source_checksums`; current pins cover the explicitly authorized
renderer/builder/test changes plus new animation tests. Host tests freeze the
validated window-style guard and handoff method blocks and timing constants.
No working managed Exit/audio, JNI, protected Activity or baseline 4:3 source
is changed. User kit/artwork, original/modified APKs and signing keys stay private.

On 2026-10-27, **374 tests passed**, including required native checks, with no
skips (43.72 seconds). Executed Java tests cover steady loading, 50 ms frame
boundaries/row transitions/two-second wrapping, multiple content offsets/sizes,
early readiness without a minimum icon interval, fade-start disappearance,
black-hold fullscreen guard lifetime, pause/detachment, late invalidations and
missing/null/wrong-size/out-of-memory sheet fallback. A private signed candidate
using the exact approved kit and synthetic background passed the established
APK checks. No Android game execution or handheld validation occurred in cloud.

Handheld acceptance: observe a sharp yellow icon with its baked-in purple halo
during loading, normal transparent blending, correct margins and continuing
animation after the PNG fade-in; confirm that **both icon and halo vanish at
fade start**, never return on pause/resume, and do not affect fade/black/logo
timing, bar-flash elimination, 4:3 gameplay or Exit/audio cleanup. Only after the
owner confirms this candidate should the animation technique be promoted into
the `STARTUP&EXIT ISSUE` skill.
