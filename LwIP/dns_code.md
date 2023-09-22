LwIP 中**dns.c**实现了域名解析功能，在知道服务器域名的情况下，可以获得该服务的 IP 地址。

# 开启编译选项

需要在`port/lwipopts.h`中定义**LWIP_DNS**宏的值，控制是否打开 DNS 功能

```c
//port/lwipopts.h
#define LWIP_DNS                        1
```

`lwipopts.h`会被`src/include/lwip/opt.h`引用, 并覆盖 opt.h 中的值

# dns 解析流程

## dns init

dns 初始化从 app 层调用如下函数开始:

```c
net_wlan_initial:
    net_ipv4stack_init();
        tcpip_init(NULL, NULL);
            lwip_init();//初始化协议栈所有模块
                dns_init();
                sys_timeouts_init();//初始化需要的timer
                    //遍历全局变量lwip_cyclic_timers中的timer

dns_init:
    //绑定udp端口, 设置接收处理函数
    if (dns_pcbs[0] == NULL)
        dns_pcbs[0] = udp_new_ip_type(IPADDR_TYPE_ANY);
        udp_bind(dns_pcbs[0], IP_ANY_TYPE, 0);//port 0, 即随意申请一个port即可?
        udp_recv(dns_pcbs[0], dns_recv, NULL);
    dns_init_local();
```

## 设置 dns server

在获取到 ip 地址和 gateway 之后, 就需要调用`dns_setserver`设置 dns server

- 固定 ip: 从 ip_config.ipv4.dns1 和 dns2 中获取
- dhcp: **在收到 dhcp ack 之后, 参照 dhcp_func.md 的 ack 处理**

```c
net_configure_address:
    case ADDR_TYPE_STATIC:
        //固定ip, 直接设置ip地址, 并设置dns server
        if(if_handle == &g_mlan)
            net_configure_dns((struct wlan_ip_config *)addr);
                dns_setserver(0, &tmp);//ip->ipv4.dns1
                dns_setserver(1, &tmp);//ip->ipv4.dns2
    case ADDR_TYPE_DHCP:
        netifapi_dhcp_start(&if_handle->netif);//开始dhcp流程
            netifapi_netif_common(n, NULL, dhcp_start);//调用dhcp_start

void dns_setserver(u8_t numdns, const ip_addr_t *dnsserver)
    dns_servers[numdns] = (*dnsserver);//存入全局变量, 最多两个
```

## app 查询某域名

当 app 层需要查询域名对应的 ip 是, 调用`dns_gethostbyname`即可:

### 查询 dns 缓存

```c
dns_gethostbyname
    return dns_gethostbyname_addrtype(hostname, addr, found, callback_arg, LWIP_DNS_ADDRTYPE_DEFAULT);
        //查询dns缓存是否命中, 命中则直接return
        dns_lookup(hostname, addr LWIP_DNS_ADDRTYPE_ARG(dns_addrtype));
            dns_lookup_local(name, addr LWIP_DNS_ADDRTYPE_ARG(dns_addrtype));
                //查询local_hostlist是否命中
            //遍历dns_table是否命中
            for (i = 0; i < DNS_TABLE_SIZE; ++i)
                if ((dns_table[i].state == DNS_STATE_DONE) &&...)//如果缓存项状态正常, 并且域名一致
                    ip_addr_copy(*addr, dns_table[i].ipaddr);//返回缓存项里的ip地址

        //缓存没有, 需要发起dns query
        return dns_enqueue(hostname, hostnamelen, found...);
```

### 发起 dns query

dns 缓存没有命中, 就需要向前面设置好的 dns server 发起查询请求

