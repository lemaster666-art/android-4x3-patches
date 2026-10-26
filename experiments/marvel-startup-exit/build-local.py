"""Combined, opt-in Marvel startup/Exit experiment. No proprietary files are bundled."""
from __future__ import annotations
import argparse
from datetime import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
import zlib

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
sys.path.insert(0,str(REPO/'src'))
from android4x3.apk import _is_v1_signature, _stdlib_core_repack, inspect_apk, verify_zip
from android4x3.errors import PatchError
from android4x3.signing import align_apk,sign_apk,verify_alignment,find_android_tool

ORIGINAL_SHA='d0c9587575f5bba17a5ac2f5ea3e56700b362f658aaaff84ae11c9b67eae18c9'
DEX_SHA='a9675bcd7552febb03e5bcca74a4c222faebaeae2d91ef86f7ddf5ac59d78eda'
BASELINE_DEX_SHA='0accefb0c85def38839d3e3015d130967a21b7545869f6cefcd7efc23bcc2fe1'
PNG_ENTRY='assets/android4x3/splash.png'
DLL_ENTRY='assets/android4x3/marvel-enhancements.bin'
SO_ENTRY='lib/arm64-v8a/libandroid4x3_marvel.so'
ADDITIONS={'classes3.dex',PNG_ENTRY,DLL_ENTRY,SO_ENTRY}
CHANGES={'classes.dex','classes2.dex'}


def sha(path:Path,algorithm='sha256')->str:
 with path.open('rb') as f:return hashlib.file_digest(f,algorithm).hexdigest()

def load_module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def baseline():return load_module('marvel_existing_patch',REPO/'games/marvel-cosmic-invasion/patch_impl.py')
def installer():return load_module('marvel_existing_installer',REPO/'games/marvel-cosmic-invasion/local_build.py')

def private(path:Path)->Path:
 path=path.expanduser().resolve()
 if path.is_relative_to(REPO):raise PatchError('Keep APKs, artwork, cache, outputs and credentials outside the Git checkout')
 return path

def run(args,env=None):
 result=subprocess.run([str(x) for x in args],capture_output=True,text=True,env=env)
 if result.returncode:raise PatchError('Tool failed: '+str(args[0])+'\n'+(result.stdout+result.stderr)[-5000:])
 return result.stdout

