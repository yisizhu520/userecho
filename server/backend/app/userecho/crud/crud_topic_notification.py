"""TopicNotification CRUD"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.userecho.crud.base import TenantAwareCRUD
from backend.app.userecho.model.topic_notification import TopicNotification


class CRUDTopicNotification(TenantAwareCRUD[TopicNotification]):
    """需求通知记录 CRUD"""

    async def get_by_topic_id(
        self,
        db: AsyncSession,
        tenant_id: str,
        topic_id: str,
        status: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[TopicNotification]:
        """
        获取议题的所有通知记录

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            topic_id: 议题ID
            status: 状态筛选
            skip: 跳过数量
            limit: 返回数量

        Returns:
            通知记录列表
        """
        query = select(self.model).where(
            self.model.tenant_id == tenant_id,
            self.model.topic_id == topic_id,
        )

        if status:
            query = query.where(self.model.status == status)

        query = query.order_by(self.model.created_time.desc()).offset(skip).limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def count_by_topic_id(
        self,
        db: AsyncSession,
        tenant_id: str,
        topic_id: str,
        status: str | None = None,
    ) -> int:
        """统计议题的通知记录数量"""
        from sqlalchemy import func

        query = (
            select(func.count())
            .select_from(self.model)
            .where(
                self.model.tenant_id == tenant_id,
                self.model.topic_id == topic_id,
            )
        )

        if status:
            query = query.where(self.model.status == status)

        result = await db.execute(query)
        return result.scalar() or 0

    async def get_pending_by_topic_id(
        self,
        db: AsyncSession,
        tenant_id: str,
        topic_id: str,
    ) -> list[TopicNotification]:
        """获取议题的待处理通知记录"""
        return await self.get_by_topic_id(db, tenant_id, topic_id, status='pending')

    async def update_reply(
        self,
        db: AsyncSession,
        tenant_id: str,
        notification_id: str,
        ai_reply: str,
        reply_tone: str | None = None,
        reply_language: str | None = None,
    ) -> TopicNotification | None:
        """更新 AI 回复内容"""
        notification = await self.get_by_id(db, tenant_id, notification_id)
        if not notification:
            return None

        notification.ai_reply = ai_reply
        notification.status = 'generated'
        if reply_tone:
            notification.reply_tone = reply_tone
        if reply_language:
            notification.reply_language = reply_language

        await db.commit()
        await db.refresh(notification)
        return notification

    async def mark_as_notified(
        self,
        db: AsyncSession,
        tenant_id: str,
        notification_id: str,
        notified_by: int,
        status: str = 'sent',
        notification_channel: str | None = None,
        notes: str | None = None,
    ) -> TopicNotification | None:
        """标记为已通知"""
        from backend.utils.timezone import timezone

        notification = await self.get_by_id(db, tenant_id, notification_id)
        if not notification:
            return None

        notification.status = status
        notification.notified_at = timezone.now()
        notification.notified_by = notified_by
        if notification_channel:
            notification.notification_channel = notification_channel
        if notes:
            notification.notes = notes

        await db.commit()
        await db.refresh(notification)
        return notification

    async def get_with_details(
        self,
        db: AsyncSession,
        tenant_id: str,
        topic_id: str,
    ) -> list[dict]:
        """获取通知记录（包含客户和反馈详情）"""
        from backend.app.userecho.model.customer import Customer
        from backend.app.userecho.model.feedback import Feedback

        query = (
            select(
                self.model,
                Customer.company_name.label('customer_company'),
                Customer.customer_tier.label('customer_tier'),
                Feedback.ai_summary.label('feedback_summary'),
                Feedback.content.label('feedback_content'),
            )
            .outerjoin(Customer, self.model.customer_id == Customer.id)
            .outerjoin(Feedback, self.model.feedback_id == Feedback.id)
            .where(
                self.model.tenant_id == tenant_id,
                self.model.topic_id == topic_id,
            )
            .order_by(self.model.created_time.desc())
        )

        result = await db.execute(query)
        rows = result.all()

        notifications = []
        for row in rows:
            notification = row[0]
            notification_dict = {c.name: getattr(notification, c.name) for c in notification.__table__.columns}
            notification_dict['customer_company'] = row.customer_company
            notification_dict['customer_tier'] = row.customer_tier
            notification_dict['feedback_summary'] = row.feedback_summary
            notification_dict['feedback_content'] = row.feedback_content
            notifications.append(notification_dict)

        return notifications


crud_topic_notification = CRUDTopicNotification(TopicNotification)
