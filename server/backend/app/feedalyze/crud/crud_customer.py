"""Customer CRUD"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.feedalyze.crud.base import TenantAwareCRUD
from backend.app.feedalyze.model.customer import Customer


class CRUDCustomer(TenantAwareCRUD[Customer]):
    """客户 CRUD"""

    async def get_by_name(
        self,
        db: AsyncSession,
        tenant_id: str,
        name: str,
    ) -> Customer | None:
        """
        根据名称获取客户（用于导入时去重）
        
        Args:
            db: 数据库会话
            tenant_id: 租户ID
            name: 客户名称
        
        Returns:
            客户实例或 None
        """
        query = select(self.model).where(
            self.model.tenant_id == tenant_id,
            self.model.name == name,
            self.model.deleted_at.is_(None)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()


crud_customer = CRUDCustomer(Customer)
