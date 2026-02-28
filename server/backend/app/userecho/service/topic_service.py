"""需求主题服务

负责主题的 CRUD 和业务逻辑
"""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.userecho.crud import crud_priority_score, crud_status_history, crud_topic
from backend.app.userecho.schema.topic import TopicCreate, TopicStatusUpdateParam, TopicUpdate
from backend.app.userecho.service.status_machine import TopicStatusMachine
from backend.common.log import log
from backend.database.db import uuid4_str


class TopicService:
    """需求主题服务"""

    async def get_detail_with_relations(
        self,
        db: AsyncSession,
        tenant_id: str,
        topic_id: str,
        current_user_id: int | None = None,
    ) -> dict[str, Any] | None:
        """
        获取主题详情（包含关联反馈、优先级评分、状态历史）

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            topic_id: 主题ID
            current_user_id: 当前用户ID（用于查询用户名）

        Returns:
            主题详情字典
        """
        try:
            # 获取主题和关联反馈
            topic_data = await crud_topic.get_with_feedbacks(db, tenant_id, topic_id)
            if not topic_data:
                return None

            # 获取优先级评分
            priority_score = await crud_priority_score.get_by_topic(db, tenant_id, topic_id)

            # 获取状态变更历史
            status_history = await crud_status_history.get_by_topic(db, tenant_id, topic_id, limit=50)

            return {
                "topic": topic_data["topic"],
                "feedbacks": topic_data["feedbacks"],
                "priority_score": priority_score,
                "status_history": status_history,
            }

        except Exception as e:
            log.error(f"Failed to get topic detail for topic {topic_id}, tenant {tenant_id}: {e}")
            return None

    async def update_status_with_history(
        self,
        db: AsyncSession,
        tenant_id: str,
        topic_id: str,
        data: TopicStatusUpdateParam,
        current_user_id: int,
    ):
        """
        更新主题状态（自动记录历史）

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            topic_id: 主题ID
            data: 状态更新数据
            current_user_id: 当前用户ID

        Returns:
            更新后的主题实例
        """
        try:
            # 获取当前状态
            topic = await crud_topic.get_by_id(db, tenant_id, topic_id)
            if not topic:
                return None

            old_status = topic.status
            new_status = data.status

            # 状态机校验：非法流转直接拒绝
            TopicStatusMachine.validate_transition(old_status, new_status)

            # 更新状态
            topic = await crud_topic.update_status(db, tenant_id, topic_id, new_status)

            # 记录状态变更历史
            if old_status != new_status:
                await crud_status_history.create_history(
                    db=db,
                    tenant_id=tenant_id,
                    topic_id=topic_id,
                    from_status=old_status,
                    to_status=new_status,
                    changed_by=current_user_id,
                    reason=data.reason,
                )

                # 当状态变更为 completed 时，自动创建通知记录
                if old_status != "completed" and new_status == "completed":
                    from backend.app.userecho.service.notification_service import (
                        notification_service,
                    )

                    try:
                        created_count = await notification_service.create_notifications_for_topic(
                            db=db, tenant_id=tenant_id, topic_id=topic_id
                        )
                        log.info(f"Auto-created {created_count} notification records for topic {topic_id}")
                    except Exception as e:
                        log.error(f"Failed to auto-create notifications for topic {topic_id}: {e}")
                        # 不抛出异常，避免影响状态更新的主流程

            return topic

        except Exception as e:
            log.error(f"Failed to update topic {topic_id} status to {data.status} for tenant {tenant_id}: {e}")
            raise

    async def create_topic(
        self,
        db: AsyncSession,
        tenant_id: str,
        data: TopicCreate,
    ):
        """
        创建主题

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            data: 主题创建数据

        Returns:
            创建的主题实例
        """
        topic = await crud_topic.create(
            db=db,
            tenant_id=tenant_id,
            id=uuid4_str(),
            title=data.title,
            category=data.category,
            status=data.status,
            description=data.description,
            board_id=data.board_id,  # 传递看板ID
            ai_generated=False,  # 手动创建的主题
            feedback_count=0,  # ✅ 显式初始化，满足 Pydantic 校验 (无 db.refresh)
        )

        # 异步生成 centroid（不阻塞响应）
        # 使手动创建的需求也能参与相似度匹配
        try:
            from backend.app.task.celery import celery_app

            celery_app.send_task(
                "userecho.generate_topic_centroid",
                args=[topic.id, tenant_id],
            )
        except Exception as e:
            # 失败不影响主流程
            log.warning(f"Failed to trigger centroid generation for topic {topic.id}: {e}")

        return topic

    async def update_topic(
        self,
        db: AsyncSession,
        tenant_id: str,
        topic_id: str,
        data: TopicUpdate,
    ):
        """
        更新主题

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            topic_id: 主题ID
            data: 更新数据

        Returns:
            更新后的主题实例
        """
        update_dict = data.model_dump(exclude_unset=True)
        return await crud_topic.update(db=db, tenant_id=tenant_id, id=topic_id, **update_dict)

    async def get_list_sorted(
        self,
        db: AsyncSession,
        tenant_id: str,
        skip: int = 0,
        limit: int = 100,
        status: list[str] | None = None,
        category: list[str] | None = None,
        board_ids: list[str] | None = None,
        sort_by: str = "created_time",
        sort_order: str = "desc",
        search_query: str | None = None,
        search_mode: str = "keyword",
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> tuple[list[Any], int]:
        """
        获取主题列表（支持排序、过滤和搜索）

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            skip: 跳过数量
            limit: 返回数量
            status: 过滤状态（多选）
            category: 过滤分类（多选）
            board_ids: 过滤看板ID（多选）
            sort_by: 排序字段
            sort_order: 排序方向
            search_query: 搜索关键词
            search_mode: 搜索模式（'keyword' | 'semantic'）
            date_from: 起始日期
            date_to: 结束日期

        Returns:
            (主题列表, 总条数)
        """
        from backend.utils.ai_client import ai_client

        # 语义搜索模式
        if search_query and search_mode == "semantic":
            # 1. 生成搜索词的 embedding
            query_embedding = await ai_client.get_embedding(search_query)
            if not query_embedding:
                log.warning(
                    f"Failed to generate embedding for search query: {search_query}, fallback to keyword search"
                )
                # Fallback 到关键词搜索
                search_mode = "keyword"
            else:
                # 2. 使用 pgvector 语义搜索
                items = await crud_topic.search_by_semantic(
                    db=db,
                    tenant_id=tenant_id,
                    query_embedding=query_embedding,
                    skip=skip,
                    limit=limit,
                    status=status,
                    category=category,
                    board_ids=board_ids,
                )
                # 语义搜索暂不支持精确计数，返回列表长度
                return items, len(items)

        # 关键词搜索模式（默认）
        effective_search_query = search_query if (search_query and search_mode == "keyword") else None

        items = await crud_topic.get_list_sorted(
            db=db,
            tenant_id=tenant_id,
            skip=skip,
            limit=limit,
            status=status,
            category=category,
            board_ids=board_ids,
            sort_by=sort_by,
            sort_order=sort_order,
            search_query=effective_search_query,
            date_from=date_from,
            date_to=date_to,
        )
        total = await crud_topic.count_with_filters(
            db=db,
            tenant_id=tenant_id,
            status=status,
            category=category,
            board_ids=board_ids,
            search_query=effective_search_query,
            date_from=date_from,
            date_to=date_to,
        )
        return items, total

    async def get_pending_count(
        self,
        db: AsyncSession,
        tenant_id: str,
    ) -> int:
        """
        获取待确认主题数量

        Args:
            db: 数据库会话
            tenant_id: 租户ID

        Returns:
            待确认主题数量
        """
        return await crud_topic.count(db=db, tenant_id=tenant_id, status="pending")

    async def link_feedbacks(
        self,
        db: AsyncSession,
        tenant_id: str,
        topic_id: str,
        feedback_ids: list[str],
    ) -> int:
        """
        批量关联反馈到主题

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            topic_id: 主题ID
            feedback_ids: 反馈ID列表

        Returns:
            关联成功的数量
        """
        from backend.app.userecho.crud import crud_feedback

        # 验证主题是否存在
        topic = await crud_topic.get_by_id(db, tenant_id, topic_id)
        if not topic:
            return 0

        # 批量更新反馈的 topic_id
        count = await crud_feedback.batch_update_topic(
            db=db,
            tenant_id=tenant_id,
            feedback_ids=feedback_ids,
            topic_id=topic_id,
        )
        return count

    async def unlink_feedback(
        self,
        db: AsyncSession,
        tenant_id: str,
        topic_id: str,
        feedback_id: str,
    ) -> bool:
        """
        从主题移除反馈关联

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            topic_id: 主题ID
            feedback_id: 反馈ID

        Returns:
            是否成功移除
        """
        from backend.app.userecho.crud import crud_feedback

        # 验证该反馈是否确实属于该主题
        feedback = await crud_feedback.get_by_id(db, tenant_id, feedback_id)
        if not feedback or feedback.topic_id != topic_id:
            return False

        # 更新 topic_id 为 None
        # 使用 batch_update_clustering 更新 topic_id=None
        # 注意: 这里借用 batch_update_clustering 因为它支持 atomic update，
        # 并将 clustering_status 重置为 'pending'，以便将来可能重新聚类
        await crud_feedback.batch_update_clustering(
            db=db,
            tenant_id=tenant_id,
            feedback_ids=[feedback_id],
            clustering_status="pending",
            topic_id=None,
        )
        return True


topic_service = TopicService()
