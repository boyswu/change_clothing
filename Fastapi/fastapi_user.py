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


@router.post("/change_clothes/register", summary="注册用户", description="注册用户", tags=['奇迹衣衣'])
async def register_user(register: ToDoModel.register_user_phone):
    """
    注册用户
    """
    user_phone = register.Phone
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

            bucket_creation_result = minion_bag.CreateBucket(user_phone)
            if not bucket_creation_result:
                error_msg = "桶名重复" if bucket_creation_result is None else "创建桶失败"
                return JSONResponse(content={"msg": False, "error": error_msg, "status_code": 400})

            if not minion_bag.create_folder(user_phone, 'image'):
                return JSONResponse(content={"msg": False, "error": "创建图片文件夹失败", "status_code": 400})

            if not minion_bag.create_folder(user_phone, 'chat_record'):
                return JSONResponse(content={"msg": False, "error": "创建对话记录文件夹失败", "status_code": 400})

            if not minion_bag.create_folder(user_phone, 'head_portrait'):
                return JSONResponse(content={"msg": False, "error": "创建头像文件夹失败", "status_code": 400})

            return JSONResponse(content={"msg": True, "data": "注册成功", "status_code": 200})

    except Exception as e:
        return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})
    finally:
        db_pool.close_connection(conn)


@router.post("/change_clothes/login", summary="账号密码登录", description="账号密码登录", tags=['奇迹衣衣'])
async def login(login: ToDoModel.login_user_phone):
    """
    账号密码登录
    """
    user_phone = login.Phone
    Password = password_utf.encrypt_password(login.Password)

    conn = db_pool.get_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT * FROM user WHERE phone = '{}' AND password = '{}' ".format(user_phone, Password)
            print(sql)
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
    Email = verify.Email
    Security_code = verify.Security_code
    try:

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
    Password = password_utf.encrypt_password(modify.Password)
    Email = modify.Email
    Security_code = modify.Security_code
    conn = db_pool.get_connection()
    try:
        with conn.cursor() as cursor:

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
            sql_select = "SELECT head_portrait FROM user WHERE phone = '{}'".format(user_phone)
            cursor.execute(sql_select)
            result = cursor.fetchone()

            if result:
                file_name = result[0].split('/')[-1]
            else:
                file_name = None

            Bucket_name = user_phone
            # 时间戳
            timestamp = int(datetime.now().timestamp())
            # 上传文件的方法返回文件路径
            file_path = upload_files(file, timestamp)

            object_name = f"{'head_portrait'}/{timestamp}_{file.filename}"
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
            sql = "UPDATE user SET head_portrait = '{}' WHERE phone = '{}'".format(file_url, user_phone)
            cursor.execute(sql)
            conn.commit()
            return JSONResponse(content={"msg": True, "info": {"file_url": file_url}, "status_code": 200})

    except Exception as e:
        conn.rollback()
        return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})
    finally:
        db_pool.close_connection(conn)


@router.post("/change_clothes/get_file", summary="获取模版照片",
             description="1.fit_type只接受，FULL_BODY：全身换装，HALF_BODY:半身换装，两种类型参数。"
                         "2.models、tops、pants参数分别为模型、上衣、裤子图片。"
                         "3.全身换装：可不上传裤子,仅上传连衣裙图片(上装必须上传)。半身换装：仅支持上传上装图片,模特照片里的裤子会保留。",
             tags=['奇迹衣衣'])
