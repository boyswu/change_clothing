import os
import threading
import random

from decimal import Decimal, ROUND_DOWN
from fastapi import Form, File, UploadFile, Depends, APIRouter
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
import Model.ToDoModel as ToDoModel
import Tool.email_send as email_send
import Tool.cache_code as cache_code
import Tool.tokens as token
import Tool.password_utf as password_utf
import Tool.Threading_await as Threading_await
from Tool.face_recognize import face_recognize
from Tool.upload import upload_files
from connect_tool.sql import MySQLConnectionPool
from Tool.timer_task import run_schedule

router = APIRouter()
# import logging
#
# logging.basicConfig(level=logging.DEBUG)
'''
    创建数据库连接池
'''
db_pool = MySQLConnectionPool()

"""
创建一个调度器线程，用于定时任务
"""


@router.on_event("startup")
def startup_event():
    # 启动调度任务的线程
    scheduler_thread = threading.Thread(target=run_schedule)
    scheduler_thread.start()
    print("调度器已启动")


"""
账户
用户注册、登录、邮箱验证、修改密码相关接口=============================================================================

"""


@router.post("/register_mission", summary="注册用户", description="注册用户", tags=['咔咔'])
async def register_user(user_name: str = Form(...),
                        user_id: str = Form(...),
                        Password: str = Form(...),
                        email: str = Form(...),
                        file: UploadFile = File(...)):  # 接收前端传来的图片文件
    password = password_utf.encrypt_password(Password)
    if user_name == '' or user_id == '' or password == '' or email == '':
        return JSONResponse(content={"msg": False, "error": "信息不能为空", "status_code": 400})

    conn = db_pool.get_connection()
    try:
        with conn.cursor() as cursor:
            file_content = await file.read()
            _, _, people_face, similar = face_recognize(file_content)

            if similar is False:
                return JSONResponse(content={"msg": False, "error": "登录失败,请确认人脸是否录入!!!"
                                                                    "\n若已录入请面向摄像头切勿遮挡人脸!!!",
                                             "status_code": 400})
            elif similar == 0:
                return JSONResponse(content={"msg": False, "error": "人员不在库中,请联系管理员!!!", "status_code": 400})
            picture_url = f'http://43.143.229.40:9000/photo5/{random.randint(1, 6)}.jpg'
            if similar and float(similar) > 0.65:
                sql = "SELECT * FROM user WHERE id = '{}'".format(user_id)
                cursor.execute(sql)
                result = cursor.fetchall()
                if result:
                    # 用户已存在
                    return JSONResponse(content={"msg": False, "error": "该用户已注册", "status_code": 400})
                else:
                    # 用户不存在，插入数据
                    sql = "INSERT INTO user (id, name,face,picture,password,email) VALUES (%s, %s, %s, %s, %s, %s)"
                    print(picture_url)
                    cursor.execute(sql, (user_id, user_name, people_face, picture_url, password, email))
                    conn.commit()
                    return JSONResponse(content={"msg": True, "info": "注册成功", "status_code": 200})
            else:
                # 用户不存在，插入数据
                sql = "INSERT INTO user (id, name,face,picture,password,email) VALUES (%s, %s, %s, %s, %s, %s)"
                print(picture_url)
                cursor.execute(sql, (user_id, user_name, people_face, picture_url, password, email))
                conn.commit()
                return JSONResponse(content={"msg": True, "info": "注册成功", "status_code": 200})
    except Exception as e:
        conn.rollback()
        return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})
    finally:
        db_pool.close_connection(conn)


@router.post("/login", summary="账号密码登录", description="账号密码登录", tags=['咔咔'])
async def login(login: ToDoModel.login_user):
    """
    账号密码登录
    """
    User_id = login.User_id
    Password = password_utf.encrypt_password(login.Password)

    conn = db_pool.get_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT * FROM user WHERE id = '{}' AND password = '{}' ".format(User_id, Password)
            cursor.execute(sql)
            result = cursor.fetchall()
            if result:
                Name = result[0][1]
                Picture = result[0][3]
                access_token_expires = timedelta(minutes=token.ACCESS_TOKEN_EXPIRE_MINUTES)
                access_token = token.create_access_token(data={"sub": User_id}, expires_delta=access_token_expires)
                if token.verify_token(access_token) is False:  # 有这样一个方法判断token是否过期
                    return JSONResponse(content={"msg": False, "error": "Token已过期", "status_code": 201})
                else:
                    return JSONResponse(
                        content={"msg": True, "User_id": User_id, "Name": Name, "picture": Picture,
                                 'token': access_token, "status_code": 200})
            else:
                return JSONResponse(content={"msg": False, "error": "学号或密码错误", "status_code": 400})
    except Exception as e:
        return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})
    finally:
        db_pool.close_connection(conn)


