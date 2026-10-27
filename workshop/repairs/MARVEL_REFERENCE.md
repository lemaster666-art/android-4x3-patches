# Validated Marvel startup, Exit and status-bar reference

Reference: [`6cbe39a7f5ad14911f1d2dc3f4a82ee35cb7c82c`](https://github.com/lemaster666-art/android-4x3-patches/commit/6cbe39a7f5ad14911f1d2dc3f4a82ee35cb7c82c).
Implementation: [experiments/marvel-startup-exit](../../experiments/marvel-startup-exit/README.md).
Preservation: [source-pinned repair profile](marvel-cosmic-invasion.json).

The profile retains the 28 historical reference hashes separately from current
source pins. The authorized [optional loading-animation candidate](../../experiments/marvel-startup-exit/LOADING_ANIMATION.md)
extends the existing drawing path without changing the validated guard, handoff
or startup timings. Its appearance/disappearance is **awaiting handheld validation**;
the hardware evidence below applies to the preserved reference, not a new output.

## Hardware evidence and limits

Device: **Retroid Pocket Classic, Android 14, 1240×1080**. Supported APK:
`com.jayeldragon.marvelcosmic.preview`, `1.0-jayeldragon-display` / code 2, ARM64,
original SHA-256 `d0c9587575f5bba17a5ac2f5ea3e56700b362f658aaaff84ae11c9b67eae18c9`.
These are owner-reported physical tests, distinct from cloud/host checks.

| Technique | Reported hardware result |
|---|---|
| Existing 4:3 gameplay patch | Menus and approximately 30 minutes of gameplay correct, 2026-10-25; 1240×930 displayed with 75-pixel borders, internal 1240×698 image retained |
| Custom PNG/stable splash layout | Artwork replacement works without the earlier aspect flicker |
| Rendering-callback handoff | PNG covers loading; original developer-logo transitions/timing preserved |
| Android Exit/audio cleanup | Normal app closure and stopped audio, no black-screen hang or manual force-close, 2026-10-26 |
| Splash-scoped window-style guard | **Hardware validated: status-bar flash eliminated**, reference commit above; confirmed 2026-10-27 |
| Local Mac delivery/update | Local original/PNG selection, verified build and same-key USB update reported successful |

This does not establish every save/resume case, exact measured fade durations,
long-term coverage, other devices/ABIs or arbitrary new outputs. The Android
launch icon and distributor toast are separate. `TOAST_WINDOW: ignore` did not
suppress that toast. The game registry remains experimental in its overall scope.

## Android entry and authored runtime bridge

Protected Activity lifecycle code stays original. The unprotected Java
`SpexApplication.startGame(Activity)` wrapper tries authored `EnhancedBridge`,
retaining its native entry fallback if the helper cannot start. No protection,
licensing or certificate checks are disabled.

Authored [bridge.c](../../experiments/marvel-startup-exit/bridge.c) opens the
already-loaded original Mono runtime with `RTLD_NOLOAD`, resolves audited embedding
exports and checks JNI environment/references. It loads only the authored managed
helper from an opaque asset and calls `Start(Activity handle)`, avoiding changes
to the fixed 96-assembly bundle table. The exact runtime's hybrid AOT/JIT capability
was checked. Missing APIs or managed failures reject integration safely. Another
runtime may not support this. Original managed/AOT/native game files stay intact;
cloud verification compiled authored code and did not execute the game.

## Artwork and actual rendering readiness

[EnhancedUi.java](../../experiments/marvel-startup-exit/java/com/vocies61/marvelcosmic/EnhancedUi.java)
draws the whole locally selected PNG in centered 4:3 bounds, without crop, zoom,
port-credit text or donation hit target. Cloud packaging uses synthetic art.
Original splash resources and developer-logo assets remain in the archive.

[Enhancements.cs](../../experiments/marvel-startup-exit/Enhancements.cs) runs the
original bootstrap on a worker. After original logging configuration, an authored
synchronous NLog target sees the audited `startinit: after LoadFonts` event and
attaches before initial context presentation. That event installs observation;
it is **not itself first-frame readiness** or log-file polling.

A pass-through `IGraphicsDeviceManager` wrapper uses a verified mutable instance
field and delegates original BeginDraw/CreateDevice/EndDraw. Before presentation,
it checks the logo context, loading thread and fade state. Only then does it ask
the UI to finish the splash, wait for bounded acknowledgement and reset elapsed
game time. Original EndDraw still runs. It does not hide running logos beneath
artwork or infer readiness from a fixed delay/brightness guess.

The current presentation has a 500 ms fade-in, PNG during loading, two-second
fade-out and 500 ms black hold. The hold begins after black is actually drawn,
including delayed redraw. Canvas fades do not depend on system animator scales.
Paused/detached Views have bounded recovery revealing original diagnostics.
Cosmetic time is additional; covering a black gap does not reduce loading work.

## Exit, saves and FMOD

The original desktop-style game loop returns while Android and FMOD can remain
alive. The repair requires the real Exiting event **and** normal bootstrap return
with no recorded game error. Original save-worker cleanup settles first. Failed
startup retains diagnostics instead of closing the app.

Original audio disposal drops a singleton without releasing its Studio system.
The helper captures the verified handle while live, then after normal completion
stops events on `bus:/`, flushes commands and releases the Studio system. It clears
the manager handle only after successful release. Missing/invalid handles and
cleanup errors are logged, not treated as successful backend cleanup. Other
games may own audio and save threads differently.

[EnhancedBridge.java](../../experiments/marvel-startup-exit/java/com/vocies61/marvelcosmic/EnhancedBridge.java)
finishes/removes the intended Activity on its UI thread, guarded against duplicate
completion. A lifecycle callback waits for destruction of **that Activity** before
normal process exit, preventing reuse of disposed FNA/Mono singletons. Unrelated
Activity destruction does not exit the process. No arbitrary kill timer is used.
Other apps may need only Activity closure, not this process-exit policy.

## Field-visibility failure and realistic fixtures

The first helper rejected attachment because it looked up
`AudioManager._studioSystem` with `BindingFlags.NonPublic`; the supported assembly
declares it **public**. Its initial host fixture also incorrectly modeled it private.
Correcting both lookup and fixture reproduced the failure before the fix and
resolved it. Named guard failures and phase diagnostics now identify the stopped
hook. Verify actual field visibility, inheritance, mutability and runtime support;
a plausible fake API and passing compiler do not prove device compatibility.

## Validated status-bar repair: stop the transient show command

The first flash report followed `f7799e2`, when hooks first attached successfully;
its Java splash code matched `c91ccb8`. Extra immersive requests/observers and
removing that controller did not fix it. Use exact revision evidence and avoid
asserting that the first reported revision proves a particular causal callback.

Video caught the real clock/battery bar returning about 1.4 seconds after the PNG
appeared, for roughly 0.17 seconds. Periodic dumps/screenshots missed it. The Android
Java windowed-style branch shows bars, clears FULLSCREEN and enables
FORCE_NOT_FULLSCREEN; the existing shim schedules re-hide after **150 ms**.
This is the show/hide mechanism addressed by the physically validated guard.

The narrow [smali transformation](../../experiments/marvel-startup-exit/build-local.py)
adds a call to `EnhancedUi.splashWindowStyle(int)` inside
`SDLActivity$SDLCommandHandler.handleMessage`, after valid Integer unboxing and
before the existing window-style decision. Zero becomes one only while PNG is
active and startup has not failed, selecting the existing fullscreen branch.
Nonzero arguments pass through exactly. Non-Integer fallback, other commands and
later window-style handling remain original. Dismissal/detachment/failure ends
the guard. No extra immersive observers/re-hide timers or native SDL/FNA edits.

It logs once privately when exercised:
`startup windowed-style request kept Android full-screen while PNG active`.
The camera, rendering buffers and accepted Exit helper stay unchanged. This is
an Android Java presentation-bridge repair. Verify every new APK's own command
semantics, handler, UI thread and splash lifecycle; never transplant class names,
offsets or smali labels blindly.

## Tests, integrity, signing and local delivery

The reference passed **316 host/native tests**, actual compiler/D8/smali assembly
and private rebuild/sign/alignment/member-integrity checks before device validation.
The preserved authored Java, managed and JNI fixtures exercise:

- Exact Activity/duplicate completion/process-exit ordering and failed startup.
- Audio stop/flush/release order and missing APIs/managed exceptions/JNI ABI.
- PNG geometry, fades, black hold, pause/detachment/recovery and stage logging.
- Style guards before/during/after PNG and on failure; nonzero passthrough;
  unknown/already-patched context rejection and minimal transformation scope.
- Corruption, source/version mismatch, unrelated-member tampering and private paths.

Every build checks original/source pins, ZIP CRCs, alignment, signatures, identity,
original/key/PNG preservation and all non-signature members. Only `classes.dex`
and baseline `classes2.dex` change; four authored/user payload entries are added;
**3238 other original entries** stay identical. Display DEX SHA-256 stays
`0accefb0c85def38839d3e3015d130967a21b7545869f6cefcd7efc23bcc2fe1`.

The unchanged launcher reuses private Python/Java/Android/smali caches and verified
.NET/Zig/Android headers. It opens original-APK/PNG pickers, builds a new Downloads
APK/report and requires the existing signer. Intel/Apple Silicon macOS 12+ are
supported by pinned configurations; both are not independently device-tested here.
Same-key updates work; a distributor signing mismatch does not.

Run `python tools/repair-workshop.py verify marvel-cosmic-invasion` before reuse.
Its 28 source/test pins freeze the implementation without moving/refactoring it.
Develop new adapters separately; repin only after intentional review/validation.
Never publish APKs, proprietary files, user art, private captures or credentials.
