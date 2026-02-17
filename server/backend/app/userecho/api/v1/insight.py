"""洞察 API 接口"""

from typing import Annotated

from fastapi import APIRouter, Query

from backend.app.task.celery import celery_app
from backend.app.userecho.crud.crud_insight import crud_insight
from backend.app.userecho.service.insight_service import insight_service
from backend.common.response.response_code import CustomResponse
from backend.common.response.response_schema import response_base
from backend.common.security.jwt import CurrentTenantId
from backend.database.db import CurrentSession

router = APIRouter()


@router.get('/insights/{insight_type}', summary='获取指定类型的洞察')
async def get_insight(
    insight_type: str,
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
    time_range: Annotated[str, Query(description='时间范围：this_week | this_month | custom')] = 'this_week',
    force_refresh: Annotated[bool, Query(description='是否强制刷新（忽略缓存）')] = False,
):
    """
    获取指定类型的洞察

    洞察类型：
    - priority_suggestion: 优先级建议
    - high_risk: 高风险需求识别
    - weekly_report: 周报/月报
    - sentiment_trend: 客户满意度趋势
    """
    result = await insight_service.generate_insight(
        db=db,
        tenant_id=tenant_id,
        insight_type=insight_type,
        time_range=time_range,
        force_refresh=force_refresh,
    )
    return response_base.success(data=result)


@router.get('/insights/dashboard/summary', summary='工作台批量获取洞察')
async def get_dashboard_insights(
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
):
    """
    工作台一次性获取所有洞察

    返回：
    - priority_suggestions: 优先级建议
    - high_risk_topics: 高风险需求
    - sentiment_summary: 满意度趋势
    """
    # 并发获取 3 种洞察（周报单独生成，不在工作台显示）
    priority_suggestions = await insight_service.generate_insight(db, tenant_id, 'priority_suggestion', 'this_week')

    high_risk_topics = await insight_service.generate_insight(db, tenant_id, 'high_risk', 'this_week')

    sentiment_summary = await insight_service.generate_insight(db, tenant_id, 'sentiment_trend', 'this_week')

    return response_base.success(
        data={
            'priority_suggestions': priority_suggestions,
            'high_risk_topics': high_risk_topics,
            'sentiment_summary': sentiment_summary,
        }
    )


@router.post('/insights/report/export', summary='导出周报/月报（异步）')
async def export_report(
    tenant_id: str = CurrentTenantId,
    time_range: Annotated[str, Query(description='时间范围：this_week | this_month')] = 'this_week',
    format: Annotated[str, Query(description='导出格式：markdown | html')] = 'markdown',
):
    """
    导出周报/月报（异步生成）

    返回 task_id，前端通过 /insights/task/{task_id} 轮询任务状态
    """
    async_result = celery_app.send_task(
        name='userecho.generate_insight_report',
        args=[tenant_id, time_range, format],
    )
    return response_base.success(
        data={'status': 'accepted', 'task_id': async_result.id},
        res=CustomResponse(code=200, msg='报告生成任务已提交'),
    )


@router.post('/insights/report/send-email', summary='发送报告邮件')
async def send_report_email(
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
    recipients: Annotated[list[str] | None, Query(description='收件人邮箱列表')] = None,
    time_range: Annotated[str, Query(description='时间范围：this_week | this_month')] = 'this_week',
):
    """
    发送周报邮件给指定收件人
    """
    if not recipients:
        return response_base.fail(msg='请提供收件人邮箱')

    # 生成报告数据
    report_content = await insight_service.generate_insight(
        db=db,
        tenant_id=tenant_id,
        insight_type='weekly_report',
        time_range=time_range,
        force_refresh=False,
    )

    # 发送邮件
    await insight_service.send_report_email(
        db=db,
        recipients=recipients,
        report_data=report_content,
        time_range=time_range,
    )

    return response_base.success(msg='报告邮件发送成功')



@router.get('/insights/task/{task_id}', summary='查询洞察生成任务状态')
async def get_insight_task_status(
    task_id: str,
    tenant_id: str = CurrentTenantId,
):
    """
    查询 Celery 洞察生成任务状态

    返回字段：
    - state: PENDING / STARTED / SUCCESS / FAILURE / RETRY
    - result: 成功时返回生成的报告内容
    - error: 失败时返回错误信息
    - progress: 任务进度（可选）
    """
    _ = tenant_id  # 租户鉴权由依赖保证；MVP 不做 task_id ↔ tenant 的强绑定
    r = celery_app.AsyncResult(task_id)
    data: dict = {'task_id': task_id, 'state': r.state}

    if r.successful():
        data['result'] = r.result
    elif r.failed():
        data['error'] = str(r.result)
    elif r.state == 'PROGRESS':
        # 支持进度更新（可选）
        data['progress'] = r.info

    return response_base.success(data=data)


@router.post('/insights/{insight_id}/dismiss', summary='忽略洞察')
async def dismiss_insight(
    insight_id: str,
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
    reason: str = Query(..., description='忽略原因'),
):
    """
    用户手动忽略洞察（例如"这个建议不合理"）
    """
    await crud_insight.dismiss_insight(
        db=db,
        insight_id=insight_id,
        tenant_id=tenant_id,
        reason=reason,
    )
    return response_base.success(msg='洞察已忽略')


@router.get('/insights/history', summary='获取历史洞察')
async def get_insights_history(
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
    insight_type: Annotated[str | None, Query(description='洞察类型筛选')] = None,
    status: Annotated[str, Query(description='状态筛选：active | archived | dismissed')] = 'active',
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """
    获取历史洞察列表（分页）
    """
    # TODO: 实现分页查询
    return response_base.success(data={'items': [], 'total': 0})
