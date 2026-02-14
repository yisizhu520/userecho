"""Topic CRUD"""
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.userecho.crud.base import TenantAwareCRUD
from backend.app.userecho.model.topic import Topic


class CRUDTopic(TenantAwareCRUD[Topic]):
    """需求主题 CRUD"""

    async def update_centroid(
        self,
        db: AsyncSession,
        tenant_id: str,
        topic_id: str,
        centroid: list[float] | None,
    ) -> bool:
        """更新主题中心向量（用于增量匹配/合并建议）"""
        stmt = (
            update(self.model)
            .where(
                self.model.id == topic_id,
                self.model.tenant_id == tenant_id,
                self.model.deleted_at.is_(None),
            )
            .values(centroid=centroid)
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount > 0

    async def update_cluster_quality(
        self,
        db: AsyncSession,
        tenant_id: str,
        topic_id: str,
        cluster_quality: dict | None,
        *,
        is_noise: bool | None = None,
    ) -> bool:
        """更新聚类质量指标（可选同时更新 is_noise）"""
        values: dict = {'cluster_quality': cluster_quality}
        if is_noise is not None:
            values['is_noise'] = is_noise

        stmt = (
            update(self.model)
            .where(
                self.model.id == topic_id,
                self.model.tenant_id == tenant_id,
                self.model.deleted_at.is_(None),
            )
            .values(**values)
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount > 0

    async def get_with_feedbacks(
        self,
        db: AsyncSession,
        tenant_id: str,
        topic_id: str,
    ) -> dict | None:
        """
        获取主题详情（包含关联反馈）
        
        Args:
            db: 数据库会话
            tenant_id: 租户ID
            topic_id: 主题ID
        
        Returns:
            包含 topic 和 feedbacks 的字典，或 None
        """
        from backend.app.userecho.model.feedback import Feedback

        # 获取主题
        topic = await self.get_by_id(db, tenant_id, topic_id)
        if not topic:
            return None

        # 获取关联反馈
        query = select(Feedback).where(
            Feedback.tenant_id == tenant_id,
            Feedback.topic_id == topic_id,
            Feedback.deleted_at.is_(None)
        )
        result = await db.execute(query)
        feedbacks = list(result.scalars().all())

        return {
            'topic': topic,
            'feedbacks': feedbacks
        }

    async def update_status(
        self,
        db: AsyncSession,
        tenant_id: str,
        topic_id: str,
        new_status: str,
    ) -> Topic | None:
        """
        更新主题状态
        
        Args:
            db: 数据库会话
            tenant_id: 租户ID
            topic_id: 主题ID
            new_status: 新状态
        
        Returns:
            更新后的主题 或 None
        """
        return await self.update(db, tenant_id, topic_id, status=new_status)

    async def increment_feedback_count(
        self,
        db: AsyncSession,
        tenant_id: str,
        topic_id: str,
        delta: int = 1,
    ) -> bool:
        """
        增加/减少反馈计数
        
        Args:
            db: 数据库会话
            tenant_id: 租户ID
            topic_id: 主题ID
            delta: 变化量（正数增加，负数减少）
        
        Returns:
            是否成功
        """
        topic = await self.get_by_id(db, tenant_id, topic_id)
        if not topic:
            return False

        topic.feedback_count = max(0, topic.feedback_count + delta)
        await db.commit()
        return True

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
    ) -> list[Topic]:
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
            sort_order: 排序方向（asc/desc）
        
        Returns:
            主题列表（包含 priority_score 关联）
        """
        from sqlalchemy.orm import joinedload
        from backend.app.userecho.model.priority_score import PriorityScore
        
        query = (
            select(self.model)
            .options(joinedload(self.model.priority_score))  # 加载关联的评分
            .where(
                self.model.tenant_id == tenant_id,
                self.model.deleted_at.is_(None)
            )
        )

        # 添加过滤条件
        if status:
            query = query.where(self.model.status == status)
        if category:
            query = query.where(self.model.category == category)

        # 添加排序
        sort_column = getattr(self.model, sort_by, self.model.created_time)
        if sort_order == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        query = query.offset(skip).limit(limit)

        result = await db.execute(query)
        return list(result.scalars().unique().all())  # unique() 防止 joinedload 产生重复


crud_topic = CRUDTopic(Topic)