@router.get("/get_Token", summary="Token登录", description="Token登录", tags=['咔咔'])
async def protected_route(access_Token: dict = Depends(token.verify_token)):
    """
    Token登录
    """
    if access_Token is None:
        return JSONResponse(content={"msg": False, "error": "Token已过期", "status_code": 201})
    print(access_Token)  # 输出字典 {'sub': '123456'}
    User_id = access_Token.get('sub')  # 提取'sub'的值

    conn = db_pool.get_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT * FROM user WHERE id = '{}'".format(User_id)
            cursor.execute(sql)
            result = cursor.fetchall()

            if result:
                Name = result[0][1]
                Picture = result[0][3]
                access_token_expires = timedelta(minutes=token.ACCESS_TOKEN_EXPIRE_MINUTES)
                access_token = token.create_access_token(data={"sub": User_id}, expires_delta=access_token_expires)
                return JSONResponse(
                    content={"msg": True, "User_id": User_id, "Name": Name, "picture": Picture,
                             'token': access_token, "status_code": 200})
            else:
                return JSONResponse(content={"msg": False, "error": "", "status_code": 400})
    except Exception as e:
        return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})
    finally:
        db_pool.close_connection(conn)


"""

邮箱相关接口=============================================================================

"""


@router.post("/send_email", summary="发送验证码", description="发送邮件,发送验证码", tags=['咔咔'])
async def send_email(email: ToDoModel.get_email):
    """
    发送邮件
    """
    Email = email.Email

    conn = db_pool.get_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT * FROM user WHERE email = '{}'".format(Email)
            cursor.execute(sql)
            result = cursor.fetchone()
            if result:
                security_code = email_send.send_email(Email)
                # 将receiver_email和security_code以key-value形式缓存起来

                cache_code.set_cache(Email, security_code)  # 缓存函数，分别存receiver_email和security_code

                # 发送邮件
                return JSONResponse(content={"msg": True, "info": "验证码已发送至邮箱,请注意查收", "status_code": 200})
            else:
                return JSONResponse(content={"msg": False, "error": "该邮箱未注册", "status_code": 400})
    except Exception as e:
        return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})
    finally:
        db_pool.close_connection(conn)


# 验证验证码
@router.post("/verify_email", summary="验证验证码", description="验证验证码", tags=['咔咔'])
async def verify_email(verify: ToDoModel.check_security_code):
    """
    验证验证码
    """
    try:
        Email = verify.Email
        Security_code = verify.Security_code
        print(Email, Security_code)
        # 验证验证码
        security_code_in_cache = cache_code.get_cache(Email)
        print(security_code_in_cache)

        if security_code_in_cache == Security_code:
            # 执行后续逻辑
            return JSONResponse(content={"msg": True, "info": "验证码正确", "status_code": 200})
        else:
            return JSONResponse(content={"msg": False, "error": "验证码错误或邮箱不正确", "status_code": 400})
    except Exception as e:
        return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})


# 接收验证码和邮箱账号修改密码
@router.post("/modify_password_by_email", summary="找回密码", description="接收验证码和邮箱账号找回密码",
             tags=['咔咔'])
async def modify_password(modify: ToDoModel.modify_password):
    """
    找回密码
    """

    conn = db_pool.get_connection()
    try:
        with conn.cursor() as cursor:
            Password = password_utf.encrypt_password(modify.Password)
            Email = modify.Email
            Security_code = modify.Security_code
            # 验证验证码
            if Security_code == cache_code.get_cache(Email):
                # 修改密码
                print(Password)
                print(Email)
                sql = "UPDATE user SET password = '{}' WHERE email = '{}'".format(Password, Email)
                cursor.execute(sql)
                conn.commit()
                # 缓存修改密码成功
                if cursor.rowcount > 0:
                    return JSONResponse(content={"msg": True, "status_code": 200})
                else:
                    return JSONResponse(content={"msg": False, "error": "修改密码与原密码相同", "status_code": 400})
            else:
                return JSONResponse(content={"msg": False, "error": "验证码错误或邮箱不正确", "status_code": 400})
    except Exception as e:
        conn.rollback()
        return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})
    finally:
        db_pool.close_connection(conn)


@router.post("/change_password", summary="修改密码", description="接收验证码和邮箱账号修改密码",
             tags=['咔咔'])
async def change_password(pd: ToDoModel.change_password, access_Token: dict = Depends(token.verify_token)):
    """
    修改密码
    """
    if access_Token is False:
        return JSONResponse(content={"msg": False, "error": "登录已过期,请重新登录", "status_code": 401})

    conn = db_pool.get_connection()
    password = password_utf.encrypt_password(pd.Password)
    user_id = access_Token.get('sub')
    try:
        with conn.cursor() as cursor:

            sql = "UPDATE user SET password = '{}' WHERE id = '{}'".format(password, user_id)
            cursor.execute(sql)
            conn.commit()
            if cursor.rowcount > 0:
                return JSONResponse(content={"msg": True, 'info': "修改密码成功", "status_code": 200})
            else:
                return JSONResponse(content={"msg": False, "error": "修改密码与原密码相同", "status_code": 400})
    except Exception as e:
        conn.rollback()
        return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})
    finally:
        db_pool.close_connection(conn)


"""
    签到相关接口===    

"""


