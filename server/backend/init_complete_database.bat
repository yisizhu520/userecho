@echo off
REM 完整数据库初始化脚本（Windows 版本）
REM 执行方式：在 server/backend 目录下运行 init_complete_database.bat

setlocal enabledelayedexpansion

REM 颜色支持（Windows 10+）
set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "NC=[0m"

REM 打印函数
goto :main

:print_header
echo %BLUE%================================================================================%NC%
echo %BLUE%%~1%NC%
echo %BLUE%================================================================================%NC%
goto :eof

:print_success
echo %GREEN%✅ %~1%NC%
goto :eof

:print_error
echo %RED%❌ %~1%NC%
goto :eof

:print_warning
echo %YELLOW%⚠️  %~1%NC%
goto :eof

:print_info
echo %BLUE%ℹ️  %~1%NC%
goto :eof

:check_directory
if not exist "alembic.ini" (
    call :print_error "错误：请在 server\backend 目录下执行此脚本"
    echo.
    echo 正确用法：
    echo   cd server\backend
    echo   init_complete_database.bat
    exit /b 1
)
goto :eof

:check_venv
REM 检查 server/.venv
if exist "..\..venv" (
    set "VENV_PATH=..\..venv"
    call :print_success "找到虚拟环境: server\.venv"
) else if exist ".venv" (
    set "VENV_PATH=.venv"
    call :print_success "找到虚拟环境: backend\.venv"
) else (
    call :print_warning "未找到 Python 虚拟环境"
    call :print_info "正在创建虚拟环境..."
    cd .. && python -m venv .venv && cd backend
    set "VENV_PATH=..\..venv"
    call :print_success "虚拟环境创建完成"
)
goto :eof

:activate_venv
call :print_info "激活虚拟环境..."
if exist "%VENV_PATH%\Scripts\activate.bat" (
    call "%VENV_PATH%\Scripts\activate.bat"
    call :print_success "虚拟环境已激活"
) else (
    call :print_error "无法找到虚拟环境激活脚本"
    exit /b 1
)
goto :eof

:check_dependencies
call :print_info "检查 Python 依赖..."
python -c "import alembic" 2>nul
if errorlevel 1 (
    call :print_warning "Alembic 未安装，正在安装依赖..."
    
    REM 检查是否使用 uv
    where uv >nul 2>nul
    if not errorlevel 1 (
        if exist "..\pyproject.toml" (
            call :print_info "使用 uv 安装依赖..."
            cd .. && uv sync && cd backend
        )
    ) else (
        call :print_info "使用 pip 安装依赖..."
        pip install -r ..\requirements.txt 2>nul || pip install -e ..
    )
    call :print_success "依赖安装完成"
) else (
    call :print_success "依赖检查通过"
)
goto :eof

:setup_database_environment
call :print_info "准备数据库环境..."

if not exist ".env" (
    call :print_error ".env 文件不存在"
    call :print_info "请在 server\backend 目录下创建 .env 文件"
    call :print_info "参考 .env.example 或文档配置数据库连接"
    exit /b 1
)

REM 运行数据库环境准备脚本
python scripts\setup_database_environment.py
if errorlevel 1 (
    call :print_error "数据库环境准备失败"
    exit /b 1
) else (
    echo.
    call :print_success "数据库环境准备完成"
)
goto :eof

