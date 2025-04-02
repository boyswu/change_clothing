from minio import Minio

"""
Fastapi + MinIO 实现文件上传下载
"""
# 替换为你的 MinIO 服务器信息
ip = "IP"
api_port = "9000"
endpoint = f"{ip}:{api_port}"
access_key = "yoursaccess_key"
secret_key = "yourssecret_key"
secure = False  # 如果使用 HTTPS 设置为 True

# 创建 MinIO 客户端
minio_client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)
