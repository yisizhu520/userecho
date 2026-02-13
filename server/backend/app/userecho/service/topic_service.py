"""需求主题服务

负责主题的 CRUD 和业务逻辑
"""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.userecho.crud import crud_priority_score, crud_status_history, crud_topic
from backend.app.userecho.schema.topic import TopicCreate, TopicStatusUpdateParam, TopicUpdate
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
                'topic': topic_data['topic'],
                'feedbacks': topic_data['feedbacks'],
                'priority_score': priority_score,
                'status_history': status_history
            }

        except Exception as e:
            log.error(f'Failed to get topic detail for topic {topic_id}, tenant {tenant_id}: {e}')
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
                    reason=data.reason
                )

            return topic

        except Exception as e:
            log.error(f'Failed to update topic {topic_id} status to {data.status} for tenant {tenant_id}: {e}')
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
        return await crud_topic.create(
            db=db,
            tenant_id=tenant_id,
            id=uuid4_str(),
            title=data.title,
            category=data.category,
            status=data.status,
            description=data.description,
            ai_generated=False  # 手动创建的主题
        )

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
        return await crud_topic.update(
            db=db,
            tenant_id=tenant_id,
            id=topic_id,
            **update_dict
        )

    async def get_list_sorted(
        self,
        db: AsyncSession,
        tenant_id: str,
        skip: int = 0,
        limit: int = 100,
        status: str | None = None,
        category: str | None = None,
        sort_by: str = 'created_time',
        sort_order: str = 'desc',
    ):
        """
        获取主题列表（支持排序和过滤）

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            skip: 跳过数量
            limit: 返回数量
            status: 过滤状态
            category: 过滤分类
            sort_by: 排序字段
            sort_order: 排序方向

        Returns:
            主题列表
        """
        return await crud_topic.get_list_sorted(
            db=db,
            tenant_id=tenant_id,
            skip=skip,
            limit=limit,
            status=status,
            category=category,
            sort_by=sort_by,
            sort_order=sort_order
        )


topic_service = TopicService()
