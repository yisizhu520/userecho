"""Customer CRUD"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.userecho.crud.base import TenantAwareCRUD
from backend.app.userecho.model.customer import Customer


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
            self.model.tenant_id == tenant_id, self.model.name == name, self.model.deleted_at.is_(None)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_multi_with_total(
        self,
        db: AsyncSession,
        tenant_id: str,
        skip: int = 0,
        limit: int = 20,
        search: str | None = None,
        customer_type: str | None = None,
    ) -> tuple[list[Customer], int]:
        """
        获取客户列表（带总数）

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            skip: 跳过数量
            limit: 返回数量
            search: 搜索关键词（模糊匹配客户名称）
            customer_type: 客户类型筛选

        Returns:
            (客户列表, 总数)
        """
        from sqlalchemy import func

        # 构建基础条件
        base_conditions = [
            self.model.tenant_id == tenant_id,
            self.model.deleted_at.is_(None),
        ]

        # 添加搜索条件
        if search:
            base_conditions.append(self.model.name.ilike(f'%{search}%'))

        # 添加类型筛选
        if customer_type:
            base_conditions.append(self.model.customer_type == customer_type)

        # 查询总数
        count_query = select(func.count(self.model.id)).where(*base_conditions)
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()

        # 查询列表
        list_query = (
            select(self.model)
            .where(*base_conditions)
            .order_by(self.model.business_value.desc(), self.model.created_time.desc())
            .offset(skip)
            .limit(limit)
        )
        list_result = await db.execute(list_query)
        items = list(list_result.scalars().all())

        return items, total

    async def search_by_name(
        self,
        db: AsyncSession,
        tenant_id: str,
        query: str,
        limit: int = 10,
    ) -> list[Customer]:
        """
        模糊搜索客户名称

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            query: 搜索关键词
            limit: 返回数量上限

        Returns:
            匹配的客户列表
        """
        stmt = (
            select(self.model)
            .where(
                self.model.tenant_id == tenant_id,
                self.model.name.ilike(f'%{query}%'),
                self.model.deleted_at.is_(None),
            )
            .order_by(self.model.name)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())


crud_customer = CRUDCustomer(Customer)