async def get_file(fit_type: str = Form(...), models: UploadFile = File(...), tops: UploadFile = File(...),
                   pants: UploadFile = File(default=None),
                   access_Token: dict = Depends(token.verify_token)):
    """
    获取模版照片
    """
    if not access_Token:
        return JSONResponse(content={"msg": False, "error": "登录已过期,请重新登录", "status_code": 401})
    user_phone = access_Token.get('sub')
    upload_results = []
    # 时间戳
    timestamp = int(datetime.now().timestamp())
    # 转成字符串
    folder_name = datetime.fromtimestamp(timestamp).strftime('%Y_%m_%d_%H:%M:%S')
    conn = db_pool.get_connection()
    try:
        # 上传文件的方法返回文件路径
        file_data = [
            {"file": models},
            {"file": tops},
        ]
        if pants:
            file_data.append({"file": pants})

        minion_bag.create_folder(user_phone, folder_name)  # minion的桶里创建文件夹存放三张模板图片以时间戳命名

        for data in file_data:
            file_path = upload_files(data["file"], timestamp)
            object_name = f"{folder_name}/{data['file'].filename}"
            content_type = data['file'].content_type
            msg = await Threading_await.upload_file_to_minion_bag_2(user_phone, object_name, file_path, content_type)
            if not msg:
                return JSONResponse(
                    content={"msg": False, "error": f"上传文件 {data['file'].filename} 失败", "status_code": 400})
            upload_results.append({"file_path": file_path, "object_name": object_name})

        # 删除所有上传成功的本地文件
        for result in upload_results:
            os.remove(result["file_path"])
        upload_results.clear()

        # 构建文件下载链接
        urls = {
            "models_url": f'http://43.143.229.40:9000/{user_phone}/{folder_name}/{file_data[0]["file"].filename}',
            "tops_url": f'http://43.143.229.40:9000/{user_phone}/{folder_name}/{file_data[1]["file"].filename}',
        }
        if pants:
            urls["pants_url"] = f'http://43.143.229.40:9000/{user_phone}/{folder_name}/{file_data[2]["file"].filename}'

        models_url = urls.get("models_url")
        tops_url = urls.get("tops_url")
        pants_url = urls.get("pants_url")

        result_keys = change_clothes_api(fit_type, models_url, tops_url, pants_url)
        with conn.cursor() as cursor:
            sql = ("INSERT INTO file_list (file_id, phone,folder_name) "
                   "VALUES ('{}', '{}', '{}')").format(result_keys, user_phone, folder_name)
            cursor.execute(sql)
            conn.commit()
            if cursor.rowcount == 0:
                print("保存数据库失败")
                minion_bag.delete_folder(user_phone, folder_name)
                return JSONResponse(content={"msg": False, "error": "保存数据库失败", "status_code": 400})
            else:
                return JSONResponse(content={"msg": True, "info": {"result_keys": result_keys}, "status_code": 200})
    except Exception as e:
        print("上传文件失败")
        minion_bag.delete_folder(user_phone, folder_name)
        # 删除所有上传成功的本地文件
        if upload_results:
            for result in upload_results:
                os.remove(result["file_path"])
        conn.rollback()
        return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})
    finally:
        db_pool.close_connection(conn)


@router.post("/change_clothes/get_file_url", summary="获取图片下载链接",
             description="需要传入result_keys以获取图片下载链接",
             tags=['奇迹衣衣'])
async def get_file_url(keys: ToDoModel.result_keys, access_Token: dict = Depends(token.verify_token)):
    """
    获取图片下载链接
    """
    result_keys = keys.key
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
            if result is None:
                return JSONResponse(content={"msg": False, "error": "无历史记录存在", "status_code": 400})
            elif result[0] is not None:
                url = result[0]
                return JSONResponse(content={"msg": True, "info": {"file_url": url}, "status_code": 200})
            else:
                folder_name = result[1]
                url = get_result_api(result_keys)
                if url == 'RUNNING':
                    return JSONResponse(content={"msg": False, "error": "生成图片中，请稍后再试", "status_code": 400})
                elif url is False:
                    return JSONResponse(content={"msg": False, "error": "生成图片失败", "status_code": 400})
                else:
                    file_path = download_url(url, user_phone)
                    if file_path is False:
                        return JSONResponse(content={"msg": False, "error": "下载图片失败", "status_code": 400})
                    # 上传本地文件到minion的桶
                    object_name = await upload_local_file(user_phone, file_path, folder_name)
                    os.remove(file_path)
                    result_url = f"http://43.143.229.40:9000/{user_phone}/{object_name}"
                    if not upload_local_file:
                        return JSONResponse(content={"msg": False, "error": "上传图片失败", "status_code": 400})

                    sql = "UPDATE file_list SET url = '{}' WHERE file_id = '{}'".format(result_url, result_keys)
                    cursor.execute(sql)
                    conn.commit()
                    if cursor.rowcount > 0:
                        return JSONResponse(
                            content={"msg": True, "info": {"file_url": result_url}, "status_code": 200})
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
