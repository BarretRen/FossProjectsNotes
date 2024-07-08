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
