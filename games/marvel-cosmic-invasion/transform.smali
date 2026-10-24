# Newly authored compositor-only helper. Appended to the existing DisplayFix class.
.method public static applyStretch4x3(Landroid/app/Activity;)V
    .locals 12
    const v0, 0x1020002
    invoke-virtual {p0, v0}, Landroid/app/Activity;->findViewById(I)Landroid/view/View;
    move-result-object v0
    if-eqz v0, :done
    invoke-static {v0}, Lcom/jayeldragon/marvelfix/DisplayFix;->surface(Landroid/view/View;)Landroid/view/SurfaceView;
    move-result-object v0
    if-eqz v0, :done
    invoke-virtual {v0}, Landroid/view/SurfaceView;->getParent()Landroid/view/ViewParent;
    move-result-object v1
    instance-of v2, v1, Landroid/view/ViewGroup;
    if-eqz v2, :done
    check-cast v1, Landroid/view/ViewGroup;
    invoke-virtual {v1}, Landroid/view/ViewGroup;->getWidth()I
    move-result v2
    invoke-virtual {v1}, Landroid/view/ViewGroup;->getHeight()I
    move-result v3
    invoke-virtual {v0}, Landroid/view/SurfaceView;->getWidth()I
    move-result v4
    invoke-virtual {v0}, Landroid/view/SurfaceView;->getHeight()I
    move-result v5
    if-lez v2, :done
    if-lez v3, :done
    if-lez v4, :done
    if-lez v5, :done

    # Largest integer 4:3 presentation fitting the parent. Never resize the buffer.
    div-int/lit8 v6, v2, 0x4
    div-int/lit8 v7, v3, 0x3
    invoke-static {v6, v7}, Ljava/lang/Math;->min(II)I
    move-result v6
    if-lez v6, :done
    mul-int/lit8 v7, v6, 0x4
    mul-int/lit8 v8, v6, 0x3
    sub-int v9, v2, v7
    div-int/lit8 v9, v9, 0x2
    sub-int v10, v3, v8
    div-int/lit8 v10, v10, 0x2

    # Centre pivots and translations make the visual bounds exact, even for odd layouts.
    const/high16 v11, 0x40000000
    int-to-float v6, v4
    div-float/2addr v6, v11
    invoke-virtual {v0, v6}, Landroid/view/SurfaceView;->setPivotX(F)V
    int-to-float v6, v5
    div-float/2addr v6, v11
    invoke-virtual {v0, v6}, Landroid/view/SurfaceView;->setPivotY(F)V
    int-to-float v6, v7
    int-to-float v4, v4
    div-float/2addr v6, v4
    invoke-virtual {v0, v6}, Landroid/view/SurfaceView;->setScaleX(F)V
    int-to-float v6, v8
    int-to-float v5, v5
    div-float/2addr v6, v5
    invoke-virtual {v0, v6}, Landroid/view/SurfaceView;->setScaleY(F)V

    int-to-float v9, v9
    int-to-float v7, v7
    sub-float/2addr v7, v4
    div-float/2addr v7, v11
    add-float/2addr v9, v7
    invoke-virtual {v0}, Landroid/view/SurfaceView;->getLeft()I
    move-result v6
    int-to-float v6, v6
    sub-float/2addr v9, v6
    invoke-virtual {v0, v9}, Landroid/view/SurfaceView;->setTranslationX(F)V
    int-to-float v10, v10
    int-to-float v8, v8
    sub-float/2addr v8, v5
    div-float/2addr v8, v11
    add-float/2addr v10, v8
    invoke-virtual {v0}, Landroid/view/SurfaceView;->getTop()I
    move-result v6
    int-to-float v6, v6
    sub-float/2addr v10, v6
    invoke-virtual {v0, v10}, Landroid/view/SurfaceView;->setTranslationY(F)V
    const/high16 v6, -0x1000000
    invoke-virtual {v1, v6}, Landroid/view/ViewGroup;->setBackgroundColor(I)V
    :done
    return-void
.end method
