"""Board CRUD"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.userecho.crud.base import TenantAwareCRUD
from backend.app.userecho.model.board import Board


class CRUDBoard(TenantAwareCRUD[Board]):
    """看板 CRUD"""

    async def get_by_name(self, db: AsyncSession, tenant_id: str, name: str) -> Board | None:
        """
        根据名称获取看板

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            name: 看板名称

        Returns:
            看板实例或 None
        """
        query = select(self.model).where(
            self.model.tenant_id == tenant_id,
            self.model.name == name,
            self.model.deleted_at.is_(None),
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_url_name(self, db: AsyncSession, tenant_id: str, url_name: str) -> Board | None:
        """
        根据 URL slug 获取看板

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            url_name: URL slug

        Returns:
            看板实例或 None
        """
        query = select(self.model).where(
            self.model.tenant_id == tenant_id,
            self.model.url_name == url_name,
            self.model.deleted_at.is_(None),
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def soft_delete(self, db: AsyncSession, board_id: str, tenant_id: str) -> bool:
        """
        软删除看板

        Args:
            db: 数据库会话
            board_id: 看板ID
            tenant_id: 租户ID

        Returns:
            是否删除成功
        """
        from backend.utils.timezone import timezone

        query = select(self.model).where(
            self.model.id == board_id,
            self.model.tenant_id == tenant_id,
            self.model.deleted_at.is_(None),
        )
        result = await db.execute(query)
        board = result.scalar_one_or_none()

        if not board:
            return False

        board.deleted_at = timezone.now()
        await db.flush()
        return True


crud_board = CRUDBoard(Board)