@router.post("/sign_in", summary="签到", description="签到", tags=['咔咔'])
async def sign_in(file: UploadFile = File(...)):
    """
    签到
    """

    conn = db_pool.get_connection()
    try:
        with conn.cursor() as cursor:
            file_content = await file.read()
            User_id, name, _, similar = face_recognize(file_content)
            if similar is False:
                return JSONResponse(content={"msg": False,
                                             "error": "登录失败,请确认人脸是否录入!!!\n若已录入请面向摄像头切勿遮挡人脸!!!",
                                             "status_code": 400})
            elif similar == 0:
                return JSONResponse(content={"msg": False, "error": "人员不在库中,请联系管理员!!!", "status_code": 400})
            if float(similar) > 0.65:  # 当相似度大于0.65时
                # 向数据库中插入签到记录
                # 获取当前时间
                Current_time = datetime.now()

                # 查询同一天里的最后一次签到记录
                sql = (
                    "SELECT begin_time,end_time FROM sign_time WHERE id = '{}' AND DATE(begin_time) = DATE('{}') ORDER "
                    "BY begin_time DESC LIMIT 1").format(User_id, Current_time)

                cursor.execute(sql)
                result = cursor.fetchall()
                # 数据库中当天没有该用户的签到记录
                if not result:
                    sql_2 = "INSERT INTO sign_time (id,name,begin_time) VALUES ('{}', '{}', '{}')".format(User_id,
                                                                                                          name,
                                                                                                          Current_time)
                    cursor.execute(sql_2)
                    conn.commit()
                    # 先查询，如果没有查到则插入
                    select_sql = (
                        "SELECT COUNT(*) FROM day_time WHERE id = '{}' AND DATE(date) = DATE('{}')"
                    ).format(User_id, Current_time)
                    cursor.execute(select_sql)
                    result = cursor.fetchone()

                    if result[0] == 0:  # 如果没有查到任何行
                        insert_sql = ("INSERT INTO day_time (id, name,description, date,duration) "
                                      "VALUES ('{}', '{}' ,'{}','{}','{}')").format(User_id, name, "无", Current_time,
                                                                                    0)
                        cursor.execute(insert_sql)
                        conn.commit()

                    return JSONResponse(content={"msg": True, "info": "{}签到成功".format(name), "status_code": 200})
                else:

                    being_time = result[0][0]
                    end_time = result[0][1]
                    print(being_time, end_time)
                    #
                    if (being_time is None and end_time is None) or (being_time is not None and end_time is not None):

                        # 向数据库中插入签到记录
                        sql_2 = "INSERT INTO sign_time (id,name,begin_time) VALUES ('{}', '{}', '{}')".format(User_id,
                                                                                                              name,
                                                                                                              Current_time)
                        cursor.execute(sql_2)
                        conn.commit()
                        # 先查询，如果没有查到则插入
                        select_sql = (
                            "SELECT COUNT(*) FROM day_time WHERE id = '{}' AND DATE(date) = DATE('{}')"
                        ).format(User_id, Current_time)
                        cursor.execute(select_sql)
                        result = cursor.fetchone()

                        if result[0] == 0:  # 如果没有查到任何行
                            insert_sql = ("INSERT INTO day_time (id, name, description,date,duration) "
                                          "VALUES ('{}', '{}' ,'{}','{}','{}')").format(User_id, name, "无",
                                                                                        Current_time, 0)
                            cursor.execute(insert_sql)
                            conn.commit()
                        return JSONResponse(
                            content={"msg": True, "info": "{}签到成功".format(name), "status_code": 200})

                    else:
                        # 签到失败，提示用户
                        return JSONResponse(
                            content={"msg": False, "error": "您今天已经签到,请勿重复操作！", "status_code": 400})
            else:
                print("登录失败，提示用户")
                # 登录失败，提示用户
                return JSONResponse(content={"msg": False, "error": "登录失败,请确认人脸是否录入!!!"
                                                                    "\n若已录入请面向摄像头切勿遮挡人脸!!!",
                                             "status_code": 400})

    except Exception as e:
        conn.rollback()
        return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})
    finally:
        db_pool.close_connection(conn)


