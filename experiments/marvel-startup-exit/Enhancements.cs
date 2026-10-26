// Authored helper. Original managed/native game libraries remain unchanged.
using System;
using System.IO;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Threading;
using Android.App;
using Android.Runtime;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using NLog;
using NLog.Config;
using NLog.Targets;
using Paris.Engine.Audio;
using Paris.Engine.Context;
using Com.Vocies61.Marvelcosmic;

namespace Android4x3.Marvel {
 public static class Enhancements {
  [DllImport("android4x3_marvel", CallingConvention=CallingConvention.Cdecl)] static extern int marvel_ready(IntPtr activity);
  [DllImport("android4x3_marvel", CallingConvention=CallingConvention.Cdecl)] static extern int marvel_finish(IntPtr activity);
  [DllImport("android4x3_marvel", CallingConvention=CallingConvention.Cdecl)] static extern int marvel_fail_open(IntPtr activity);
  static int started;
  static Activity activity;
  static Game game;
  static FieldInfo managerField, loadingThreadField, studioField;
  static bool exitObserved, handoffDone;
  static AudioManager capturedAudio;
  static FMOD.Studio.System capturedStudio;
  static bool haveStudio;

  // Invoked by the added JNI loader, after Mono is already initialized.
  public static void Start(IntPtr handle) {
   if (Interlocked.CompareExchange(ref started, 1, 0) != 0) return;
   try {
    activity = Java.Lang.Object.GetObject<Activity>(handle, JniHandleOwnership.DoNotTransfer);
    if (activity == null || activity.IsFinishing) throw new InvalidOperationException("No live Activity");
    exitObserved=false; handoffDone=false; game=null; capturedAudio=null; haveStudio=false;
    LogManager.ConfigurationChanged += LoggingConfigured;
    var worker = new Thread(Run) { IsBackground=true, Name="SPEXGameLoop" };
    Write("enhanced bootstrap accepted; original libraries unchanged");
    worker.Start();
   } catch {
    LogManager.ConfigurationChanged -= LoggingConfigured;
    Interlocked.Exchange(ref started,0);
    throw;
   }
  }

