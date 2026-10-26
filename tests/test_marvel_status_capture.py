"""Exercise the diagnostic launcher with authored ADB responses, no device/APK."""
import os
from pathlib import Path
import subprocess

import pytest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'experiments/marvel-startup-exit/capture-status-bar.sh'


@pytest.mark.parametrize('mode', ['success', 'running', 'unauthorized', 'incomplete'])
def test_capture_is_private_and_changes_no_settings(tmp_path,mode):
    fake=tmp_path/'adb'
    fake.write_text('''#!/bin/sh
case "$*" in
  get-state)
    if [ "$CAPTURE_TEST_MODE" = unauthorized ]; then echo 'device unauthorized' >&2; exit 1; fi
    echo device ;;
  'shell pidof com.jayeldragon.marvelcosmic.preview')
    if [ "$CAPTURE_TEST_MODE" = running ]; then echo 1234; exit 0; fi
    exit 1 ;;
  'shell sh')
    cat > "$CAPTURE_TEST_COMMANDS"
    if [ "$CAPTURE_TEST_MODE" = incomplete ]; then echo 'connection closed'; exit 0; fi
    echo '=== CAPTURE COMPLETE ===' ;;
  *) echo 'Unexpected ADB mutation/command' >&2; exit 99 ;;
esac
''')
    fake.chmod(0o700)
    out=tmp_path/'private-capture';commands=tmp_path/'device-commands.sh'
    env={**os.environ,'CAPTURE_TEST_MODE':mode,'CAPTURE_TEST_COMMANDS':str(commands)}
    result=subprocess.run(['bash',str(SCRIPT),'--adb',str(fake),'--output-dir',str(out)],env=env,text=True,capture_output=True)
    assert result.returncode==(0 if mode=='success' else 1),result.stdout+result.stderr
    if mode in ['running','unauthorized']:
        assert not out.exists() and not commands.exists()
        assert ('Exit option' if mode=='running' else 'unauthorized') in result.stdout+result.stderr
        return
    log=out/'marvel-status-bar.txt'
    assert out.stat().st_mode&0o777==0o700
    assert log.stat().st_mode&0o777==0o600
    source=commands.read_text()
    assert 'dumpsys window windows' in source and 'dumpsys window displays' in source
    assert 'cat /proc/uptime' in source
    assert 'am start -n com.jayeldragon.marvelcosmic.preview/com.vocies61.marvelcosmic.MainActivity' in source
    assert '"$sample" -lt 30' in source
    for forbidden in ['force-stop','pm clear','appops set','logcat -c','screenrecord','screencap','install ', 'curl ', 'wget ']:
        assert forbidden not in source
    assert str(log) in result.stdout+result.stderr


def test_capture_refuses_output_in_checkout(tmp_path):
    fake=tmp_path/'adb';fake.write_text('#!/bin/sh\n[ "$1" = get-state ]\n');fake.chmod(0o700)
    out=ROOT/'private-capture-refuse'
    result=subprocess.run(['bash',str(SCRIPT),'--adb',str(fake),'--output-dir',str(out)],text=True,capture_output=True)
    assert result.returncode==1 and 'outside the Git checkout' in result.stderr
    assert not out.exists()
