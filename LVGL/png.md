解码 PNG 图片就是把一张图片从二进制数据转成包含像素数据的 `ImageData`。

图片的二进制数据可以从 `<canvas>`，`<img>`，Object URLs，Image URLs，`Blob` 对象上获取到。参见[浏览器图像转换手册](https://vivaxyblog.github.io/2019/11/08/comprehensive-image-processing-on-browsers-cn.html)。

`ImageData` 是一个包括了像素数据、图片宽高数据的对象。

# 示例图片

这是一张我们接下去要解码的图片，放大了展示给大家看下

![Alt text](png.assets/image.png)

我们先从浏览器的 `<input>` 标签上读取到 `Blob` 对象，然后拿到这张图片的二进制数据。

```html
<input type="file" />
<script>
  const input = document.querySelector("input");
  input.addEventListener("change", async function (e) {
    const [file] = e.target.files;
    const arrayBuffer = await file.arrayBuffer();
    console.log("arrayBuffer", arrayBuffer);
    // TODO: Let's decode arrayBuffer
    const imageData = decode(arrayBuffer);
    console.log("imageData", imageData);
  });
</script>
```

得到的 `arrayBuffer` 如下：

<style>
table {
  font-size: 12px;
}
table tbody tr td {
  padding: .6rem .4rem;
}
</style>

|           | 0 ~ 3             | 4 ~ 7                | 8 ~ 11            | 12 ~ 15           |
| --------- | ----------------- | -------------------- | ----------------- | ----------------- |
| 0 ~ 15    | `137, 80, 78, 71` | `13, 10, 26, 10`     | `0, 0, 0, 13`     | `73, 72, 68, 82`  |
| 16 ~ 31   | `0, 0, 0, 2`      | `0, 0, 0, 2`         | `2, 3, 0, 0`      | `0, 15, 216, 229` |
| 32 ~ 47   | `183, 0, 0, 0`    | `1, 115, 82, 71`     | `66, 1, 217, 201` | `44, 127, 0, 0`   |
| 48 ~ 63   | `0, 9, 112, 72`   | `89, 115, 0, 0`      | `11, 19, 0, 0`    | `11, 19, 1, 0`    |
| 64 ~ 79   | `154, 156, 24, 0` | `0, 0, 12, 80`       | `76, 84, 69, 255` | `0, 0, 0, 255`    |
| 80 ~ 95   | `0, 0, 0, 255`    | `255, 255, 255, 251` | `0, 96, 246, 0`   | `0, 0, 4, 116`    |
| 96 ~ 111  | `82, 78, 83, 255` | `255, 255, 127, 128` | `144, 197, 89, 0` | `0, 0, 12, 73`    |
| 112 ~ 127 | `68, 65, 84, 120` | `156, 99, 16, 96`    | `216, 0, 0, 0`    | `228, 0, 193, 39` |
| 128 ~ 143 | `168, 232, 87, 0` | `0, 0, 0, 73`        | `69, 78, 68, 174` | `66, 96, 130`     |

每个表格的单元格内有 4 字节数据，每个字节由 8 位组成，1 位代表的是 `0` 或者 `1` 的一个数字。

# PNG 文件签名

一张 PNG 图片二进制数据的开头必须是这 8 字节：`0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a`。

`0x` 代表这个数字是 16 进制表示的，`0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a` 转换为 10 进制是 `137, 80, 78, 71, 13, 10, 26, 10`。

| 0 ~ 3                    | 4 ~ 7                    |
| ------------------------ | ------------------------ |
| `137, 80, 78, 71`        | `13, 10, 26, 10`         |
| `0x89, 0x50, 0x4e, 0x47` | `0x0d, 0x0a, 0x1a, 0x0a` |

这张图片的前 8 个字节满足签名的要求。

# 数据块

**数据块包含了图片所有的数据，一个数据块可以分为数据块的开始信息、数据块的数据信息和数据块的结束信息**。

一个数据块的开始信息包含 2 个 32 位的数字，换算成字节的话，就是 8 个字节。前 4 个字节会被合并成一个 32 位的数字，表示数据信息的长度，后面 4 个字节可以被转换成文本，表示数据块的类型（类型如下）。
![Alt text](png.assets/image-2.png)

## 开始信息 1

我们从第 8 个字节开始解析数据块的开始信息。

| 8 ~ 11        | 12 ~ 15          |
| ------------- | ---------------- |
| `0, 0, 0, 13` | `73, 72, 68, 82` |
| 长度          | 类型             |
| `13`          | `IHDR`           |

这个数据块是 `IHDR` 类型，有 `13` 字节的数据信息。

## 数据信息 1 `IHDR`

`IHDR` 里面的数据信息如下：

| 16 ~ 19      | 20 ~ 23      | 24 ~ 27                                       | 28          |
| ------------ | ------------ | --------------------------------------------- | ----------- |
| `0, 0, 0, 2` | `0, 0, 0, 2` | `2, 3, 0, 0`                                  | `0`         |
| `width`      | `height`     | `depth`, `colorType`, `compression`, `filter` | `interlace` |
| `2`          | `2`          | `2, 3, 0, 0`                                  | `0`         |

- `width`（宽）和 `height`（高）表示图片的宽高。
- `depth` （通道深度）代表每个色彩通道用几位数据表示。一张 PNG 图片是由像素组成的，每个像素由色彩通道组成，每个色彩通道又是由位来组成。
- `colorType`（色彩类型）PNG 图片一共有 5 种色彩类型，`0` 代表灰度颜色，`2` 代表用 RGB 表示颜色，即 `(R, G, B)`，`3` 代表用色板表示颜色，`4` 代表灰度和透明度来表示颜色，`6` 代表用 RGB 和透明度表示颜色，即 `(R, G, B, A)`。色板的色彩类型里，每个像素是由 1 个色彩通道表示的。
- `compression` 代表了压缩算法。目前只支持 `0`，表示 deflate/inflate。Deflate/inflate 是一种结合了 LZ77 和霍夫曼编码的无损压缩算法，被广泛运用于 `7-zip`，`zlib`，`gzip` 等场景。
- `filter` 代表在压缩前应用的过滤函数类型，目前只支持 `0`。过滤函数类型 `0` 里面包括了 5 种过滤函数。
- `interlace` 代表图片数据是否经过交错，`0` 代表没有交错，`1` 代表交错。

从上面的信息看出，这是一张 2 \* 2 像素的图片，使用色板作为颜色类型，每个像素由 1 个色彩通道组成，每个色彩通道由 2 位组成。像素数据没有交错，经过 `0` 的过滤函数类型后，经过 `deflate` 压缩，

## 结束信息 1

| 29 ~ 32             |
| ------------------- |
| `15, 216, 229, 183` |

结束信息包括了 4 字节的 CRC32 校验和。解码器应该根据数据块类型和数据块的数据信息计算 CRC32 校验和，并与结束信息中的校验和比对。如果相等，则认为图片数据被正确传输。

## 开始信息 2

| 33 ~ 36      | 37 ~ 40           |
| ------------ | ----------------- |
| `0, 0, 0, 1` | `115, 82, 71, 66` |
| 长度         | 类型              |
| `1`          | `sRGB`            |

这个数据块是 `sRGB` 信息，长度是 1 字节。

这个数据块类型是小写字母开头的，这表示这个数据块是辅助数据块，大写字母开头的数据块类型表示关键数据块。

## 数据信息 2 `sRGB`

| 41  |
| --- |
| `1` |

`sRGB` 表示图片使用的色彩空间。

- `0` 表示感性的，用于展示照片等。
- `1` 表示相对色彩，用于展示图标等。
- `2` 表示饱和的，用于展示图表等。
- `3` 表示绝对色彩，用于展示图片原本的色彩。

## 结束信息 2

| 42 ~ 45             |
| ------------------- |
| `217, 201, 44, 127` |

需要比对 CRC32。

## 开始信息 3

| 46 ~ 49      | 50 ~ 53            |
| ------------ | ------------------ |
| `0, 0, 0, 9` | `112, 72, 89, 115` |
| 长度         | 类型               |
| `9`          | `pHYs`             |

9 个字节的 `pHYs` 辅助数据信息。

## 数据信息 3 `pHYs`

| 54 ~ 57            | 58 ~ 61            | 62   |
| ------------------ | ------------------ | ---- |
| `0, 0, 11, 19`     | `0, 0, 11, 19`     | `1`  |
| X 轴每个单位像素数 | Y 轴每个单位像素数 | 单位 |
| `2835`             | `2835`             | 米   |

`pHYs` 数据块代表图片的物理世界大小，从上面的数据可以看出，这张图在现实世界中应该被渲染成每米 2835 像素，宽高一样。

## 结束信息 3

| 63 ~ 66           |
| ----------------- |
| `0, 154, 156, 24` |

比对 CRC32。

## 开始信息 4

| 67 ~ 70       | 71 ~ 74          |
| ------------- | ---------------- |
| `0, 0, 0, 12` | `80, 76, 84, 69` |
| 长度          | 类型             |
| `12`          | `PLTE`           |

12 字节 `PLTE` 色板数据，是关键数据块。

## 数据信息 4 `PLTE`

| 75 ~ 78        | 79 ~ 82        | 83 ~ 86              |
| -------------- | -------------- | -------------------- |
| `255, 0, 0, 0` | `255, 0, 0, 0` | `255, 255, 255, 255` |

色板中包含的数据是 RGB 数据，以 `R, G, B` 的形式保存，这里一共 12 字节，表示了 4 个色块。得到的色板信息如下：

### 色板

`[[255, 0, 0], [0, 255, 0], [0, 0, 255], [255, 255, 255]]`

## 结束信息 4

| 87 ~ 90           |
| ----------------- |
| `251, 0, 96, 246` |

比对 CRC32。

## 开始信息 5

| 91 ~ 94      | 95 ~ 98           |
| ------------ | ----------------- |
| `0, 0, 0, 4` | `116, 82, 78, 83` |
| 长度         | 类型              |
| `4`          | `tRNS`            |

4 字节 `tRNS` 透明度数据，是辅助数据块。

## 数据信息 5 `tRNS`

| 99 ~ 102             |
| -------------------- |
| `255, 255, 255, 127` |

这个数据块为色板提供透明信息，每个字节表示一个色块的透明信息。与色板组合后的色板如下：

### 色板

`[[255, 0, 0, 255], [0, 255, 0, 255], [0, 0, 255, 255], [255, 255, 255, 127]]`

## 结束信息 5

| 103 ~ 106           |
| ------------------- |
| `128, 144, 197, 89` |

比对 CRC32。

## 开始信息 6

| 107 ~ 110     | 111 ~ 114        |
| ------------- | ---------------- |
| `0, 0, 0, 12` | `73, 68, 65, 84` |
| 长度          | 类型             |
| `12`          | `IDAT`           |

12 字节 `IDAT` 像素数据，是关键数据块。

## 数据信息 6 `IDAT`

| 115 ~ 118          | 119 ~ 122       | 123 ~ 126        |
| ------------------ | --------------- | ---------------- |
| `120, 156, 99, 16` | `96, 216, 0, 0` | `0, 228, 0, 193` |

在解析像素数据前，我们先要了解下像素数据是如何编码的。每行像素都会先经过过滤函数处理，每行像素的过滤函数可以不同。然后所有行的像素数据会经过 deflate 压缩算法压缩。所以，我们需要对这里的像素数据先解压，这里我们直接使用了 `zlib.inflate()` 函数。在浏览器上，可以使用 [`pako`](https://github.com/nodeca/pako) 工具包。

解压出来的像素数据是 Uint8Array：`0, 16, 0, 176`。

接下去我们需要仔细了解每行像素是如何编码，才能把上面的数据还原成像素点。

### 扫描线 Scanline

一根扫描线包含图片一行像素的数据。我们知道这张图片的高度是 2，也就是像素数据中有 2 行扫描线。

一根扫描线由 1 字节的过滤函数标记和像素信息组成。像素信息一个接一个地排列，中间没有多余的空位。如果扫描线长度不足以填满字节的位数，最后几位会被补齐。一根扫描线的结构如下：

| 过滤函数 | 像素...[补齐...]                      |
| -------- | ------------------------------------- |
| `8 位`   | `每像素位数` \* `每行像素数` + `补齐` |

所以我们先要知道每个像素的位数才能解码扫描线。

### 色彩类型 - 色彩通道 - 通道深度 - 每像素位数

| 色彩类型 | 色彩                   | 每像素通道数 | 通道深度       | 每像素位数     |
| -------- | ---------------------- | ------------ | -------------- | -------------- |
| `0`      | 灰度                   | 1            | 1, 2, 4, 8, 16 | 1, 2, 4, 8, 16 |
| `2`      | 真彩色（RGB）          | 3            | 8, 16          | 24, 48         |
| `3`      | 色板                   | 1            | 1, 2, 4, 8     | 1, 2, 4, 8     |
| `4`      | 灰度和透明度           | 2            | 8, 16          | 16, 32         |
| `6`      | 色彩色和透明度（RGBA） | 4            | 8, 16          | 32, 64         |

这张图片的色彩类型是 `3`，所以每个像素包含 `1` 个色彩通道。又因为图片的通道深度是 `2`，所以我们知道每个像素是用 `2` 位来表示的。

所以我们可以解码扫描线了。

### 解码扫描线

| 行  | 过滤函数 | 像素...[补齐...]                             |
| --- | -------- | -------------------------------------------- |
|     | `8 位`   | `每像素 2 位 * 2 像素` + `4 位补齐` = `8 位` |
| `0` | `0`      | `00010000` (`16`)                            |
| `1` | `0`      | `10110000` (`176`)                           |

### 过滤函数

在扫描线被压缩前，每根扫描线都会被单独的过滤函数处理，以使后面的压缩效果更好。

在过滤函数类型 `0` 中，有 5 种过滤函数：

| 过滤函数 | 函数  | 过滤方式                                       |
| -------- | ----- | ---------------------------------------------- |
| 0        | 无    | 保留原始数据                                   |
| 1        | 减    | 减去 A                                         |
| 2        | 上    | 减去 B                                         |
| 3        | 平均  | 根据 A 和 B 取平均，并向下取证                 |
| 4        | Paeth | 使用最接近于 p = A + B − C 的 A、B 或 C 的数值 |

![Alt text](png.assets/image-1.png)

过滤函数用 A、B、C 三点的数值来计算当前点 X。

这张图片里面的过滤函数 `0` 表示这张图数据未经过滤。所以我们只要保留原始数据就行了。

### 扫描线像素

| 行  | 第 1 列 | 第 2 列 | 补齐... |
| --- | ------- | ------- | ------- |
| `0` | `00`    | `01`    | `0000`  |
| `1` | `10`    | `11`    | `0000`  |

这里每个像素中的数据表示了这个像素的颜色在色板中的索引。根据色板，我们可以还原出图片的像素信息：`[[255, 0, 0, 255], [0, 255, 0, 255], [0, 0, 255, 255], [255, 255, 255, 127]]`。

### 图片像素

| 行\列 | `0`                | `1`                    |
| ----- | ------------------ | ---------------------- |
| `0`   | `(255, 0, 0, 255)` | `(0, 255, 0, 255)`     |
| `1`   | `(0, 0, 255, 255)` | `(255, 255, 255, 127)` |

## 结束信息 6

| 127 ~ 130          |
| ------------------ |
| `39, 168, 232, 87` |

比对 CRC32。

## 开始信息 7

| 131 ~ 134    | 135 ~ 138        |
| ------------ | ---------------- |
| `0, 0, 0, 0` | `73, 69, 78, 68` |
| `0`          | `IEND`           |

0 字节 `IEND` 图片结束数据块，是关键数据块。

## 数据信息 7 `IEND`

无。

## 结束信息 7

| 139 ~ 142          |
| ------------------ |
| `174, 66, 96, 130` |

比对 CRC32。

# ImageData

整张图片解码完成，最终的 `ImageData` 对象是:

```js
imageData = {
  width: 2,
  height: 2,
  data: [255, 0, 0, 255, 0, 255, 0, 255, 0, 0, 255, 255, 255, 255, 255, 127],
};
```

# 总结

我们成功解码了一张简单的 PNG 图片，但其中，我简化了很多细节：

- `IDAT` 数据可以被分开放在多个数据块中。所以我们需要先收集到所有 `IDAT` 数据块，再对其解码。
- 一共有 4 种关键数据块和 14 种辅助数据块。可以参考 [PNG 规范](http://www.libpng.org/pub/png/spec/1.2/PNG-Contents.html)中的[标准数据块摘要](http://www.libpng.org/pub/png/spec/1.2/PNG-Chunks.html#C.Summary-of-standard-chunks)。
- 交错型的 PNG 图片可以让 PNG 展示地更快，但是会让 `IDAT` 数据变大。

你可以在 [GitHub](https://github.com/vivaxy/png) 看到实现了以上功能的源码。
