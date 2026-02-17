"""Status History CRUD"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.userecho.crud.base import TenantAwareCRUD
from backend.app.userecho.model.status_history import StatusHistory
from backend.database.db import uuid4_str
from backend.utils.timezone import timezone


class CRUDStatusHistory(TenantAwareCRUD[StatusHistory]):
    """状态变更历史 CRUD"""

    async def create_history(
        self,
        db: AsyncSession,
        tenant_id: str,
        topic_id: str,
        from_status: str,
        to_status: str,
        changed_by: int,
        reason: str | None = None,
    ) -> StatusHistory:
        """
        创建状态变更历史记录

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            topic_id: 主题ID
            from_status: 原状态
            to_status: 新状态
            changed_by: 操作人用户ID
            reason: 变更原因

        Returns:
            状态历史实例
        """
        history = self.model(
            id=uuid4_str(),
            tenant_id=tenant_id,
            topic_id=topic_id,
            from_status=from_status,
            to_status=to_status,
            changed_by=changed_by,
            reason=reason,
            changed_at=timezone.now(),
        )
        db.add(history)
        await db.commit()
        await db.refresh(history)
        return history

    async def get_by_topic(
        self,
        db: AsyncSession,
        tenant_id: str,
        topic_id: str,
        limit: int = 50,
    ) -> list[StatusHistory]:
        """
        获取主题的状态变更历史

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            topic_id: 主题ID
            limit: 返回数量上限

        Returns:
            状态历史列表（按时间倒序）
        """
        query = (
            select(self.model)
            .where(self.model.tenant_id == tenant_id, self.model.topic_id == topic_id)
            .order_by(self.model.changed_at.desc())
            .limit(limit)
        )
        result = await db.execute(query)
        return list(result.scalars().all())


crud_status_history = CRUDStatusHistory(StatusHistory)
