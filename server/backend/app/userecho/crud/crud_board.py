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


crud_board = CRUDBoard(Board)
