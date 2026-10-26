#!/bin/bash
# Read window/insets state around a normal launch of the installed game.
# No APK transfer, installation, data clearing, force-stop or settings changes.
set -eu
umask 077

adb_path="$HOME/Downloads/platform-tools/adb"
output_dir="$HOME/Downloads/marvel-status-bar-$(date +%Y%m%d-%H%M%S)"
while [ "$#" -gt 0 ]; do
  case "$1" in
    --adb|--output-dir)
      [ "$#" -ge 2 ] || { echo "Missing value for $1" >&2; exit 1; }
      case "$1" in --adb) adb_path=$2 ;; --output-dir) output_dir=$2 ;; esac
      shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

[ -x "$adb_path" ] || { echo "ADB not found at: $adb_path" >&2; exit 1; }
"$adb_path" get-state >/dev/null
package=com.jayeldragon.marvelcosmic.preview
if "$adb_path" shell pidof "$package" >/dev/null 2>&1; then
  echo 'Marvel is already running. Close it with its working Exit option, then run this command again.' >&2
  exit 1
fi

# Keep diagnostics outside this source checkout, and never overwrite a capture.
repo_dir=$(cd "$(dirname "$0")/../.." && pwd -P)
parent_dir=$(cd "$(dirname "$output_dir")" && pwd -P)
output_dir="$parent_dir/$(basename "$output_dir")"
case "$output_dir" in
  "$repo_dir"|"$repo_dir"/*) echo 'Keep private captures outside the Git checkout.' >&2; exit 1 ;;
esac
mkdir -m 700 "$output_dir"
log_file="$output_dir/marvel-status-bar.txt"
printf 'Launching Marvel and collecting 30 startup window snapshots.\nLeave the Retroid untouched until this finishes. No settings or saves are changed.\n'

if "$adb_path" shell sh > "$log_file" 2>&1 <<'ANDROID_CAPTURE'
set -eu
printf 'MARVEL STATUS-BAR CAPTURE; installed build; no APK modifications\n'
printf '\n=== ANDROID VERSION ===\n'
getprop ro.build.version.release
getprop ro.build.version.sdk
wm size
printf '\n=== BEFORE LAUNCH ===\n'
date
cat /proc/uptime
dumpsys window windows
dumpsys window displays
printf '\n=== NORMAL LAUNCH REQUEST ===\n'
am start -n com.jayeldragon.marvelcosmic.preview/com.vocies61.marvelcosmic.MainActivity
sample=0
while [ "$sample" -lt 30 ]; do
  printf '\n=== STARTUP SNAPSHOT %s ===\n' "$sample"
  date
  cat /proc/uptime
  dumpsys window windows
  dumpsys window displays
  sample=$((sample+1))
  sleep 0.2
done
printf '\n=== CAPTURE COMPLETE ===\n'
ANDROID_CAPTURE
then
  if ! LC_ALL=C grep -q '^=== CAPTURE COMPLETE ===' "$log_file"; then
    printf '\nCapture incomplete. Keep the partial file for review:\n%s\n' "$log_file" >&2
    exit 1
  fi
else
  printf '\nCapture failed; keep the partial diagnostic file and report the error.\nSaved to: %s\n' "$log_file" >&2
  exit 1
fi
printf '\nFinished. Attach this private text file in the chat:\n%s\n' "$log_file"
printf 'The capture stays on your Mac; this script uploads nothing.\n'
if [ "$(uname -s)" = Darwin ]; then open -R "$log_file" || true; fi
