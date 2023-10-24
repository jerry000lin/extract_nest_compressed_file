import os
import zipfile_modify as zipfile
import tarfile
import gzip
import rarfile
import py7zr


class CompressStatus:
    SUCCESS = 0
    ENCRYPTED = 1
    FAIL = 2


def zipfile_extract_all_to(file_path, target_path):
    status = CompressStatus.SUCCESS
    message = None
    try:
        zip_file = zipfile.ZipFile(file_path)
        for zinfo in zip_file.infolist():
            is_encrypted = zinfo.flag_bits & 0x1
            if is_encrypted:
                # 加密的压缩文件
                message = "加密文件"
                status = CompressStatus.ENCRYPTED

        if status == CompressStatus.SUCCESS:
            zip_file.extractall(target_path)
    except Exception as e:
        # 解压失败
        status = CompressStatus.FAIL
        message = str(e)
    finally:
        if 'zip_file' in dir():
            zip_file.close()
    return status, message


def tarfile_extract_all_to(file_path, target_path):
    status = CompressStatus.SUCCESS
    message = None

    try:
        tar_file = tarfile.open(file_path)
        tar_file.extractall(target_path)
    except Exception as e:
        # 解压失败
        status = CompressStatus.FAIL
        message = str(e)
    finally:
        if 'tar_file' in dir():
            tar_file.close()
    return status, message


def gzfile_extract_all_to(file_path, target_path):
    '''
    .gz 为压缩单个文件, .tar.gz 结尾的包通过 tarfile 处理
    '''
    status = CompressStatus.SUCCESS
    message = None

    try:
        gz_file = gzip.open(file_path, 'rb')
        target_file = open(target_path, 'wb')
        while True:
            block = gz_file.read(65536)
            if not block:
                break
            else:
                target_file.write(block)
    except Exception as e:
        # 解压失败
        status = CompressStatus.FAIL
        message = str(e)
    finally:
        if 'gz_file' in dir():
            gz_file.close()
        if 'target_file' in dir():
            target_file.close()
    return status, message


def rarfile_extract_all_to(file_path, target_path):
    status = CompressStatus.SUCCESS
    message = None
    try:
        rar_file = rarfile.RarFile(file_path)
        if rar_file.needs_password():
            # 加密的压缩文件
            status = CompressStatus.ENCRYPTED
            message = "加密文件"
        else:
            rar_file.extractall(target_path)
    except Exception as e:
        # 解压失败
        status = CompressStatus.FAIL
        message = str(e)
    finally:
        if 'rar_file' in dir():
            rar_file.close()
    return status, message


def py7zr_extract_all_to(file_path, target_path):
    status = CompressStatus.SUCCESS
    message = None
    try:
        py7zr_file = py7zr.SevenZipFile(file_path)
        py7zr_file.extractall(target_path)
    except py7zr.exceptions.PasswordRequired:
        status = CompressStatus.ENCRYPTED
        message = "加密文件"
    except Exception as e:
        # 解压失败
        status = CompressStatus.FAIL
        message = str(e)
    finally:
        if 'py7zr_file' in dir():
            py7zr_file.close()
    return status, message


class FileInfo:
    '''
    解压的单个文件信息保存
    '''

    def __init__(self, path, compressed_path):
        self.path = path
        self.compressed_path = compressed_path


class CompressedFileInfo(FileInfo):
    '''
    压缩文件信息
    '''

    def __init__(self, path, compressed_path):
        super().__init__(path, compressed_path)
        self.to_path = ''
        self.encrypted = False
        self.is_error = False
        self.error_message = ''


class CompressedFile():
    '''
    压缩文件工具
    '''
    uncomprees_func_dict = {
        'zip': zipfile_extract_all_to,
        'tar': tarfile_extract_all_to,
        'gz': gzfile_extract_all_to,
        'rar': rarfile_extract_all_to,
        '7z': py7zr_extract_all_to
    }

    @classmethod
    def is_compressed_file(cls, path):
        '''
        判断是否是当前支持的压缩文件
        '''
        _, ext = os.path.splitext(path)
        return ext[1:] in cls.uncomprees_func_dict

    def __init__(self, path, compressed_path, target_path_default=None):
        self.info = CompressedFileInfo(path, compressed_path)
        if path.endswith('.tar.gz'):
            self.uncompress_func = tarfile_extract_all_to
            self.target_path_default = path[:-len('.tar.gz')]
        else:
            path_without_ext, ext = os.path.splitext(path)
            self.uncompress_func = self.uncomprees_func_dict.get(ext[1:])
            self.target_path_default = path_without_ext
        if target_path_default != None:
            self.target_path_default = target_path_default

    def extract_all(self, target_path=None):
        if not target_path:
            target_path = self.target_path_default
        self.info.to_path = self.check_uncompress_path(target_path)
        status, message = self.uncompress_func(self.info.path, self.info.to_path)
        if status == CompressStatus.ENCRYPTED:
            self.info.encrypted = True
            self.info.msg = message
        elif status == CompressStatus.FAIL:
            self.info.is_error = True
            self.info.msg = message
        return self.info

    def check_uncompress_path(self, to_path):
        '''
        若解压路径存在，返回新的路径
        在原路径前添加 (i) i=1,2,3...
        '''
        suffix = 1
        file_dir, filename = os.path.split(to_path)

        while True:
            if os.path.exists(to_path):
                to_path = os.path.join(file_dir, f"({str(suffix)}){filename}")
                suffix += 1
            else:
                return to_path


class NestedCompressedFile():

    def __init__(self, file_path):
        self.file_path = file_path
        self.compressed_file_queue = []
        self.filelist = []
        self.origin_compress_file = None

    def deep_extract_all_to(self, target_path):
        '''
        核心功能
        将嵌套的压缩包按源相对路径挨个解压到 target_path ,
        并将子文件的信息保存到 fileList 中
        '''
        self.filelist = []

        _, filename = os.path.split(self.file_path)
        self.origin_compress_file = CompressedFile(self.file_path, filename, target_path_default=target_path)

        self.compressed_file_queue.append(self.origin_compress_file)

        while len(self.compressed_file_queue) != 0:
            compressed_file = self.compressed_file_queue.pop(0)

            compressed_file_info = compressed_file.extract_all()
            if compressed_file_info.encrypted or compressed_file_info.is_error:
                self.filelist.append(compressed_file_info)
            else:
                self.uncompress_subfile_walk(compressed_file_info.to_path, compressed_file_info.compressed_path)

    def uncompress_subfile_walk(self, walk_path, path_in_compressed):
        '''
        遍历文件夹子文件
        将子文件信息保存于 filelist 和 compressed_file_queue
        '''
        if os.path.isdir(walk_path):
            for current_dir, _, sub_file_list in os.walk(walk_path):
                if len(sub_file_list) != 0:
                    for sub_file_fullname in sub_file_list:
                        file_save_path = os.path.join(current_dir, sub_file_fullname)
                        file_path_in_compressed = file_save_path.replace(walk_path, path_in_compressed)

                        if CompressedFile.is_compressed_file(file_save_path):
                            self.compressed_file_queue.append(CompressedFile(file_save_path, file_path_in_compressed))
                        else:
                            self.filelist.append(FileInfo(file_save_path, file_path_in_compressed))
        else:
            if CompressedFile.is_compressed_file(walk_path):
                self.compressed_file_queue.append(CompressedFile(walk_path, path_in_compressed))
            else:
                self.filelist.append(FileInfo(walk_path, path_in_compressed))
