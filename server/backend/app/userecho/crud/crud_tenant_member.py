from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.userecho.model.tenant_user import TenantUser, TenantUserRole


class CRUDTenantMember:
    """租户成员 CRUD 操作"""

    @staticmethod
    async def get(db: AsyncSession, tenant_user_id: str) -> TenantUser | None:
        """获取单个成员"""
        return await db.get(TenantUser, tenant_user_id)

    @staticmethod
    async def get_by_user_id(db: AsyncSession, tenant_id: str, user_id: int) -> TenantUser | None:
        """根据租户 ID 和用户 ID 获取成员"""
        stmt = select(TenantUser).where(TenantUser.tenant_id == tenant_id, TenantUser.user_id == user_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_list(db: AsyncSession, tenant_id: str, *, status: str | None = None) -> Sequence[TenantUser]:
        """获取租户的成员列表（包含实时反馈数量统计）"""
        from sqlalchemy import func

        from backend.app.userecho.model.feedback import Feedback

        # 子查询：统计每个成员提交的反馈数
        feedback_count_subq = (
            select(Feedback.submitter_id, func.count(Feedback.id).label('count'))
            .where(Feedback.tenant_id == tenant_id)
            .where(Feedback.deleted_at.is_(None))  # 排除已删除的反馈
            .group_by(Feedback.submitter_id)
            .subquery()
        )

        # 主查询：关联 TenantUser 和反馈统计
        from backend.app.admin.model.user import User

        stmt = (
            select(TenantUser, func.coalesce(feedback_count_subq.c.count, 0).label('real_feedback_count'))
            .outerjoin(User, TenantUser.user_id == User.id)
            .outerjoin(feedback_count_subq, User.id == feedback_count_subq.c.submitter_id)
            .where(TenantUser.tenant_id == tenant_id)
            .order_by(TenantUser.joined_at.desc())
        )

        if status:
            stmt = stmt.where(TenantUser.status == status)

        result = await db.execute(stmt)
        rows = result.all()

        # 动态设置 feedback_count
        members = []
        for row in rows:
            member = row[0]  # TenantUser 对象
            member.feedback_count = row[1]  # 实时统计的反馈数
            members.append(member)

        return members

    @staticmethod
    async def create(db: AsyncSession, *, tenant_id: str, user_id: int, user_type: str = 'member') -> TenantUser:
        """创建成员"""
        member = TenantUser(tenant_id=tenant_id, user_id=user_id, user_type=user_type)
        db.add(member)
        await db.flush()
        return member

    @staticmethod
    async def update(
        db: AsyncSession, member: TenantUser, *, user_type: str | None = None, status: str | None = None
    ) -> TenantUser:
        """更新成员"""
        if user_type is not None:
            member.user_type = user_type
        if status is not None:
            member.status = status
        await db.flush()
        return member

    @staticmethod
    async def delete(db: AsyncSession, member: TenantUser) -> None:
        """删除成员"""
        await db.delete(member)
        await db.flush()

    @staticmethod
    async def get_member_roles(db: AsyncSession, tenant_user_id: str) -> Sequence[TenantUserRole]:
        """获取成员的角色列表"""
        stmt = select(TenantUserRole).where(TenantUserRole.tenant_user_id == tenant_user_id)
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def set_member_roles(
        db: AsyncSession, tenant_user_id: str, role_ids: list[str], assigned_by: int | None = None
    ) -> None:
        """设置成员的角色（全量覆盖）"""
        # 删除旧的角色关联
        stmt = select(TenantUserRole).where(TenantUserRole.tenant_user_id == tenant_user_id)
        result = await db.execute(stmt)
        old_roles = result.scalars().all()
        for role in old_roles:
            await db.delete(role)

        # 立即 flush 删除操作，确保删除先于插入执行
        await db.flush()

        # 创建新的角色关联
        for role_id in role_ids:
            new_role = TenantUserRole(tenant_user_id=tenant_user_id, role_id=role_id, assigned_by=assigned_by)
            db.add(new_role)

        await db.flush()


tenant_member_dao = CRUDTenantMember()
