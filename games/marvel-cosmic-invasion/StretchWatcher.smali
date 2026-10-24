# Newly authored lifecycle observer. Does not retain the Activity strongly.
.class public final Landroid4x3/marvel/StretchWatcher;
.super Ljava/lang/Object;
.implements Landroid/view/ViewTreeObserver$OnPreDrawListener;

.field private final activity:Ljava/lang/ref/WeakReference;

.method public constructor <init>(Landroid/app/Activity;)V
    .locals 1
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    new-instance v0, Ljava/lang/ref/WeakReference;
    invoke-direct {v0, p1}, Ljava/lang/ref/WeakReference;-><init>(Ljava/lang/Object;)V
    iput-object v0, p0, Landroid4x3/marvel/StretchWatcher;->activity:Ljava/lang/ref/WeakReference;
    return-void
.end method

.method public onPreDraw()Z
    .locals 1
    iget-object v0, p0, Landroid4x3/marvel/StretchWatcher;->activity:Ljava/lang/ref/WeakReference;
    invoke-virtual {v0}, Ljava/lang/ref/WeakReference;->get()Ljava/lang/Object;
    move-result-object v0
    check-cast v0, Landroid/app/Activity;
    if-eqz v0, :done
    invoke-static {v0}, Lcom/jayeldragon/marvelfix/DisplayFix;->applyStretch4x3(Landroid/app/Activity;)V
    :done
    const/4 v0, 0x1
    return v0
.end method
