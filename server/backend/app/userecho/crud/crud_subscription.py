"""订阅体系 CRUD"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.userecho.model.subscription import (
    SubscriptionHistory,
    SubscriptionPlan,
    TenantSubscription,
)


class CRUDSubscriptionPlan:
    """套餐计划 CRUD"""

    async def get_by_code(self, db: AsyncSession, code: str) -> SubscriptionPlan | None:
        """根据代号获取套餐"""
        query = select(SubscriptionPlan).where(SubscriptionPlan.code == code)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_all_active(self, db: AsyncSession) -> list[SubscriptionPlan]:
        """获取所有启用套餐"""
        query = (
            select(SubscriptionPlan).where(SubscriptionPlan.is_active.is_(True)).order_by(SubscriptionPlan.sort_order)
        )
        result = await db.execute(query)
        return list(result.scalars().all())


class CRUDTenantSubscription:
    """租户订阅 CRUD"""

    async def get_by_tenant(self, db: AsyncSession, tenant_id: str) -> TenantSubscription | None:
        """获取租户当前的订阅记录"""
        query = select(TenantSubscription).where(TenantSubscription.tenant_id == tenant_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, obj_in: TenantSubscription) -> TenantSubscription:
        """创建订阅记录"""
        db.add(obj_in)
        await db.flush()
        await db.refresh(obj_in)
        return obj_in

    async def update(self, db: AsyncSession, db_obj: TenantSubscription, obj_in: dict) -> TenantSubscription:
        """更新订阅记录"""
        for field, value in obj_in.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj


class CRUDSubscriptionHistory:
    """订阅历史 CRUD"""

    async def create(self, db: AsyncSession, obj_in: SubscriptionHistory) -> SubscriptionHistory:
        """创建历史记录"""
        db.add(obj_in)
        await db.flush()
        await db.refresh(obj_in)
        return obj_in

    async def get_by_tenant(
        self, db: AsyncSession, tenant_id: str, skip: int = 0, limit: int = 20
    ) -> list[SubscriptionHistory]:
        """获取租户订阅历史"""
        query = (
            select(SubscriptionHistory)
            .where(SubscriptionHistory.tenant_id == tenant_id)
            .order_by(SubscriptionHistory.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return list(result.scalars().all())


subscription_plan_dao = CRUDSubscriptionPlan()
tenant_subscription_dao = CRUDTenantSubscription()
subscription_history_dao = CRUDSubscriptionHistory()
