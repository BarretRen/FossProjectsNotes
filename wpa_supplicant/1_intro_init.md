wpa_supplicant 就是 WiFi 驱动和用户的中转站外加对协议和加密认证的支持.

# 源码目录

wpa_supplicant 的源码目录介绍

```
├── hs20
│   └── client
├── src
│   ├── ap            // hostapd 相关功能
│   ├── common        // 通用函数和定义
│   ├── crypto        // 各种加密功能
│   ├── drivers       // 对接底层驱动
│   ├── eap_common    // eap 相关
│   ├── eapol_auth
│   ├── eapol_supp    //eapol状态机和802.1x处理
│   ├── eap_peer      //eap状态机
│   ├── eap_server
│   ├── fst           // fst 模块
│   ├── l2_packet     // 链路层的访问封装
│   ├── p2p           // WiFi P2P协议,
│   ├── pae           // ieeee802 协议
│   ├── radius        // Remote Authentication Dial In User Service 消息处理
│   ├── rsn_supp      // RSN协议(Robust Secure Network)，即通常所说的WPA2安全模式
│   ├── tls           // tls 协议
│   ├── utils         // 包括 RFC1341编解码, 通用的辅助函数, 双链表, UUID, debug, epool
│   └── wps           // wps 功能的实现
└── wpa_supplicant    //wpas核心功能和ctrl_iface控制界面
    ├── binder
    ├── dbus
    ├── doc
    ├── examples
    ├── systemd
    ├── utils
    ├── vs2005
    └── wpa_gui-qt4
```

# 重要的数据结构

- wpa_global 是一个全局性质的上下文信息，它通过 iface 变量指向一个 wpa_supplicant 链表
- **wpa_supplicant 属于核心数据结构**，一个 interface 对应有一个 wpa_supplicant 对象，系统中所有 wpa_supplicant 对象都通过 next 变量链接在一起.
- wpa_interface 表示一个网络设备, 包含该设备的信息
- wpa_drivers 是一个全局变量, 定义在 drivers.c, 包含不同设备的 wpas 驱动(**wpa_driver_ops**). **wpa_driver_ops 是 driver 模块的核心数据结构**，内部定义了很多函数指针，通过此方法 wpa_supplicant 能够隔离上层使用者和具体的 drivers.

## wpa_global

基本属性如下:

```c
struct wpa_global {
    //指向wpa_s链表的头部
    struct wpa_supplicant *ifaces;
    //运行时参数
    struct wpa_params params;
    //全局控制接口
    struct ctrl_iface_global_priv *ctrl_iface;
    //dbug通信, 暂时用不到
    struct wpas_dbus_priv *dbus;
    struct wpas_binder_priv *binder;
    //driver wrapper上下文信息
    void **drv_priv;
    //driver wrapper个数
    size_t drv_count;
};
```

## wpa_supplicant

基本属性如下:

```c
struct wpa_supplicant {
    //指向global全局变量
    struct wpa_global *global;
    //radio work链表, 所有要调用驱动的任务都要加到链表中, 等待radio_work_check_next启动timer执行
    struct wpa_radio *radio;
    //指向wpa_s链表的下一个
    struct wpa_supplicant *next;
    //当前设备连接的wifi名
    struct wpa_ssid *current_ssid;
    //当前设备连接的wifi信息
    struct wpa_bss *current_bss;
    //保存wifi扫描结果的链表
    struct dl_list bss_id;
    //当前状态
    enum wpa_states wpa_state;
};
```

## wpa_interface

基本属性如下:

```c
struct wpa_interface {
     // 配置文件名,也就是-c 指定的wpa_supplicant.conf
    const char *confname;
     // 控制接口unix socket 地址，配置文件中ctrl_interface指定的
    const char *ctrl_interface;
     //网络设备对应的驱动和参数
    const char *driver;
    const char *driver_param;
     //网络接口设备，代表wlan0
    const char *ifname;
};
```

# wpa_supplicant 启动流程

## 启动命令

```shell
wpa_supplicant -D nl80211 -i wlan0 -c /etc/wpa_supplicant.conf -B
```

- -D 驱动程序名称（可以是多个驱动程序：nl80211，wext）
- -i 接口名称
- -c 配置文件
- -B 在后台运行守护进程

## 初始化启动流程

```c
//wpa_supplicant/main.c
main:
    // 重要的数据结构1
    struct wpa_interface *ifaces, *iface;
    // 重要的数据结构2
    struct wpa_global *global;
    // 设置打印调试等级
    params.wpa_debug_level = MSG_INFO;
    //输入输出重定向到/dev/null
    wpa_supplicant_fd_workaround(1);

    for (;;)
        c = getopt(argc, argv, "b:Bc:C:D:de:f:g:G:hi:I:KLMm:No:O:p:P:qsTtuvW");
        switch (c)
            //参数解析

    //主要函数1 : 创建并初始化一个global
    global = wpa_supplicant_init(&params);
        global = os_zalloc(sizeof(*global));//创建一个global对象
        global->ctrl_iface = wpa_supplicant_global_ctrl_iface_init(global);//初始化全局控制接口对象
        global->drv_priv = os_calloc(global->drv_count, sizeof(void *));//分配全局driver wrapper上下文信息数组
        //注册定时清理timer
        eloop_register_timeout(WPA_SUPPLICANT_CLEANUP_INTERVAL, 0, wpas_periodic, global, NULL);

    for (i = 0; exitcode == 0 && i < iface_count; i++)
        // 主要函数2 : 添加多个无线网络设备, 一个wpa_s代表一个设备
        wpa_s = wpa_supplicant_add_iface(global, &ifaces[i], NULL);
            wpa_s->global = global;
            wpa_supplicant_init_iface(wpa_s, &t_iface);
                //根据iface内容初始化wpa_s
                wpas_init_driver(wpa_s, iface);//初始化驱动
                    wpa_supplicant_set_driver(wpa_s, driver);
                        for (i = 0; wpa_drivers[i]; i++)//遍历数组中的驱动, 设置到wpa_s
                            select_driver(wpa_s, i);
                                wpa_s->driver = wpa_drivers[i];
            //将新建的wpa_s填入到global链表
            wpa_s->next = global->ifaces;
            global->ifaces = wpa_s;

    // 启动, wpa_supplicant 通过epoll 方式实现多路I/O复用
    if (exitcode == 0)
        exitcode = wpa_supplicant_run(global);
            eloop_run();//开始主循环

    // 释放相关资源
    wpa_supplicant_deinit(global);
    fst_global_deinit();
```
