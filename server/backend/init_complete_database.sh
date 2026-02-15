#!/bin/bash
# 完整数据库初始化脚本（包含系统数据 + 业务数据）
# 执行方式：chmod +x init_complete_database.sh && ./init_complete_database.sh

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印函数
print_header() {
    echo -e "${BLUE}================================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# 检查是否在正确的目录
check_directory() {
    if [ ! -f "alembic.ini" ]; then
        print_error "错误：请在 server/backend 目录下执行此脚本"
        echo ""
        echo "正确用法："
        echo "  cd server/backend"
        echo "  ./init_complete_database.sh"
        exit 1
    fi
}

# 检查 Python 虚拟环境
check_venv() {
    # 检查 server/.venv（项目使用 uv 管理）
    if [ -d "../.venv" ]; then
        VENV_PATH="../.venv"
        print_success "找到虚拟环境: server/.venv"
    # 检查 backend/.venv（备用）
    elif [ -d ".venv" ]; then
        VENV_PATH=".venv"
        print_success "找到虚拟环境: backend/.venv"
    else
        print_warning "未找到 Python 虚拟环境"
        print_info "正在创建虚拟环境..."
        cd .. && python -m venv .venv && cd backend
        VENV_PATH="../.venv"
        print_success "虚拟环境创建完成"
    fi
}

# 激活虚拟环境
activate_venv() {
    print_info "激活虚拟环境..."
    
    if [ -f "$VENV_PATH/Scripts/activate" ]; then
        # Windows Git Bash
        source "$VENV_PATH/Scripts/activate"
    elif [ -f "$VENV_PATH/bin/activate" ]; then
        # Linux/Mac
        source "$VENV_PATH/bin/activate"
    else
        print_error "无法找到虚拟环境激活脚本"
        exit 1
    fi
    
    print_success "虚拟环境已激活"
}

# 检查依赖
check_dependencies() {
    print_info "检查 Python 依赖..."
    
    if ! python -c "import alembic" 2>/dev/null; then
        print_warning "Alembic 未安装，正在安装依赖..."
        
        # 检查是否使用 uv
        if command -v uv &> /dev/null && [ -f "../pyproject.toml" ]; then
            print_info "使用 uv 安装依赖..."
            cd .. && uv sync && cd backend
        else
            print_info "使用 pip 安装依赖..."
            pip install -r ../requirements.txt 2>/dev/null || pip install -e ..
        fi
        
        print_success "依赖安装完成"
    else
        print_success "依赖检查通过"
    fi
}

# 准备数据库环境
setup_database_environment() {
    print_info "准备数据库环境..."
    
    # 检查 .env 文件是否存在
    if [ ! -f ".env" ]; then
        print_error ".env 文件不存在"
        print_info "请在 server/backend 目录下创建 .env 文件"
        print_info "参考 .env.example 或文档配置数据库连接"
        exit 1
    fi
    
    # 运行数据库环境准备脚本
    python scripts/setup_database_environment.py
    
    if [ $? -eq 0 ]; then
        echo ""
        print_success "数据库环境准备完成"
    else
        print_error "数据库环境准备失败"
        exit 1
    fi
}

# 步骤 1: 使用 fba init 初始化系统基础数据
step1_fba_init() {
    print_header "步骤 1/4: 使用 fba init 初始化系统基础数据"
    
    print_warning "此操作将清空数据库所有数据并重建！"
    echo ""
    print_info "fba init 将会："
    echo "  • 执行数据库迁移（创建表结构）"
    echo "  • 导入系统管理菜单（/system/*, /log/*, /monitor/* 等）"
    echo "  • 创建 admin 超级管理员（密码：Admin123456）"
    echo "  • 创建测试部门和测试角色"
    echo ""
    
    # 自动确认 fba init（非交互模式）
    print_info "执行 fba init..."
    export PYTHONIOENCODING=utf-8
    echo "y" | fba init
    
    if [ $? -eq 0 ]; then
        print_success "系统基础数据初始化完成"
    else
        print_error "fba init 执行失败"
        exit 1
    fi
    
    echo ""
}

# 步骤 2: 创建默认租户
step2_default_tenant() {
    print_header "步骤 2/5: 创建默认租户"
    
    print_info "创建 default-tenant 租户记录..."
    python scripts/init_default_tenant.py
    
    if [ $? -eq 0 ]; then
        print_success "默认租户创建完成"
    else
        print_error "默认租户创建失败"
        exit 1
    fi
    
    echo ""
}

# 步骤 3: 初始化业务菜单和角色
step3_business_menus() {
    print_header "步骤 3/5: 初始化业务菜单和角色"
    
    print_info "创建业务菜单（/app/*）和业务角色..."
    python scripts/init_business_menus.py
    
    if [ $? -eq 0 ]; then
        print_success "业务菜单和角色初始化完成"
    else
        print_error "业务菜单初始化失败"
        exit 1
    fi
    
    echo ""
}

# 步骤 4: 创建测试用户
step4_test_users() {
    print_header "步骤 4/5: 创建测试用户"
    
    print_info "创建 6 个测试账号（sysadmin, pm, cs, dev, boss, hybrid）..."
    python scripts/create_test_users.py
    
    if [ $? -eq 0 ]; then
        print_success "测试用户创建完成"
    else
        print_warning "测试用户创建失败，您可以稍后手动创建"
    fi
    
    echo ""
}

# 步骤 5: 验证初始化结果
step5_verify() {
    print_header "步骤 5/5: 验证初始化结果"
    
    print_info "验证数据库初始化状态..."
    
    python -c "
import sys
import io
import asyncio

# Windows 平台 UTF-8 输出支持
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, '.')
from sqlalchemy import select, func
from backend.database.db import async_db_session
from backend.app.admin.model import Menu, Role, User, Dept

async def verify():
    from backend.app.userecho.model import Tenant
    
    async with async_db_session() as db:
        # 检查租户
        tenant = await db.scalar(select(Tenant).where(Tenant.id == 'default-tenant'))
        if tenant:
            print(f'  🏢 默认租户: {tenant.name} ({tenant.id})')
        
        # 检查部门
        dept_count = await db.scalar(select(func.count(Dept.id)))
        print(f'  🏢 部门数量: {dept_count}')
        
        # 检查系统菜单
        sys_menu_count = await db.scalar(
            select(func.count(Menu.id)).where(Menu.path.like('/system/%'))
        )
        print(f'  📋 系统菜单数量: {sys_menu_count}')
        
        # 检查业务菜单
        app_menu_count = await db.scalar(
            select(func.count(Menu.id)).where(Menu.path.like('/app/%'))
        )
        print(f'  📱 业务菜单数量: {app_menu_count}')
        
        # 检查角色
        role_count = await db.scalar(select(func.count(Role.id)))
        print(f'  👥 角色数量: {role_count}')
        
        # 检查用户
        user_count = await db.scalar(select(func.count(User.id)))
        print(f'  🧑 用户数量: {user_count}')
        
        # 检查 admin 用户
        admin = await db.scalar(select(User).where(User.username == 'admin'))
        if admin:
            print(f'  ✅ admin 超级管理员已创建')
        
        return tenant and dept_count > 0 and sys_menu_count > 0 and app_menu_count > 0

try:
    if asyncio.run(verify()):
        sys.exit(0)
    else:
        sys.exit(1)
except Exception as e:
    print(f'  ❌ 验证失败: {e}')
    sys.exit(1)
"
    
    if [ $? -eq 0 ]; then
        print_success "数据库初始化验证通过"
    else
        print_warning "验证未完全通过，请检查上述输出"
    fi
    
    echo ""
}

