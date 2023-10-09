# 开关中断函数

开关中断的函数在 porting 里也举例了, 因为和硬件强相关, 所以定义在`portmacro.h`中:

```c
//以portable/RVDS/ARM_CA9为例
#define portDISABLE_INTERRUPTS()                  vPortRaiseBASEPRI()
#define portENABLE_INTERRUPTS()                   vPortSetBASEPRI( 0 )
```

# 临界区保护函数

临界区是指**那些必须完整运行, 不能被打断的代码段**, 比如外设的初始化(需要严格的时序, 不能打断).

临界区保护的实质是开关中断, FreeRTOS 有相应的临界区保护函数, **临界区保护函数在 freeRTOS 内部被频繁调用, 所以在移植时需要定义好其内部逻辑**.

- 调用上面的中断开关函数
- 记录临界区嵌套次数, 嵌套次数为 0 时才重新打开中断

<font color='red'>临界区函数在`task.h`中通过宏定义, 实际的调用函数需要在`portmacro.h`中指定.</font>

## 任务级临界区保护

以下两个是任务级临界区保护的进入和退出函数

```c
#define taskENTER_CRITICAL()    portENTER_CRITICAL()
#define taskEXIT_CRITICAL()     portEXIT_CRITICAL()
```

## 中断级临界区保护

以下两个是中断级临界区保护的进入和退出函数, **用于中断处理函数中, 且中断的优先级低于 configMAX_SYSCALL_INTERRUPT_PRIORITY**.

```c
#define taskENTER_CRITICAL_FROM_ISR()      portSET_INTERRUPT_MASK_FROM_ISR()
#define taskEXIT_CRITICAL_FROM_ISR( x )    portCLEAR_INTERRUPT_MASK_FROM_ISR( x )
```
