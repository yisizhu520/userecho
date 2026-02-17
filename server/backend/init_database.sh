#!/bin/bash
# 数据库一键初始化脚本（Linux/Mac/Git Bash）
# 用于全新数据库的完整初始化
# 执行方式：chmod +x init_database.sh && ./init_database.sh

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
        echo "  ./init_database.sh"
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

# 检查数据库连接
check_database() {
    print_info "检查数据库连接..."
    
    # 检查 .env 文件是否存在
    if [ ! -f ".env" ]; then
        print_error ".env 文件不存在"
        print_info "请在 server/backend 目录下创建 .env 文件"
        print_info "参考 .env.example 或文档配置数据库连接"
        exit 1
    fi
    
    # 尝试连接数据库（使用简单的测试脚本）
    db_check_output=$(python test_db_connection_simple.py 2>&1)
    db_check_exit_code=$?
    
    if [ $db_check_exit_code -eq 0 ]; then
        print_success "数据库连接成功"
    else
        print_error "数据库连接失败"
        echo ""
        print_warning "错误详情："
        echo "$db_check_output" | grep -E "❌|ERROR" | head -5
        echo ""
        print_info "运行详细测试获取更多信息："
        echo "  python test_db_connection_simple.py"
        echo ""
        exit 1
    fi
}

# 步骤 1: 执行数据库迁移
step1_migration() {
    print_header "步骤 1/4: 执行数据库迁移（创建表结构）"
    
    print_info "运行 Alembic 迁移..."
    alembic upgrade head
    
    if [ $? -eq 0 ]; then
        print_success "数据库表结构创建完成"
    else
        print_error "数据库迁移失败"
        exit 1
    fi
    
    echo ""
}

# 步骤 2: 初始化业务菜单和角色
step2_business_menus() {
    print_header "步骤 2/4: 初始化业务菜单和角色"
    
    print_info "运行业务菜单初始化脚本..."
    python scripts/init_business_menus.py
    
    if [ $? -eq 0 ]; then
        print_success "业务菜单和角色初始化完成"
    else
        print_error "业务菜单初始化失败"
        exit 1
    fi
    
    echo ""
}

# 步骤 3: 创建测试用户
step3_test_users() {
    print_header "步骤 3/4: 创建测试用户"
    
    # 检查是否可以使用 psql
    if command -v psql &> /dev/null; then
        print_info "使用 SQL 脚本创建测试用户..."
        
        # 从 .env 读取数据库配置
        if [ -f "../../.env" ]; then
            export $(grep -v '^#' ../../.env | xargs)
        fi
        
        # 尝试执行 SQL 脚本
        if psql -h "${DB_HOST:-localhost}" -p "${DB_PORT:-5432}" -U "${DB_USER:-postgres}" -d "${DB_DATABASE:-userecho}" -f sql/postgresql/init_test_users.sql 2>/dev/null; then
            print_success "测试用户创建完成（使用 SQL 脚本）"
        else
            print_warning "SQL 脚本执行失败，尝试使用 Python 脚本..."
            use_python_script=true
        fi
    else
        print_warning "未找到 psql 命令，使用 Python 脚本..."
        use_python_script=true
    fi
    
    # 如果 SQL 脚本失败或不可用，使用 Python 脚本
    if [ "$use_python_script" = true ]; then
        if [ -f "scripts/create_test_users.py" ]; then
            python scripts/create_test_users.py
            if [ $? -eq 0 ]; then
                print_success "测试用户创建完成（使用 Python 脚本）"
            else
                print_warning "测试用户创建失败，您可以稍后手动创建"
            fi
        else
            print_warning "未找到 create_test_users.py 脚本"
            print_info "您可以稍后手动运行："
            echo "  psql -U postgres -d your_database -f sql/postgresql/init_test_users.sql"
        fi
    fi
    
    echo ""
}

# 步骤 4: 验证初始化结果
step4_verify() {
    print_header "步骤 4/4: 验证初始化结果"
    
    print_info "验证数据库初始化状态..."
    
    python -c "
import sys
import asyncio
sys.path.insert(0, '.')
from sqlalchemy import select, func
from backend.database.db import async_db_session
from backend.app.admin.model import Menu, Role, User

async def verify():
    async with async_db_session() as db:
        # 检查菜单
        menu_count = await db.scalar(
            select(func.count(Menu.id)).where(Menu.path.like('/app/%'))
        )
        print(f'  📋 业务菜单数量: {menu_count}')
        
        # 检查角色
        role_count = await db.scalar(
            select(func.count(Role.id)).where(Role.role_type == 'business')
        )
        print(f'  👥 业务角色数量: {role_count}')
        
        # 检查测试用户
        test_users = ['sysadmin', 'pm', 'cs', 'dev', 'boss', 'hybrid']
        user_count = await db.scalar(
            select(func.count(User.id)).where(User.username.in_(test_users))
        )
        print(f'  🧑 测试用户数量: {user_count}/{len(test_users)}')
        
        return menu_count > 0 and role_count > 0

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
    clear
    
    print_header "🚀 UserEcho 数据库一键初始化脚本"
    echo ""
    print_warning "此脚本将执行以下操作："
    echo "  1. 执行数据库迁移（创建所有表结构）"
    echo "  2. 初始化业务菜单和角色"
    echo "  3. 创建测试用户（6 个测试账号）"
    echo "  4. 验证初始化结果"
    echo ""
    print_warning "注意：此脚本适用于全新数据库，请确保数据库连接配置正确"
    echo ""
    
    read -p "按 Enter 键继续，或按 Ctrl+C 取消..." dummy
    echo ""
    
    # 前置检查
    check_directory
    check_venv
    activate_venv
    check_dependencies
    check_database
    
    echo ""
    
    # 执行初始化步骤
    step1_migration
    step2_business_menus
    step3_test_users
    step4_verify
    
    # 完成提示
    print_header "✅ 数据库初始化完成！"
    echo ""
    print_success "您现在可以使用以下测试账号登录："
    echo ""
    echo "  📝 测试账号清单（统一密码：Test123456）"
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
    print_info "超级管理员账号：admin / Admin123456（如果已创建）"
    echo ""
    print_header "🎉 初始化完成，祝您使用愉快！"
}

# 错误处理
trap 'print_error "初始化过程中发生错误，请检查上述输出"; exit 1' ERR

# 执行主函数
main
