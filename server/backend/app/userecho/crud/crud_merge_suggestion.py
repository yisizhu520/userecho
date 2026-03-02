"""合并建议 CRUD"""

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.userecho.crud.base import TenantAwareCRUD
from backend.app.userecho.model.merge_suggestion import MergeSuggestion
from backend.utils.timezone import timezone


class CRUDMergeSuggestion(TenantAwareCRUD[MergeSuggestion]):
    """合并建议 CRUD"""

    async def get_pending_suggestions(
        self,
        db: AsyncSession,
        tenant_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[MergeSuggestion]:
        """
        获取待处理的合并建议

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            skip: 跳过数量
            limit: 返回数量

        Returns:
            待处理建议列表
        """
        query = (
            select(self.model)
            .where(
                self.model.tenant_id == tenant_id,
                self.model.status == "pending",
                self.model.deleted_at.is_(None),
            )
            .order_by(self.model.created_time.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_by_topic(
        self,
        db: AsyncSession,
        tenant_id: str,
        topic_id: str,
        status: str | None = None,
    ) -> list[MergeSuggestion]:
        """
        获取指定需求的合并建议

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            topic_id: 需求ID
            status: 可选，过滤状态

        Returns:
            建议列表
        """
        query = select(self.model).where(
            self.model.tenant_id == tenant_id,
            self.model.suggested_topic_id == topic_id,
            self.model.deleted_at.is_(None),
        )

        if status:
            query = query.where(self.model.status == status)

        query = query.order_by(self.model.created_time.desc())
        result = await db.execute(query)
        return list(result.scalars().all())

    async def update_status(
        self,
        db: AsyncSession,
        tenant_id: str,
        suggestion_id: str,
        status: str,
        processed_by: str,
    ) -> bool:
        """
        更新建议状态

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            suggestion_id: 建议ID
            status: 新状态
            processed_by: 处理人ID

        Returns:
            是否成功
        """
        stmt = (
            update(self.model)
            .where(
                self.model.id == suggestion_id,
                self.model.tenant_id == tenant_id,
                self.model.deleted_at.is_(None),
            )
            .values(
                status=status,
                processed_by=processed_by,
                processed_at=timezone.now(),
                updated_time=timezone.now(),
            )
        )
        result = await db.execute(stmt)
        return result.rowcount > 0

    async def count_pending(
        self,
        db: AsyncSession,
        tenant_id: str,
    ) -> int:
        """
        统计待处理建议数量

        Args:
            db: 数据库会话
            tenant_id: 租户ID

        Returns:
            待处理数量
        """
        from sqlalchemy import func

        query = select(func.count(self.model.id)).where(
            self.model.tenant_id == tenant_id,
            self.model.status == "pending",
            self.model.deleted_at.is_(None),
        )
        result = await db.execute(query)
        return result.scalar() or 0

    async def batch_update_status(
        self,
        db: AsyncSession,
        tenant_id: str,
        suggestion_ids: list[str],
        status: str,
        processed_by: str,
    ) -> int:
        """
        批量更新建议状态

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            suggestion_ids: 建议ID列表
            status: 新状态
            processed_by: 处理人ID

        Returns:
            更新数量
        """
        stmt = (
            update(self.model)
            .where(
                self.model.id.in_(suggestion_ids),
                self.model.tenant_id == tenant_id,
                self.model.deleted_at.is_(None),
            )
            .values(
                status=status,
                processed_by=processed_by,
                processed_at=timezone.now(),
                updated_time=timezone.now(),
            )
        )
        result = await db.execute(stmt)
        return result.rowcount


crud_merge_suggestion = CRUDMergeSuggestion(MergeSuggestion)
