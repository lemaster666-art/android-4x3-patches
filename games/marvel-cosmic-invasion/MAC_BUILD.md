# Build the stretched 4:3 APK on your Mac

This builds the same experimental display patch without transferring the game
through GitHub. You supply your original APK locally. The original stays untouched.
The existing display patch is not changed by the launcher.

**Confirmed by the device owner on 2026-10-25:** this exact Terminal workflow
worked perfectly with their local original APK. The resulting build installed
on a Retroid Pocket Classic running Android 14, with correct centred stretched
4:3 presentation in menus and approximately 30 minutes of gameplay. This is the
preferred method for future Marvel builds: build locally from your own APK,
retain your local signing key, and transfer only the finished output to the
Retroid. No APK upload or cloud file-transfer service is needed.

Supports Apple Silicon and Intel Macs. Allow roughly 5 GB of free disk space and
an internet connection for the first run. Homebrew, Android Studio, Xcode and
administrator access are not required. Missing Python/Java and Android tools are
installed into your own private folders with HTTPS and pinned SHA-256 checks.

## One Terminal command

1. Put your **original Marvel Cosmic Invasion APK** somewhere on your Mac, such
   as Downloads. It must be the `1.0-jayeldragon-display` build used for this patch.
2. Open **Terminal**: press Command–Space, type `Terminal`, and press Return.
3. Copy the entire following block, paste it into Terminal, and press Return.
   It is one command, split across lines for readability:

```sh
marvel_tools=$(mktemp -d) && \
curl --proto '=https' --proto-redir '=https' -fL \
  https://codeload.github.com/lemaster666-art/android-4x3-patches/zip/refs/heads/main \
  -o "$marvel_tools/tools.zip" && \
ditto -x -k "$marvel_tools/tools.zip" "$marvel_tools" && \
bash "$marvel_tools/android-4x3-patches-main/games/marvel-cosmic-invasion/build-local.sh"
```

4. A Mac file picker opens. Select your **original APK**, then click **Choose**.
5. Wait for Terminal to say **SUCCESS**. The first run downloads tools and can
   take several minutes. Finder then selects your finished APK in a new folder
   inside **Downloads**, named `Marvel-4x3-YYYYMMDD-HHMMSS`.

If you downloaded this repository's ZIP yourself instead, unzip it and run
`bash /path/to/android-4x3-patches-main/games/marvel-cosmic-invasion/build-local.sh`.
You can drag the script from Finder into Terminal after typing `bash ` to avoid
typing its path. Paths containing spaces must stay quoted.

No account password, APK upload, GitHub login or signing-key entry is required
when the repository is public. If the repository is private, download its ZIP
through your signed-in GitHub browser and use the alternative above.

## What you get

The output folder contains:

- `Marvel-Cosmic-Invasion-stretched-4x3-experimental.apk`: aligned, locally signed
  APK with the original package identity.
- A matching `.json` report: SHA-256, size, original preservation and content checks.
- `signature-verification.txt`: Android signature-verification results.

The launcher checks the original's SHA-256 before patching, checks the unchanged
patch-source hashes, and rejects an unexpected assembled display DEX. It checks
alignment, ZIP integrity, signatures, manifest identity and every content member.
Only `classes2.dex` and signing metadata may differ. FNA3D, SDL3, the camera,
protection libraries and game assets stay unchanged.

The intended display is **1240×930**, centred on the Classic's **1240×1080**
screen, leaving **75 pixels above and below**. Internal rendering stays 1240×698.
Device startup and menu/gameplay presentation have the user validation above.
Separate overlay, lifecycle and longer-session coverage remains experimental.

Your Mac creates its own signing key. Therefore its whole-APK SHA-256 normally
differs from the cloud test APK, even though the patched display DEX must always
have SHA-256 `0accefb0c85def38839d3e3015d130967a21b7545869f6cefcd7efc23bcc2fe1`.
The JSON report gives the correct checksum for your particular signed build.

## Install and test on the Retroid

1. Copy the generated APK to the Retroid using your usual file-transfer method.
2. Uninstall the existing differently signed version before installing this one.
   As discussed, this normally deletes its private saved progress.
3. Open the generated APK in the Retroid's file manager and install it. Android
   may ask you to allow that file manager to install unknown apps.
4. Test gameplay, menus, controls, Home/resume and sleep/resume. Check that the
   whole picture is visible, stretched vertically, with centred black borders.

To revert, uninstall the experimental version and reinstall your unchanged
original APK. This does not restore private saves deleted during uninstall.
Do not change protection or native graphics libraries if startup fails; report
the error so the display-only experiment can be assessed first.

## Tool and key locations

- Downloaded tools: `~/Library/Caches/android-4x3-marvel/`
- Private signing key and password files:
  `~/Library/Application Support/android-4x3-patches/`
- APK outputs and reports: the dated folder inside `~/Downloads/`.

Keep the signing folder private and retain it for future builds. Reusing that
key allows later locally signed test builds to update one another. Deleting it
creates a different key on the next run. Nothing in these locations is added to
Git or uploaded. The script never installs or launches the game.

## Troubleshooting and advanced use

- **Original SHA-256 mismatch:** choose the original APK, not the experimental
  output or a different port revision. Supported original SHA-256:
  `d0c9587575f5bba17a5ac2f5ea3e56700b362f658aaaff84ae11c9b67eae18c9`.
- **Checksum or TLS failure:** stop and keep the error message. Verification is
  never disabled. For a corrupt cached download, remove only the named cached
  file and rerun; no APK or signing material needs to be removed.
- **Existing output:** the script refuses to replace it. The normal command
  creates a new dated folder on every run.
- **No file picker / using an existing checkout:** provide the original path:
  `bash games/marvel-cosmic-invasion/build-local.sh "/path/to/Original.apk"`.
- **Custom output:** append `--output "$HOME/Downloads/My-new-test.apk"`.
- **Advanced cache relocation:** set `MARVEL_BUILD_CACHE` to a private directory
  outside the checkout. Set `XDG_DATA_HOME` only if intentionally reusing another
  patcher signing identity. These variables contain local paths, not credentials.

## Reproduction evidence

In the Linux cloud environment, the wrapper downloaded and verified its tools,
reused the existing signing identity, and reproduced the original experimental
APK byte-for-byte: SHA-256
`27d97ef4a4404137f19a0fd1a6354aa2d04a0656efa4c7fcd3c325163d219613`.
The original APK and four existing patch/build files remained unchanged.
The fresh private Python 3.12.15 / Java 21.0.13 bootstrap path also reproduced
that exact APK, after downloading and verifying both runtimes.
All 275 repository tests passed with native test dependencies enabled.
The macOS Android alignment binary was inspected and contains both ARM64 and
x86_64 code. The owner subsequently confirmed successful macOS execution and
Retroid hardware testing on 2026-10-25. The cloud agent did not perform those
physical checks. The Mac model/macOS version, separate sleep/resume checks and
pixel measurements were not recorded; the device report covers menus and
approximately 30 minutes of gameplay on the Classic with Android 14.
