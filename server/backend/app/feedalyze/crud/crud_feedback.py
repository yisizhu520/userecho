"""Feedback CRUD"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.feedalyze.crud.base import TenantAwareCRUD
from backend.app.feedalyze.model.feedback import Feedback


class CRUDFeedback(TenantAwareCRUD[Feedback]):
    """反馈 CRUD"""

    async def get_unclustered(
        self,
        db: AsyncSession,
        tenant_id: str,
        limit: int = 100,
    ) -> list[Feedback]:
        """
        获取未聚类的反馈（topic_id 为 NULL）
        
        Args:
            db: 数据库会话
            tenant_id: 租户ID
            limit: 返回数量上限
        
        Returns:
            反馈列表
        """
        query = select(self.model).where(
            self.model.tenant_id == tenant_id,
            self.model.topic_id.is_(None),
            self.model.deleted_at.is_(None)
        ).limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def batch_update_topic(
        self,
        db: AsyncSession,
        tenant_id: str,
        feedback_ids: list[str],
        topic_id: str,
    ) -> int:
        """
        批量更新反馈的主题ID（用于聚类后批量关联）
        
        Args:
            db: 数据库会话
            tenant_id: 租户ID
            feedback_ids: 反馈ID列表
            topic_id: 主题ID
        
        Returns:
            更新的记录数量
        """
        from sqlalchemy import update

        stmt = (
            update(self.model)
            .where(
                self.model.id.in_(feedback_ids),
                self.model.tenant_id == tenant_id,
                self.model.deleted_at.is_(None)
            )
            .values(topic_id=topic_id)
        )

        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount

    async def get_list_with_relations(
        self,
        db: AsyncSession,
        tenant_id: str,
        skip: int = 0,
        limit: int = 100,
        topic_id: str | None = None,
        customer_id: str | None = None,
        is_urgent: bool | None = None,
        has_topic: bool | None = None,
    ) -> list[dict]:
        """
        获取反馈列表（包含关联的客户名和主题标题）
        
        Args:
            db: 数据库会话
            tenant_id: 租户ID
            skip: 跳过数量
            limit: 返回数量
            topic_id: 过滤主题ID
            customer_id: 过滤客户ID
            is_urgent: 过滤紧急程度
            has_topic: 过滤是否已聚类
        
        Returns:
            反馈列表（包含 customer_name 和 topic_title）
        """
        from backend.app.feedalyze.model.customer import Customer
        from backend.app.feedalyze.model.topic import Topic
        from sqlalchemy.orm import aliased

        # 使用左连接查询
        CustomerAlias = aliased(Customer)
        TopicAlias = aliased(Topic)

        query = (
            select(
                self.model,
                CustomerAlias.name.label('customer_name'),
                TopicAlias.title.label('topic_title')
            )
            .outerjoin(CustomerAlias, self.model.customer_id == CustomerAlias.id)
            .outerjoin(TopicAlias, self.model.topic_id == TopicAlias.id)
            .where(
                self.model.tenant_id == tenant_id,
                self.model.deleted_at.is_(None)
            )
        )

        # 添加过滤条件
        if topic_id is not None:
            query = query.where(self.model.topic_id == topic_id)
        if customer_id is not None:
            query = query.where(self.model.customer_id == customer_id)
        if is_urgent is not None:
            query = query.where(self.model.is_urgent == is_urgent)
        if has_topic is not None:
            if has_topic:
                query = query.where(self.model.topic_id.is_not(None))
            else:
                query = query.where(self.model.topic_id.is_(None))

        query = query.offset(skip).limit(limit)

        result = await db.execute(query)
        rows = result.all()

        # 转换为字典列表
        feedback_list = []
        for row in rows:
            feedback_dict = {
                **{c.name: getattr(row[0], c.name) for c in row[0].__table__.columns},
                'customer_name': row.customer_name,
                'topic_title': row.topic_title
            }
            feedback_list.append(feedback_dict)

        return feedback_list


crud_feedback = CRUDFeedback(Feedback)
