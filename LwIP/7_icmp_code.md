# icmp_echo_hdr

lwip 中使用`struct icmp_echo_hdr`作为所有 ICMP 报文的 header, 因为各个类型的 ICMP 报文首部都是差不多的，所以能将 ICMP 回显报文首部用于其他 ICMP 报文首部.

```c
struct icmp_echo_hdr {
    PACK_STRUCT_FLD_8(u8_t type);     //类型
    PACK_STRUCT_FLD_8(u8_t code);     //代码
    PACK_STRUCT_FIELD(u16_t chksum);  //校验和
    PACK_STRUCT_FIELD(u16_t id);      //标识符
    PACK_STRUCT_FIELD(u16_t seqno);   //序号
} PACK_STRUCT_STRUCT;
```

此外 LwIP 还定义了很多**宏与枚举类型的变量对 ICMP 的类型及代码字段进行描述, 还有一些宏用于对报文的字段进行读写操作**.
<font color='red'>lwip 只对 ICMP 回显报文和某些差错报文进行处理, 其他的只做识别.</font>

# ICMP 代码流程

## 发送 ICMP 差错报文

lwip 支持发送如下几种差错报文:

- 目标不可达: ip 报文无法传递到协议层, 调用`icmp_dest_unreach`
- 端口不可达: 传输层无法传递到应用层, 找不到端口, 调用`icmp_port_unreach`
- 超时: 报文 TTL 为 0, 或分片数据在重装时超时, 调用`icmp_time_exceeded`

上面三个函数最终都调用`icmp_send_response`发送

```c
icmp_send_response:
    //申请pbuf, 大小为icmp header + ip header + 8 bytes
    response_pkt_len = IP_HLEN + ICMP_DEST_UNREACH_DATASIZE;
    q = pbuf_alloc(PBUF_IP, sizeof(struct icmp_echo_hdr) + response_pkt_len, PBUF_RAM);
    //指向icmp header, 填充内容
    icmphdr = (struct icmp_echo_hdr *)q->payload;
    //从原始报文中复制ip header + 8 bytes
    SMEMCPY((u8_t *)q->payload + sizeof(struct icmp_echo_hdr), (u8_t *)p->payload, response_pkt_len);
    //根据原始报文的src addr找到网卡
    netif = ip4_route(&iphdr_src);
        //遍历所有已保存且up的网卡, 对比ip地址
    //发送ip包
    ip4_output_if(q, NULL, &iphdr_src, ICMP_TTL, 0, IP_PROTO_ICMP, netif);
```

## 处理收到的 ICMP 报文

LwIP 协议是轻量级 TCP/IP 协议栈，所以对 ICMP 报文中很多类型的报文都不做处理， LwIP 会将这些不处理的报文丢掉，只对 ICMP 回显请求报文就做出处理.

```c
icmp_input:
    //获取icmp报文的type, 分别处理
    type = *((u8_t *)p->payload);
    switch (type)
        case ICMP_ECHO://只处理回显类型的报文
            //判断dest addr是否为单播, 不是则返回错误
            //调整回显报文中src和dest, 设置相关字段, 在此基础上生成回显应答报文
            iecho = (struct icmp_echo_hdr *)p->payload;
            if (!pbuf_add_header(p, hlen))//添加ip header
                struct ip_hdr *iphdr = (struct ip_hdr *)p->payload;
                //设置ip header中的src和dest地址
                ICMPH_TYPE_SET(iecho, ICMP_ER); //echo reply
                //发送echo reply
                ret = ip4_output_if(p, src, LWIP_IP_HDRINCL, ICMP_TTL, 0, IP_PROTO_ICMP, inp);
        default:
            //其他报文, 直接丢掉
```
