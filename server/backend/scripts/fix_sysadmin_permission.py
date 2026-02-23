#!/usr/bin/env python3
"""
修复 sysadmin 权限脚本
将 sysadmin 用户设置为超级管理员
"""

import asyncio
import io
import sys

# Windows 平台 UTF-8 输出支持
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

sys.path.insert(0, ".")

from sqlalchemy import select

from backend.app.admin.model import User
from backend.database.db import async_db_session


async def fix_sysadmin_permission() -> None:
    """修复 sysadmin 权限"""
    async with async_db_session() as db:
        # 查找 sysadmin 用户
        stmt = select(User).where(User.username == "sysadmin")
        user = await db.scalar(stmt)

        if not user:
            print("❌ 未找到 sysadmin 用户")
            return

        print(f"👤 找到用户: {user.username} (ID: {user.id})")
        print(f"   当前状态: is_superuser={user.is_superuser}, is_staff={user.is_staff}")

        if user.is_superuser:
            print("✅ 用户已经是超级管理员，无需修改")
            return

        # 更新为超级管理员
        user.is_superuser = True
        # 确保也是 staff
        user.is_staff = True

        await db.commit()
        print("✅ 已将 sysadmin 设置为超级管理员 (is_superuser=True)")


async def main() -> int | None:
    """主函数"""
    print("=" * 80)
    print("🔧 修复 sysadmin 权限")
    print("=" * 80)
    print()

    try:
        await fix_sysadmin_permission()
        print()
        print("✅ 修复完成！")
        return 0
    except Exception as e:
        print()
        print(f"❌ 修复失败: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
