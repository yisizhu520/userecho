"""更新现有角色的菜单权限

此脚本用于给现有角色分配新增的菜单权限。
执行方式: python scripts/update_role_menus.py
"""
import asyncio
import io
import sys
from pathlib import Path

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目根目录到 Python 路径
backend_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.model import Menu, Role, role_menu
from backend.database.db import async_db_session


async def update_role_menus():
    """更新角色菜单权限"""
    async with async_db_session.begin() as db:
        print('开始更新角色菜单权限...\n')
        
        # 定义需要全部权限的角色
        full_access_roles = ['PM', '老板']
        
        # 定义其他角色的特定菜单权限
        specific_access = {
            'CS': ['/app/feedback/list', '/app/customer', '/app/ai/discovery'],
            '开发': ['/app/topic/list', '/app/ai/discovery'],
        }
        
        # 获取所有业务菜单
        all_app_menus = await db.scalars(
            select(Menu).where(
                (Menu.path.like('/app/%')) | (Menu.path == '/app/userecho')
            )
        )
        all_app_menu_list = list(all_app_menus)
        menu_by_path = {menu.path: menu for menu in all_app_menu_list}
        
        print(f'找到 {len(all_app_menu_list)} 个业务菜单\n')
        
        # 更新全权限角色
        for role_name in full_access_roles:
            role = await db.scalar(
                select(Role).where(Role.name == role_name)
            )
            
            if not role:
                print(f'   ⚠️  角色 {role_name} 不存在，跳过')
                continue
            
            # 清除现有权限
            await db.execute(
                delete(role_menu).where(role_menu.c.role_id == role.id)
            )
            
            # 重新分配所有业务菜单
            assigned_count = 0
            for menu in all_app_menu_list:
                await db.execute(
                    role_menu.insert().values(role_id=role.id, menu_id=menu.id)
                )
                assigned_count += 1
            
            print(f'   [OK] {role_name}: 分配 {assigned_count} 个菜单权限')
        
        # 更新特定权限角色
        for role_name, menu_paths in specific_access.items():
            role = await db.scalar(
                select(Role).where(Role.name == role_name)
            )
            
            if not role:
                print(f'   ⚠️  角色 {role_name} 不存在，跳过')
                continue
            
            # 清除现有权限
            await db.execute(
                delete(role_menu).where(role_menu.c.role_id == role.id)
            )
            
            # 分配指定菜单 + 父菜单
            assigned_menus = []
            for menu_path in menu_paths:
                menu = menu_by_path.get(menu_path)
                if menu:
                    await db.execute(
                        role_menu.insert().values(role_id=role.id, menu_id=menu.id)
                    )
                    assigned_menus.append(menu.title)
            
            # 同时分配父菜单（目录）
            parent_menu = menu_by_path.get('/app/userecho')
            if parent_menu:
                await db.execute(
                    role_menu.insert().values(role_id=role.id, menu_id=parent_menu.id)
                )
            
            # 分配设置目录（如果该角色有设置权限）
            settings_menu = menu_by_path.get('/app/settings')
            if settings_menu and role_name in ['PM', '老板']:  # 只给 PM 和老板分配设置权限
                await db.execute(
                    role_menu.insert().values(role_id=role.id, menu_id=settings_menu.id)
                )
                
                # 分配设置子菜单
                clustering_menu = menu_by_path.get('/app/settings/clustering')
                if clustering_menu:
                    await db.execute(
                        role_menu.insert().values(role_id=role.id, menu_id=clustering_menu.id)
                    )
                    assigned_menus.append(clustering_menu.title)
            
            print(f'   [OK] {role_name}: 分配菜单 - {", ".join(assigned_menus)}')
        
        await db.commit()
        print('\n角色菜单权限更新完成！')


async def verify_role_menus():
    """验证角色菜单权限"""
    async with async_db_session() as db:
        print('\n验证角色菜单权限...\n')
        
        roles = await db.scalars(
            select(Role).where(Role.role_type == 'business')
        )
        
        for role in roles:
            # 获取角色的菜单
            role_menus = await db.execute(
                select(Menu)
                .join(role_menu, Menu.id == role_menu.c.menu_id)
                .where(role_menu.c.role_id == role.id)
                .order_by(Menu.sort)
            )
            menu_list = list(role_menus.scalars())
            
            print(f'[{role.name}] ({len(menu_list)} 个菜单):')
            for menu in menu_list:
                indent = '   ' if menu.parent_id else ''
                print(f'   {indent}- {menu.title} ({menu.path})')
            print()


async def main():
    """主函数"""
    await update_role_menus()
    await verify_role_menus()


if __name__ == '__main__':
    # 修复 Windows 控制台编码问题
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    print('=' * 60)
    print('更新角色菜单权限')
    print('=' * 60)
    print()
    
    try:
        asyncio.run(main())
        print('=' * 60)
        print('更新成功！请重新登录查看效果')
        print('=' * 60)
    except Exception as e:
        print(f'\n更新失败: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)

