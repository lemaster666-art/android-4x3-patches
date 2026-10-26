// Authored host-test doubles only. No game code or assets.
using System;
using System.Collections.Generic;
using System.Threading;
namespace Android.App {
 public class Activity {
  public static Activity Current=new Activity(); public bool IsFinishing=false;public IntPtr Handle=new IntPtr(123);
  public string Directory;
  public Java.IO.File GetExternalFilesDir(object unused){return new Java.IO.File(Directory);}
  public Java.IO.File FilesDir{get{return new Java.IO.File(Directory);}}
 }
}
namespace Android.Runtime {public enum JniHandleOwnership{DoNotTransfer}}
namespace Android.Util{public static class Log{public static int Info(string tag,string text){return 0;}}}
namespace Java.IO{public class File{public string AbsolutePath;public File(string path){AbsolutePath=path;}}}
namespace Java.Lang{public class Object{public static T GetObject<T>(IntPtr p,Android.Runtime.JniHandleOwnership o) where T:class{return Android.App.Activity.Current as T;}}}
namespace NLog.Config{public class LoggingConfigurationChangedEventArgs:EventArgs{} public class LoggingConfiguration {
 public void AddTarget(string name,NLog.Targets.Target target){NLog.LogManager.Target=target;}
 public void AddRule(NLog.LogLevel a,NLog.LogLevel b,NLog.Targets.Target c,string pattern){}
}}
namespace NLog.Targets{public abstract class Target{protected abstract void Write(NLog.LogEventInfo e);public void Send(NLog.LogEventInfo e){Write(e);}}}
namespace NLog {
 public class LogLevel{public static LogLevel Info=new LogLevel(),Fatal=new LogLevel();}
 public class LogEventInfo{public string LoggerName,FormattedMessage;}
 public static class LogManager {
  public static event EventHandler<NLog.Config.LoggingConfigurationChangedEventArgs> ConfigurationChanged;
  public static NLog.Targets.Target Target;
  static NLog.Config.LoggingConfiguration config;
  public static NLog.Config.LoggingConfiguration Configuration{get{return config;}set{config=value;ConfigurationChanged?.Invoke(null,new NLog.Config.LoggingConfigurationChangedEventArgs());}}
  public static void ReconfigExistingLoggers(){}
  public static void Emit(string text){Target?.Send(new LogEventInfo{LoggerName="Paris.Paris",FormattedMessage=text});}
 }
}
namespace Microsoft.Xna.Framework {
 public interface IGraphicsDeviceManager{bool BeginDraw();void CreateDevice();void EndDraw();}
 public class Game {
  IGraphicsDeviceManager graphicsDeviceManager=new FakeManager();
  public event EventHandler Exiting;
  public void ResetElapsedTime(){TestState.TimerReset++;}
  public void Frame(){graphicsDeviceManager.EndDraw();}
  public void TriggerExit(){TestState.NormalCleanup=true;Paris.Engine.Audio.AudioManagerBase.Singleton=null;Exiting?.Invoke(this,EventArgs.Empty);}
 }
 public class FakeManager:IGraphicsDeviceManager{public bool BeginDraw(){return true;}public void CreateDevice(){}public void EndDraw(){TestState.Frames++;if(TestState.Frames==4 && Native.ReadyCount()!=1)throw new Exception("First drawable logo frame presented before handoff");}}
}
namespace Microsoft.Xna.Framework.Graphics{public class GraphicsAdapter{}}
namespace Paris {
 public class Paris:Microsoft.Xna.Framework.Game{}
 public static class Program{public static string LastError;}
}
namespace Paris.Game.Menu{public class LogoScreen{}}
namespace Paris.Engine.Context {
 public class ContextManager {
  public static ContextManager Singleton;
  Microsoft.Xna.Framework.Game _game;
  object _loadingThread;
  public object CurrentContext;public int Fadestate;
  public ContextManager(Microsoft.Xna.Framework.Game owner){_game=owner;}
  public void SetLoading(bool value){_loadingThread=value?new object():null;}
 }
}
namespace Paris.Engine.Audio {
 public class AudioManagerBase{public static AudioManagerBase Singleton;}
 // The supported original declares this field PUBLIC (not private). Match its
 // metadata so reflection tests exercise the Android build's access contract.
 public class AudioManager:AudioManagerBase{public FMOD.Studio.System _studioSystem=new FMOD.Studio.System{live=true};}
}
namespace FMOD{public enum RESULT{OK,ERR_INVALID_HANDLE}}
namespace FMOD.Studio {
 public enum STOP_MODE{IMMEDIATE}
 public struct Bus{public FMOD.RESULT stopAllEvents(STOP_MODE mode){TestState.AudioStopped=true;return FMOD.RESULT.OK;}}
 public struct System{
  public bool live;
  public bool hasHandle(){return live;}
  public FMOD.RESULT getBus(string path,out Bus bus){if(path!="bus:/")throw new Exception("Wrong audio bus");bus=new Bus();return live?FMOD.RESULT.OK:FMOD.RESULT.ERR_INVALID_HANDLE;}
  public FMOD.RESULT flushCommands(){return FMOD.RESULT.OK;}
  public FMOD.RESULT release(){if(!TestState.NormalCleanup || !TestState.AudioStopped)throw new Exception("Audio released before normal game cleanup");TestState.AudioReleased=true;return FMOD.RESULT.OK;}
 }
}
public static class TestState{public static bool NormalCleanup,AudioStopped,AudioReleased;public static int Frames,TimerReset;public static string Mode;}
public static class Native {
 [System.Runtime.InteropServices.DllImport("android4x3_marvel")]public static extern int ReadyCount();
 [System.Runtime.InteropServices.DllImport("android4x3_marvel")]public static extern int FinishCount();
 [System.Runtime.InteropServices.DllImport("android4x3_marvel")]public static extern int FailureCount();
 [System.Runtime.InteropServices.DllImport("android4x3_marvel")]public static extern void SetReadyResult(int result);
}
namespace Com.Vocies61.Marvelcosmic {
 public static class SpexBootstrap {
  public static void Run(Android.App.Activity activity,string[] args) {
   NLog.LogManager.Configuration=new NLog.Config.LoggingConfiguration();
   var owner=new Paris.Paris();var context=new Paris.Engine.Context.ContextManager(owner);
   Paris.Engine.Context.ContextManager.Singleton=context;
   Paris.Engine.Audio.AudioManagerBase.Singleton=new Paris.Engine.Audio.AudioManager();
   // This synchronous callback precedes context creation and all frame presentation.
   NLog.LogManager.Emit("startinit: after LoadFonts");
   owner.Frame(); // No current context.
   context.CurrentContext=new Paris.Game.Menu.LogoScreen();context.SetLoading(true);owner.Frame();
   context.SetLoading(false);context.Fadestate=1;owner.Frame(); // Fully faded out is not drawable.
   if(Native.ReadyCount()!=0)throw new Exception("Splash handed off before a drawable logo frame");
   context.Fadestate=2;owner.Frame();owner.Frame(); // Exactly one handoff, both frames presented.
   if(TestState.Mode=="startup-error"){Paris.Program.LastError="Synthetic startup error";return;}
   owner.TriggerExit();
  }
 }
}
