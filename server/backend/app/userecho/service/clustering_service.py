"""聚类服务

负责反馈的 AI 聚类，生成需求主题
"""

from typing import Any

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.userecho.crud import crud_feedback, crud_topic
from backend.common.log import log
from backend.core.conf import settings
from backend.utils.timezone import timezone
from backend.utils.ai_client import ai_client
from backend.utils.clustering import clustering_engine


class ClusteringService:
    """AI 聚类服务"""

    @staticmethod
    def _is_clustering_acceptable(quality: dict[str, float]) -> bool:
        """
        质量门槛：先评估，再创建 Topic（避免制造低质量垃圾数据）

        注意：当没有任何有效聚类（全是噪声点）时，silhouette/noise_ratio 会非常差，
        但这不是错误，只代表“这批数据暂时不该生成 Topic”。
        """
        try:
            return (
                quality.get('silhouette', 0.0) >= settings.CLUSTERING_MIN_SILHOUETTE
                and quality.get('noise_ratio', 1.0) <= settings.CLUSTERING_MAX_NOISE_RATIO
            )
        except Exception:
            return False

    async def trigger_clustering(
        self,
        db: AsyncSession,
        tenant_id: str,
        max_feedbacks: int = 100,
        force_recluster: bool = False,
    ) -> dict[str, Any]:
        """
        触发聚类任务

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            max_feedbacks: 最多处理的反馈数量
            force_recluster: 是否强制重新聚类（默认只聚类未聚类的反馈）

        Returns:
            聚类结果统计
        """
        try:
            log.info(f'Starting clustering for tenant: {tenant_id}')

            # 1. 获取待聚类的反馈（避免噪声点 topic_id=NULL 被反复聚类）
            feedbacks = await crud_feedback.get_pending_clustering(
                db=db,
                tenant_id=tenant_id,
                limit=max_feedbacks,
                include_failed=True,
                force_recluster=force_recluster,
            )

            min_required = max(2, settings.CLUSTERING_MIN_SAMPLES)
            if len(feedbacks) < min_required:
                return {
                    'status': 'skipped',
                    'message': f'反馈数量不足，至少需要 {min_required} 条 (当前: {len(feedbacks)})',
                    'feedbacks_count': len(feedbacks),
                    'clusters_count': 0,
                    'topics_created': 0,
                }

            log.debug(f'Found {len(feedbacks)} unclustered feedbacks for tenant {tenant_id}')

            started_at = timezone.now()
            feedback_ids = [f.id for f in feedbacks]
            await crud_feedback.batch_update_clustering(
                db=db,
                tenant_id=tenant_id,
                feedback_ids=feedback_ids,
                clustering_status='processing',
                clustering_metadata={'started_at': started_at.isoformat()},
            )

            # 2. 获取 embedding（优先使用缓存，然后批量调用 API）
            embeddings = []
            valid_feedbacks = []
            feedbacks_need_embedding = []  # 需要调用 API 的反馈

            # 2.1 先尝试从缓存读取
            cache_hit = 0
            for feedback in feedbacks:
                cached_embedding = crud_feedback.get_cached_embedding(feedback)
                if cached_embedding is not None:  # 修复：numpy.ndarray 不能直接用 if 判断
                    embeddings.append(cached_embedding)
                    valid_feedbacks.append(feedback)
                    cache_hit += 1
                else:
                    # 需要调用 API
                    feedbacks_need_embedding.append(feedback)

            log.info(f'Embedding cache hit: {cache_hit}/{len(feedbacks)} ({cache_hit/len(feedbacks)*100:.1f}%)')

            # 2.2 批量调用 API 获取缺失的 embedding
            failed_embedding_ids: list[str] = []
            if feedbacks_need_embedding:
                contents = [f.content for f in feedbacks_need_embedding]
                embeddings_batch = await ai_client.get_embeddings_batch(contents, batch_size=50)

                # 2.3 缓存新获取的 embedding
                embeddings_to_cache = {}
                for feedback, embedding in zip(feedbacks_need_embedding, embeddings_batch):
                    if embedding is not None:  # 明确检查 None，而不是依赖布尔转换
                        embeddings.append(embedding)
                        valid_feedbacks.append(feedback)
                        embeddings_to_cache[feedback.id] = embedding
                    else:
                        log.warning(f'Failed to get embedding for feedback: {feedback.id}')
                        failed_embedding_ids.append(feedback.id)

                # 2.4 批量写入缓存
                if embeddings_to_cache:
                    cached_count = await crud_feedback.batch_update_embeddings(
                        db=db,
                        tenant_id=tenant_id,
                        feedback_embeddings=embeddings_to_cache
                    )
                    log.info(f'Cached {cached_count} new embeddings to database')

            if failed_embedding_ids:
                await crud_feedback.batch_update_clustering(
                    db=db,
                    tenant_id=tenant_id,
                    feedback_ids=failed_embedding_ids,
                    clustering_status='failed',
                    clustering_metadata={
                        'failed_at': timezone.now().isoformat(),
                        'reason': 'embedding_failed',
                    },
                )

            if len(embeddings) < min_required:
                remaining_ids = [f.id for f in valid_feedbacks]
                if remaining_ids:
                    await crud_feedback.batch_update_clustering(
                        db=db,
                        tenant_id=tenant_id,
                        feedback_ids=remaining_ids,
                        clustering_status='failed',
                        clustering_metadata={
                            'failed_at': timezone.now().isoformat(),
                            'reason': 'not_enough_embeddings',
                        },
                    )
                return {
                    'status': 'failed',
                    'message': '无法获取足够的 embedding 向量',
                    'feedbacks_count': len(feedbacks),
                    'valid_embeddings': len(embeddings),
                    'clusters_count': 0,
                    'topics_created': 0
                }

            embeddings_array = np.array(embeddings)
            log.info(f'Batch embedding completed: {len(embeddings)}/{len(feedbacks)} valid, shape: {embeddings_array.shape}')

            # 4. 执行聚类
            labels = clustering_engine.cluster(embeddings_array)

            # 5. 质量评估（先评估，再创建）
            quality_metrics = clustering_engine.calculate_cluster_quality(embeddings_array, labels)
            n_clusters = len(set(labels)) - (1 if -1 in labels else 0)

            # 全是噪声点：标记为 clustered，但不生成 Topic（避免垃圾 Topic）
            if n_clusters == 0:
                noise_ids = [valid_feedbacks[idx].id for idx, label in enumerate(labels) if label == -1]
                if noise_ids:
                    await crud_feedback.batch_update_clustering(
                        db=db,
                        tenant_id=tenant_id,
                        feedback_ids=noise_ids,
                        clustering_status='clustered',
                        clustering_metadata={
                            'cluster_label': -1,
                            'clustered_at': timezone.now().isoformat(),
                            'quality': quality_metrics,
                            'reason': 'all_noise',
                        },
                    )

                return {
                    'status': 'completed',
                    'message': '本次聚类没有形成有效簇（全部为噪声点），已标记为已处理',
                    'feedbacks_count': len(valid_feedbacks),
                    'clusters_count': 0,
                    'topics_created': 0,
                    'topics_failed': 0,
                    'topics': [],
                    'noise_count': len(noise_ids),
                    'quality_metrics': quality_metrics,
                }

            if not self._is_clustering_acceptable(quality_metrics):
                # 不生成 Topic，把反馈放回 pending（等待更多数据/参数调整）
                pending_ids = [f.id for f in valid_feedbacks]
                if pending_ids:
                    await crud_feedback.batch_update_clustering(
                        db=db,
                        tenant_id=tenant_id,
                        feedback_ids=pending_ids,
                        clustering_status='pending',
                        clustering_metadata={
                            'deferred_at': timezone.now().isoformat(),
                            'reason': 'quality_gate',
                            'quality': quality_metrics,
                        },
                    )
                return {
                    'status': 'skipped',
                    'message': '聚类质量未达门槛，本次不生成主题（已延期，等待更多反馈或调整阈值）',
                    'feedbacks_count': len(valid_feedbacks),
                    'clusters_count': int(n_clusters),
                    'topics_created': 0,
                    'topics_failed': 0,
                    'topics': [],
                    'quality_metrics': quality_metrics,
                }

            # 6. 按聚类结果分组（噪声点单独处理，不创建 Topic）
            clusters: dict[int, list[int]] = {}
            noise_indices: list[int] = []
            for idx, label in enumerate(labels):
                if label == -1:
                    noise_indices.append(idx)
                    continue
                clusters.setdefault(int(label), []).append(idx)

            log.info(f'Clustering completed for tenant {tenant_id}: {len(clusters)} clusters, {len(noise_indices)} noise points')

            # 7. 为每个聚类创建 Topic
            created_topics = []
            failed_topics = []

            for label, indices in clusters.items():
                try:
                    cluster_feedbacks = [valid_feedbacks[i] for i in indices]
                    cluster_embeddings = embeddings_array[indices]

                    # 使用 AI 生成主题标题和分类
                    feedback_contents = [f.content for f in cluster_feedbacks]
                    topic_data = await ai_client.generate_topic_title(feedback_contents)

                    # 计算中心向量（均值）
                    centroid = np.mean(cluster_embeddings, axis=0).astype(float).tolist()

                    # 计算簇内平均相似度（用于展示/置信度）
                    avg_similarity = 1.0
                    if len(indices) >= 2:
                        from sklearn.metrics.pairwise import cosine_similarity

                        sim = cosine_similarity(cluster_embeddings)
                        upper = sim[np.triu_indices_from(sim, k=1)]
                        if upper.size > 0:
                            avg_similarity = float(np.mean(upper))

                    # 简单置信度：相似度 + 规模（MVP 版本）
                    size_factor = min(1.0, len(indices) / 5.0)
                    similarity_factor = max(0.0, min(1.0, (avg_similarity - settings.CLUSTERING_SIMILARITY_THRESHOLD) / (1 - settings.CLUSTERING_SIMILARITY_THRESHOLD)))
                    confidence = float(min(1.0, 0.2 + 0.8 * size_factor * similarity_factor))

                    topic = await crud_topic.create(
                        db=db,
                        tenant_id=tenant_id,
                        title=topic_data['title'],
                        category=topic_data['category'],
                        ai_generated=True,
                        ai_confidence=confidence,
                        feedback_count=len(cluster_feedbacks),
                        centroid=centroid,
                        cluster_quality={
                            'silhouette': quality_metrics.get('silhouette', 0.0),
                            'noise_ratio': quality_metrics.get('noise_ratio', 1.0),
                            'confidence': confidence,
                            'avg_similarity': avg_similarity,
                            'size': len(cluster_feedbacks),
                        },
                        is_noise=False,
                    )

                    feedback_ids = [f.id for f in cluster_feedbacks]
                    await crud_feedback.batch_update_clustering(
                        db=db,
                        tenant_id=tenant_id,
                        feedback_ids=feedback_ids,
                        clustering_status='clustered',
                        topic_id=topic.id,
                        clustering_metadata={
                            'cluster_label': int(label),
                            'clustered_at': timezone.now().isoformat(),
                            'topic_id': topic.id,
                            'confidence': confidence,
                        },
                    )

                    created_topics.append({
                        'topic_id': topic.id,
                        'title': topic.title,
                        'feedback_count': len(cluster_feedbacks),
                        'is_noise': False,
                    })

                    log.debug(f'Created topic: {topic.title} with {len(cluster_feedbacks)} feedbacks')

                except Exception as e:
                    log.error(f'Failed to create topic for cluster {label}, tenant {tenant_id}: {e}')
                    failed_topics.append({'label': label, 'error': str(e)})

            # 噪声点：标记为 clustered，但保持 topic_id=NULL
            if noise_indices:
                noise_ids = [valid_feedbacks[i].id for i in noise_indices]
                await crud_feedback.batch_update_clustering(
                    db=db,
                    tenant_id=tenant_id,
                    feedback_ids=noise_ids,
                    clustering_status='clustered',
                    clustering_metadata={
                        'cluster_label': -1,
                        'clustered_at': timezone.now().isoformat(),
                        'quality': quality_metrics,
                        'reason': 'noise',
                    },
                )

            log.info(f'Topic creation completed for tenant {tenant_id}: {len(created_topics)} created, {len(failed_topics)} failed')

            return {
                'status': 'completed',
                'feedbacks_count': len(valid_feedbacks),
                'clusters_count': len(clusters),
                'topics_created': len(created_topics),
                'topics_failed': len(failed_topics),
                'topics': created_topics,
                'noise_count': len(noise_indices),
                'quality_metrics': quality_metrics,
                'elapsed_ms': int((timezone.now() - started_at).total_seconds() * 1000),
            }

        except Exception as e:
            log.error(f'Clustering failed for tenant {tenant_id}: {e}')
            # 最好努力把 status 从 processing 拉回 failed，避免卡死
            try:
                await crud_feedback.batch_update_clustering(
                    db=db,
                    tenant_id=tenant_id,
                    feedback_ids=[f.id for f in feedbacks] if 'feedbacks' in locals() else [],
                    clustering_status='failed',
                    clustering_metadata={
                        'failed_at': timezone.now().isoformat(),
                        'reason': 'exception',
                        'error': str(e),
                    },
                )
            except Exception:
                pass
            return {
                'status': 'error',
                'message': str(e),
                'feedbacks_count': 0,
                'clusters_count': 0,
                'topics_created': 0
            }

    async def get_clustering_suggestions(
        self,
        db: AsyncSession,
        tenant_id: str,
        feedback_id: str,
        top_k: int = 5,
    ) -> list[dict]:
        """
        获取反馈的聚类建议（查找相似反馈）

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            feedback_id: 反馈ID
            top_k: 返回最相似的 K 个反馈

        Returns:
            相似反馈列表
        """
        try:
            # 获取目标反馈
            target_feedback = await crud_feedback.get_by_id(db, tenant_id, feedback_id)
            if not target_feedback:
                return []

            # 获取目标反馈的 embedding
            target_embedding = target_feedback.embedding
            if not target_embedding:
                target_embedding = await ai_client.get_embedding(target_feedback.content)
                if not target_embedding:
                    return []
                await crud_feedback.update_embedding(
                    db=db,
                    tenant_id=tenant_id,
                    feedback_id=target_feedback.id,
                    embedding=target_embedding,
                )

            # 使用 pgvector 向量搜索（性能更好，避免 Python 侧 O(n^2)）
            similar = await crud_feedback.find_similar_feedbacks(
                db=db,
                tenant_id=tenant_id,
                query_embedding=target_embedding,
                limit=top_k + 1,  # 多取 1 个，方便过滤自己
                min_similarity=min(0.8, settings.CLUSTERING_SIMILARITY_THRESHOLD),
            )

            # 过滤自己
            similar = [(fb, sim) for fb, sim in similar if fb.id != feedback_id][:top_k]
            if not similar:
                return []

            # 批量拉取 topic 标题
            topic_ids = {fb.topic_id for fb, _ in similar if fb.topic_id}
            topic_title_map: dict[str, str] = {}
            if topic_ids:
                from backend.app.userecho.model.topic import Topic

                q = select(Topic.id, Topic.title).where(
                    Topic.tenant_id == tenant_id,
                    Topic.id.in_(list(topic_ids)),
                    Topic.deleted_at.is_(None),
                )
                rows = (await db.execute(q)).all()
                topic_title_map = {str(tid): title for tid, title in rows}

            return [
                {
                    'feedback_id': fb.id,
                    'content': fb.content,
                    'similarity': similarity,
                    'topic_id': fb.topic_id,
                    'topic_title': topic_title_map.get(fb.topic_id or '', None),
                }
                for fb, similarity in similar
            ]

        except Exception as e:
            log.error(f'Failed to get clustering suggestions for feedback {feedback_id}, tenant {tenant_id}: {e}')
            return []


clustering_service = ClusteringService()
