
from pydantic import BaseModel
from typing import Optional


class register_user(BaseModel):
    """
    User_id:用户ID
    Name:用户名
    Password:密码
    Phone:手机号
    """
    User_id: Optional[str] = None
    Name: Optional[str] = None
    Password: Optional[str] = None
    Email: Optional[str] = None


class login_user(BaseModel):
    """
    Name:用户名
    Password:密码
    """
    User_id: Optional[str] = None
    Password: Optional[str] = None


class public_bucket(BaseModel):
    """
    Bucket_name:桶名称
    """
    bucket_name: Optional[str] = None


class file(BaseModel):
    """
    Mission_id:任务ID
    """
    Mission_id: Optional[str] = None


class folder(BaseModel):
    """
    Mission_id:  任务ID
    folder_name: 文件夹名称
    """
    Mission_id: Optional[str] = None
    folder_name: Optional[str] = None


class get_email(BaseModel):
    """
    Email:邮箱
    """
    Email: Optional[str] = None


class check_security_code(BaseModel):
    """
    Security_code:验证码
    """
    Email: Optional[str] = None
    Security_code: Optional[str] = None


class modify_password(BaseModel):
    """
    Password:密码
    """
    Password: Optional[str] = None
    Email: Optional[str] = None
    Security_code: Optional[str] = None


class change_password(BaseModel):
    """
    Password:密码
    """
    Password: Optional[str] = None


class login_token(BaseModel):
    """
    Token:登录token
    """
    Token: Optional[str] = None


class create_folder(BaseModel):
    """
    folder_name:文件夹名称
    remark:备注
    """
    folder_name: Optional[str] = None
    remark: Optional[str] = None


class get_file_url(BaseModel):
    """
    File_name:文件名称
    """
    File_id: Optional[str] = None


class delete_file(BaseModel):
    """
    File_name:文件名称
    """
    File_name: Optional[str] = None


class UploadFileModel(BaseModel):
    """
    Folder_id:文件夹ID
    """
    Folder_id: Optional[str] = None


class get_user_name(BaseModel):
    """
    User_name:用户名
    """
    User_name: Optional[str] = None


class get_ppt_time(BaseModel):
    """
    Start_time:开始时间
    End_time:结束时间
    """
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class set_permission(BaseModel):
    """
    Permission:权限
    Folder_id:文件ID
    """
    permission: Optional[str] = None
    Folder_id: Optional[str] = None


class get_file_list(BaseModel):
    """
    Folder_id:文件夹ID
    """
    Folder_id: Optional[str] = None


class description(BaseModel):
    """
    daty:日期
    Description:描述
    """
    description: Optional[str] = None
