"""积分服务

提供积分消耗、查询、刷新等功能
"""

from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.userecho.model.credits import CreditsConfig, CreditsUsageLog, TenantCredits
from backend.common.log import log
from backend.utils.timezone import timezone

# 默认积分消耗配置（数据库无配置时使用）
DEFAULT_OPERATION_COSTS = {
    'clustering': 10,  # AI 聚类（每次）
    'screenshot': 5,  # 截图识别（每张）
    'summary': 2,  # AI 摘要（每条反馈）
    'embedding': 1,  # 向量化（每条反馈）
    'insight': 20,  # 洞察报告（每份）
}

# 默认套餐月度额度
DEFAULT_PLAN_QUOTAS = {
    'starter': 500,  # 启航版 ¥99/月
    'pro': 2000,  # 专业版 ¥199/月
    'team': 10000,  # 团队版 ¥599/月
    'enterprise': -1,  # 企业版（无限制，-1 表示不限）
}


class CreditsService:
    """通用积分管理服务"""

    async def get_operation_cost(self, db: AsyncSession, operation_type: str) -> int:
        """获取操作的积分消耗值"""
        config_key = f'cost_{operation_type}'
        result = await db.execute(select(CreditsConfig).where(CreditsConfig.config_key == config_key))
        config = result.scalar_one_or_none()

        if config:
            return config.config_value

        return DEFAULT_OPERATION_COSTS.get(operation_type, 1)

    async def get_plan_quota(self, db: AsyncSession, plan_type: str) -> int:
        """获取套餐的月度积分额度"""
        config_key = f'quota_{plan_type}'
        result = await db.execute(select(CreditsConfig).where(CreditsConfig.config_key == config_key))
        config = result.scalar_one_or_none()

        if config:
            return config.config_value

        return DEFAULT_PLAN_QUOTAS.get(plan_type, 500)

    async def get_or_create_tenant_credits(self, db: AsyncSession, tenant_id: str) -> TenantCredits:
        """获取或创建租户积分配置"""
        result = await db.execute(select(TenantCredits).where(TenantCredits.tenant_id == tenant_id))
        tenant_credits = result.scalar_one_or_none()

        if tenant_credits:
            # 检查是否需要刷新
            await self._check_and_refresh_if_needed(db, tenant_credits)
            return tenant_credits

        # 创建新的租户积分配置
        now = timezone.now()
        next_refresh = now + timedelta(days=30)
        monthly_quota = await self.get_plan_quota(db, 'starter')

        tenant_credits = TenantCredits(
            tenant_id=tenant_id,
            plan_type='starter',
            monthly_quota=monthly_quota,
            current_balance=monthly_quota,
            total_used=0,
            last_refresh_at=now,
            next_refresh_at=next_refresh,
        )
        db.add(tenant_credits)
        await db.flush()

        log.info(f'Created tenant credits for tenant {tenant_id}: quota={monthly_quota}')
        return tenant_credits

    async def consume(
        self,
        db: AsyncSession,
        tenant_id: str,
        operation_type: str,
        count: int = 1,
        user_id: str | None = None,
        description: str | None = None,
        extra_data: dict | None = None,
    ) -> dict:
        """
        消耗积分

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            operation_type: 操作类型
            count: 操作次数
            user_id: 操作用户ID
            description: 操作描述
            extra_data: 扩展信息

        Returns:
            {
                "success": True/False,
                "credits_cost": 消耗积分数,
                "remaining": 剩余积分,
                "warning": 余额不足时的警告信息（可选）
            }
        """
        try:
            tenant_credits = await self.get_or_create_tenant_credits(db, tenant_id)

            # 获取单次操作消耗
            unit_cost = await self.get_operation_cost(db, operation_type)
            total_cost = unit_cost * count

            # 企业版无限制
            is_unlimited = tenant_credits.monthly_quota == -1
            warning = None

            if not is_unlimited:
                # 检查余额（但不阻止，仅警告）
                if tenant_credits.current_balance < total_cost:
                    warning = f'积分余额不足，当前余额 {tenant_credits.current_balance}，需要 {total_cost}'
                    log.warning(f'Tenant {tenant_id} credits insufficient: {warning}')

                # 扣减积分（允许负数，初期不限制）
                tenant_credits.current_balance -= total_cost

            tenant_credits.total_used += total_cost

            # 记录使用日志
            usage_log = CreditsUsageLog(
                tenant_id=tenant_id,
                user_id=user_id,
                operation_type=operation_type,
                credits_cost=total_cost,
                description=description or f'{operation_type} x {count}',
                extra_data=extra_data,
            )
            db.add(usage_log)
            await db.flush()

            result = {
                'success': True,
                'credits_cost': total_cost,
                'remaining': tenant_credits.current_balance if not is_unlimited else -1,
            }
            if warning:
                result['warning'] = warning

            log.debug(
                f'Credits consumed: tenant={tenant_id}, operation={operation_type}, cost={total_cost}, remaining={tenant_credits.current_balance}'
            )
            return result

        except Exception as e:
            log.error(f'Failed to consume credits for tenant {tenant_id}: {e}')
            return {'success': False, 'credits_cost': 0, 'remaining': 0, 'error': str(e)}

    async def get_balance(self, db: AsyncSession, tenant_id: str) -> dict:
        """
        获取积分余额

        Returns:
            {
                "plan_type": 订阅类型,
                "monthly_quota": 月度额度,
                "current_balance": 当前余额,
                "total_used": 累计使用,
                "next_refresh_at": 下次刷新时间,
                "usage_percentage": 使用百分比
            }
        """
        tenant_credits = await self.get_or_create_tenant_credits(db, tenant_id)

        is_unlimited = tenant_credits.monthly_quota == -1
        usage_percentage = 0.0
        if not is_unlimited and tenant_credits.monthly_quota > 0:
            used_this_month = tenant_credits.monthly_quota - tenant_credits.current_balance
            usage_percentage = round(used_this_month / tenant_credits.monthly_quota * 100, 1)

        return {
            'plan_type': tenant_credits.plan_type,
            'monthly_quota': tenant_credits.monthly_quota,
            'current_balance': tenant_credits.current_balance,
            'total_used': tenant_credits.total_used,
            'next_refresh_at': tenant_credits.next_refresh_at.isoformat() if tenant_credits.next_refresh_at else None,
            'usage_percentage': usage_percentage,
            'is_unlimited': is_unlimited,
        }

    async def get_usage_history(
        self,
        db: AsyncSession,
        tenant_id: str,
        start_date: str | None = None,
        end_date: str | None = None,
        operation_type: str | None = None,
        limit: int = 100,
    ) -> list[dict]:
        """获取积分使用记录"""
        query = select(CreditsUsageLog).where(CreditsUsageLog.tenant_id == tenant_id)

        if start_date:
            query = query.where(CreditsUsageLog.created_at >= start_date)
        if end_date:
            query = query.where(CreditsUsageLog.created_at <= end_date)
        if operation_type:
            query = query.where(CreditsUsageLog.operation_type == operation_type)

        query = query.order_by(CreditsUsageLog.created_at.desc()).limit(limit)
        result = await db.execute(query)
        logs = result.scalars().all()

        return [
            {
                'id': log.id,
                'operation_type': log.operation_type,
                'credits_cost': log.credits_cost,
                'description': log.description,
                'created_at': log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ]

    async def get_usage_stats(self, db: AsyncSession, tenant_id: str) -> dict:
        """获取积分使用统计（按类型分组）"""
        query = (
            select(CreditsUsageLog.operation_type, func.sum(CreditsUsageLog.credits_cost).label('total'))
            .where(CreditsUsageLog.tenant_id == tenant_id)
            .group_by(CreditsUsageLog.operation_type)
        )
        result = await db.execute(query)
        rows = result.all()

        breakdown = {row.operation_type: int(row.total) for row in rows}
        return {'breakdown': breakdown, 'total': sum(breakdown.values())}

    async def _check_and_refresh_if_needed(self, db: AsyncSession, tenant_credits: TenantCredits) -> bool:
        """检查是否需要刷新积分，需要则刷新"""
        if not tenant_credits.next_refresh_at:
            return False

        now = timezone.now()
        if now < tenant_credits.next_refresh_at:
            return False

        # 需要刷新
        return await self._refresh_credits(db, tenant_credits)

    async def _refresh_credits(self, db: AsyncSession, tenant_credits: TenantCredits) -> bool:
        """刷新租户积分"""
        try:
            now = timezone.now()
            monthly_quota = await self.get_plan_quota(db, tenant_credits.plan_type)

            tenant_credits.monthly_quota = monthly_quota
            tenant_credits.current_balance = monthly_quota
            tenant_credits.last_refresh_at = now
            tenant_credits.next_refresh_at = now + timedelta(days=30)

            await db.flush()
            log.info(f'Refreshed credits for tenant {tenant_credits.tenant_id}: quota={monthly_quota}')
            return True

        except Exception as e:
            log.error(f'Failed to refresh credits for tenant {tenant_credits.tenant_id}: {e}')
            return False

    async def sync_subscription_plan(
        self, db: AsyncSession, tenant_id: str, plan_code: str, monthly_quota: int
    ) -> None:
        """同步订阅套餐变更"""
        tenant_credits = await self.get_or_create_tenant_credits(db, tenant_id)

        # Update plan and quota
        tenant_credits.plan_type = plan_code
        tenant_credits.monthly_quota = monthly_quota

        # Reset balance to new quota
        tenant_credits.current_balance = monthly_quota

        # Reset refresh timer
        now = timezone.now()
        tenant_credits.last_refresh_at = now
        tenant_credits.next_refresh_at = now + timedelta(days=30)

        await db.flush()
        log.info(f'Synced credits plan for tenant {tenant_id}: plan={plan_code}, quota={monthly_quota}')

    async def refresh_all_expired(self, db: AsyncSession) -> int:
        """刷新所有过期的租户积分（定时任务调用）"""
        now = timezone.now()
        query = select(TenantCredits).where(TenantCredits.next_refresh_at <= now)
        result = await db.execute(query)
        expired_list = result.scalars().all()

        refreshed_count = 0
        for tenant_credits in expired_list:
            if await self._refresh_credits(db, tenant_credits):
                refreshed_count += 1

        if refreshed_count > 0:
            log.info(f'Batch refreshed credits for {refreshed_count} tenants')

        return refreshed_count


# 单例
credits_service = CreditsService()
