@echo off
REM 快速验证数据库初始化状态（Windows）
REM 执行方式：verify_database.bat

setlocal enabledelayedexpansion
chcp 65001 > nul

echo ============================================================
echo 🔍 数据库初始化状态验证
echo ============================================================
echo.

REM 激活虚拟环境
if exist "..\\.venv\\Scripts\\activate.bat" (
    call ..\.venv\Scripts\activate.bat
) else (
    echo ⚠️  未找到虚拟环境
    pause
    exit /b 1
)

REM 运行验证
python test_db_connection_simple.py

echo.
echo ---
echo.

python -c "import asyncio, io, sys; exec(open('verify_check.py').read()) if False else exec(\"import asyncio, io, sys\\nif sys.platform == 'win32':\\n    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')\\nsys.path.insert(0, '.')\\nfrom sqlalchemy import select, func\\nfrom backend.app.admin.model import User, Role, Menu, user_role\\nfrom backend.database.db import async_db_session\\n\\nasync def verify():\\n    async with async_db_session() as db:\\n        menus = await db.scalar(select(func.count(Menu.id)))\\n        business_menus = await db.scalar(select(func.count(Menu.id)).where(Menu.path.like('/app/%%')))\\n        roles = await db.scalar(select(func.count(Role.id)))\\n        business_roles = await db.scalar(select(func.count(Role.id)).where(Role.role_type == 'business'))\\n        users = await db.scalar(select(func.count(User.id)))\\n        test_users = await db.scalar(select(func.count(User.id)).where(User.username.in_(['sysadmin','pm','cs','dev','boss','hybrid'])))\\n        print('📊 数据库统计:')\\n        print(f'   菜单总数: {menus} (业务菜单: {business_menus})')\\n        print(f'   角色总数: {roles} (业务角色: {business_roles})')\\n        print(f'   用户总数: {users} (测试用户: {test_users}/6)')\\n        print()\\n        if menus >= 8 and roles >= 5 and test_users == 6:\\n            print('✅ 数据库已完全初始化，可以直接使用！')\\n            print()\\n            print('💡 下一步:')\\n            print('   1. 启动后端: cd server\\\\\\\\backend && python run.py')\\n            print('   2. 启动前端: cd front && pnpm dev')\\n            print('   3. 使用测试账号登录 (密码: Test123456)')\\n        else:\\n            print('⚠️  数据库部分初始化，建议重新运行: init_database.bat')\\nasyncio.run(verify())\\n\")"

echo.
echo ============================================================
echo.
pause
