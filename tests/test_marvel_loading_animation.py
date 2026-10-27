"""Private-asset-free loading animation regressions against the real Java helper."""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import runpy
import subprocess
import zipfile
import pytest

ROOT=Path(__file__).resolve().parents[1]
HERE=ROOT/'experiments/marvel-startup-exit'
spec=importlib.util.spec_from_file_location('marvel_loading_build',HERE/'build-local.py')
build=importlib.util.module_from_spec(spec);spec.loader.exec_module(build)

HARNESS=r'''package com.vocies61.marvelcosmic;
import android.app.*;import android.os.*;import android.view.*;import android.graphics.*;
import android.content.res.AssetManager;
public class AnimationHarness {
 static void check(boolean ok,String why){if(!ok)throw new AssertionError(why);}
 static void close(float a,float b){check(Math.abs(a-b)<.001f,"Mapping: "+a+" != "+b);}
 static Canvas.IconDraw last(){return Canvas.icons.get(Canvas.icons.size()-1);}
 static volatile boolean returned,result;
 public static void main(String[] args)throws Exception {
  Looper.getMainLooper();String mode=args[0];AssetManager.iconMode="ok";
  if(mode.equals("missing") || mode.equals("invalid") || mode.equals("dimensions") || mode.equals("oom"))AssetManager.iconMode=mode;
  if(mode.equals("reference")){View.width=1280;View.height=960;}
  if(mode.equals("wide")){View.width=2000;View.height=1080;}
  if(mode.equals("portrait")){View.width=900;View.height=1240;}
  Activity activity=new Activity();SplashView splash=new SplashView(activity);EnhancedUi.attach(splash);
  if(!AssetManager.iconMode.equals("ok")) {
   Handler.advanceTo(1500);check(Canvas.icons.isEmpty(),"Bad sheet drew an icon");
   check(Canvas.alphas.get(Canvas.alphas.size()-1)==255 && splash.finishes==0,"Optional icon failure broke PNG/loading");
   check(EnhancedUi.splashWindowStyle(0)==1,"Optional failure disabled guard");
   check(BitmapFactory.sheet==null || BitmapFactory.sheet.recycled,"Bad sheet leaked");
   EnhancedUi.failOpen();check(BitmapFactory.art.recycled,"Error cleanup leaked art");
   System.out.println("PASS animation "+mode);return;
  }
  if(mode.equals("frames")) {
   long[] ticks={0,49,50,399,400,1949,1950,1999,2000,4050};
   int[] frames={0,0,1,7,8,38,39,39,0,1};
   for(int i=0;i<ticks.length;i++){SystemClock.now=ticks[i];EnhancedUi.draw(splash,new Canvas());check(last().frame==frames[i],"50ms frame/row/2s wrap incorrect");}
   check(BitmapFactory.decodes==2,"Decoding during draw");
  }else if(mode.equals("steady")) {
   Handler.advanceTo(1000);int count=Canvas.icons.size();Handler.advanceTo(3100);
   check(Canvas.icons.size()>count+35,"Animation stopped after initial fade-in");
   for(Canvas.IconDraw draw:Canvas.icons)check(draw.frame==(int)((draw.time/50)%40),"Scheduler controls phase instead of monotonic time");
   check(BitmapFactory.decodes==2 && splash.finishes==0,"Steady animation changed loading lifetime/decoded again");
   // A pause drops draws, not phase; resume picks current monotonic frame.
   splash.drawing=false;int pausedCount=Canvas.icons.size();Handler.advanceTo(5000);
   check(Canvas.icons.size()==pausedCount,"Detached/non-drawing view animated");
   splash.drawing=true;EnhancedUi.draw(splash,new Canvas());check(last().frame==20,"Resume restarted animation phase");
  }else if(mode.equals("fade-start") || mode.equals("early-ready")) {
   long start=mode.equals("early-ready")?0:1137;
   Handler.advanceTo(start);EnhancedUi.draw(splash,new Canvas());int before=Canvas.icons.size();
   Thread worker=new Thread(()->{result=EnhancedUi.handoff(activity);returned=true;});worker.start();
   for(int i=0;i<1000 && !Handler.hasCurrent();i++)Thread.sleep(1);
   check(Handler.hasCurrent(),"Missing existing readiness handoff");Handler.advanceTo(start);
   EnhancedUi.draw(splash,new Canvas());
   check(Canvas.icons.size()==before && splash.finishes==0 && !returned,"Fade-start must remove whole icon without finishing splash/latch");
   check(EnhancedUi.splashWindowStyle(0)==1,"Icon hide disabled validated fullscreen guard");
   Handler.advanceTo(start+1999);check(!returned,"Changed 2s fade-out");
   check(Canvas.icons.size()==before,"Late invalidate revived icon during fade");
   Handler.advanceTo(start+2024);check(!returned && EnhancedUi.splashWindowStyle(0)==1,"Changed black hold/guard lifetime");
   Handler.advanceTo(start+2520);worker.join(1000);check(returned && result && splash.finishes==1,"Added icon minimum duration/loop completion wait");
   check(BitmapFactory.sheet.recycled && BitmapFactory.art.recycled,"Normal completion leaked bitmaps");
   Handler.advanceTo(start+65000);EnhancedUi.draw(splash,new Canvas());
   check(Canvas.icons.size()==before && EnhancedUi.splashWindowStyle(0)==0,"Late callback restored icon/guard");
   System.out.println("PASS animation "+mode);return;
  }else if(mode.equals("reference") || mode.equals("retroid") || mode.equals("wide") || mode.equals("portrait")) {
   Handler.advanceTo(516);Canvas.IconDraw d=last();
   int u=Math.min(View.width/4,View.height/3);float scale=(u*4)/1280f;
   float left=(View.width-u*4)/2f,top=(View.height-u*3)/2f;
   close(d.left,left+1104*scale);close(d.top,top+800*scale);
   close(d.right,left+1264*scale);close(d.bottom,top+960*scale);
   close(d.left+16*scale,left+1120*scale);close(d.top+16*scale,top+816*scale);
   close(left+u*4-(d.right-16*scale),32*scale);
   close(top+u*3-(d.bottom-16*scale),16*scale);
   if(mode.equals("retroid")){close(d.left,1069.5f);close(d.top,850f);close(d.right,1224.5f);close(d.bottom,1005f);}
   check(Canvas.iconPaint!=Canvas.artPaint && Canvas.artPaint.alpha==255,"Icon corrupted splash paint");
  }else if(mode.equals("failed")) {
   Handler.advanceTo(700);int before=Canvas.icons.size();EnhancedUi.failOpen();
   EnhancedUi.draw(splash,new Canvas());Handler.advanceTo(1000);
   check(Canvas.icons.size()==before && splash.finishes==1,"Failure retained/restored icon");
   check(BitmapFactory.sheet.recycled && EnhancedUi.splashWindowStyle(0)==0,"Failure retained resource/guard");
   System.out.println("PASS animation "+mode);return;
  }else throw new AssertionError("Unknown scenario");
  int count=Canvas.icons.size();EnhancedUi.detached(splash);
  check(BitmapFactory.sheet.recycled && BitmapFactory.art.recycled,"Detach leaked bitmaps");
  EnhancedUi.draw(splash,new Canvas());Handler.advanceTo(SystemClock.now+65000);
  check(Canvas.icons.size()==count && EnhancedUi.splashWindowStyle(0)==0,"Late callback revived detached splash");
  System.out.println("PASS animation "+mode);
 }
}'''

