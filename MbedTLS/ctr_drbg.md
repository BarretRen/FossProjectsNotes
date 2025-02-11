在 MbedTLs 库中，ctr_drbg（基于 CTR 模式的确定性随机比特生成器）是一个伪随机数生成器（PRNG），它根据 NIST SP 800-90A 标准实现。ctr_drbg 需要定期重新种子（reseed）以保持其安全性，确保生成的随机数具有足够的不可预测性。

# 初始化

在使用 ctr_drbg 之前，首先需要对其进行初始化。
初始化时，需要提供一个熵源（entropy source）和一个可选的个性化字符串（personalization string）

- 熵源通常是一个硬件随机数生成器或操作系统提供的随机源。MbedTLS 提供了 `mbedtls_entropy_func` 函数来从熵池中获取熵数据

```c
mbedtls_ctr_drbg_init(&ctr_drbg);
mbedtls_ctr_drbg_seed(&ctr_drbg, mbedtls_entropy_func, &entropy, (const unsigned char *) pers, pers_len);
```

# reseed 过程

ctr_drbg 会在以下情况下触发重新种子：

- 生成的随机数达到一定的数量（`MBEDTLS_CTR_DRBG_RESEED_INTERVAL`定义）。
- 显式调用 mbedtls_ctr_drbg_reseed 函数

在生成随机数时，ctr_drbg 中`mbedtls_ctr_drbg_random`函数会检查是否需要重新种子。如果需要，它会调用 mbedtls_ctr_drbg_reseed 函数

```c
mbedtls_ctr_drbg_random:
    ret = mbedtls_ctr_drbg_random_with_add( ctx, output, output_len, NULL, 0 );
        if( ctx->reseed_counter > ctx->reseed_interval || ctx->prediction_resistance )
            ret = mbedtls_ctr_drbg_reseed( ctx, additional, add_len ));
```

当需要重新种子时，ctr_drbg 会从熵源获取新的熵数据，并将其与当前的内部状态混合，以生成新的种子。

# 示例

```c
#include "mbedtls/ctr_drbg.h"
#include "mbedtls/entropy.h"

int main() {
    mbedtls_ctr_drbg_context ctr_drbg;
    mbedtls_entropy_context entropy;
    unsigned char output[16];
    const char *pers = "my_app";

    // 初始化
    mbedtls_ctr_drbg_init(&ctr_drbg);
    mbedtls_entropy_init(&entropy);

    // 种子
    mbedtls_ctr_drbg_seed(&ctr_drbg, mbedtls_entropy_func, &entropy, (const unsigned char *) pers, strlen(pers));

    // 生成随机数
    mbedtls_ctr_drbg_random(&ctr_drbg, output, sizeof(output));

    // 显式重新种子
    mbedtls_ctr_drbg_reseed(&ctr_drbg, NULL, 0);

    // 清理
    mbedtls_ctr_drbg_free(&ctr_drbg);
    mbedtls_entropy_free(&entropy);

    return 0;
}
```
