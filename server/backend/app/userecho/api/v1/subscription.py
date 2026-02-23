"""订阅信息 API (租户端)"""

from fastapi import APIRouter

from backend.app.userecho.schema.subscription import (
    SubscriptionPlanSchema,
    TenantSubscriptionSchema,
)
from backend.app.userecho.service.subscription_service import subscription_service
from backend.common.response.response_schema import response_base
from backend.common.security.jwt import CurrentTenantId, CurrentUser
from backend.database.db import CurrentSession

router = APIRouter(prefix="/subscription", tags=["UserEcho - 订阅信息"])


@router.get("/me", summary="获取当前订阅")
async def get_current_subscription(
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
    _: dict = CurrentUser,
):
    """获取当前租户的订阅详情"""
    sub = await subscription_service.get_current_subscription(db, tenant_id)
    plan = await subscription_service.get_plan(db, sub.plan_id)

    data = TenantSubscriptionSchema.model_validate(sub)
    if plan:
        data.plan = SubscriptionPlanSchema.model_validate(plan)

    return response_base.success(data=data)
