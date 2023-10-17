信号量一般用于进行**共享资源管理和任务同步**, <font color='red'>FreeRTOS 中信号量是借助消息队列实现的</font>, 分为如下几类

- 二值信号量
- 计数型信号量
- 互斥信号量(也叫互斥锁)
- 递归互斥信号量(也叫递归锁)

和队列一样, 信号量 API 也支持设置阻塞时间, \*\*当多个任务同时阻塞在同一个信号量上时, 优先级最高的任务优先获得信号量.

# 信号量创建

## 二值信号量

二值信号量本质是一个**只有一个队列项的队列, 且队列项长度为 0**, 队列要么满要么空, 不关系实际保存的消息. 利用这个机制可以实现任务和中断之间的同步.

| 函数                         | 作用                                                 |
| ---------------------------- | ---------------------------------------------------- |
| vSemaphoreCreateBinary       | 动态方法创建二值信号量, 老 API, 建后不需要释放       |
| xSemaphoreCreateBinary       | 动态方法创建二值信号量, 新 API, 创建后需要先释放一下 |
| xSemaphoreCreateBinaryStatic | 静态方法创建二值信号量                               |

## 计数型信号量

计数型信号量是一个**队列项长度为 0, 但有对各队列项的队列**, 信号量的值代表当前自由的可用数量, 数量用尽就需要等待.

| 函数                           | 作用                     |
| ------------------------------ | ------------------------ |
| xSemaphoreCreateCounting       | 动态方法创建计数型信号量 |
| xSemaphoreCreateCountingStatic | 静态方法创建计数型信号量 |

## 互斥信号量

互斥信号量就是一个**拥有优先级继承的二值信号量**, 即当一个低优先级的任务正在使用信号量, 高优先级的任务阻塞时**会将低优先级的任务提升到与自己相同的优先级**, 以此来避免优先级反转.
<font color='red'>互斥信号量不能用于中断处理函数中.</font>

| 函数                        | 作用                   |
| --------------------------- | ---------------------- |
| xSemaphoreCreateMutex       | 动态方法创建互斥信号量 |
| xSemaphoreCreateMutexStatic | 静态方法创建互斥信号量 |

在互斥信号量的释放和获取时, 涉及到优先级继承的处理, 会比上面两种信号量的处理复杂一点.

# 信号量获取和释放

| 函数                  | 作用                                           |
| --------------------- | ---------------------------------------------- |
| xSemaphoreGive        | 释放信号量, 计数型信号量和互斥信号量           |
| xSemaphoreGiveFromISR | 中断函数中释放信号量, 计数型信号量和互斥信号量 |
| xSemaphoreTake        | 释放信号量, 计数型信号量和互斥信号量           |
| xSemaphoreTakeFromISR | 中断函数中释放信号量, 计数型信号量和互斥信号量 |

## take

