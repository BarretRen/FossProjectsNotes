# 超时链表

LwIP 通过一个`struct sys_timeo`类型的数据结构管理与超时链表相关的所有超时事件。
LwIP 定义了一个`struct sys_timeo`类型的指针`next_timeout`，并且将`next_timeout`指向当前内核中链表头部，所有被注册的超时事件都会**按照超时时间从小到大的顺序**排列在超时链表上.

```c
static struct sys_timeo *next_timeout;
```

# 增删 timer

## 初始化 lwip 内部 timer

在 lwip 初始化时, 会将各个子模块所需要的 timer 都添加到超时链表中, 这些 timer 是固定添加的, 用于协议栈处理.

```c
tcpip_init(NULL, NULL);
    lwip_init();//初始化协议栈所有模块
        sys_timeouts_init();//初始化需要的timer
            //遍历全局变量lwip_cyclic_timers中的timer
            for (i = (LWIP_TCP ? 1 : 0); i < LWIP_ARRAYSIZE(lwip_cyclic_timers); i++)
                sys_timeout(lwip_cyclic_timers[i].interval_ms, lwip_cyclic_timer...);//添加到超时链表中
    //启动tcpip thread
    sys_thread_new(TCPIP_THREAD_NAME, tcpip_thread, NULL, TCPIP_THREAD_STACKSIZE, TCPIP_THREAD_PRIO);
```

## 添加一个 timer

使用函数**tcpip_timeout**可以动态添加一个 timer(), 最终会调用`sys_timeout`:

```c
sys_timeout:
    //计算未来超时时间
    next_timeout_time = (u32_t)(sys_now() + msecs);
    sys_timeout_abs(next_timeout_time, handler, arg);
        //创建新的timeout
        timeout = (struct sys_timeo *)memp_malloc(MEMP_SYS_TIMEOUT);
        //设置超时处理函数超时时间
        timeout->h = handler;
        timeout->time = abs_time;
        //添加到超时链表next_timeout中, 链表按超时时间从小到大排序
```

## 删除一个 timer

使用函数**tcpip_untimeout**可以动态删除一个 timer, 最终要调用`sys_untimeout`并传入超时处理函数.
`sys_untimeout`会遍历超时链表, 根据输入参数查找到对应的 timeout, 然后从链表中删除.

# 超时检查

有两种超时检查的方式，分别用于有 os 和无 os 的情况：

- `sys_check_timeouts`：用于无 os 裸机系统， app 程序需要周期性调用此函数去检查超时链表是否有超时的 timer
- `tcpip_timeouts_mbox_fetch`： 最终也是调用`sys_check_timeouts`, 用于有 os 的系统. 在 tcpip thread 主循环调用, **用于阻塞式等待 mbox 消息, 并同时检测 timer 超时**.
  - 在等待 mbox 消息过程中出现 timer 超时, 就会指向超时处理.
  - 收到 mbox 消息时, 函数退出, 否则一致阻塞

## tcpip_timeouts_mbox_fetch

```c
//tcpip thread主循环
tcpip_thread:
    while (1)
        TCPIP_MBOX_FETCH(&tcpip_mbox, (void **)&msg);//等待mbox消息, 并在等待时处理超时
            //宏指向tcpip_timeouts_mbox_fetch函数
        tcpip_thread_handle_msg(msg);

tcpip_timeouts_mbox_fetch:
again:
    sleeptime = sys_timeouts_sleeptime();//计算到链表最小的timer超时还有多长时间
    if (sleeptime == SYS_TIMEOUTS_SLEEPTIME_INFINITE)
        //超时链表为空, 一直等待mbox消息即可, 等到消息就退出
        sys_arch_mbox_fetch(mbox, msg, 0);
        return;
    else if (sleeptime == 0)
        //已经有timer超时了, 进行超时处理
        sys_check_timeouts();
        goto again;//返回开始继续等待

    //如果链表不为空, 并且当前没有超时, 等待mbox消息, 等待时间为sleeptime
    res = sys_arch_mbox_fetch(mbox, msg, sleeptime);
     if (res == SYS_ARCH_TIMEOUT)
        //sleeptime时间耗尽, 没有mbox消息, 就需要处理先处理超时
        sys_check_timeouts();
        goto again;//返回开始继续等待
```

## sys_check_timeouts

```c
sys_check_timeouts:
    now = sys_now();
    while(1)
        //如果链表第一个timer没有超时, 表示所有timer都没有超时, 退出
        if (TIME_LESS_THAN(now, tmptimeout->time))
            return;
        //前面没return, 说明第一个timer超时了
        next_timeout = tmptimeout->next;//链表指向下一个timer
        handler = tmptimeout->h;
        memp_free(MEMP_SYS_TIMEOUT, tmptimeout);//释放当前timer的内存
        if (handler != NULL)
            handler(arg);//执行超时处理函数
```

# 统一的超时处理函数

在初始化内部 timer 时可以看到, 每个 timer 都设置的同一个处理函数, 因为基本处理是一致的:

- 取出 timer 实际的处理函数执行, `lwip_cyclic_timers`已定义好
- 重启 timer

```c
lwip_cyclic_timer:
    //取出timer实际的handler, 运行
    const struct lwip_cyclic_timer *cyclic = (const struct lwip_cyclic_timer *)arg;
    cyclic->handler();
    //重新添加timer, 注意这里有个纠正机制
    if (TIME_LESS_THAN(next_timeout_time, now))
        //timer本应超时的时间 + interval < 当前时间, 说明少了一次超时处理, 按当前时间计算下一次超时时间
        sys_timeout_abs((u32_t)(now + cyclic->interval_ms), lwip_cyclic_timer, arg);
    else
        //timer本应超时的时间 + interval > 当前时间, 按此时间添加timer
         sys_timeout_abs(next_timeout_time, lwip_cyclic_timer, arg);
```
