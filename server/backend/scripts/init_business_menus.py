"""初始化业务菜单和角色

此脚本用于创建 UserEcho 业务功能的菜单和角色。
执行方式: python scripts/init_business_menus.py
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
backend_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.model import Menu, Role, role_menu
from backend.database.db import async_db_session


async def init_business_menus():
    """初始化业务菜单和角色"""
    async with async_db_session.begin() as db:
        print('📋 开始初始化业务菜单和角色...')
        
        # ========== 1. 创建反馈管理目录 ==========
        print('\n1️⃣  检查反馈管理目录...')
        userecho_menu = await db.scalar(
            select(Menu).where(Menu.path == '/app/userecho')
        )
        
        if not userecho_menu:
            userecho_menu = Menu(
                title='反馈管理',
                name='UserEcho',
                path='/app/userecho',
                icon='lucide:messages-square',
                type=0,  # 目录
                sort=100,
                status=1,
                display=1,
            )
            db.add(userecho_menu)
            await db.flush()
            print('   ✅ 创建反馈管理目录')
        else:
            print('   ⏭️  反馈管理目录已存在，跳过')
        
        # ========== 2. 创建子菜单 ==========
        print('\n2️⃣  创建子菜单...')
        sub_menus = [
            {
                'title': '反馈列表',
                'name': 'FeedbackList',
                'path': '/app/feedback/list',
                'component': '/userecho/feedback/list',
                'icon': 'lucide:inbox',
                'perms': 'app:feedback:view',
                'sort': 1,
            },
            {
                'title': 'AI 发现中心',
                'name': 'AIDiscovery',
                'path': '/app/ai/discovery',
                'component': '/userecho/discovery/index',
                'icon': 'lucide:sparkles',
                'perms': 'app:ai:view',
                'sort': 2,
            },
            {
                'title': '导入反馈',
                'name': 'FeedbackImport',
                'path': '/app/feedback/import',
                'component': '/userecho/feedback/import',
                'icon': 'lucide:upload',
                'perms': 'app:feedback:import',
                'sort': 3,
            },
            {
                'title': '需求主题',
                'name': 'TopicList',
                'path': '/app/topic/list',
                'component': '/userecho/topic/list',
                'icon': 'lucide:lightbulb',
                'perms': 'app:topic:view',
                'sort': 4,
            },
            {
                'title': '客户管理',
                'name': 'CustomerManage',
                'path': '/app/customer',
                'component': '/userecho/customer/index',
                'icon': 'lucide:users',
                'perms': 'app:customer:view',
                'sort': 5,
            },
        ]
        
        created_menus = []
        updated_menus = []
        for menu_data in sub_menus:
            existing = await db.scalar(
                select(Menu).where(Menu.path == menu_data['path'])
            )
            if not existing:
                menu = Menu(
                    **menu_data, 
                    parent_id=userecho_menu.id, 
                    type=1,  # 菜单
                    status=1, 
                    display=1
                )
                db.add(menu)
                created_menus.append(menu_data['title'])
            else:
                # 更新已存在的菜单（修复旧的 component 路径）
                existing.component = menu_data['component']
                existing.icon = menu_data['icon']
                existing.sort = menu_data['sort']
                existing.perms = menu_data['perms']
                updated_menus.append(menu_data['title'])
        
        if created_menus or updated_menus:
            await db.flush()
            if created_menus:
                print(f'   ✅ 创建子菜单: {", ".join(created_menus)}')
            if updated_menus:
                print(f'   🔄 更新子菜单: {", ".join(updated_menus)}')
        else:
            print('   ⏭️  所有子菜单已是最新，跳过')
        
        # ========== 3. 创建设置目录和子菜单 ==========
        print('\n3️⃣  创建设置目录和子菜单...')
        settings_menu = await db.scalar(
            select(Menu).where(Menu.path == '/app/settings')
        )
        
        if not settings_menu:
            settings_menu = Menu(
                title='设置',
                name='Settings',
                path='/app/settings',
                icon='lucide:settings',
                type=0,  # 目录
                sort=6,
                status=1,
                display=1,
                parent_id=userecho_menu.id,
            )
            db.add(settings_menu)
            await db.flush()
            print('   ✅ 创建设置目录')
        else:
            print('   ⏭️  设置目录已存在，跳过')
        
        # 设置子菜单
        settings_sub_menus = [
            {
                'title': '聚类策略',
                'name': 'ClusteringConfig',
                'path': '/app/settings/clustering',
                'component': '/userecho/settings/clustering-config',
                'icon': 'lucide:layers',
                'perms': 'app:settings:clustering',
                'sort': 1,
            },
        ]
        
        created_settings_menus = []
        updated_settings_menus = []
        for menu_data in settings_sub_menus:
            existing = await db.scalar(
                select(Menu).where(Menu.path == menu_data['path'])
            )
            if not existing:
                menu = Menu(
                    **menu_data,
                    parent_id=settings_menu.id,
                    type=1,  # 菜单
                    status=1,
                    display=1
                )
                db.add(menu)
                created_settings_menus.append(menu_data['title'])
            else:
                # 更新已存在的菜单
                existing.component = menu_data['component']
                existing.icon = menu_data['icon']
                existing.sort = menu_data['sort']
                existing.perms = menu_data['perms']
                existing.parent_id = settings_menu.id
                updated_settings_menus.append(menu_data['title'])
        
        if created_settings_menus or updated_settings_menus:
            await db.flush()
            if created_settings_menus:
                print(f'   ✅ 创建设置子菜单: {", ".join(created_settings_menus)}')
            if updated_settings_menus:
                print(f'   🔄 更新设置子菜单: {", ".join(updated_settings_menus)}')
        else:
            print('   ⏭️  所有设置子菜单已是最新，跳过')
        
        # ========== 4. 创建业务角色 ==========
        print('\n4️⃣  创建业务角色...')
        business_roles = [
            {
                'name': 'PM',
                'role_type': 'business',
                'remark': '产品经理，可管理全部反馈功能',
                'menus': ['all'],  # 全部业务菜单
            },
            {
                'name': 'CS',
                'role_type': 'business',
                'remark': '客户成功，可查看反馈和客户',
                'menus': ['/app/feedback/list', '/app/customer', '/app/ai/discovery'],
            },
            {
                'name': '开发',
                'role_type': 'business',
                'remark': '开发人员，只读需求主题',
                'menus': ['/app/topic/list', '/app/ai/discovery'],
            },
            {
                'name': '老板',
                'role_type': 'business',
                'remark': '租户管理员，查看全部',
                'menus': ['all'],
            },
        ]
        
        created_roles = []
        for role_data in business_roles:
            existing_role = await db.scalar(
                select(Role).where(Role.name == role_data['name'])
            )
            
            if not existing_role:
                menu_paths = role_data.pop('menus')
                role = Role(**role_data)
                db.add(role)
                await db.flush()
                
                # 分配菜单权限
                if 'all' in menu_paths:
                    # 分配所有 /app/* 菜单
                    all_app_menus = await db.scalars(
                        select(Menu).where(
                            (Menu.path.like('/app/%')) | (Menu.path == '/app/userecho')
                        )
                    )
                    for menu in all_app_menus:
                        await db.execute(
                            role_menu.insert().values(role_id=role.id, menu_id=menu.id)
                        )
                else:
                    # 分配指定菜单
                    for menu_path in menu_paths:
                        menu = await db.scalar(
                            select(Menu).where(Menu.path == menu_path)
                        )
                        if menu:
                            await db.execute(
                                role_menu.insert().values(role_id=role.id, menu_id=menu.id)
                            )
                    
                    # 同时分配父菜单（目录）
                    parent_menu = await db.scalar(
                        select(Menu).where(Menu.path == '/app/userecho')
                    )
                    if parent_menu:
                        await db.execute(
                            role_menu.insert().values(role_id=role.id, menu_id=parent_menu.id)
                        )
                
                created_roles.append(role_data['name'])
        
        if created_roles:
            print(f'   ✅ 创建业务角色: {", ".join(created_roles)}')
        else:
            print('   ⏭️  所有业务角色已存在，跳过')
        
        await db.commit()
        print('\n✅ 业务菜单和角色初始化完成！')
        print('\n📝 创建的资源：')
        print('   - 反馈管理目录')
        print('   - 5 个功能菜单（反馈列表、AI 发现中心、导入反馈、需求主题、客户管理）')
        print('   - 设置目录')
        print('   - 1 个设置子菜单（聚类策略）')
        print('   - 4 个业务角色（PM、CS、开发、老板）')


async def verify_initialization():
    """验证初始化结果"""
    async with async_db_session() as db:
        print('\n\n🔍 验证初始化结果...')
        
        # 检查菜单
        menus = await db.scalars(
            select(Menu).where(Menu.path.like('/app/%'))
        )
        menu_list = list(menus)
        print(f'\n📋 业务菜单数量: {len(menu_list)}')
        for menu in menu_list:
            print(f'   - {menu.title} ({menu.path})')
        
        # 检查角色
        roles = await db.scalars(
            select(Role).where(Role.role_type == 'business')
        )
        role_list = list(roles)
        print(f'\n👥 业务角色数量: {len(role_list)}')
        for role in role_list:
            print(f'   - {role.name} ({role.remark})')


async def main():
    """主函数：合并初始化和验证到同一个 event loop"""
    await init_business_menus()
    await verify_initialization()


if __name__ == '__main__':
    print('=' * 60)
    print('🚀 UserEcho 业务菜单和角色初始化脚本')
    print('=' * 60)
    
    try:
        asyncio.run(main())
        print('\n' + '=' * 60)
        print('✅ 初始化成功！')
        print('=' * 60)
    except Exception as e:
        print(f'\n❌ 初始化失败: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)
