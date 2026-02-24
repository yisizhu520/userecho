"""邮箱验证 Schemas"""

from pydantic import BaseModel, Field


class EmailVerificationCreateReq(BaseModel):
    """创建邮箱验证请求"""

    email: str = Field(..., description="邮箱")


class EmailVerifyReq(BaseModel):
    """验证邮箱请求"""

    verification_code: str = Field(..., description="验证码")


class EmailVerifyResp(BaseModel):
    """验证邮箱响应"""

    verified: bool = Field(..., description="是否验证成功")
    message: str = Field(..., description="提示信息")


class EmailResendReq(BaseModel):
    """重新发送验证邮件请求"""

    email: str = Field(..., description="邮箱")


class EmailResendResp(BaseModel):
    """重新发送验证邮件响应"""

    sent: bool = Field(..., description="是否发送成功")
    message: str = Field(..., description="提示信息")
    retry_after: int | None = Field(None, description="多少秒后可重试")
