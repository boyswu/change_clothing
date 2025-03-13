"""
保存文件
"""
import os
from datetime import datetime


def upload_files(file):
    # 获取项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # 读取文件内容
    file_content = file.file.read()
    # 时间戳
    timestamp = int(datetime.now().timestamp())
    # 指定保存路径
    file_path = os.path.join(project_root, 'file_{}'.format(str(timestamp)))

    # 保存文件到本地
    with open(file_path, 'wb') as f:
        f.write(file_content)
    return file_path

