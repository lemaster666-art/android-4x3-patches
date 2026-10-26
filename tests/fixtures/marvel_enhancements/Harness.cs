using System;
using System.Threading;
public static class Harness {
 public static int Main(string[] args) {
  TestState.Mode=args[0];Android.App.Activity.Current.Directory=args[1];
  Native.SetReadyResult(args[0]=="handoff-error"?0:1);
  Android4x3.Marvel.Enhancements.Start(new IntPtr(123));
  for(int i=0;i<500 && (args[0]=="startup-error"?Native.FailureCount()==0:Native.FinishCount()==0);i++)Thread.Sleep(10);
  if(TestState.Frames!=5 || Native.ReadyCount()!=1 || TestState.TimerReset!=1)throw new Exception("Frame/handoff ordering failed");
  if(args[0]=="startup-error") {
   if(Native.FinishCount()!=0 || Native.FailureCount()!=1 || TestState.AudioReleased)throw new Exception("Failed startup was closed or audio released");
  }else {
   if(Native.FinishCount()!=1 || Native.FailureCount()!=(args[0]=="handoff-error"?1:0) || !TestState.AudioStopped || !TestState.AudioReleased)throw new Exception("Normal completion cleanup/finish failed");
  }
  Console.WriteLine("PASS "+args[0]);return 0;
 }
}
