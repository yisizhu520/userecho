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

        # 直接查询，不使用基类方法（SystemNotification 没有 deleted_at 字段）
        stmt = select(self.model).where(
            self.model.tenant_id == tenant_id,
            self.model.id == notification_id,
        )
        result = await db.execute(stmt)
        notification = result.scalar_one_or_none()

        if not notification:
            return None
        if notification.user_id is not None and notification.user_id != user_id:
            return None

        notification.is_read = True
        notification.read_at = timezone.now()

        # ❌ 禁止手动 commit 和 refresh
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
        # ❌ 禁止手动 commit
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
        # ❌ 禁止手动 commit
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
        from backend.database.db import uuid4_str
        from backend.utils.timezone import timezone

        notification = SystemNotification(
            id=uuid4_str(),
            tenant_id=tenant_id,
            user_id=user_id,
            type="topic_completed",
            title="需求已完成，待通知用户",
            message=f"「{topic_title}」已完成，有 {pending_count} 位用户等待通知",
            avatar=None,
            action_url=f"/app/topic/detail/{topic_id}?tab=notify",
            extra_data={"topic_id": topic_id, "pending_notifications": pending_count},
            is_read=False,
            created_time=timezone.now(),
        )

        db.add(notification)
        # ❌ 禁止手动 commit 和 refresh
        return notification

    async def create_batch_reply_completed_notification(
        self,
        db: AsyncSession,
        tenant_id: str,
        topic_id: str,
        topic_title: str,
        success_count: int,
        failed_count: int,
        user_id: int | None = None,
    ) -> SystemNotification:
        """创建批量回复生成完成通知"""
        from backend.database.db import uuid4_str
        from backend.utils.timezone import timezone

        notification = SystemNotification(
            id=uuid4_str(),
            tenant_id=tenant_id,
            user_id=user_id,
            type="batch_reply_completed",
            title="批量回复生成完成",
            message=f"「{topic_title}」的用户回复已生成完成，成功 {success_count} 条，失败 {failed_count} 条",
            avatar=None,
            action_url=f"/app/topic/detail/{topic_id}?tab=notify",
            extra_data={"topic_id": topic_id, "success": success_count, "failed": failed_count},
            is_read=False,
            created_time=timezone.now(),
        )

        db.add(notification)
        return notification

    async def create_screenshot_batch_completed_notification(
        self,
        db: AsyncSession,
        tenant_id: str,
        total_count: int,
        success_count: int,
        failed_count: int,
        user_id: int | None = None,
    ) -> SystemNotification:
        """创建截图批量识别完成通知"""
        from backend.database.db import uuid4_str
        from backend.utils.timezone import timezone

        notification = SystemNotification(
            id=uuid4_str(),
            tenant_id=tenant_id,
            user_id=user_id,
            type="screenshot_batch_completed",
            title="截图批量识别完成",
            message=f"批量截图识别已完成，共处理 {total_count} 张，成功 {success_count} 张，失败 {failed_count} 张",
            avatar=None,
            action_url="/app/feedback/list",
            extra_data={"total": total_count, "success": success_count, "failed": failed_count},
            is_read=False,
            created_time=timezone.now(),
        )

        db.add(notification)
        return notification


crud_system_notification = CRUDSystemNotification(SystemNotification)
