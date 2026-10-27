"""Proprietary-free checks for the combined opt-in startup/Exit experiment."""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import shutil
import struct
import subprocess
import zlib
import pytest

ROOT=Path(__file__).resolve().parents[1]
HERE=ROOT/'experiments/marvel-startup-exit'
spec=importlib.util.spec_from_file_location('marvel_enhanced_build',HERE/'build-local.py')
build=importlib.util.module_from_spec(spec);spec.loader.exec_module(build)


def png(width=4,height=3):
 def c(t,d):return struct.pack('>I',len(d))+t+d+struct.pack('>I',zlib.crc32(t+d)&0xffffffff)
 return b'\x89PNG\r\n\x1a\n'+c(b'IHDR',struct.pack('>IIBBBBB',width,height,8,2,0,0,0))+c(b'IDAT',zlib.compress((b'\x00'+b'\x20\x40\x60'*width)*height))+c(b'IEND',b'')


def test_png_integrity_and_complete_image_input(tmp_path):
 path=tmp_path/'my splash.png';path.write_bytes(png());before=path.read_bytes()
 assert build.validate_png(path)=={'width':4,'height':3,'bytes':len(before),'sha256':hashlib.sha256(before).hexdigest()}
 assert path.read_bytes()==before
 for data in [before[:-1],before+b'extra',before[:35]+b'x'+before[36:],b'not a PNG',png(4097,1)]:
  path.write_bytes(data)
  with pytest.raises(build.PatchError):build.validate_png(path)


def test_lz4_literal_overlap_and_bad_offsets():
 assert build.lz4_block(b'\x50hello',5)==b'hello'
 assert build.lz4_block(b'\x11a\x01\x00',6)==b'aaaaaa'
 for data,size in [(b'\x11a\x00\x00',6),(b'\x11a\x02\x00',6),(b'\xf0',1),(b'\x50hello',4),(b'\x50hell',5)]:
  with pytest.raises(build.PatchError):build.lz4_block(data,size)


def test_lz4_matches_reference_decoder():
 import lz4.block
 for data in [b'a'*50000,bytes(range(256))*40,os.urandom(4096),b'MZ'+b'abcd'*5000]:
  compressed=lz4.block.compress(data,store_size=False)
  assert build.lz4_block(compressed,len(data))==data


def splash_fixture():
 return '''.class final Lcom/vocies61/marvelcosmic/SplashView;
.super Landroid/view/View;
.method start(Ljava/lang/Runnable;)V
 .registers 5
 const-wide/16 v1, 0x1b58
 return-void
.end method
.method protected onDraw(Landroid/graphics/Canvas;)V
 .registers 22
 return-void
.end method
.method public onTouchEvent(Landroid/view/MotionEvent;)Z
 .registers 5
 const/4 v0, 0x1
 return v0
.end method
.method protected onDetachedFromWindow()V
 .registers 3
    return-void
.end method
.method private dismiss()V
 .registers 1
 return-void
.end method
'''


def test_splash_targeted_transform_preserves_callback():
 old=splash_fixture();new=build.transform_splash(old)
 old_methods=build.baseline().method_blocks(old);new_methods=build.baseline().method_blocks(new)
 assert old_methods['.method private dismiss()V']==new_methods['.method private dismiss()V']
 assert '->onFinished:Ljava/lang/Runnable;' in new
 assert '->attach(' in new and '->draw(' in new and '->detached(' in new
 assert new.count('.method public finishEnhancedSplash()V')==1
 with pytest.raises(build.PatchError):build.transform_splash(new)
 with pytest.raises(build.PatchError):build.transform_splash(old.replace('0x1b58','0x1b59'))


def test_application_dispatch_and_original_fallback():
 old='''.class public Lcom/vocies61/marvelcosmic/SpexApplication;
.method public startGame(Landroid/app/Activity;)V
    .registers 2
    invoke-direct {p0, p1}, Lcom/vocies61/marvelcosmic/SpexApplication;->n_StartGame(Landroid/app/Activity;)V
    return-void
.end method
.method private native n_StartGame(Landroid/app/Activity;)V
.end method
'''
 new=build.transform_application(old)
 assert new.index('->tryStart(')<new.index('if-nez v0, :enhanced_done')<new.index('->n_StartGame(')
 assert '.method private native n_StartGame(Landroid/app/Activity;)V\n.end method' in new
 with pytest.raises(build.PatchError):build.transform_application(new)


