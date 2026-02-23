from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.userecho.crud.crud_tenant_permission import tenant_permission_dao
from backend.app.userecho.crud.crud_tenant_role import tenant_role_dao
from backend.app.userecho.model.tenant_permission import TenantPermission
from backend.app.userecho.model.tenant_role import TenantRole
from backend.common.exception import errors


# 内置角色定义
BUILTIN_ROLES = [
    {
        'code': 'admin',
        'name': '管理员',
        'description': '租户管理员，拥有所有权限',
        'permissions': ['feedback', 'discovery', 'topic', 'customer', 'insight', 'settings', 'member', 'role']
    },
    {
        'code': 'product_manager',
        'name': '产品经理',
        'description': '管理需求和反馈',
        'permissions': ['feedback', 'discovery', 'topic', 'customer', 'insight']
    },
    {
        'code': 'sales',
        'name': '销售',
        'description': '录入客户反馈',
        'permissions': ['feedback', 'customer']
    },
    {
        'code': 'developer',
        'name': '开发者',
        'description': '查看需求和反馈',
        'permissions': ['topic', 'discovery']
    },
    {
        'code': 'viewer',
        'name': '观察者',
        'description': '只读权限',
        'permissions': ['feedback', 'topic', 'customer', 'insight']
    },
]


class TenantRoleService:
    """租户角色服务类"""

    @staticmethod
    async def get(db: AsyncSession, role_id: str) -> TenantRole:
        """获取角色详情"""
        role = await tenant_role_dao.get(db, role_id)
        if not role:
            raise errors.NotFoundError(msg='角色不存在')
        return role

    @staticmethod
    async def get_list(db: AsyncSession, tenant_id: str, *, status: str | None = None) -> Sequence[TenantRole]:
        """获取租户的角色列表"""
        return await tenant_role_dao.get_list(db, tenant_id, status=status)

    @staticmethod
    async def get_permissions(db: AsyncSession) -> Sequence[TenantPermission]:
        """获取所有权限点"""
        return await tenant_permission_dao.get_all(db)

    @staticmethod
    async def get_role_permissions(db: AsyncSession, role_id: str) -> Sequence[TenantPermission]:
        """获取角色的权限列表"""
        return await tenant_permission_dao.get_role_permissions(db, role_id)

    @staticmethod
    async def create(
        db: AsyncSession,
        *,
        tenant_id: str,
        name: str,
        code: str,
        description: str | None = None,
        permission_ids: list[str] | None = None,
    ) -> TenantRole:
        """创建角色"""
        # 检查角色代码是否已存在
        existing = await tenant_role_dao.get_by_code(db, tenant_id, code)
        if existing:
            raise errors.ConflictError(msg='角色代码已存在')

        role = await tenant_role_dao.create(db, tenant_id=tenant_id, name=name, code=code, description=description)

        # 设置权限
        if permission_ids:
            await tenant_permission_dao.set_role_permissions(db, role.id, permission_ids)

        return role

    @staticmethod
    async def update(
        db: AsyncSession,
        role_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        status: str | None = None,
    ) -> TenantRole:
        """更新角色"""
        role = await tenant_role_dao.get(db, role_id)
        if not role:
            raise errors.NotFoundError(msg='角色不存在')

        return await tenant_role_dao.update(db, role, name=name, description=description, status=status)

    @staticmethod
    async def update_permissions(db: AsyncSession, role_id: str, permission_ids: list[str]) -> None:
        """更新角色权限"""
        role = await tenant_role_dao.get(db, role_id)
        if not role:
            raise errors.NotFoundError(msg='角色不存在')

        await tenant_permission_dao.set_role_permissions(db, role_id, permission_ids)

    @staticmethod
    async def delete(db: AsyncSession, role_id: str) -> None:
        """删除角色"""
        role = await tenant_role_dao.get(db, role_id)
        if not role:
            raise errors.NotFoundError(msg='角色不存在')

        if role.is_builtin:
            raise errors.ForbiddenError(msg='内置角色不可删除')

        await tenant_role_dao.delete(db, role)

    @staticmethod
    async def init_builtin_roles(db: AsyncSession, tenant_id: str) -> list[TenantRole]:
        """为租户初始化内置角色"""
        created_roles = []

        # 获取所有权限
        all_permissions = await tenant_permission_dao.get_all(db)
        perm_code_to_id = {p.code: p.id for p in all_permissions}

        for i, role_def in enumerate(BUILTIN_ROLES):
            # 检查是否已存在
            existing = await tenant_role_dao.get_by_code(db, tenant_id, role_def['code'])
            if existing:
                continue

            # 创建角色
            role = await tenant_role_dao.create(
                db,
                tenant_id=tenant_id,
                name=role_def['name'],
                code=role_def['code'],
                description=role_def['description'],
                is_builtin=True,
                sort=i,
            )

            # 设置权限
            perm_ids = [perm_code_to_id[code] for code in role_def['permissions'] if code in perm_code_to_id]
            if perm_ids:
                await tenant_permission_dao.set_role_permissions(db, role.id, perm_ids)

            created_roles.append(role)

        return created_roles


tenant_role_service = TenantRoleService()
