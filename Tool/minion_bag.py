# encoding: utf-8
# @author: DayDreamer
# @file: minios.py
# @time: 2024/6/4 21:29
# @desc:
"""
minion_bag模块主要用于处理minio相关的操作，包括创建桶、删除桶、上传文件、下载文件、获取文件列表、获取文件链接、获取文件大小等功能。
"""
# 从minio库中导入Minio客户端类
import logging

from datetime import timedelta, datetime
from minio.commonconfig import GOVERNANCE
from minio.retention import Retention
from connect_tool.minion_connect import minio_client, endpoint
import io
import json


def CreateBucket(BucketName: str) -> bool:
    """
    创建存储桶
    @Author: ChuanCheng Shi
    :param BucketName: 桶名字
    :return: bool
    """
    try:
        if not minio_client.bucket_exists(BucketName):
            minio_client.make_bucket(BucketName, location="us-east-1")
            # 设置桶为公开状态
            policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": "*",
                        "Action": ["s3:GetObject"],
                        "Resource": [f"arn:aws:s3:::{BucketName}/*"]
                    }
                ]
            }
            minio_client.set_bucket_policy(BucketName, json.dumps(policy))
            return True
        else:
            return None
    except BaseException as e:
        logging.debug(str(e))
        return False


def DelBucket(BucketName: str) -> bool:
    """
    删除存储桶
    @Author: ChuanCheng Shi
    :param BucketName: 桶名字
    :return: bool
    """
    try:
        # 遍历存储桶中的所有对象
        objects = minio_client.list_objects(BucketName)
        # 逐一删除每个对象
        for File_name in objects:
            try:
                print(f"删除文件 {File_name.object_name} 成功。")
                # 获取所有以文件夹名称开头的对象
                objects = list(minio_client.list_objects(BucketName, prefix=File_name.object_name, recursive=True))
                if not objects:
                    print(f"没有找到以 {File_name.object_name} 为前缀的对象。")
                    continue  # 如果没有对象，则跳过

                objects_to_delete = [obj.object_name for obj in objects]
                print(f"待删除对象列表: {objects_to_delete}")

                # 删除所有以文件夹名称开头的对象
                for obj_name in objects_to_delete:
                    minio_client.remove_object(BucketName, obj_name)
                    print(f"删除文件 {obj_name} 成功。")

                print(f"删除文件夹 {File_name.object_name} 成功。")
            except Exception as e:
                print(f"处理文件 {File_name.object_name} 时发生错误: {e}")

        # 确保所有对象已删除后，再尝试删除存储桶
        # 再次确认存储桶中没有对象
        objects_after_deletion = minio_client.list_objects(BucketName)
        print(objects_after_deletion)
        if not list(objects_after_deletion):  # 如果列表为空，则存储桶为空
            minio_client.remove_bucket(BucketName)
            print(f"存储桶 {BucketName} 已成功删除。")
            return True
        else:
            print(f"存储桶 {BucketName} 仍然有对象，无法删除。")
            return False
    except BaseException as e:
        print(e)
        logging.debug(str(e))
        return False


def GetObjectListFromBucket(BucketName: str) -> list:
    """
    获取桶内数据信息
    @Author: ChuanCheng Shi
    :param BucketName: 桶名称
    :return:
    """
    if minio_client.bucket_exists(BucketName):
        objects = minio_client.list_objects(BucketName)
        obj_list = [obj.object_name for obj in objects]
        return obj_list
    else:
        logging.warning(msg="Maybe your Bucket is Empty")
        return []


def DownloadObjectFromBucket(BucketName: str, ObjectName: str, SavePath: str) -> bool:
    """
    下载文件到本地, 函数会优先检查桶内是否存在该文件，在进行下载，后续需要更新文件路径检测机制
    :param ObjectName: 文件名
    :param BucketName: 桶名称
    :param SavePath: 保存路径
    :return: bool
    """

    if ObjectName in GetObjectListFromBucket(BucketName):
        minio_client.fget_object(BucketName, ObjectName, SavePath)
        return True
    else:
        return False


def GetObjectLink(ObjectName: str, BucketName: str) -> str:
    """
    获取一个存储对象的链接
    :param ObjectName: 文件名
    :param BucketName: 桶名称
    :return: 链接
    """
    if ObjectName in GetObjectListFromBucket(BucketName):
        return "http://" + endpoint + "/" + BucketName + "/" + ObjectName
    else:
        return "No Link"


def GetObjectSize(ObjectName: str, BucketName: str) -> str:
    """
    获取一个存储对象的大小
    :param ObjectName: 文件名
    :param BucketName: 桶名称
    :return: 文件大小(字节)
    """
    if ObjectName in GetObjectListFromBucket(BucketName):
        ObjectSize = minio_client.stat_object(BucketName, ObjectName)
        return ObjectSize.size
    else:
        return 'not exist Object'


