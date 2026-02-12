"""优先级评分 API 端点"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.feedalyze.schema.priority import PriorityScoreCreate
from backend.app.feedalyze.service import priority_service
from backend.common.response.response_schema import response_base
from backend.database.db import CurrentSession

router = APIRouter(prefix='/priority', tags=['Feedalyze - 优先级评分'])


def get_current_tenant_id() -> str:
    """获取当前租户ID"""
    return 'default-tenant'


@router.post('/score', summary='创建/更新优先级评分')
async def create_or_update_priority_score(
    data: PriorityScoreCreate,
    db: CurrentSession,
    tenant_id: str = Depends(get_current_tenant_id),
):
    """
    创建或更新优先级评分

    公式: (影响范围 × 商业价值) / 开发成本 × 紧急系数

    - **topic_id**: 主题ID
    - **impact_scope**: 影响范围 (1-10)
    - **business_value**: 商业价值 (1-10)
    - **dev_cost**: 开发成本 (1-10)
    - **urgency_factor**: 紧急系数 (1.0-2.0)
    """
    score = await priority_service.calculate_and_save(
        db=db,
        tenant_id=tenant_id,
        data=data
    )
    return await response_base.success(data=score, msg='评分成功')


@router.get('/ranking', summary='获取优先级排行榜')
async def get_priority_ranking(
    db: CurrentSession,
    tenant_id: str = Depends(get_current_tenant_id),
    limit: int = 50,
):
    """
    获取优先级排行榜（按总分降序）

    用于决策哪些需求应该优先开发

    - **limit**: 返回数量（默认50）
    """
    ranking = await priority_service.get_ranking(
        db=db,
        tenant_id=tenant_id,
        limit=limit
    )
    return await response_base.success(data=ranking)
