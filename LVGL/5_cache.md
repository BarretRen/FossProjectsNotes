# img cache

## init

对应宏配置为`LV_IMG_CACHE_DEF_SIZE`.

`lv_init`中会对 img cache 进行设置, 从内存申请内存

```c
lv_init:
    lv_img_cache_set_size(LV_IMG_CACHE_DEF_SIZE);
        //申请内存, 一个img cache entry大小是44
        LV_GC_ROOT(_lv_img_cache_array) = lv_mem_alloc(sizeof(_lv_img_cache_entry_t) * new_entry_cnt);
        //内存区域置0
        lv_memset_00(LV_GC_ROOT(_lv_img_cache_array), entry_cnt * sizeof(_lv_img_cache_entry_t));
```

## 使用

```c
lv_draw_img:
    if(draw_ctx->draw_img)
        res = draw_ctx->draw_img(draw_ctx, dsc, coords, src);
    else
        res = decode_and_draw(draw_ctx, dsc, coords, src);
            _lv_img_cache_entry_t * cdsc = _lv_img_cache_open(src, draw_dsc->recolor, draw_dsc->frame_id);
    //开始绘图
    //函数结束, 清理资源
    draw_cleanup(cdsc);
        #if LV_IMG_CACHE_DEF_SIZE == 0
            lv_img_decoder_close(&cache->dec_dsc);//清理内存
        #else
            LV_UNUSED(cache);
        #endif
    return LV_RES_OK;

_lv_img_cache_open:
    #if LV_IMG_CACHE_DEF_SIZE
        //根据图片的src路径查找img cache中是否存在此图片
        //如果找到了cache, 直接返回
        if(cached_src) return cached_src;
        //如果没有找到, 找到一个cache entry用于保存即将打开的图片
    #else
        //没有启用cache, 直接引用全局变量
        cached_src = &LV_GC_ROOT(_lv_img_cache_single);
    #endif

    //打开图片并解码
    lv_res_t open_res = lv_img_decoder_open(&cached_src->dec_dsc, src, color, frame_id);
        _LV_LL_READ(&LV_GC_ROOT(_lv_img_decoder_ll), decoder) //遍历解码器, 调用图片对应解码器的函数
            res = decoder->info_cb(decoder, src, &dsc->header);
            res = decoder->open_cb(decoder, dsc);
            if(res == LV_RES_OK) return res; //打开图片成功, 返回
    //返回
    return cached_src;
```

# LVGL9 img cache

## 配置项

- `LV_CACHE_DEF_SIZE`: 缓存图片解码数据
- `LV_IMAGE_HEADER_CACHE_DEF_CNT`: 缓存图片的 header 信息

## 保存缓存

LVGL9 img cache 结构发生了变化, 需要在解码后主动添加到 cache 中.如果当前设置的大小不足, 会尝试释放当前没被使用的缓存:

```c
//设置用于搜索的key和size
lv_image_cache_data_t search_key;
search_key.src_type = dsc->src_type;
search_key.src = dsc->src;
search_key.slot.size = decoded->data_size;
//添加到缓存
lv_cache_entry_t * entry = lv_image_decoder_add_to_cache(decoder, &search_key, decoded, NULL);
    //获取新的缓存
    lv_cache_entry_t * cache_entry = lv_cache_add(img_cache_p, search_key, NULL);
        lv_cache_entry_t * entry = cache_add_internal_no_lock(cache, key, user_data);
            //判断缓存释放足够
            lv_cache_reserve_cond_res_t reserve_cond_res = cache->clz->reserve_cond_cb(cache, key, 0, user_data);
            //如果直接超过设置的最大值, 返回错误
            if(reserve_cond_res == LV_CACHE_RESERVE_COND_TOO_LARGE)
            //如果有已经占用的缓存, 尝试释放不被使用的
            cache_evict_one_internal_no_lock(cache, user_data);
                //查找引用计数为0的缓存, 释放
                lv_cache_entry_t * victim = cache->clz->get_victim_cb(cache, user_data);
                cache->clz->remove_cb(cache, victim, user_data);
                cache->ops.free_cb(lv_cache_entry_get_data(victim), user_data);
                lv_cache_entry_delete(victim);
            //添加新的缓存
            lv_cache_entry_t * entry = cache->clz->add_cb(cache, key, user_data);
        if(entry != NULL)
            lv_cache_entry_acquire_data(entry);//增加引用计数
    //设置缓存数据
    cached_data = lv_cache_entry_get_data(cache_entry);
    cached_data->decoded = decoded;//解码后的数据还是解码时动态申请的, 缓存实际只是用一个cache_entry指向对应的位置
//返回的entry不为null, 表示添加成功
```

## 查找缓存

在`lv_image_decoder_open`中会首先查找缓存, 根据图片的 src 路径和 src_type, 查找不到再调用`decoder_open`进行解码:

```c
lv_image_decoder_open:
    if(lv_image_cache_is_enabled())
        dsc->cache = img_cache_p;//指向全局的图片缓存
        try_cache(dsc);
            //组建key开始查找
            search_key.src_type = dsc->src_type;
            search_key.src = dsc->src;
            lv_cache_entry_t * entry = lv_cache_acquire(cache, &search_key, NULL);
            //如果找到, 获取解码数据
            if(entry)
                dsc->decoded = cached_data->decoded;
```

## 删除缓存

调用`lv_image_cache_drop`直接释放, 或者设置为 invalid, 等待调用`lv_cache_release`释放

```c
lv_image_cache_drop:
    lv_image_header_cache_drop(src);//释放header缓存
    lv_cache_drop(img_cache_p, &search_key, NULL);//释放解码数据
        cache_drop_internal_no_lock(cache, key, user_data);
            if(lv_cache_entry_get_ref(entry) == 0)
                //当前引用计数为0, 直接可以释放
            else
                //设置为invalid
                lv_cache_entry_set_invalid(entry, true);
```
