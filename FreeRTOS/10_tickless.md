# tickless 原理

## 低功耗模式

FreeRTOS 无滴答模式的原理是，在 MCU 执行空闲任务时，使 MCU 进入低功耗模式以节省系统功耗。调用中断等待指令(arm 是 WFI, 其他指令集可能命令不同)可使 MCU 进入低功耗模式，而使用中断可唤醒 MCU。

因此，FreeRTOS 无滴答模式的核心思想是：

- 当执行空闲任务时，如果满足满足某些条件, 就使 MCU 进入低功耗模式
  - 调用`vPortSuppressTicksAndSleep`
- 在适当条件下，通过中断或外部事件唤醒 MCU

## 低功耗的持续时间

如果系统是空闲的，则在 IDLE task 中计算下一个用户 task unblock 的时间作为低功耗模式的最长持续时间. **这个时间只是不影响 app task 的理论上限时间, 实际上可能因为外部事件提前唤醒**.

## tick 补偿

FreeRTOS 是使用 Systick 定时器来产生系统滴答节拍并生成中断的，systick 中断也会唤醒 MCU，因此**在进入低功耗模式之前必须禁用系统滴答中断**.
一旦系统滴答节拍停止，在退出低功耗模式后，系统滴答计数器将丢失一些计数值，这是不允许的。针对这种情况，FreeRTOS 也提供了相应的解决方案，即: **使用一个定时器记录系统处于低功耗模式的时间，并在退出低功耗模式后将此时间补偿到系统滴答计数器**.

## 宏开关

需要在 config 头文件中开启如下宏才能使用 tickless:

```c
configUSE_TICKLESS_IDLE //开启tickless功能
configEXPECTED_IDLE_TIME_BEFORE_SLEEP //持续时间大于多少才允许进入低功耗模式
portSUPPRESS_TICKS_AND_SLEEP //进入低功耗需要的操作函数
```

# 代码流程

## idle task

```c
static portTASK_FUNCTION( prvIdleTask, pvParameters )
    for( ; ; )
        #if ( configUSE_TICKLESS_IDLE != 0 )
            xExpectedIdleTime = prvGetExpectedIdleTime();//获取最大持续时间
                if( xExpectedIdleTime >= configEXPECTED_IDLE_TIME_BEFORE_SLEEP )
                    //大于预设时间, 则可以进入低功耗模式
                    vTaskSuspendAll();
                    //重新计算一遍最大持续时间, 避免刚才过程中发送变化
                    if( xExpectedIdleTime >= configEXPECTED_IDLE_TIME_BEFORE_SLEEP )
                        portSUPPRESS_TICKS_AND_SLEEP( xExpectedIdleTime );
                            //进入低功耗模式, 不同平台自己实现具体步骤
                    xTaskResumeAll();
```

## portSUPPRESS_TICKS_AND_SLEEP

`portSUPPRESS_TICKS_AND_SLEEP`每个平台具体的步骤不一样, 不过基本的操作流程是统一的, 举例如下:

```c
portSUPPRESS_TICKS_AND_SLEEP:
    //停止中断接收
    //根据最大持续时间设置timer, 到指定时间唤醒
    //调用指令让mcu进入低功耗模式, 比如WFI

    //如果mcu恢复运行, 将从这里继续执行
    //停止上面启动的timer
    //恢复中断处理
    //计算需要补偿的tick数
    //调用vTaskStepTick补偿freeRTOS中缺失的tick计数
```
