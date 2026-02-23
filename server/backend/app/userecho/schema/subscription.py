"""订阅 Schemas"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from backend.app.userecho.model.subscription import (
    PlanCode,
    SubscriptionAction,
    SubscriptionStatus,
)
from backend.common.schema import SchemaBase

# --- Subscription Plan ---


class SubscriptionPlanBase(BaseModel):
    code: str = Field(..., description="套餐代号")
    name: str = Field(..., description="套餐名称")
    description: str | None = Field(None, description="套餐描述")
    price_monthly: int = Field(..., description="月付价格（分）")
    price_yearly: int = Field(..., description="年付价格（分）")
    seat_limit: int = Field(..., description="席位上限")
    feedback_limit: int = Field(..., description="反馈存储上限")
    ai_credits_monthly: int = Field(..., description="月度 AI 积分")
    features: dict = Field(..., description="功能配置")
    is_active: bool = Field(True, description="是否启用")
    sort_order: int = Field(0, description="排序")


class SubscriptionPlanSchema(SubscriptionPlanBase, SchemaBase):
    """订阅套餐响应模型"""

    model_config = ConfigDict(from_attributes=True)


# --- Tenant Subscription ---


class SubscriptionCreateReq(BaseModel):
    """创建/设置订阅请求"""

    plan_code: PlanCode = Field(..., description="套餐代号")
    expires_at: datetime = Field(..., description="过期时间")
    status: SubscriptionStatus = Field(SubscriptionStatus.ACTIVE, description="状态")
    notes: str | None = Field(None, description="备注")


class SubscriptionUpdateReq(BaseModel):
    """更新订阅请求"""

    plan_code: PlanCode = Field(..., description="套餐代号")
    expires_at: datetime = Field(..., description="过期时间")
    status: SubscriptionStatus = Field(..., description="状态")
    notes: str | None = Field(None, description="备注")


class TenantSubscriptionSchema(SchemaBase):
    """租户订阅响应模型"""

    tenant_id: str
    plan_id: str
    status: SubscriptionStatus
    started_at: datetime
    expires_at: datetime
    trial_ends_at: datetime | None = None
    canceled_at: datetime | None = None
    source: str
    created_by: str | None = None
    notes: str | None = None

    # 额外字段（需要 Service 层填充或 join）
    plan: SubscriptionPlanSchema | None = None

    model_config = ConfigDict(from_attributes=True)


# --- History ---


class SubscriptionHistorySchema(SchemaBase):
    """订阅历史响应模型"""

    tenant_id: str
    subscription_id: str
    action: SubscriptionAction
    old_plan_code: str | None
    new_plan_code: str
    changed_by: str | None
    reason: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