def test_window_command_guard_is_local_and_rejects_unknown_context():
 # Authored minimal dispatch fixture; not extracted game code.
 source='''.class public Lorg/libsdl/app/SDLActivity$SDLCommandHandler;
.super Landroid/os/Handler;
.method public handleMessage(Landroid/os/Message;)V
    .registers 10
    if-eq v2, v5, :cond_91
    return-void
    :cond_91
    invoke-virtual {p1}, Ljava/lang/Integer;->intValue()I

    move-result p1

    if-eqz p1, :cond_c3
    const/16 p1, 0x1706
    return-void
    :cond_c3
    const/16 p1, 0x100
    return-void
.end method
.method public unrelated()V
    .registers 1
    return-void
.end method
'''
 new=build.transform_window_command(source)
 insertion='    invoke-static {p1}, Lcom/vocies61/marvelcosmic/EnhancedUi;->splashWindowStyle(I)I\n    move-result p1\n\n'
 assert new.count(insertion)==1
 assert new.replace(insertion,'')==source
 for bad in [new,source.replace('0x100','0x101'),source.replace('0x1706','0x1707'),source.replace('if-eq v2, v5, :cond_91','if-eq v2, v4, :cond_91')]:
  with pytest.raises(build.PatchError):build.transform_window_command(bad)


def test_private_paths_and_original_build_guards(tmp_path):
 with pytest.raises(build.PatchError):build.private(ROOT/'test.apk')
 bad=tmp_path/'wrong.apk';bad.write_bytes(b'bad')
 with pytest.raises(build.PatchError,match='checksum'):build.main(['--apk',str(bad),'--artwork',str(tmp_path/'missing.png')])


def test_member_comparison_rejects_unrelated_change(tmp_path):
 import zipfile
 old=tmp_path/'original.apk';new=tmp_path/'new.apk'
 original={'classes.dex':b'original main','classes2.dex':b'original display','lib/arm64-v8a/game.so':b'preserve native','assets/logo.dat':b'preserve logo'}
 with zipfile.ZipFile(old,'w') as z:
  for n,data in original.items():z.writestr(n,data)
 payloads={}
 for n in build.ADDITIONS|build.CHANGES:
  p=tmp_path/str(len(payloads));p.write_bytes(n.encode());payloads[n]=p
 with zipfile.ZipFile(new,'w') as z:
  for n,data in original.items():z.writestr(n,b'changed unrelated logo' if n=='assets/logo.dat' else payloads[n].read_bytes() if n in payloads else data)
  for n in build.ADDITIONS:z.writestr(n,payloads[n].read_bytes())
 with pytest.raises(build.PatchError,match='Unrelated'):build.verify_members(old,new,payloads)


def test_managed_success_failure_and_handoff_execution(tmp_path):
 dotnet=os.environ.get('MCI_DOTNET')
 if not dotnet:pytest.skip('Set MCI_DOTNET to run authored managed/native integration tests')
 dotnet=Path(dotnet);runtime_root=dotnet.parent
 refs=sorted((runtime_root/'packs/Microsoft.NETCore.App.Ref').glob('*/ref/net8.0'))[-1]
 csc=sorted((runtime_root/'sdk').glob('*/Roslyn/bincore/csc.dll'))[-1]
 fixture=ROOT/'tests/fixtures/marvel_enhancements'
 compiler=shutil.which('cc');assert compiler,'A host C compiler is needed'
 native=tmp_path/'libandroid4x3_marvel.so'
 subprocess.run([compiler,'-shared','-fPIC',str(fixture/'native_callbacks.c'),'-o',str(native)],check=True,capture_output=True)
 output=tmp_path/'Harness.dll'
 args=[str(dotnet),str(csc),'-noconfig','-nostdlib+','-target:exe','-out:'+str(output)]+['-reference:'+str(p) for p in sorted(refs.glob('*.dll'))]+[str(HERE/'Enhancements.cs'),str(fixture/'FakeApis.cs'),str(fixture/'Harness.cs')]
 result=subprocess.run(args,capture_output=True,text=True);assert result.returncode==0,result.stdout+result.stderr
 (tmp_path/'Harness.runtimeconfig.json').write_text(json.dumps({'runtimeOptions':{'tfm':'net8.0','framework':{'name':'Microsoft.NETCore.App','version':'8.0.0'}}}))
 for mode in ['success','handoff-error','startup-error']:
  log=tmp_path/mode;log.mkdir()
  result=subprocess.run([str(dotnet),str(output),mode,str(log)],capture_output=True,text=True,timeout=15)
  assert result.returncode==0,result.stdout+result.stderr
  assert 'PASS '+mode in result.stdout
  text=(log/'android4x3-enhancements.txt').read_text()
  assert 'frame handoff and completion observation armed before initial context load' in text
  assert 'frame handoff unavailable:' not in text
  assert 'splash handoff acknowledged:' in text
  if mode!='startup-error':assert text.index('normal game completion confirmed')<text.index('FMOD release: OK')


