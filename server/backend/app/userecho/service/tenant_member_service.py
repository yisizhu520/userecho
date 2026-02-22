from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.crud.crud_user import user_dao
from backend.app.admin.model import User
from backend.app.userecho.crud.crud_tenant_member import tenant_member_dao
from backend.app.userecho.crud.crud_tenant_permission import tenant_permission_dao
from backend.app.userecho.crud.crud_tenant_role import tenant_role_dao
from backend.app.userecho.model.tenant_user import TenantUser
from backend.app.userecho.service.tenant_role_service import tenant_role_service
from backend.common.exception import errors
from backend.app.admin.utils.password_security import get_hash_password


class TenantMemberService:
    """租户成员服务类"""

    @staticmethod
    async def get(db: AsyncSession, tenant_user_id: str) -> TenantUser:
        """获取成员详情"""
        member = await tenant_member_dao.get(db, tenant_user_id)
        if not member:
            raise errors.NotFoundError(msg='成员不存在')
        return member

    @staticmethod
    async def get_list(db: AsyncSession, tenant_id: str, *, status: str | None = None) -> Sequence[TenantUser]:
        """获取租户的成员列表"""
        return await tenant_member_dao.get_list(db, tenant_id, status=status)

    @staticmethod
    async def get_member_role_ids(db: AsyncSession, tenant_user_id: str) -> list[str]:
        """获取成员的角色 ID 列表"""
        roles = await tenant_member_dao.get_member_roles(db, tenant_user_id)
        return [r.role_id for r in roles]

    @staticmethod
    async def get_member_permissions(db: AsyncSession, tenant_user_id: str) -> list[str]:
        """获取成员的权限代码列表（多角色取并集）"""
        roles = await tenant_member_dao.get_member_roles(db, tenant_user_id)
        all_permissions: set[str] = set()
        for role in roles:
            perms = await tenant_permission_dao.get_role_permission_codes(db, role.role_id)
            all_permissions.update(perms)
        return list(all_permissions)

    @staticmethod
    async def get_user_permission_codes(db: AsyncSession, tenant_id: str, user_id: int) -> list[str]:
        """
        获取用户在指定租户内的权限代码列表

        通过 user_id 查询，用于用户信息接口返回租户权限码

        :param db: 数据库会话
        :param tenant_id: 租户 ID
        :param user_id: 用户 ID
        :return: 权限代码列表
        """
        # 先查找用户对应的租户成员
        member = await tenant_member_dao.get_by_user_id(db, tenant_id, user_id)
        if not member:
            return []

        # 获取成员的权限码
        return await TenantMemberService.get_member_permissions(db, member.id)

    @staticmethod
    async def create(
        db: AsyncSession,
        *,
        tenant_id: str,
        username: str,
        nickname: str,
        password: str,
        email: str | None = None,
        role_ids: list[str] | None = None,
        created_by: int | None = None,
    ) -> tuple[User, TenantUser]:
        """
        创建成员（直接创建用户账号）

        1. 创建 sys_user 记录
        2. 创建 tenant_users 关联
        3. 分配角色
        """
        # 检查用户名是否已存在
        existing_user = await user_dao.get_by_username(db, username)
        if existing_user:
            # 检查是否已是该租户成员
            existing_member = await tenant_member_dao.get_by_user_id(db, tenant_id, existing_user.id)
            if existing_member:
                raise errors.ConflictError(msg='该用户已是租户成员')
            # 用户存在但不是成员，直接添加为成员
            user = existing_user
        else:
            # 创建新用户
            import bcrypt
            salt = bcrypt.gensalt()
            hashed_password = get_hash_password(password, salt)
            user = User(
                username=username,
                nickname=nickname,
                password=hashed_password,
                salt=salt,
                email=email,
                tenant_id=tenant_id,
            )
            db.add(user)
            await db.flush()

        # 创建成员关联
        member = await tenant_member_dao.create(db, tenant_id=tenant_id, user_id=user.id, user_type='member')

        # 分配角色
        if role_ids:
            await tenant_member_dao.set_member_roles(db, member.id, role_ids, assigned_by=created_by)
        else:
            # 默认分配 viewer 角色
            viewer_role = await tenant_role_dao.get_by_code(db, tenant_id, 'viewer')
            if viewer_role:
                await tenant_member_dao.set_member_roles(db, member.id, [viewer_role.id], assigned_by=created_by)

        return user, member

    @staticmethod
    async def update(
        db: AsyncSession,
        tenant_user_id: str,
        *,
        user_type: str | None = None,
        status: str | None = None,
    ) -> TenantUser:
        """更新成员信息"""
        member = await tenant_member_dao.get(db, tenant_user_id)
        if not member:
            raise errors.NotFoundError(msg='成员不存在')

        return await tenant_member_dao.update(db, member, user_type=user_type, status=status)

    @staticmethod
    async def update_roles(db: AsyncSession, tenant_user_id: str, role_ids: list[str], assigned_by: int | None = None) -> None:
        """更新成员角色"""
        member = await tenant_member_dao.get(db, tenant_user_id)
        if not member:
            raise errors.NotFoundError(msg='成员不存在')

        await tenant_member_dao.set_member_roles(db, tenant_user_id, role_ids, assigned_by=assigned_by)

    @staticmethod
    async def delete(db: AsyncSession, tenant_user_id: str) -> None:
        """移除成员"""
        member = await tenant_member_dao.get(db, tenant_user_id)
        if not member:
            raise errors.NotFoundError(msg='成员不存在')

        # 检查是否是租户管理员
        if member.user_type == 'admin':
            raise errors.ForbiddenError(msg='不能移除租户管理员')

        await tenant_member_dao.delete(db, member)


tenant_member_service = TenantMemberService()
