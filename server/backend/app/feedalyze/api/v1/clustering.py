"""聚类 API 端点"""

from fastapi import APIRouter

from backend.app.feedalyze.service import clustering_service
from backend.app.task.celery import celery_app
from backend.common.response.response_code import CustomResponse
from backend.common.response.response_schema import response_base
from backend.common.security.jwt import CurrentTenantId
from backend.database.db import CurrentSession

router = APIRouter(prefix='/clustering', tags=['Feedalyze - AI聚类'])


@router.post('/trigger', summary='触发聚类任务')
async def trigger_clustering(
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
    max_feedbacks: int = 100,
    force_recluster: bool = False,
    async_mode: bool = False,
):
    """
    触发 AI 聚类任务

    自动聚类未聚类的反馈，生成需求主题

    - **max_feedbacks**: 最多处理的反馈数量（默认100）

    流程：
    1. 获取未聚类的反馈
    2. 提取 AI embedding 向量
    3. 执行 DBSCAN 聚类
    4. 为每个聚类生成主题标题
    5. 批量更新反馈的主题关联
    """
    if async_mode:
        async_result = celery_app.send_task(
            name='feedalyze_clustering_batch',
            args=[tenant_id],
            kwargs={'max_feedbacks': max_feedbacks, 'force_recluster': force_recluster},
        )
        return response_base.success(
            data={'status': 'accepted', 'task_id': async_result.id},
            res=CustomResponse(code=200, msg='聚类任务已提交'),
        )

    result = await clustering_service.trigger_clustering(
        db=db,
        tenant_id=tenant_id,
        max_feedbacks=max_feedbacks,
        force_recluster=force_recluster,
    )

    if result['status'] == 'error':
        return response_base.fail(res=CustomResponse(code=400, msg=result.get('message', '聚类失败')))

    if result['status'] == 'failed':
        return response_base.fail(res=CustomResponse(code=400, msg=result.get('message', '聚类失败')))

    if result['status'] == 'skipped':
        return response_base.fail(res=CustomResponse(code=400, msg=result.get('message', '聚类已跳过')))

    return response_base.success(data=result, res=CustomResponse(code=200, msg='聚类完成'))


@router.get('/task/{task_id}', summary='查询聚类任务状态')
async def get_clustering_task_status(
    task_id: str,
    tenant_id: str = CurrentTenantId,
):
    """
    查询 Celery 聚类任务状态（MVP：基于 task_id 轮询）

    返回字段：
    - state: PENDING / STARTED / SUCCESS / FAILURE / RETRY
    - result: 成功时返回 trigger_clustering 的结果
    - error: 失败时返回错误信息
    """
    _ = tenant_id  # 租户鉴权由依赖保证；MVP 不做 task_id ↔ tenant 的强绑定
    r = celery_app.AsyncResult(task_id)
    data: dict = {'task_id': task_id, 'state': r.state}
    if r.successful():
        data['result'] = r.result
    elif r.failed():
        data['error'] = str(r.result)
    return response_base.success(data=data)


@router.get('/suggestions/{feedback_id}', summary='获取聚类建议')
async def get_clustering_suggestions(
    feedback_id: str,
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
    top_k: int = 5,
):
    """
    获取反馈的聚类建议（查找相似反馈）

    用于人工调整时参考

    - **top_k**: 返回最相似的 K 个反馈（默认5个）
    """
    suggestions = await clustering_service.get_clustering_suggestions(
        db=db,
        tenant_id=tenant_id,
        feedback_id=feedback_id,
        top_k=top_k,
    )

    return response_base.success(data=suggestions)