@router.post("/sign_out", summary="签退", description="签退", tags=['咔咔'])
async def sign_out(access_Token: dict = Depends(token.verify_token)):
    """
    签退
    """
    if access_Token is False:
        return JSONResponse(content={"msg": False, "error": "登录已过期,请重新登录", "status_code": 401})

    conn = db_pool.get_connection()
    User_id = access_Token.get('sub')
    try:
        with conn.cursor() as cursor:
            # 获取当前时间
            Current_time = datetime.now()

            # 查询同一天里的最后一次签到记录
            sql = ("SELECT begin_time, end_time, name FROM sign_time "
                   "WHERE id = %s AND DATE(begin_time) = DATE(%s) "
                   "ORDER BY begin_time DESC LIMIT 1")
            cursor.execute(sql, (User_id, Current_time))
            result = cursor.fetchone()

            if result:
                begin_time, end_time, name = result

                if end_time is not None:
                    return JSONResponse(
                        content={"msg": False, "error": "您今天已经签退,请勿重复操作！", "status_code": 400})

                now_time = datetime.now()
                # 计算时间差
                duration = round((now_time - begin_time).total_seconds() / 3600, 2)  # 转换为小时并保留两位小数
                if duration > 0:
                    # 更新数据库
                    update_sql = (
                        "UPDATE sign_time SET end_time = '{}', duration = '{}', status = '{}' WHERE id = '{}' AND "
                        "begin_time = '{}'").format(Current_time, duration, "已签退", User_id, begin_time)
                    cursor.execute(update_sql)

                    # 先尝试更新，如果没有更新到行数，则插入
                    update_sql = (
                        "UPDATE day_time SET duration = duration + '{}' WHERE id = '{}' AND DATE(date) = DATE('{"
                        "}')").format(duration, User_id, Current_time)
                    cursor.execute(update_sql)

                    if cursor.rowcount == 0:  # 如果没有更新到任何行
                        insert_sql = ("INSERT INTO day_time (id, name, description,date, duration) "
                                      "VALUES ('{}', '{}' ,'{}','{}','{}')").format(User_id, name, "无", Current_time,
                                                                                    duration)
                        cursor.execute(insert_sql)

                    # # 如果记录存在，则更新其时长
                    # update_week_time_sql = ("UPDATE week_time SET duration = duration +'{}' "
                    #                         "WHERE id = '{}' AND  YEARWEEK(date) = YEARWEEK(NOW())").format(duration,
                    #                                                                                         User_id)
                    # cursor.execute(update_week_time_sql)
                    # 如果记录存在，则更新其时长
                    update_week_time_sql = ("""UPDATE week_time SET duration = duration +'{}'WHERE id = '{}' 
                                            AND date >= CASE
                                                WHEN WEEKDAY(CURDATE()) IN (0, 1, 2) THEN DATE_SUB(CURDATE(), INTERVAL (WEEKDAY(CURDATE()) + 4) DAY)
                                                ELSE DATE_SUB(CURDATE(), INTERVAL (WEEKDAY(CURDATE()) - 3) DAY)
                                            END""").format(duration, User_id)

                    cursor.execute(update_week_time_sql)
                    if cursor.rowcount == 0:  # 如果没有更新到任何行
                        # 如果记录不存在，则插入新记录
                        insert_week_time_sql = ("INSERT INTO week_time (id, name, date, duration) VALUES"
                                                " ('{}', '{}', '{}', '{}')").format(User_id, name, Current_time,
                                                                                    duration)
                        cursor.execute(insert_week_time_sql)

                    conn.commit()

                    return JSONResponse(content={"msg": True, "info": "{}签退成功".format(name), "status_code": 200})
                else:
                    delete_sql = ("DELETE FROM sign_time WHERE id = '{}' AND  DATE(begin_time) = DATE(CURDATE()) "
                                  "ORDER BY begin_time DESC LIMIT 1").format(User_id)
                    cursor.execute(delete_sql)
                    conn.commit()
                    return JSONResponse(
                        content={"msg": False, "error": "学习时长为0,不予记录！", "status_code": 400})
            else:
                return JSONResponse(content={"msg": False, "error": "您今天还未签到,请先签到！", "status_code": 400})

    except Exception as e:
        conn.rollback()
        return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})
    finally:
        db_pool.close_connection(conn)


