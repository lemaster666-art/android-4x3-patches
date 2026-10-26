# Marvel Cosmic Invasion: combined startup and Exit experiment

This is a separate, opt-in local builder. It preserves the working
`games/marvel-cosmic-invasion/` patch and its original one-command Mac launcher.
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

**Current startup-only follow-up needs a new device test.** It adds a 500 ms
readiness-triggered PNG fade to black and restores immersive mode at focus and
handoff boundaries. Its bounded startup observers leave SDL's existing listeners
intact. These address the reported presentation issues without changing the
accepted Exit helper, native bridge or display DEX. The precise cause of the
original status-bar appearance remains unconfirmed; SDL can reset full-screen
flags during startup and its own re-hide callback waits two seconds.

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
  full-screen View is 1240 x 1080. It requests immersive mode before drawing.
  It has a 250 ms fade-in, no zoom/gradient/title/port-credit/donation button,
  and no promotional tap target. Additional window-focus and pre-draw observers
  restore hidden system bars during startup, including when only the status bar
  becomes visible. They do not replace SDL's listeners, alter surface geometry
  or disable Android's normal swipe access to system bars after startup. They
  are removed two seconds after handoff, or immediately on splash detachment.
- Splash dismissal is triggered by a matching game-frame callback, replacing
  the seven-second dismissal timer. The PNG fades to its black backdrop over
  **500 ms before** the original graphics manager presents the first drawable
  LogoScreen frame. Canvas redraws drive the fade independently of Android's
  animation-scale setting; the game is released after the zero-alpha artwork
  has been drawn. This is a fade to black followed by the original logos, not
  a crossfade that starts the logos underneath the artwork.
  The game timer is reset after this short wait, preserving subsequent animation
  progression. A non-drawing/paused view recovers after 1000 ms; the game-thread
  wait is bounded to 1250 ms and reports unsuccessful handoff on recovery.
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
neither the APK nor its saves, and requires no root. **Its effect on the observed
APKVision toast is not device-verified.** Android 14 can render text toasts in
SystemUI rather than the game's own window, so that toast may still appear even
when this operation reports `ignore`. Disabling notification permission also
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

The startup-only follow-up passed **310 automated tests** and a fresh private
rebuild/sign/alignment/integrity check. An executable Java UI harness checks
monotonic 500 ms alpha reduction, the black endpoint before game release, a
fully visible PNG during loading, unchanged complete-source 4:3 bounds,
status-bar-only and focus recovery, preservation of existing observers,
pre-API-30 behavior, listener cleanup and safe paused/detached recovery. Against
the corrected Exit cloud reference, only `classes3.dex` and signature metadata
changed: the managed helper, native bridge, `classes.dex` and baseline
`classes2.dex` remained byte-for-byte identical. This is host/package evidence;
the new fade and status-bar behavior still need Retroid testing.

With a private .NET SDK and JDK prepared, run the complete tests with:

```bash
MCI_DOTNET=/private/dotnet/dotnet MCI_JDK=/private/jdk \
ANDROID4X3_REQUIRE_NATIVE_TESTS=1 python -m pytest -ra
```

The existing baseline launcher and its tests remain unchanged.
