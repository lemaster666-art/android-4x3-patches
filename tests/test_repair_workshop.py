"""Command, preservation and lifecycle contracts; no proprietary game fixtures."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from android4x3.delivery import mac_source_command
from android4x3.errors import PatchError
from android4x3 import repair_workshop as r
from android4x3 import workshop as w

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('text,modes', [
    ('EXIT issues', ['exit']), ('exit-issues!', ['exit']), ('  ExIt   IsSuEs: ', ['exit']),
    ('EXIT.ISSUE', ['exit']), ('ＳＴＡＲＴＵＰ＆ＥＸＩＴ ＩＳＳＵＥ', ['startup-exit']),
    ('STARTUP&EXIT ISSUE', ['startup-exit']), ('startup / exit issues', ['startup-exit']),
    ('Startup-and-Exit Issues', ['startup-exit']), ('startup & exit issue', ['startup-exit']),
    ('4:3 time', ['aspect']), ('4 : 3 TIME', ['aspect']),
    ('4:3time + EXIT issues', ['aspect', 'exit']),
    ('STARTUP&EXIT ISSUE with 4:3 time', ['aspect', 'startup-exit']),
    ('4:3 time + EXIT issues + STARTUP&EXIT ISSUE', ['aspect', 'startup-exit']),
])
def test_project_command_routes(text, modes):
    result = r.route_invocation(text)
    assert result['workflows'] == modes
    assert all((ROOT / name).is_file() for name in result['skills'])


def test_link_is_reused_and_explanatory_text_does_not_trigger():
    url='https://example.com/game.apk?version=1#checksum'
    result=r.route_invocation('EXIT issues [APK]('+url+')')
    assert result['apk_links']==[url]
    for text in ['', 'I have exit issues', 'Please explain STARTUP&EXIT ISSUE', 'startup issue', 'EXIT issues and']:
        with pytest.raises(PatchError):r.route_invocation(text)


@pytest.fixture
def profile(tmp_path):
    repo=tmp_path/'repo';launcher=repo/'games/synthetic-game/build-local.sh'
    launcher.parent.mkdir(parents=True);launcher.write_text('#!/bin/bash\nexit 0\n')
    p={'schema_version':1,'repair_id':'synthetic-game','workflow':'exit',
       'launcher':launcher.relative_to(repo).as_posix(),'launcher_arguments':[],
       'source_checksums':{launcher.relative_to(repo).as_posix():w.sha(launcher)},
       'original_apk_sha256':['a'*64],'signing_policy':'reuse-existing',
       'artwork_required':False,'includes_aspect_patch':False,
       'allowed_changes':['classes.dex'],'allowed_additions':[]}
    dest=repo/'workshop/repairs/synthetic-game.json';dest.parent.mkdir(parents=True)
    def save():dest.write_text(json.dumps(p))
    save()
    return repo,p,launcher,save


def test_repair_delivery_is_safe_and_keeps_exit_only_scope(profile):
    repo,p,launcher,save=profile
    command=r.repair_mac_command(repo,'synthetic-game','b'*40,'owner/repo',workflow='exit')
    assert '/zip/'+'b'*40 in command
    assert '/games/synthetic-game/build-local.sh' in command
    assert 'curl' in command and 'ditto' in command and command.count('\n')==3
    subprocess.run(['bash','-n'],input=command,text=True,check=True)
    with pytest.raises(PatchError,match='different workflow'):
        r.repair_mac_command(repo,'synthetic-game','main','owner/repo',workflow='startup-exit')
    with pytest.raises(PatchError):r.repair_mac_command(repo,'../escape','main','owner/repo')
    launcher.write_text('changed source')
    with pytest.raises(PatchError,match='source changed'):r.load_repair_profile(repo,'synthetic-game')


@pytest.mark.parametrize('field,value', [
    ('schema_version',2),('workflow','anything'),('source_checksums',{}),
    ('original_apk_sha256',['bad']),('signing_policy','replace-key'),
    ('artwork_required',None),('includes_aspect_patch',None),
    ('allowed_changes',['../bad']),('allowed_additions',['META-INF/new.SF']),
    ('allowed_changes',['assets/*']),('allowed_additions',['classes.dex']),
    ('launcher_arguments',['$(bad)']),('launcher','tools/unpinned.sh'),
])
def test_unsupported_profiles_fail_closed(profile,field,value):
    repo,p,launcher,save=profile;p[field]=value;save()
    with pytest.raises(PatchError):r.load_repair_profile(repo,'synthetic-game')


def test_profile_cannot_pin_binary_or_escape_checkout(profile,tmp_path):
    repo,p,launcher,save=profile
    bad=launcher.with_suffix('.dll');bad.write_bytes(b'MZ')
    p['source_checksums'][bad.relative_to(repo).as_posix()]=w.sha(bad);save()
    with pytest.raises(PatchError,match='source code only'):r.load_repair_profile(repo,'synthetic-game')
    p['source_checksums'].pop(bad.relative_to(repo).as_posix())
    outside=tmp_path/'outside.sh';outside.write_text('exit 0')
    link=launcher.parent/'escape.sh';link.symlink_to(outside)
    p['source_checksums'][link.relative_to(repo).as_posix()]=w.sha(outside);save()
    with pytest.raises(PatchError,match='escapes'):r.load_repair_profile(repo,'synthetic-game')


def test_mac_generator_rejects_injection_and_quotes_arguments():
    for launcher,ref,repo in [('tools/$(bad).sh','main','owner/repo'),
                              ('../escape.sh','main','owner/repo'),
                              ('tools/run.sh','main;bad','owner/repo'),
                              ('tools/run.sh','main','https://token@host/repo')]:
        with pytest.raises(PatchError):mac_source_command(launcher,ref,repo)
    command=mac_source_command('tools/run.sh','main','owner/repo',('name with spaces;$(bad)',))
    assert "'name with spaces;$(bad)'" in command
    subprocess.run(['bash','-n'],input=command,text=True,check=True)


def test_preserved_marvel_reference_and_generated_command():
    p=r.load_repair_profile(ROOT,'marvel-cosmic-invasion')
    assert p['validated_reference']==r.REFERENCE
    assert p['hardware_validation']['status']=='hardware validated: status-bar flash eliminated'
    assert p['artwork_required'] and p['includes_aspect_patch']
    assert len(p['source_checksums'])==28
    assert 'tests/test_marvel_enhancements.py' in p['source_checksums']
    command=r.repair_mac_command(ROOT,'marvel-cosmic-invasion',r.REFERENCE,'lemaster666-art/android-4x3-patches',workflow='startup-exit')
    assert 'experiments/marvel-startup-exit/build-local.sh' in command
    with pytest.raises(PatchError,match='different workflow'):
        r.repair_mac_command(ROOT,'marvel-cosmic-invasion','main','owner/repo',workflow='exit')
    subprocess.run(['bash','-n'],input=command,text=True,check=True)


SUCCESS=['exit_intent_confirmed','saves_settled','game_returned_success',
         'audio_cleanup_complete','activity_finish_requested','activity_destroyed','process_exit']


def test_engine_neutral_lifecycle_fixture_allows_backend_specific_audio_order():
    r.validate_exit_trace(SUCCESS,successful=True,process_exit_expected=True)
    events=SUCCESS.copy();events.remove('audio_cleanup_complete');events.insert(2,'audio_cleanup_complete')
    r.validate_exit_trace(events,successful=True)
    r.validate_exit_trace(SUCCESS[:-1],successful=True)
    r.validate_exit_trace(['startup_failed','diagnostics_visible'],successful=False)


@pytest.mark.parametrize('events,successful,process', [
    (SUCCESS[:-1],True,True),
    ([e for e in SUCCESS if e!='saves_settled'],True,False),
    (['activity_finish_requested']+SUCCESS[:4]+SUCCESS[5:],True,False),
    (SUCCESS[:-2]+['process_exit','activity_destroyed'],True,False),
    (SUCCESS+['process_exit'],True,False),
    (['startup_failed','activity_finish_requested'],False,False),
    (['startup_failed','process_exit'],False,False),
])
def test_early_or_failed_startup_termination_is_rejected(events,successful,process):
    with pytest.raises(PatchError):r.validate_exit_trace(events,successful=successful,process_exit_expected=process)


def test_cli_route_verify_and_command():
    env={**os.environ,'PYTHONPATH':str(ROOT/'src')}
    for args in [['route','startup & exit issue'],['verify','marvel-cosmic-invasion'],
                 ['command','marvel-cosmic-invasion','--ref',r.REFERENCE]]:
        result=subprocess.run([sys.executable,str(ROOT/'tools/repair-workshop.py'),*args],env=env,capture_output=True,text=True)
        assert result.returncode==0,result.stdout+result.stderr
        assert result.stdout.strip()


def test_skill_entry_points_and_document_links_exist():
    agents=(ROOT/'AGENTS.md').read_text()
    for path in r.SKILLS.values():
        skill=ROOT/path
        assert path in agents and skill.is_file()
        assert skill.read_text().startswith('---\nname:')
    for path in ['workshop/repairs/README.md','workshop/repairs/MARVEL_REFERENCE.md']:
        assert (ROOT/path).is_file()