@router.post("/face_sign_out", summary="人脸签退", description="人脸签退", tags=['咔咔'])
async def face_sign_out(file: UploadFile = File(...)):
    """
    人脸签退
    """

    conn = db_pool.get_connection()
    try:
        with conn.cursor() as cursor:
            file_content = await file.read()
            User_id, name, _, similar = face_recognize(file_content)
            if similar is False:
                return JSONResponse(content={"msg": False,
                                             "error": "登录失败,请确认人脸是否录入!!!\n若已录入请面向摄像头切勿遮挡人脸!!!",
                                             "status_code": 400})
            elif similar == 0:
                return JSONResponse(content={"msg": False, "error": "人员不在库中,请联系管理员!!!", "status_code": 400})
            if float(similar) > 0.65:  # 当相似度大于0.65时
                # 获取当前时间
                Current_time = datetime.now()

                # 查询同一天里的最后一次签到记录
                sql = ("SELECT begin_time, end_time, name FROM sign_time "
                       "WHERE id = %s AND DATE(begin_time) = DATE(%s) "
                       "ORDER BY begin_time DESC LIMIT 1")
                cursor.execute(sql, (User_id, Current_time))
                result = cursor.fetchone()

                if result:
                    begin_time, end_time, name = result

                    if end_time is not None:
                        return JSONResponse(
                            content={"msg": False, "error": "您今天已经签退,请勿重复操作！", "status_code": 400})

                    now_time = datetime.now()
                    # 计算时间差
                    duration = round((now_time - begin_time).total_seconds() / 3600, 2)  # 转换为小时并保留两位小数

                    if duration > 0:

                        # 更新数据库
                        update_sql = (
                            "UPDATE sign_time SET end_time = '{}', duration = '{}', status = '{}' WHERE id = '{}' AND "
                            "begin_time = '{}'").format(Current_time, duration, "已签退", User_id, begin_time)
                        cursor.execute(update_sql)
                        # 先尝试更新，如果没有更新到行数，则插入
                        update_sql = (
                            "UPDATE day_time SET duration = duration + '{}' WHERE id = '{}' AND DATE(date) = DATE('{"
                            "}')").format(duration, User_id, Current_time)
                        cursor.execute(update_sql)

                        if cursor.rowcount == 0:  # 如果没有更新到任何行
                            insert_sql = ("INSERT INTO day_time (id, name, description,date, duration) "
                                          "VALUES ('{}', '{}','{}','{}','{}')").format(User_id, name, "无",
                                                                                       Current_time,
                                                                                       duration)
                            cursor.execute(insert_sql)

                        # # 如果记录存在，则更新其时长
                        # update_week_time_sql = ("UPDATE week_time SET duration = duration +'{}' "
                        #                         "WHERE id = '{}' AND  YEARWEEK(date) = YEARWEEK(NOW())").format(
                        #     duration,
                        #     User_id)
                        # 如果记录存在，则更新其时长
                        update_week_time_sql = ("""UPDATE week_time SET duration = duration +'{}'WHERE id = '{}' 
                                                AND date >= CASE
                                                    WHEN WEEKDAY(CURDATE()) IN (0, 1, 2) THEN DATE_SUB(CURDATE(), INTERVAL (WEEKDAY(CURDATE()) + 4) DAY)
                                                    ELSE DATE_SUB(CURDATE(), INTERVAL (WEEKDAY(CURDATE()) - 3) DAY)
                                                END""").format(duration, User_id)

                        cursor.execute(update_week_time_sql)
                        if cursor.rowcount == 0:  # 如果没有更新到任何行
                            # 如果记录不存在，则插入新记录
                            insert_week_time_sql = ("INSERT INTO week_time (id, name, date, duration) VALUES"
                                                    " ('{}', '{}', '{}', '{}')").format(User_id, name, Current_time,
                                                                                        duration)
                            cursor.execute(insert_week_time_sql)

                        conn.commit()
                        return JSONResponse(
                            content={"msg": True, "info": "{}签退成功".format(name), "status_code": 200})
                    else:
                        delete_sql = ("DELETE FROM sign_time WHERE id = '{}' AND  DATE(begin_time) = DATE(CURDATE()) "
                                      "ORDER BY begin_time DESC LIMIT 1").format(User_id)
                        cursor.execute(delete_sql)
                        conn.commit()
                        return JSONResponse(
                            content={"msg": False, "error": "学习时长为0,不予记录！", "status_code": 400})
                else:
                    return JSONResponse(content={"msg": False, "error": "您今天还未签到,请先签到！", "status_code": 400})
            else:
                return JSONResponse(content={"msg": False, "error": "登录失败,请确认人脸是否录入!!!"
                                                                    "\n若已录入请面向摄像头切勿遮挡人脸!!!",
                                             "status_code": 400})

    except Exception as e:
        conn.rollback()
        return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})

    finally:
        db_pool.close_connection(conn)


@router.get("/get_all_study_time", summary="获取所有人一天的学习排名", description="获取所有人一天的学习排名",
            tags=['咔咔'])
async def get_all_study_time(access_Token: dict = Depends(token.verify_token)):
    """
    获取所有人一天的学习排名
    return:
        {
            "msg": True,
            "info": {
                "id": "123456",
                "name": "张三",
                "day_duration": 10,
                "picture": "http://43.143.229.40:9000/photo/1.jpg",
            },
            "status_code": 200
        }
    """
    if access_Token is False:
        return JSONResponse(content={"msg": False, "error": "登录已过期,请重新登录", "status_code": 401})

    conn = db_pool.get_connection()
    try:
        with conn.cursor() as cursor:
            # 获取用户信息
            cursor.execute("SELECT id, name, picture FROM user")
            results = cursor.fetchall()

            if not results:
                return JSONResponse(content={"msg": False, "error": "用户信息获取失败", "status_code": 400})

            user_info = [{"id": user[0], "name": user[1], "duration": 0, "picture": user[2], "description": ""}
                         for user in results]

            # 查询今天签到记录
            cursor.execute(
                "SELECT id, begin_time FROM sign_time WHERE DATE(begin_time) = CURDATE() AND end_time IS NULL")
            sign_in_records = cursor.fetchall()

            current_time = datetime.now()
            duration_info = {user["id"]: 0 for user in user_info}  # 初始化学习时长字典
            description_info = {user["id"]: "无" for user in user_info}  # 初始化描述字典

            if sign_in_records:
                for user_id, begin_time in sign_in_records:
                    # 计算持续时间
                    duration = (Decimal((current_time - begin_time).total_seconds()) / Decimal(3600)).quantize(
                        Decimal('0.00'), rounding=ROUND_DOWN)

                    duration_info[user_id] += float(duration)

                    # 查询今天的学习时长
            cursor.execute("SELECT id,duration,description FROM day_time WHERE DATE(date) = CURDATE()")
            day_time_records = cursor.fetchall()

            for record in day_time_records:
                user_id, day_duration, description = record
                duration_info[user_id] += round(day_duration, 2)  # 累加今天的学习时长
                description_info[user_id] = description  # 记录描述

            # 合并学习时长和描述
            for user in user_info:
                user["duration"] = round(duration_info[user["id"]], 2)  # 保留两位小数
                user["description"] = description_info[user["id"]]

            # 排序
            user_info.sort(key=lambda x: x["duration"], reverse=True)
            return JSONResponse(content={"msg": True, "info": user_info, "status_code": 200})

    except Exception as e:
        return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})
    finally:
        db_pool.close_connection(conn)


