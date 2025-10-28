import requests
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# --- 配置信息 (从环境变量/Secrets 读取) ---
GLADOS_COOKIE = os.environ.get("GLADOS_COOKIE")
SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 465 # SSL 端口
SENDER_EMAIL = os.environ.get("TO_EMAIL") # 使用接收邮箱作为发件人
TO_EMAIL = os.environ.get("TO_EMAIL")
AUTH_CODE = os.environ.get("SMTP_AUTH_CODE") 

# --- 签到函数 ---
def glados_checkin(cookie):
    """执行 GLaDOS 签到操作"""
    
    url = "https://glados.rocks/api/user/checkin"
    headers = {
        "Content-Type": "application/json",
        "Cookie": cookie,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64 ) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    }
    # 签到请求的 body
    payload = {"token": "glados.one"} 

    try:
        # 禁用 SSL 验证以避免证书问题
        response = requests.post(url, headers=headers, data=json.dumps(payload), verify=False, timeout=10)
        response.raise_for_status() # 检查 HTTP 错误
        
        data = response.json()
        
        # 检查签到结果
        if data.get("code") == 0:
            # 签到成功
            message = data.get("message", "GLaDOS 签到成功,但未返回具体消息。")
            return True, message
        else:
            # 签到失败 (例如: 已经签到过)
            message = data.get("message", "GLaDOS 签到失败,未返回具体错误消息。")
            return False, message
            
    except requests.exceptions.RequestException as e:
        return False, f"请求 GLaDOS 签到 API 失败: {e}"
    except json.JSONDecodeError:
        return False, f"GLaDOS 签到 API 返回的响应不是有效的 JSON: {response.text}"
    except Exception as e:
        return False, f"发生未知错误: {e}"

# --- 邮件通知函数 ---
def send_email_notification(to_email, subject, body, auth_code):
    """发送邮件通知"""
    
    sender_email = SENDER_EMAIL
    
    try:
        msg = MIMEText(body, 'plain', 'utf-8')
        msg['From'] = Header(f"GLaDOS 自动签到 <{sender_email}>", 'utf-8')
        msg['To'] = Header(to_email, 'utf-8')
        msg['Subject'] = Header(subject, 'utf-8')

        # 使用 SSL 连接到 QQ 邮箱的 SMTP 服务器
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as smtp:
            # 使用授权码登录
            smtp.login(sender_email, auth_code)
            smtp.sendmail(sender_email, [to_email], msg.as_string())
        print(f"邮件通知已发送至 {to_email}")
    except Exception as e:
        print(f"邮件发送失败: {e}")
        print(f"请检查授权码是否正确,或 POP3/SMTP 服务是否已开启。错误详情: {e}")

# --- 主执行逻辑 ---
if __name__ == "__main__":
    if not GLADOS_COOKIE or not AUTH_CODE or not TO_EMAIL:
        print("错误: 缺少必要的环境变量 (GLADOS_COOKIE, SMTP_AUTH_CODE, TO_EMAIL)。请检查 GitHub Secrets 配置。")
        exit(1)
        
    # 签到
    success, result_message = glados_checkin(GLADOS_COOKIE)
    
    # 准备邮件内容
    if success:
        subject = "GLaDOS 自动签到成功"
        body = f"GLaDOS 每日自动签到已成功完成。\n\n签到结果: {result_message}"
    else:
        subject = "GLaDOS 自动签到失败"
        body = f"GLaDOS 每日自动签到失败。\n\n错误信息: {result_message}\n\n请检查您的 Cookie 是否过期或网络连接。"

    # 发送通知
    send_email_notification(TO_EMAIL, subject, body, AUTH_CODE)
    
    # 打印最终结果,方便定时任务捕获日志
    print(f"--- GLaDOS 签到结果 ---")
    print(f"成功: {success}")
    print(f"消息: {result_message}")
