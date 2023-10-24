# 简述

以队列的形式解压嵌套的 `zip`, `tar`, `gz`, `rar`, `7z` 压缩文件

## 使用方法

```py
from extract_nested_compressed_file import NestedCompressedFile, CompressedFileInfo
ncf = NestedCompressedFile("compressed_file_path")
ncf.deep_extract_all_to("to_path")
for item in ncf.filelist:
    if type(item) == CompressedFileInfo:
        print(f"文件 {item.compressed_path} 解压到路径 {item.to_path}，失败原因：{item.msg}")
    else:
        print(f"文件 {item.compressed_path} 解压到路径 {item.path}")
```