@router.get("/sunday_get_week_all_study_time", summary="获取所有人一周的学习排名",
            description="获取所有人一周的学习排名",
            tags=['咔咔'])
async def sunday_get_week_all_study_time(access_Token: dict = Depends(token.verify_token)):
    """
    获取所有人一周的学习排名,从周日开始
    """
    if access_Token is False:
        return JSONResponse(content={"msg": False, "error": "登录已过期,请重新登录", "status_code": 401})

    conn = db_pool.get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, name, picture FROM user")
            results = cursor.fetchall()
            if not results:
                return JSONResponse(content={"msg": False, "error": "用户信息获取失败", "status_code": 400})

            # 初始化用户信息
            user_info = [{"id": user[0], "name": user[1], "duration": 0, "picture": user[2]} for user in results]
            #
            # # 查询本周内的签到记录
            # cursor.execute(
            #     "SELECT id, begin_time FROM sign_time WHERE YEARWEEK(begin_time) = YEARWEEK(NOW()) AND end_time IS NULL")
            # sign_in_records = cursor.fetchall()
            # 查询当天的签到记录（begin_time 为当天且 end_time 为 NULL）
            cursor.execute(
                "SELECT id, begin_time FROM sign_time WHERE DATE(begin_time) = CURDATE() AND end_time IS NULL")
            sign_in_records = cursor.fetchall()

            current_time = datetime.now()
            duration_info = {user["id"]: 0 for user in user_info}  # 初始化学习时长字典

            # 计算签到用户的学习时长
            for user_id, begin_time in sign_in_records:
                duration = (Decimal((current_time - begin_time).total_seconds()) / Decimal(3600)).quantize(
                    Decimal('0.00'), rounding=ROUND_DOWN)
                duration_info[user_id] += float(duration)

            # 查询本周的学习时长
            cursor.execute("SELECT id, duration FROM week_time WHERE YEARWEEK(date) = YEARWEEK(NOW())")
            week_time_records = cursor.fetchall()

            # 将本周学习时长添加到用户信息
            for user_id, week_duration in week_time_records:
                duration_info[user_id] += round(week_duration, 2)

            for user in user_info:
                user["duration"] = round(duration_info[user["id"]], 2)  # 保留两位小数
            # 排序
            user_info.sort(key=lambda x: x["duration"], reverse=True)
            return JSONResponse(content={"msg": True, "info": user_info, "status_code": 200})

    except Exception as e:
        return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})
    finally:
        db_pool.close_connection(conn)


@router.get("/get_week_all_study_time", summary="获取所有人一周的学习排名,从周三开始",
            description="获取所有人一周的学习排名,从周三开始",
            tags=['咔咔'])
async def get_week_all_study_time(access_Token: dict = Depends(token.verify_token)):
    """
    获取所有人一周的学习排名,从周三开始
    """
    if access_Token is False:
        return JSONResponse(content={"msg": False, "error": "登录已过期,请重新登录", "status_code": 401})

    conn = db_pool.get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, name, picture FROM user")
            results = cursor.fetchall()
            if not results:
                return JSONResponse(content={"msg": False, "error": "用户信息获取失败", "status_code": 400})

            # 初始化用户信息
            user_info = [{"id": user[0], "name": user[1], "duration": 0, "picture": user[2]} for user in results]

            # 查询本周内的签到记录
            cursor.execute(
                "SELECT id, begin_time FROM sign_time WHERE DATE(begin_time) = CURDATE() AND end_time IS NULL")
            sign_in_records = cursor.fetchall()

            current_time = datetime.now()
            duration_info = {user["id"]: 0 for user in user_info}  # 初始化学习时长字典

            # 计算签到用户的学习时长
            for user_id, begin_time in sign_in_records:
                duration = (Decimal((current_time - begin_time).total_seconds()) / Decimal(3600)).quantize(
                    Decimal('0.00'), rounding=ROUND_DOWN)
                duration_info[user_id] += float(duration)

            # 查询在上周四到本周三内的学习时长（包括上周四和下周三）

            cursor.execute("""SELECT id, duration FROM week_time 
                            WHERE date >= CASE
                                WHEN WEEKDAY(CURDATE()) IN (0, 1, 2) THEN DATE_SUB(CURDATE(), INTERVAL (WEEKDAY(CURDATE()) + 4) DAY)
                                ELSE DATE_SUB(CURDATE(), INTERVAL (WEEKDAY(CURDATE()) - 3) DAY)
                            END
                            AND date <= NOW();
                            """)

            week_time_records = cursor.fetchall()

            # 将本周学习时长添加到用户信息
            for user_id, week_duration in week_time_records:
                duration_info[user_id] += round(week_duration, 2)

            for user in user_info:
                user["duration"] = round(duration_info[user["id"]], 2)  # 保留两位小数
            # 排序
            user_info.sort(key=lambda x: x["duration"], reverse=True)
            return JSONResponse(content={"msg": True, "info": user_info, "status_code": 200})

    except Exception as e:
        return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})
    finally:
        db_pool.close_connection(conn)


