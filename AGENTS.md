# Preferred APK build workflow

The user's default for **all APK builds**, across games, is to build locally in
macOS Terminal using their own original APK. Prepare reproducible patching code
and beginner-friendly local instructions, preferably one command with dependency
setup, signing and verification. Preserve the original and produce a separate
output. Keep the local signing key private and reusable.

Use the cloud workspace for code, documentation and proprietary-free tests by
default. Build or transfer proprietary APKs in the cloud only when the user
explicitly requests it. Never commit or publish APKs, extracted proprietary game
files or signing material. Publish only patch/build code, synthetic tests and
instructions. Describe what was actually validated and preserve working patches
unless the user requests changes.

The Marvel macOS launcher is a validated example of this workflow, not a generic
launcher for every game. Use or prepare the appropriate local builder per game.
