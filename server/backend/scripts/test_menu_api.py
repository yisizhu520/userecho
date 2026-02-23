#!/usr/bin/env python3
"""
测试菜单API返回的实际数据
模拟前端调用 /api/v1/sys/menus/sidebar
"""

import asyncio
import io
import json
import sys

# Windows 平台 UTF-8 输出支持
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

sys.path.insert(0, ".")


from backend.app.admin.crud.crud_user import user_dao
from backend.app.admin.service.menu_service import menu_service
from backend.database.db import async_db_session


class FakeRequest:
    """模拟 FastAPI Request 对象"""

    def __init__(self, user):
        self.user = user


async def test_menu_api() -> None:
    """测试菜单API"""
    async with async_db_session() as db:
        # 获取 sysadmin 用户
        user = await user_dao.get_join(db, username="sysadmin")

        if not user:
            print("❌ 未找到 sysadmin 用户")
            return

        print(f"👤 测试用户: {user.username}")
        print(f"   is_superuser: {user.is_superuser}")
        print(f"   is_staff: {user.is_staff}")
        print()

        # 创建假的 request 对象
        request = FakeRequest(user)

        # 调用菜单服务
        print("📡 调用 menu_service.get_sidebar()...")
        menus = await menu_service.get_sidebar(db=db, request=request)

        print(f"\n✅ 返回 {len(menus)} 个菜单项")
        print("=" * 80)

        # 打印详细数据（类似前端收到的数据）
        print(json.dumps(menus, indent=2, ensure_ascii=False))


async def main() -> int | None:
    """主函数"""
    print("=" * 80)
    print("🔍 测试菜单 API 返回数据")
    print("=" * 80)
    print()

    try:
        await test_menu_api()
        return 0
    except Exception as e:
        print()
        print(f"❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
