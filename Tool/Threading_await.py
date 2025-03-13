import asyncio

import Tool.minion_bag as minion_bag
from concurrent.futures import ThreadPoolExecutor

"""
创建一个线程池
"""

executor = ThreadPoolExecutor(max_workers=10)  # 线程池最大线程数为10


async def upload_file_to_minion_bag(bucket_name, file_name, object_name, file_path, content_type):
    loop = asyncio.get_event_loop()
    # 使用线程池提交任务
    msg = await loop.run_in_executor(executor, minion_bag.UploadObject, bucket_name, object_name, file_path,
                                     content_type, False)
    msg2 = await loop.run_in_executor(executor, minion_bag.delete_file, bucket_name, file_name)
    return msg, msg2


async def upload_file_to_minion_bag_2(bucket_name, object_name, file_path, content_type):
    loop = asyncio.get_event_loop()
    # 使用线程池提交任务
    msg = await loop.run_in_executor(executor, minion_bag.UploadObject, bucket_name, object_name, file_path,
                                     content_type, False)
    return msg


async def delete_file_from_minion_bag(bucket_name, file_name):
    loop = asyncio.get_event_loop()
    # 使用线程池提交任务
    msg = await loop.run_in_executor(executor, minion_bag.delete_file, bucket_name, file_name)
    return msg
