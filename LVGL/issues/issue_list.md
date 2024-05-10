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
