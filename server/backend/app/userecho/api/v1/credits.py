"""积分管理 API"""

from fastapi import APIRouter, Query

from backend.app.userecho.service.credits_service import credits_service
from backend.common.response.response_schema import response_base
from backend.common.security.jwt import CurrentTenantId
from backend.database.db import CurrentSession

router = APIRouter(prefix='/credits', tags=['UserEcho - 积分管理'])


@router.get('/balance', summary='获取积分余额')
async def get_credits_balance(
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
):
    """
    获取当前租户的积分余额信息

    返回：
    - plan_type: 订阅类型
    - monthly_quota: 月度额度
    - current_balance: 当前余额
    - total_used: 累计使用
    - next_refresh_at: 下次刷新时间
    - usage_percentage: 使用百分比
    - is_unlimited: 是否无限制
    """
    balance = await credits_service.get_balance(db, tenant_id)
    return response_base.success(data=balance)


@router.get('/usage', summary='获取积分使用记录')
async def get_credits_usage(
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
    operation_type: str | None = Query(None, description='操作类型过滤'),
    limit: int = Query(100, ge=1, le=500, description='返回记录数'),
):
    """
    获取积分使用记录列表

    支持按操作类型过滤
    """
    history = await credits_service.get_usage_history(
        db=db,
        tenant_id=tenant_id,
        operation_type=operation_type,
        limit=limit,
    )
    return response_base.success(data=history)


@router.get('/stats', summary='获取积分统计')
async def get_credits_stats(
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
):
    """
    获取积分使用统计（按类型分组）

    返回：
    - breakdown: 各操作类型的消耗统计
    - total: 总消耗
    """
    stats = await credits_service.get_usage_stats(db, tenant_id)
    return response_base.success(data=stats)
