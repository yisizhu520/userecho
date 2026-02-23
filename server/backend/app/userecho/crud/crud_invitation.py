"""邀请 CRUD"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.userecho.model.invitation import Invitation
from backend.utils.timezone import timezone


class CRUDInvitation:
    """邀请 CRUD"""

    async def get(self, db: AsyncSession, invitation_id: str) -> Invitation | None:
        """根据ID获取邀请"""
        query = select(Invitation).where(Invitation.id == invitation_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_token(self, db: AsyncSession, token: str) -> Invitation | None:
        """根据token获取邀请"""
        query = select(Invitation).where(Invitation.token == token)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, obj_in: Invitation) -> Invitation:
        """创建邀请"""
        db.add(obj_in)
        await db.flush()
        await db.refresh(obj_in)
        return obj_in

    async def update(self, db: AsyncSession, db_obj: Invitation, obj_in: dict) -> Invitation:
        """更新邀请"""
        for field, value in obj_in.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        db_obj.updated_at = timezone.now()
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def increment_usage(self, db: AsyncSession, invitation_id: str) -> Invitation | None:
        """增加使用次数"""
        invitation = await self.get(db, invitation_id)
        if invitation:
            invitation.used_count += 1
            invitation.updated_at = timezone.now()
            await db.flush()
            await db.refresh(invitation)
        return invitation

    async def get_list(
        self,
        db: AsyncSession,
        status: str | None = None,
        source: str | None = None,
        campaign: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Invitation], int]:
        """获取邀请列表（分页）"""
        # 构建查询条件
        conditions = []
        if status:
            conditions.append(Invitation.status == status)
        if source:
            conditions.append(Invitation.source == source)
        if campaign:
            conditions.append(Invitation.campaign == campaign)

        # 查询列表
        query = select(Invitation).order_by(Invitation.created_at.desc()).offset(skip).limit(limit)
        if conditions:
            query = query.where(*conditions)

        result = await db.execute(query)
        items = list(result.scalars().all())

        # 查询总数
        count_query = select(func.count(Invitation.id))
        if conditions:
            count_query = count_query.where(*conditions)
        count_result = await db.execute(count_query)
        total = count_result.scalar_one()

        return items, total

    async def delete(self, db: AsyncSession, invitation_id: str) -> bool:
        """删除邀请（软删除，标记为disabled）"""
        invitation = await self.get(db, invitation_id)
        if invitation:
            invitation.status = "disabled"
            invitation.updated_at = timezone.now()
            await db.flush()
            return True
        return False


invitation_dao = CRUDInvitation()
