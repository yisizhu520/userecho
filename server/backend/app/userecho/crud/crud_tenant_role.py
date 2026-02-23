from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.userecho.model.tenant_role import TenantRole


class CRUDTenantRole:
    """租户角色 CRUD 操作"""

    @staticmethod
    async def get(db: AsyncSession, role_id: str) -> TenantRole | None:
        """获取单个角色"""
        return await db.get(TenantRole, role_id)

    @staticmethod
    async def get_by_code(db: AsyncSession, tenant_id: str, code: str) -> TenantRole | None:
        """根据租户 ID 和角色代码获取角色"""
        stmt = select(TenantRole).where(TenantRole.tenant_id == tenant_id, TenantRole.code == code)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_list(db: AsyncSession, tenant_id: str, *, status: str | None = None) -> Sequence[TenantRole]:
        """获取租户的角色列表"""
        stmt = (
            select(TenantRole)
            .where(TenantRole.tenant_id == tenant_id)
            .order_by(TenantRole.sort, TenantRole.created_time)
        )
        if status:
            stmt = stmt.where(TenantRole.status == status)
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def create(
        db: AsyncSession,
        *,
        tenant_id: str,
        name: str,
        code: str,
        description: str | None = None,
        is_builtin: bool = False,
        sort: int = 0,
    ) -> TenantRole:
        """创建角色"""
        role = TenantRole(
            tenant_id=tenant_id,
            name=name,
            code=code,
            description=description,
            is_builtin=is_builtin,
            sort=sort,
        )
        db.add(role)
        await db.flush()
        return role

    @staticmethod
    async def update(
        db: AsyncSession,
        role: TenantRole,
        *,
        name: str | None = None,
        description: str | None = None,
        sort: int | None = None,
        status: str | None = None,
    ) -> TenantRole:
        """更新角色"""
        if name is not None:
            role.name = name
        if description is not None:
            role.description = description
        if sort is not None:
            role.sort = sort
        if status is not None:
            role.status = status
        await db.flush()
        return role

    @staticmethod
    async def delete(db: AsyncSession, role: TenantRole) -> None:
        """删除角色"""
        await db.delete(role)
        await db.flush()


tenant_role_dao = CRUDTenantRole()