def test_native_jni_table_indices_match_jdk(tmp_path):
 jdk=os.environ.get('MCI_JDK')
 if not jdk:pytest.skip('Set MCI_JDK to check JNI ABI against JDK headers')
 jdk=Path(jdk);names={'GetStaticMethodID':113,'CallStaticBooleanMethod':117,'CallStaticVoidMethod':141,'NewStringUTF':167,'GetArrayLength':171,'GetByteArrayElements':184,'ReleaseByteArrayElements':192,'ExceptionCheck':228,'NewGlobalRef':21,'DeleteGlobalRef':22,'DeleteLocalRef':23,'ExceptionClear':17}
 lines=['#include <jni.h>','#include <stddef.h>','int main(void){']
 for name,index in names.items():lines.append(f'if(offsetof(struct JNINativeInterface_,{name})/sizeof(void*)!={index})return {index};')
 lines.append('if(offsetof(struct JNIInvokeInterface_,GetEnv)/sizeof(void*)!=6)return 99;return 0;}')
 src=tmp_path/'abi.c';src.write_text('\n'.join(lines));exe=tmp_path/'abi'
 subprocess.run(['cc','-I'+str(jdk/'include'),'-I'+str(jdk/'include/linux'),str(src),'-o',str(exe)],check=True,capture_output=True)
 subprocess.run([str(exe)],check=True)


def test_native_jni_loader_and_callbacks(tmp_path):
 jdk=os.environ.get('MCI_JDK')
 if not jdk:pytest.skip('Set MCI_JDK to execute the authored JNI loader harness')
 jdk=Path(jdk);exe=tmp_path/'jni-harness'
 args=['cc','-std=c11','-I'+str(jdk/'include'),'-I'+str(jdk/'include/linux'),str(HERE/'bridge.c'),str(ROOT/'tests/fixtures/marvel_enhancements/jni_harness.c'),'-o',str(exe)]
 result=subprocess.run(args,capture_output=True,text=True);assert result.returncode==0,result.stdout+result.stderr
 for mode in ['success','missing-api','oversize','managed-error']:
  result=subprocess.run([str(exe),mode],capture_output=True,text=True)
  assert result.returncode==0,result.stdout+result.stderr+f' mode={mode}, rc={result.returncode}'
  assert 'PASS '+mode in result.stdout


