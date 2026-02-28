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
        # ❌ 禁止手动 commit 和 refresh
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
        from backend.app.admin.model.user import User

        query = (
            select(self.model, User.nickname.label("changed_by_name"))
            .outerjoin(User, self.model.changed_by == User.id)
            .where(self.model.tenant_id == tenant_id, self.model.topic_id == topic_id)
            .order_by(self.model.changed_at.desc())
            .limit(limit)
        )
        result = await db.execute(query)

        history_list = []
        for history, changed_by_name in result.all():
            # 将 SQLAlchemy 对象转换为字典并附加 changed_by_name
            # 使用 __dict__ 可能包含内部状态，使用 vars 或手动构建比较安全
            # 或者直接依赖 Pydantic 从 attributes 读取（如果 history 对象上能动态 setattr）
            # 最稳妥：转字典
            h_dict = {c.name: getattr(history, c.name) for c in history.__table__.columns}
            h_dict["changed_by_name"] = changed_by_name
            history_list.append(h_dict)

        return history_list


crud_status_history = CRUDStatusHistory(StatusHistory)
