"""SystemNotification CRUD"""

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.userecho.crud.base import TenantAwareCRUD
from backend.app.userecho.model.system_notification import SystemNotification


class CRUDSystemNotification(TenantAwareCRUD[SystemNotification]):
    """系统提醒 CRUD"""

    async def get_user_notifications(
        self,
        db: AsyncSession,
        tenant_id: str,
        user_id: int,
        skip: int = 0,
        limit: int = 20,
        unread_only: bool = False,
    ) -> list[SystemNotification]:
        """
        获取用户的系统提醒

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            user_id: 用户ID
            skip: 跳过数量
            limit: 返回数量
            unread_only: 只返回未读

        Returns:
            提醒列表
        """
        from sqlalchemy import or_

        query = select(self.model).where(
            self.model.tenant_id == tenant_id,
            # 用户专属通知 OR 租户全员通知
            or_(self.model.user_id == user_id, self.model.user_id.is_(None)),
        )

        if unread_only:
            query = query.where(self.model.is_read == False)  # noqa: E712

        query = query.order_by(self.model.created_time.desc()).offset(skip).limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def count_unread(
        self,
        db: AsyncSession,
        tenant_id: str,
        user_id: int,
    ) -> int:
        """统计未读通知数量"""
        from sqlalchemy import or_

        query = (
            select(func.count())
            .select_from(self.model)
            .where(
                self.model.tenant_id == tenant_id,
                or_(self.model.user_id == user_id, self.model.user_id.is_(None)),
                self.model.is_read == False,  # noqa: E712
            )
        )

        result = await db.execute(query)
        return result.scalar() or 0

    async def mark_as_read(
        self,
        db: AsyncSession,
        tenant_id: str,
        notification_id: str,
        user_id: int,
    ) -> SystemNotification | None:
        """标记为已读"""

        from backend.utils.timezone import timezone

        # 验证通知属于该用户（或租户全员通知）
        notification = await self.get_by_id(db, tenant_id, notification_id)
        if not notification:
            return None
        if notification.user_id is not None and notification.user_id != user_id:
            return None

        notification.is_read = True
        notification.read_at = timezone.now()

        await db.commit()
        await db.refresh(notification)
        return notification

    async def mark_all_as_read(
        self,
        db: AsyncSession,
        tenant_id: str,
        user_id: int,
    ) -> int:
        """标记所有通知为已读"""
        from sqlalchemy import or_

        from backend.utils.timezone import timezone

        stmt = (
            update(self.model)
            .where(
                self.model.tenant_id == tenant_id,
                or_(self.model.user_id == user_id, self.model.user_id.is_(None)),
                self.model.is_read == False,  # noqa: E712
            )
            .values(is_read=True, read_at=timezone.now())
        )

        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount

    async def clear_all(
        self,
        db: AsyncSession,
        tenant_id: str,
        user_id: int,
    ) -> int:
        """清空用户的所有通知（物理删除）"""
        from sqlalchemy import delete, or_

        stmt = delete(self.model).where(
            self.model.tenant_id == tenant_id,
            or_(self.model.user_id == user_id, self.model.user_id.is_(None)),
        )

        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount

    async def create_topic_completed_notification(
        self,
        db: AsyncSession,
        tenant_id: str,
        topic_id: str,
        topic_title: str,
        pending_count: int,
        user_id: int | None = None,
    ) -> SystemNotification:
        """创建议题完成通知"""
        notification = SystemNotification(
            tenant_id=tenant_id,
            user_id=user_id,
            type='topic_completed',
            title='需求已完成，待通知用户',
            message=f'「{topic_title}」已完成，有 {pending_count} 位用户等待通知',
            avatar=None,
            action_url=f'/app/userecho/topic/{topic_id}?tab=notify',
            extra_data={'topic_id': topic_id, 'pending_notifications': pending_count},
        )

        db.add(notification)
        await db.commit()
        await db.refresh(notification)
        return notification


crud_system_notification = CRUDSystemNotification(SystemNotification)
