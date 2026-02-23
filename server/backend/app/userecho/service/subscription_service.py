"""订阅服务层"""

from datetime import timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.userecho.crud.crud_subscription import (
    subscription_history_dao,
    subscription_plan_dao,
    tenant_subscription_dao,
)
from backend.app.userecho.model.subscription import (
    PlanCode,
    SubscriptionAction,
    SubscriptionHistory,
    SubscriptionPlan,
    SubscriptionSource,
    SubscriptionStatus,
    TenantSubscription,
)
from backend.app.userecho.service.credits_service import credits_service
from backend.common.exception.errors import NotFoundError
from backend.utils.timezone import timezone


class SubscriptionService:
    """订阅管理服务"""

    async def get_current_subscription(self, db: AsyncSession, tenant_id: str) -> TenantSubscription:
        """获取当前订阅（不存在则创建默认试用）"""
        sub = await tenant_subscription_dao.get_by_tenant(db, tenant_id)
        if not sub:
            # 默认创建试用订阅
            sub = await self.create_trial_subscription(db, tenant_id)

        # 检查是否过期
        now = timezone.now()
        if sub.status in [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL] and sub.expires_at < now:
            await self._expire_subscription(db, sub)

        return sub

    async def get_plan(self, db: AsyncSession, plan_id: str) -> SubscriptionPlan | None:
        """获取套餐信息"""
        return await db.get(SubscriptionPlan, plan_id)

    async def create_trial_subscription(self, db: AsyncSession, tenant_id: str) -> TenantSubscription:
        """创建试用订阅（默认 90 天专业版）"""
        # 获取专业版套餐
        plan = await subscription_plan_dao.get_by_code(db, PlanCode.PRO)
        if not plan:
            # Fallback to starter if pro not found (shouldn't happen if initialized)
            plan = await subscription_plan_dao.get_by_code(db, PlanCode.STARTER)

        if not plan:
            raise NotFoundError(msg="Default subscription plan not found")

        now = timezone.now()
        expires_at = now + timedelta(days=90)

        sub = TenantSubscription(
            tenant_id=tenant_id,
            plan_id=plan.id,
            status=SubscriptionStatus.TRIAL,
            started_at=now,
            expires_at=expires_at,
            trial_ends_at=expires_at,
            source=SubscriptionSource.MANUAL,  # System auto
            notes="系统自动创建试用订阅",
        )
        sub = await tenant_subscription_dao.create(db, sub)

        # 记录历史
        await self._record_history(
            db,
            tenant_id,
            sub.id,
            SubscriptionAction.CREATED,
            None,
            plan.code,
            reason="Initial trial subscription",
        )

        # 同步积分
        await credits_service.sync_subscription_plan(db, tenant_id, plan.code, plan.ai_credits_monthly)

        return sub

    async def manual_update_subscription(
        self,
        db: AsyncSession,
        tenant_id: str,
        plan_code: str,
        expires_at: Any,
        status: str = SubscriptionStatus.ACTIVE,
        operator_id: str | None = None,
        notes: str | None = None,
    ) -> TenantSubscription:
        """管理员手动更新订阅"""
        sub = await tenant_subscription_dao.get_by_tenant(db, tenant_id)

        new_plan = await subscription_plan_dao.get_by_code(db, plan_code)
        if not new_plan:
            raise NotFoundError(msg=f"Plan {plan_code} not found")

        old_plan_code = None
        action = SubscriptionAction.CREATED

        if sub:
            # 获取旧套餐信息
            old_plan = await self.get_plan(db, sub.plan_id)
            old_plan_code = old_plan.code if old_plan else "unknown"

            update_data = {
                "plan_id": new_plan.id,
                "status": status,
                "expires_at": expires_at,
                "notes": notes,
            }

            # 判断操作类型
            if status == SubscriptionStatus.CANCELED:
                update_data["canceled_at"] = timezone.now()
                action = SubscriptionAction.CANCELED
            elif old_plan and new_plan.price_monthly > old_plan.price_monthly:
                action = SubscriptionAction.UPGRADED
            elif old_plan and new_plan.price_monthly < old_plan.price_monthly:
                action = SubscriptionAction.DOWNGRADED
            elif old_plan and new_plan.id == old_plan.id:
                action = SubscriptionAction.RENEWED  # or EXTENDED
            else:
                action = SubscriptionAction.UPGRADED  # Default

            sub = await tenant_subscription_dao.update(db, sub, update_data)
        else:
            # Create new
            sub = TenantSubscription(
                tenant_id=tenant_id,
                plan_id=new_plan.id,
                status=status,
                started_at=timezone.now(),
                expires_at=expires_at,
                source=SubscriptionSource.MANUAL,
                created_by=operator_id,
                notes=notes,
            )
            sub = await tenant_subscription_dao.create(db, sub)

        # Record history
        await self._record_history(
            db,
            tenant_id,
            sub.id,
            action,
            old_plan_code,
            new_plan.code,
            operator_id,
            reason=notes,
        )

        # Sync credits
        await credits_service.sync_subscription_plan(db, tenant_id, new_plan.code, new_plan.ai_credits_monthly)

        return sub

    async def _expire_subscription(self, db: AsyncSession, sub: TenantSubscription) -> None:
        """过期订阅"""
        await tenant_subscription_dao.update(db, sub, {"status": SubscriptionStatus.EXPIRED})

        # 获取当前 Plan Code 用于记录
        plan = await self.get_plan(db, sub.plan_id)
        plan_code = plan.code if plan else ""

        await self._record_history(
            db,
            sub.tenant_id,
            sub.id,
            SubscriptionAction.EXPIRED,
            plan_code,
            plan_code,  # Plan didn't change
            reason="Subscription expired",
        )

    async def _record_history(
        self,
        db: AsyncSession,
        tenant_id: str,
        sub_id: str,
        action: str,
        old_code: str | None,
        new_code: str | None,
        changed_by: str | None = None,
        reason: str | None = None,
    ) -> None:
        """记录订阅变更历史"""
        history = SubscriptionHistory(
            tenant_id=tenant_id,
            subscription_id=sub_id,
            action=action,
            old_plan_code=old_code,
            new_plan_code=new_code or "",
            changed_by=changed_by,
            reason=reason,
        )
        await subscription_history_dao.create(db, history)


subscription_service = SubscriptionService()
