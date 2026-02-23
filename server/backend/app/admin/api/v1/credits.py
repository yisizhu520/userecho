"""积分配置管理 API（Admin）"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from backend.app.userecho.model.credits import CreditsConfig, TenantCredits
from backend.common.response.response_schema import response_base
from backend.database.db import CurrentSession

router = APIRouter(prefix='/credits', tags=['Admin - 积分管理'])


class CreditsConfigUpdate(BaseModel):
    """积分配置更新"""

    config_value: int
    description: str | None = None


class TenantCreditsAdjust(BaseModel):
    """租户积分调整"""

    adjustment: int  # 正数增加，负数减少
    reason: str


# ==================== 积分配置管理 ====================


@router.get('/configs', summary='获取所有积分配置')
async def get_all_credits_configs(db: CurrentSession):
    """
    获取所有积分配置（操作消耗 + 套餐额度）

    返回按 config_type 分组的配置列表
    """
    result = await db.execute(select(CreditsConfig).order_by(CreditsConfig.config_type, CreditsConfig.config_key))
    configs = result.scalars().all()

    grouped = {'operation_cost': [], 'plan_quota': []}
    for config in configs:
        item = {
            'id': config.id,
            'config_key': config.config_key,
            'config_value': config.config_value,
            'description': config.description,
        }
        if config.config_type in grouped:
            grouped[config.config_type].append(item)

    return response_base.success(data=grouped)


@router.put('/configs/{config_id}', summary='更新积分配置')
async def update_credits_config(
    config_id: str,
    data: CreditsConfigUpdate,
    db: CurrentSession,
):
    """
    更新积分配置值

    可修改操作消耗积分数或套餐月度额度
    """
    result = await db.execute(select(CreditsConfig).where(CreditsConfig.id == config_id))
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=404, detail='配置不存在')

    config.config_value = data.config_value
    if data.description:
        config.description = data.description

    await db.commit()

    return response_base.success(
        data={
            'id': config.id,
            'config_key': config.config_key,
            'config_value': config.config_value,
            'description': config.description,
        }
    )


# ==================== 租户积分管理 ====================


@router.get('/tenants', summary='获取所有租户积分状态')
async def get_all_tenant_credits(db: CurrentSession):
    """
    获取所有租户的积分状态列表

    用于 Admin 查看和管理租户积分
    """
    result = await db.execute(
        select(TenantCredits).order_by(TenantCredits.current_balance.asc())  # 余额少的排前面
    )
    credits_list = result.scalars().all()

    return response_base.success(
        data=[
            {
                'id': tc.id,
                'tenant_id': tc.tenant_id,
                'plan_type': tc.plan_type,
                'monthly_quota': tc.monthly_quota,
                'current_balance': tc.current_balance,
                'total_used': tc.total_used,
                'next_refresh_at': tc.next_refresh_at.isoformat() if tc.next_refresh_at else None,
            }
            for tc in credits_list
        ]
    )


@router.post('/tenants/{tenant_id}/adjust', summary='调整租户积分')
async def adjust_tenant_credits(
    tenant_id: str,
    data: TenantCreditsAdjust,
    db: CurrentSession,
):
    """
    手动调整租户积分余额

    用于客服手动增加/扣减积分
    """
    from backend.app.userecho.model.credits import CreditsUsageLog
    from backend.common.log import log

    result = await db.execute(select(TenantCredits).where(TenantCredits.tenant_id == tenant_id))
    tenant_credits = result.scalar_one_or_none()

    if not tenant_credits:
        raise HTTPException(status_code=404, detail='租户积分记录不存在')

    old_balance = tenant_credits.current_balance
    tenant_credits.current_balance += data.adjustment

    # 记录调整日志
    usage_log = CreditsUsageLog(
        tenant_id=tenant_id,
        operation_type='admin_adjust',
        credits_cost=-data.adjustment,  # 负数表示增加
        description=f'Admin 调整: {data.reason}',
        extra_data={'old_balance': old_balance, 'adjustment': data.adjustment, 'reason': data.reason},
    )
    db.add(usage_log)

    await db.commit()

    log.info(f'Admin adjusted credits for tenant {tenant_id}: {old_balance} -> {tenant_credits.current_balance}')

    return response_base.success(
        data={
            'tenant_id': tenant_id,
            'old_balance': old_balance,
            'new_balance': tenant_credits.current_balance,
            'adjustment': data.adjustment,
        }
    )


@router.put('/tenants/{tenant_id}/plan', summary='变更租户套餐')
async def update_tenant_plan(
    tenant_id: str,
    plan_type: str,
    db: CurrentSession,
):
    """
    变更租户订阅套餐

    变更后立即更新月度额度（不刷新当前余额）
    """
    from backend.app.userecho.service.credits_service import credits_service

    valid_plans = ['starter', 'pro', 'team', 'enterprise']
    if plan_type not in valid_plans:
        raise HTTPException(status_code=400, detail=f'无效的套餐类型，可选: {valid_plans}')

    result = await db.execute(select(TenantCredits).where(TenantCredits.tenant_id == tenant_id))
    tenant_credits = result.scalar_one_or_none()

    if not tenant_credits:
        raise HTTPException(status_code=404, detail='租户积分记录不存在')

    old_plan = tenant_credits.plan_type
    new_quota = await credits_service.get_plan_quota(db, plan_type)

    tenant_credits.plan_type = plan_type
    tenant_credits.monthly_quota = new_quota

    await db.commit()

    return response_base.success(
        data={
            'tenant_id': tenant_id,
            'old_plan': old_plan,
            'new_plan': plan_type,
            'monthly_quota': new_quota,
        }
    )