  static void LoggingConfigured(object sender, LoggingConfigurationChangedEventArgs args) {
   LogManager.ConfigurationChanged -= LoggingConfigured;
   try {
    var config=LogManager.Configuration;
    if(config==null)throw new InvalidOperationException("No logging configuration");
    var target=new PreFrameTarget();
    config.AddTarget("android4x3-preframe",target);
    config.AddRule(LogLevel.Info,LogLevel.Fatal,target,"*");
    LogManager.ReconfigExistingLoggers();
    Write("pre-frame initialization callback armed");
   } catch(Exception e) {
    Write("hook unavailable: "+e);
    marvel_fail_open(activity.Handle);
   }
  }
  sealed class PreFrameTarget:Target {
   protected override void Write(LogEventInfo entry) {
    if(game!=null || entry.FormattedMessage!="startinit: after LoadFonts")return;
    AttachGame();
   }
  }
  static void AttachGame() {
   try {
    var context=ContextManager.Singleton;
    var ownerField=typeof(ContextManager).GetField("_game",BindingFlags.Instance|BindingFlags.NonPublic);
    managerField=typeof(Game).GetField("graphicsDeviceManager",BindingFlags.Instance|BindingFlags.NonPublic);
    loadingThreadField=typeof(ContextManager).GetField("_loadingThread",BindingFlags.Instance|BindingFlags.NonPublic);
    studioField=typeof(AudioManager).GetField("_studioSystem",BindingFlags.Instance|BindingFlags.NonPublic);
    if(context==null || ownerField==null || managerField==null || loadingThreadField==null || studioField==null || managerField.IsInitOnly)
     throw new InvalidOperationException("Audited mutable frame-handoff context unavailable");
    var instance=ownerField.GetValue(context) as Game;
    if(instance==null || instance.GetType().FullName!="Paris.Paris")throw new InvalidOperationException("Unexpected game instance");
    var manager=managerField.GetValue(instance) as IGraphicsDeviceManager;
    if(manager==null)throw new InvalidOperationException("No graphics manager");
    game=instance;
    managerField.SetValue(instance,new FrameHandoff(manager));
    instance.Exiting += GameExiting;
    Write("frame handoff and completion observation armed before initial context load");
   } catch(Exception e) {
    Write("frame handoff unavailable: "+e);
    marvel_fail_open(activity.Handle);
   }
  }
  static void GameExiting(object sender,EventArgs e) {
   exitObserved=true;
   Write("game Exiting event observed; waiting for normal bootstrap return");
  }
  static void Run() {
   try {
    SpexBootstrap.Run(activity,new string[0]);
    // The original error overlay must remain available on failed startup.
    if(game!=null && exitObserved && String.IsNullOrEmpty(Paris.Program.LastError)) {
     Write("normal game completion confirmed");
     StopAudio();
     if(marvel_finish(activity.Handle)==0) Write("Activity finish callback failed");
    } else {
     Write("no successful game completion; keeping original diagnostic behavior");
     marvel_fail_open(activity.Handle);
    }
   } catch(Exception e) {
    Write("helper exception: "+e);
    if(activity!=null)marvel_fail_open(activity.Handle);
   } finally {
    LogManager.ConfigurationChanged -= LoggingConfigured;
    if(game!=null)game.Exiting-=GameExiting;
    capturedAudio=null; game=null; activity=null;
    Interlocked.Exchange(ref started,0);
   }
  }
  static void CaptureAudio() {
   if(haveStudio || studioField==null)return;
   var manager=AudioManagerBase.Singleton as AudioManager;
   if(manager==null)return;
   var system=(FMOD.Studio.System)studioField.GetValue(manager);
   if(!system.hasHandle())return;
   capturedAudio=manager; capturedStudio=system; haveStudio=true;
  }
  static void StopAudio() {
   if(!haveStudio) {Write("no live FMOD handle captured");return;}
   try {
    FMOD.Studio.Bus bus;
    var result=capturedStudio.getBus("bus:/",out bus);
    if(result!=FMOD.RESULT.OK) {Write("FMOD root bus unavailable: "+result);return;}
    result=bus.stopAllEvents(FMOD.Studio.STOP_MODE.IMMEDIATE);
    Write("FMOD stopAllEvents: "+result);
    capturedStudio.flushCommands();
    result=capturedStudio.release();
    Write("FMOD release: "+result);
    if(result==FMOD.RESULT.OK && capturedAudio!=null)studioField.SetValue(capturedAudio,default(FMOD.Studio.System));
    haveStudio=false;
   } catch(Exception e) {Write("audio cleanup failed: "+e);}
  }
  static void BeforePresent() {
   CaptureAudio();
   if(handoffDone)return;
   var context=ContextManager.Singleton;
   if(context==null || context.CurrentContext==null || context.CurrentContext.GetType().FullName!="Paris.Game.Menu.LogoScreen")return;
   // Match the audited Render() conditions; do not infer readiness from logs or timers.
   if(loadingThreadField.GetValue(context)!=null || (int)context.Fadestate==1)return;
   handoffDone=true;
   Write("first drawable LogoScreen frame ready; fading splash before presentation");
   var ok=marvel_ready(activity.Handle);
   if(ok==0)marvel_fail_open(activity.Handle);
   game.ResetElapsedTime(); // Do not charge the short UI fade against subsequent game ticks.
   Write("splash handoff acknowledged: "+ok);
  }
  sealed class FrameHandoff:IGraphicsDeviceManager {
   readonly IGraphicsDeviceManager inner;
   public FrameHandoff(IGraphicsDeviceManager manager) {inner=manager;}
   public bool BeginDraw(){return inner.BeginDraw();}
   public void CreateDevice(){inner.CreateDevice();}
   public void EndDraw(){
    try {BeforePresent();}
    catch(Exception e){handoffDone=true;Write("handoff exception: "+e);marvel_fail_open(activity.Handle);}
    inner.EndDraw(); // Original presentation always runs, with unchanged buffer/viewport.
   }
  }
  static void Write(string message) {
   try {
    Android.Util.Log.Info("Android4x3Marvel",message);
    var dir=activity.GetExternalFilesDir(null) ?? activity.FilesDir;
    File.AppendAllText(Path.Combine(dir.AbsolutePath,"android4x3-enhancements.txt"),DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss.fff")+" "+message+Environment.NewLine);
   } catch { }
  }
 }
}
