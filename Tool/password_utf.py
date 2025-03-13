"""
密码加密模块
"""
import hashlib


def encrypt_password(password: str) -> str:
    sha256 = hashlib.sha256()
    sha256.update(password.encode('utf-8'))
    encrypted_password = sha256.hexdigest()
    return encrypted_password