@router.get("/get_one_study_time", summary="获取一个人七天的学习时长",
            description="获取一个人七天的学习时长",
            tags=['咔咔'])
async def get_one_study_time(access_Token: dict = Depends(token.verify_token)):
    """
    获取一个人七天的学习时长
    """
    if access_Token is False:
        return JSONResponse(content={"msg": False, "error": "登录已过期,请重新登录", "status_code": 401})

    conn = db_pool.get_connection()
    User_id = access_Token.get('sub')
    try:
        with conn.cursor() as cursor:
            # 查询用户信息
            sql_1 = "SELECT id, name, picture FROM user WHERE id = '{}'".format(User_id)
            cursor.execute(sql_1)
            result1 = cursor.fetchone()

            if not result1:
                return JSONResponse(content={"msg": False, "error": "用户信息获取失败", "status_code": 400})

            # 查询day_time表中该用户14天的学习时长,日期,心得不包括今天的记录
            sql_2 = ("SELECT DATE(date), duration, description FROM day_time WHERE id = '{}' AND DATE(date) NOT IN ("
                     "CURDATE()) AND DATE(date) >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)").format(User_id)
            cursor.execute(sql_2)
            result = cursor.fetchall()
            date = [date.strftime("%m-%d") for date, duration, description in result]  # 使用列表生成式
            duration = [duration for date, duration, description in result]

            return JSONResponse(content={"msg": True, "date": date, "duration": duration, "status_code": 200})

    except Exception as e:
        return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})

    finally:
        db_pool.close_connection(conn)


@router.post("/upload_file", summary="上传/修改头像", description="上传/修改头像", tags=['咔咔'])
async def upload_file(file: UploadFile = File(...), access_Token: dict = Depends(token.verify_token)):
    """
    上传/修改头像
    """
    if not access_Token:
        return JSONResponse(content={"msg": False, "error": "登录已过期,请重新登录", "status_code": 401})

    User_id = access_Token.get('sub')

    conn = db_pool.get_connection()
    try:
        with conn.cursor() as cursor:
            sql_select = "SELECT picture FROM user WHERE id = '{}'".format(User_id)
            cursor.execute(sql_select)
            result = cursor.fetchone()

            if result:
                file_name = result[0].split('/')[-1]
            else:
                file_name = None

            Bucket_name = "photo"
            # 上传文件的方法返回文件路径
            file_path = upload_files(file)
            # 时间戳
            timestamp = int(datetime.now().timestamp())
            object_name = f"{timestamp}_{User_id}_{file.filename}"
            content_type = file.content_type

            # 将文件上传任务交给线程池
            if file_name:
                msg, msg2 = await Threading_await.upload_file_to_minion_bag(Bucket_name, file_name, object_name,
                                                                            file_path,
                                                                            content_type)
                if not (msg and msg2):
                    return JSONResponse(content={"msg": False, "error": "上传失败", "status_code": 400})
            else:
                msg = await Threading_await.upload_file_to_minion_bag_2(Bucket_name, object_name, file_path,
                                                                        content_type)
                if not msg:
                    return JSONResponse(content={"msg": False, "error": "上传失败", "status_code": 400})

            os.remove(file_path)
            file_url = f'http://43.143.229.40:9000/{Bucket_name}/{object_name}'
            # 更新用户头像
            sql = "UPDATE user SET picture = '{}' WHERE id = '{}'".format(file_url, User_id)
            cursor.execute(sql)
            conn.commit()
            return JSONResponse(content={"msg": True, "info": {"file_url": file_url}, "status_code": 200})

    except Exception as e:
        conn.rollback()
        return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})
    finally:
        db_pool.close_connection(conn)


# 添加每日心得
@router.post("/add_day_description", summary="添加每日心得", description="添加每日心得", tags=['咔咔'])
async def add_day_description(day_description: ToDoModel.description, access_Token: dict = Depends(token.verify_token)):
    """
    添加每日心得
    """
    if access_Token is False:
        return JSONResponse(content={"msg": False, "error": "登录已过期,请重新登录", "status_code": 401})

    conn = db_pool.get_connection()  # 获取数据库连接

    description = day_description.description
    # 获取用户id
    User_id = access_Token.get('sub')

    try:
        with conn.cursor() as cursor:
            # 更新day_time表只要今天的记录
            day_time = datetime.now()
            sql = "UPDATE day_time SET description = '{}' WHERE id = '{}' AND DATE(date) = '{}'".format(description,
                                                                                                        User_id,
                                                                                                        day_time.date())
            cursor.execute(sql)
            conn.commit()
            if cursor.rowcount == 0:
                return JSONResponse(content={"msg": False, "error": "今日未签到，无法添加心得", "status_code": 400})
            return JSONResponse(content={"msg": True, "description": description, "status_code": 200})

    except Exception as e:
        conn.rollback()
        return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})
    finally:
        db_pool.close_connection(conn)


