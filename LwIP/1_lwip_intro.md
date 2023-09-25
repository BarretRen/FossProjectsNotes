- 数据的发送过程, 可以概括为 TCP/IP 的各层协议对数据进行封装的过程
- 数据的接收过程, 可以概括为 TCP/IP 的各层协议对数据进行解析的过程

# LwIP 初步介绍

## 什么是 LwIP

LwIP 全名： Light weight IP, 意思是轻量化的 TCP/IP 协议, 是瑞典计算机科学院 (SICS) 的 Adam Dunkels 开发的一个小型开源的 TCP/IP 协议栈.

1. 资源开销低, 轻量化
1. 支持协议完成, 几乎支持 TCP/IP 所以常见协议
1. 实现了一些常见的 app, 比如 DHCP client, DNS client
1. 同时提供三种编程接口: RAW API/NETCONN API/Socket API
1. 高度可移植, **既可以移植到操作系统上运行, 也可以在无操作系统的情况下独立运行**
1. 开源免费, 而且发展历史久, 功能稳定

## 源码目录

LwIP 内核是由一系列模块组合而成的，这些模块包括： TCP/IP 协议栈的各种协议、内存管理模块、数据包管理模块、网卡管理模块、网卡接口模块、基础功能类模块、API 模块.
构成每个模块的头文件都被组织在了 include 目录中，而源文件则根据类型被分散地组织在 api、 apps、 core、 netif 目录中.

- **TCP 模块的实现是 LwIP 的最大特点**，它以很小的资源开销几乎实现了 TCP 协议中规定的全部内容
- RAW/Callback API 是 LwIP 的一大特色

```plain
├── api                ---- NETCONN和socket API相关, 仅用于有操作系统的环境
├── apps               ---- 实现的常见app的源文件
│   ├── altcp_tls
│   ├── http
│   ├── lwiperf
│   ├── mdns
│   ├── mqtt
│   ├── netbiosns
│   ├── smtp
│   ├── snmp
│   ├── sntp
│   └── tftp
├── core               ---- 协议栈核心源文件
│   ├── ipv4           -- ip4协议相关
│   ├── ipv6           -- ip6协议相关
│   ├── altcp_alloc.c
│   ├── altcp.c
│   ├── altcp_tcp.c
│   ├── def.c          -- 通用基础函数, 比如字节序转换
│   ├── dns.c          -- 域名解析协议
│   ├── inet_chksum.c  -- 报文校验
│   ├── init.c         -- 检查lwip宏配置, 初始化
│   ├── ip.c           -- 封装的ipv4和ipv6中的函数,统一接口
│   ├── mem.c          -- c malloc或lwip管理heap区域
│   ├── memp.c         -- 静态内存池
│   ├── netif.c        -- 管理网卡的注册删除, 使能, 设置ip等
│   ├── pbuf.c         -- 封装保存网络报文
│   ├── raw.c          -- 传输层协议框架, 可以用于实现自定义传输层协议
│   ├── stats.c        -- 状态和统计
│   ├── sys.c          -- 临界区相关的操作
│   ├── tcp.c          -- 管理TCP连接
│   ├── tcp_in.c       -- 处理TCP报文输入
│   ├── tcp_out.c      -- 处理TCP报文输出
│   ├── timeouts.c     -- 超时处理机制
│   └── udp.c          -- UDP协议处理
├── include            ---- 头文件
└── netif              ---- 网卡移植相关的文件, 实现接口以便让lwip管理网卡
```

# 三种 API 接口

LwIP 提供了三种编程接口，分别为 RAW/Callback API、 NETCONN API、 SOCKET API:

- 易用性: 从左到右依次提高
- 执行效率: 从左到右依次降低

## RAW/Callback API

- **在没有操作系统支持的裸机环境中，只能使用这种 API 进行开发**
- 在有操作系统的环境中, 用户代码**以回调函数的形式成为 lwip 的一部分, 与 lwip 内核代码在同一线程**.

## NETCONN API

NETCONN API 是基于操作系统的 IPC 机制（即信号量和 mbox）实现的，它的设计将 LwIP 内核代码和网络应用程序分离成了独立的线程.

- 操作系统下, **lwip 内核代码在`tcpip_thread`线程**运行, 只负责数据包的封装和拆解
- 使用 NETCONN API 的代码在其他线程, 对网络连接进行抽象, **像操作文件一样操作网络连接和数据读写**, 但需要了解 lwip 内部的数据结构

## SOCKET API

Socket API 即标准的 socket 变成, 对网络连接进行了高级的抽象，使得用户可以像操作文件一样操作网络连接, 使用 socket 的 buffer 结构且**不用关系 lwip 内部的数据结构**。
**LwIP 的 Socket API 是基于 NETCONN API 实现的**，所以效率上相较前者要打个折扣.
