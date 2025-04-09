# 工作原理

## 解码流程

1. 解码初始化：
   1. 通过`gd_open_gif_*`系列函数解析 GIF 文件头
   1. 创建内存画布（gif->canvas）存储解码后的像素数据
   1. 初始化第一帧的显示参数
1. 帧调度机制：
   1. 使用 LVGL 的定时器系统（10ms 间隔轮询）
   1. 根据 GIF 帧延迟时间（gce.delay）控制刷新节奏
   1. 通过 last_call 记录最后刷新时间实现时间同步
1. 帧渲染过程：
   1. 调用 gd_render_frame 将当前帧叠加到画布
   1. 处理 GIF 的透明色和帧累积效果
   1. 通过 alpha 通道实现透明效果（LV_IMG_CF_TRUE_COLOR_ALPHA）
1. 显示更新：
   1. 使用 lv_img_cache_invalidate_src 强制刷新图片缓存
   1. 调用 lv_obj_invalidate 触发界面重绘
1. 内存管理：
   1. 单画布设计复用内存空间（所有帧共享同一内存区域）
   1. 析构时自动释放解码器实例和定时器资源

## 定时器代码

```c
// 关键结构体
typedef struct {
    lv_img_t img;           // 继承自基础图片控件
    gd_GIF * gif;           // GIF解码器实例
    lv_timer_t * timer;     // 帧控制定时器
    lv_img_dsc_t imgdsc;    // 存储当前帧图像数据
    uint32_t last_call;     // 记录上次帧刷新时间
} lv_gif_t;

// 核心逻辑在定时器回调函数中
static void next_frame_task_cb(lv_timer_t * t) {
    // 计算时间间隔
    uint32_t elaps = lv_tick_elaps(gifobj->last_call);

    // 当达到帧延迟时间后
    if(elaps < gifobj->gif->gce.delay * 10) return;

    // 解码下一帧
    int has_next = gd_get_frame(gifobj->gif);

    // 渲染帧到内存画布
    gd_render_frame(gifobj->gif, (uint8_t *)gifobj->imgdsc.data);

    // 刷新显示
    lv_img_cache_invalidate_src(lv_img_get_src(obj));
    lv_obj_invalidate(obj);
}
```

## 读取图像

`gd_get_frame`负责从 flash 读取一帧图像

- 每帧开始时读取 1 字节分隔符
- 图像数据按子块读取（每个子块 1 字节长度头 + N 字节数据）
- LZW 压缩数据按位读取（通过 get_key()函数）

```c
int gd_get_frame(gd_GIF *gif) {
    // ... 其他代码 ...

    /* 关键读取逻辑 */
    while (sep != ',') {
        if (sep == ';') {    // 遇到结束符
            f_gif_seek(gif, gif->anim_start, LV_FS_SEEK_SET);
            return 0;
        }
        else if (sep == '!') // 遇到扩展块
            read_ext(gif);   // 读取扩展数据
        f_gif_read(gif, &sep, 1); // 每次读取1字节分隔符
    }

    // 读取图像数据块（变长）
    if (read_image(gif) == -1)
        return -1;
}
```

# 速度提升

gif 播放比 PC 上慢，除去文件读取慢之外，其他耗时基本都在 gif 解码的过程。在`next_frame_task_cb`打印时间间隔, PC 上基本为 0.

1. [将 gif 文件全部读到内存中，按 data 的方式运行](./7_gif.assets/gif_file_load_to_psram.diff)
2. [添加文件缓存，减少读 flash 的次数](./7_gif.assets/gif_file_read_buffer.diff)
3. [添加 lzw cache](./7_gif.assets/gif_lzw_cache.diff)
