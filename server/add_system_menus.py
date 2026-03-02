#!/usr/bin/env python3
"""
添加缺失的系统菜单：任务调度、日志管理、系统监控
"""

import asyncio
import io
import sys

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

sys.path.insert(0, ".")

from sqlalchemy import select, text

from backend.app.admin.model import Menu
from backend.database.db import async_db_session


async def add_missing_system_menus():
    """添加缺失的系统菜单"""
    async with async_db_session() as db:
        print("=" * 80)
        print("🔧 添加缺失的系统菜单")
        print("=" * 80)
        print()

        # 获取 System 菜单的 ID
        system_menu = await db.scalar(select(Menu).where(Menu.name == "System"))
        if not system_menu:
            print("❌ 未找到 System 父菜单！")
            return

        system_menu_id = system_menu.id
        print(f"✅ 找到 System 父菜单 (ID: {system_menu_id})")
        print()

        # 需要添加的菜单定义
        menus_to_add = [
            # 1. 任务调度（Celery）
            {
                "title": "任务调度",
                "name": "SysTask",
                "path": "/system/task",
                "sort": 20,
                "icon": "ant-design:schedule-outlined",
                "type": 1,  # 菜单
                "component": "/src/views/system/task/index",
                "perms": None,
                "status": 1,
                "display": 1,
                "cache": 1,
                "link": "",
                "remark": "Celery 任务调度管理",
            },
            # 2. 日志管理（目录）
            {
                "title": "日志管理",
                "name": "SysLog",
                "path": "/system/log",
                "sort": 30,
                "icon": "ant-design:file-text-outlined",
                "type": 0,  # 目录
                "component": "",
                "perms": None,
                "status": 1,
                "display": 1,
                "cache": 1,
                "link": "",
                "remark": "系统日志管理",
            },
            # 3. 系统监控（目录）
            {
                "title": "系统监控",
                "name": "SysMonitor",
                "path": "/system/monitor",
                "sort": 40,
                "icon": "ant-design:dashboard-outlined",
                "type": 0,  # 目录
                "component": "",
                "perms": None,
                "status": 1,
                "display": 1,
                "cache": 1,
                "link": "",
                "remark": "系统监控管理",
            },
        ]

        added_count = 0

        for menu_def in menus_to_add:
            # 检查菜单是否已存在
            existing = await db.scalar(select(Menu).where(Menu.name == menu_def["name"]))

            if existing:
                print(f"  ⏭️  {menu_def['title']} 已存在，跳过")
                continue

            # 添加菜单
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
                {**menu_def, "parent_id": system_menu_id},
            )
            print(f"  ✅ 已添加: {menu_def['title']} ({menu_def['name']})")
            added_count += 1

        # 现在添加"日志管理"下的子菜单
        log_parent = await db.scalar(select(Menu).where(Menu.name == "SysLog"))
        if log_parent:
            log_submenus = [
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
                },
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
                },
            ]

            for submenu_def in log_submenus:
                existing = await db.scalar(select(Menu).where(Menu.name == submenu_def["name"]))
                if existing:
                    print(f"  ⏭️  {submenu_def['title']} 已存在，跳过")
                    continue

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
                    {**submenu_def, "parent_id": log_parent.id},
                )
                print(f"  ✅ 已添加: {submenu_def['title']} ({submenu_def['name']})")
                added_count += 1

        # 添加"系统监控"下的子菜单
        monitor_parent = await db.scalar(select(Menu).where(Menu.name == "SysMonitor"))
        if monitor_parent:
            monitor_submenus = [
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
                },
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
                },
            ]

            for submenu_def in monitor_submenus:
                existing = await db.scalar(select(Menu).where(Menu.name == submenu_def["name"]))
                if existing:
                    print(f"  ⏭️  {submenu_def['title']} 已存在，跳过")
                    continue

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
                    {**submenu_def, "parent_id": monitor_parent.id},
                )
                print(f"  ✅ 已添加: {submenu_def['title']} ({submenu_def['name']})")
                added_count += 1

        # 提交事务
        await db.commit()

        print()
        print("=" * 80)
        if added_count > 0:
            print(f"✅ 成功添加 {added_count} 个菜单！")
        else:
            print("✅ 所有菜单已存在，无需添加")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(add_missing_system_menus())
