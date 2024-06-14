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

触发`The remain empty sector is 1, GC threshold is 1`时会进行 gc, 擦除保留 sector 之外的所以 sector 并把保存的 key 移动到第一个 sector 上.
