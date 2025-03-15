import os
import threading
import random
import asyncio
from decimal import Decimal, ROUND_DOWN
from pathlib import Path
from fastapi import Form, File, UploadFile, Depends, APIRouter
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import Model.ToDoModel as ToDoModel
import Tool.email_send as email_send
import Tool.cache_code as cache_code
import Tool.tokens as token
import Tool.password_utf as password_utf
import Tool.minion_bag as minion_bag
import Tool.Threading_await as Threading_await
# from Tool.face_recognize import face_recognize
from Tool.upload import upload_files
from Tool.downland_url import download_url, upload_local_file
from Tool.API import change_clothes_api, get_result_api
from connect_tool.sql import MySQLConnectionPool

# from Tool.timer_task import run_schedule

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
executor = ThreadPoolExecutor(max_workers=10)  # 线程池最大线程数为10
#
# @router.on_event("startup")
# def startup_event():
#     # 启动调度任务的线程
#     scheduler_thread = threading.Thread(target=run_schedule)
#     scheduler_thread.start()
#     print("调度器已启动")


"""
账户
用户注册、登录、邮箱验证、修改密码相关接口=============================================================================

"""


# TODO: 添加sql和桶存在bug
@router.post("/change_clothes/register", summary="注册用户", description="注册用户", tags=['奇迹衣衣'])
async def register_user(register: ToDoModel.register_user):
    """
    注册用户
    """
    user_phone = register.user_phone
    Name = register.Name
    Password = password_utf.encrypt_password(register.Password)
    Email = register.Email

    # 验证输入信息是否为空
    if not all([user_phone, Name, Password, Email]):
        return JSONResponse(content={"msg": False, "error": "信息不能为空", "status_code": 400})

    conn = db_pool.get_connection()
    try:
        with conn.cursor() as cursor:
            # 验证用户是否存在
            sql = "SELECT * FROM user WHERE phone = %s"
            cursor.execute(sql, (user_phone,))
            if cursor.fetchone():
                return JSONResponse(content={"msg": False, "error": "用户已存在", "status_code": 400})

            # 生成随机图片URL
            picture_url = f'http://43.143.229.40:9000/photo5/{random.randint(1, 6)}.jpg'

            # 插入用户数据
            sql = "INSERT INTO user (phone, user_name, password, email, head_portrait) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(sql, (user_phone, Name, Password, Email, picture_url))
            conn.commit()

            # 创建桶和文件夹
            if not (bucket_creation_result := minion_bag.CreateBucket(user_phone)):
                error_msg = "桶名重复" if bucket_creation_result is None else "创建桶失败"
                return JSONResponse(content={"msg": False, "error": error_msg, "status_code": 400})

            if not minion_bag.create_folder(user_phone, 'image'):
                return JSONResponse(content={"msg": False, "error": "创建图片文件夹失败", "status_code": 400})

            if not minion_bag.create_folder(user_phone, 'chat_record'):
                return JSONResponse(content={"msg": False, "error": "创建对话记录文件夹失败", "status_code": 400})

            return JSONResponse(content={"msg": True, "data": "注册成功", "status_code": 200})

    except Exception as e:
        return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})
    finally:
        db_pool.close_connection(conn)


@router.post("/change_clothes/login", summary="账号密码登录", description="账号密码登录", tags=['奇迹衣衣'])
async def login(login: ToDoModel.login_user):
    """
    账号密码登录
    """
    user_phone = login.user_phone
    Password = password_utf.encrypt_password(login.Password)

    conn = db_pool.get_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT * FROM user WHERE phone = '{}' AND password = '{}' ".format(user_phone, Password)
            cursor.execute(sql)
            result = cursor.fetchall()
            if result:
                Name = result[0][0]
                Picture = result[0][4]
                access_token_expires = timedelta(minutes=token.ACCESS_TOKEN_EXPIRE_MINUTES)
                access_token = token.create_access_token(data={"sub": user_phone}, expires_delta=access_token_expires)
                if token.verify_token(access_token) is False:  # 有这样一个方法判断token是否过期
                    return JSONResponse(content={"msg": False, "error": "Token已过期", "status_code": 201})
                else:
                    return JSONResponse(
                        content={"msg": True, "user_phone": user_phone, "Name": Name, "picture": Picture,
                                 'token': access_token, "status_code": 200})
            else:
                return JSONResponse(content={"msg": False, "error": "手机号或密码错误", "status_code": 400})
    except Exception as e:
        return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})
    finally:
        db_pool.close_connection(conn)


