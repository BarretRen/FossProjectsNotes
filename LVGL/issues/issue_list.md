# 工作时遇到的问题

## draw buf 大小不对

通过开机 log 看如下 log 打印，确认每个 buffer 起始地址是否正确:
`LVGL addr1:%x, addr2:%x, pixel size: %d, sram_fb1:%x, sram_fb2:%x, direct:%d\r\n`

需要重点关注第二个 buffer 设置起始地址时, **要加括号**, 不然因为**颜色深度**的原因, `lv_color_t`的大小不同, 会导致指针位移出错:

```c
lv_vnd_config.draw_buf_2_1 = (lv_color_t *)PSRAM_DRAW_BUFFER;
//加括号!!
lv_vnd_config.draw_buf_2_2 = (lv_color_t *)(PSRAM_DRAW_BUFFER + lv_vnd_config.draw_pixel_size * sizeof(lv_color_t));
```

## png 图片切换页面内存泄漏

问题：

> 使用图片控件，并打开了 png 的 psram 的方式，测试如果不指定图片，单纯的图片控件销毁和创建没有问题，只要指定了图片来回切换，sram 就会增加
> 如果使用 imgbtn 控件，在启动完成后不用任何操作 sram 内存就会一直增加，直到死机重启

可能原因：

1. style init 没有 reset
2. `lv_obj_clean`没有清除自身, 应该用`lv_obj_del`
3. 文件系统问题
4. strdup 之后不 free 的问题

## 启用 img cache 后内存占用多的问题

img cache 涉及到的内存占用:

- img cache entry 的内存占用, 44
- 图片解码后数据占用的内存
- 不同图片格式内部处理时的额外内存占用

### jpg 内部处理内存占用

1. sjpeg: 结构体 SJPEG, 即 88
1. sjpeg->frame_cache: 根据`LV_SJPG_USE_PSRAM`可指定使用 heap 或 psram, 大小为`width * height * 3`
1. sjpeg->frame_base_array: `LV_IMG_SRC_VARIABLE`时使用, 帧数为 1, 大小为`sizeof(uint8_t *) * sjpeg->sjpeg_total_frames`, 即 4
1. sjpeg->frame_base_offset: `LV_IMG_SRC_FILE`时使用, 帧数为 1, 大小为`sizeof(uint8_t *) * sjpeg->sjpeg_total_frames`, 即 4
1. sjpeg->tjpeg_jd: 结构体 JDEC, 即 120, 在绘图过程中逐行解析时使用
1. sjpeg->workb: 在绘图过程中逐行解析时使用, 大小为`TJPGD_WORKBUFF_SIZE`, 默认 4096
1. sjpeg->io.lv_file 的 cache:
   1. cache: 结构体 lv_fs_file_cache_t, 即 16
   1. cache->buffer: 大小根据 drv 定义的 cache_size, bk posix 定义为 0(`LV_FS_BK_POSIX_CACHE_SIZE`)

## 如何提高 lvgl 的帧率?

1. 修改刷新周期`LV_DISP_DEF_REFR_PERIOD`
1. `LV_DPI_DEF`设置, 会影响动画的效果, 例如 480x272 分辨率 1.28 英寸的屏幕，那么$$DPI = ((√480*272) / 1.28) ≈ 89$$
1. 帧缓存区不要低于屏幕的 1/4，建议双缓存
1. lvgl 的高级效果关掉也能提升一些帧率
1. 关闭 lvgl 中的 assert
1. 图片的宽度和控件的位置最好都是偶数

参考下面的 code diff

- [双 buf 只复制更新区域](0001-双buf局部区域更新.patch)
- [竖屏横用旋转优化](0002-竖屏横用旋转优化算法.patch)
- [lvgl 代码段单独存放](0003-lvgl_draw-section-and-lv_code_load_psram.patch)

## label 显示超长文本滚动时卡顿

1. `lv_obj_set_style_anim_speed`加快速度
1. [修改动画的步长和动画速度](./label_long_text_scroll.diff)
