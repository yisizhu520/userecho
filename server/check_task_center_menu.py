#!/usr/bin/env python3
"""
检查任务中心菜单是否正确添加
"""

import asyncio
import io
import sys

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

sys.path.insert(0, ".")

from sqlalchemy import select

from backend.app.admin.model import Menu
from backend.database.db import async_db_session


async def check_task_center_menu():
    """检查任务中心菜单"""
    async with async_db_session() as db:
        print("=" * 80)
        print("🔍 检查任务中心菜单")
        print("=" * 80)
        print()

        # 查找任务中心菜单
        task_menu = await db.scalar(
            select(Menu).where(Menu.name == "TaskCenter")
        )

        if not task_menu:
            print("❌ 未找到任务中心菜单！")
            return

        print("✅ 找到任务中心菜单：")
        print(f"  ID: {task_menu.id}")
        print(f"  标题: {task_menu.title}")
        print(f"  名称: {task_menu.name}")
        print(f"  路径: {task_menu.path}")
        print(f"  组件: {task_menu.component}")
        print(f"  父菜单ID: {task_menu.parent_id}")
        print(f"  排序: {task_menu.sort}")
        print(f"  图标: {task_menu.icon}")
        print(f"  类型: {task_menu.type} (0=目录, 1=菜单, 2=按钮)")
        print(f"  状态: {task_menu.status} (0=禁用, 1=启用)")
        print(f"  显示: {task_menu.display} (0=隐藏, 1=显示)")
        print(f"  权限: {task_menu.perms}")
        print()

        # 查找父菜单
        if task_menu.parent_id:
            parent = await db.scalar(
                select(Menu).where(Menu.id == task_menu.parent_id)
            )
            if parent:
                print(f"父菜单信息：")
                print(f"  ID: {parent.id}")
                print(f"  标题: {parent.title}")
                print(f"  名称: {parent.name}")
                print(f"  路径: {parent.path}")
                print(f"  状态: {parent.status}")
                print()

        # 检查可能的问题
        issues = []
        
        if task_menu.status != 1:
            issues.append(f"⚠️  菜单状态为 {task_menu.status}，应该是 1（启用）")
        
        if task_menu.display != 1:
            issues.append(f"⚠️  菜单显示为 {task_menu.display}，应该是 1（显示）")
        
        if task_menu.type != 1:
            issues.append(f"⚠️  菜单类型为 {task_menu.type}，应该是 1（菜单）")
        
        if not task_menu.path.startswith("/"):
            issues.append(f"⚠️  路径格式可能不对: {task_menu.path}")
        
        if issues:
            print("发现的问题：")
            for issue in issues:
                print(f"  {issue}")
            print()
        else:
            print("✅ 菜单配置看起来正确")
            print()

        # 列出同级所有菜单
        if task_menu.parent_id:
            print(f"同级菜单（父菜单ID={task_menu.parent_id}）：")
            siblings = await db.scalars(
                select(Menu)
                .where(Menu.parent_id == task_menu.parent_id)
                .order_by(Menu.sort)
            )
            for sibling in siblings:
                status_icon = "✅" if sibling.status == 1 else "❌"
                display_icon = "👁️" if sibling.display == 1 else "🙈"
                current = "👉" if sibling.id == task_menu.id else "  "
                print(f"  {current} {status_icon}{display_icon} [{sibling.sort:2d}] {sibling.title} (path={sibling.path})")
        
        print()
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(check_task_center_menu())
