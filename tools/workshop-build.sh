#!/usr/bin/env bash
# Shared workshop bootstrap; the original Marvel launcher remains untouched.
set -euo pipefail
umask 077
if [ "$#" -lt 1 ]; then echo "Usage: bash tools/workshop-build.sh GAME-ID [--apk ORIGINAL.apk] [--output OUTPUT.apk]" >&2; exit 2; fi
apk4x3_script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
apk4x3_system=$(uname -s)
apk4x3_machine=$(uname -m)
case "$apk4x3_system:$apk4x3_machine" in
  Darwin:arm64)
    apk4x3_python_target=aarch64-apple-darwin
    apk4x3_python_sha=a18cc33862b53bd54a148c710def5375c1b47470cccedf817a19c2d211764584 ;;
  Darwin:x86_64)
    apk4x3_python_target=x86_64-apple-darwin
    apk4x3_python_sha=869e0b30959beccc616ce14907439f4d0b3170c5830a2362dade07f07b0ed3b8 ;;
  Linux:x86_64)
    apk4x3_python_target=x86_64-unknown-linux-gnu
    apk4x3_python_sha=5ff9f0602ce964a529ed1e8555d3abab6341926d724402ba9a15e9e877191124 ;;
  *) echo "Supported hosts: Apple Silicon/Intel macOS and x86_64 Linux." >&2; exit 2 ;;
esac
if [ "$apk4x3_system" = Darwin ]; then
  apk4x3_default_cache="$HOME/Library/Caches/android-4x3-workshop"
else
  apk4x3_default_cache="${XDG_CACHE_HOME:-$HOME/.cache}/android-4x3-workshop"
fi
# Reuse the validated Marvel cache on Macs that have already used that launcher.
if [ "$apk4x3_system" = Darwin ] && [ -d "$HOME/Library/Caches/android-4x3-marvel" ]; then
  apk4x3_default_cache="$HOME/Library/Caches/android-4x3-marvel"
fi
apk4x3_cache=${APK4X3_CACHE:-$apk4x3_default_cache}
apk4x3_python=""
apk4x3_use_system_python=1
# Avoid triggering Apple's Command Line Tools installer through its Python stub.
if [ "$apk4x3_system" = Darwin ] && [ "$(command -v python3 || true)" = /usr/bin/python3 ]; then
  if ! /usr/bin/xcode-select -p >/dev/null 2>&1; then apk4x3_use_system_python=0; fi
fi
if [ "$apk4x3_use_system_python" = 1 ] && [ "${APK4X3_FORCE_PRIVATE_PYTHON:-0}" != 1 ] && command -v python3 >/dev/null 2>&1; then
  if python3 -c 'import sys; raise SystemExit(sys.version_info < (3, 11))' >/dev/null 2>&1; then
    apk4x3_python=$(command -v python3)
  fi
fi
if [ -z "$apk4x3_python" ]; then
  apk4x3_python_root="$apk4x3_cache/python-3.12.15-$apk4x3_python_target"
  apk4x3_python="$apk4x3_python_root/python/bin/python3"
  if [ ! -x "$apk4x3_python" ]; then
    mkdir -p "$apk4x3_cache"
    apk4x3_temp=$(mktemp -d "$apk4x3_cache/python-download.XXXXXXXX")
    trap 'rm -rf -- "$apk4x3_temp"' EXIT
    apk4x3_url="https://github.com/astral-sh/python-build-standalone/releases/download/20261021/cpython-3.12.15%2B20261021-$apk4x3_python_target-install_only.tar.gz"
    echo "Installing private Python 3.12.15 (no administrator access needed)..."
    curl --proto '=https' --proto-redir '=https' -fL --retry 2 "$apk4x3_url" -o "$apk4x3_temp/python.tar.gz"
    if command -v shasum >/dev/null 2>&1; then
      printf '%s  %s\n' "$apk4x3_python_sha" "$apk4x3_temp/python.tar.gz" | shasum -a 256 -c -
    else
      printf '%s  %s\n' "$apk4x3_python_sha" "$apk4x3_temp/python.tar.gz" | sha256sum -c -
    fi
    mkdir "$apk4x3_temp/unpacked"
    tar -xzf "$apk4x3_temp/python.tar.gz" -C "$apk4x3_temp/unpacked"
    mv "$apk4x3_temp/unpacked" "$apk4x3_python_root"
    rm -rf -- "$apk4x3_temp"
    trap - EXIT
  fi
fi
export APK4X3_CACHE="$apk4x3_cache"
exec "$apk4x3_python" "$apk4x3_script_dir/workshop.py" local-build "$@"
