package com.vocies61.marvelcosmic;

import android.app.Activity;
import android.util.Log;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import android.app.Application;
import android.os.Bundle;
import java.util.concurrent.atomic.AtomicBoolean;

/** Authored JNI dispatcher. The existing native/managed port remains intact. */
public final class EnhancedBridge {
    private static boolean loaded;
    private static native boolean nativeStart(Activity activity, byte[] assembly);
    public static synchronized boolean tryStart(Activity activity) {
        try {
            if (!loaded) { System.loadLibrary("android4x3_marvel"); loaded=true; }
            byte[] bytes;
            try (InputStream input=activity.getAssets().open("android4x3/marvel-enhancements.bin");
                 ByteArrayOutputStream output=new ByteArrayOutputStream()) {
                byte[] chunk=new byte[8192]; int count;
                while ((count=input.read(chunk))!=-1) {
                    if(output.size()+count>2*1024*1024)throw new IllegalStateException("Helper exceeds size guard");
                    output.write(chunk,0,count);
                }
                bytes=output.toByteArray();
            }
            boolean accepted=nativeStart(activity,bytes);
            if(!accepted) { note("Helper unavailable; retaining original game entry point"); EnhancedUi.failOpen(); }
            return accepted;
        } catch(Throwable error) {
            Log.e("Android4x3Marvel","Helper unavailable; retaining original game entry point",error);
            EnhancedUi.failOpen();
            return false;
        }
    }
    public static boolean onReady(Activity activity) { return EnhancedUi.handoff(activity); }
    public static void onFailure(Activity activity) { activity.runOnUiThread(new Runnable(){public void run(){EnhancedUi.failOpen();}}); }
    // A normal process exit AFTER Activity destruction avoids retaining disposed FNA/Mono singletons on relaunch.
    // This is reached only after the observed Exiting event and successful bootstrap return; no kill timer is used.
    private static final AtomicBoolean closing=new AtomicBoolean();
    static Runnable processExit=new Runnable(){public void run(){System.exit(0);}};
    public static void onFinished(final Activity activity) {
        if(!closing.compareAndSet(false,true))return;
        activity.runOnUiThread(new Runnable(){ public void run(){
            if(activity.isDestroyed()){processExit.run();return;}
            final Application application=activity.getApplication();
            final Application.ActivityLifecycleCallbacks callback=new Application.ActivityLifecycleCallbacks(){
                public void onActivityDestroyed(Activity item){
                    if(item==activity){application.unregisterActivityLifecycleCallbacks(this);processExit.run();}
                }
                public void onActivityCreated(Activity item,Bundle state){}
                public void onActivityStarted(Activity item){}
                public void onActivityResumed(Activity item){}
                public void onActivityPaused(Activity item){}
                public void onActivityStopped(Activity item){}
                public void onActivitySaveInstanceState(Activity item,Bundle state){}
            };
            application.registerActivityLifecycleCallbacks(callback);
            try {if(!activity.isFinishing())activity.finishAndRemoveTask();}
            catch(Throwable error){application.unregisterActivityLifecycleCallbacks(callback);closing.set(false);Log.e("Android4x3Marvel","Activity finish failed",error);}
        }});
    }
    public static void note(String text) { Log.i("Android4x3Marvel",text); }
    private EnhancedBridge() {}
}
