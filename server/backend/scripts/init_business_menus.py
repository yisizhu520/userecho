"""初始化业务菜单和角色

此脚本用于创建 UserEcho 业务功能的菜单和角色。
执行方式: python scripts/init_business_menus.py
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

from sqlalchemy import select

from backend.app.admin.model import Menu, Role, role_menu
from backend.database.db import async_db_session


async def init_business_menus() -> None:
    """初始化业务菜单和角色

    菜单结构：所有业务菜单直接作为顶级菜单展示（无父目录）
    设置功能：移至导航栏右侧偏好设置区域
    """
    async with async_db_session.begin() as db:
        print('📋 开始初始化业务菜单和角色...')

        # ========== 1. 清理旧的反馈管理目录（如果存在） ==========
        print('\n1️⃣  清理旧的菜单目录...')
        userecho_menu = await db.scalar(select(Menu).where(Menu.path == '/app/userecho'))
        if userecho_menu:
            await db.delete(userecho_menu)
            print('   🗑️  删除旧的反馈管理目录')
        else:
            print('   ⏭️  无需清理')

        # 清理旧的设置目录（如果存在）
        settings_menu = await db.scalar(select(Menu).where(Menu.path == '/app/settings'))
        if settings_menu:
            # 先删除设置子菜单
            settings_sub = await db.scalar(select(Menu).where(Menu.path == '/app/settings/clustering'))
            if settings_sub:
                await db.delete(settings_sub)
            await db.delete(settings_menu)
            print('   🗑️  删除旧的设置目录及子菜单')

        await db.flush()

        # ========== 2. 创建顶级菜单（无父目录，铺平展示） ==========
        print('\n2️⃣  创建顶级菜单...')
        top_level_menus = [
            {
                'title': '工作台',
                'name': 'UserEchoWorkspace',
                'path': '/app/dashboard/workspace',
                'component': '/userecho/dashboard/workspace',
                'icon': 'lucide:layout-dashboard',
                'perms': 'app:dashboard:view',
                'sort': 100,  # 业务菜单从100开始排序
            },
            {
                'title': '反馈列表',
                'name': 'FeedbackList',
                'path': '/app/feedback/list',
                'component': '/userecho/feedback/list',
                'icon': 'lucide:inbox',
                'perms': 'app:feedback:view',
                'sort': 101,
            },
            {
                'title': '截图识别',
                'name': 'ScreenshotUpload',
                'path': '/app/feedback/screenshot',
                'component': '/userecho/feedback/screenshot-upload',
                'icon': 'lucide:camera',
                'perms': 'app:feedback:screenshot',
                'sort': 102,
                'display': 0,  # 隐藏菜单
            },
            {
                'title': '导入反馈',
                'name': 'FeedbackImport',
                'path': '/app/feedback/import',
                'component': '/userecho/feedback/import',
                'icon': 'lucide:upload',
                'perms': 'app:feedback:import',
                'sort': 103,
                'display': 0,  # 隐藏菜单
            },
            {
                'title': 'AI 发现中心',
                'name': 'AIDiscovery',
                'path': '/app/ai/discovery',
                'component': '/userecho/discovery/index',
                'icon': 'lucide:sparkles',
                'perms': 'app:ai:view',
                'sort': 104,
            },
            {
                'title': '需求主题',
                'name': 'TopicList',
                'path': '/app/topic/list',
                'component': '/userecho/topic/list',
                'icon': 'lucide:lightbulb',
                'perms': 'app:topic:view',
                'sort': 105,
            },
            {
                'title': '主题详情',
                'name': 'TopicDetail',
                'path': '/app/topic/detail/:id',
                'component': '/userecho/topic/detail',
                'icon': '',
                'perms': 'app:topic:view',
                'sort': 106,
                'display': 0,  # hideInMenu
            },
            {
                'title': '客户管理',
                'name': 'CustomerManage',
                'path': '/app/customer',
                'component': '/userecho/customer/index',
                'icon': 'lucide:users',
                'perms': 'app:customer:view',
                'sort': 107,
            },
            {
                'title': '洞察报告',
                'name': 'InsightReport',
                'path': '/app/insights/report',
                'component': '/userecho/insights/report',
                'icon': 'lucide:file-bar-chart',
                'perms': 'app:insights:view',
                'sort': 108,
            },
        ]

        created_menus = []
        updated_menus = []
        for menu_data in top_level_menus:
            existing = await db.scalar(select(Menu).where(Menu.path == menu_data['path']))
            # 获取 display 参数，默认为 1（显示）
            display = menu_data.pop('display', 1)

            if not existing:
                menu = Menu(
                    **menu_data,
                    parent_id=None,  # 顶级菜单，无父目录
                    type=1,  # 菜单
                    status=1,
                    display=display,
                )
                db.add(menu)
                created_menus.append(menu_data['title'])
            else:
                # 更新已存在的菜单
                existing.component = menu_data['component']
                existing.icon = menu_data['icon']
                existing.sort = menu_data['sort']
                existing.perms = menu_data['perms']
                existing.display = display
                existing.parent_id = None  # 确保是顶级菜单
                updated_menus.append(menu_data['title'])

        if created_menus or updated_menus:
            await db.flush()
            if created_menus:
                print(f'   ✅ 创建顶级菜单: {", ".join(created_menus)}')
            if updated_menus:
                print(f'   🔄 更新顶级菜单: {", ".join(updated_menus)}')
        else:
            print('   ⏭️  所有菜单已是最新，跳过')

        # ========== 3. 创建业务角色 ==========
        print('\n3️⃣  创建业务角色...')
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
                'menus': [
                    '/app/feedback/list',
                    '/app/customer',
                    '/app/ai/discovery',
                    '/app/dashboard/workspace',
                    '/app/insights/report',
                ],
            },
            {
                'name': '开发',
                'role_type': 'business',
                'remark': '开发人员，只读需求主题',
                'menus': ['/app/topic/list', '/app/ai/discovery', '/app/dashboard/workspace', '/app/insights/report'],
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
            existing_role = await db.scalar(select(Role).where(Role.name == role_data['name']))

            if not existing_role:
                menu_paths = role_data.pop('menus')
                role = Role(**role_data)
                db.add(role)
                await db.flush()

                # 分配菜单权限
                if 'all' in menu_paths:
                    # 分配所有 /app/* 菜单
                    all_app_menus = await db.scalars(select(Menu).where(Menu.path.like('/app/%')))
                    for menu in all_app_menus:
                        await db.execute(role_menu.insert().values(role_id=role.id, menu_id=menu.id))
                else:
                    # 分配指定菜单
                    for menu_path in menu_paths:
                        menu = await db.scalar(select(Menu).where(Menu.path == menu_path))
                        if menu:
                            await db.execute(role_menu.insert().values(role_id=role.id, menu_id=menu.id))

                created_roles.append(role_data['name'])

        if created_roles:
            print(f'   ✅ 创建业务角色: {", ".join(created_roles)}')
        else:
            print('   ⏭️  所有业务角色已存在，跳过')

        print('\n✅ 业务菜单和角色初始化完成！')
        print('\n📝 创建的资源：')
        print(
            '   - 9 个顶级菜单（工作台、反馈列表、截图识别[隐藏]、导入反馈[隐藏]、'
            'AI发现、需求主题、主题详情[隐藏]、客户管理、洞察报告）'
        )
        print('   - 4 个业务角色（PM、CS、开发、老板）')
        print('\n💡 菜单结构（扁平化展示）：')
        print('   📊 工作台')
        print('   📋 反馈列表')
        print('   ✨ AI 发现中心')
        print('   💡 需求主题')
        print('   👥 客户管理')
        print('   📊 洞察报告')
        print('\n💡 设置功能已移至导航栏右侧偏好设置区域')


async def verify_initialization() -> None:
    """验证初始化结果"""
    async with async_db_session() as db:
        print('\n\n🔍 验证初始化结果...')

        # 检查菜单
        menus = await db.scalars(select(Menu).where(Menu.path.like('/app/%')))
        menu_list = list(menus)
        print(f'\n📋 业务菜单数量: {len(menu_list)}')
        for menu in menu_list:
            print(f'   - {menu.title} ({menu.path})')

        # 检查角色
        roles = await db.scalars(select(Role).where(Role.role_type == 'business'))
        role_list = list(roles)
        print(f'\n👥 业务角色数量: {len(role_list)}')
        for role in role_list:
            print(f'   - {role.name} ({role.remark})')


async def main() -> None:
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