def lz4_block(data:bytes,expected:int)->bytes:
 if not 0<expected<=32*1024*1024:raise PatchError('Assembly size guard failed')
 out=bytearray();pos=0
 def length(base):
  nonlocal pos
  if base==15:
   while True:
    if pos>=len(data):raise PatchError('Truncated LZ4 length')
    x=data[pos];pos+=1;base+=x
    if x!=255:break
  return base
 while pos<len(data):
  token=data[pos];pos+=1;literal=length(token>>4)
  if pos+literal>len(data) or len(out)+literal>expected:raise PatchError('Invalid LZ4 literal')
  out.extend(data[pos:pos+literal]);pos+=literal
  if pos==len(data):break
  if pos+2>len(data):raise PatchError('Truncated LZ4 offset')
  offset=int.from_bytes(data[pos:pos+2],'little');pos+=2
  if not offset or offset>len(out):raise PatchError('Invalid LZ4 back reference')
  count=length(token&15)+4
  if len(out)+count>expected:raise PatchError('LZ4 output exceeds declared size')
  pattern=bytes(out[-offset:]);out.extend((pattern*((count+offset-1)//offset))[:count])
 if len(out)!=expected:raise PatchError('LZ4 output length mismatch')
 return bytes(out)

def decode_assembly(data:bytes)->bytes:
 if data[:4]==b'XALZ':
  if len(data)<12:raise PatchError('Truncated XALZ header')
  data=lz4_block(data[12:],struct.unpack_from('<I',data,8)[0])
 if data[:2]!=b'MZ':raise PatchError('Expected managed PE assembly')
 return data

def validate_png(path:Path)->dict:
 size=path.stat().st_size
 if size>32*1024*1024:raise PatchError('PNG must be at most 32 MiB')
 data=path.read_bytes()
 if data[:8]!=b'\x89PNG\r\n\x1a\n':raise PatchError('Select an original PNG image')
 pos=8;types=[];width=height=0
 while pos<len(data):
  if pos+12>len(data):raise PatchError('Truncated PNG chunk')
  length=struct.unpack_from('>I',data,pos)[0];kind=data[pos+4:pos+8];end=pos+12+length
  if end>len(data):raise PatchError('Truncated PNG data')
  if zlib.crc32(data[pos+4:end-4])&0xffffffff!=struct.unpack_from('>I',data,end-4)[0]:raise PatchError('PNG CRC mismatch')
  if not types and (kind!=b'IHDR' or length!=13):raise PatchError('Invalid PNG header')
  if kind==b'IHDR':
   width,height=struct.unpack_from('>II',data,pos+8)
   if not(1<=width<=4096 and 1<=height<=4096 and width*height<=12*1024*1024):raise PatchError('PNG dimensions exceed the splash memory limit')
  types.append(kind);pos=end
  if kind==b'IEND':break
 if not types or types[-1]!=b'IEND' or b'IDAT' not in types or pos!=len(data):raise PatchError('Incomplete PNG or trailing data')
 return {'width':width,'height':height,'bytes':size,'sha256':hashlib.sha256(data).hexdigest()}

def transform_splash(source:str)->str:
 module=baseline();blocks=module.method_blocks(source)
 required={
  '.method start(Ljava/lang/Runnable;)V':'''    .registers 2
    iput-object p1, p0, Lcom/vocies61/marvelcosmic/SplashView;->onFinished:Ljava/lang/Runnable;
    invoke-static {p0}, Lcom/vocies61/marvelcosmic/EnhancedUi;->attach(Lcom/vocies61/marvelcosmic/SplashView;)V
    return-void''',
  '.method protected onDraw(Landroid/graphics/Canvas;)V':'''    .registers 2
    invoke-static {p0,p1}, Lcom/vocies61/marvelcosmic/EnhancedUi;->draw(Lcom/vocies61/marvelcosmic/SplashView;Landroid/graphics/Canvas;)V
    return-void''',
  '.method public onTouchEvent(Landroid/view/MotionEvent;)Z':'''    .registers 3
    const/4 v0, 0x1
    return v0'''}
 if 'finishEnhancedSplash' in source:raise PatchError('Splash already modified')
 for signature,body in required.items():
  if signature not in blocks:raise PatchError('Unsupported SplashView method context')
  if signature.startswith('.method start') and '0x1b58' not in blocks[signature]:raise PatchError('Unsupported splash lifetime')
  source=source.replace(blocks[signature],signature+'\n'+body+'\n.end method')
 signature='.method protected onDetachedFromWindow()V'
 original=blocks.get(signature,'')
 if original.count('    return-void')!=1:raise PatchError('Unexpected splash detach method')
 source=source.replace(original,original.replace('    return-void','    invoke-static {p0}, Lcom/vocies61/marvelcosmic/EnhancedUi;->detached(Lcom/vocies61/marvelcosmic/SplashView;)V\n    return-void'))
 return source+'''\n.method public finishEnhancedSplash()V
    .registers 1
    invoke-direct {p0}, Lcom/vocies61/marvelcosmic/SplashView;->dismiss()V
    return-void
.end method
'''

def transform_application(source:str)->str:
 signature='.method public startGame(Landroid/app/Activity;)V';blocks=baseline().method_blocks(source);method=blocks.get(signature,'')
 call='    invoke-direct {p0, p1}, Lcom/vocies61/marvelcosmic/SpexApplication;->n_StartGame(Landroid/app/Activity;)V'
 if method.count(call)!=1 or '.registers 2' not in method or 'EnhancedBridge' in source:raise PatchError('Unsupported Java game entry point')
 replacement=method.replace('.registers 2','.registers 3').replace(call,'''    invoke-static {p1}, Lcom/vocies61/marvelcosmic/EnhancedBridge;->tryStart(Landroid/app/Activity;)Z
    move-result v0
    if-nez v0, :enhanced_done
'''+call+'\n    :enhanced_done')
 return source.replace(method,replacement)

def patch_classes(original:bytes,work:Path)->Path:
 if hashlib.sha256(original).hexdigest()!=DEX_SHA:raise PatchError('Unsupported original classes.dex')
 module=baseline();module.check_dex(original)
 dex=work/'classes-original.dex';dex.write_bytes(original);tree=work/'original-smali';result=work/'classes.dex'
 module.smali_command('org.jf.baksmali.Main','disassemble','--api','26',str(dex),'-o',str(tree))
 mapping={'com/vocies61/marvelcosmic/SplashView.smali':transform_splash,'com/vocies61/marvelcosmic/SpexApplication.smali':transform_application}
 before={str(p.relative_to(tree)):p.read_text() for p in tree.rglob('*.smali')}
 for name,transform in mapping.items():
  p=tree/name;p.write_text(transform(before[name]))
 for p in tree.rglob('*.smali'):
  name=str(p.relative_to(tree))
  if name not in mapping and p.read_text()!=before[name]:raise PatchError('Unrelated smali changed')
 module.smali_command('org.jf.smali.Main','assemble','--api','26','--jobs','1',str(tree),'-o',str(result))
 module.check_dex(result.read_bytes());return result

def extra_tools(cache:Path,system:str,machine:str)->dict:
 base=installer();config=json.loads((HERE/'tools.json').read_text());host=f'{system}:{machine}'
 if host not in config['dotnet']:raise PatchError('Unsupported compiler host')
 root=cache/'marvel-startup-exit-tools';root.mkdir(parents=True,exist_ok=True,mode=0o700)
 flavor,pin=config['dotnet'][host];version=config['dotnet_version'];archive=root/f'dotnet-sdk-{version}-{flavor}.tar.gz'
 if not archive.exists():
  print('Downloading pinned private .NET SDK (first build only)...',flush=True)
  url=f'https://builds.dotnet.microsoft.com/dotnet/Sdk/{version}/{archive.name}'
  with urllib.request.build_opener(base.HTTPSOnly()).open(url,timeout=180) as source,archive.with_suffix('.partial').open('wb') as dest:shutil.copyfileobj(source,dest)
  archive.with_suffix('.partial').replace(archive)
 if sha(archive,'sha512')!=pin:raise PatchError('Pinned .NET SDK checksum mismatch')
 sdk=root/f'dotnet-{version}-{flavor}'
 if not (sdk/'dotnet').is_file():base.extract(archive,sdk)
 zig_url,zig_pin=config['zig'][host];zig_archive=base.download(zig_url,root/Path(zig_url).name,zig_pin);zig_root=root/f'zig-0.13.0-{system}-{machine}'
 if not (zig_root/'ziglang/zig').is_file():base.extract(zig_archive,zig_root)
 zig=zig_root/'ziglang/zig';zig.chmod(0o700)
 url,pin=config['platform'];platform_zip=base.download(url,root/'platform-34-ext7_r03.zip',pin);platform_root=root/'platform-34'
 if not (platform_root/'android-34/android.jar').is_file():base.extract(platform_zip,platform_root)
 env=os.environ.copy();env.update(DOTNET_CLI_HOME=str(root/'dotnet-home'),DOTNET_CLI_TELEMETRY_OPTOUT='1',DOTNET_SKIP_FIRST_TIME_EXPERIENCE='1',ZIG_GLOBAL_CACHE_DIR=str(root/'zig-cache'))
 return {'dotnet':sdk/'dotnet','csc':sdk/f'sdk/{version}/Roslyn/bincore/csc.dll','zig':zig,'android_jar':platform_root/'android-34/android.jar','env':env}

def compile_payloads(original:Path,work:Path,tools:dict)->dict[str,Path]:
 references=work/'references';references.mkdir()
 with zipfile.ZipFile(original) as z:
  for n in z.namelist():
   if n.startswith('assemblies/') and n.endswith('.dll'):(references/Path(n).name).write_bytes(decode_assembly(z.read(n)))
 assembly=work/'Android4x3.Marvel.Enhancements.dll'
 arguments=['-nostdlib+','-target:library','-deterministic+','-optimize+','-langversion:10','-pathmap:'+str(HERE)+'=/_/marvel-enhancements','-out:'+str(assembly)]+['-reference:'+str(x) for x in sorted(references.glob('*.dll'))]+[str(HERE/'Enhancements.cs')]
 run([tools['dotnet'],tools['csc'],'-noconfig',*arguments],tools['env'])
 classes=work/'java-classes';classes.mkdir();java_sources=sorted((HERE/'java').rglob('*.java'))
 run(['javac','-source','8','-target','8','-bootclasspath',tools['android_jar'],'-d',classes,*java_sources])
 jar=work/'authored-java.jar'
 with zipfile.ZipFile(jar,'w') as z:
  for p in sorted(classes.rglob('*.class')):
   if p.name=='SplashView.class':continue # Authored compile-only signature stub is never shipped.
   z.write(p,p.relative_to(classes).as_posix())
 own_dex=work/'authored-dex';own_dex.mkdir();d8=find_android_tool('apksigner').parent/'lib/d8.jar'
 run(['java','-cp',d8,'com.android.tools.r8.D8','--lib',tools['android_jar'],'--min-api','26','--output',own_dex,jar])
 stub=work/'libdl.so';native=work/'libandroid4x3_marvel.so'
 flags=['cc','-target','aarch64-linux-android','-shared','-nostdlib','-fno-stack-protector','-fno-builtin','-O2']
 run([tools['zig'],*flags,'-Wl,-soname,libdl.so','-o',stub,HERE/'dl_stub.c'],tools['env'])
 run([tools['zig'],*flags,'-fvisibility=hidden','-Wl,-soname,libandroid4x3_marvel.so','-L'+str(work),'-ldl','-o',native,HERE/'bridge.c'],tools['env'])
 data=native.read_bytes()
 if data[:4]!=b'\x7fELF' or struct.unpack_from('<HH',data,16)!=(3,183):raise PatchError('Authored native helper is not an ARM64 shared library')
 return {DLL_ENTRY:assembly,SO_ENTRY:native,'classes3.dex':own_dex/'classes.dex'}

def signature(apk:Path)->str:
 text=run([find_android_tool('apksigner'),'verify','--verbose','--print-certs',apk])
 match=re.search(r'Signer #1 certificate SHA-256 digest: ([0-9a-f]{64})',text)
 if not match:raise PatchError('APK signer certificate was not verified')
 return match[1]

def verify_members(original:Path,output:Path,payloads:dict[str,Path])->dict:
 with zipfile.ZipFile(original) as a,zipfile.ZipFile(output) as b:
  old={n for n in a.namelist() if not _is_v1_signature(n)};new={n for n in b.namelist() if not _is_v1_signature(n)}
  if old-new or new-old!=ADDITIONS:raise PatchError('Unexpected removed/added APK members')
  changed=[];unchanged=0
  for n in old:
   different=hashlib.sha256(a.read(n)).digest()!=hashlib.sha256(b.read(n)).digest()
   if different:
    if n not in CHANGES:raise PatchError('Unrelated APK member changed: '+n)
    changed.append(n)
   else:unchanged+=1
  if set(changed)!=CHANGES:raise PatchError('Both baseline display and startup changes must be present')
  for n,p in payloads.items():
   if hashlib.sha256(b.read(n)).hexdigest()!=sha(p):raise PatchError('Packaged payload mismatch: '+n)
  if hashlib.sha256(b.read('classes2.dex')).hexdigest()!=BASELINE_DEX_SHA:raise PatchError('Working 4:3 transformation changed')
 return {'changed_members':sorted(changed),'added_members':sorted(ADDITIONS),'unchanged_original_members':unchanged}

def build(original:Path,artwork:Path,output:Path,tools:dict)->dict:
 original,artwork,output=map(private,[original,artwork,output]);report_path=output.with_suffix('.json')
 if len({original,artwork,output,report_path})!=4 or output.exists() or report_path.exists():raise PatchError('Inputs/outputs must be distinct; output and report must not already exist')
 if sha(original)!=ORIGINAL_SHA:raise PatchError('Original APK checksum mismatch; unsupported build')
 art=validate_png(artwork);art_sha=sha(artwork);verify_zip(original,full=True,allow_signatures=True);original_signer=signature(original)
 # Never silently replace the signing identity used by the working local build.
 state_base=Path(os.environ.get('XDG_DATA_HOME',str(Path.home()/'Library/Application Support' if platform.system()=='Darwin' else Path.home()/'.local/share')))
 state=private(state_base/'android-4x3-patches')
 if not all((state/n).is_file() for n in ['signing.p12','signing-password.txt','signing-key-password.txt','signing.json']):raise PatchError('Existing Marvel signing identity is missing. Stop; restore your original private patcher signing folder before building this experiment.')
 key_before=sha(state/'signing.p12')
 output.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(prefix='marvel-enhanced-',dir=output.parent) as tmp:
  work=Path(tmp);payloads=compile_payloads(original,work,tools)
  with zipfile.ZipFile(original) as z:
   payloads['classes.dex']=patch_classes(z.read('classes.dex'),work)
   display=work/'classes2.dex';display.write_bytes(baseline().patch_dex(z.read('classes2.dex')));payloads['classes2.dex']=display
  payloads[PNG_ENTRY]=artwork
  unsigned,aligned,signed=[work/n for n in ['unsigned.apk','aligned.apk','signed.apk']]
  _stdlib_core_repack(original,unsigned,{n:p for n,p in payloads.items() if n in CHANGES})
  with zipfile.ZipFile(unsigned,'a',allowZip64=False) as z:
   for n in sorted(ADDITIONS):
    entry=zipfile.ZipInfo(n,(1980,1,1,0,0,0));entry.external_attr=0o600<<16
    z.writestr(entry,payloads[n].read_bytes(),compress_type=zipfile.ZIP_STORED)
  align_apk(unsigned,aligned);sign_apk(aligned,signed);verify_alignment(signed);verify_zip(signed,full=True,allow_signatures=True)
  signer=signature(signed)
  if inspect_apk(original)!=inspect_apk(signed):raise PatchError('Package identity/version changed')
  members=verify_members(original,signed,payloads)
  if sha(original)!=ORIGINAL_SHA or sha(artwork)!=art_sha or sha(state/'signing.p12')!=key_before:raise PatchError('Original input/artwork/signing identity changed during build')
  info={'experimental':True,'device_tested_this_build':False,'output':str(output),'sha256':sha(signed),'bytes':signed.stat().st_size,'original_sha256':ORIGINAL_SHA,'original_unchanged':True,'artwork':art,'original_signer_sha256':original_signer,'signer_sha256':signer,'existing_local_key_reused':True,'baseline_display_dex_sha256':BASELINE_DEX_SHA,'target':{'display':[1240,1080],'picture':[1240,930],'top_bottom_borders':[75,75]},**members}
  with output.open('xb') as dest,signed.open('rb') as src:shutil.copyfileobj(src,dest)
  output.chmod(0o600)
  if sha(output)!=info['sha256']:output.unlink();raise PatchError('Final copy checksum mismatch')
  try:
   with report_path.open('x') as f:json.dump(info,f,indent=2);f.write('\n')
   report_path.chmod(0o600)
  except Exception:output.unlink();raise
 return info

def pick(prompt:str)->Path:
 result=run(['osascript','-e','on run argv','-e','return POSIX path of (choose file with prompt (item 1 of argv))','-e','end run',prompt])
 return Path(result.strip())

def main(argv=None):
 os.umask(0o077)
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apk',type=Path);parser.add_argument('--artwork',type=Path);parser.add_argument('--output',type=Path);parser.add_argument('--cache',type=Path);args=parser.parse_args(argv)
 system,machine=platform.system(),platform.machine()
 if system=='Darwin' and tuple(map(int,platform.mac_ver()[0].split('.')[:1]))<(12,):raise PatchError('The experimental compiler requires macOS 12 or newer')
 original=args.apk or (pick('Choose your ORIGINAL Marvel Cosmic Invasion APK') if system=='Darwin' else None)
 artwork=args.artwork or (pick('Choose your replacement Marvel splash PNG') if system=='Darwin' else None)
 if original is None or artwork is None:raise PatchError('--apk and --artwork are required on Linux')
 original,artwork=private(original),private(artwork)
 if sha(original)!=ORIGINAL_SHA:raise PatchError('Original APK checksum mismatch; stopping before dependency installation')
 validate_png(artwork)
 for name,digest in json.loads((REPO/'workshop/profiles/marvel-cosmic-invasion.json').read_text())['source_checksums'].items():
  if sha(REPO/name)!=digest:raise PatchError('The working Marvel patch changed: '+name)
 default=Path.home()/('Library/Caches/android-4x3-marvel' if system=='Darwin' else '.cache/android-4x3-marvel')
 cache=private(args.cache or Path(os.environ.get('APK4X3_CACHE',str(default))))
 if system=='Darwin' and 'XDG_DATA_HOME' not in os.environ:os.environ['XDG_DATA_HOME']=str(Path.home()/'Library/Application Support')
 state=Path(os.environ.get('XDG_DATA_HOME',str(Path.home()/'.local/share')))/'android-4x3-patches'
 if not (state/'signing.p12').is_file():raise PatchError('Existing local signing.p12 not found; restore the signing identity used for your working Marvel build')
 print('Reusing existing Java/Android/smali tools; preparing pinned experimental compilers...',flush=True)
 os.environ.update(installer().ensure_tools(cache,system,machine))
 if not shutil.which('javac'):
  previous=os.environ.get('MARVEL_FORCE_PRIVATE_JAVA');os.environ['MARVEL_FORCE_PRIVATE_JAVA']='1'
  try:os.environ.update(installer().ensure_tools(cache,system,machine))
  finally:
   if previous is None:os.environ.pop('MARVEL_FORCE_PRIVATE_JAVA',None)
   else:os.environ['MARVEL_FORCE_PRIVATE_JAVA']=previous
 tools=extra_tools(cache,system,machine)
 output=args.output or Path.home()/'Downloads'/('Marvel-4x3-startup-exit-'+datetime.now().strftime('%Y%m%d-%H%M%S'))/'Marvel-Cosmic-Invasion-4x3-startup-exit-experimental.apk'
 info=build(original,artwork,output,tools);print(json.dumps(info,indent=2))
 if system=='Darwin':subprocess.run(['open','-R',str(output)],check=False)

if __name__=='__main__':
 try:main()
 except (PatchError,OSError,ValueError,subprocess.SubprocessError) as e:raise SystemExit('Error: '+str(e))
