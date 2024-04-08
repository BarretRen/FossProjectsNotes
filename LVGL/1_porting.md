LVGL 以源码的形式发布, 需要复制到自己的工程中编译并初始化. 下面是主要的步骤:

# 加入工程

1. 复制 lvgl 文件夹到自己的工程中, 下载地址: https://github.com/lvgl/lvgl.git
1. 复制`lvgl/lv_conf_template.h`为`lv_conf.h`进行自定义配置
1. 设置 lvgl tick source, lvgl 需要用来维持内部的计时. 两种方式:
   1. 单独的线程调用`lv_tick_inc`手动更新 lvgl 内部的变量`sys_time`
   1. 设置`LV_TICK_CUSTOM_SYS_TIME_EXPR`指定其他 tick 来源, 比如操作系统的计时函数
1. 引用头文件`lvgl/lvgl.h`, 调用相关的 API

# 加入编译

## make

引入 lvgl 目录下的 mk 文件即可:

```
include $(SOURCE_DIR)/lvgl/lvgl.mk
# 操作CSRCS编译
```

## cmake

lvgl 下已经存在 cmakelists.txt, 使用`add_subdirectory`引入 lvgl 目录即可, 在使用时链接 lvgl 库与应用程序一起编译:

```
add_subdirectory(lvgl)
#...
add_executable(LittleGL main.c)

# The target "LittleGL" depends on LVGL
target_link_libraries(LittleGL PRIVATE lvgl::lvgl lvgl::examples lvgl_demos)
```

# 初始化

1. 调用`lv_init`初始化 lvgl
1. 调用`lv_disp_draw_buf_init`初始化 draw buffer. lvgl 需要使用一块内存空间保存要显示的数据.
1. 初始化驱动, 并注册到 lvgl
   1. 调用`lv_disp_drv_register`注册 draw buffer 和显示驱动函数, 启动 refresh timer.
   1. 调用`lv_indev_drv_register`注册输入设备的 read 驱动函数, 比如键盘/触摸等. 并启动 indev read timer.
   1. <font color='red'>如果 lvgl 需要直接访问文件, 需要调用`lv_fs_drv_register`注册 fs 驱动函数</font>
      - lvlg 内置了四种 fs 访问接口, 可以在`lv_conf.h`打开`LV_USE_FS`前缀的宏
1. 启动一个高优先级线程调用`lv_task_handler`, 用于保持 lvgl 运行. task 内部调用`lv_timer_handler`处理各个超时的 timer, 刷新屏幕或处理输入设备的事件.

# 其他配置

## log 打印函数

1. 可以直接使用`printf`, 设置`LV_LOG_PRINTF`为 1 即可
1. 如果不能使用`printf`, 需要用`lv_log_register_print_cb`注册自定义的 log 打印函数

## cpu/帧率/mem

在`lv_conf.h`中打开如下宏, 可以在屏幕上显示帧率/mem/cpu 等性能信息(刷新使用 refresh timer`_lv_disp_refr_timer`):

- `LV_USE_PERF_MONITOR`: 对应初始化函数`perf_monitor_init`
- `LV_USE_MEM_MONITOR`: 对应初始化函数`mem_monitor_init`
