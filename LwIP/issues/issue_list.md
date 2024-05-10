# beken 工作时遇到的问题

## socket recv ENOTCONN 错误

可能的原因有:

1. 如果确定 socket 经正确连接，`ENOTCONN`最有可能是由 socketfd 在您处于请求中间的情况下(可能在另一个线程中)被关闭引起的
1. TCP 连接的一端没有关闭连接，可能是远程端关闭了连接, 在调用时导致 ENOTCONN
1. libemqtt 代码相关: **Broker 主动关闭连接之前不会向 Client 发送任何 MQTT 数据包，而是直接关闭底层的 TCP 连接**
