"""认证相关 Schemas（邀请注册）"""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RegisterWithInvitationReq(BaseModel):
    """通过邀请码注册请求"""

    invitation_token: str = Field(..., description="邀请token")
    email: EmailStr = Field(..., description="邮箱")
    password: str = Field(..., description="密码", min_length=8, max_length=128)
    nickname: str = Field(..., description="昵称", min_length=1, max_length=64)


class RegisterWithInvitationResp(BaseModel):
    """通过邀请码注册响应"""

    user: dict = Field(..., description="用户信息")
    access_token: str = Field(..., description="访问令牌")
    session_uuid: str = Field(..., description="会话UUID")
    access_token_expire_time: datetime = Field(..., description="访问令牌过期时间")
    verification_email_sent: bool = Field(..., description="验证邮件是否已发送")
    next_step: str = Field(..., description="下一步操作")