@pytest.fixture(scope='module')
def animation_java(tmp_path_factory):
 jdk=os.environ.get('MCI_JDK')
 if not jdk:pytest.skip('Set MCI_JDK to execute real loading renderer with authored Android doubles')
 jdk=Path(jdk);tmp=tmp_path_factory.mktemp('animation-java');classes=tmp/'classes';classes.mkdir()
 sources=runpy.run_path(str(ROOT/'tests/fixtures/marvel_enhancements/ui_fixtures.py'))['SOURCES'].copy()
 sources['com/vocies61/marvelcosmic/AnimationHarness.java']=HARNESS
 paths=[]
 for name,code in sources.items():
  p=tmp/'src'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(code);paths.append(p)
 result=subprocess.run([str(jdk/'bin/javac'),'-source','8','-target','8','-d',str(classes),*map(str,paths),str(HERE/'java/com/vocies61/marvelcosmic/EnhancedUi.java')],capture_output=True,text=True)
 assert result.returncode==0,result.stdout+result.stderr
 return jdk,classes

@pytest.mark.parametrize('mode',['frames','steady','reference','retroid','wide','portrait','fade-start','early-ready','missing','invalid','dimensions','oom','failed'])
def test_animation_timing_mapping_visibility_and_lifecycle(animation_java,tmp_path,mode):
 jdk,classes=animation_java
 result=subprocess.run([str(jdk/'bin/java'),'-Dmarvel.ui.logdir='+str(tmp_path),'-cp',str(classes),'com.vocies61.marvelcosmic.AnimationHarness',mode],capture_output=True,text=True,timeout=10)
 assert result.returncode==0,result.stdout+result.stderr
 assert 'PASS animation '+mode in result.stdout


