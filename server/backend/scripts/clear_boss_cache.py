#!/usr/bin/env python3
"""清除 boss 用户的 Redis 缓存"""

import asyncio
import io
import sys

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

sys.path.insert(0, ".")

from sqlalchemy import select

from backend.app.admin.model import User
from backend.core.conf import settings
from backend.database.db import async_db_session
from backend.database.redis import redis_client


async def clear_boss_cache() -> None:
    """清除 boss 用户的 Redis 缓存"""
    print("=" * 80)
    print("🧹 清除 boss 用户的 Redis 缓存")
    print("=" * 80)
    print()

    async with async_db_session() as db:
        # 获取 boss 用户 ID
        boss = await db.scalar(select(User).where(User.username == "boss"))

        if not boss:
            print("❌ boss 用户不存在")
            return

        user_id = boss.id
        print(f"✅ boss 用户 ID: {user_id}")
        print()

    # 清除用户信息缓存
    cache_key = f"{settings.JWT_USER_REDIS_PREFIX}:{user_id}"
    print(f"🔍 检查缓存键: {cache_key}")

    cache_exists = await redis_client.exists(cache_key)
    if cache_exists:
        await redis_client.delete(cache_key)
        print(f"✅ 已删除缓存: {cache_key}")
    else:
        print(f"ℹ️  缓存不存在: {cache_key}")

    print()
    print("=" * 80)
    print("✅ 缓存清理完成！")
    print("=" * 80)
    print()
    print("💡 下次请求时，系统会从数据库重新加载用户信息")
    print("   包括最新的 tenant_id")
    print()


if __name__ == "__main__":
    asyncio.run(clear_boss_cache())
