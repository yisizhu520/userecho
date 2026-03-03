"""订阅管理 API"""

from typing import Annotated, Any

from fastapi import APIRouter

from backend.app.userecho.crud.crud_subscription import subscription_plan_dao
from backend.app.userecho.schema.subscription import (
    SubscriptionPlanSchema,
    SubscriptionUpdateReq,
    TenantSubscriptionSchema,
)
from backend.app.userecho.service.subscription_service import subscription_service
from backend.common.response.response_schema import response_base
from backend.common.security.jwt import CurrentUser
from backend.database.db import CurrentSession

router = APIRouter(prefix="/subscription", tags=["Admin - 订阅管理"])


@router.get("/plans", summary="获取所有订阅套餐")
async def get_subscription_plans(
    db: CurrentSession,
    _: Annotated[dict, CurrentUser],
) -> Any:
    """获取所有启用的订阅套餐"""
    plans = await subscription_plan_dao.get_all_active(db)
    return response_base.success(data=plans)


@router.get("/tenant/{tenant_id}", summary="获取租户订阅信息")
async def get_tenant_subscription(
    tenant_id: str,
    db: CurrentSession,
    _: Annotated[dict, CurrentUser],
) -> Any:
    """获取租户当前的订阅状态"""
    sub = await subscription_service.get_current_subscription(db, tenant_id)
    plan = await subscription_service.get_plan(db, sub.plan_id)

    # 构造响应
    data = TenantSubscriptionSchema.model_validate(sub)
    if plan:
        data.plan = SubscriptionPlanSchema.model_validate(plan)

    return response_base.success(data=data)


@router.post("/tenant/{tenant_id}", summary="更新租户订阅")
async def update_tenant_subscription(
    tenant_id: str,
    body: SubscriptionUpdateReq,
    db: CurrentSession,
    current_user: Annotated[Any, CurrentUser],
) -> Any:
    """管理员手动更新租户订阅"""
    operator_id = getattr(current_user, "id", None)
    if not operator_id:
        return response_base.fail(msg="未登录或 Token 已过期")

    sub = await subscription_service.manual_update_subscription(
        db,
        tenant_id,
        body.plan_code,
        body.expires_at,
        body.status,
        operator_id=str(operator_id),
        notes=body.notes,
    )
    return response_base.success(data=sub)