def UploadObject(BucketName: str, ObjectName: str, file_path: str, content_type: str, retention: bool = False) -> bool:
    """
    # 上传文件到minio
    :param ObjectName: 文件路径/文件名,注意路径要以斜杠结尾
    :param BucketName:  桶名称
    :param file_path:   本地文件路径
    :param content_type: 文件的内容类型
    :param retention: 是否设置过期时间
    :return:
    """
    # 目标对象名（即文件在 MinIO 中的完整路径）
    # object_name = folder_path + "your-file-name.txt"
    # folder_path：目标文件夹路径，注意路径要以斜杠结尾。
    try:
        if retention:  # 是否设置过期时间
            date = datetime.utcnow().replace(
                hour=0, minute=0, second=0, microsecond=0,
            ) + timedelta(days=3)
            retention = Retention(GOVERNANCE, date)
            minio_client.fput_object(BucketName, ObjectName, file_path, content_type, retention=retention)
        else:
            minio_client.fput_object(BucketName, ObjectName, file_path, content_type)
        logging.debug("Upload Success!")
        return True
    except BaseException as e:
        logging.warning(str(e))
        return False


def UploadMultipleObjects(BucketName: str, folder_path: str, file_paths: list, content_type: str,
                          retention: bool = False) -> bool:
    """
    # 上传多个文件到minio，如果文件夹不存在则创建文件夹，如果有上传失败则删除已上传的文件
    :param BucketName: MinIO 中的桶名
    :param folder_path: MinIO 中的目标文件夹路径，注意路径要以斜杠结尾
    :param file_paths: 本地文件路径列表
    :param content_type: 文件的内容类型
    :param retention: 是否设置过期时间
    :return: 所有文件上传是否成功
    """
    try:

        # 如果文件夹不存在则创建文件夹
        minio_client.make_bucket(BucketName, location="")  # 确保桶存在
        minio_client.put_object(BucketName, folder_path, b"", content_type="application/octet-stream")

        uploaded_objects = []
        for file_path in file_paths:
            file_name = file_path.split('/')[-1]  # 获取文件名
            ObjectName = folder_path + file_name  # 构建 MinIO 中的对象名
            if UploadObject(BucketName, ObjectName, file_path, content_type, retention):
                uploaded_objects.append(ObjectName)
            else:
                # 如果有上传失败，则删除已上传的文件
                for obj in uploaded_objects:
                    minio_client.remove_object(BucketName, obj)
                return False

        return True

    except Exception as e:
        print(f"操作失败: {e}")
        return False


def create_folder(Bucket_name: str, Folder_name: str):
    """
    创建一个空文件夹
    :param Bucket_name: 桶名称
    :param Folder_name: 文件夹名称
    :return: bool
    """
    # 创建一个空的内存文件对象
    data = io.BytesIO(b"")
    try:
        minio_client.put_object(Bucket_name, Folder_name, data, length=0)
        return True
    except BaseException as e:
        logging.warning(str(e))
        return False


def delete_folder(Bucket_name: str, File_name: str):
    """
    删除一个文件夹
    :param Bucket_name: 桶名称
    :param Folder_name: 文件夹名称
    :return: bool
    """
    try:
        # 检查是否是文件夹
        if File_name.endswith('/'):
            # 获取所有以文件夹名称开头的对象
            objects = minio_client.list_objects(Bucket_name, prefix=File_name, recursive=True)
            objects_to_delete = [obj.object_name for obj in objects]

            # 删除所有以文件夹名称开头的对象
            for obj in objects_to_delete:
                minio_client.remove_object(Bucket_name, obj)
            return True
        else:
            # 删除单个文件
            minio_client.remove_object(Bucket_name, File_name)
            return True
    except BaseException as e:
        logging.warning(str(e))
        return False


# 删除一个文件
def delete_file(Bucket_name: str, object_name: str):
    """
    删除一个文件
    :param Bucket_name: 桶名称
    :param object_name: 文件名称
    :return: bool
    """
    print("delete_file")
    try:
        # 删除单个文件
        minio_client.remove_object(Bucket_name, object_name)
        return True
    except BaseException as e:
        logging.warning(str(e))
        return False


def get_object_url(Bucket_name: str, Folder_name: str, File_name: str):
    """
    获取一个文件的链接
    :param Bucket_name: 桶名称
    :param File_name: 文件名称
    :return: 链接
    """
    try:
        # 构建文件夹路径
        folder_path = f"{Bucket_name}/{Folder_name}/"
        # 构建对象名称
        object_name = folder_path + File_name
        # 使用 MinIO 客户端获取文件下载链接
        url = minio_client.presigned_get_object(Bucket_name, object_name)
        return url
    except BaseException as e:
        logging.warning(str(e))
        return False

# if __name__ == '__main__':
#     m = MinioCommand(ip="43.143.229.40", api_port="9000", access_key="GFRTW6X53IYFASR3FN2Q",
#                      secret_key="NE1+SErpSxo+hABqdhPEwIlkEMz22x02t22y+8XF")
#
# if __name__ == '__main__': minio_minio_client = MinioCommand(ip='192.168.1.100', api_port='9000',
# access_key='minioadmin', secret_key='minioadmin', secure=False) # minio_minio_client.CreateBucket('test') #
# minio_minio_client.DelBucket('test') minio_minio_client.UploadObject('test.txt', 'test', 'D:\\test.txt', 'text/plain')
