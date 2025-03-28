"""
保存文件
"""
import os


def upload_files(file, timestamp):
    # 获取项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # 读取文件内容
    file_content = file.file.read()
    # 指定保存路径
    file_path = os.path.join(project_root, 'file_{}_{}'.format(str(timestamp), file.filename))

    # 保存文件到本地
    with open(file_path, 'wb') as f:
        f.write(file_content)
    return file_path
