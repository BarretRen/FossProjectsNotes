# 常见问题

## 如何检查 mbedtls 返回值含义

从 log 中获取打印的返回值，根据`mbedtls_high_level_strerr`和`mbedtls_low_level_strerr`来细分错误信息

## mbedtls_ssl_write 导致 stack overflow

工作遇到的，一个 8192 大小的线程调用`mbedtls_ssl_write`发送 tls 数据包, 正常发送 11 个小时之后出现了栈溢出. 很奇怪的是, `mbedtls_ssl_write`的执行流程是一样的, 怎么可能是前面正常发送, 11 个小时之后就出问题. 如果是栈空间不足, 应该一开始就不足才对.

1. 打印了整个栈的内容, 确实是栈溢出了, 并且覆盖了别的线程的栈空间
1. 从前面正常的调用栈流程判断, 怀疑是 mbedtls 的随机生成器 ctr_drbg 要重新生成随机数种子, 导致走向了不同的代码分支

```c
mbedtls_ssl_encrypt_buf:
    ret = f_rng( p_rng, transform->iv_enc, transform->ivlen ); //实际调用mbedtls_ctr_drbg_random

mbedtls_ctr_drbg_random:
    ret = mbedtls_ctr_drbg_random_with_add( ctx, output, output_len, NULL, 0 );
        if( ctx->reseed_counter > ctx->reseed_interval || ctx->prediction_resistance )
        {
            if( ( ret = mbedtls_ctr_drbg_reseed( ctx, additional, add_len ) ) != 0 )
            {
                return( ret );
            }
            add_len = 0;
        }

//ctx->reseed_interval默认值在这里初始化的
mbedtls_ctr_drbg_init:
    ctx->reseed_counter = -1;
    ctx->reseed_interval = MBEDTLS_CTR_DRBG_RESEED_INTERVAL; //10000
```
