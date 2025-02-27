# target_config.h 主要配置项

## System clock module configuration

|                                  |                 |                                                           |
| -------------------------------- | --------------- | --------------------------------------------------------- |
| OS_SYS_CLOCK                     | SystemCoreClock | 系统时钟                                                  |
| LOSCFG_BASE_CORE_TICK_PER_SECOND | 1000            | 系统 1 秒中断多少次                                       |
| LOSCFG_BASE_CORE_TICK_HW_TIME    | NO              | 使用专门的定时器作为系统滴答时钟, 默认使用`OsTickHandler` |
| LOSCFG_KERNEL_TICKLESS           | NO              | 配置内核无滴答定时器                                      |

## Hardware interrupt module configuration

|                           |     |                      |
| ------------------------- | --- | -------------------- |
| LOSCFG_PLATFORM_HWI       | NO  | 使用 LiteOS 接管中断 |
| LOSCFG_PLATFORM_HWI_LIMIT | 96  | 配置最大中断数       |

## Task module configuration

|                                         |        |                                    |
| --------------------------------------- | ------ | ---------------------------------- |
| LOSCFG_BASE_CORE_TSK_DEFAULT_PRIO       | 10     | 创建任务时，默认的中断优先级       |
| LOSCFG_BASE_CORE_TSK_LIMIT              | 15     | 最大任务数量                       |
| LOSCFG_BASE_CORE_TSK_IDLE_STACK_SIZE    | 0x500U | 空闲任务栈大小                     |
| LOSCFG_BASE_CORE_TSK_DEFAULT_STACK_SIZE | 0x2D0U | 默认任务栈大小                     |
| LOSCFG_BASE_CORE_TSK_MIN_STACK_SIZE     | 0x130U | 任务最小栈大小                     |
| LOSCFG_BASE_CORE_TIMESLICE              | YES    | 是否使用时间片                     |
| LOSCFG_BASE_CORE_TIMESLICE_TIMEOUT      | 10     | 具有相同优先级的任务的最长执行时间 |
| LOSCFG_BASE_CORE_TSK_MONITOR            | YES    | 任务栈监控模块定制的配置项         |
| LOSCFG_BASE_CORE_EXC_TSK_SWITCH         | YES    | 任务执行过滤器钩子函数的配置项     |
| OS_INCLUDE_PERF                         | YES    | 性能监视器单元的配置项             |
| LOS_TASK_PRIORITY_HIGHEST               | 0      | 任务最高优先级                     |
| LOS_TASK_PRIORITY_LOWEST                | 31     | 任务最低优先级                     |

## Semaphore module configuration

|                           |     |                |
| ------------------------- | --- | -------------- |
| LOSCFG_BASE_IPC_SEM       | YES | 是否使用信号量 |
| LOSCFG_BASE_IPC_SEM_LIMIT | 20  | 最大信号量个数 |

## Mutex module configuration

|                           |     |                |
| ------------------------- | --- | -------------- |
| LOSCFG_BASE_IPC_MUX       | YES | 是否使用互斥量 |
| LOSCFG_BASE_IPC_MUX_LIMIT | 10  | 最大互斥量个数 |

## Queue module configuration

|                             |     |                  |
| --------------------------- | --- | ---------------- |
| LOSCFG_BASE_IPC_QUEUE       | YES | 是否使用消息队列 |
| LOSCFG_BASE_IPC_QUEUE_LIMIT | 15  | 最大消息队列个数 |

## Software timer module configuration

|                                       |        |                              |
| ------------------------------------- | ------ | ---------------------------- |
| LOSCFG_BASE_CORE_SWTMR                | YES    | 是否时间软件定时器           |
| LOSCFG_BASE_CORE_TSK_SWTMR_STACK_SIZE | 0x2D0U | 软件定时任务栈大小           |
| LOSCFG_BASE_CORE_SWTMR_ALIGN          | YES    | 软件定时器对齐               |
| LOSCFG_BASE_CORE_SWTMR_LIMIT          | 16     | 软件定时器最大数量           |
| OS_SWTMR_MAX_TIMERID                  | 65520  | 定时器最大 id                |
| OS_SWTMR_HANDLE_QUEUE_SIZE            | 16     | 软件定时器队列大小           |
| LOS_COMMON_DIVISOR                    | 10     | 软件定时器多重对齐的最小除数 |

## Memory module configuration

|                        |                                                       |                                   |
| ---------------------- | ----------------------------------------------------- | --------------------------------- |
| OS_SYS_MEM_ADDR        | LOS_HEAP_MEM_BEGIN                                    | 系统动态内存池起始地址            |
| OS_SYS_MEM_SIZE        |                                                       | 系统动态内存池大小                |
| LOSCFG_MEM_MUL_POOL    | YES                                                   | 使用多数量内存池                  |
| OS_SYS_MEM_NUM         | 20                                                    | 内存块数量                        |