@router.get("/change_clothes/get_Token", summary="Token登录", description="Token登录", tags=['奇迹衣衣'])
async def protected_route(access_Token: dict = Depends(token.verify_token)):
    """
    Token登录
    """
    if access_Token is None:
        return JSONResponse(content={"msg": False, "error": "Token已过期", "status_code": 201})
    print(access_Token)  # 输出字典 {'sub': '123456'}
    user_phone = access_Token.get('sub')  # 提取'sub'的值

    conn = db_pool.get_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT * FROM user WHERE phone = '{}'".format(user_phone)
            cursor.execute(sql)
            result = cursor.fetchall()

            if result:
                Name = result[0][0]
                Picture = result[0][4]
                access_token_expires = timedelta(minutes=token.ACCESS_TOKEN_EXPIRE_MINUTES)
                access_token = token.create_access_token(data={"sub": user_phone}, expires_delta=access_token_expires)
                return JSONResponse(
                    content={"msg": True, "user_phone": user_phone, "Name": Name, "picture": Picture,
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


@router.post("/change_clothes/send_email", summary="发送验证码", description="发送邮件,发送验证码", tags=['奇迹衣衣'])
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
@router.post("/change_clothes/verify_email", summary="验证验证码", description="验证验证码", tags=['奇迹衣衣'])
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
@router.post("/change_clothes/modify_password_by_email", summary="找回密码", description="接收验证码和邮箱账号找回密码",
             tags=['奇迹衣衣'])
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


@router.post("/change_clothes/change_password", summary="修改密码", description="接收验证码和邮箱账号修改密码",
             tags=['奇迹衣衣'])
async def change_password(pd: ToDoModel.change_password, access_Token: dict = Depends(token.verify_token)):
    """
    修改密码
    """
    if access_Token is False:
        return JSONResponse(content={"msg": False, "error": "登录已过期,请重新登录", "status_code": 401})

    conn = db_pool.get_connection()
    password = password_utf.encrypt_password(pd.Password)
    user_phone = access_Token.get('sub')
    try:
        with conn.cursor() as cursor:

            sql = "UPDATE user SET password = '{}' WHERE phone = '{}'".format(password, user_phone)
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


@router.post("/change_clothes/upload_file", summary="上传/修改头像", description="上传/修改头像", tags=['奇迹衣衣'])
async def upload_file(file: UploadFile = File(...), access_Token: dict = Depends(token.verify_token)):
    """
    上传/修改头像
    """
    if not access_Token:
        return JSONResponse(content={"msg": False, "error": "登录已过期,请重新登录", "status_code": 401})

    user_phone = access_Token.get('sub')

    conn = db_pool.get_connection()
    try:
        with conn.cursor() as cursor:
            sql_select = "SELECT picture FROM user WHERE phone = '{}'".format(user_phone)
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
            object_name = f"{timestamp}_{user_phone}_{file.filename}"
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
            sql = "UPDATE user SET picture = '{}' WHERE phone = '{}'".format(file_url, user_phone)
            cursor.execute(sql)
            conn.commit()
            return JSONResponse(content={"msg": True, "info": {"file_url": file_url}, "status_code": 200})

    except Exception as e:
        conn.rollback()
        return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})
    finally:
        db_pool.close_connection(conn)


# TODO:注册时候需要以手机号创建桶，并创建两个文件夹，一个放生成的图片作历史代存区，一个放txt文件记录用户ai对话
# minion建文件夹放置每一次的照片(共三张)生成的图片单独放置在一个文件夹里，文件夹和生成的图片以时间戳命名，并返回文件夹路径
@router.get("/change_clothes/get_file", summary="获取模版照片",
            description="1.fit_type只接受，FULL_BODY：全身换装，HALF_BODY:半身换装，两种类型参数。"
                        "2.上传正身照,上衣照,下装照，并要求照片开头分别命名为：models,tops,pants",
            tags=['奇迹衣衣'])
