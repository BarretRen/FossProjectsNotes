# FreeRTOSConfig.h

在使用 freeRTOS 时需要根据需要自定义配置(不同的应用场景， 不同的硬件都有区别)， **freeRTOS 的配置文件为`FreeRTOSConfig.h`, 此文件负责 os 的裁剪和配置**.

## `INCLUDE_`宏

在配置文件中使用`INCLUDE_`前缀的宏可以**配置 freeRTOS 中的可选 API 函数**, 通过条件编译的方式步编译某些代码, 节省空间.
所有的宏都可以在 `include/freeRTOS.h` 中找到, 然后在配置文件中设置值. 下面常见的 API 开关:

```c
//FreeRTOSConfig.h
#define INCLUDE_vTaskPrioritySet            1
#define INCLUDE_uxTaskPriorityGet           1
#define INCLUDE_vTaskDelete                 1
#define INCLUDE_vTaskCleanUpResources       0
#define INCLUDE_vTaskSuspend                1
#define INCLUDE_vTaskDelayUntil             1
#define INCLUDE_vTaskDelay                  1
#define INCLUDE_xTaskAbortDelay             1
#define INCLUDE_xTaskGetCurrentTaskHandle   1
#define INCLUDE_xSemaphoreGetMutexHolder    1
```

## `config`宏

`config`前缀的宏用于分割代码功能, 开启和关闭宏会影响代码的执行流程. 同样的, 这些宏也可以在 `include/freeRTOS.h` 中找到.
常见的有:

```c
//设置cpu频率和tick频率
#define configCPU_CLOCK_HZ    ( ( unsigned long ) 120000000 )
#define configTICK_RATE_HZ    ( ( TickType_t ) 500 )
//使用timer, 设置timer task优先级
#define configUSE_TIMERS      ( 1 )
#define configTIMER_TASK_PRIORITY                 ( 2 )
//堆栈溢出检测, 出现溢出会调用回调函数
#define configCHECK_FOR_STACK_OVERFLOW            2
//时间统计功能
#define configGENERATE_RUN_TIME_STATS             0
//设置与idle task同优先级的用户task的行为
#define configIDLE_SHOULD_YIELD                   1
//task的优先级数量, 值越大优先级越高
#define configMAX_PRIORITIES                      ( 10 )
//task的最小堆栈大小
#define configMINIMAL_STACK_SIZE                  ( ( unsigned short ) (512/2) )
//设置动态内存申请的堆大小
#define configTOTAL_HEAP_SIZE                     ( ( size_t ) ( 80 * 1024 ) )
//是否开启协程支持, 功能有限建议关闭
#define configUSE_CO_ROUTINES                     0
//使能idle task的回调函数
#define configUSE_IDLE_HOOK                       1
//使能抢占式调度器
#define configUSE_PREEMPTION                      1
```

# portmacro.h

`portmacro.h`中定义了 freeRTOS 内部使用的数据类型重定义, 和硬件操作相关的宏和函数, 同时也声明`port.c`中实现的硬件操作的函数.
比如我们需要设置临界区保护的时候, 就需要开关硬件中断, 而相关的开关函数需要在上述两个文件中定义和实现:

```c
//以源码自带的示例为例:
//portable/RVDS/ARM_CM4_MPU/portmacro.h, 定义了开关中断的宏
#define portDISABLE_INTERRUPTS()                  vPortRaiseBASEPRI()
#define portENABLE_INTERRUPTS()                   vPortSetBASEPRI( 0 )

//上面宏指定的函数在port.c或portmacro.h中实现
vPortSetBASEPRI:
    __asm
    {
        msr basepri, ulBASEPRI
    }

vPortClearInterruptMask:
    __asm
    {
        msr basepri, ulNewBASEPRI
        dsb
        isb
    }
```
