LwIP 中有各种数据包的处理，包括数据包的接收和发送以及各层协议处理；为了记录这些信息，LwIP 中专门实现了性能统计模块.

# 宏定义开关

opt.h 有各个子模块的统计开关, 总开关为**LWIP_STATS**

```c
#define LINK_STATS                      0
#define ETHARP_STATS                    0
#define IP_STATS                        0
#define IPFRAG_STATS                    0
#define ICMP_STATS                      0
#define IGMP_STATS                      0
#define UDP_STATS                       0
#define TCP_STATS                       0
#define MEM_STATS                       0
#define MEMP_STATS                      0
#define SYS_STATS                       0
#define LWIP_STATS_DISPLAY              0
#define IP6_STATS                       0
#define ICMP6_STATS                     0
#define IP6_FRAG_STATS                  0
#define MLD6_STATS                      0
#define ND6_STATS                       0
#define MIB2_STATS                      0
```

# 统计结构体

## stats_mem

用于统计内存的使用情况，包括内存堆和各个内存池:

```c
struct stats_mem {
#if defined(LWIP_DEBUG) || LWIP_STATS_DISPLAY
  const char *name;
#endif /* defined(LWIP_DEBUG) || LWIP_STATS_DISPLAY */
  STAT_COUNTER err;  //内存分配出错次数
  mem_size_t avail; //可使用的内存数量
  mem_size_t used; //已经使用的内存数量
  mem_size_t max; //运行过程中最大使用的内存量
  STAT_COUNTER illegal; //内存操作非法的次数
};
```

## stats_proto

用于统计数据包的收发情况:

```c
struct stats_proto {
  STAT_COUNTER xmit;             /* 发送的数据包量. */
  STAT_COUNTER recv;             /* 接收到的数据包量. */
  STAT_COUNTER fw;               /* 转发的数据包量. */
  STAT_COUNTER drop;             /* 丢弃的数据包量. */
  STAT_COUNTER chkerr;           /* 校验和出错的数据包数量. */
  STAT_COUNTER lenerr;           /* 非法长度的数据包量. */
  STAT_COUNTER memerr;           /* 由于内存分配失败的数据量. */
  STAT_COUNTER rterr;            /* 路由出错的次数. */
  STAT_COUNTER proterr;          /* 协议出错数. */
  STAT_COUNTER opterr;           /* 可选字段的错误数. */
  STAT_COUNTER err;              /* 其他错误的次数. */
  STAT_COUNTER cachehit;         /* 缓存命中次数 */
};
```

## stats_sys

用于统计系统信号量和锁的使用情况

```c
/** System element stats */
struct stats_syselem {
  STAT_COUNTER used;
  STAT_COUNTER max;
  STAT_COUNTER err;
};

/** System stats */
struct stats_sys {
  struct stats_syselem sem;
  struct stats_syselem mutex;
  struct stats_syselem mbox;
};
```

# stats_display函数
`stats_display`用于显示各个部分的统计数据.