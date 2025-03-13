"""
token模块
"""
import jwt
import datetime
from datetime import datetime, timedelta

from fastapi import Header

# 假设你已经有了MinIO的连接配置

SECRET_KEY = "team2111"  # 请替换为你的密钥
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 10080  # 一周


def create_access_token(data: dict, expires_delta: timedelta = None):
    """
    生成token
    :param data:
    :param expires_delta:
    :return:
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=60)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_token_data(Token):
    # 将字典编码为 JWT 字符串
    encoded_token = jwt.encode(Token, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_token


# 用于验证 token 的函数
def verify_token(access_token: str = Header(None)):
    """
    验证token, 检查token是否过期
    :param access_token:
    :return:
    """
    if not access_token:
        print("Token未提供")
        return False
    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        print("Token过期")
        return False
    except jwt.InvalidTokenError:
        print("Token无效")
        return False
