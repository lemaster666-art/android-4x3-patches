"""Authored Android test doubles for executing the real startup UI helper."""

SOURCES = {
    'android/content/Context.java': '''package android.content;
public class Context {public android.content.res.AssetManager getAssets(){return new android.content.res.AssetManager();}}''',
    'android/content/res/AssetManager.java': '''package android.content.res;
public class AssetManager {public java.io.InputStream open(String s){return new java.io.ByteArrayInputStream(new byte[]{1});}}''',
    'android/os/Build.java': '''package android.os; public class Build {public static class VERSION {public static int SDK_INT=34;}}''',
    'android/os/Looper.java': '''package android.os;
public class Looper {static final Thread UI=Thread.currentThread();static final Looper MAIN=new Looper();public static Looper getMainLooper(){return MAIN;}public static Looper myLooper(){return Thread.currentThread()==UI?MAIN:null;}}''',
    'android/os/SystemClock.java': '''package android.os; public class SystemClock {public static volatile long now;public static long uptimeMillis(){return now;}}''',
    'android/os/Handler.java': '''package android.os; import java.util.*;
public class Handler {
 static class Task {long time,order;Runnable run;Task(long t,long o,Runnable r){time=t;order=o;run=r;}}
 static final PriorityQueue<Task> tasks=new PriorityQueue<>((a,b)->a.time==b.time?Long.compare(a.order,b.order):Long.compare(a.time,b.time));static long order;
 public Handler(Looper l){}public boolean post(Runnable r){return postDelayed(r,0);}
 public boolean postDelayed(Runnable r,long delay){synchronized(tasks){tasks.add(new Task(SystemClock.now+delay,order++,r));}return true;}
 public void removeCallbacks(Runnable r){synchronized(tasks){tasks.removeIf(t->t.run==r);}}
 public static boolean hasCurrent(){synchronized(tasks){return !tasks.isEmpty() && tasks.peek().time<=SystemClock.now;}}
 public static void advanceTo(long end){int limit=10000;while(true){Task task;synchronized(tasks){if(tasks.isEmpty() || tasks.peek().time>end)break;task=tasks.remove();}if(--limit==0)throw new AssertionError("Unbounded UI scheduling");SystemClock.now=task.time;task.run.run();}SystemClock.now=end;}
}''',
    'android/util/Log.java': '''package android.util; public class Log {public static int e(String t,String m){return 0;}public static int e(String t,String m,Throwable e){return 0;}}''',
    'android/graphics/Color.java': '''package android.graphics; public class Color {public static final int BLACK=0xff000000;}''',
    'android/graphics/Bitmap.java': '''package android.graphics;public class Bitmap {public boolean recycled;public static class Config {public static final Config ARGB_8888=new Config();}public void recycle(){recycled=true;}}''',
    'android/graphics/BitmapFactory.java': '''package android.graphics;public class BitmapFactory {public static class Options {public Bitmap.Config inPreferredConfig;}public static Bitmap decodeStream(java.io.InputStream i,Object o,Options p){return new Bitmap();}}''',
    'android/graphics/Paint.java': '''package android.graphics;public class Paint {public static final int ANTI_ALIAS_FLAG=1,FILTER_BITMAP_FLAG=2;public int alpha;public Paint(int f){}public void setAlpha(int a){alpha=a;}}''',
    'android/graphics/RectF.java': '''package android.graphics;public class RectF {public float left,top,right,bottom;public void set(float l,float t,float r,float b){left=l;top=t;right=r;bottom=b;}}''',
    'android/graphics/Canvas.java': '''package android.graphics;import java.util.*;public class Canvas {
 public static final List<Integer> alphas=new ArrayList<>();public static final List<Long> times=new ArrayList<>();
 public void drawColor(int color){if(color!=Color.BLACK)throw new AssertionError("Background must stay black");}
 public void drawBitmap(Bitmap b,Object src,RectF dest,Paint p){if(b.recycled)throw new AssertionError("Recycled bitmap used");if(src!=null || dest.left!=0 || dest.top!=75 || dest.right!=1240 || dest.bottom!=1005)throw new AssertionError("Changed 4:3 bounds/cropped source");alphas.add(p.alpha);times.add(android.os.SystemClock.now);}
}''',
    'android/view/WindowInsets.java': '''package android.view;public class WindowInsets {public int visible=1;public boolean isVisible(int mask){return (visible&mask)==mask;}public static class Type {public static int statusBars(){return 1;}public static int navigationBars(){return 2;}public static int systemBars(){return 3;}}}''',
    'android/view/WindowInsetsController.java': '''package android.view;public class WindowInsetsController {public static final int BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE=2;public int hides,behavior;final WindowInsets insets;public WindowInsetsController(WindowInsets i){insets=i;}public void setSystemBarsBehavior(int b){behavior=b;}public void hide(int mask){hides++;insets.visible&=~mask;}}''',
    'android/view/WindowManager.java': '''package android.view;public class WindowManager {public static class LayoutParams {public static final int FLAG_FULLSCREEN=1024,FLAG_FORCE_NOT_FULLSCREEN=2048;}}''',
    'android/view/ViewTreeObserver.java': '''package android.view;import java.util.*;public class ViewTreeObserver {
 public interface OnWindowFocusChangeListener {void onWindowFocusChanged(boolean f);}public interface OnPreDrawListener {boolean onPreDraw();}
 public final List<OnWindowFocusChangeListener> focus=new ArrayList<>();public final List<OnPreDrawListener> pre=new ArrayList<>();public boolean isAlive(){return true;}
 public void addOnWindowFocusChangeListener(OnWindowFocusChangeListener l){focus.add(l);}public void removeOnWindowFocusChangeListener(OnWindowFocusChangeListener l){focus.remove(l);}
 public void addOnPreDrawListener(OnPreDrawListener l){pre.add(l);}public void removeOnPreDrawListener(OnPreDrawListener l){pre.remove(l);}
 public void focus(boolean f){for(OnWindowFocusChangeListener l:new ArrayList<>(focus))l.onWindowFocusChanged(f);}
 public void draw(){for(OnPreDrawListener l:new ArrayList<>(pre))if(!l.onPreDraw())throw new AssertionError("Suppressed original drawing");}
}''',
    'android/view/View.java': '''package android.view;import android.content.Context;import android.os.*;public class View {
 final Context context;final ViewTreeObserver tree=new ViewTreeObserver();public boolean drawing=true;public int flags,flagWrites;public final WindowInsets insets=new WindowInsets();
 public View(Context c){context=c;}public Context getContext(){return context;}public int getWidth(){return 1240;}public int getHeight(){return 1080;}
 public void setBackgroundColor(int color){}public void setAlpha(float a){if(a!=1f)throw new AssertionError("Do not animate whole-view alpha");}
 public void invalidate(){postInvalidateOnAnimation();}public void postInvalidateOnAnimation(){new Handler(Looper.getMainLooper()).postDelayed(()->{if(drawing)onFrame();},16);}protected void onFrame(){}
 public ViewTreeObserver getViewTreeObserver(){return tree;}public boolean hasWindowFocus(){return true;}public WindowInsets getRootWindowInsets(){return insets;}
 public int getSystemUiVisibility(){return flags;}public void setSystemUiVisibility(int f){flagWrites++;flags=f;}
}''',
    'android/view/Window.java': '''package android.view;public class Window {final View decor;final WindowInsetsController controller;public int flags,writes;
 public Window(android.app.Activity a){decor=new View(a);controller=new WindowInsetsController(decor.insets);}public View getDecorView(){return decor;}public WindowInsetsController getInsetsController(){return controller;}public void clearFlags(int f){writes++;flags&=~f;}public void addFlags(int f){writes++;flags|=f;}}''',
    'android/app/Activity.java': '''package android.app;public class Activity extends android.content.Context {final android.view.Window window=new android.view.Window(this);public boolean isFinishing(){return false;}public boolean isDestroyed(){return false;}public android.view.Window getWindow(){return window;}public void runOnUiThread(Runnable r){if(android.os.Looper.myLooper()==android.os.Looper.getMainLooper())r.run();else new android.os.Handler(android.os.Looper.getMainLooper()).post(r);}}''',
    'com/vocies61/marvelcosmic/SplashView.java': '''package com.vocies61.marvelcosmic;public class SplashView extends android.view.View {
 public int finishes;public SplashView(android.app.Activity a){super(a);}protected void onFrame(){EnhancedUi.draw(this,new android.graphics.Canvas());}public void finishEnhancedSplash(){finishes++;drawing=false;}
}''',
    'com/vocies61/marvelcosmic/StartupHarness.java': '''package com.vocies61.marvelcosmic;
import android.app.*;import android.os.*;import android.view.*;import android.graphics.*;
public class StartupHarness {
 static volatile boolean result,returned;static void check(boolean ok,String m){if(!ok)throw new AssertionError(m);}
 public static void main(String[] args)throws Exception {
  Looper.getMainLooper();boolean legacy=args[0].equals("legacy");if(legacy)Build.VERSION.SDK_INT=29;
  Activity activity=new Activity();View decor=activity.getWindow().getDecorView();ViewTreeObserver tree=decor.getViewTreeObserver();
  int[] originalCallbacks={0,0};ViewTreeObserver.OnWindowFocusChangeListener oldFocus=f->originalCallbacks[0]++;ViewTreeObserver.OnPreDrawListener oldDraw=()->{originalCallbacks[1]++;return true;};tree.addOnWindowFocusChangeListener(oldFocus);tree.addOnPreDrawListener(oldDraw);
  decor.flags=5894;decor.insets.visible=0;activity.getWindow().flags=WindowManager.LayoutParams.FLAG_FULLSCREEN;
  SplashView splash=new SplashView(activity);EnhancedUi.attach(splash);Handler.advanceTo(250);
  int initialMid=Canvas.alphas.get(Canvas.alphas.size()-1);check(initialMid>=120 && initialMid<=140,"PNG fade-in must take 500ms");Handler.advanceTo(1000);
  check(splash.finishes==0,"Splash disappeared during loading");check(Canvas.alphas.get(Canvas.alphas.size()-1)==255,"PNG not opaque while loading");
  check(decor.flags==5894 && activity.getWindow().flags==WindowManager.LayoutParams.FLAG_FULLSCREEN,"Changed original full-screen state");
  decor.insets.visible=1;decor.flags=0;tree.draw();tree.focus(true);
  check(decor.flags==0 && decor.insets.visible==1,"Helper overrides original window policy");
  check(originalCallbacks[0]==1 && originalCallbacks[1]==1,"Lost original SDL callbacks");
  check(tree.focus.size()==1 && tree.pre.size()==1,"Added competing startup observers");
  decor.flags=5894;decor.insets.visible=0;
  if(args[0].equals("paused"))splash.drawing=false;
  int samples=Canvas.alphas.size();long start=SystemClock.now;
  Thread worker=new Thread(()->{result=EnhancedUi.handoff(activity);returned=true;});worker.start();
  for(int i=0;i<1000 && !Handler.hasCurrent();i++)Thread.sleep(1);
  check(Handler.hasCurrent(),"UI handoff was not scheduled");Handler.advanceTo(start);
  if(args[0].equals("detached")) {
   splash.drawing=false;EnhancedUi.detached(splash);worker.join(1000);check(returned && !result,"Detached splash left worker blocked");
   check(tree.focus.size()==1 && tree.pre.size()==1,"Detach leaked observers");
  }else if(args[0].equals("paused")) {
   Handler.advanceTo(start+4000);worker.join(1000);check(returned && !result && splash.finishes==1,"Paused redraw did not recover safely");
   Handler.advanceTo(start+6000);
  }else {
   if(args[0].equals("late-black")) {
    splash.drawing=false;Handler.advanceTo(start+2500);splash.drawing=true;splash.postInvalidateOnAnimation();Handler.advanceTo(start+2520);
   }else {
    Handler.advanceTo(start+1000);check(!returned && splash.finishes==0,"Presented game before fade completed");
    int mid=Canvas.alphas.get(Canvas.alphas.size()-1);check(mid>=120 && mid<=140,"Half-fade must be visibly intermediate");
    Handler.advanceTo(start+1999);check(!returned && splash.finishes==0,"Fade ended before 2000ms");
    Handler.advanceTo(start+2024);
   }
   check(Canvas.alphas.get(Canvas.alphas.size()-1)==0 && !returned,"Full black not held before logo presentation");
   long blackAt=-1;for(int i=samples;i<Canvas.alphas.size();i++)if(Canvas.alphas.get(i)==0){blackAt=Canvas.times.get(i);break;}
   check(blackAt>=start+2000,"Black endpoint arrived too early");
   Handler.advanceTo(blackAt+499);check(!returned && splash.finishes==0,"Black hold must last 500ms from actual redraw");
   Handler.advanceTo(blackAt+516);worker.join(1000);
   check(returned && result && splash.finishes==1,"Completed fade did not release exactly once");
   check(Canvas.alphas.get(Canvas.alphas.size()-1)==0,"Game released before black was drawn");
   int last=256;for(int i=samples;i<Canvas.alphas.size();i++){int a=Canvas.alphas.get(i);check(a<=last,"Fade reversed");last=a;}
   check(tree.focus.size()==1 && tree.pre.size()==1,"Added window handling at handoff");
   Handler.advanceTo(SystemClock.now+2000);
  }
  check(tree.focus.size()==1 && tree.pre.size()==1,"Startup observers leaked into gameplay");
  check(tree.focus.contains(oldFocus) && tree.pre.contains(oldDraw),"Removed original SDL observers");
  check(decor.flagWrites==0 && activity.getWindow().writes==0 && activity.getWindow().getInsetsController().hides==0 && activity.getWindow().getInsetsController().behavior==0,"Helper competes with original bar handling");
  Handler.advanceTo(start+65000);check(splash.finishes<=1,"Stale watchdog finished twice");
  System.out.println("PASS startup "+args[0]);
 }
}''',
}
