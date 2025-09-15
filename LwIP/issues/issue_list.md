# beken 工作时遇到的问题

## socket recv ENOTCONN 错误

可能的原因有:

1. 如果确定 socket 经正确连接，`ENOTCONN`最有可能是由 socketfd 在您处于请求中间的情况下(可能在另一个线程中)被关闭引起的
1. TCP 连接的一端没有关闭连接，可能是远程端关闭了连接, 在调用时导致 ENOTCONN
1. libemqtt 代码相关: **Broker 主动关闭连接之前不会向 Client 发送任何 MQTT 数据包，而是直接关闭底层的 TCP 连接**

## 本地 socket 连接发送端大量占用缓冲区, 导致 lwip tx 内存超出限制

1. 增大 lwip 总内存和 tx 最大限制, `MEM_SIZE`和`MEM_MAX_TX_SIZE`
1. 发送端通过`TCP_NODELAY`禁用 nagle 算法, 有数据直接发送, 不要等待组合

```c
int enable = 1;
lwip_setsockopt(i, IPPROTO_TCP, TCP_NODELAY, &enable, sizeof(enable));
```

## 延迟 ACK 机制导致发送端 unacked 过大

LWIP 默认采用延迟 ACK 机制，即在接收到数据后不会立即发送 ACK，而是等待以下两种情况之一, 可能导致发送端 unacked 报文累积：

- 有数据要发送时，将 ACK 附带在数据包中
- 延迟定时器超时（`tcp_fasttmr`, 默认 200ms）后发送纯 ACK

对于下面情况会立刻发送 ACK:

- 如果接收到的数据超过一定量(TCP_WND_UPDATE_THRESHOLD)
- 如果收到 PUSH 标志(如 HTTP 请求)

修改方式:

1. 修改`tcp_fasttmr`调用频率

```c
#define TCP_TMR_INTERVAL 10  // 默认 200ms，改为 10ms 让 ACK 更快发出

void tcp_fasttmr(void)
    while (pcb != NULL)
        if (pcb->flags & TF_ACK_DELAY)
            tcp_ack_now(pcb);
            tcp_output(pcb);
        if (pcb->refused_data != NULL)
            tcp_process_refused_data(pcb);//处理refused data, 触发ack
                TCP_EVENT_RECV(pcb, refused_data, ERR_OK, err);
```

2. 修改`TCP_WND_UPDATE_THRESHOLD`

```c
#define TCP_WND_UPDATE_THRESHOLD 0 // 收到任何数据都立即 ACK

//相关代码
void tcp_recved(struct tcp_pcb *pcb, u16_t len)
    if (wnd_inflation >= TCP_WND_UPDATE_THRESHOLD)
        tcp_ack_now(pcb); //发送ack
        tcp_output(pcb);//发送缓存数据
```

3. 在`tcp_receive`函数中, 接收到数据后立即调用`tcp_ack_now`强制发送 ACK

```c
void tcp_receive(struct tcp_pcb *pcb)
{
  /* ...原有代码... */

  if ((tcplen > 0) && (pcb->state < CLOSE_WAIT))
    tcp_ack_now(pcb);/* 强制立即发送ACK */

  /* ... */
}
```

## connection closed by peer

当 LwIP 报告 connection closed by peer 时，它告诉你：对端发送了一个带有 FIN 标志的 TCP 包，主动发起了 TCP 连接的终止流程（四次挥手），而 LwIP 作为接收方，已经完整地处理了这个关闭流程

一个正常的 TCP 连接关闭是“四次挥手”：

1. 主动关闭方（在这里就是“对端/peer”）发送一个 FIN 包。
1. 被动关闭方（在这里是你的 LwIP 设备）收到 FIN 后，回应一个 ACK 包，并通知你的应用程序（例如，recv 返回 0，或者 err 回调函数被调用并提示连接关闭）。
1. 你的 LwIP 设备（被动关闭方）继续发送完所有未发送的数据后（如果需要），也发送一个 FIN 包。
1. 对端收到你的 FIN 包后，回应一个 ACK 包。连接完全关闭。

## socket errno 104

Socket error 104 对应的是 ECONNRESET。它的字面意思是“连接被对端重置”。通俗来讲，就是你的设备和服务器已经成功建立了 TCP 连接，但在通信过程中，服务器端（或中间的某个网络设备）主动发送了一个带有 RST 标志的 TCP 包，强行中断了这条连接.

lwip 内部 err ERR_RST 经过函数`err_to_errno`被映射为 104, 然后通过`sock_set_errno`设置 errno 变量.

## select 机制

LWIP 为了高效地模拟 select() 的多路复用功能，采用了一种计数器机制（select_waiting 或 rcvevent）来跟踪每个 socket 上的事件状态。

- NETCONN_EVT_RCVPLUS (加事件)：
  - 何时触发：当底层协议栈（如 TCP）接收到新的数据并放入 socket 的接收缓冲区时。
  - 作用：内部计数器 加 1。这表示“有新的数据可读事件发生了”。
  - 对 select() 的影响：如果计数器从 0 变为 1，意味着 socket 从“不可读”变成了“可读”。这时，如果 select() 正在等待这个 socket，就需要被唤醒。
- NETCONN_EVT_RCVMINUS (减事件)：
  - 何时触发：当应用程序通过 recv(), read(), netconn_recv() 等函数从 socket 的接收缓冲区中成功读取走数据后。
  - 作用：内部计数器 减 1。这表示“一个可读事件已经被消费掉了”。
  - 对 select() 的影响：递减计数器。如果计数器减到 0，意味着所有已通知的“可读事件”都已经被应用程序处理完毕，接收缓冲区可能已经空了。此时，socket 应- 该从“可读”状态变回“不可读”状态，这样下一次调用 select() 时，如果没有新数据到来，就不会立即返回

工作流程示例：
假设一个 TCP socket 的接收缓冲区初始为空，内部计数器为 0。

1. 数据包 1 到达：
   - LWIP 调用 `lwip_select_fd_callback(fd, NETCONN_EVT_RCVPLUS, 1);`
   - **计数器从 0 -> 1**。由于状态从无到有，`select()` 线程被唤醒。
   - 应用程序的 `select()` 返回，指示 socket 可读。
1. 应用程序调用 `recv()` 读取数据包 1：
   - 读取成功后，LWIP 会调用 `lwip_select_fd_callback(fd, NETCONN_EVT_RCVMINUS, 1);`
   - **计数器从 1 -> 0**。
   - 此时，如果接收缓冲区真的空了，socket 就不再处于可读状态。
1. 数据包 2 和 3 紧接着到达：
   - LWIP 可能会调用两次 `lwip_select_fd_callback(fd, NETCONN_EVT_RCVPLUS, 1);`
   - **计数器从 0 -> 1** (第一次加，唤醒 `select`)，然后 **1 -> 2** (第二次加，但计数器已大于 0，可能不会再次唤醒)。
1. 应用程序再次调用 `recv()`：
   - 这次调用可能只读取了数据包 2。
   - LWIP 会调用 `lwip_select_fd_callback(fd, NETCONN_EVT_RCVMINUS, 1);`
   - **计数器从 2 -> 1**。
   - 因为计数器是 1（大于 0），socket **仍然处于可读状态**（因为数据包 3 还在缓冲区里），所以下一次 `select()` 会立即返回。
