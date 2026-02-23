"""邮箱黑名单 CRUD"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.userecho.model.email_blacklist import EmailBlacklist
from backend.utils.timezone import timezone


class CRUDEmailBlacklist:
    """邮箱黑名单 CRUD"""

    async def get(self, db: AsyncSession, blacklist_id: str) -> EmailBlacklist | None:
        """根据ID获取黑名单"""
        query = select(EmailBlacklist).where(EmailBlacklist.id == blacklist_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_domain(self, db: AsyncSession, domain: str) -> EmailBlacklist | None:
        """根据域名获取黑名单"""
        query = select(EmailBlacklist).where(EmailBlacklist.domain == domain.lower())
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def is_blocked(self, db: AsyncSession, domain: str) -> bool:
        """检查域名是否在黑名单中（且启用）"""
        query = select(EmailBlacklist).where(
            EmailBlacklist.domain == domain.lower(), EmailBlacklist.is_active.is_(True)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none() is not None

    async def create(self, db: AsyncSession, obj_in: EmailBlacklist) -> EmailBlacklist:
        """添加黑名单"""
        db.add(obj_in)
        await db.flush()
        await db.refresh(obj_in)
        return obj_in

    async def update(self, db: AsyncSession, db_obj: EmailBlacklist, obj_in: dict) -> EmailBlacklist:
        """更新黑名单"""
        for field, value in obj_in.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        db_obj.updated_at = timezone.now()
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def get_list(
        self, db: AsyncSession, type: str | None = None, is_active: bool | None = None, skip: int = 0, limit: int = 100
    ) -> tuple[list[EmailBlacklist], int]:
        """获取黑名单列表"""
        # 构建查询条件
        conditions = []
        if type:
            conditions.append(EmailBlacklist.type == type)
        if is_active is not None:
            conditions.append(EmailBlacklist.is_active.is_(is_active))

        # 查询列表
        query = select(EmailBlacklist).order_by(EmailBlacklist.created_at.desc()).offset(skip).limit(limit)
        if conditions:
            query = query.where(*conditions)

        result = await db.execute(query)
        items = list(result.scalars().all())

        # 查询总数
        count_query = select(func.count(EmailBlacklist.id))
        if conditions:
            count_query = count_query.where(*conditions)
        count_result = await db.execute(count_query)
        total = count_result.scalar_one()

        return items, total

    async def delete(self, db: AsyncSession, blacklist_id: str) -> bool:
        """删除黑名单"""
        blacklist = await self.get(db, blacklist_id)
        if blacklist:
            await db.delete(blacklist)
            await db.flush()
            return True
        return False


email_blacklist_dao = CRUDEmailBlacklist()
