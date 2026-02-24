#!/usr/bin/env python3
"""
初始化默认租户脚本
在 fba init 之后立即执行，创建 default-tenant 租户记录
并在 demo 模式下分配专业版订阅（有效期一年）
"""

import asyncio
import io
import os
import sys
from datetime import timedelta

# Windows 平台 UTF-8 输出支持
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

sys.path.insert(0, ".")

from sqlalchemy import select

from backend.app.userecho.model import Board, Tenant
from backend.app.userecho.model.subscription import (
    PlanCode,
    SubscriptionAction,
    SubscriptionHistory,
    SubscriptionPlan,
    SubscriptionSource,
    SubscriptionStatus,
    TenantSubscription,
)
from backend.database.db import async_db_session
from backend.utils.timezone import timezone


async def create_default_tenant() -> None:
    """创建默认租户和默认看板"""
    async with async_db_session() as db:
        # 检查默认租户是否已存在
        existing = await db.scalar(select(Tenant).where(Tenant.id == "default-tenant"))

        if existing:
            print("✅ 默认租户已存在")
        else:
            # 创建默认租户
            default_tenant = Tenant(
                id="default-tenant",
                name="默认租户",
                slug="default",  # 新增 slug 字段
                status="active",
                created_time=timezone.now(),
            )

            db.add(default_tenant)
            await db.flush()

            print("✅ 默认租户创建成功")
            print(f"   租户ID: {default_tenant.id}")
            print(f"   租户名称: {default_tenant.name}")
            print(f"   slug: {default_tenant.slug}")
            print(f"   状态: {default_tenant.status}")

        # 检查默认看板是否已存在
        existing_board = await db.scalar(select(Board).where(Board.id == "default-board"))

        if existing_board:
            print("✅ 默认看板已存在")
        else:
            # 创建默认看板
            default_board = Board(
                id="default-board",
                tenant_id="default-tenant",
                name="默认看板",
                url_name="default",
                description="默认反馈看板，用于收集所有产品反馈",
                access_mode="private",
                category="general",
                sort_order=0,
                created_time=timezone.now(),
            )

            db.add(default_board)
            print("✅ 默认看板创建成功")
            print(f"   看板ID: {default_board.id}")
            print(f"   看板名称: {default_board.name}")
            print(f"   URL: {default_board.url_name}")

        await db.commit()


async def create_demo_subscription() -> None:
    """为默认租户创建专业版订阅（仅在 demo 模式下）"""
    # 检查是否是 demo 模式
    is_demo = os.getenv("DEMO_MODE", "false").lower() == "true"
    env_file = os.getenv("ENV_FILE", "")

    if not is_demo and ".env.demo" not in env_file:
        print("⏭️  非 demo 模式，跳过订阅分配")
        return

    async with async_db_session() as db:
        # 检查默认租户是否已有订阅
        existing_sub = await db.scalar(
            select(TenantSubscription).where(TenantSubscription.tenant_id == "default-tenant")
        )

        if existing_sub:
            print("✅ 默认租户订阅已存在")
            # 获取套餐信息显示
            plan = await db.get(SubscriptionPlan, existing_sub.plan_id)
            if plan:
                print(f"   套餐: {plan.name} ({plan.code})")
                print(f"   状态: {existing_sub.status}")
                print(f"   到期时间: {existing_sub.expires_at}")
            return

        # 获取专业版套餐
        pro_plan = await db.scalar(select(SubscriptionPlan).where(SubscriptionPlan.code == PlanCode.PRO))

        if not pro_plan:
            print("⚠️  专业版套餐不存在，请先运行 init_subscription_plans.py")
            return

        # 创建专业版订阅，有效期一年
        now = timezone.now()
        expires_at = now + timedelta(days=365)

        subscription = TenantSubscription(
            tenant_id="default-tenant",
            plan_id=pro_plan.id,
            status=SubscriptionStatus.ACTIVE,
            started_at=now,
            expires_at=expires_at,
            source=SubscriptionSource.MANUAL,
            notes="Demo 环境自动分配专业版订阅",
        )

        db.add(subscription)
        await db.flush()

        # 记录订阅历史
        history = SubscriptionHistory(
            tenant_id="default-tenant",
            subscription_id=subscription.id,
            action=SubscriptionAction.CREATED,
            old_plan_code=None,
            new_plan_code=pro_plan.code,
            reason="Demo environment: auto-assign professional plan for 1 year",
        )
        db.add(history)

        await db.commit()

        print("✅ 专业版订阅创建成功")
        print(f"   套餐: {pro_plan.name} ({pro_plan.code})")
        print(f"   状态: {subscription.status}")
        print(f"   开始时间: {subscription.started_at}")
        print(f"   到期时间: {subscription.expires_at}")
        print("   有效期: 365 天（一年）")


async def main() -> int | None:
    """主函数"""
    print("=" * 80)
    print("🏢 初始化默认租户")
    print("=" * 80)
    print()

    try:
        await create_default_tenant()
        print()

        # Demo 模式下分配专业版订阅
        print("=" * 80)
        print("📦 检查订阅计划")
        print("=" * 80)
        print()
        await create_demo_subscription()

        print()
        print("✅ 初始化完成！")
        return 0
    except Exception as e:
        print()
        print(f"❌ 初始化失败: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
