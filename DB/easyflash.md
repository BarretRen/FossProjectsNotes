# easyflash 写入次数

每次调用`set_env`会写入多次, 从 log 看分别是:

```log
alloc end, start_time=8882ms, end_time=8888ms, time_cost=6ms  ==>new_env_by_kv
ef_port_write, addr=16649596, size=4  ==>del old env, ENV_PRE_DELETE
ef_port_write, addr=16649648, size=4  ==>write status
ef_port_write, addr=16649668, size=20 ==>write header
ef_port_write, addr=16649688, size=4  ==>write key
ef_port_write, addr=16649692, size=16 ==>write value
ef_port_write, addr=16649652, size=4  ==>write status
ef_port_write, addr=16649600, size=4  ==>del old env, ENV_DELETED
```

# easyflash 擦除次数

触发`The remain empty sector is 1, GC threshold is 1`时会进行 gc, 擦除保留 sector 之外的所有 sector 并把保存的 key 移动到第一个 sector 上.

# GC 机制

## 初始化时

初始化时会 load env，其中会检查是否需要进行 GC 处理

```c
ef_env_init:
    env_start_addr = EF_START_ADDR;
    result = ef_load_env();
        //检查sector header
        sector_iterator(&sector, SECTOR_STORE_UNUSED, &check_failed_count, NULL, check_sec_hdr_cb, false);
            //调用check_sec_hdr_cb
        //如果所有sector都损坏了, 重置
        if (check_failed_count == SECTOR_NUM)
            ef_env_set_default();
        //检查是否有脏数据, 是否需要GC
        sector_iterator(&sector, SECTOR_STORE_UNUSED, NULL, NULL, check_and_recovery_gc_cb, false);
            //调用check_and_recovery_gc_cb

//检查有无损坏的sector,并重新格式化, 返回有问题的个数
check_sec_hdr_cb:
    if (!sector->check_ok)
        (*failed_count) ++;
        format_sector(sector->addr, SECTOR_NOT_COMBINED);

check_and_recovery_gc_cb:
    if (sector->check_ok && sector->status.dirty == SECTOR_DIRTY_GC)
        //有脏数据, 执行GC操作
        gc_collect();
            //检查剩余sector小于预设值的个数,就执行GC
            if (empty_sec <= EF_GC_EMPTY_SEC_THRESHOLD)
                sector_iterator(&sector, SECTOR_STORE_UNUSED, NULL, NULL, do_gc, false);
```
