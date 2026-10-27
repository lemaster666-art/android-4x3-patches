# Marvel Cosmic Invasion: combined startup and Exit experiment

**New optional loading-animation candidate:** see [LOADING_ANIMATION.md](LOADING_ANIMATION.md)
for the private kit picker (`--loading-animation`), unchanged startup timings and
handheld acceptance checks. This opt-in animation is **awaiting handheld validation**;
the successful status-bar repair below retains its validated reference status.

This is a separate, opt-in local builder. It preserves the working
`games/marvel-cosmic-invasion/` patch and its original one-command Mac launcher.

**Hardware validated: status-bar flash eliminated.** On **2026-10-27**, the owner
confirmed successful Retroid Pocket Classic / Android 14 testing of
[`6cbe39a7f5ad14911f1d2dc3f4a82ee35cb7c82c`](https://github.com/lemaster666-art/android-4x3-patches/commit/6cbe39a7f5ad14911f1d2dc3f4a82ee35cb7c82c).
The splash-scoped window-style guard is now a validated repair alongside the
custom PNG, developer-logo handoff/timing, 4:3 presentation and Android Exit/audio
cleanup. These are owner-reported hardware successes for this supported build,
not host-only claims or universal compatibility. The working source, tests and
Mac launcher are tracked by the [repair reference profile](../../workshop/repairs/marvel-cosmic-invasion.json),
which retains the validated hashes separately from authorized candidate changes.
Future sessions can use `STARTUP&EXIT ISSUE`; see the
[reusable technical reference](../../workshop/repairs/MARVEL_REFERENCE.md).

The paragraphs below retain the earlier investigation history. Previous failed
attempts and unverified candidates are superseded by that hardware result.

**Main-menu Exit is device-validated on the supported port.** On 26 October 2026,
the owner tested the local build from commit
`f7799e29a8346aefa8028cc9dc19c00afa69000f` on a Retroid Pocket Classic running
Android 14 and confirmed that Exit closes the app properly, with no continuing
audio, black-screen hang or manual force-close required. This is the accepted
Exit implementation for this build/device; it remains in this separate builder.

In that validated revision the selected PNG stays at its stable 4:3 size until
the original developer logos appear, but the Android status bar (time/date UI)
briefly appears during startup. The owner did not separately confirm the exact
fade duration or every logo frame/audio cue. Saved-progress checks, repeated
relaunch and pause/resume during loading were not separately reported.

The owner also tested revision `81cec6a94dd6c9b7be54c01c33d613b14f77a8f4`:
USB update installation from the Mac and the 500 ms fade worked, but the status
bar still appeared **over the PNG**. Setting `TOAST_WINDOW` to `ignore` succeeded
yet the startup toast remained. Neither attempt is recorded as a fix for its
respective issue.

**Preserved startup presentation.** At the owner's
request it uses a 500 ms PNG fade-in, then keeps the image fully visible during
loading. Once the first logo frame is ready, it fades out for **two seconds**,
holds **full black for 500 ms**, then releases that frame. The extra 2.5 seconds
are deliberate presentation time after readiness, not necessary loading time.

The previous full-screen candidate copied the original shim's flags into an
additional startup controller. The owner still observed the bar in the first
two seconds of the PNG, so that candidate **did not resolve the flash**. A
private capture showed the game window already full-screen and the status bar
marked hidden in all 28 samples containing that window. This does not identify
the pixels visible during the reported flash. Timed screenshots did not catch it.

The controlled regression build `9787a9c` removed the helper's extra window
handling; the owner reported that this also did **not** stop the flash. The
first flash report in the conversation followed `f7799e2`, when the frame/Exit
hooks first attached successfully. Its Java splash code was identical to the
preceding `c91ccb8`; this identifies the first reported boundary, not the cause.

**Video evidence, 27 October 2026:** a private startup clip shows the PNG first
appearing with no status-bar text. Roughly 1.4 seconds later, the Android clock
and battery bar reappear for about 0.17 seconds, then hide again while the toast
remains. Timing is approximate and comes from this clip, not the earlier window
capture. This identifies a real, brief SystemUI bar return after the PNG appears;
it does not by itself identify which callback requested it. It also explains
how periodic snapshots can miss the event. Only written findings are retained;
the downloaded video and extracted review images were deleted after review.

**Validated narrowly scoped repair:** the original Android window-style handler has
a windowed branch that shows bars, clears `FLAG_FULLSCREEN` and enables
`FLAG_FORCE_NOT_FULLSCREEN`. The original display shim schedules re-hide after
150 ms when fullscreen visibility is lost. That mechanism is consistent with the
observed flash but is not a device-traced causal proof. A guarded patch now
filters the handler's valid Integer style argument: zero (windowed) becomes one
(fullscreen) only while the authored PNG splash is active and startup has not
failed. The existing fullscreen branch writes all flags; no extra window
observers or re-hide timers are added. Before attachment, after dismissal/detach
and on startup failure, the original argument and behavior are preserved.

This changes the Android Java presentation bridge, **not the native SDL3/FNA
libraries**, game rendering size, camera, original managed code, protected
lifecycle, manifest, accepted Exit helper or fade timings. The circular-icon
launch screen is unchanged. The guard records one diagnostic line when it
actually intercepts a windowed request. The owner has now physically confirmed
that this implementation eliminates the flash on the named device. Each new APK
or device still needs its own validation; no additional screenshot capture is
needed to establish this reported success.

This is owner-reported physical-device validation, distinct from host tests and
cloud packaging checks. It applies to the exact supported APK and device, not
every Android port. The overall optional builder retains its experimental name
while the startup issue and broader compatibility checks remain open.

The earlier combined build failed to attach both hooks because the authored
helper looked up `AudioManager._studioSystem` as non-public, while the original
assembly declares it public. The corrected lookup and matching host fixture
reproduce the failure before the fix and pass afterward. The corrected revision
passed all 309 automated tests and cloud signing, alignment and member-integrity
checks before this device test. No loading timer was extended and the working
4:3 patch remains unchanged. Raw device logs stay private.

## Build on your Mac

Requires Intel or Apple Silicon macOS **12 or newer** and the private signing
identity previously created by your working Marvel local build. Save your
replacement artwork as an original PNG on your Mac. Run this one paste:

```bash
marvel_test_tools=$(mktemp -d) &&
curl -fL https://codeload.github.com/lemaster666-art/android-4x3-patches/zip/refs/heads/main -o "$marvel_test_tools/tools.zip" &&
ditto -x -k "$marvel_test_tools/tools.zip" "$marvel_test_tools" &&
bash "$marvel_test_tools/android-4x3-patches-main/experiments/marvel-startup-exit/build-local.sh"
```

Choose your **original APK**, then your **replacement PNG** in the two Mac file
pickers. It creates a dated `Marvel-4x3-startup-exit-*` folder in Downloads with
one signed experimental APK and its integrity report, then reveals it in Finder.
Your artwork stays local and is copied into that APK without cropping or editing
the original PNG. No APK or image is sent to Codex/GitHub by this command.

Java, Android Build Tools and smali reuse the existing Marvel cache. The first
experimental build also downloads checksum-pinned .NET SDK 8.0.427 (compiler
only), Zig 0.13.0 (Android cross-compiler) and Android API 34 compile headers.
Those tools are cached for later builds. No Homebrew/admin access is required.
The downloaded SDK/tool archives are verified before extraction/execution.

The original input must match SHA-256:
`d0c9587575f5bba17a5ac2f5ea3e56700b362f658aaaff84ae11c9b67eae18c9`.
A patched APK or another distributor/version stops before dependency setup.
The PNG must have valid chunk CRCs, be at most 32 MiB and fit the bounded decode
size (maximum 4096 in either dimension and 12 megapixels).

## Included behavior

- The proven gameplay SurfaceView transformation is unchanged. Its final
  `classes2.dex` must remain
  `0accefb0c85def38839d3e3015d130967a21b7545869f6cefcd7efc23bcc2fe1`.
- The custom splash displays the **entire selected PNG** stretched into a
  centered 4:3 rectangle: 1240 x 930 with 75-pixel top/bottom borders when its
  full-screen View is 1240 x 1080. The original Android window handler owns
  flag/insets writes; its windowed-style argument is guarded while PNG is active.
  It has a 500 ms fade-in, no zoom/gradient/title/port-credit/donation button,
  and no promotional tap target. No extra window listeners are installed.
- Splash dismissal is triggered by a matching game-frame callback, replacing
  the seven-second dismissal timer. The PNG fades to its black backdrop over
  **2000 ms**, holds full black for **500 ms**, then lets the original graphics
  manager present the first drawable LogoScreen frame. Canvas redraws drive the
  fade independently of Android's animation-scale setting. The hold starts when
  zero-alpha artwork is actually drawn; a delayed redraw cannot shorten it.
  This is a fade to black followed by the original logos, not
  a crossfade that starts the logos underneath the artwork.
  The game timer is reset after this short wait, preserving subsequent animation
  progression. A non-drawing/paused view recovers after 4000 ms; the game-thread
  wait is bounded to 4500 ms and reports unsuccessful handoff on recovery.
  No developer-logo assets or logo game code are modified.
- After the original bootstrap returns normally and a game Exiting event was
  observed, the helper stops FMOD events, flushes commands and releases its
  captured Studio system. It then finishes/removes the Android activity on the
  UI thread. After that activity is destroyed, a lifecycle callback performs
  a normal `System.exit(0)` so a new launch cannot reuse disposed FNA/Mono
  singletons. There is no arbitrary process-kill timer, pixel-based Exit test,
  or Exit action on failed startup.
- The original Android circular-icon launch screen and APKVision distributor
  toast are separate components and remain present in this two-change test.

This does not claim to make game loading faster. It aims to cover the observed
pre-logo gap with artwork and provide a complete successful-exit lifecycle.
The timeout is a **60-second recovery fallback**, never the normal readiness
signal. If the helper cannot initialize, it reveals the original game/error
screen and retains the original Java game entry point where possible. Such a
fallback is not a successful modification and must be reported during testing.

## How the guarded integration works

The original APK's native/AOT libraries, managed assemblies, content, developer
logos, manifest and distributor/protection components remain byte-for-byte
unchanged. The unchanged 4:3 display patch is applied through its existing module.
A second, authored helper is built from the sources here:

1. An unprotected Java `SpexApplication.startGame` wrapper first attempts the
   authored bridge, retaining the original `n_StartGame` fallback. Original
   native registration and protected lifecycle methods are left intact.
2. A small authored ARM64 JNI library opens the already-initialized, exact
   original Mono runtime with `RTLD_NOLOAD` and resolves its embedding APIs.
   It loads the authored managed helper from an opaque `.bin` asset. This avoids
   adding an assembly to the port's fixed 96-entry bundled-assembly table.
   The audited original runtime uses hybrid AOT/JIT; no AOT disabling or rewrite
   is performed. Missing APIs reject the enhancement before its worker starts.
3. The managed helper invokes the original `SpexBootstrap.Run` on the original
   style of background game thread. A synchronous NLog target receives the
   audited `startinit: after LoadFonts` call, before the initial context load
   and frame loop's first draw. This installs a pass-through
   `IGraphicsDeviceManager` wrapper using the mutable instance field. It does
   not modify FNA's read-only platform delegates, cameras, buffers or viewports.
4. Before presentation, the wrapper checks the same conditions the audited
   context renderer uses to draw: no context-loading thread, a LogoScreen
   current context and a fade state other than fully faded out. Its first
   matching frame triggers the UI fade and a bounded acknowledgement wait;
   original `EndDraw` always runs. There is no log-file polling or readiness
   estimate based on a fixed elapsed loading time.
5. Audio is captured while live, because the original disposal path drops its
   singleton reference without releasing the underlying Studio system. Extra
   cleanup is gated behind successful game completion, after save cleanup has
   returned. The existing failure/diagnostic path does not close the activity.
6. A unique, audited decision in
   `SDLActivity$SDLCommandHandler.handleMessage` calls the authored
   `splashWindowStyle(int)` after the original Integer unboxing and before its
   fullscreen/windowed branch. All other method instructions remain original.
   Non-Integer fallback, keyboard/title/keep-awake commands, original insets
   notification and calls after the splash retain their original handling.

The reusable lesson for desktop-to-Android ports is to connect successful game
loop completion to Android activity teardown: a desktop-style return from the
game loop alone may leave the Android window and native audio alive. In this
port, cleanup waits for both the Exiting event and normal bootstrap return with
no recorded game error, then stops/releases audio and closes the activity on the
UI thread. This ordering is now device-validated here. Other ports require their
own audited completion, save and audio lifecycle; these private field names and
callbacks are not a universal patch.

`SplashView.java` is an **authored compile-only signature stub**, not copied
original code. Its `.class` is explicitly excluded from the packaged helper
DEX; only the original, guarded SplashView is shipped with targeted methods.
`dl_stub.c` is a link-only import stub and is never included in the APK. Android
supplies its real system `libdl.so`. All source here is patch/helper code; no
original game assemblies, libraries, images or APKs are committed.

The owner's corrected-build test confirms successful startup and the observable
Exit result on the named device. Resume during loading, exact first-logo/audio
timing, repeated relaunch and other devices still require separate checks.
If protection or startup fails, collect diagnostics and return to the existing
working 4:3 APK. Do not disable protection or replace original game libraries.

## Signing, installation and comparison

The builder **requires and reuses** the signing files from the working local
Marvel build under:
`~/Library/Application Support/android-4x3-patches/`
(or your existing `XDG_DATA_HOME`). It stops if these are missing; it does not
silently generate a new identity. Keep that private folder and the working APK.
No signing credentials belong in GitHub.

Install the new APK **as an update** to the locally signed working game. The
package identity and version remain unchanged. If Android reports a signature
conflict, stop and report it; do not uninstall your working game to work around
it. The local report includes the new signer certificate SHA-256.

Compare with the working APK on the Retroid Pocket Classic / Android 14:

1. Cold launch: correct complete PNG, stable 4:3 size, no added text/button/zoom.
2. Loading: artwork covers the previous black gap; first Tribute logo appears
   from its beginning, followed by the complete original logo sequence/audio.
3. Pause/resume during loading and gameplay: no stuck overlay or lost controls.
4. Main-menu Exit: return to launcher, music stops, task closes.
5. Launch again, check saved progress and confirm a second normal Exit.

If a test fails, preserve the working APK and report the behavior. The authored
helper appends its diagnostic phases to `android4x3-enhancements.txt` in the
same app external-files directory used by `spex-boot.txt`. Retrieve it privately:

```bash
"$HOME/Downloads/platform-tools/adb" pull /sdcard/Android/data/com.jayeldragon.marvelcosmic.preview/files/android4x3-enhancements.txt "$HOME/Downloads/android4x3-enhancements.txt"
```

No game content or diagnostic captures are published by the build scripts.
When the new style guard executes, the same private file contains
`startup windowed-style request kept Android full-screen while PNG active`,
prefixed with device uptime. It logs once per splash; absence of that line means
the capture does not establish that the guarded path was reached. Diagnostic
file-write failure does not prevent normal command handling.

## Capture the early status-bar flash without rebuilding

Close Marvel with its working **Exit** option, connect and unlock the Retroid,
and authorize USB debugging if prompted. This diagnostic helper uses the
installed APK. It does not rebuild/install anything, force-stop the game, change
settings or clear saves/logs. It refuses to start if Marvel is still running.

From a downloaded source archive, run:

```bash
bash experiments/marvel-startup-exit/capture-status-bar.sh
```

It takes a window/insets baseline, launches Marvel normally, then captures 30
window/display snapshots with device time and uptime markers. Leave the device
untouched until it finishes. The single private `marvel-status-bar.txt` file is
saved in a dated `marvel-status-bar-*` folder in your Mac's Downloads and
revealed in Finder. Share it privately in the chat; the script uploads nothing
and refuses an output directory inside the source checkout. No APK, artwork,+screenshot, video or save content is collected. Window dumps may include other
visible app/window names, so keep the capture private.

The capture is intended to distinguish the game's requested full-screen state
from Android's actual bar visibility and window/control ownership. Sampling
adds diagnostic overhead and is not an untouched loading-time benchmark.
The helper's host tests use authored ADB responses; its output still needs to
be collected and reviewed from the real Retroid. Optional developer arguments
are `--adb /path/to/adb` and `--output-dir /private/new-capture-directory`.

## Optional per-game toast restriction through ADB

This device setting is separate from the APK build. With the Retroid connected
over USB, unlocked and authorized for USB debugging, paste this once in your
Mac Terminal (using the previously installed Downloads/platform-tools):

```bash
marvel_adb="$HOME/Downloads/platform-tools/adb" &&
"$marvel_adb" shell cmd appops set com.jayeldragon.marvelcosmic.preview TOAST_WINDOW ignore &&
"$marvel_adb" shell cmd appops get com.jayeldragon.marvelcosmic.preview TOAST_WINDOW
```

Look for `TOAST_WINDOW: ignore`, then close Marvel normally and launch it again.
This targets only this game's toast windows, not the entire device. It changes
neither the APK nor its saves, and requires no root. **The owner tested this on
the Retroid: the operation reported `ignore`, but the startup toast still
appeared. It is not a working suppression method for that observed toast.**
Android 14 can render text toasts in SystemUI rather than the game's own window;
the confirmed result is consistent with that limitation, but does not by itself
prove which code creates this toast. Disabling notification permission also
does not reliably block a foreground app's toasts.

To remove this override and restore Android's default policy, paste:

```bash
"$HOME/Downloads/platform-tools/adb" shell cmd appops set com.jayeldragon.marvelcosmic.preview TOAST_WINDOW default
```

If ADB reports an error, preserve the exact message. Do not treat a rejected
setting or a remaining toast as a successful suppression. Android 14 source:
[toast-window app-op enforcement](https://github.com/aosp-mirror/platform_frameworks_base/blob/android-14.0.0_r1/services/core/java/com/android/server/wm/WindowState.java),
[toast presenter attribution](https://github.com/aosp-mirror/platform_frameworks_base/blob/android-14.0.0_r1/core/java/android/widget/ToastPresenter.java)
and [foreground toast policy](https://github.com/aosp-mirror/platform_frameworks_base/blob/android-14.0.0_r1/services/core/java/com/android/server/notification/NotificationManagerService.java).

## Verification and developer checks

Every build verifies the supported original's hash, archive CRCs and signature,
then verifies output ZIP integrity, alignment, APK signatures, package identity,
unchanged inputs/signing-key file and every original APK member. Exactly
`classes.dex` plus the baseline `classes2.dex` change; exactly four authored/user
payload entries are added. The remaining **3238 original non-signature entries**
must match byte-for-byte, including every original managed/native library and
logo/video asset. A newly generated build report keeps `device_tested_this_build`
false because the builder performs no physical-device test. The subsequent
owner-reported result for the named revision is recorded above and in
[the project verification record](../../VERIFICATION.md#marvel-cosmic-invasion-startup-and-exit-follow-up).

Cloud packaging verification uses authored, proprietary-free test artwork,
because the user's PNG is selected locally on the Mac. It does not claim that
synthetic artwork is the user's image or that cloud compilation runs the game.

Developer tests include independent PNG/LZ4 corruption checks, unsupported
source/target rejection, member-tamper rejection, authored managed callback
execution with dependency doubles (successful Exit, failed startup, failed
handoff), JNI ABI checks against JDK headers, JNI/Mono loader argument/error
execution with authored doubles, and Java destruction/exit ordering. These
host tests cannot establish Android runtime behavior.

The window-command follow-up passed **316 automated tests** and a fresh private
rebuild/sign/alignment/integrity check. An executable Java UI harness checks
the 500 ms fade-in, monotonic 2000 ms alpha reduction and a full 500 ms black
hold before game release, including when the first black redraw is delayed, a
fully visible PNG during loading, unchanged complete-source 4:3 bounds,
no direct helper window-flag/insets writes at attach, focus changes and handoff,
preservation of existing SDL observers/callbacks, pre-API-30 behavior and safe
paused/detached recovery. The Java harness executes the guard before attachment,
during PNG and black hold, on failure and after dismissal/detach, checks that
nonzero arguments pass through, and verifies one diagnostic line per splash.
The smali test verifies that only the audited style decision gains a call and
rejects unknown/already-patched contexts. Actual APK assembly exercises the
original guarded method. Against the previous controlled cloud reference,
only `classes.dex`, `classes3.dex` and signature metadata change: the managed
helper, native bridge and baseline `classes2.dex` remain byte-for-byte identical.
This is host/package evidence, supplemented by the owner's **2026-10-27 physical
confirmation that the status-bar flash is eliminated**. The workflow/knowledge
update adds no runtime changes to that validated source.

With a private .NET SDK and JDK prepared, run the complete tests with:

```bash
MCI_DOTNET=/private/dotnet/dotnet MCI_JDK=/private/jdk \
ANDROID4X3_REQUIRE_NATIVE_TESTS=1 python -m pytest -ra
```

The existing baseline launcher and its tests remain unchanged.