```c
dns_enqueue:
    //查询dns_table中是否已经正在发起的同域名的dns请求, 返回in progress

    //没有重复请求, 从dns_table获取一个新的entry
    for (i = 0; i < DNS_TABLE_SIZE; ++i)
        //使用DNS_STATE_UNUSED 或者 已缓存的最老的一个entry
    entry = &dns_table[i];
    //从dns_requests中获取一个新的请求entry
    for (r = 0; r < DNS_MAX_REQUESTS; r++)
        if (dns_requests[r].found == NULL)
            req = &dns_requests[i];

    //填充entry和req
    req->dns_table_idx = i; //保存缓存项的index, dns查询结束后需要根据此index找到req, 然后调用回调
    entry->state = DNS_STATE_NEW;
    req->found = found;//设置查询结束时的异步回调函数
    MEMCPY(entry->name, name, namelen);//设置域名
    dns_check_entry(i);//进入状态机
        case DNS_STATE_NEW:
            entry->txid = dns_create_txid();//随机生成的id, 用于收到报文时比较
            entry->state = DNS_STATE_ASKING;
            entry->server_idx = 0;//使用哪个dns server
            err = dns_send(i);//发送请求
                //申请pbuf构建报文
                p = pbuf_alloc(PBUF_TRANSPORT, (u16_t)(SIZEOF_DNS_HDR + strlen(entry->name)...);
                //获取dns server和port, 返回发送
                dst_port = DNS_SERVER_PORT;
                dst = &dns_servers[entry->server_idx];
                err = udp_sendto(dns_pcbs[pcb_idx], p, dst, dst_port);

```

## 处理 dns reply

```c
dns_recv:
    //将报文的header部分复制到遍历hdr
    pbuf_copy_partial(p, &hdr, SIZEOF_DNS_HDR, 0);
    //取出txid, 根据txid找到dns_table中对应的entry
    txid = lwip_htons(hdr.id);
    for (i = 0; i < DNS_TABLE_SIZE; i++)
        if ((entry->state == DNS_STATE_ASKING) && (entry->txid == txid))
            //比较收到的报文地址和dns server地址是否一致
            ip_addr_cmp(addr, &dns_servers[entry->server_idx])
            //比较收到的报文中域名和entry中是否一致
            res_idx = dns_compare_name(entry->name, p, SIZEOF_DNS_HDR);
            //获取报文中回答区域
            pbuf_copy_partial(p, &ans, SIZEOF_DNS_ANSWER, res_idx);
            if (ans.cls == PP_HTONS(DNS_RRCLASS_IN))
                //根据回答区域不同的type值, 分别处理, 比如常用的A类型
                if ((ans.type == PP_HTONS(DNS_RRTYPE_A)) &&...)
                    ip_addr_copy_from_ip4(dns_table[i].ipaddr, ip4addr);//保存ip地址到dns缓存
                    dns_correct_response(i, lwip_ntohl(ans.ttl));

//dns缓存保存之后, 需要处理存活时间, 并调用dns结束的回调函数
dns_correct_response:
    entry->state = DNS_STATE_DONE;//设置为最终状态
    entry->ttl = ttl;//保存存活时间
    dns_call_found(idx, &entry->ipaddr);//调用回调
        //遍历dns_requests, 根据idx找到req entry
        for (i = 0; i < DNS_MAX_REQUESTS; i++)
            if (dns_requests[i].found && (dns_requests[i].dns_table_idx == idx))
                (*dns_requests[i].found)(dns_table[idx].name, addr, dns_requests[i].arg);//调用回调
```

# 存活时间到期如何清理?

在`lwip_init`中会调用`sys_timeouts_init`会启动所有需要的 timer, 其中包括检查 dns 缓存是否到期的`dns_tmr`, interval 为**DNS_TMR_INTERVAL**:

```c
dns_tmr:
    //检查每个dns缓存entry
    dns_check_entries();
        for (i = 0; i < DNS_TABLE_SIZE; ++i)
            dns_check_entry(i);

dns_check_entry:
    case DNS_STATE_NEW://这里我们不关注new状态的entry, new状态的签名发起请求时已经处理
    case DNS_STATE_ASKING:
        //该状态下, 说明已经用默认的dns1 server发出了请求, 但是没有得到回复
        entry->server_idx++;
        err = dns_send(i);//选择dns2 server, 再发一次dns请求
    case DNS_STATE_DONE:
        if ((entry->ttl == 0) || (--entry->ttl == 0))//检查存活时间是否到期
            entry->state = DNS_STATE_UNUSED;//到期, 重置状态, 表示该缓存无效了
```
