"""聚类 API 端点"""

import operator

import numpy as np

from fastapi import APIRouter
from sklearn.cluster import DBSCAN
from sklearn.metrics import silhouette_score
from sklearn.metrics.pairwise import cosine_similarity

from backend.app.task.celery import celery_app
from backend.app.userecho.crud import crud_feedback
from backend.app.userecho.service import clustering_service
from backend.common.response.response_code import CustomResponse
from backend.common.response.response_schema import response_base
from backend.common.security.depends import DependsTurnstile
from backend.common.security.jwt import CurrentTenantId
from backend.core.conf import settings
from backend.database.db import CurrentSession
from backend.utils.ai_client import ai_client

router = APIRouter(prefix='/clustering', tags=['UserEcho - AI聚类'])


@router.post('/trigger', summary='触发聚类任务', dependencies=[DependsTurnstile])
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


@router.get('/status', summary='获取聚类状态概览')
async def get_clustering_status(
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
):
    """
    获取聚类状态概览

    返回内容：
    - pending_count: 待聚类反馈数量
    - processing_count: 处理中反馈数量
    - last_run_at: 上次聚类运行时间
    - last_run_result: 上次聚类结果摘要
    
    智能超时检测：
    - 自动清理超过10分钟的 processing 状态（防止任务失败后状态卡死）
    - 只统计最近10分钟内的真实 processing 记录
    """
    from datetime import timedelta

    from sqlalchemy import func, select

    from backend.app.userecho.model.feedback import Feedback
    from backend.common.log import log
    from backend.utils.timezone import timezone

    # 超时阈值：10分钟（大于 Celery 任务的 9分钟软超时 + 1分钟硬超时）
    PROCESSING_TIMEOUT_MINUTES = 10
    timeout_threshold = timezone.now() - timedelta(minutes=PROCESSING_TIMEOUT_MINUTES)

    # ========================================
    # 1. 自动清理超时的 processing 状态
    # ========================================
    # 查找超时的 processing 记录（updated_time 超过10分钟）
    stale_processing_query = select(Feedback.id).where(
        Feedback.tenant_id == tenant_id,
        Feedback.deleted_at.is_(None),
        Feedback.clustering_status == 'processing',
        Feedback.updated_time < timeout_threshold,
    )
    stale_processing_ids = list(await db.scalars(stale_processing_query))

    # 如果发现超时记录，自动清理并记录日志
    if stale_processing_ids:
        log.warning(
            f'Found {len(stale_processing_ids)} stale processing feedbacks for tenant {tenant_id}, '
            f'cleaning up (threshold: {PROCESSING_TIMEOUT_MINUTES} minutes)'
        )

        # 批量更新为 failed 状态
        await crud_feedback.batch_update_clustering(
            db=db,
            tenant_id=tenant_id,
            feedback_ids=stale_processing_ids,
            clustering_status='failed',
            clustering_metadata={
                'failed_at': timezone.now().isoformat(),
                'reason': 'timeout_cleanup',
                'timeout_minutes': PROCESSING_TIMEOUT_MINUTES,
            },
        )

        log.info(f'Successfully cleaned up {len(stale_processing_ids)} stale processing feedbacks for tenant {tenant_id}')

    # ========================================
    # 2. 统计真实的 processing 数量（10分钟内）
    # ========================================
    processing_query = select(func.count(Feedback.id)).where(
        Feedback.tenant_id == tenant_id,
        Feedback.deleted_at.is_(None),
        Feedback.clustering_status == 'processing',
        Feedback.updated_time >= timeout_threshold,  # 只统计最近10分钟内的
    )
    processing_count = await db.scalar(processing_query) or 0

    # ========================================
    # 3. 统计待聚类数量（pending 状态）
    # ========================================
    pending_query = select(func.count(Feedback.id)).where(
        Feedback.tenant_id == tenant_id,
        Feedback.deleted_at.is_(None),
        Feedback.topic_id.is_(None),
        Feedback.clustering_status == 'pending',
    )
    pending_count = await db.scalar(pending_query) or 0

    # ========================================
    # 4. 获取最近一次聚类的时间
    # ========================================
    last_clustered_query = (
        select(Feedback.clustering_metadata)
        .where(
            Feedback.tenant_id == tenant_id,
            Feedback.deleted_at.is_(None),
            Feedback.clustering_status == 'clustered',
            Feedback.clustering_metadata.is_not(None),
        )
        .order_by(Feedback.updated_time.desc())
        .limit(1)
    )
    last_metadata = await db.scalar(last_clustered_query)

    last_run_at = None
    if last_metadata and isinstance(last_metadata, dict):
        last_run_at = last_metadata.get('clustered_at')

    return response_base.success(
        data={
            'pending_count': pending_count,
            'processing_count': processing_count,
            'last_run_at': last_run_at,
        }
    )


