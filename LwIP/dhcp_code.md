# dhcp 代码流程

## dhcp discover

在`net_configure_address`设置 DHCP 方式获取 ip 时, 会首先设置回调函数`wm_netif_status_callback`, 并调用`dhcp_start`开启 DHCP 流程

```c
dhcp_start:
    dhcp = netif_dhcp_data(netif);//获取网卡的client_data
    if (dhcp == NULL)//如果没有dhcp client data, 需要先申请并赋值到netif上
        dhcp = (struct dhcp *)mem_malloc(sizeof(struct dhcp));
        netif_set_client_data(netif, LWIP_NETIF_CLIENT_DATA_INDEX_DHCP, dhcp);
    //设置dhcp 收发端口
    dhcp_inc_pcb_refcount();
        dhcp_pcb = udp_new();
        //绑定端口, 设置接收处理函数
        udp_bind(dhcp_pcb, IP4_ADDR_ANY, DHCP_CLIENT_PORT);//port 67
        udp_connect(dhcp_pcb, IP4_ADDR_ANY, DHCP_SERVER_PORT);//port 68
        udp_recv(dhcp_pcb, dhcp_recv, NULL);
    //开始discover流程
    result = dhcp_discover(netif);
        //设置dhcp当前状态
        dhcp_set_state(dhcp, DHCP_STATE_SELECTING);
        //创建discover msg, 并填充需要的option
        result = dhcp_create_msg(netif, dhcp, DHCP_DISCOVER);
        //发送msg
        udp_sendto_if_src(dhcp_pcb, dhcp->p_out, IP_ADDR_BROADCAST, DHCP_SERVER_PORT, netif, IP4_ADDR_ANY);
        //设置dhcp timeout时间, 会在dhcp_fine_tmr中检查要不要重新发送
        dhcp->request_timeout = (msecs + DHCP_FINE_TIMER_MSECS - 1) / DHCP_FINE_TIMER_MSECS;
```

## dhcp offer

上面绑定的端口收到 dhcp 消息, 会调用`dhcp_recv`进行处理, 这里主要关注 offer 和 ack 消息

```c
dhcp_recv:
    //解析收到的dhcp报文,相关信息存入dhcp
    dhcp_parse_reply(dhcp, p);
        dhcp->msg_in = (struct dhcp_msg *)p->payload;
        //解析各类option, 然后存入dhcp相应位置
        if (!dhcp_option_given(dhcp, decode_idx))
            dhcp_got_option(dhcp, decode_idx); //是否保存了有个option
            dhcp_set_option_value(dhcp, decode_idx, value);//option value
    //获取msg type, 根据不同type处理
    msg_type = (u8_t)dhcp_get_option_value(dhcp, DHCP_OPTION_IDX_MSG_TYPE);
    if (msg_type == DHCP_ACK)//处理ack消息
    //处理offer消息
    else if ((msg_type == DHCP_OFFER) && (dhcp->state == DHCP_STATE_SELECTING))
        dhcp_handle_offer(netif);
            if (dhcp_option_given(dhcp, DHCP_OPTION_IDX_SERVER_ID))
                dhcp_select(netif);
```

## dhcp request

如果 offer 消息携带了 ip 信息, 就需要发送 dhcp request 申请使用该 ip:

```c
//开始request流程, 申请使用offer携带的ip
dhcp_select:
    //设置dhcp当前状态
    dhcp_set_state(dhcp, DHCP_STATE_REQUESTING);
    //创建request消息, 并填充需要的option
    result = dhcp_create_msg(netif, dhcp, DHCP_REQUEST);
    //发送msg
    udp_sendto_if_src(dhcp_pcb, dhcp->p_out, IP_ADDR_BROADCAST, DHCP_SERVER_PORT, netif, IP4_ADDR_ANY);
    //设置dhcp timeout时间, 会在dhcp_fine_tmr中检查要不要重新发送
    dhcp->request_timeout = (msecs + DHCP_FINE_TIMER_MSECS - 1) / DHCP_FINE_TIMER_MSECS;
```

## dhcp ack

和 dhcp offer 一样的流程, 解析收到的报文, 如果是 dhcp ack 消息, 则按下面处理:

```c
dhcp_recv:
    //解析收到的dhcp报文,相关信息存入dhcp
    //获取msg type, 根据不同type处理
    if (msg_type == DHCP_ACK)//处理ack消息
        if (dhcp->state == DHCP_STATE_REQUESTING)
            dhcp_handle_ack(netif);
                //设置ip地址和其他信息
                 ip4_addr_copy(dhcp->offered_ip_addr, dhcp->msg_in->yiaddr);
                //设置dhcp 释放时间
                dhcp->offered_t0_lease = dhcp_get_option_value(dhcp, DHCP_OPTION_IDX_LEASE_TIME);
                //设置ntp server
                dhcp_set_ntp_servers(n, ntp_server_addrs);
                //设置dns server
                dns_setserver(n, &dns_addr);
            dhcp_bind(netif);
                dhcp_set_state(dhcp, DHCP_STATE_BOUND);//最终状态
                //网卡使用该ip
                netif_set_addr(netif, &dhcp->offered_ip_addr, &sn_mask, &gw_addr);
                    NETIF_STATUS_CALLBACK(netif);//设置完ip, 调用netif status cb
```

## netif status cb

开始前已经设置了回调函数`wm_netif_status_callback`, 前面设置网卡 ip 时就会调用 cb 函数

```c
wm_netif_status_callback:
    if (n->flags & NETIF_FLAG_UP)//确定网卡已经up
        if(dhcp != NULL)//检查dhcp信息, 固定IP的默认好使, 不做检查
            if (dhcp->state == DHCP_STATE_BOUND)
                //dhcp过程已经结束, 说明已经获得了IP
                os_printf("IP up: %d.%d.%d.%d\r\n"...);//打印ip地址
                //上报wlan status事件: RW_EVT_STA_GOT_IP

```

# 存活时间到期如何处理?

在`lwip_init`中会调用`sys_timeouts_init`会启动所有需要的 timer, 其中包括检查 dns 缓存是否到期的`dhcp_coarse_tmr`, interval 为**DHCP_COARSE_TIMER_MSECS**:

```c
dhcp_coarse_tmr:
    //遍历所以已添加的网卡
    struct netif *netif = netif_list;
    while (netif != NULL)
        struct dhcp *dhcp = netif_dhcp_data(netif);//获取dhcp记录
        if (dhcp->t0_timeout && (++dhcp->lease_used == dhcp->t0_timeout))//t0超时, 重新discover
            dhcp_release(netif);
                dhcp_set_state(dhcp, DHCP_STATE_OFF);
                //发起dhcp release消息
                //清空网卡的ip
                netif_set_addr(netif, IP4_ADDR_ANY4, IP4_ADDR_ANY4, IP4_ADDR_ANY4);
            dhcp_discover(netif);//发起新的discover流程
```
