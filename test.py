from extract_nested_compressed_file import NestedCompressedFile, CompressedFileInfo
import time
import os
import json
ncf = NestedCompressedFile("./target.zip")
save_path = os.path.join("./save_dir", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())))
ncf.deep_extract_all_to(save_path)

file_info_list = []
for item in ncf.filelist:
    file_info_list.append(item.__dict__)
    if type(item) == CompressedFileInfo:
        print(f"文件 {item.compressed_path} 解压到路径 {item.to_path}，失败原因：{item.msg}")
    else:
        print(f"文件 {item.compressed_path} 解压到路径 {item.path}")
strjson = json.dumps(file_info_list, ensure_ascii=False)

with open('./output.json', "w") as f:  # 设置文件对象
    str = f.write(strjson)
