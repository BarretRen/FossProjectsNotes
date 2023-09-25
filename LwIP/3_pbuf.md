如果按照标准的 TCP/IP 协议栈这种严格的分层思想，在数据传输的时候就需要层层拷贝，因为各层之间的内存都不是共用的, 这样的效率时很慢的。
由于处理器的性能有限， LwIP 并没有采用很明确的分层结构，**LwIP 假设各层之间的资源都是共用的，各层之间的实现方式也是已知的**，这样的处理的方式就无需拷贝，各个层次之间存在交叉存取数据的现象，既节省系统的空间也节省处理的时间，而且更加灵活。

# struct pbuf

pbuf 是描述数据报文的结构， 用于在 lwip 各个模块和各层之间传输报文，统一的结构便于封装和拆解。
基本属性如下:

```c
struct pbuf {
    struct pbuf *next; //可能需要多个pbuf保存一个完整的报文, 所以需要pbuf链表
    void *payload; //指向报文数据区域
    u16_t tot_len;//本pbuf数据长度 + pbuf链表后续所有pbuf的数据长度
    u16_t len;    //本pbuf数据长度
    u8_t type_internal; //pbuf的类型
    LWIP_PBUF_REF_T ref;//本pbuf被引用了多少次, 用于释放时判断?
    u8_t if_idx; //用于收到的报文, 表示属于哪个netif网卡
};
```

## pbuf 类型

上面结构体中有一个属性是 pbuf 的类型, pbuf 共有 4 种类型:

- PBUF_RAM: 空间通过**heap**分配, 从内存中之间 malloc,或从 lwip 管理的 heap 空间 malloc
  ![Alt text](3_pbuf.assets/image.png)
- PBUF_POOL: 空间通过**MEMP_PBUF_POOL 内存池**分配, 从内存池分配适当的内存块个数以满足申请的空间大小
  ![Alt text](3_pbuf.assets/image-1.png)
- PBUF_ROM & PBUF_REF: **只包含 pbuf 结构体, 不包含数据区域**. 空间通过**MEMP_PBUF 内存池**分配
  ![Alt text](3_pbuf.assets/image-2.png)

## pbuf layer

在调用`pbuf_alloc`申请 pbuf 时, 指定不同的协议层次就可以申请出足够的空间, 并且预留出对应的协议 header 部分.
比如下面调用:

```c
p = pbuf_alloc(PBUF_TRANSPORT, 512, PBUF_RAM);
```

实际申请的长度是: `pbuf 结构体长度+传输层 header 长度+ip 层 header 长度+链路层以太网 header 长度+512`

# pbuf 操作函数

- pbuf_alloc: 根据 pbuf type 和 pbuf layer 申请内存
- pbuf_free: 释放 pbuf 内存. 当引用为 0 时释放; **对应 pbuf 链表, 只能传入 header, 不能传入中间节点**
- pbuf_realloc: 释放尾部多余的空间
- pbuf_header: 使 payload 指针指向 layer header 区域
