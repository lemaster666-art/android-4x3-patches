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
import android.view.ViewTreeObserver;
import android.view.WindowManager;
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
    private static Runnable fadeRecovery;
    private static long fadeStartedAt;
    private static FadeRequest pendingFade;
    private static ImmersiveGuard immersiveGuard;
    private static final long FADE_IN_MS=500;
    private static final long FADE_OUT_MS=2000;
    private static final long BLACK_HOLD_MS=500;
    private static final long FADE_RECOVERY_MS=4000;
    private static final long HANDOFF_WAIT_MS=4500;
    private static long blackDrawnAt=-1;
    private static final Paint PAINT=new Paint(Paint.ANTI_ALIAS_FLAG|Paint.FILTER_BITMAP_FLAG);
    private static final RectF DEST=new RectF();

    public static void attach(final SplashView view) {
        current=new WeakReference<>(view); fading=false; blackDrawnAt=-1; attachedAt=SystemClock.uptimeMillis();
        view.setBackgroundColor(Color.BLACK); view.setAlpha(1f);
        if(immersiveGuard!=null)immersiveGuard.close();
        if(view.getContext() instanceof Activity)
            immersiveGuard=new ImmersiveGuard((Activity)view.getContext());
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
        long now=SystemClock.uptimeMillis();
        float fade=Math.min(1f,(now-attachedAt)/(float)FADE_IN_MS);
        float out=fading?Math.min(1f,(now-fadeStartedAt)/(float)FADE_OUT_MS):0f;
        fade*=1f-out;
        PAINT.setAlpha(Math.round(255f*fade));
        canvas.drawBitmap(artwork,null,DEST,PAINT); // Whole source rectangle; no crop or zoom.
        if(fading && out>=1f && blackDrawnAt<0)blackDrawnAt=now;
        if(fading && blackDrawnAt>=0 && now-blackDrawnAt>=BLACK_HOLD_MS) {
            // Release the game only after the zero-alpha artwork/black backdrop
            // has stayed drawn for the requested hold. Time it from the actual
            // black draw, not an estimated fade deadline after a stalled redraw.
            MAIN.post(new Runnable(){public void run(){finish(view,true);}});
        }else if(fading || fade<1f)view.postInvalidateOnAnimation();
    }
    public static boolean handoff(final Activity activity) {
        // Called on the game thread BEFORE its original graphics manager presents the first logo frame.
        if(Looper.myLooper()==Looper.getMainLooper()) { failOpen();return false; }
        final FadeRequest request=new FadeRequest();
        activity.runOnUiThread(new Runnable(){public void run(){
            final SplashView view=current.get();
            if(request.cancelled || view==null || fading){request.done.countDown();return;}
            pendingFade=request;fading=true;blackDrawnAt=-1;fadeStartedAt=SystemClock.uptimeMillis();
            if(immersiveGuard!=null)immersiveGuard.hide();
            view.postInvalidateOnAnimation();
            // A paused/non-drawing view must never block game presentation forever.
            fadeRecovery=new Runnable(){public void run(){
                if(pendingFade==request){Log.e("Android4x3Marvel","Fade redraw timeout; revealing original game");finish(view);}
            }};MAIN.postDelayed(fadeRecovery,FADE_RECOVERY_MS);
        }});
        try {
            if(request.done.await(HANDOFF_WAIT_MS,TimeUnit.MILLISECONDS))return request.completed;
        } catch(InterruptedException error){Thread.currentThread().interrupt();}
        request.cancelled=true;
        activity.runOnUiThread(new Runnable(){public void run(){failOpen();}});
        return false;
    }
    public static void failOpen() {
        if(Looper.myLooper()!=Looper.getMainLooper()) {MAIN.post(new Runnable(){public void run(){failOpen();}});return;}
        failed=true;SplashView view=current.get();if(view!=null)finish(view);
    }
    public static void detached(SplashView view) {
        if(current.get()==view){
            current.clear();clearArtwork();releaseFade(false);
            if(immersiveGuard!=null){immersiveGuard.close();immersiveGuard=null;}
        }
    }
    private static void clearArtwork() {
        if(watchdog!=null){MAIN.removeCallbacks(watchdog);watchdog=null;}
        if(fadeRecovery!=null){MAIN.removeCallbacks(fadeRecovery);fadeRecovery=null;}
        if(artwork!=null){artwork.recycle();artwork=null;}
    }
    private static void finish(SplashView view) {finish(view,false);}
    private static void finish(SplashView view,boolean completed) {
        if(current.get()!=view)return;
        current.clear();
        try {
            if(immersiveGuard!=null)immersiveGuard.afterHandoff();
            view.finishEnhancedSplash();
        }finally{clearArtwork();releaseFade(completed);}
    }
    private static void releaseFade(boolean completed) {
        FadeRequest request=pendingFade;pendingFade=null;
        if(request!=null){request.completed=completed;request.done.countDown();}
    }
    private static final class FadeRequest {
        final CountDownLatch done=new CountDownLatch(1);
        volatile boolean completed,cancelled;
    }
    /** Additional observers preserve SDL's existing Activity and insets listeners. */
    private static final class ImmersiveGuard implements ViewTreeObserver.OnWindowFocusChangeListener,ViewTreeObserver.OnPreDrawListener {
        final WeakReference<Activity> owner;
        final View decor;
        final ViewTreeObserver observer;
        boolean closed;
        final Runnable closeLater=new Runnable(){public void run(){close();}};
        ImmersiveGuard(Activity activity) {
            owner=new WeakReference<>(activity);decor=activity.getWindow().getDecorView();
            observer=decor.getViewTreeObserver();
            observer.addOnWindowFocusChangeListener(this);observer.addOnPreDrawListener(this);
            hide();
        }
        void hide() {
            Activity activity=owner.get();
            if(closed || activity==null || activity.isFinishing() || activity.isDestroyed())return;
            activity.getWindow().clearFlags(WindowManager.LayoutParams.FLAG_FORCE_NOT_FULLSCREEN);
            activity.getWindow().addFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN);
            // Match the original DisplayFix/SDL routine on Android 14 too.
            // SDL still writes these legacy flags. Keep both requested states
            // consistent; the reported status-bar flash still needs device testing.
            decor.setSystemUiVisibility(5894);
            if(Build.VERSION.SDK_INT>=30) {
                WindowInsetsController controller=activity.getWindow().getInsetsController();
                if(controller!=null) {
                    controller.setSystemBarsBehavior(WindowInsetsController.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE);
                    controller.hide(WindowInsets.Type.systemBars());
                }
            }
        }
        public void onWindowFocusChanged(boolean hasFocus){if(hasFocus)hide();}
        public boolean onPreDraw() {
            if(!closed && decor.hasWindowFocus()) {
                if((decor.getSystemUiVisibility()&5894)!=5894)hide();
                if(Build.VERSION.SDK_INT>=30) {
                    WindowInsets insets=decor.getRootWindowInsets();
                    if(insets!=null && (insets.isVisible(WindowInsets.Type.statusBars()) || insets.isVisible(WindowInsets.Type.navigationBars())))hide();
                }
            }
            return true; // Never suppress or rescale the original game/splash draw.
        }
        void afterHandoff() {
            hide();
            // Bounded startup observation also covers SDL's final full-screen
            // request. No permanent listener or change to gameplay UI behavior.
            MAIN.removeCallbacks(closeLater);MAIN.postDelayed(closeLater,2000);
        }
        void close() {
            if(closed)return;closed=true;MAIN.removeCallbacks(closeLater);
            ViewTreeObserver tree=observer.isAlive()?observer:decor.getViewTreeObserver();
            if(tree.isAlive()){tree.removeOnWindowFocusChangeListener(this);tree.removeOnPreDrawListener(this);}
            owner.clear();
            if(immersiveGuard==this)immersiveGuard=null;
        }
    }
    private EnhancedUi() {}
}