@router.get('/suggestions/{feedback_id}', summary='获取聚类建议', dependencies=[DependsTurnstile])
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


@router.get('/pending-suggestions', summary='获取待处理的合并建议', dependencies=[DependsTurnstile])
async def get_pending_suggestions(
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
):
    """
    获取当前租户所有待处理的合并建议

    包括：
    - 与已有需求重复的聚类（未自动创建新需求，等待人工确认）
    """
    suggestions = await clustering_service.get_pending_suggestions(
        db=db,
        tenant_id=tenant_id,
    )

    return response_base.success(data=suggestions)



@router.get('/debug/similarity-matrix', summary='【调试】查看反馈相似度矩阵和聚类结果')
async def debug_similarity_matrix(
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
    limit: int = 20,
    similarity_threshold: float | None = None,
    min_samples: int | None = None,
):
    """
    调试接口：查看待聚类反馈之间的相似度矩阵 + 实际聚类结果

    帮助调整聚类参数

    - **similarity_threshold**: 自定义相似度阈值（默认使用配置值）
    - **min_samples**: 自定义最小簇大小（默认使用配置值）

    返回：
    - 相似度矩阵
    - 高相似度对
    - 实际聚类结果（每个簇包含哪些反馈）
    - 质量指标（轮廓系数、噪声率）
    """
    # 使用自定义参数或配置默认值
    threshold = similarity_threshold if similarity_threshold is not None else settings.CLUSTERING_SIMILARITY_THRESHOLD
    min_samples_val = min_samples if min_samples is not None else settings.CLUSTERING_MIN_SAMPLES

    # 获取待聚类的反馈
    feedbacks = await crud_feedback.get_pending_clustering(
        db=db,
        tenant_id=tenant_id,
        limit=limit,
        include_failed=True,
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

    # 构造反馈信息
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
    high_similarity_pairs.sort(key=operator.itemgetter('similarity'), reverse=True)

    # ========================================
    # 执行 DBSCAN 聚类
    # ========================================
    # 转换为距离矩阵（1 - 相似度）
    # 注意：clip 到 [0, 1] 避免浮点数误差导致负值
    similarity_matrix_clipped = np.clip(similarity_matrix, 0, 1)
    distance_matrix = 1 - similarity_matrix_clipped

    # 再次确保距离矩阵非负（防御性编程）
    distance_matrix = np.maximum(distance_matrix, 0)

    # DBSCAN 参数：eps = 1 - threshold（距离阈值）
    eps = 1 - threshold
    dbscan = DBSCAN(eps=eps, min_samples=min_samples_val, metric='precomputed')
    labels = dbscan.fit_predict(distance_matrix)

    # ========================================
    # 计算质量指标
    # ========================================
    noise_count = np.sum(labels == -1)
    noise_ratio = noise_count / len(labels)

    # 计算轮廓系数（需要至少 2 个簇且有非噪声样本）
    unique_labels = set(labels)
    n_clusters = len(unique_labels) - (1 if -1 in unique_labels else 0)

    silhouette = None
    if n_clusters >= 2 and noise_count < len(labels):
        # 只对非噪声样本计算轮廓系数
        non_noise_mask = labels != -1
        non_noise_count = np.sum(non_noise_mask)

        # 需要至少 2 个样本且至少 2 个不同的簇
        if non_noise_count >= 2 and len(set(labels[non_noise_mask])) >= 2:
            try:
                # 使用欧几里得距离（最稳定，不会有负值问题）
                silhouette = silhouette_score(
                    embeddings_array[non_noise_mask],
                    labels[non_noise_mask],
                    metric='euclidean',
                )
            except Exception as e:
                # 如果还是失败，记录错误并跳过
                from backend.common.log import log

                log.warning(f'Failed to calculate silhouette score: {e}')
                silhouette = None

    # ========================================
    # 构造聚类结果
    # ========================================
    clusters_result = []

    for label in sorted(unique_labels):
        if label == -1:
            continue  # 噪声单独处理

        cluster_indices = np.where(labels == label)[0]
        cluster_feedbacks = [
            {
                'id': valid_feedbacks[idx].id,
                'content': feedbacks_info[idx]['content'],
                'full_content': valid_feedbacks[idx].content,
            }
            for idx in cluster_indices
        ]

        # 计算簇内平均相似度
        cluster_similarities = []
        for i in range(len(cluster_indices)):
            cluster_similarities.extend(
                similarity_matrix[cluster_indices[i]][cluster_indices[j]] for j in range(i + 1, len(cluster_indices))
            )

        avg_similarity = float(np.mean(cluster_similarities)) if cluster_similarities else 0.0

        clusters_result.append({
            'cluster_id': int(label),
            'size': len(cluster_feedbacks),
            'feedbacks': cluster_feedbacks,
            'avg_similarity': round(avg_similarity, 4),
        })

    # 噪声样本
    noise_indices = np.where(labels == -1)[0]
    noise_feedbacks = [
        {
            'id': valid_feedbacks[idx].id,
            'content': feedbacks_info[idx]['content'],
            'full_content': valid_feedbacks[idx].content,
        }
        for idx in noise_indices
    ]

    # ========================================
    # 质量判断
    # ========================================
    quality_pass = True
    quality_issues = []

    if n_clusters == 0:
        quality_pass = False
        quality_issues.append('未形成任何聚类簇')

    if noise_ratio > settings.CLUSTERING_MAX_NOISE_RATIO:
        quality_pass = False
        quality_issues.append(f'噪声率过高: {noise_ratio:.2%} > {settings.CLUSTERING_MAX_NOISE_RATIO:.2%}')

    if silhouette is not None and silhouette < settings.CLUSTERING_MIN_SILHOUETTE:
        quality_pass = False
        quality_issues.append(f'轮廓系数过低: {silhouette:.3f} < {settings.CLUSTERING_MIN_SILHOUETTE:.3f}')

    # ========================================
    # 返回完整数据
    # ========================================
    return response_base.success(
        data={
            # 原有数据
            'feedbacks': feedbacks_info,
            'similarity_matrix': similarity_matrix.tolist(),
            'high_similarity_pairs': high_similarity_pairs,
            'stats': {
                'total_feedbacks': len(valid_feedbacks),
                'avg_similarity': float(np.mean(similarity_matrix[np.triu_indices_from(similarity_matrix, k=1)])),
                'max_similarity': float(np.max(similarity_matrix[np.triu_indices_from(similarity_matrix, k=1)])),
                'min_similarity': float(np.min(similarity_matrix[np.triu_indices_from(similarity_matrix, k=1)])),
                'pairs_above_075': len(high_similarity_pairs),
            },
            # 新增：聚类结果
            'clustering': {
                'parameters': {
                    'similarity_threshold': threshold,
                    'min_samples': min_samples_val,
                    'eps': round(eps, 4),
                },
                'results': {
                    'n_clusters': n_clusters,
                    'clusters': clusters_result,
                    'noise': {
                        'count': int(noise_count),
                        'ratio': round(noise_ratio, 4),
                        'feedbacks': noise_feedbacks,
                    },
                },
                'quality': {
                    'silhouette_score': round(silhouette, 4) if silhouette is not None else None,
                    'noise_ratio': round(noise_ratio, 4),
                    'pass': quality_pass,
                    'issues': quality_issues,
                    'thresholds': {
                        'min_silhouette': settings.CLUSTERING_MIN_SILHOUETTE,
                        'max_noise_ratio': settings.CLUSTERING_MAX_NOISE_RATIO,
                    },
                },
            },
        }
    )
