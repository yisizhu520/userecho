@echo off
REM 数据库一键初始化脚本（Windows CMD/PowerShell）
REM 用于全新数据库的完整初始化
REM 执行方式：直接双击或在 CMD 中运行 init_database.bat

setlocal enabledelayedexpansion
chcp 65001 > nul

echo ================================================================================
echo 🚀 UserEcho 数据库一键初始化脚本
echo ================================================================================
echo.
echo 此脚本将执行以下操作：
echo   1. 执行数据库迁移（创建所有表结构）
echo   2. 初始化业务菜单和角色
echo   3. 创建测试用户（6 个测试账号）
echo   4. 验证初始化结果
echo.
echo ⚠️  注意：此脚本适用于全新数据库，请确保数据库连接配置正确
echo.
pause
echo.

REM ================================================================================
REM 前置检查
REM ================================================================================

echo ================================================================================
echo 前置检查
echo ================================================================================
echo.

REM 检查是否在正确的目录
if not exist "alembic.ini" (
    echo ❌ 错误：请在 server\backend 目录下执行此脚本
    echo.
    echo 正确用法：
    echo   cd server\backend
    echo   init_database.bat
    echo.
    pause
    exit /b 1
)

REM 检查 Python 虚拟环境
if not exist ".venv" (
    echo ⚠️  未找到 Python 虚拟环境
    echo ℹ️  正在创建虚拟环境...
    python -m venv .venv
    if errorlevel 1 (
        echo ❌ 虚拟环境创建失败
        pause
        exit /b 1
    )
    echo ✅ 虚拟环境创建完成
    echo.
)

REM 激活虚拟环境
echo ℹ️  激活虚拟环境...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ 虚拟环境激活失败
    pause
    exit /b 1
)
echo ✅ 虚拟环境已激活
echo.

REM 检查依赖
echo ℹ️  检查 Python 依赖...
python -c "import alembic" 2>nul
if errorlevel 1 (
    echo ⚠️  Alembic 未安装，正在安装依赖...
    pip install -r ..\..\requirements.txt
    if errorlevel 1 (
        echo ❌ 依赖安装失败
        pause
        exit /b 1
    )
    echo ✅ 依赖安装完成
) else (
    echo ✅ 依赖检查通过
)
echo.

REM 检查数据库连接
echo ℹ️  检查数据库连接...
python -c "import sys; import asyncio; sys.path.insert(0, '.'); from backend.database.db import async_db_session; asyncio.run(async_db_session().__aenter__())" 2>nul
if errorlevel 1 (
    echo ❌ 数据库连接失败
    echo.
    echo 请检查 .env 文件中的数据库配置：
    echo   - DB_HOST
    echo   - DB_PORT
    echo   - DB_USER
    echo   - DB_PASSWORD
    echo   - DB_DATABASE
    echo.
    pause
    exit /b 1
)
echo ✅ 数据库连接成功
echo.

REM ================================================================================
REM 步骤 1: 执行数据库迁移
REM ================================================================================

echo ================================================================================
echo 步骤 1/4: 执行数据库迁移（创建表结构）
echo ================================================================================
echo.

echo ℹ️  运行 Alembic 迁移...
alembic upgrade head
if errorlevel 1 (
    echo ❌ 数据库迁移失败
    pause
    exit /b 1
)
echo ✅ 数据库表结构创建完成
echo.

REM ================================================================================
REM 步骤 2: 初始化业务菜单和角色
REM ================================================================================

echo ================================================================================
echo 步骤 2/4: 初始化业务菜单和角色
echo ================================================================================
echo.

echo ℹ️  运行业务菜单初始化脚本...
python scripts\init_business_menus.py
if errorlevel 1 (
    echo ❌ 业务菜单初始化失败
    pause
    exit /b 1
)
echo ✅ 业务菜单和角色初始化完成
echo.

REM ================================================================================
REM 步骤 3: 创建测试用户
REM ================================================================================

echo ================================================================================
echo 步骤 3/4: 创建测试用户
echo ================================================================================
echo.

REM 检查是否可以使用 psql
where psql >nul 2>&1
if %errorlevel% equ 0 (
    echo ℹ️  使用 SQL 脚本创建测试用户...
    
    REM 从 .env 读取数据库配置（简化版，假设使用默认值）
    psql -h localhost -p 5432 -U postgres -d userecho -f sql\postgresql\init_test_users.sql >nul 2>&1
    if errorlevel 1 (
        echo ⚠️  SQL 脚本执行失败，尝试使用 Python 脚本...
        goto use_python_script
    ) else (
        echo ✅ 测试用户创建完成（使用 SQL 脚本）
        goto test_users_done
    )
) else (
    echo ⚠️  未找到 psql 命令，使用 Python 脚本...
    goto use_python_script
)

:use_python_script
if exist "scripts\create_test_users.py" (
    python scripts\create_test_users.py
    if errorlevel 1 (
        echo ⚠️  测试用户创建失败，您可以稍后手动创建
    ) else (
        echo ✅ 测试用户创建完成（使用 Python 脚本）
    )
) else (
    echo ⚠️  未找到 create_test_users.py 脚本
    echo ℹ️  您可以稍后手动运行：
    echo   psql -U postgres -d your_database -f sql\postgresql\init_test_users.sql
)

:test_users_done
echo.

REM ================================================================================
REM 步骤 4: 验证初始化结果
REM ================================================================================

echo ================================================================================
echo 步骤 4/4: 验证初始化结果
echo ================================================================================
echo.

echo ℹ️  验证数据库初始化状态...
python -c "import sys; import asyncio; sys.path.insert(0, '.'); from sqlalchemy import select, func; from backend.database.db import async_db_session; from backend.app.admin.model import Menu, Role, User; async def verify(): async with async_db_session() as db: menu_count = await db.scalar(select(func.count(Menu.id)).where(Menu.path.like('/app/%%'))); print(f'  📋 业务菜单数量: {menu_count}'); role_count = await db.scalar(select(func.count(Role.id)).where(Role.role_type == 'business')); print(f'  👥 业务角色数量: {role_count}'); test_users = ['sysadmin', 'pm', 'cs', 'dev', 'boss', 'hybrid']; user_count = await db.scalar(select(func.count(User.id)).where(User.username.in_(test_users))); print(f'  🧑 测试用户数量: {user_count}/{len(test_users)}'); return menu_count > 0 and role_count > 0; asyncio.run(verify())"
if errorlevel 1 (
    echo ⚠️  验证未完全通过，请检查上述输出
) else (
    echo ✅ 数据库初始化验证通过
)
echo.

REM ================================================================================
REM 完成提示
REM ================================================================================

echo ================================================================================
echo ✅ 数据库初始化完成！
echo ================================================================================
echo.
echo 您现在可以使用以下测试账号登录：
echo.
echo   📝 测试账号清单（统一密码：Test123456）
echo   ────────────────────────────────────────
echo   账号      角色            菜单权限
echo   ────────────────────────────────────────
echo   sysadmin  系统管理员      /admin/* 菜单
echo   pm        PM              /app/* 全部菜单
echo   cs        CS              /app/* 部分菜单
echo   dev       开发            /app/* 只读菜单
echo   boss      老板            /app/* 全部菜单
echo   hybrid    混合角色        全部菜单
echo.
echo ℹ️  超级管理员账号：admin / Admin123456（如果已创建）
echo.
echo ================================================================================
echo 🎉 初始化完成，祝您使用愉快！
echo ================================================================================
echo.
pause
