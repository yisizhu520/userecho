"""聚类 API 端点"""

import numpy as np
from fastapi import APIRouter

from backend.app.userecho.service import clustering_service
from backend.app.userecho.crud import crud_feedback
from backend.app.task.celery import celery_app
from backend.common.response.response_code import CustomResponse
from backend.common.response.response_schema import response_base
from backend.common.security.jwt import CurrentTenantId
from backend.database.db import CurrentSession
from backend.utils.ai_client import ai_client
from sklearn.metrics.pairwise import cosine_similarity

router = APIRouter(prefix='/clustering', tags=['UserEcho - AI聚类'])


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
            name='userecho_clustering_batch',
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


@router.get('/debug/similarity-matrix', summary='【调试】查看反馈相似度矩阵')
async def debug_similarity_matrix(
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
    limit: int = 20,
):
    """
    调试接口：查看待聚类反馈之间的相似度矩阵
    
    帮助调整聚类参数（CLUSTERING_SIMILARITY_THRESHOLD）
    """
    # 获取待聚类的反馈
    feedbacks = await crud_feedback.get_pending_clustering(
        db=db,
        tenant_id=tenant_id,
        limit=limit,
        include_failed=False,
        force_recluster=False,
    )
    
    if len(feedbacks) < 2:
        return response_base.fail(res=CustomResponse(code=400, msg=f'待聚类反馈不足（当前: {len(feedbacks)}）'))
    
    # 获取 embedding
    embeddings = []
    valid_feedbacks = []
    
    for feedback in feedbacks:
        cached_embedding = crud_feedback.get_cached_embedding(feedback)
        if cached_embedding is not None:
            embeddings.append(cached_embedding)
            valid_feedbacks.append(feedback)
        else:
            # 临时获取 embedding（不缓存）
            embedding = await ai_client.get_embedding(feedback.content)
            if embedding is not None:
                embeddings.append(embedding)
                valid_feedbacks.append(feedback)
    
    if len(embeddings) < 2:
        return response_base.fail(res=CustomResponse(code=400, msg='无法获取足够的 embedding'))
    
    # 计算相似度矩阵
    embeddings_array = np.array(embeddings)
    similarity_matrix = cosine_similarity(embeddings_array)
    
    # 构造返回数据
    feedbacks_info = [
        {
            'id': fb.id,
            'content': fb.content[:50] + '...' if len(fb.content) > 50 else fb.content,
            'full_content': fb.content,
        }
        for fb in valid_feedbacks
    ]
    
    # 找出高相似度对（>= 0.75）
    high_similarity_pairs = []
    for i in range(len(similarity_matrix)):
        for j in range(i + 1, len(similarity_matrix)):
            sim = float(similarity_matrix[i][j])
            if sim >= 0.75:
                high_similarity_pairs.append({
                    'feedback1_id': valid_feedbacks[i].id,
                    'feedback1_content': feedbacks_info[i]['content'],
                    'feedback2_id': valid_feedbacks[j].id,
                    'feedback2_content': feedbacks_info[j]['content'],
                    'similarity': round(sim, 4),
                })
    
    # 按相似度降序排列
    high_similarity_pairs.sort(key=lambda x: x['similarity'], reverse=True)
    
    return response_base.success(data={
        'feedbacks': feedbacks_info,
        'similarity_matrix': similarity_matrix.tolist(),
        'high_similarity_pairs': high_similarity_pairs,
        'stats': {
            'total_feedbacks': len(valid_feedbacks),
            'avg_similarity': float(np.mean(similarity_matrix[np.triu_indices_from(similarity_matrix, k=1)])),
            'max_similarity': float(np.max(similarity_matrix[np.triu_indices_from(similarity_matrix, k=1)])),
            'min_similarity': float(np.min(similarity_matrix[np.triu_indices_from(similarity_matrix, k=1)])),
            'pairs_above_075': len(high_similarity_pairs),
        }
    })
