import requests
import os
from pathlib import Path
from Tool import Threading_await


def download_url(url: str, local_file_path: str):
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # 下载图片
    response = requests.get(url)
    # 指定保存路径
    file_path = os.path.join(project_root, 'photo_{}'.format(local_file_path))

    # 检查请求是否成功
    if response.status_code == 200:
        # 将图片保存至本地
        with open(file_path, 'wb') as file:
            file.write(response.content)
        print(f"图片已成功下载到: {file_path}")
        return file_path
    else:
        print(f"下载失败，状态码: {response.status_code}")
        return False


def upload_local_file(user_phone: str, file_path: str, folder_name: str):
    # 创建Path对象
    path = Path(file_path)
    # 获取文件的扩展名，不包括前面的点
    extension = path.suffix[1:]
    # 上传文件到minion的桶里
    object_name = f"{user_phone}/{'image'}/{'photo'}_{folder_name}"
    content_type = f"image/{extension}"

    msg = Threading_await.upload_file_to_minion_bag_2(user_phone, object_name, file_path,
                                                      content_type)
    if not msg:
        return False
    else:
        return True