def test_java_finish_waits_for_target_activity_destruction(tmp_path):
 jdk=os.environ.get('MCI_JDK')
 if not jdk:pytest.skip('Set MCI_JDK to execute authored Java lifecycle tests')
 jdk=Path(jdk);src=tmp_path/'src';classes=tmp_path/'classes';classes.mkdir()
 fixtures={
 'android/os/Bundle.java':'package android.os; public class Bundle {}',
 'android/util/Log.java':'package android.util; public class Log { public static int i(String t,String m){return 0;} public static int e(String t,String m,Throwable e){return 0;} }',
 'android/content/res/AssetManager.java':'package android.content.res; public class AssetManager { public java.io.InputStream open(String name) throws java.io.IOException {return new java.io.ByteArrayInputStream(new byte[2048]);} }',
 'android/app/Application.java':'''package android.app; import java.util.*; import android.os.Bundle;
 public class Application {
  public interface ActivityLifecycleCallbacks {void onActivityDestroyed(Activity a);void onActivityCreated(Activity a,Bundle b);void onActivityStarted(Activity a);void onActivityResumed(Activity a);void onActivityPaused(Activity a);void onActivityStopped(Activity a);void onActivitySaveInstanceState(Activity a,Bundle b);}
  public final List<ActivityLifecycleCallbacks> callbacks=new ArrayList<>();
  public void registerActivityLifecycleCallbacks(ActivityLifecycleCallbacks c){callbacks.add(c);}
  public void unregisterActivityLifecycleCallbacks(ActivityLifecycleCallbacks c){callbacks.remove(c);}
  public void destroy(Activity a){a.destroyed=true;for(ActivityLifecycleCallbacks c:new ArrayList<>(callbacks))c.onActivityDestroyed(a);}
 }''',
 'android/app/Activity.java':'''package android.app;
 public class Activity {public boolean finishing,destroyed; public final Application app;
  public Activity(Application p){app=p;}public boolean isFinishing(){return finishing;}public boolean isDestroyed(){return destroyed;}
  public void runOnUiThread(Runnable r){r.run();}public Application getApplication(){return app;}
  public void finishAndRemoveTask(){finishing=true;}public android.content.res.AssetManager getAssets(){return new android.content.res.AssetManager();}
 }''',
 'com/vocies61/marvelcosmic/EnhancedUi.java':'package com.vocies61.marvelcosmic; public class EnhancedUi {public static void failOpen(){}public static boolean handoff(android.app.Activity a){return true;}}',
 'com/vocies61/marvelcosmic/LifecycleHarness.java':'''package com.vocies61.marvelcosmic; import android.app.*;
 public class LifecycleHarness {static int exits;
  public static void main(String[] args) {
   EnhancedBridge.processExit=new Runnable(){public void run(){exits++;}};
   Application app=new Application();Activity target=new Activity(app),other=new Activity(app);
   EnhancedBridge.onFinished(target);EnhancedBridge.onFinished(target);
   if(!target.finishing || exits!=0 || app.callbacks.size()!=1)throw new AssertionError("Exit must wait for destruction and register once");
   app.destroy(other);if(exits!=0)throw new AssertionError("Unrelated Activity destroyed");
   app.destroy(target);if(exits!=1 || !app.callbacks.isEmpty())throw new AssertionError("Exit did not follow target destruction exactly once");
   System.out.println("PASS activity lifecycle");
  }
 }'''}
 paths=[]
 for name,data in fixtures.items():
  p=src/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(data);paths.append(p)
 args=[str(jdk/'bin/javac'),'-d',str(classes),*[str(x) for x in paths],str(HERE/'java/com/vocies61/marvelcosmic/EnhancedBridge.java')]
 result=subprocess.run(args,capture_output=True,text=True);assert result.returncode==0,result.stdout+result.stderr
 result=subprocess.run([str(jdk/'bin/java'),'-cp',str(classes),'com.vocies61.marvelcosmic.LifecycleHarness'],capture_output=True,text=True)
 assert result.returncode==0,result.stdout+result.stderr
 assert 'PASS activity lifecycle' in result.stdout


def test_java_startup_fade_original_window_policy_and_pause_recovery(tmp_path):
 import runpy
 jdk=os.environ.get('MCI_JDK')
 if not jdk:pytest.skip('Set MCI_JDK to execute authored startup UI tests')
 jdk=Path(jdk);src=tmp_path/'src';classes=tmp_path/'classes';classes.mkdir()
 fixtures=runpy.run_path(str(ROOT/'tests/fixtures/marvel_enhancements/ui_fixtures.py'))['SOURCES']
 paths=[]
 for name,data in fixtures.items():
  p=src/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(data);paths.append(p)
 result=subprocess.run([str(jdk/'bin/javac'),'-source','8','-target','8','-d',str(classes),*[str(p) for p in paths],str(HERE/'java/com/vocies61/marvelcosmic/EnhancedUi.java')],capture_output=True,text=True)
 assert result.returncode==0,result.stdout+result.stderr
 for mode in ['success','paused','detached','legacy','late-black','failed']:
  log=tmp_path/mode;log.mkdir()
  result=subprocess.run([str(jdk/'bin/java'),'-Dmarvel.ui.logdir='+str(log),'-cp',str(classes),'com.vocies61.marvelcosmic.StartupHarness',mode],capture_output=True,text=True,timeout=10)
  assert result.returncode==0,result.stdout+result.stderr+f' mode={mode}'
  assert 'PASS startup '+mode in result.stdout
  text=(log/'android4x3-enhancements.txt').read_text()
  assert text.count('startup windowed-style request kept Android full-screen while PNG active')==1
