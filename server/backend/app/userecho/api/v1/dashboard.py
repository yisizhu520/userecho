"""工作台 API 端点"""

from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.userecho.crud.crud_topic import crud_topic
from backend.app.userecho.service.dashboard_service import dashboard_service
from backend.common.response.response_schema import response_base
from backend.common.security.jwt import CurrentTenantId
from backend.database.db import CurrentSession, CurrentSessionTransaction

router = APIRouter(prefix='/dashboard', tags=['UserEcho - 工作台'])


@router.get('/stats', summary='获取工作台统计数据')
async def get_dashboard_stats(
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
):
    """
    获取工作台所有统计数据（一次性返回）

    返回内容：
    - feedback_stats: 反馈统计（总数/待处理/本周新增）
    - topic_stats: 需求统计（总数/待处理/已完成/本周新增）
    - urgent_topics: 紧急需求列表 TOP 5（按优先级排序）
    - pending_decisions: 待决策主题列表 TOP 5（带 MVP 优先级评分）
    - top_topics: TOP 需求主题 TOP 5（按反馈数量排序）
    - weekly_trend: 7天反馈趋势（每日新增数量）
    - tag_distribution: 标签分布统计（各标签的需求数/反馈数/平均评分）
    """
    stats = await dashboard_service.get_stats(db, tenant_id)
    return response_base.success(data=stats)


# ========================================
# 快速决策 API
# ========================================


class QuickDecisionParam(BaseModel):
    """快速决策参数"""

    action: Literal['confirm', 'ignore'] = Field(description='决策动作：confirm(确认) 或 ignore(忽略)')


@router.post('/topic/{topic_id}/quick-decision', summary='快速决策')
async def quick_decision(
    topic_id: str,
    param: QuickDecisionParam,
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
):
    """
    快速决策:确认或忽略主题

    - confirm: 将主题状态从 pending 变更为 planned
    - ignore: 将主题状态变更为 ignored
    """
    # 查询主题
    topic = await crud_topic.get_by_id(db, tenant_id, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail='主题不存在')

    if topic.status != 'pending':
        raise HTTPException(status_code=400, detail=f'主题状态为 {topic.status}，无法进行决策操作')

    # 更新状态
    new_status = 'planned' if param.action == 'confirm' else 'ignored'
    await crud_topic.update(db, tenant_id, topic_id, status=new_status)
    await db.commit()

    return response_base.success(
        data={
            'id': topic_id,
            'action': param.action,
            'new_status': new_status,
        }
    )


# ========================================
# 我的反馈 API
# ========================================


@router.get('/my-feedbacks', summary='获取我录入的反馈统计')
async def get_my_feedbacks(
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
    limit: int = 10,
):
    """
    获取当前用户录入的反馈统计

    返回内容：
    - summary: 统计摘要
      - submitted_count: 我录入的反馈总数
      - in_progress_count: 已进入排期的数量
      - completed_count: 已完成的数量
    - recent_updates: 最近更新的反馈列表
    """
    from backend.common.security.jwt import get_current_user_id

    user_id = get_current_user_id()
    stats = await dashboard_service.get_my_feedbacks(db, tenant_id, user_id, limit)
    return response_base.success(data=stats)