:step1_fba_init
call :print_header "步骤 1/4: 使用 fba init 初始化系统基础数据"
echo.
call :print_warning "此操作将清空数据库所有数据并重建！"
echo.
call :print_info "fba init 将会："
echo   • 执行数据库迁移（创建表结构）
echo   • 导入系统管理菜单（/system/*, /log/*, /monitor/* 等）
echo   • 创建 admin 超级管理员（密码：Admin123456）
echo   • 创建测试部门和测试角色
echo.

call :print_info "执行 fba init..."
set PYTHONIOENCODING=utf-8
echo y | fba init
if errorlevel 1 (
    call :print_error "fba init 执行失败"
    exit /b 1
)
call :print_success "系统基础数据初始化完成"
echo.
goto :eof

:step2_default_tenant
call :print_header "步骤 2/5: 创建默认租户"
echo.
call :print_info "创建 default-tenant 租户记录..."
python scripts\init_default_tenant.py
if errorlevel 1 (
    call :print_error "默认租户创建失败"
    exit /b 1
)
call :print_success "默认租户创建完成"
echo.
goto :eof

:step3_business_menus
call :print_header "步骤 3/5: 初始化业务菜单和角色"
echo.
call :print_info "创建业务菜单（/app/*）和业务角色..."
python scripts\init_business_menus.py
if errorlevel 1 (
    call :print_error "业务菜单初始化失败"
    exit /b 1
)
call :print_success "业务菜单和角色初始化完成"
echo.
goto :eof

:step4_test_users
call :print_header "步骤 4/5: 创建测试用户"
echo.
call :print_info "创建 6 个测试账号（sysadmin, pm, cs, dev, boss, hybrid）..."
python scripts\create_test_users.py
if errorlevel 1 (
    call :print_warning "测试用户创建失败，您可以稍后手动创建"
) else (
    call :print_success "测试用户创建完成"
)
echo.
goto :eof

:step5_verify
call :print_header "步骤 5/5: 验证初始化结果"
echo.
call :print_info "验证数据库初始化状态..."

python -c "import sys; import io; import asyncio; if sys.platform == 'win32': sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8'); sys.path.insert(0, '.'); from sqlalchemy import select, func; from backend.database.db import async_db_session; from backend.app.admin.model import Menu, Role, User, Dept; from backend.app.userecho.model import Tenant; async def verify(): async with async_db_session() as db: tenant = await db.scalar(select(Tenant).where(Tenant.id == 'default-tenant')); tenant and print(f'  🏢 默认租户: {tenant.name} ({tenant.id})'); dept_count = await db.scalar(select(func.count(Dept.id))); print(f'  🏢 部门数量: {dept_count}'); sys_menu_count = await db.scalar(select(func.count(Menu.id)).where(Menu.path.like('/system/%%'))); print(f'  📋 系统菜单数量: {sys_menu_count}'); app_menu_count = await db.scalar(select(func.count(Menu.id)).where(Menu.path.like('/app/%%'))); print(f'  📱 业务菜单数量: {app_menu_count}'); role_count = await db.scalar(select(func.count(Role.id))); print(f'  👥 角色数量: {role_count}'); user_count = await db.scalar(select(func.count(User.id))); print(f'  🧑 用户数量: {user_count}'); admin = await db.scalar(select(User).where(User.username == 'admin')); admin and print(f'  ✅ admin 超级管理员已创建'); return tenant and dept_count > 0 and sys_menu_count > 0 and app_menu_count > 0; try: sys.exit(0 if asyncio.run(verify()) else 1); except Exception as e: print(f'  ❌ 验证失败: {e}'); sys.exit(1)"

if errorlevel 1 (
    call :print_warning "验证未完全通过，请检查上述输出"
) else (
    call :print_success "数据库初始化验证通过"
)
echo.
goto :eof

:main
cls
call :print_header "🚀 UserEcho 一键完整数据库初始化脚本"
echo.
call :print_warning "⚠️  此脚本将清空数据库所有数据并重建 ⚠️"
echo.
call :print_info "此脚本将自动完成以下操作："
echo.
echo   【环境准备】（自动）
echo   • 检查并创建数据库（如果不存在）
echo   • 安装 pgvector 扩展
echo   • 配置 Redis 连接
echo.
echo   【数据初始化】
echo   1. 使用 fba init 初始化系统基础数据（部门、系统菜单、admin）
echo   2. 创建默认租户（default-tenant）
echo   3. 初始化业务菜单和角色（/app/* 菜单）
echo   4. 创建测试用户（6 个测试账号）
echo   5. 验证初始化结果
echo.
call :print_warning "⚠️  注意：数据库中的所有现有数据将被删除 ⚠️"
echo.

pause
echo.

REM 前置检查
call :check_directory
if errorlevel 1 exit /b 1

call :check_venv
if errorlevel 1 exit /b 1

call :activate_venv
if errorlevel 1 exit /b 1

call :check_dependencies
if errorlevel 1 exit /b 1

call :setup_database_environment
if errorlevel 1 exit /b 1

echo.

REM 执行初始化步骤
call :step1_fba_init
if errorlevel 1 exit /b 1

call :step2_default_tenant
if errorlevel 1 exit /b 1

call :step3_business_menus
if errorlevel 1 exit /b 1

call :step4_test_users
REM 测试用户创建失败不影响整体流程

call :step5_verify
REM 验证失败不影响整体流程

REM 完成提示
call :print_header "✅ 完整数据库初始化完成！"
echo.
call :print_success "您现在可以使用以下账号登录："
echo.
echo   🔐 超级管理员账号
echo   ────────────────────────────────────────
echo   账号: admin
echo   密码: Admin123456
echo   权限: 全部系统管理功能
echo.
echo   👥 业务测试账号（统一密码：Test123456）
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
call :print_header "🎉 初始化完成，祝您使用愉快！"
echo.

pause
