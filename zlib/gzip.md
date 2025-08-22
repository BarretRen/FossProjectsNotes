zlib 提供 api 支持压缩解压 gzip 文件，示例如下：

```c
#include <zlib.h>
#define BUF_SIZE 512
void compress_file(const char *source_path, const char *dest_path)
{
    int fd = open(source_path, O_RDONLY);
    if (fd < 0) {
        bk_printf("[%s][%d] open %s fail:%d\r\n", __FUNCTION__, __LINE__, source_path, fd);
    }
    else
    {
        gzFile gzfile = gzopen(dest_path, "wb");
        if (gzfile == NULL) {
            bk_printf("[%s][%d] gzopen fail\r\n", __FUNCTION__, __LINE__);
        } else {
            uint8_t buf[BUF_SIZE];
            int bytes_read;
            int written = 0;

            while ((bytes_read = read(fd, buf, BUF_SIZE)) > 0) {
                written = gzwrite(gzfile, buf, bytes_read);
                if (written <= 0) {
                    bk_printf("[%s][%d] gzwrite fail: %s\r\n", __FUNCTION__, __LINE__, gzerror(gzfile, NULL));
                    break;
                }
                else
                {
                    bk_printf("[%s][%d] gzwrite success: %d\r\n", __FUNCTION__, __LINE__, written);
                }
            }

            if (gzflush(gzfile, Z_FINISH) != Z_OK) {
                bk_printf("[%s][%d] Final flush failed\r\n", __FUNCTION__, __LINE__);
            }

            if (gzclose(gzfile) != Z_OK) {
                bk_printf("[%s][%d] gzclose failed:%s\r\n", __FUNCTION__, __LINE__, gzerror(gzfile, NULL));
            }
        }

        close(fd);
    }
}

void decompress_file(const char *source_path, const char *dest_path)
{
    gzFile gzfile = gzopen(source_path, "rb");
    if (gzfile == NULL) {
        bk_printf("[%s][%d] gzopen fail\r\n", __FUNCTION__, __LINE__);
    }
    else
    {
        int fd = open(dest_path, O_WRONLY | O_CREAT | O_APPEND);
        if (fd < 0) {
            bk_printf("[%s][%d] open %s fail:%d\r\n", __FUNCTION__, __LINE__, dest_path, fd);
        }
        else
        {
            uint8_t buf[BUF_SIZE];
            int bytes_read;
            int written = 0;

            while ((bytes_read = gzread(gzfile, buf, BUF_SIZE)) > 0) {
                written = write(fd, buf, bytes_read);
                if (written <= 0) {
                    bk_printf("[%s][%d] write fail\r\n", __FUNCTION__, __LINE__);
                    break;
                }
                else
                {
                    bk_printf("[%s][%d] write success: %d\r\n", __FUNCTION__, __LINE__, written);
                }
            }

            close(fd);
        }

        if (gzclose(gzfile) != Z_OK) {
            bk_printf("[%s][%d] gzclose failed:%s\r\n", __FUNCTION__, __LINE__, gzerror(gzfile, NULL));
        }
    }
}

//调用示例：
compress_file("/qspi/bg.jpg", "/qspi/bg.jpg.gz");
decompress_file("/qspi/bg.jpg.gz", "/qspi/bg2.jpg");
```