# 主函数
main() {
    # clear - Windows Git Bash 可能不支持，注释掉
    # clear
    
    print_header "🚀 UserEcho 一键完整数据库初始化脚本"
    echo ""
    print_warning "⚠️  此脚本将清空数据库所有数据并重建 ⚠️"
    echo ""
    print_info "此脚本将自动完成以下操作："
    echo ""
    echo "  【环境准备】（自动）"
    echo "  • 检查并创建数据库（如果不存在）"
    echo "  • 安装 pgvector 扩展"
    echo "  • 配置 Redis 连接"
    echo ""
    echo "  【数据初始化】"
    echo "  1. 使用 fba init 初始化系统基础数据（部门、系统菜单、admin）"
    echo "  2. 创建默认租户（default-tenant）"
    echo "  3. 初始化业务菜单和角色（/app/* 菜单）"
    echo "  4. 创建测试用户（6 个测试账号）"
    echo "  5. 验证初始化结果"
    echo ""
    print_warning "⚠️  注意：数据库中的所有现有数据将被删除 ⚠️"
    echo ""
    
    read -p "确认继续？按 Enter 键继续，或按 Ctrl+C 取消..." dummy
    echo ""
    
    # 前置检查
    check_directory
    check_venv
    activate_venv
    check_dependencies
    setup_database_environment
    
    echo ""
    
    # 执行初始化步骤
    step1_fba_init
    step2_default_tenant
    step3_business_menus
    step4_test_users
    step5_verify
    
    # 完成提示
    print_header "✅ 完整数据库初始化完成！"
    echo ""
    print_success "您现在可以使用以下账号登录："
    echo ""
    echo "  🔐 超级管理员账号"
    echo "  ────────────────────────────────────────"
    echo "  账号: admin"
    echo "  密码: Admin123456"
    echo "  权限: 全部系统管理功能"
    echo ""
    echo "  👥 业务测试账号（统一密码：Test123456）"
    echo "  ────────────────────────────────────────"
    echo "  账号      角色            菜单权限"
    echo "  ────────────────────────────────────────"
    echo "  sysadmin  系统管理员      /admin/* 菜单"
    echo "  pm        PM              /app/* 全部菜单"
    echo "  cs        CS              /app/* 部分菜单"
    echo "  dev       开发            /app/* 只读菜单"
    echo "  boss      老板            /app/* 全部菜单"
    echo "  hybrid    混合角色        全部菜单"
    echo ""
    print_header "🎉 初始化完成，祝您使用愉快！"
}

# 错误处理
trap 'print_error "初始化过程中发生错误，请检查上述输出"; exit 1' ERR

# 执行主函数
main

