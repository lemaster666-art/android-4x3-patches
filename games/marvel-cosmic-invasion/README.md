# Marvel Cosmic Invasion — experimental stretched presentation

This device profile deliberately stretches the original picture. It does not
expand the camera's field of view. The owner reported successful Retroid Pocket
Classic / Android 14 validation on **2026-10-25**, covering menus and approximately
**30 minutes of gameplay**. The module remains experimental within that scope.

**Mac users:** follow [Build on your Mac](MAC_BUILD.md) for one Terminal command,
automatic private tool installation, signing and verification. You supply the
original APK locally; no game files are uploaded or included in this repository.
The owner confirmed this Terminal workflow worked perfectly; it is the preferred
method for future Marvel builds using their own local APK.

An [optional startup and Exit builder](../../experiments/marvel-startup-exit/README.md)
adds a locally selected PNG and translates normal game-loop completion into
Android audio cleanup and app closure. The owner validated proper main-menu Exit
on Retroid Pocket Classic / Android 14 on **2026-10-26**, with no lingering audio
or black-screen hang. The PNG remains until the developer logos appear; a brief
Android status-bar appearance during startup remains unresolved. This is a
separate builder; the baseline patch and Terminal launcher here are unchanged.

Target: Retroid Pocket Classic, Android 14, full-screen 1240×1080 parent. The
existing 1240×698 SDL SurfaceView layout remains 16:9 internally. A centred
compositor transform displays it at 1240×930, from y=75 to y=1005, leaving 75
black pixels above and below. Vertical scale is `930 / 698`, not a rounded 4/3.
No cropping, FNA3D/SDL3 edits, camera edits, asset changes or AOT changes occur.

The existing `DisplayFix.fit(Activity)` becomes a wrapper around its preserved
16:9 fit body and an authored `applyStretch4x3(Activity)` helper. The helper
changes View pivot, scale and translation, never layout/buffer dimensions. It
handles early returns and measures actual dimensions after layout. An observer
registered alongside the original global-layout listener reapplies the transform
before each draw, including menu transitions and resumed rendering. It holds
only a weak reference to the Activity and does not accumulate scaling.

The observer depends on the existing shim's install path, which this protected
port invokes through native startup code. The owner's locally built APK launched
and displayed correctly during the reported hardware test. Separate Android
touch/credit/diagnostic overlays are not transformed or removed; their complete
input behavior and interaction with the borders were not separately reported.

## Compatibility and dependencies

Supported identity: `com.jayeldragon.marvelcosmic.preview`, version
`1.0-jayeldragon-display`, code 2, ARM64. The private builder requires original
APK SHA-256 `d0c9587575f5bba17a5ac2f5ea3e56700b362f658aaaff84ae11c9b67eae18c9`.
`patch_impl.py` checks manifest identity/version, the display DEX's exact original
or patched SHA-256, its SHA-1/Adler32 integrity, and unique method/listener
contexts. An unfamiliar build fails closed. The assembled result must match the
audited patched DEX checksum. Patched input is recognized and not patched twice.

Applying requires Java plus smali/baksmali 2.5.2 and their Maven dependencies.
Set `SMALI_CLASSPATH` to a Java classpath containing those jars. The prepared
cloud instance has them at `/workspace/.tools/smali-2.5.2/*` (the default).
They are not needed for `--check`. Python requirements are the project's existing
ones. No proprietary DEX or reconstructed original smali is shipped here:
`transform.smali` and `StretchWatcher.smali` are newly authored patch code only.

## Build outside the checkout

From the repository root, with its virtualenv and Android SDK initialized:

```sh
python games/marvel-cosmic-invasion/build.py /private/original.apk /private/Marvel-stretched-experimental.apk
./patch.sh --allow-experimental --check --json /private/Marvel-stretched-experimental.apk
```

The builder refuses an output inside the checkout, an existing output, an input
hash mismatch or any unexpected content changes. It creates a separate output,
aligns and signs it with the patcher's local private key, verifies the archive,
signature, alignment and manifest, and compares every non-signature APK member.
Only `classes2.dex` may change. Signature metadata is replaced. The original
hash is checked again before publishing the local output. A JSON report is
written next to it. The normal patch CLI also honors this module's
`PRESERVE_UNRELATED_ENTRIES` flag: optional branding/protection cleanup is disabled.

## Installation and save compatibility

The supplied original is signed by APKVISION.ORG. A locally signed APK with
the same package identity cannot update it: Android rejects a signing-key
mismatch, regardless of `adb install -r`. A version-code bump cannot fix this.
No original signing key is supplied or requested. No protection bypass or
signature-check modification is part of this patch.

Uninstalling a conflicting installation normally removes its private saves.
Proceed only after accepting that loss or verifying an appropriate backup.
Private saves are not automatically accessible or exportable merely because
`allowBackup` is enabled. No save backup has been obtained or verified here.
Keeping the original APK alone does not back up installed save data.

The same-package test APK can be installed only on a device without a conflicting
installation, or updated over a build signed with the same local patcher key:

```sh
adb install /private/Marvel-stretched-experimental.apk
```

There is no connected Android device in this cloud environment. The user chose
to retain the original identity and accept uninstalling their existing build;
no side-by-side package or save migration is included. Do not attempt invasive
changes if the protected port refuses to boot.

## Validation

Proprietary-free tests execute the authored smali arithmetic in a small mocked
Android interpreter, check exact Retroid bounds, no buffer resizing, unchanged
state on repeated application, correction after simulated property reset,
portrait/odd-size layouts, missing/unlaid-out surfaces, original method
preservation, unknown/corrupt/version-mismatched rejection and idempotence.
A synthetic DEX assembly/disassembly test exercises the real smali toolchain
when available. These tests do not execute Dalvik or SurfaceFlinger.

User-reported hardware validation on **2026-10-25**: the macOS Terminal launcher
successfully built from the owner's original APK, installation on the Retroid
Pocket Classic / Android 14 succeeded, and centred stretched 4:3 presentation
worked correctly in menus and approximately 30 minutes of gameplay. The working
patch was unchanged for this documentation update. No APK was uploaded to the
repository. See the [verification record](../../VERIFICATION.md#marvel-cosmic-invasion-10-jayeldragon-display-2)
for evidence and scope.

Further acceptance checks include precise pixel measurements, sleep/resume,
all touch overlays, wider scene coverage and longer sessions. These were not
separately reported. Stop and report startup or protection failures on other
builds; do not automatically change native rendering or security code as a
fallback.
