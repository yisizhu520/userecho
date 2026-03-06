"""聚类服务

负责反馈的 AI 聚类，生成需求主题
"""

import operator

from typing import Any

import numpy as np

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.userecho.crud import crud_feedback, crud_topic
from backend.app.userecho.service.clustering_config_service import clustering_config_service
from backend.app.userecho.service.clustering_validator import ClusteringValidator
from backend.common.log import log
from backend.core.conf import settings
from backend.utils.ai_client import ai_client
from backend.utils.clustering import FeedbackClustering
from backend.utils.timezone import timezone


class ClusteringService:
    """AI 聚类服务"""

    async def trigger_clustering(
        self,
        db: AsyncSession,
        tenant_id: str,
        max_feedbacks: int = 100,
        force_recluster: bool = False,
        board_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        触发聚类任务（支持按看板独立聚类）

        ✅ Linus 优化：拆分为多个短事务，避免 LLM 验证期间长期持有数据库连接

        Args:
            db: 数据库会话（仅用于获取配置和反馈，不用于 LLM 验证和 Topic 创建）
            tenant_id: 租户ID
            max_feedbacks: 最多处理的反馈数量
            force_recluster: 是否强制重新聚类
            board_ids: 可选，指定需要聚类的看板ID列表。每个看板会独立聚类。

        Returns:
            聚类结果统计
        """
        # 如果指定了 board_ids，则循环处理每个看板
        if board_ids:
            aggregate_result = {
                "status": "completed",
                "feedbacks_count": 0,
                "clusters_count": 0,
                "topics_created": 0,
                "topics_failed": 0,
                "merge_suggestions": [],
                "details": [],
            }

            for board_id in board_ids:
                # 针对每个看板单独执行聚类
                res = await self._trigger_clustering_internal(
                    db, tenant_id, max_feedbacks, force_recluster, board_id=board_id
                )

                # 聚合统计结果
                aggregate_result["feedbacks_count"] += res.get("feedbacks_count", 0)
                aggregate_result["clusters_count"] += res.get("clusters_count", 0)
                aggregate_result["topics_created"] += res.get("topics_created", 0)
                aggregate_result["topics_failed"] += res.get("topics_failed", 0)
                aggregate_result["merge_suggestions"].extend(res.get("merge_suggestions", []))

                # 保留每次运行的简要信息
                aggregate_result["details"].append(
                    {"board_id": board_id, "status": res.get("status"), "topics_created": res.get("topics_created", 0)}
                )

            return aggregate_result

        # 如果没有指定 board_ids，则执行全局聚类（兼容旧行为）
        return await self._trigger_clustering_internal(db, tenant_id, max_feedbacks, force_recluster, board_id=None)

    async def _trigger_clustering_internal(
        self,
        db: AsyncSession,
        tenant_id: str,
        max_feedbacks: int = 100,
        force_recluster: bool = False,
        board_id: str | None = None,
    ) -> dict[str, Any]:
        """
        内部方法：执行单次聚类任务（限定在指定 board_id 范围内）

        ✅ Linus 优化：拆分为多个短事务
        - 事务 1（快速）：领取反馈并标记 processing（SKIP LOCKED）
        - 无事务：聚类计算/LLM 验证（纯内存操作，无数据库）
        - 事务 2（快速）：创建 Topic（新 session）
        """
        # ============================================================
        # 事务 1：聚类计算（快速，< 5 秒）
        # ============================================================
        try:
            log.info(f"Starting clustering for tenant: {tenant_id}")

            from backend.app.task.tasks.userecho.tasks import local_db_session

            # 0. 获取租户聚类配置（短事务）
            async with local_db_session() as db_cfg:
                tenant_config = await clustering_config_service.get_clustering_config(db_cfg, tenant_id)
            log.info(f"Using clustering config for tenant {tenant_id}: preset={tenant_config.get('preset_mode')}")

            # 1. 原子领取待聚类反馈并标记 processing（短事务，避免长时间持锁）
            log.info(
                f"Fetching pending feedbacks for tenant {tenant_id}: limit={max_feedbacks}, "
                f"force_recluster={force_recluster}, board_id={board_id}"
            )
            fetch_started_at = timezone.now()
            started_at = timezone.now()
            try:
                async with local_db_session() as db_claim:
                    # 防止锁等待无限期卡住
                    try:
                        await db_claim.execute(text("SET LOCAL lock_timeout = '5s'"))
                        await db_claim.execute(text("SET LOCAL statement_timeout = '30s'"))
                    except Exception as e:
                        log.warning(f"Failed to set lock/statement timeout for tenant {tenant_id}: {e}")

                    feedbacks = await crud_feedback.claim_pending_clustering(
                        db=db_claim,
                        tenant_id=tenant_id,
                        limit=max_feedbacks,
                        include_failed=True,
                        force_recluster=force_recluster,
                        board_id=board_id,
                        started_at=started_at,
                    )
            except Exception as e:
                log.error(f"Failed to claim feedbacks for tenant {tenant_id}: {e}")
                return {
                    "status": "error",
                    "message": f"领取反馈失败（可能锁等待超时）: {str(e)}",
                    "feedbacks_count": 0,
                    "clusters_count": 0,
                    "topics_created": 0,
                }

            log.info(
                f"Fetched {len(feedbacks)} feedbacks for tenant {tenant_id} in "
                f"{(timezone.now() - fetch_started_at).total_seconds():.3f}s"
            )

            min_required = max(2, tenant_config.get("min_samples", 2))
            if len(feedbacks) < min_required:
                if feedbacks:
                    async with local_db_session() as db_revert:
                        await crud_feedback.batch_update_clustering(
                            db=db_revert,
                            tenant_id=tenant_id,
                            feedback_ids=[f["id"] for f in feedbacks],
                            clustering_status="pending",
                            clustering_metadata={
                                "deferred_at": timezone.now().isoformat(),
                                "reason": "not_enough_samples",
                            },
                        )
                return {
                    "status": "skipped",
                    "message": f"反馈数量不足，至少需要 {min_required} 条 (当前: {len(feedbacks)})",
                    "feedbacks_count": len(feedbacks),
                    "clusters_count": 0,
                    "topics_created": 0,
                }

            log.debug(f"Found {len(feedbacks)} unclustered feedbacks for tenant {tenant_id}")

            # 2. 获取 embedding（优先使用缓存，然后批量调用 API）
            embeddings = []
            valid_feedbacks = []
            feedbacks_need_embedding = []  # 需要调用 API 的反馈

            # 2.1 先尝试从缓存读取
            cache_hit = 0
            cache_started_at = timezone.now()
            for feedback in feedbacks:
                cached_embedding = feedback.get("embedding")
                if cached_embedding is not None:  # 修复：numpy.ndarray 不能直接用 if 判断
                    embeddings.append(cached_embedding)
                    valid_feedbacks.append(feedback)
                    cache_hit += 1
                else:
                    # 需要调用 API
                    feedbacks_need_embedding.append(feedback)

            log.info(
                f"Embedding cache scan completed for tenant {tenant_id} in "
                f"{(timezone.now() - cache_started_at).total_seconds():.3f}s"
            )

            log.info(f"Embedding cache hit: {cache_hit}/{len(feedbacks)} ({cache_hit / len(feedbacks) * 100:.1f}%)")

            # 2.2 批量调用 API 获取缺失的 embedding
            failed_embedding_ids: list[str] = []
            if feedbacks_need_embedding:
                log.info(
                    f"Fetching embeddings for {len(feedbacks_need_embedding)} feedbacks, "
                    f"batch_size=50, tenant={tenant_id}"
                )
                embed_started_at = timezone.now()
                contents = [f["content"] for f in feedbacks_need_embedding]
                embeddings_batch = await ai_client.get_embeddings_batch(contents, batch_size=50)
                log.info(
                    f"Embeddings fetched for tenant {tenant_id} in "
                    f"{(timezone.now() - embed_started_at).total_seconds():.3f}s"
                )

                # 2.3 缓存新获取的 embedding
                embeddings_to_cache = {}
                for feedback, embedding in zip(feedbacks_need_embedding, embeddings_batch):
                    if embedding is not None:  # 明确检查 None，而不是依赖布尔转换
                        embeddings.append(embedding)
                        valid_feedbacks.append(feedback)
                        embeddings_to_cache[feedback["id"]] = embedding
                    else:
                        log.warning(f"Failed to get embedding for feedback: {feedback['id']}")
                        failed_embedding_ids.append(feedback["id"])

                # 2.4 批量写入缓存
                if embeddings_to_cache:
                    async with local_db_session() as db_cache:
                        cached_count = await crud_feedback.batch_update_embeddings(
                            db=db_cache, tenant_id=tenant_id, feedback_embeddings=embeddings_to_cache
                        )
                    log.info(f"Cached {cached_count} new embeddings to database")

            if failed_embedding_ids:
                try:
                    async with local_db_session() as db_failed:
                        await crud_feedback.batch_update_clustering(
                            db=db_failed,
                            tenant_id=tenant_id,
                            feedback_ids=failed_embedding_ids,
                            clustering_status="failed",
                            clustering_metadata={
                                "failed_at": timezone.now().isoformat(),
                                "reason": "embedding_failed",
                            },
                        )
                except Exception as e:
                    log.error(f"Failed to update embedding failed status: {e}")

            if len(embeddings) < min_required:
                remaining_ids = [f["id"] for f in valid_feedbacks]
                if remaining_ids:
                    try:
                        async with local_db_session() as db_insufficient:
                            await crud_feedback.batch_update_clustering(
                                db=db_insufficient,
                                tenant_id=tenant_id,
                                feedback_ids=remaining_ids,
                                clustering_status="failed",
                                clustering_metadata={
                                    "failed_at": timezone.now().isoformat(),
                                    "reason": "not_enough_embeddings",
                                },
                            )
                    except Exception as e:
                        log.error(f"Failed to update insufficient embeddings status: {e}")
                return {
                    "status": "failed",
                    "message": "无法获取足够的 embedding 向量",
                    "feedbacks_count": len(feedbacks),
                    "valid_embeddings": len(embeddings),
                    "clusters_count": 0,
                    "topics_created": 0,
                }

            embeddings_array = np.array(embeddings)
            log.info(
                f"Batch embedding completed: {len(embeddings)}/{len(feedbacks)} valid, shape: {embeddings_array.shape}"
            )

            # 4. 使用租户配置创建聚类引擎并执行聚类
            clustering_engine = FeedbackClustering(
                similarity_threshold=tenant_config.get("similarity_threshold", 0.85),
                min_samples=tenant_config.get("min_samples", 2),
            )

            # 根据配置选择聚类算法
            use_hdbscan = settings.CLUSTERING_USE_HDBSCAN
            if use_hdbscan:
                min_cluster_size = settings.CLUSTERING_HDBSCAN_MIN_CLUSTER_SIZE
                min_samples = settings.CLUSTERING_HDBSCAN_MIN_SAMPLES
                log.info(f"Using HDBSCAN: min_cluster_size={min_cluster_size}, min_samples={min_samples}")
                labels = clustering_engine.cluster_hdbscan(
                    embeddings_array, min_cluster_size=min_cluster_size, min_samples=min_samples
                )
            else:
                log.info(f"Using DBSCAN: threshold={tenant_config.get('similarity_threshold', 0.85)}")
                labels = clustering_engine.cluster(embeddings_array)

            # 5. 质量评估（先评估，再创建）
            quality_metrics = clustering_engine.calculate_cluster_quality(embeddings_array, labels)
            n_clusters = len(set(labels)) - (1 if -1 in labels else 0)

            # ✅ Linus: "全噪声点保持 pending，等后续再聚类。clustered 只用于已关联 Topic 的反馈。"
            # 全是噪声点：保持 pending 状态，等待后续聚类（可能会有更多相似反馈）
            if n_clusters == 0:
                noise_count = sum(1 for label in labels if label == -1)
                log.info(
                    f"All feedbacks are noise points ({noise_count} feedbacks), keeping pending status for future clustering"
                )

                # 将 processing 状态改回 pending（不标记为 clustered）
                noise_ids = [valid_feedbacks[idx]["id"] for idx, label in enumerate(labels) if label == -1]
                if noise_ids:
                    try:
                        async with local_db_session() as db_noise:
                            await crud_feedback.batch_update_clustering(
                                db=db_noise,
                                tenant_id=tenant_id,
                                feedback_ids=noise_ids,
                                clustering_status="pending",  # ✅ 改为 pending
                                clustering_metadata={
                                    "last_attempt_at": timezone.now().isoformat(),
                                    "reason": "all_noise",
                                    "quality": quality_metrics,
                                },
                            )
                    except Exception as e:
                        log.error(f"Failed to reset noise feedbacks to pending: {e}")

                return {
                    "status": "completed",
                    "message": "本次聚类全部为噪声点，已重置为待聚类状态（等待后续更多相似反馈）",
                    "feedbacks_count": len(valid_feedbacks),
                    "clusters_count": 0,
                    "topics_created": 0,
                    "topics_failed": 0,
                    "topics": [],
                    "noise_count": noise_count,
                    "quality_metrics": quality_metrics,
                }

            # 6. 按聚类结果分组（噪声点单独处理，不创建 Topic）
            # ✅ Linus: "质量门槛已移除，直接创建 Topic，让数据说话！"
            initial_clusters: dict[int, list[int]] = {}
            noise_indices: list[int] = []
            for idx, label in enumerate(labels):
                if label == -1:
                    noise_indices.append(idx)
                    continue
                initial_clusters.setdefault(int(label), []).append(idx)

            log.info(
                f"Initial clustering completed for tenant {tenant_id}: {len(initial_clusters)} clusters, {len(noise_indices)} noise points"
            )

            # 7. LLM 语义校验（可选）
            clusters = initial_clusters
            llm_validation_enabled = settings.CLUSTERING_LLM_VALIDATION_ENABLED
            llm_min_size = settings.CLUSTERING_LLM_VALIDATION_MIN_SIZE

            if llm_validation_enabled and len(initial_clusters) > 0:
                log.info(f"LLM validation enabled: validating clusters with size >= {llm_min_size}")
                validator = ClusteringValidator()
                refined_clusters: dict[int, list[int]] = {}
                next_cluster_id = 0
                validation_count = 0
                split_count = 0

                for cluster_id, cluster_indices in initial_clusters.items():
                    if len(cluster_indices) >= llm_min_size:
                        # 需要 LLM 校验的大聚类
                        validation_count += 1
                        cluster_feedbacks_data = [valid_feedbacks[i] for i in cluster_indices]

                        try:
                            # 构建 Feedback 对象用于 LLM 校验
                            from backend.app.userecho.model.feedback import Feedback as FeedbackModel

                            feedback_objs = []
                            for f_data in cluster_feedbacks_data:
                                feedback_obj = FeedbackModel()
                                feedback_obj.id = f_data["id"]
                                feedback_obj.content = f_data["content"]
                                feedback_objs.append(feedback_obj)

                            result = await validator.validate_cluster_with_llm(feedback_objs)

                            if result.is_valid:
                                # 保持原聚类
                                refined_clusters[next_cluster_id] = cluster_indices
                                next_cluster_id += 1
                                log.info(
                                    f"Cluster #{cluster_id} validated: {len(cluster_indices)} feedbacks - {result.common_theme}"
                                )
                            elif result.sub_clusters and len(result.sub_clusters) > 0:
                                # LLM 建议拆分为子聚类
                                split_count += 1
                                log.info(
                                    f"Cluster #{cluster_id} split into {len(result.sub_clusters)} sub-clusters: {result.reason}"
                                )

                                for sub_cluster in result.sub_clusters:
                                    # feedback_indices 是从 1 开始的，转换为实际索引
                                    sub_indices = [
                                        cluster_indices[i - 1]
                                        for i in sub_cluster.feedback_indices
                                        if 0 < i <= len(cluster_indices)
                                    ]

                                    # 只保留至少 2 条反馈的子聚类
                                    if len(sub_indices) >= 2:
                                        refined_clusters[next_cluster_id] = sub_indices
                                        next_cluster_id += 1
                                        log.info(f"  → Sub-cluster: {sub_cluster.theme} ({len(sub_indices)} feedbacks)")
                                    else:
                                        # 单条反馈标记为噪声
                                        noise_indices.extend(sub_indices)
                            else:
                                # 无法拆分，标记为噪声
                                split_count += 1
                                noise_indices.extend(cluster_indices)
                                log.info(f"Cluster #{cluster_id} marked as noise: {result.reason}")

                        except Exception as e:
                            # LLM 校验失败，保留原聚类
                            log.error(f"LLM validation failed for cluster #{cluster_id}: {e}")
                            refined_clusters[next_cluster_id] = cluster_indices
                            next_cluster_id += 1
                    else:
                        # 小聚类直接保留（不需要 LLM 校验）
                        refined_clusters[next_cluster_id] = cluster_indices
                        next_cluster_id += 1

                clusters = refined_clusters
                log.info(
                    f"LLM validation completed: validated={validation_count}, split={split_count}, "
                    f"final_clusters={len(clusters)}, noise={len(noise_indices)}"
                )

            # ============================================================
            # 关键：提取所有需要的数据，准备释放数据库连接
            # ============================================================
            # 提取 feedback 的纯数据（ID、content、board_id、customer_id），避免使用 ORM 对象
            feedbacks_data = [
                {
                    "id": f["id"],
                    "content": f["content"],
                    "board_id": f["board_id"],
                    "customer_id": f["customer_id"],
                }
                for f in valid_feedbacks
            ]

            # 构建聚类结果数据（纯字典，无 ORM 对象）
            clustering_result = {
                "tenant_id": tenant_id,
                "tenant_config": tenant_config,
                "feedbacks_data": feedbacks_data,
                "embeddings_array": embeddings_array,
                "clusters": clusters,
                "noise_indices": noise_indices,
                "quality_metrics": quality_metrics,
                "started_at": started_at,
                "feedbacks_need_embedding": feedbacks_need_embedding,
            }

            # ============================================================
            # 无事务：预生成 Topic 标题（AI 调用）
            # ============================================================
            topic_summaries: dict[int, dict[str, object]] = {}
            for label, indices in clusters.items():
                try:
                    cluster_feedbacks_data = [feedbacks_data[i] for i in indices]
                    feedback_contents = [f["content"] for f in cluster_feedbacks_data]
                    topic_data = await ai_client.generate_topic_title(feedback_contents)

                    title = topic_data.get("title") if isinstance(topic_data, dict) else None
                    category = topic_data.get("category") if isinstance(topic_data, dict) else None
                    description = topic_data.get("description") if isinstance(topic_data, dict) else None

                    topic_summaries[int(label)] = {
                        "title": title or "未命名主题",
                        "category": category or "other",
                        "description": description,
                    }
                except Exception as e:
                    log.warning(f"Failed to generate topic summary for cluster {label}: {e}")
                    topic_summaries[int(label)] = {
                        "title": "未命名主题",
                        "category": "other",
                        "description": None,
                    }

            clustering_result["topic_summaries"] = topic_summaries

        except Exception as e:
            log.error(f"Clustering calculation failed for tenant {tenant_id}: {e}")
            # 失败时标记反馈状态
            try:
                if "feedbacks" in locals() and feedbacks:
                    async with local_db_session() as db_fail:
                        await crud_feedback.batch_update_clustering(
                            db=db_fail,
                            tenant_id=tenant_id,
                            feedback_ids=[f["id"] for f in feedbacks],
                            clustering_status="failed",
                            clustering_metadata={
                                "failed_at": timezone.now().isoformat(),
                                "reason": "exception",
                                "error": str(e),
                            },
                        )
            except Exception:
                pass
            return {
                "status": "error",
                "message": str(e),
                "feedbacks_count": 0,
                "clusters_count": 0,
                "topics_created": 0,
            }

        # ============================================================
        # 事务 2：创建 Topic（使用新的 session，快速完成）
        # ============================================================
        from backend.app.task.tasks.userecho.tasks import local_db_session

        try:
            async with local_db_session() as db_new:
                return await self._create_topics_from_clusters(db_new, clustering_result)
        except Exception as e:
            log.error(f"Topic creation failed for tenant {tenant_id}: {e}")
            return {
                "status": "error",
                "message": f"Topic 创建失败: {str(e)}",
                "feedbacks_count": len(clustering_result.get("feedbacks_data", [])),
                "clusters_count": len(clustering_result.get("clusters", {})),
                "topics_created": 0,
            }

    async def _create_topics_from_clusters(
        self,
        db: AsyncSession,
        clustering_result: dict[str, Any],
    ) -> dict[str, Any]:
        """
        从聚类结果创建 Topic（在新的事务中）

        Args:
            db: 新的数据库 session
            clustering_result: 聚类结果数据（纯字典，无 ORM 对象）
        """
        tenant_id = clustering_result["tenant_id"]
        tenant_config = clustering_result["tenant_config"]
        feedbacks_data = clustering_result["feedbacks_data"]
        embeddings_array = clustering_result["embeddings_array"]
        clusters = clustering_result["clusters"]
        noise_indices = clustering_result["noise_indices"]
        quality_metrics = clustering_result["quality_metrics"]
        started_at = clustering_result["started_at"]
        feedbacks_need_embedding = clustering_result["feedbacks_need_embedding"]
        topic_summaries: dict[int, dict[str, object]] = clustering_result.get("topic_summaries", {})

        try:
            # 7. 为每个聚类创建 Topic（或生成合并建议）
            created_topics = []
            failed_topics = []
            merge_suggestions = []  # 新增：合并建议（与已有需求重复）

            for label, indices in clusters.items():
                try:
                    # Topic 创建流程
                    # 根据索引重建 feedback 数据
                    cluster_feedbacks_data = [feedbacks_data[i] for i in indices]
                    cluster_embeddings = embeddings_array[indices]

                    # 主题标题/分类已在事务外生成
                    topic_data = topic_summaries.get(
                        int(label),
                        {"title": "未命名主题", "category": "other", "description": None},
                    )

                    # 计算中心向量（均值）
                    centroid = np.mean(cluster_embeddings, axis=0).astype(float).tolist()
                    # ============================================================
                    # 新增：检查是否与已有 Topic 重复
                    # ============================================================
                    similar_topics = await crud_topic.search_by_semantic(
                        db=db,
                        tenant_id=tenant_id,
                        query_embedding=centroid,
                        limit=3,
                        min_similarity=0.80,  # 高阈值：只匹配高度相似的
                    )

                    if similar_topics:
                        # 找到相似需求，生成合并建议
                        matched_topic = similar_topics[0]
                        matched_status = matched_topic.status
                        similarity_score = getattr(matched_topic, "similarity_score", 0.85)

                        merge_suggestion = {
                            "cluster_label": int(label),
                            "suggested_topic_id": matched_topic.id,
                            "suggested_topic_title": matched_topic.title,
                            "suggested_topic_status": matched_status,
                            "suggested_topic_category": matched_topic.category,
                            "similarity": float(similarity_score),
                            "feedback_ids": [f["id"] for f in cluster_feedbacks_data],
                            "feedback_count": len(cluster_feedbacks_data),
                            "is_completed": matched_status == "completed",
                            "ai_generated_title": topic_data.get("title"),  # AI 生成的标题（供参考）
                        }

                        # 如果是已完成的需求，增加额外提示
                        if matched_status == "completed":
                            merge_suggestion["warning"] = "此需求已完成，请确认用户反馈的问题是否已解决"
                            merge_suggestion["suggested_actions"] = [
                                {"action": "mark_outdated", "label": "标记反馈为过时"},
                                {"action": "reopen_and_link", "label": "重新打开需求"},
                                {"action": "create_new", "label": "创建新需求"},
                            ]
                        else:
                            merge_suggestion["suggested_actions"] = [
                                {"action": "link_to_existing", "label": "关联到此需求"},
                                {"action": "create_new", "label": "创建新需求"},
                            ]

                        merge_suggestions.append(merge_suggestion)

                        # 将这些反馈标记为 suggested 状态，等待用户决策
                        # ⚠️ 必须用 "suggested" 而非 "pending"：
                        # claim_pending_clustering 只 claim "pending"/"failed"/"clustered"，
                        # "suggested" 状态会被跳过，不会被下次聚类覆盖 merge_suggestion 数据
                        feedback_ids = [f["id"] for f in cluster_feedbacks_data]
                        await crud_feedback.batch_update_clustering(
                            db=db,
                            tenant_id=tenant_id,
                            feedback_ids=feedback_ids,
                            clustering_status="suggested",  # 等待用户决策（不会被下次聚类 re-claim）
                            clustering_metadata={
                                "cluster_label": int(label),
                                "clustered_at": timezone.now().isoformat(),
                                "merge_suggestion": {
                                    "topic_id": matched_topic.id,
                                    "similarity": float(similarity_score),
                                },
                            },
                        )

                        log.info(
                            f"Found similar topic for cluster {label}: {matched_topic.title} "
                            f"(id={matched_topic.id}, similarity={similarity_score:.2f}, status={matched_status})"
                        )
                        continue  # 不创建新 Topic，跳到下一个聚类

                    # ============================================================
                    # 没有找到相似需求，创建新 Topic
                    # ============================================================

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
                    threshold = tenant_config.get("similarity_threshold", 0.85)
                    similarity_factor = max(0.0, min(1.0, (avg_similarity - threshold) / (1 - threshold)))
                    confidence = float(min(1.0, 0.2 + 0.8 * size_factor * similarity_factor))

                    # 从 Feedback 推断 board_id（取出现频率最高的）
                    from collections import Counter

                    board_ids = [f["board_id"] for f in cluster_feedbacks_data if f["board_id"]]
                    inferred_board_id = Counter(board_ids).most_common(1)[0][0] if board_ids else None

                    topic = await crud_topic.create(
                        db=db,
                        tenant_id=tenant_id,
                        board_id=inferred_board_id,
                        title=topic_data.get("title", "未命名主题"),
                        category=topic_data.get("category", "other"),
                        ai_generated=True,
                        ai_confidence=confidence,
                        feedback_count=len(cluster_feedbacks_data),
                        centroid=centroid,
                        cluster_quality={
                            "silhouette": quality_metrics.get("silhouette", 0.0),
                            "noise_ratio": quality_metrics.get("noise_ratio", 1.0),
                            "confidence": confidence,
                            "avg_similarity": avg_similarity,
                            "size": len(cluster_feedbacks_data),
                        },
                        is_noise=False,
                    )

                    # ✅ 自动生成默认优先级评分
                    try:
                        from backend.app.userecho.service.priority_service import priority_service

                        # 统计客户数量
                        customer_ids = {f["customer_id"] for f in cluster_feedbacks_data if f["customer_id"]}
                        customer_count = len(customer_ids)

                        # 生成默认评分(传递 customer_ids 避免查询数据库)
                        await priority_service.create_default_priority_score(
                            db=db,
                            tenant_id=tenant_id,
                            topic_id=topic.id,
                            category=topic.category,
                            title=topic.title,
                            customer_count=len(customer_ids),
                            feedback_count=len(cluster_feedbacks_data),
                            is_urgent=False,
                            customer_ids=customer_ids,  # 传递 customer_ids 避免查询数据库
                        )
                    except Exception as e:
                        log.warning(f"Failed to generate initial priority score for topic {topic.id}: {e}")

                    # ✅ CRITICAL: flush Topic 到数据库，确保外键存在
                    # 问题：topic.id 在 Python 侧已存在，但数据库中尚未 flush
                    # 后续 batch_update 使用 topic.id 时，PostgreSQL 外键约束检查会失败
                    await db.flush()

                    # 关联反馈到主题
                    feedback_ids = [f["id"] for f in cluster_feedbacks_data]
                    await crud_feedback.batch_update_clustering(
                        db=db,
                        tenant_id=tenant_id,
                        feedback_ids=feedback_ids,
                        clustering_status="clustered",
                        topic_id=topic.id,
                        clustering_metadata={
                            "cluster_label": int(label),
                            "clustered_at": timezone.now().isoformat(),
                            "topic_id": topic.id,
                            "topic_title": topic.title,
                            "quality": {
                                "avg_similarity": avg_similarity,
                                "confidence": confidence,
                            },
                        },
                    )

                    # 异步生成 Topic 的向量（虽然我们已经计算了 centroid，但统一逻辑可能更好）
                    # 不过既然我们已经有 centroid 了，直接存进去更高效（上面 create 已经做了）
                    # 触发异步任务去更新其他关联信息（如通知等）
                    try:
                        from backend.app.task.celery import celery_app

                        celery_app.send_task(
                            "userecho.generate_topic_centroid",
                            args=[topic.id, tenant_id],
                        )
                    except Exception as e:
                        log.warning(f"Failed to trigger topic async task: {e}")

                    created_topics.append(
                        {
                            "topic_id": topic.id,
                            "title": topic.title,
                            "feedback_count": len(cluster_feedbacks_data),
                            "is_noise": False,
                        }
                    )

                except Exception as e:
                    # Topic 创建失败,记录日志并跳过该聚类
                    # Feedbacks 保持原状态(pending),等待下次聚类
                    # 成功的聚类会在事务结束时一起提交
                    log.exception(f"Failed to create topic for cluster {label}: {e}")
                    failed_topics.append({"label": int(label), "error": str(e)})
                    continue

            # ✅ Linus: "噪声点保持 pending，不是 clustered。clustered 只用于已关联 Topic 的反馈。"
            # 噪声点：重置为 pending 状态（等待后续聚类）
            if noise_indices:
                noise_ids = [feedbacks_data[i]["id"] for i in noise_indices]
                try:
                    await crud_feedback.batch_update_clustering(
                        db=db,
                        tenant_id=tenant_id,
                        feedback_ids=noise_ids,
                        clustering_status="pending",  # ✅ 改为 pending
                        clustering_metadata={
                            "cluster_label": -1,
                            "last_attempt_at": timezone.now().isoformat(),
                            "quality": quality_metrics,
                            "reason": "noise",
                        },
                    )
                except Exception as e:
                    log.error(f"Failed to reset noise feedbacks to pending: {e}")

            log.info(
                f"Topic creation completed for tenant {tenant_id}: {len(created_topics)} created, {len(failed_topics)} failed"
            )

            # 记录积分消耗
            try:
                from backend.app.userecho.service.credits_service import credits_service

                # 聚类操作消耗
                await credits_service.consume(
                    db=db,
                    tenant_id=tenant_id,
                    operation_type="clustering",
                    count=1,
                    description=f"AI 聚类：{len(feedbacks_data)} 条反馈 → {len(created_topics)} 个主题",
                    extra_data={"feedbacks_count": len(feedbacks_data), "topics_created": len(created_topics)},
                )

                # Embedding 操作消耗（仅记录新生成的）
                if feedbacks_need_embedding:
                    await credits_service.consume(
                        db=db,
                        tenant_id=tenant_id,
                        operation_type="embedding",
                        count=len(feedbacks_need_embedding),
                        description=f"向量化：{len(feedbacks_need_embedding)} 条反馈",
                        extra_data={"source": "clustering"},
                    )
            except Exception as e:
                log.warning(f"Failed to record credits usage for tenant {tenant_id}: {e}")

            return {
                "status": "completed",
                "feedbacks_count": len(feedbacks_data),
                "clusters_count": len(clusters),
                "topics_created": len(created_topics),
                "topics_failed": len(failed_topics),
                "topics": created_topics,
                "merge_suggestions": merge_suggestions,  # 新增：合并建议
                "noise_count": len(noise_indices),
                "quality_metrics": quality_metrics,
                "elapsed_ms": int((timezone.now() - started_at).total_seconds() * 1000),
            }

        except Exception as e:
            log.error(f"Topic creation failed for tenant {tenant_id}: {e}")
            return {
                "status": "error",
                "message": f"Topic 创建失败: {str(e)}",
                "feedbacks_count": len(feedbacks_data) if "feedbacks_data" in locals() else 0,
                "clusters_count": len(clusters) if "clusters" in locals() else 0,
                "topics_created": 0,
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
            # 获取租户聚类配置
            tenant_config = await clustering_config_service.get_clustering_config(db, tenant_id)

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
            threshold = tenant_config.get("similarity_threshold", 0.85)
            similar = await crud_feedback.find_similar_feedbacks(
                db=db,
                tenant_id=tenant_id,
                query_embedding=target_embedding,
                limit=top_k + 1,  # 多取 1 个，方便过滤自己
                min_similarity=min(0.8, threshold),
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
                    "feedback_id": fb.id,
                    "content": fb.content,
                    "similarity": similarity,
                    "topic_id": fb.topic_id,
                    "topic_title": topic_title_map.get(fb.topic_id or ""),
                }
                for fb, similarity in similar
            ]

        except Exception as e:
            log.error(f"Failed to get clustering suggestions for feedback {feedback_id}, tenant {tenant_id}: {e}")
            return []

    async def get_pending_suggestions(
        self,
        db: AsyncSession,
        tenant_id: str,
    ) -> list[dict]:
        """
        获取当前租户所有待处理的合并建议

        查询那些聚类成功但因为与已有需求相似而未自动创建新需求的反馈，
        将它们按聚类分组返回，供用户决策是合并到已有需求还是创建新需求。

        Args:
            db: 数据库会话
            tenant_id: 租户ID

        Returns:
            合并建议列表，每个建议包含：
            - cluster_label: 聚类标签
            - suggested_topic_id: 建议关联的需求ID
            - suggested_topic_title: 建议关联的需求标题
            - similarity: 相似度
            - feedback_ids: 反馈ID列表
            - feedback_count: 反馈数量
        """
        try:
            from backend.app.userecho.model.feedback import Feedback

            # 查询待处理的合并建议反馈：
            # 1) 新逻辑使用 suggested
            # 2) 兼容历史数据（pending + merge_suggestion）
            # 3) 仅处理尚未关联 topic 的反馈
            query = (
                select(Feedback)
                .where(
                    Feedback.tenant_id == tenant_id,
                    Feedback.deleted_at.is_(None),
                    Feedback.topic_id.is_(None),
                    Feedback.clustering_status.in_(["suggested", "pending"]),
                    Feedback.clustering_metadata.is_not(None),
                )
                .order_by(Feedback.updated_time.desc())
            )

            result = await db.execute(query)
            feedbacks = result.scalars().all()

            # 按 cluster_label 分组
            suggestions_map: dict[int, dict] = {}

            for feedback in feedbacks:
                metadata = feedback.clustering_metadata
                if not isinstance(metadata, dict):
                    continue

                merge_suggestion = metadata.get("merge_suggestion")
                if not merge_suggestion:
                    continue

                cluster_label = metadata.get("cluster_label")
                if cluster_label is None:
                    continue

                # 初始化或更新建议
                if cluster_label not in suggestions_map:
                    # 从第一个反馈的 metadata 中获取完整的建议信息
                    suggestions_map[cluster_label] = {
                        "cluster_label": cluster_label,
                        "suggested_topic_id": merge_suggestion.get("topic_id"),
                        "suggested_topic_title": None,  # 待填充
                        "suggested_topic_status": None,  # 待填充
                        "suggested_topic_category": None,  # 待填充
                        "similarity": merge_suggestion.get("similarity", 0.0),
                        "feedback_ids": [],
                        "feedback_count": 0,
                        "is_completed": False,
                    }

                # 添加反馈ID
                suggestions_map[cluster_label]["feedback_ids"].append(feedback.id)
                suggestions_map[cluster_label]["feedback_count"] += 1

            if not suggestions_map:
                return []

            # 批量查询 topic 信息
            from backend.app.userecho.model.topic import Topic

            topic_ids = {sug["suggested_topic_id"] for sug in suggestions_map.values() if sug["suggested_topic_id"]}
            topic_map = {}

            if topic_ids:
                topic_query = select(Topic).where(
                    Topic.tenant_id == tenant_id,
                    Topic.id.in_(list(topic_ids)),
                    Topic.deleted_at.is_(None),
                )
                topic_result = await db.execute(topic_query)
                topics = topic_result.scalars().all()
                topic_map = {t.id: t for t in topics}

            # 填充 topic 信息
            for suggestion in suggestions_map.values():
                topic_id = suggestion["suggested_topic_id"]
                if topic_id and topic_id in topic_map:
                    topic = topic_map[topic_id]
                    suggestion["suggested_topic_title"] = topic.title
                    suggestion["suggested_topic_status"] = topic.status
                    suggestion["suggested_topic_category"] = topic.category
                    suggestion["is_completed"] = topic.status == "completed"

                    # 添加建议的操作
                    if topic.status == "completed":
                        suggestion["warning"] = "此需求已完成，请确认用户反馈的问题是否已解决"
                        suggestion["suggested_actions"] = [
                            {"action": "mark_outdated", "label": "标记反馈为过时"},
                            {"action": "reopen_and_link", "label": "重新打开需求"},
                            {"action": "create_new", "label": "创建新需求"},
                        ]
                    else:
                        suggestion["suggested_actions"] = [
                            {"action": "link_to_existing", "label": "关联到此需求"},
                            {"action": "create_new", "label": "创建新需求"},
                        ]

            # 按反馈数量降序排列
            suggestions = sorted(suggestions_map.values(), key=operator.itemgetter("feedback_count"), reverse=True)

            return suggestions

        except Exception as e:
            log.error(f"Failed to get pending suggestions for tenant {tenant_id}: {e}")
            return []


clustering_service = ClusteringService()
