"""
发送邮件验证码
"""
import smtplib
import random
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# 生成随机的6位验证码

def generate_security_code():
    return ''.join(random.choices('0123456789', k=6))


def base64_encode_nickname(nickname):
    # 编码为base64
    encoded_bytes = base64.b64encode(nickname.encode('utf-8'))
    encoded_str = encoded_bytes.decode('utf-8')
    # 构造最终形式
    return f"=?UTF-8?B?{encoded_str}?="


def send_email(receiver_email):
    # 邮箱账号信息
    sender_email = "2976699191@qq.com"
    password = "lrqropzxnbmydcff"
    security_code = generate_security_code()  # 使用随机生成的验证码
    # 创建邮件
    message = MIMEMultipart()
    nickname = "咔咔"  # 中文昵称
    encoded_nickname = base64_encode_nickname(nickname)

    # 设置邮件头部
    message["From"] = f"{encoded_nickname} <{sender_email}>"
    message["To"] = receiver_email
    message["Subject"] = f"咔咔 -邮箱验证码：{security_code}"
    # 邮件正文
    body = f"这是您的验证码:{security_code}请尽快进行验证。此邮件为系统邮件，请勿回复。"
    message.attach(MIMEText(body, "plain"))

    # 连接到QQ邮箱的SMTP服务器
    server = smtplib.SMTP("smtp.qq.com", 587)
    server.starttls()
    try:
        server.login(sender_email, password)
    except smtplib.SMTPAuthenticationError as e:
        print("登录失败，请检查邮箱账号和授权码是否正确。")
        server.quit()
        exit()

    # 发送邮件
    text = message.as_string()
    server.sendmail(sender_email, receiver_email, text)

    # 关闭连接
    server.quit()

    print("邮件发送成功")
    return security_code


def send_warning_email(receiver_email):
    # 邮箱账号信息
    sender_email = "2976699191@qq.com"
    password = "lrqropzxnbmydcff"
    # 创建邮件
    message = MIMEMultipart()
    nickname = "咔咔"  # 中文昵称
    encoded_nickname = base64_encode_nickname(nickname)

    # 设置邮件头部
    message["From"] = f"{encoded_nickname} <{sender_email}>"
    message["To"] = receiver_email
    message["Subject"] = f"咔咔 -签退警告"
    # 邮件正文
    body = f"签退超时，本次签到记录清零，保留未签退记录,给予一次警告。此邮件为系统邮件，请勿回复。"
    message.attach(MIMEText(body, "plain"))

    # 连接到QQ邮箱的SMTP服务器
    server = smtplib.SMTP("smtp.qq.com", 587)
    server.starttls()
    try:
        server.login(sender_email, password)
    except smtplib.SMTPAuthenticationError as e:
        print("登录失败，请检查邮箱账号和授权码是否正确。")
        server.quit()
        exit()

    # 发送邮件
    text = message.as_string()
    server.sendmail(sender_email, receiver_email, text)

    # 关闭连接
    server.quit()

    print("邮件发送成功")
    return True
