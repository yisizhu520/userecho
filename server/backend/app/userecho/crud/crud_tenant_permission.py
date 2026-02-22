from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.userecho.model.tenant_permission import TenantPermission, TenantRolePermission


class CRUDTenantPermission:
    """租户权限 CRUD 操作"""

    @staticmethod
    async def get_all(db: AsyncSession) -> Sequence[TenantPermission]:
        """获取所有权限点（全局定义）"""
        stmt = select(TenantPermission).order_by(TenantPermission.sort)
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_by_code(db: AsyncSession, code: str) -> TenantPermission | None:
        """根据权限代码获取权限"""
        stmt = select(TenantPermission).where(TenantPermission.code == code)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_role_permissions(db: AsyncSession, role_id: str) -> Sequence[TenantPermission]:
        """获取角色的权限列表"""
        stmt = (
            select(TenantPermission)
            .join(TenantRolePermission, TenantRolePermission.permission_id == TenantPermission.id)
            .where(TenantRolePermission.role_id == role_id)
            .order_by(TenantPermission.sort)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_role_permission_codes(db: AsyncSession, role_id: str) -> list[str]:
        """获取角色的权限代码列表"""
        permissions = await CRUDTenantPermission.get_role_permissions(db, role_id)
        return [p.code for p in permissions]

    @staticmethod
    async def set_role_permissions(db: AsyncSession, role_id: str, permission_ids: list[str]) -> None:
        """设置角色的权限（全量覆盖）"""
        # 删除旧的权限关联
        stmt = select(TenantRolePermission).where(TenantRolePermission.role_id == role_id)
        result = await db.execute(stmt)
        old_perms = result.scalars().all()
        for perm in old_perms:
            await db.delete(perm)

        # 创建新的权限关联
        for perm_id in permission_ids:
            new_perm = TenantRolePermission(role_id=role_id, permission_id=perm_id)
            db.add(new_perm)

        await db.flush()


tenant_permission_dao = CRUDTenantPermission()
