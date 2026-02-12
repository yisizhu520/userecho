"""聚类服务

负责反馈的 AI 聚类，生成需求主题
"""

from typing import Any

import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.feedalyze.crud import crud_feedback, crud_topic
from backend.common.log import log
from backend.utils.ai_client import ai_client
from backend.utils.clustering import clustering_engine


class ClusteringService:
    """AI 聚类服务"""

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

            # 1. 获取未聚类的反馈
            feedbacks = await crud_feedback.get_unclustered(db, tenant_id, limit=max_feedbacks)

            if len(feedbacks) < 2:
                return {
                    'status': 'skipped',
                    'message': f'反馈数量不足，至少需要 2 条 (当前: {len(feedbacks)})',
                    'feedbacks_count': len(feedbacks),
                    'clusters_count': 0,
                    'topics_created': 0
                }

            log.info(f'Found {len(feedbacks)} unclustered feedbacks')

            # 2. 批量获取 embedding
            embeddings = []
            valid_feedbacks = []

            for feedback in feedbacks:
                embedding = await ai_client.get_embedding(feedback.content)
                if embedding:
                    embeddings.append(embedding)
                    valid_feedbacks.append(feedback)
                else:
                    log.warning(f'Failed to get embedding for feedback: {feedback.id}')

            if len(embeddings) < 2:
                return {
                    'status': 'failed',
                    'message': '无法获取足够的 embedding 向量',
                    'feedbacks_count': len(feedbacks),
                    'valid_embeddings': len(embeddings),
                    'clusters_count': 0,
                    'topics_created': 0
                }

            embeddings_array = np.array(embeddings)
            log.info(f'Got {len(embeddings)} valid embeddings, shape: {embeddings_array.shape}')

            # 3. 执行聚类
            labels = clustering_engine.cluster(embeddings_array)

            # 4. 按聚类结果分组
            clusters: dict[int, list] = {}
            for idx, label in enumerate(labels):
                if label == -1:  # 噪声点，每个单独成一个主题
                    noise_label = f'noise_{idx}'
                    clusters[noise_label] = [valid_feedbacks[idx]]
                else:
                    if label not in clusters:
                        clusters[label] = []
                    clusters[label].append(valid_feedbacks[idx])

            log.info(f'Clustering completed: {len(clusters)} clusters')

            # 5. 为每个聚类创建 Topic
            created_topics = []
            failed_topics = []

            for label, cluster_feedbacks in clusters.items():
                try:
                    # 使用 AI 生成主题标题和分类
                    feedback_contents = [f.content for f in cluster_feedbacks]
                    topic_data = await ai_client.generate_topic_title(feedback_contents)

                    # 创建主题
                    from backend.database.db import uuid4_str

                    topic = await crud_topic.create(
                        db=db,
                        tenant_id=tenant_id,
                        id=uuid4_str(),
                        title=topic_data['title'],
                        category=topic_data['category'],
                        ai_generated=True,
                        ai_confidence=0.8,  # TODO: 后续可根据聚类质量动态计算
                        feedback_count=len(cluster_feedbacks)
                    )

                    # 批量更新反馈的 topic_id
                    feedback_ids = [f.id for f in cluster_feedbacks]
                    await crud_feedback.batch_update_topic(
                        db=db,
                        tenant_id=tenant_id,
                        feedback_ids=feedback_ids,
                        topic_id=topic.id
                    )

                    created_topics.append({
                        'topic_id': topic.id,
                        'title': topic.title,
                        'feedback_count': len(cluster_feedbacks),
                        'is_noise': str(label).startswith('noise_')
                    })

                    log.info(f'Created topic: {topic.title} with {len(cluster_feedbacks)} feedbacks')

                except Exception as e:
                    log.error(f'Failed to create topic for cluster {label}: {e}')
                    failed_topics.append({'label': label, 'error': str(e)})

            # 6. 计算聚类质量
            quality_metrics = clustering_engine.calculate_cluster_quality(embeddings_array, labels)

            return {
                'status': 'completed',
                'feedbacks_count': len(valid_feedbacks),
                'clusters_count': len(clusters),
                'topics_created': len(created_topics),
                'topics_failed': len(failed_topics),
                'topics': created_topics,
                'quality_metrics': quality_metrics,
            }

        except Exception as e:
            log.error(f'Clustering failed: {e}')
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
            target_embedding = await ai_client.get_embedding(target_feedback.content)
            if not target_embedding:
                return []

            # 获取所有已聚类的反馈
            all_feedbacks = await crud_feedback.get_multi(db, tenant_id, limit=1000)

            # 获取所有 embedding
            embeddings = []
            valid_feedbacks = []
            for feedback in all_feedbacks:
                if feedback.id == feedback_id:
                    continue  # 跳过自己

                # 尝试从 ai_metadata 中获取缓存的 embedding
                if feedback.ai_metadata and 'embedding' in feedback.ai_metadata:
                    embedding = feedback.ai_metadata['embedding']
                else:
                    embedding = await ai_client.get_embedding(feedback.content)

                if embedding:
                    embeddings.append(embedding)
                    valid_feedbacks.append(feedback)

            if not embeddings:
                return []

            # 查找最相似的反馈
            embeddings_array = np.array(embeddings)
            similar_indices = clustering_engine.find_similar_feedbacks(
                np.array(target_embedding),
                embeddings_array,
                top_k=top_k
            )

            # 构造返回结果
            results = []
            for idx, similarity in similar_indices:
                feedback = valid_feedbacks[idx]
                results.append({
                    'feedback_id': feedback.id,
                    'content': feedback.content,
                    'similarity': similarity,
                    'topic_id': feedback.topic_id,
                    'topic_title': None,  # TODO: 关联查询 topic 标题
                })

            return results

        except Exception as e:
            log.error(f'Failed to get clustering suggestions: {e}')
            return []


clustering_service = ClusteringService()