async def get_file(fit_type: str = Form(...), models: UploadFile = File(...), tops: UploadFile = File(...),
                   pants: UploadFile = File(...),
                   access_Token: dict = Depends(token.verify_token)):
    """
    获取模版照片
    """
    if not access_Token:
        return JSONResponse(content={"msg": False, "error": "登录已过期,请重新登录", "status_code": 401})
    user_phone = access_Token.get('sub')
    # 时间戳
    timestamp = int(datetime.now().timestamp())
    """
        时间格式字符串是否支持
    """
    # 转成字符串
    folder_name = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

    # 上传文件的方法返回文件路径
    file_data = [
        {"file": models},
        {"file": tops},
        {"file": pants},
    ]
    minion_bag.create_folder(user_phone, folder_name)  # minion的桶里创建文件夹存放三张模板图片以时间戳命名

    upload_results = []
    for data in file_data:
        file_path = upload_files(data["file"])
        object_name = f"{folder_name}/{data['file'].filename}"
        content_type = data['file'].content_type

        try:
            msg = await Threading_await.upload_file_to_minion_bag_2(user_phone, object_name, file_path, content_type)
            if not msg:
                return JSONResponse(
                    content={"msg": False, "error": f"上传文件 {data['file'].filename} 失败", "status_code": 400})

            upload_results.append({"file_path": file_path, "object_name": object_name})
        except Exception as e:
            # 移除已经上传成功的文件
            for result in upload_results:
                os.remove(result["file_path"])
            return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})

    # 删除所有上传成功的本地文件
    for result in upload_results:
        os.remove(result["file_path"])

    # 构建文件下载链接
    urls = {
        "models_url": f'http://43.143.229.40:9000/{user_phone}/{folder_name}/{file_data[0]["file"].filename}',
        "tops_url": f'http://43.143.229.40:9000/{user_phone}/{folder_name}/{file_data[1]["file"].filename}',
        "pants_url": f'http://43.143.229.40:9000/{user_phone}/{folder_name}/{file_data[2]["file"].filename}',
    }
    models_url = urls.get("models_url")
    tops_url = urls.get("tops_url")
    pants_url = urls.get("pants_url")
    result_keys = change_clothes_api(fit_type, models_url, tops_url, pants_url)
    url = get_result_api(result_keys)
    conn = db_pool.get_connection()
    try:
        with conn.cursor() as cursor:
            if url is 'RUNNING':
                sql = ("INSERT INTO file_list (file_id, phone,folder_name,url) "
                       "VALUES ('{}', '{}', '{}')").format(result_keys, user_phone, folder_name)
                cursor.execute(sql)
                conn.commit()
                if cursor.rowcount > 0:
                    return JSONResponse(content={"msg": False, "error": "生成图片中，请稍后再试", "status_code": 400})
                else:
                    return JSONResponse(content={"msg": False, "error": "保存数据库失败", "status_code": 400})

            elif url is False:
                minion_bag.delete_folder(user_phone, folder_name)  # minion的桶里删除文件夹
                return JSONResponse(content={"msg": False, "error": "生成图片失败", "status_code": 400})
            else:
                file_path = download_url(url, folder_name)  # folder_name为时间戳字符串
                if file_path is False:
                    return JSONResponse(content={"msg": False, "error": "下载图片失败", "status_code": 400})
                else:
                    # 上传本地文件到minion的桶
                    upload_local_file(user_phone, file_path, folder_name)
                    if not upload_local_file:
                        return JSONResponse(content={"msg": False, "error": "上传图片失败", "status_code": 400})

                    result_url = f"http://43.143.229.40:9000/{'image'}/{'photo'}_{folder_name}"
                    sql = ("INSERT INTO file_list (file_id, phone,folder_name,url) "
                           "VALUES ('{}', '{}', '{}', '{}')").format(result_keys, user_phone, folder_name, result_url)
                    cursor.execute(sql)
                    conn.commit()
                    if cursor.rowcount > 0:
                        return JSONResponse(content={"msg": True, "info": {"file_url": result_url}, "status_code": 200})
                    else:
                        return JSONResponse(content={"msg": False, "error": "上传失败", "status_code": 400})
    except Exception as e:
        conn.rollback()
        return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})
    finally:
        db_pool.close_connection(conn)


