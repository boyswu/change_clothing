"""
缓存工具验证码和验证邮箱的缓存工具
"""

from cachetools import TTLCache

# 创建一个缓存，最大容量为100，过期时间为5分钟（300秒）
cache = TTLCache(maxsize=100, ttl=300)


# 添加数据到缓存的函数
def set_cache(key, value):
    cache[key] = value
    print(f"设置缓存: {key} -> {value}")


# 获取缓存数据的函数
def get_cache(key):
    if key in cache:
        value = cache.pop(key)  # 先获取缓存，然后删除缓存
        print(f"获取缓存: {key} -> {value}")
        return value
    else:
        print(f"缓存未命中: {key} 已过期或不存在")
        return None
