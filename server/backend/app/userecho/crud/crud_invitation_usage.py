"""邀请使用记录 CRUD"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.userecho.model.invitation_usage import InvitationUsage


class CRUDInvitationUsage:
    """邀请使用记录 CRUD"""

    async def get(self, db: AsyncSession, usage_id: str) -> InvitationUsage | None:
        """根据ID获取使用记录"""
        query = select(InvitationUsage).where(InvitationUsage.id == usage_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_email(self, db: AsyncSession, email: str) -> InvitationUsage | None:
        """根据邮箱获取使用记录（检查是否已使用）"""
        query = select(InvitationUsage).where(InvitationUsage.registered_email == email)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_invitation(
        self, db: AsyncSession, invitation_id: str, skip: int = 0, limit: int = 100
    ) -> tuple[list[InvitationUsage], int]:
        """获取邀请的使用记录列表"""
        # 查询列表
        query = (
            select(InvitationUsage)
            .where(InvitationUsage.invitation_id == invitation_id)
            .order_by(InvitationUsage.used_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        items = list(result.scalars().all())

        # 查询总数
        count_query = select(func.count(InvitationUsage.id)).where(InvitationUsage.invitation_id == invitation_id)
        count_result = await db.execute(count_query)
        total = count_result.scalar_one()

        return items, total

    async def create(self, db: AsyncSession, obj_in: InvitationUsage) -> InvitationUsage:
        """创建使用记录"""
        db.add(obj_in)
        await db.flush()
        await db.refresh(obj_in)
        return obj_in

    async def update(self, db: AsyncSession, db_obj: InvitationUsage, obj_in: dict) -> InvitationUsage:
        """更新使用记录"""
        for field, value in obj_in.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def mark_onboarding_completed(self, db: AsyncSession, usage_id: str, tenant_id: str) -> InvitationUsage | None:
        """标记完成引导"""
        usage = await self.get(db, usage_id)
        if usage:
            usage.completed_onboarding = True
            usage.created_tenant_id = tenant_id
            await db.flush()
            await db.refresh(usage)
        return usage


invitation_usage_dao = CRUDInvitationUsage()
