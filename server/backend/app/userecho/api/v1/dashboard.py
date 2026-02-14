"""工作台 API 端点"""

from fastapi import APIRouter

from backend.app.userecho.service.dashboard_service import dashboard_service
from backend.common.response.response_schema import response_base
from backend.common.security.jwt import CurrentTenantId
from backend.database.db import CurrentSession

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
    - top_topics: TOP 需求主题 TOP 5（按反馈数量排序）
    - weekly_trend: 7天反馈趋势（每日新增数量）
    """
    stats = await dashboard_service.get_stats(db, tenant_id)
    return response_base.success(data=stats)
