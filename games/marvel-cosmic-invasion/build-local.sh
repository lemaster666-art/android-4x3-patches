#!/usr/bin/env bash
# Installs a private Python only when needed, then runs the unchanged patch.
set -euo pipefail
umask 077
marvel_script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
marvel_system=$(uname -s)
marvel_machine=$(uname -m)
case "$marvel_system:$marvel_machine" in
  Darwin:arm64)
    marvel_python_target=aarch64-apple-darwin
    marvel_python_sha=a18cc33862b53bd54a148c710def5375c1b47470cccedf817a19c2d211764584 ;;
  Darwin:x86_64)
    marvel_python_target=x86_64-apple-darwin
    marvel_python_sha=869e0b30959beccc616ce14907439f4d0b3170c5830a2362dade07f07b0ed3b8 ;;
  Linux:x86_64)
    marvel_python_target=x86_64-unknown-linux-gnu
    marvel_python_sha=5ff9f0602ce964a529ed1e8555d3abab6341926d724402ba9a15e9e877191124 ;;
  *) echo "Supported hosts: Apple Silicon/Intel macOS and x86_64 Linux." >&2; exit 2 ;;
esac
if [ "$marvel_system" = Darwin ]; then
  marvel_default_cache="$HOME/Library/Caches/android-4x3-marvel"
else
  marvel_default_cache="${XDG_CACHE_HOME:-$HOME/.cache}/android-4x3-marvel"
fi
marvel_cache=${MARVEL_BUILD_CACHE:-$marvel_default_cache}
marvel_python=""
marvel_use_system_python=1
# Avoid triggering Apple's Command Line Tools installer through its Python stub.
if [ "$marvel_system" = Darwin ] && [ "$(command -v python3 || true)" = /usr/bin/python3 ]; then
  if ! /usr/bin/xcode-select -p >/dev/null 2>&1; then marvel_use_system_python=0; fi
fi
if [ "$marvel_use_system_python" = 1 ] && [ "${MARVEL_FORCE_PRIVATE_PYTHON:-0}" != 1 ] && command -v python3 >/dev/null 2>&1; then
  if python3 -c 'import sys; raise SystemExit(sys.version_info < (3, 11))' >/dev/null 2>&1; then
    marvel_python=$(command -v python3)
  fi
fi
if [ -z "$marvel_python" ]; then
  marvel_python_root="$marvel_cache/python-3.12.15-$marvel_python_target"
  marvel_python="$marvel_python_root/python/bin/python3"
  if [ ! -x "$marvel_python" ]; then
    mkdir -p "$marvel_cache"
    marvel_temp=$(mktemp -d "$marvel_cache/python-download.XXXXXXXX")
    trap 'rm -rf -- "$marvel_temp"' EXIT
    marvel_url="https://github.com/astral-sh/python-build-standalone/releases/download/20261021/cpython-3.12.15%2B20261021-$marvel_python_target-install_only.tar.gz"
    echo "Installing private Python 3.12.15 (no administrator access needed)..."
    curl --proto '=https' --proto-redir '=https' -fL --retry 2 "$marvel_url" -o "$marvel_temp/python.tar.gz"
    if command -v shasum >/dev/null 2>&1; then
      printf '%s  %s\n' "$marvel_python_sha" "$marvel_temp/python.tar.gz" | shasum -a 256 -c -
    else
      printf '%s  %s\n' "$marvel_python_sha" "$marvel_temp/python.tar.gz" | sha256sum -c -
    fi
    mkdir "$marvel_temp/unpacked"
    tar -xzf "$marvel_temp/python.tar.gz" -C "$marvel_temp/unpacked"
    mv "$marvel_temp/unpacked" "$marvel_python_root"
    rm -rf -- "$marvel_temp"
    trap - EXIT
  fi
fi
export MARVEL_BUILD_CACHE="$marvel_cache"
exec "$marvel_python" "$marvel_script_dir/local_build.py" "$@"