@router.get("/change_clothes/get_file_url", summary="获取图片下载链接",
            description="需要传入result_keys以获取图片下载链接",
            tags=['奇迹衣衣'])
async def get_file_url(result_keys: str, access_Token: dict = Depends(token.verify_token)):
    """
    获取图片下载链接
    """
    if not access_Token:
        return JSONResponse(content={"msg": False, "error": "登录已过期,请重新登录", "status_code": 401})
    user_phone = access_Token.get('sub')
    conn = db_pool.get_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT url,folder_name FROM file_list WHERE file_id = '{}'and phone = '{}'".format(result_keys,
                                                                                                      user_phone)
            cursor.execute(sql)
            result = cursor.fetchone()
            url, folder_name = result[0], result[1]
            if url is not None:
                return JSONResponse(content={"msg": True, "info": {"file_url": url}, "status_code": 200})
            else:
                url = get_result_api(result_keys)
                if url is 'RUNNING':
                    return JSONResponse(content={"msg": False, "error": "生成图片中，请稍后再试", "status_code": 400})
                elif url is False:
                    return JSONResponse(content={"msg": False, "error": "生成图片失败", "status_code": 400})
                else:
                    file_path = download_url(url, user_phone)
                    if file_path is False:
                        return JSONResponse(content={"msg": False, "error": "下载图片失败", "status_code": 400})
                    # 上传本地文件到minion的桶
                    upload_local_file(user_phone, file_path, folder_name)
                    if not upload_local_file:
                        return JSONResponse(content={"msg": False, "error": "上传图片失败", "status_code": 400})

                    sql = "UPDATE file_list SET url = '{}' WHERE file_id = '{}'".format(url, result_keys)
                    cursor.execute(sql)
                    conn.commit()
                    if cursor.rowcount > 0:
                        return JSONResponse(
                            content={"msg": True, "info": {"file_url": url}, "status_code": 200})
                    else:
                        return JSONResponse(content={"msg": False, "error": "上传失败", "status_code": 400})

    except Exception as e:
        conn.rollback()
        return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})
    finally:
        db_pool.close_connection(conn)


@router.get("/change_clothes/get_file_list", summary="获取图像列表", description="获取历史图像", tags=['奇迹衣衣'])
async def get_file_list(access_Token: dict = Depends(token.verify_token)):
    """
    获取文件列表
    """
    if not access_Token:
        return JSONResponse(content={"msg": False, "error": "登录已过期,请重新登录", "status_code": 401})
    user_phone = access_Token.get('sub')
    conn = db_pool.get_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT url FROM file_list WHERE phone = '{}'".format(user_phone)
            cursor.execute(sql)
            result = cursor.fetchall()
            if result:
                return JSONResponse(content={"msg": True, "info": {"file_list": result}, "status_code": 200})
            else:
                return JSONResponse(content={"msg": False, "error": "文件列表为空", "status_code": 400})
    except Exception as e:
        conn.rollback()
        return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})
    finally:
        db_pool.close_connection(conn)


# 接入deepseek
@router.post("/change_clothes/get_deepseek_result", summary="DeepSeek聊天接口", description="获取DeepSeek结果",
             tags=['奇迹衣衣'])
async def get_deepseek_result(chat_text: str = Form(...), access_Token: dict = Depends(token.verify_token)):
    """
    获取DeepSeek结果
    """
    if not access_Token:
        return JSONResponse(content={"msg": False, "error": "登录已过期,请重新登录", "status_code": 401})
    user_phone = access_Token.get('sub')
    conn = db_pool.get_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT deepseek_result FROM user WHERE phone = '{}'".format(user_phone)
            cursor.execute(sql)
            result = cursor.fetchone()
            if result:
                deepseek_result = result[0]
                if deepseek_result:
                    return JSONResponse(
                        content={"msg": True, "info": {"deepseek_result": deepseek_result}, "status_code": 200})
                else:
                    return JSONResponse(content={"msg": False, "error": "DeepSeek结果为空", "status_code": 400})
            else:
                return JSONResponse(content={"msg": False, "error": "用户不存在", "status_code": 400})
    except Exception as e:
        conn.rollback()
        return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})
    finally:
        db_pool.close_connection(conn)
