# struct netif

LwIP 使用`struct netif`来抽象描述一个网卡，由于网卡是直接与硬件打交道的，硬件不同则处理基本是不同的，所以必须由**用户提供最底层接口函数(比如网卡的初始化，网卡的收发数据)，LwIP 提供统一的接口**, 这样才能把数据从硬件接口到软件内核无缝连接起来.

- 当底层接口函数得到了网络的数据之后， 传入 lwip 内核中去处理
- 同理，LwIP 内核需要发送一个数据包的时候，也需要调用网卡的底层发送函数

重要的属性如下:

```c
struct netif {
    ip_addr_t ip_addr; //网卡的ip地址
    netif_input_fn input; //网卡驱动调用, 将收到的报文传给lwip
    netif_output_fn output;//IP模块调用, 发送报文到网卡
    netif_linkoutput_fn linkoutput;//网卡驱动的发送函数, 从网卡将报文发出去
    netif_status_callback_fn status_callback;//网卡 state up down时调用的cb
    netif_status_callback_fn link_callback;//网卡 link up down时调用的cb
    netif_status_callback_fn remove_callback;//删除网卡时调用的cb
    void* client_data[LWIP_NETIF_CLIENT_...];//dhcp报文数据
};
```

# netif_list

为满足多网卡的需求, lwip 将每个用 netif 描述的网卡连接成一个链表（`netif_list`），该链表就记录每个网卡的 netif 信息,

## netif add

lwip 要管理网卡, 需要将包含网卡信息的 netif 变量添加到`netif_list`上, 并完成网卡初始化.

```c
netifapi_netif_add: //NETCONN API
    //定义api msg, 并填充内容
    NETIFAPI_VAR_DECLARE(msg);
    NETIFAPI_VAR_REF(msg).netif = netif;//网卡变量
    NETIFAPI_VAR_REF(msg).msg.add.init    = init;//指定网卡的初始化函数
    //交给tcpip ghread处理
    err = tcpip_api_call(netifapi_do_netif_add, &API_VAR_REF(msg).call);
        TCPIP_MSG_VAR_REF(msg).type = TCPIP_MSG_API_CALL;
        TCPIP_MSG_VAR_REF(msg).msg.api_call.function = fn;//指定处理函数
        sys_mbox_post(&tcpip_mbox, &TCPIP_MSG_VAR_REF(msg));//发到mbox

//tcpip thread主循环
tcpip_thread:
    while (1)
        TCPIP_MBOX_FETCH(&tcpip_mbox, (void **)&msg);//从mbox获取数据
        tcpip_thread_handle_msg(msg);
            case TCPIP_MSG_API_CALL:
                msg->msg.api_call.function(msg->msg.api_call.arg);//用发消息前指定的函数处理msg

//发消息前指定的处理函数为
netifapi_do_netif_add:
    netif_add( msg->netif, ...);
        netif_set_addr(netif, ipaddr, netmask, gw);//设置网卡的ip, mask和gw
        netif->input = input;//设置input函数
        init(netif);//初始化网卡, 调用函数入参的init函数, 该函数由用户指定
        //遍历已存的所以网卡, 为当前网卡分配唯一标识
        //添加到netif_list
        netif->next = netif_list;
        netif_list = netif;
```

## netif remove

删除网卡需要调用函数`netifapi_netif_remove`

```c
netifapi_netif_remove:
    netifapi_netif_common(n, netif_remove, NULL);
        NETIFAPI_VAR_REF(msg).msg.common.voidfunc = voidfunc;//指定msg处理函数
        err = tcpip_api_call(netifapi_do_netif_common, &API_VAR_REF(msg).call);

netif_remove:
    if (netif_is_up(netif))
        netif_set_down(netif);//关闭网卡
    //判断当前网卡是不是netif_default
    //从netif_list移除当前网卡
    //调用remove_callback
    if (netif->remove_callback)
        netif->remove_callback(netif);
```

# ethernetif.c

**ethernetif.c 文件为底层接口的驱动的模版**，用于为自己的网络设备实现驱动时应参照此模板做修改。
ethernetif.c 文件中的函数通常为与硬件打交道的底层函数，当有数据需要通过网卡接收或者发送数据的时候就会被调用，经过 LwIP 协议栈内部进行处理后，从应用层就能得到数据或者可以发送数据.

<font color='red'>注意, ethernetif.c 文件在 contrib/example 中, 不在 lwip 源代码中, 需要另行下载</font>

主要函数和功能如下:

- ethernetif_init: 管理网卡 netif 的到时候会被调用的函数，如使用 netif_add()添加网卡, 就会调用 ethernetif_init()函数对网卡进行初始化，其实该函数的最终调用的初就是 low_level_init 函数
  - low_level_init: 网卡初始化函数，它主要完成网卡的复位及参数初始化，根据实际的网卡属性进行配置 netif 中与网卡相关的字段，例如网卡的 MAC 地址、长度，最大发送单元等
- ethernetif_input: 调用`low_level_input`从网卡中读取一个数据包，然后交由`netif->input`继续处理. **需要在网卡接收线程或中断函数中主动调用此函数**.
  - low_level_input: 网卡的数据接收函数，该函数会接收一个数据包，并将接收的数据封装成 pbuf 的形式
- low_level_output: 网卡的发送函数，它主要将内核的数据包发送出去，数据包采用 pbuf 数据结构进行描述. **作为`netif->linkoutput使用`, 是发送报文出去的最后一步**.

## ethernetif_init

在调用`netifapi_netif_add`添加网卡时, 一般将此函数作为网卡初始化的函数, 在`netif_add`里被调用.

```c
ethernetif_init:
    //通过 netif 的 state 成员变量将 ethernetif 结构传递给上层
    netif->state = ethernetif;
    //设置网卡name
    //设置output函数, 设置linkoutput函数
    netif->output = etharp_output;
    netif->linkoutput = low_level_output;
    //调用网卡初始化
    low_level_init(netif);
        //每个网卡具体实现各不相同
```
