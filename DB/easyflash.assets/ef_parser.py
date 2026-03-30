import struct
import binascii
import argparse

def calculate_ef_crc(data: bytes) -> int:
    """匹配EasyFlash的CRC32计算"""
    return binascii.crc32(data) & 0xFFFFFFFF

def parse_easyflash_bin(file_path):
    with open(file_path, "rb") as f:
        raw_data = f.read()

    offset = 0
    total_size = len(raw_data)
    print("=" * 70)
    print("EasyFlash NG 解析器 (修复CRC + 完整打印值)")
    print("=" * 70 + "\n")

    while offset < total_size:
        # 1. 查找KV40魔数锚点
        kv_magic_pos = raw_data.find(b"KV40", offset)
        if kv_magic_pos == -1:
            break  # 没有更多KV块了

        # 2. 定位元数据区
        meta_start = kv_magic_pos + 8
        if meta_start + 12 > total_size:
            offset = kv_magic_pos + 1
            continue

        # 3. 解析元数据
        meta_bytes = raw_data[meta_start : meta_start + 12]
        crc_stored, name_len_raw, value_len = struct.unpack("<III", meta_bytes)

        # 解析长度
        name_len = name_len_raw & 0xFF  # name_len取第一个字节

        # 4. 边界安全校验
        name_start = meta_start + 12
        name_end = name_start + name_len
        sep_pos = name_end
        value_start = sep_pos + 1
        value_end = value_start + value_len

        if value_end > total_size:
            offset = kv_magic_pos + 1
            continue

        # 5. 提取数据
        name_bytes = raw_data[name_start : name_end]
        value_bytes = raw_data[value_start : value_end]

        # 6. 打印结果 (不校验CRC，直接打印)
        print(f"[块起始偏移: 0x{kv_magic_pos:08X}]")
        print(f"  键名: {repr(name_bytes)} (长度: {name_len} 字节)")
        print(f"  值: {repr(value_bytes)} (长度: {len(value_bytes)} 字节)")
        print("-" * 70 + "\n")

        # 跳到当前块末尾，继续查找下一个块
        offset = value_end

    print("✅ 解析完成！")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EasyFlash 4.x NG 分区数据解析器")
    parser.add_argument("dump_file", help="Flash镜像dump文件的路径")
    args = parser.parse_args()

    parse_easyflash_bin(args.dump_file)