def test_loading_kit_only_reads_approved_sheet_never_runs_scripts(tmp_path,monkeypatch):
 # Synthetic bytes; user sheet/artwork is never a test fixture in Git.
 data=b'authored synthetic fixture';pin=hashlib.sha256(data).hexdigest()
 monkeypatch.setattr(build,'ICON_SHA',pin)
 kit=tmp_path/'loading.zip'
 with zipfile.ZipFile(kit,'w') as z:
  z.writestr(build.ICON_KIT_MEMBER,data)
  z.writestr('xmen-purple-loading/make_neon_spin.py','raise SystemExit("never run")')
  z.writestr('../escape.txt','never extract')
 before=kit.read_bytes()
 assert build.read_loading_sheet(kit)==data
 assert kit.read_bytes()==before and not (tmp_path/'escape.txt').exists()
 monkeypatch.setattr(build,'ICON_SHA','0'*64)
 with pytest.raises(build.PatchError,match='checksum'):build.read_loading_sheet(kit)
 with zipfile.ZipFile(kit,'w') as z:z.writestr('wrong.png',data)
 with pytest.raises(build.PatchError,match='one bounded'):build.read_loading_sheet(kit)
 kit.write_bytes(b'invalid ZIP')
 with pytest.raises(build.PatchError,match='Invalid loading kit'):build.read_loading_sheet(kit)
 with zipfile.ZipFile(kit,'w') as z:z.writestr(build.ICON_KIT_MEMBER,b'x'*(1024*1024+1))
 with pytest.raises(build.PatchError,match='bounded'):build.read_loading_sheet(kit)


def test_optional_sheet_archive_allowlist_is_exact(tmp_path,monkeypatch):
 # Authored archive fixtures test both optional modes and reject extras/omission.
 monkeypatch.setattr(build,'BASELINE_DEX_SHA',hashlib.sha256(b'display patch').hexdigest())
 original=tmp_path/'original.zip';output=tmp_path/'output.zip'
 with zipfile.ZipFile(original,'w') as z:
  for name in ['classes.dex','classes2.dex','assets/original-logo.dat']:z.writestr(name,b'original')
 for icon in [False,True]:
  names=build.ADDITIONS|build.CHANGES|({build.ICON_ENTRY} if icon else set());payloads={}
  for i,name in enumerate(sorted(names)):
   p=tmp_path/f'{i}.payload';p.write_bytes(b'display patch' if name=='classes2.dex' else name.encode());payloads[name]=p
  def archive(extra=None,omit=None):
   with zipfile.ZipFile(output,'w') as z:
    z.writestr('assets/original-logo.dat',b'original')
    for name,p in payloads.items():
     if name!=omit:z.writestr(name,p.read_bytes())
    if extra:z.writestr(extra,b'no')
  archive();report=build.verify_members(original,output,payloads)
  assert set(report['added_members'])==names-build.CHANGES
  archive(extra='unapproved.dat')
  with pytest.raises(build.PatchError,match='removed/added'):build.verify_members(original,output,payloads)
  archive(omit=build.ICON_ENTRY if icon else build.PNG_ENTRY)
  with pytest.raises(build.PatchError,match='removed/added'):build.verify_members(original,output,payloads)


def test_validated_guard_handoff_and_unrelated_runtime_sources_preserved():
 source=(HERE/'java/com/vocies61/marvelcosmic/EnhancedUi.java').read_text()
 # Exact authored method blocks from validated 6cbe; works in source ZIPs without Git.
 for start,end,pin in [
  ('    public static int splashWindowStyle(','    public static boolean handoff(','33ef04fd2bdd0f887d8a53c7ee0a8b37179b52a35f7bad94d282730b345b9a90'),
  ('    public static boolean handoff(','    public static void failOpen(','25a495585bffb4e634ce06ed939d26c7217f20aa498f844f06c743e619ba31e2')]:
  assert hashlib.sha256(source[source.index(start):source.index(end)].encode()).hexdigest()==pin
 for declaration in ['FADE_IN_MS=500','FADE_OUT_MS=2000','BLACK_HOLD_MS=500','FADE_RECOVERY_MS=4000','HANDOFF_WAIT_MS=4500','MAIN.postDelayed(watchdog,60000)']:
  assert declaration in source
 profile=json.loads((ROOT/'workshop/repairs/marvel-cosmic-invasion.json').read_text())
 authorized_changes={
  'experiments/marvel-startup-exit/build-local.py',
  'experiments/marvel-startup-exit/java/com/vocies61/marvelcosmic/EnhancedUi.java',
  'tests/fixtures/marvel_enhancements/ui_fixtures.py','tests/test_marvel_enhancements.py'}
 changed={name for name,pin in profile['validated_source_checksums'].items() if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=pin}
 assert changed==authorized_changes