# 现场情况
@router.post("/add_live_situation", summary="现场情况", description="现场情况", tags=['咔咔'])
async def add_live_situation(access_Token: dict = Depends(token.verify_token)):
    """
    现场情况
    """
    if access_Token is False:
        return JSONResponse(content={"msg": False, "error": "登录已过期,请重新登录", "status_code": 401})

    conn = db_pool.get_connection()  # 获取数据库连接

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, name, picture FROM user")
            results = cursor.fetchall()
            if not results:
                return JSONResponse(content={"msg": False, "error": "用户信息获取失败", "status_code": 400})
            # 初始化用户信息
            user_info = [{"id": user[0], "name": user[1], "picture": user[2], "bool_status": False, "status": ""} for
                         user
                         in results]

            # 查询今天签到记录
            cursor.execute(
                "SELECT id FROM sign_time WHERE DATE(begin_time) = CURDATE() AND end_time IS NULL")
            results2 = cursor.fetchall()
            status_info = {user["id"]: "离开" for user in user_info}  # 初始化状态字典
            bool_status_info = {user["id"]: False for user in user_info}  # 初始化状态字典
            for user_id in results2:
                status_info[user_id[0]] = '在场'
                bool_status_info[user_id[0]] = True
            for user in user_info:
                user["status"] = status_info[user["id"]]
                user["bool_status"] = bool_status_info[user["id"]]
                # 排序将在场的用户排在前面
            user_info.sort(key=lambda x: 0 if x["status"] == "在场" else 1)

            return JSONResponse(content={"msg": True, "info": user_info, "status_code": 200})

    except Exception as e:
        conn.rollback()
        return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})
    finally:
        db_pool.close_connection(conn)


# 删除用户
@router.delete("/delete_user", summary="删除用户", description="删除用户", tags=['咔咔'])
async def delete_user(access_Token: dict = Depends(token.verify_token)):
    """
    删除用户
    """
    if access_Token is False:
        return JSONResponse(content={"msg": False, "error": "登录已过期,请重新登录", "status_code": 401})

    conn = db_pool.get_connection()  # 获取数据库连接
    # 获取用户id
    User_id = access_Token.get('sub')
    try:
        with conn.cursor() as cursor:
            sql = "SELECT picture FROM user WHERE id = '{}'".format(User_id)
            cursor.execute(sql)
            result = cursor.fetchall()
            # 删除用户

            sql5 = "DELETE FROM user WHERE id = '{}'".format(User_id)
            sql2 = "DELETE FROM sign_time WHERE id = '{}'".format(User_id)
            sql3 = "DELETE FROM day_time WHERE id = '{}'".format(User_id)
            sql4 = "DELETE FROM week_time WHERE id = '{}'".format(User_id)
            cursor.execute(sql5)
            cursor.execute(sql2)
            cursor.execute(sql3)
            cursor.execute(sql4)
            # 删除头像(不存在没有头像的用户)
            if result:
                picture = result[0][0]
                Bucket_name = "photo"
                object_name = picture.split('/')[-1]
                await Threading_await.delete_file_from_minion_bag(Bucket_name, object_name)
                conn.commit()
                return JSONResponse(content={"msg": True, "info": "删除成功", "status_code": 200})

    except Exception as e:
        conn.rollback()
        return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})
    finally:
        db_pool.close_connection(conn)


# 删除用户
@router.delete("/delete_user_by_id", summary="删除用户", description="删除用户", tags=['咔咔'])
async def delete_user_by_id(User_id: int):
    """
    删除用户
    """

    conn = db_pool.get_connection()  # 获取数据库连接

    try:
        with conn.cursor() as cursor:
            sql = "SELECT picture FROM user WHERE id = '{}'".format(User_id)
            cursor.execute(sql)
            result = cursor.fetchall()
            # 删除用户

            sql5 = "DELETE FROM user WHERE id = '{}'".format(User_id)
            sql2 = "DELETE FROM sign_time WHERE id = '{}'".format(User_id)
            sql3 = "DELETE FROM day_time WHERE id = '{}'".format(User_id)
            sql4 = "DELETE FROM week_time WHERE id = '{}'".format(User_id)
            cursor.execute(sql5)
            cursor.execute(sql2)
            cursor.execute(sql3)
            cursor.execute(sql4)
            # 删除头像(不存在没有头像的用户)
            if result:
                picture = result[0][0]
                Bucket_name = "photo"
                object_name = picture.split('/')[-1]
                await Threading_await.delete_file_from_minion_bag(Bucket_name, object_name)
                conn.commit()
                return JSONResponse(content={"msg": True, "info": "删除成功", "status_code": 200})

    except Exception as e:
        conn.rollback()
        return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})
    finally:
        db_pool.close_connection(conn)