```c
xSemaphoreTake:
    xQueueSemaphoreTake( ( xSemaphore ),( xBlockTime ) );
        if( uxSemaphoreCount > ( UBaseType_t ) 0 )//判断信号在是否可获取
            pxQueue->uxMessagesWaiting = uxSemaphoreCount - ( UBaseType_t ) 1;//信号量计数减一
            if( pxQueue->uxQueueType == queueQUEUE_IS_MUTEX ) //互斥信号量
                pxQueue->u.xSemaphore.xMutexHolder = pvTaskIncrementMutexHeldCount();//设置拥有者为当前任务
            //判断是否有其他任务等待释放信号量, 进行任务调度
        else //信号量为空
            if( xTicksToWait == ( TickType_t ) 0 )
                return errQUEUE_EMPTY;//阻塞时间为0, 返回

        //如果队列还是空的, 且阻塞时间不为0, 检查是否超时
        if( xTaskCheckForTimeOut( &xTimeOut, &xTicksToWait ) == pdFALSE )
            if( prvIsQueueEmpty( pxQueue ) != pdFALSE )
                if( pxQueue->uxQueueType == queueQUEUE_IS_MUTEX )
                    //互斥量处理优先级继承问题
                    xInheritanceOccurred = xTaskPriorityInherit( pxQueue->u.xSemaphore.xMutexHolder );
                    vTaskPlaceOnEventList( &( pxQueue->xTasksWaitingToReceive ), xTicksToWait);
                        //添加到等待接收链表
                        //将当前任务放入delay list
        else
            if( prvIsQueueEmpty( pxQueue ) != pdFALSE )
                if( xInheritanceOccurred != pdFALSE )
                    //处理优先级变化
                    TaskPriorityDisinheritAfterTimeout( pxQueue->u.xSemaphore.xMutexHolder, uxHighestWaitingPriority );
                return errQUEUE_EMPTY;

xTaskPriorityInherit:
    if( pxMutexHolder != NULL )
        //用于互斥量的当前任务优先级比当前任务低, 那就需要切换
        if( pxMutexHolderTCB->uxPriority < pxCurrentTCB->uxPriority )
            //更新拥有者任务的当前优先级
            //添加到ready list
            xReturn = pdTRUE;
        else if( pxMutexHolderTCB->uxBasePriority < pxCurrentTCB->uxPriority )
            //用于互斥量的基础任务优先级比当前任务低, 返回true
            xReturn = pdTRUE;
```

## give

```c
//释放信号量
xSemaphoreGive:
    xQueueGenericSend( ( QueueHandle_t ) ( xSemaphore), NULL, semGIVE_BLOCK_TIME, queueSEND_TO_BACK );
        if( ( pxQueue->uxMessagesWaiting < pxQueue->uxLength ) || ( xCopyPosition == queueOVERWRITE )
            //没有消息要复制, 对于信号量来说只是处理计数和优先级继承
            xYieldRequired = prvCopyDataToQueue( pxQueue, pvItemToQueue, xCopyPosition );
                if( pxQueue->uxItemSize == ( UBaseType_t ) 0 )//队列项长度为0, 即信号量类型的队列
                    if( pxQueue->uxQueueType == queueQUEUE_IS_MUTEX )//互斥信号量
                        xReturn = xTaskPriorityDisinherit( pxQueue->u.xSemaphore.xMutexHolder );
                            //处理优先级继承问题
                    //其他类型信号量不需要处理什么
                pxQueue->uxMessagesWaiting = uxMessagesWaiting + ( UBaseType_t ) 1;//计数加1

            if( xYieldRequired != pdFALSE ) //返回值为true, 手动进行任务调度
                queueYIELD_IF_USING_PREEMPTION();
        //后续处理和队列发送消息一样

//优先级继承
xTaskPriorityDisinherit:
    //互斥量肯定已经被当前运行的任务获取, 所以holder不为空
    if( pxMutexHolder != NULL )
        ( pxTCB->uxMutexesHeld )--;//任务拥有的互斥量数减一
        //判断释放存在优先级继承, 如果有, 则任务的当前优先级必然不等于基础优先级
        if( pxTCB->uxPriority != pxTCB->uxBasePriority )
            //只有当前要释放的是最有一个互斥量, 才能处理优先级继承
            if( pxTCB->uxMutexesHeld == ( UBaseType_t ) 0 )
                //将任务从ready list中删除
                //修改当前优先级为基础优先级
                //重新将任务添加到ready list
                //返回true, 表示需要任务调度
```

# 递归互斥信号量

递归互斥信号量是特殊的互斥量, **已经获得互斥量的任务何以再次获取, 但要保证获取和释放的次数要一致**.
<font color='red'>递归互斥信号量也有优先级继承机制, 所以不能用于中断处理函数中.</font>

| 函数                                 | 作用                       |
| ------------------------------------ | -------------------------- |
| xSemaphoreCreateRecursiveMutex       | 动态方法创建递归互斥信号量 |
| xSemaphoreCreateRecursiveMutexStatic | 动态方法创建递归互斥信号量 |
| xSemaphoreTakeRecursive              | 获取递归信号量             |
| xSemaphoreGiveRecursive              | 释放递归信号量             |
