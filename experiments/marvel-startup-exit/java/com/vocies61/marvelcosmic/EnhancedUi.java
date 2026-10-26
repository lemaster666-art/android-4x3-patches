package com.vocies61.marvelcosmic;

import android.app.Activity;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.RectF;
import android.os.Handler;
import android.os.Build;
import android.view.WindowInsets;
import android.view.WindowInsetsController;
import android.os.Looper;
import android.os.SystemClock;
import android.util.Log;
import android.view.View;
import java.io.InputStream;
import java.lang.ref.WeakReference;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;

/** A complete-source, fixed-4:3 splash; readiness is supplied before game presentation. */
public final class EnhancedUi {
    private static final Handler MAIN=new Handler(Looper.getMainLooper());
    private static WeakReference<SplashView> current=new WeakReference<>(null);
    private static Bitmap artwork;
    private static long attachedAt;
    private static boolean fading;
    private static boolean failed;
    private static Runnable watchdog;
    private static final Paint PAINT=new Paint(Paint.ANTI_ALIAS_FLAG|Paint.FILTER_BITMAP_FLAG);
    private static final RectF DEST=new RectF();

    public static void attach(final SplashView view) {
        current=new WeakReference<>(view); fading=false; attachedAt=SystemClock.uptimeMillis();
        view.setBackgroundColor(Color.BLACK); view.setAlpha(1f);
        if(view.getContext() instanceof Activity) {
            Activity owner=(Activity)view.getContext();
            if(Build.VERSION.SDK_INT>=30) {
                WindowInsetsController controller=owner.getWindow().getInsetsController();
                if(controller!=null)controller.hide(WindowInsets.Type.systemBars());
            }else owner.getWindow().getDecorView().setSystemUiVisibility(5894);
        }
        if(failed) { MAIN.post(new Runnable(){public void run(){finish(view);}}); return; }
        try(InputStream input=view.getContext().getAssets().open("android4x3/splash.png")) {
            BitmapFactory.Options options=new BitmapFactory.Options();options.inPreferredConfig=Bitmap.Config.ARGB_8888;
            artwork=BitmapFactory.decodeStream(input,null,options);
            if(artwork==null)throw new IllegalArgumentException("PNG could not be decoded");
        }catch(Exception error) {
            Log.e("Android4x3Marvel","Artwork unavailable",error); failed=true;
            MAIN.post(new Runnable(){public void run(){finish(view);}});return;
        }
        view.invalidate();
        // Recovery timeout only: never use this as the normal logo handoff.
        if(watchdog!=null)MAIN.removeCallbacks(watchdog);
        watchdog=new Runnable(){public void run(){
            if(current.get()==view){Log.e("Android4x3Marvel","Readiness timeout; revealing original game/diagnostics");finish(view);}
        }};MAIN.postDelayed(watchdog,60000);
    }
    public static void draw(SplashView view,Canvas canvas) {
        canvas.drawColor(Color.BLACK);
        if(artwork==null || view.getWidth()<=0 || view.getHeight()<=0)return;
        int unit=Math.min(view.getWidth()/4,view.getHeight()/3);
        int w=unit*4,h=unit*3;float left=(view.getWidth()-w)/2f,top=(view.getHeight()-h)/2f;
        DEST.set(left,top,left+w,top+h);
        float fade=Math.min(1f,(SystemClock.uptimeMillis()-attachedAt)/250f);
        PAINT.setAlpha(Math.round(255f*fade));
        canvas.drawBitmap(artwork,null,DEST,PAINT); // Whole source rectangle; no crop or zoom.
        if(fade<1f)view.postInvalidateOnAnimation();
    }
    public static boolean handoff(final Activity activity) {
        // Called on the game thread BEFORE its original graphics manager presents the first logo frame.
        if(Looper.myLooper()==Looper.getMainLooper()) { failOpen();return false; }
        final CountDownLatch done=new CountDownLatch(1);
        activity.runOnUiThread(new Runnable(){public void run(){
            final SplashView view=current.get();
            if(view==null || fading){done.countDown();return;}
            fading=true;
            view.animate().cancel();
            view.animate().alpha(0f).setDuration(180).withEndAction(new Runnable(){public void run(){finish(view);done.countDown();}}).start();
            // A paused/cancelled animator must never block the game indefinitely.
            MAIN.postDelayed(new Runnable(){public void run(){if(done.getCount()!=0){finish(view);done.countDown();}}},500);
        }});
        try {
            if(done.await(750,TimeUnit.MILLISECONDS))return true;
        } catch(InterruptedException error){Thread.currentThread().interrupt();}
        activity.runOnUiThread(new Runnable(){public void run(){failOpen();}});
        return false;
    }
    public static void failOpen() {
        if(Looper.myLooper()!=Looper.getMainLooper()) {MAIN.post(new Runnable(){public void run(){failOpen();}});return;}
        failed=true;SplashView view=current.get();if(view!=null)finish(view);
    }
    public static void detached(SplashView view) {
        if(current.get()==view){current.clear();clearArtwork();}
    }
    private static void clearArtwork() {
        if(watchdog!=null){MAIN.removeCallbacks(watchdog);watchdog=null;}
        if(artwork!=null){artwork.recycle();artwork=null;}
    }
    private static void finish(SplashView view) {
        if(current.get()!=view)return;
        current.clear();view.animate().cancel();view.finishEnhancedSplash();
        clearArtwork();
    }
    private EnhancedUi() {}
}
