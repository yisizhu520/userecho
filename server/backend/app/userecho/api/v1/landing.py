"""Landing Page 公开 API - 不需要登录"""

from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from aiosmtplib import SMTP
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from backend.common.log import log
from backend.common.response.response_schema import ResponseModel, response_base
from backend.core.conf import settings
from backend.utils.timezone import timezone

router = APIRouter(prefix='/landing', tags=['Landing'])


class TrialApplicationRequest(BaseModel):
    """试用申请请求"""
    name: str = Field(..., min_length=1, max_length=50, description='姓名')
    phone: str = Field(..., min_length=1, max_length=50, description='手机/微信')
    company: str = Field(default='', max_length=100, description='公司/团队')


async def send_notification_email(recipients: str, subject: str, content: str) -> None:
    """
    直接发送邮件通知，不依赖数据库配置
    """
    message = MIMEMultipart()
    message['Subject'] = subject
    message['From'] = settings.EMAIL_USERNAME
    message['date'] = timezone.now().strftime('%a, %d %b %Y %H:%M:%S %z')
    message.attach(MIMEText(content, 'plain', 'utf-8'))
    
    smtp_client = SMTP(
        hostname=settings.EMAIL_HOST,
        port=settings.EMAIL_PORT,
        use_tls=settings.EMAIL_SSL,
    )
    async with smtp_client:
        await smtp_client.login(settings.EMAIL_USERNAME, settings.EMAIL_PASSWORD)
        await smtp_client.sendmail(settings.EMAIL_USERNAME, recipients, message.as_bytes())


@router.post('/trial-application', summary='提交试用申请')
async def submit_trial_application(
    request: Request,
    data: TrialApplicationRequest,
) -> ResponseModel:
    """
    接收用户的试用申请，发送邮件通知管理员
    
    这是一个公开接口，不需要登录
    """
    try:
        # 获取用户 IP
        client_ip = request.client.host if request.client else 'unknown'
        
        # 构建邮件内容
        submit_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        email_subject = f'📥 新用户申请免费试用 - {data.name}'
        email_content = f"""
📥 新用户申请免费试用《回响》

────────────────────────
👤 姓名：{data.name}
📱 手机/微信：{data.phone}
🏢 公司/团队：{data.company or '未填写'}
────────────────────────

⏰ 提交时间：{submit_time}
🌐 来源IP：{client_ip}

请尽快联系该用户！
"""
        
        # 发送邮件通知
        admin_email = '1914731404@qq.com'
        
        await send_notification_email(
            recipients=admin_email,
            subject=email_subject,
            content=email_content,
        )
        
        log.info(f'Trial application submitted: name={data.name}, phone={data.phone}')
        
        return response_base.success(data={'message': '提交成功，我们会尽快联系您'})
        
    except Exception as e:
        log.error(f'Failed to submit trial application: {e}')
        # 即使邮件发送失败，也返回成功，避免用户重复提交
        return response_base.success(data={'message': '提交成功，我们会尽快联系您'})
