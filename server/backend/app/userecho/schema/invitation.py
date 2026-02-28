"""邀请 Schemas"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from backend.common.schema import SchemaBase


# --- Invitation ---


class InvitationCreateReq(BaseModel):
    """创建邀请请求"""

    usage_limit: int = Field(10, description="使用次数限制", ge=1, le=1000)
    expires_days: int = Field(90, description="过期天数", ge=1, le=365)
    plan_code: str = Field("pro", description="赋予的套餐代号")
    trial_days: int = Field(30, description="试用天数", ge=1, le=365)
    source: str | None = Field(None, description="来源标签", max_length=50)
    campaign: str | None = Field(None, description="活动标识", max_length=100)
    notes: str | None = Field(None, description="管理备注")


class InvitationUpdateReq(BaseModel):
    """更新邀请请求"""

    status: str | None = Field(None, description="状态: active/expired/disabled")
    usage_limit: int | None = Field(None, description="使用次数限制", ge=1)
    expires_at: datetime | None = Field(None, description="过期时间")
    notes: str | None = Field(None, description="管理备注")


class InvitationSchema(SchemaBase):
    """邀请响应模型"""

    token: str = Field(..., description="邀请token")
    usage_limit: int = Field(..., description="使用次数限制")
    used_count: int = Field(..., description="已使用次数")
    expires_at: datetime = Field(..., description="过期时间")
    plan_code: str = Field(..., description="套餐代号")
    trial_days: int = Field(..., description="试用天数")
    source: str | None = Field(None, description="来源标签")
    campaign: str | None = Field(None, description="活动标识")
    creator_id: int | None = Field(None, description="创建者ID")
    notes: str | None = Field(None, description="管理备注")
    status: str = Field(..., description="状态")

    model_config = ConfigDict(from_attributes=True)


class InvitationDetailSchema(InvitationSchema):
    """邀请详情响应（包含URL）"""

    url: str = Field(..., description="邀请URL")
    short_url: str | None = Field(None, description="短链接")
    qr_code_url: str = Field(..., description="二维码URL")
    remaining_usage: int = Field(..., description="剩余使用次数")


class InvitationValidateResp(BaseModel):
    """验证邀请响应"""

    valid: bool = Field(..., description="是否有效")
    plan: dict | None = Field(None, description="套餐信息")
    expires_at: datetime | None = Field(None, description="过期时间")
    remaining_usage: int | None = Field(None, description="剩余使用次数")
    error_code: str | None = Field(None, description="错误代码")
    error_message: str | None = Field(None, description="错误信息")


# --- Invitation Usage ---


class InvitationUsageSchema(SchemaBase):
    """邀请使用记录响应"""

    invitation_id: str = Field(..., description="邀请ID")
    user_id: int = Field(..., description="用户ID")
    registered_email: str = Field(..., description="注册邮箱")
    ip_address: str | None = Field(None, description="IP地址")
    user_agent: str | None = Field(None, description="浏览器信息")
    completed_onboarding: bool = Field(..., description="是否完成引导")
    created_tenant_id: str | None = Field(None, description="创建的租户ID")
    used_at: datetime = Field(..., description="使用时间")

    model_config = ConfigDict(from_attributes=True)


class InvitationUsageDetailResp(InvitationUsageSchema):
    """邀请使用详情（包含关联信息）"""

    user: dict | None = Field(None, description="用户信息")
    created_tenant: dict | None = Field(None, description="租户信息")


class InvitationStatistics(BaseModel):
    """邀请统计信息"""

    total_used: int = Field(..., description="总使用次数")
    completed_onboarding: int = Field(..., description="完成引导的用户数")
    conversion_rate: float = Field(..., description="转化率")
