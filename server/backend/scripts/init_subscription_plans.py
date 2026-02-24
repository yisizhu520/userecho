#!/usr/bin/env python3
"""
初始化订阅套餐脚本
创建或更新系统默认的订阅套餐计划
"""

import asyncio
import io
import os
import sys
from pathlib import Path

# 【重要】确保使用 .env.demo 配置文件（必须在导入 backend 模块之前设置）
if "ENV_FILE" not in os.environ:
    backend_path = Path(__file__).resolve().parent.parent
    env_demo_path = backend_path / ".env.demo"
    if env_demo_path.exists():
        os.environ["ENV_FILE"] = str(env_demo_path)

# Windows 平台 UTF-8 输出支持
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

sys.path.insert(0, ".")

from sqlalchemy import select

from backend.app.userecho.model.subscription import PlanCode, SubscriptionPlan
from backend.database.db import async_db_session

PLANS = [
    {
        "code": PlanCode.STARTER,
        "name": "启航版",
        "description": "适合个人产品经理、独立开发者或初创团队验证想法",
        "price_monthly": 9900,  # 99元
        "price_yearly": 94800,  # 948元
        "seat_limit": 1,
        "feedback_limit": 1000,
        "ai_credits_monthly": 500,
        "features": {
            "clustering": True,
            "screenshot": True,
            "priority_score": True,
            "insight_report": "basic",
            "data_export": ["csv"],
            "customer_management": "basic",
            "private_deployment": False,
            "sso": False,
            "support": "community",
        },
        "sort_order": 1,
    },
    {
        "code": PlanCode.PRO,
        "name": "专业版",
        "description": "适合小型产品团队，提供完整的反馈管理和分析能力",
        "price_monthly": 19900,  # 199元
        "price_yearly": 190800,  # 1908元
        "seat_limit": 3,
        "feedback_limit": 10000,
        "ai_credits_monthly": 2000,
        "features": {
            "clustering": True,
            "screenshot": True,
            "priority_score": True,
            "insight_report": "full",
            "data_export": ["csv", "excel"],
            "customer_management": "full",
            "private_deployment": False,
            "sso": False,
            "support": "email",
        },
        "sort_order": 2,
    },
    {
        "code": PlanCode.FLAGSHIP,
        "name": "旗舰版",
        "description": "适合中型企业团队，更强大的协作和分析能力",
        "price_monthly": 59900,  # 599元
        "price_yearly": 574800,  # 5748元
        "seat_limit": 10,
        "feedback_limit": 100000,
        "ai_credits_monthly": 10000,
        "features": {
            "clustering": True,
            "screenshot": True,
            "priority_score": True,
            "insight_report": "full",
            "data_export": ["csv", "excel", "api"],
            "customer_management": "advanced",
            "private_deployment": False,
            "sso": False,
            "support": "priority",
        },
        "sort_order": 3,
    },
    {
        "code": PlanCode.ENTERPRISE,
        "name": "定制版",
        "description": "适合大型企业，提供私有化部署和专属服务",
        "price_monthly": 0,
        "price_yearly": 0,
        "seat_limit": -1,  # 无限
        "feedback_limit": -1,  # 无限
        "ai_credits_monthly": -1,  # 无限
        "features": {
            "clustering": True,
            "screenshot": True,
            "priority_score": True,
            "insight_report": "advanced",
            "data_export": ["csv", "excel", "api", "custom"],
            "customer_management": "advanced",
            "private_deployment": True,
            "sso": True,
            "support": "dedicated",
        },
        "sort_order": 4,
    },
]


async def init_plans() -> None:
    """初始化订阅套餐"""
    print("=" * 80)
    print("📦 初始化订阅套餐")
    print("=" * 80)
    print()

    async with async_db_session() as db:
        for plan_data in PLANS:
            # Check if plan exists (by code)
            stmt = select(SubscriptionPlan).where(SubscriptionPlan.code == plan_data["code"])
            result = await db.execute(stmt)
            existing_plan = result.scalar_one_or_none()

            if existing_plan:
                # Update existing plan
                print(f"🔄 更新套餐: {plan_data['name']} ({plan_data['code']})")
                for key, value in plan_data.items():
                    setattr(existing_plan, key, value)
            else:
                # Create new plan
                print(f"✨ 创建套餐: {plan_data['name']} ({plan_data['code']})")
                new_plan = SubscriptionPlan(**plan_data)
                db.add(new_plan)

        await db.commit()
        print()
        print("✅ 订阅套餐初始化完成！")


if __name__ == "__main__":
    exit_code = 0
    try:
        asyncio.run(init_plans())
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        import traceback

        traceback.print_exc()
        exit_code = 1

    sys.exit(exit_code)
