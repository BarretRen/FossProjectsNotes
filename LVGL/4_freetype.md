FreeType 是一个免费、开源、可移植且高质量的字体引擎，它有以下优点：

1. 支持多种字体格式文件，并提供了统一的访问接口；
1. 支持单色位图、反走样位图渲染，这使字体显示质量达到 Mac 的水平；
1. 采用面向对象思想设计，用户可以灵活的根据需要裁剪。

LVGL 提供了 freetype 相关的接口函数, 需要在`lv_conf.h`中打开`LV_USE_FREETYPE`是能这些接口, **并保证在编译时同 freetype 库一同编译链接**.

# LVGL 中使用 freetype 示例

## 初始化

```c
//在lv_vendor_start调用之前, 先完成字体的加载
ttf_init:
    //加载字体文件到psram中, psram保证渲染效率
    ret = _load_font_to_psram("/font/simhei_new.ttf", &g_PingFang_map, &g_PingFang_map_len);
        file_content = psram_malloc(file_len);//申请psram内存
        fd = open(font_name, O_RDONLY);
        read(fd, file_content, file_len);//将文件内容写入psram中
        close(fd);
    //填充lv_ft_info_t并进行初始化
    ft_info.name = "/font/simhei_new.ttf";
    ft_info.mem = g_PingFang_map;
    ft_info.mem_size = g_PingFang_map_len;
    lv_ft_font_init(&ft_info);//调用lvgl的font初始化函数
        return lv_ft_font_init_cache(info);
            //填充lv_font_fmt_ft_dsc_t
            dsc->mem = info->mem;
            dsc->mem_size = info->mem_size;
            //调用freetype函数
            //返回dec->font给lvgl
            info->font = font;
```

## 在 lvgl 中使用

```c
//在 lvgl 要显示文字时, 设置 style text font 为上面返回的 font 即可:
static lv_style_t style;
lv_style_init(&style);
lv_style_set_text_font(&style, LV_STATE_DEFAULT, ft_info.font);

/*Create a label with the new style*/
lv_obj_t * label = lv_label_create(lv_scr_act(), NULL);
lv_obj_add_style(label, LV_LABEL_PART_MAIN, &style);//方式1: 添加style
lv_label_set_text(label, "Hello world");
lv_obj_align(label, NULL, LV_ALIGN_IN_TOP_LEFT, 0, 0);

//方式2: 不使用lv_style_t, 直接设置label的text font属性
lv_obj_set_style_text_font(label, ft_info.font, LV_PART_MAIN | LV_STATE_DEFAULT);
```

# 字体库裁剪

ttf 字体库比较大, 会占用很大的内存空间, 因此可以对字体库进行裁剪, 删除不需要的字以减小体积.

```bash
pip install fonttools
# 裁剪成只包含在text.txt文件中的字符的字体
pyftsubset Input.ttf --text-file=text.txt  --output-file=Output.ttf

# 保留指定unicodes范围的字体
pyftsubset Input.ttf --output-file=Output.ttf --unicodes=U+0000-007F
```
