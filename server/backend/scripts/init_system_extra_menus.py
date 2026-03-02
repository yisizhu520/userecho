#!/usr/bin/env python3
"""
添加额外的系统管理菜单
包括：订阅管理、积分管理、邀请管理、任务调度、日志管理、系统监控
这些菜单是后来添加的，不在 fba init 的基础数据中
"""

import asyncio
import io
import sys

# Windows 平台 UTF-8 输出支持
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

sys.path.insert(0, ".")

from sqlalchemy import select, text

from backend.app.admin.model import Menu
from backend.database.db import async_db_session


async def add_extra_system_menus() -> None:
    """添加额外的系统管理菜单"""
    async with async_db_session() as db:
        # 获取 System 菜单的 ID
        stmt = select(Menu).where(Menu.name == "System")
        system_menu = await db.scalar(stmt)

        if not system_menu:
            print("❌ 未找到 System 菜单，跳过添加额外菜单")
            return

        system_menu_id = system_menu.id
        print(f"✅ 找到 System 菜单 (ID: {system_menu_id})")

        menus_added = 0

        # 1. 添加"订阅管理"（sort=10）
        existing_subscription = await db.scalar(select(Menu).where(Menu.name == "SysSubscription"))
        if not existing_subscription:
            await db.execute(
                text(
                    """
                INSERT INTO sys_menu (
                    title, name, path, sort, icon, type, component,
                    perms, status, display, cache, link, remark, parent_id, created_time
                )
                VALUES (
                    :title, :name, :path, :sort, :icon, :type, :component,
                    :perms, :status, :display, :cache, :link, :remark, :parent_id, NOW()
                )
            """
                ),
                {
                    "title": "订阅管理",
                    "name": "SysSubscription",
                    "path": "/system/subscription",
                    "sort": 10,
                    "icon": "lucide:credit-card",
                    "type": 1,
                    "component": "/src/views/system/subscription/index",
                    "perms": None,
                    "status": 1,
                    "display": 1,
                    "cache": 1,
                    "link": "",
                    "remark": "系统订阅套餐管理",
                    "parent_id": system_menu_id,
                },
            )
            print("  ✅ 已添加: 订阅管理")
            menus_added += 1
        else:
            print("  ⏭️  订阅管理菜单已存在，跳过")

        # 2. 添加"积分管理"（sort=11）
        existing_credits = await db.scalar(select(Menu).where(Menu.name == "SysCredits"))
        if not existing_credits:
            await db.execute(
                text(
                    """
                INSERT INTO sys_menu (
                    title, name, path, sort, icon, type, component,
                    perms, status, display, cache, link, remark, parent_id, created_time
                )
                VALUES (
                    :title, :name, :path, :sort, :icon, :type, :component,
                    :perms, :status, :display, :cache, :link, :remark, :parent_id, NOW()
                )
            """
                ),
                {
                    "title": "积分管理",
                    "name": "SysCredits",
                    "path": "/system/credits",
                    "sort": 11,
                    "icon": "carbon:user-certification",
                    "type": 1,
                    "component": "/src/views/system/credits/index",
                    "perms": None,
                    "status": 1,
                    "display": 1,
                    "cache": 1,
                    "link": "",
                    "remark": "系统积分配置管理",
                    "parent_id": system_menu_id,
                },
            )
            print("  ✅ 已添加: 积分管理")
            menus_added += 1
        else:
            print("  ⏭️  积分管理菜单已存在，跳过")

        # 3. 添加"邀请管理"（sort=12）
        existing_invitation = await db.scalar(select(Menu).where(Menu.name == "SysInvitation"))
        if not existing_invitation:
            await db.execute(
                text(
                    """
                INSERT INTO sys_menu (
                    title, name, path, sort, icon, type, component,
                    perms, status, display, cache, link, remark, parent_id, created_time
                )
                VALUES (
                    :title, :name, :path, :sort, :icon, :type, :component,
                    :perms, :status, :display, :cache, :link, :remark, :parent_id, NOW()
                )
            """
                ),
                {
                    "title": "邀请管理",
                    "name": "SysInvitation",
                    "path": "/system/invitation",
                    "sort": 12,
                    "icon": "lucide:mail-open",
                    "type": 1,
                    "component": "/src/views/system/invitation/index",
                    "perms": None,
                    "status": 1,
                    "display": 1,
                    "cache": 1,
                    "link": "",
                    "remark": "试用邀请管理",
                    "parent_id": system_menu_id,
                },
            )
            print("  ✅ 已添加: 邀请管理")
            menus_added += 1
        else:
            print("  ⏭️  邀请管理菜单已存在，跳过")

        # 4. 添加"任务调度"（sort=20）
        existing_task = await db.scalar(select(Menu).where(Menu.name == "SysTask"))
        if not existing_task:
            await db.execute(
                text(
                    """
                INSERT INTO sys_menu (
                    title, name, path, sort, icon, type, component,
                    perms, status, display, cache, link, remark, parent_id, created_time
                )
                VALUES (
                    :title, :name, :path, :sort, :icon, :type, :component,
                    :perms, :status, :display, :cache, :link, :remark, :parent_id, NOW()
                )
            """
                ),
                {
                    "title": "任务调度",
                    "name": "SysTask",
                    "path": "/system/task",
                    "sort": 20,
                    "icon": "ant-design:schedule-outlined",
                    "type": 1,
                    "component": "/src/views/system/task/index",
                    "perms": None,
                    "status": 1,
                    "display": 1,
                    "cache": 1,
                    "link": "",
                    "remark": "Celery 任务调度管理",
                    "parent_id": system_menu_id,
                },
            )
            print("  ✅ 已添加: 任务调度")
            menus_added += 1
        else:
            print("  ⏭️  任务调度菜单已存在，跳过")

        # 5. 添加"日志管理"目录（sort=30）
        existing_log = await db.scalar(select(Menu).where(Menu.name == "SysLog"))
        if not existing_log:
            await db.execute(
                text(
                    """
                INSERT INTO sys_menu (
                    title, name, path, sort, icon, type, component,
                    perms, status, display, cache, link, remark, parent_id, created_time
                )
                VALUES (
                    :title, :name, :path, :sort, :icon, :type, :component,
                    :perms, :status, :display, :cache, :link, :remark, :parent_id, NOW()
                )
            """
                ),
                {
                    "title": "日志管理",
                    "name": "SysLog",
                    "path": "/system/log",
                    "sort": 30,
                    "icon": "ant-design:file-text-outlined",
                    "type": 0,
                    "component": "",
                    "perms": None,
                    "status": 1,
                    "display": 1,
                    "cache": 1,
                    "link": "",
                    "remark": "系统日志管理",
                    "parent_id": system_menu_id,
                },
            )
            print("  ✅ 已添加: 日志管理（目录）")
            menus_added += 1

            # 5.1 添加"操作日志"子菜单
            log_parent = await db.scalar(select(Menu).where(Menu.name == "SysLog"))
            if log_parent:
                await db.execute(
                    text(
                        """
                    INSERT INTO sys_menu (
                        title, name, path, sort, icon, type, component,
                        perms, status, display, cache, link, remark, parent_id, created_time
                    )
                    VALUES (
                        :title, :name, :path, :sort, :icon, :type, :component,
                        :perms, :status, :display, :cache, :link, :remark, :parent_id, NOW()
                    )
                """
                    ),
                    {
                        "title": "操作日志",
                        "name": "SysOperaLog",
                        "path": "/system/log/opera",
                        "sort": 1,
                        "icon": "ant-design:profile-outlined",
                        "type": 1,
                        "component": "/src/views/system/log/opera/index",
                        "perms": None,
                        "status": 1,
                        "display": 1,
                        "cache": 1,
                        "link": "",
                        "remark": "系统操作日志",
                        "parent_id": log_parent.id,
                    },
                )
                print("    ✅ 已添加: 操作日志")
                menus_added += 1

                # 5.2 添加"登录日志"子菜单
                await db.execute(
                    text(
                        """
                    INSERT INTO sys_menu (
                        title, name, path, sort, icon, type, component,
                        perms, status, display, cache, link, remark, parent_id, created_time
                    )
                    VALUES (
                        :title, :name, :path, :sort, :icon, :type, :component,
                        :perms, :status, :display, :cache, :link, :remark, :parent_id, NOW()
                    )
                """
                    ),
                    {
                        "title": "登录日志",
                        "name": "SysLoginLog",
                        "path": "/system/log/login",
                        "sort": 2,
                        "icon": "ant-design:login-outlined",
                        "type": 1,
                        "component": "/src/views/system/log/login/index",
                        "perms": None,
                        "status": 1,
                        "display": 1,
                        "cache": 1,
                        "link": "",
                        "remark": "用户登录日志",
                        "parent_id": log_parent.id,
                    },
                )
                print("    ✅ 已添加: 登录日志")
                menus_added += 1
        else:
            print("  ⏭️  日志管理菜单已存在，跳过")

        # 6. 添加"系统监控"目录（sort=40）
        existing_monitor = await db.scalar(select(Menu).where(Menu.name == "SysMonitor"))
        if not existing_monitor:
            await db.execute(
                text(
                    """
                INSERT INTO sys_menu (
                    title, name, path, sort, icon, type, component,
                    perms, status, display, cache, link, remark, parent_id, created_time
                )
                VALUES (
                    :title, :name, :path, :sort, :icon, :type, :component,
                    :perms, :status, :display, :cache, :link, :remark, :parent_id, NOW()
                )
            """
                ),
                {
                    "title": "系统监控",
                    "name": "SysMonitor",
                    "path": "/system/monitor",
                    "sort": 40,
                    "icon": "ant-design:dashboard-outlined",
                    "type": 0,
                    "component": "",
                    "perms": None,
                    "status": 1,
                    "display": 1,
                    "cache": 1,
                    "link": "",
                    "remark": "系统监控管理",
                    "parent_id": system_menu_id,
                },
            )
            print("  ✅ 已添加: 系统监控（目录）")
            menus_added += 1

            # 6.1 添加"服务监控"子菜单
            monitor_parent = await db.scalar(select(Menu).where(Menu.name == "SysMonitor"))
            if monitor_parent:
                await db.execute(
                    text(
                        """
                    INSERT INTO sys_menu (
                        title, name, path, sort, icon, type, component,
                        perms, status, display, cache, link, remark, parent_id, created_time
                    )
                    VALUES (
                        :title, :name, :path, :sort, :icon, :type, :component,
                        :perms, :status, :display, :cache, :link, :remark, :parent_id, NOW()
                    )
                """
                    ),
                    {
                        "title": "服务监控",
                        "name": "SysMonitorServer",
                        "path": "/system/monitor/server",
                        "sort": 1,
                        "icon": "ant-design:cloud-server-outlined",
                        "type": 1,
                        "component": "/src/views/system/monitor/server/index",
                        "perms": None,
                        "status": 1,
                        "display": 1,
                        "cache": 1,
                        "link": "",
                        "remark": "服务器监控",
                        "parent_id": monitor_parent.id,
                    },
                )
                print("    ✅ 已添加: 服务监控")
                menus_added += 1

                # 6.2 添加"Redis监控"子菜单
                await db.execute(
                    text(
                        """
                    INSERT INTO sys_menu (
                        title, name, path, sort, icon, type, component,
                        perms, status, display, cache, link, remark, parent_id, created_time
                    )
                    VALUES (
                        :title, :name, :path, :sort, :icon, :type, :component,
                        :perms, :status, :display, :cache, :link, :remark, :parent_id, NOW()
                    )
                """
                    ),
                    {
                        "title": "Redis监控",
                        "name": "SysMonitorRedis",
                        "path": "/system/monitor/redis",
                        "sort": 2,
                        "icon": "simple-icons:redis",
                        "type": 1,
                        "component": "/src/views/system/monitor/redis/index",
                        "perms": None,
                        "status": 1,
                        "display": 1,
                        "cache": 1,
                        "link": "",
                        "remark": "Redis 监控",
                        "parent_id": monitor_parent.id,
                    },
                )
                print("    ✅ 已添加: Redis监控")
                menus_added += 1
        else:
            print("  ⏭️  系统监控菜单已存在，跳过")

        # 提交事务
        if menus_added > 0:
            await db.commit()
            print(f"\n✅ 成功添加 {menus_added} 个额外系统菜单")
        else:
            print("\n✅ 所有额外系统菜单已存在，无需添加")


async def main() -> int:
    """主函数"""
    print("=" * 80)
    print("🔧 添加额外系统管理菜单")
    print("=" * 80)
    print()

    try:
        await add_extra_system_menus()
        print()
        print("✅ 完成！")
        return 0
    except Exception as e:
        print()
        print(f"❌ 失败: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
