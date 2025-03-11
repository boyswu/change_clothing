import pymysql
from dbutils.pooled_db import PooledDB

# host = '8.147.233.239'
host = '43.143.229.40'  #实验室
port = 3306
user = 'root'
# password = 'team2111'
password = 'team2111..'  #实验室
database = 'sign_in_system'


# def connect_sql():
#     # 连接数据库
#     db = pymysql.connect(host=host, user=user, passwd=passwd, db=db2, charset='utf8')
#     cursor = db.cursor()
#     return db, cursor

class MySQLConnectionPool:

    def __init__(self):
        self.pool = PooledDB(
            creator=pymysql,  # 使用 pymysql 作为数据库连接的模块
            mincached=5,  # 初始化时连接池中至少创建的连接数，0表示不创建
            maxconnections=100,  # 连接池允许的最大连接数，0和None表示不限制连接数
            blocking=True,  # 如果没有可用连接后，是否阻塞等待
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )

    def get_connection(self):
        # 从连接池获取一个连接
        return self.pool.connection()

    def close_connection(self, conn):
        # 关闭连接，返回连接池
        conn.close()
