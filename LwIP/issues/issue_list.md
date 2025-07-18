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
