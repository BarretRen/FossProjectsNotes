# 数据结构

每个任务都有一个 32 位的通知值，在大多数情况下，**任务通知可以替代二值信号量、计数信号量、事件组， 也可以替代长度为 1 的队列**.
按照 FreeRTOS 官方的说法，使用任务通知比通过信号量等 ICP 通信方式解除阻塞的任务要快 45%, 并且更加节省内存.

```c
//task.c中定义, 主要属性有:
typedef struct tskTaskControlBlock
{
    //...
    //task notify相关
    volatile uint32_t ulNotifiedValue[ configTASK_NOTIFICATION_ARRAY_ENTRIES ]; //任务通知值
    volatile uint8_t ucNotifyState[ configTASK_NOTIFICATION_ARRAY_ENTRIES ]; //任务通知状态
    //...
} tskTCB;

typedef tskTCB TCB_t;
```

## 通知状态

- `taskNOT_WAITING_NOTIFICATION`: 任务没有在等待通知
- `taskWAITING_NOTIFICATION`: 任务在等待通知
- `taskNOTIFICATION_RECEIVED`: 任务接收到了通知，也被称为 pending(有数据了，待处理)

## 通知值类型

`ulNotifiedValue`是一个 32 位的数值, 在使用时可以传递多种类型:

- 计数值
- 按 bit 位存取值(类似事件组)
- 任意数值

# 通知的限制

- 只有一个任务接收通知，必须指定接收通知的 task
- 不能再中断中等待通知
- 只有等待通知的任务可以阻塞，如果发送受阻，发送方无法进入阻塞状态等待

# 通知函数接口

## 发送通知

以`xTaskGenericNotify`和`xTaskGenericNotifyFromISR`为基础, 扩展出了如下通知发送函数:

| 任务级通知发送函数         | 中断级通知发送函数                |
| -------------------------- | --------------------------------- |
| xTaskGenericNotify         | xTaskGenericNotifyFromISR         |
| xTaskNotify                | xTaskNotifyFromISR                |
| xTaskNotifyIndexed         | xTaskNotifyIndexedFromISR         |
| xTaskNotifyAndQuery        | xTaskNotifyAndQueryFromISR        |
| xTaskNotifyAndQueryIndexed | xTaskNotifyAndQueryIndexedFromISR |
| xTaskNotifyGive            |                                   |
| xTaskNotifyGiveIndexed     |                                   |

### 通知发送方式

FreeRTOS 提供以下几种方式发送通知给任务, 通过`eNotifyAction`指定:

| eNotifyAction             | 含义                                                 |
| ------------------------- | ---------------------------------------------------- |
| eNoAction                 | 仅更新 state, 不修改 value, 相当于轻量级的二值信号量 |
| eSetBits                  | 设置通知值的一个或者多个位，可以当做事件组来使用     |
| eIncrement                | 增通知值，可以当做计数信号量使用                     |
| eSetValueWithOverwrite    | 不管当前 state, 直接覆盖通知值                       |
| eSetValueWithoutOverwrite | 判断 state, 如果有通知未读，不覆盖通知值             |

### xTaskGenericNotify

```c
xTaskGenericNotify:
    //通过出参返回之前的notify value
    *pulPreviousNotificationValue = pxTCB->ulNotifiedValue[ uxIndexToNotify ];
    //设置notify state为收到通知
    pxTCB->ucNotifyState[ uxIndexToNotify ] = taskNOTIFICATION_RECEIVED;
    //根据action的不同执行不同的操作， 更新notify value
    switch( eAction )
    //如果当前被notify的task正处于阻塞状态，则唤醒
    if( ucOriginalNotifyState == taskWAITING_NOTIFICATION )
        listREMOVE_ITEM( &( pxTCB->xStateListItem ) );//从阻塞列表中删除
        prvAddTaskToReadyList( pxTCB );//加入到ready list
        //如果被通知的任务优先级大于当前任务，则切换任务
        if( pxTCB->uxPriority > pxCurrentTCB->uxPriority )
            taskYIELD_IF_USING_PREEMPTION();
```

## 接收通知

以`ulTaskGenericNotifyTake`和`xTaskGenericNotifyWait`为基础, 扩展出了如下通知发送函数:

| 任务级通知 take 函数    | 任务级通知 wait 函数   |
| ----------------------- | ---------------------- |
| ulTaskGenericNotifyTake | xTaskGenericNotifyWait |
| ulTaskNotifyTake        | xTaskNotifyWait        |
| ulTaskNotifyTakeIndexed | xTaskNotifyWaitIndexed |

### ulTaskGenericNotifyTake

- 任务通知值为 0，对应信号量无效，如果任务设置了阻塞等待，任务被阻塞挂起
- 当其他任务或中断发送了通知值使其不为 0 后，通知变为有效
- 等待通知的任务将获取到通知，并且在退出时候根据参数 xClearCountOnExit 选择清零通知值或者减一
  - 清零：适用于代替二值信号量
  - 减一：适用于代替计数信号量

```c
ulTaskGenericNotifyTake:
    //当前notify value为0, 需要阻塞当前task
    if( pxCurrentTCB->ulNotifiedValue[ uxIndexToWait ] == 0UL )
        pxCurrentTCB->ucNotifyState[ uxIndexToWait ] = taskWAITING_NOTIFICATION;
        //如果指定了阻塞时间, 则加入delay list
        if( xTicksToWait > ( TickType_t ) 0 )
            prvAddCurrentTaskToDelayedList( xTicksToWait, pdTRUE );
            //切换任务
            portYIELD_WITHIN_API();

    //代码走到这里说明其它任务或中断向这个任务发送了通知,或者任务阻塞超时,现在继续处理
    if( ulReturn != 0UL )
        //notify value不为0, 选择清零或者减一
    //更新notify state
    pxCurrentTCB->ucNotifyState[ uxIndexToWait ] = taskNOT_WAITING_NOTIFICATION;
```

### xTaskGenericNotifyWait

`xTaskGenericNotifyWait`是全功能版的等待任务通知，根据用户指定的参数的不同，可以灵活的用于实现轻量级的消息队列、二值信号量、计数信号量和事件组功能，并带有超时等待.

```c
xTaskGenericNotifyWait:
    //当前notify state不是received时, 需要阻塞当前task
    if( pxCurrentTCB->ucNotifyState[ uxIndexToWait ] != taskNOTIFICATION_RECEIVED )
        pxCurrentTCB->ucNotifyState[ uxIndexToWait ] = taskWAITING_NOTIFICATION;
        //如果指定了阻塞时间, 则加入delay list
        if( xTicksToWait > ( TickType_t ) 0 )
            prvAddCurrentTaskToDelayedList( xTicksToWait, pdTRUE );
            //切换任务
            portYIELD_WITHIN_API();

    //代码走到这里说明其它任务或中断向这个任务发送了通知,或者任务阻塞超时,现在继续处理
    *pulNotificationValue = pxCurrentTCB->ulNotifiedValue[ uxIndexToWait ];//返回当前值
    if( pxCurrentTCB->ucNotifyState[ uxIndexToWait ] != taskNOTIFICATION_RECEIVED )
        //notify state不是received, 说明是阻塞超时才走到这里, 返回失败
        xReturn = pdFALSE;
    else
        Return = pdTRUE;//返回成功
    //更新notify state
    pxCurrentTCB->ucNotifyState[ uxIndexToWait ] = taskNOT_WAITING_NOTIFICATION;
```
