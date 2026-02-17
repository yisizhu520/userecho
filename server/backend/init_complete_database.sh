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

# 询问用户是否 drop 所有表
ask_drop_tables() {
    print_header "🗑️  数据库清理选项"
    echo ""
    print_warning "您希望如何初始化数据库？"
    echo ""
    echo "  1) 完全重建（推荐）- 删除所有表并重新创建"
    echo "     • 适用于：全新安装、彻底重置"
    echo "     • 警告：将删除所有现有数据"
    echo ""
    echo "  2) 增量更新 - 保留现有数据，仅更新表结构"
    echo "     • 适用于：数据库升级、添加新表"
    echo "     • 注意：不会重新初始化基础数据"
    echo ""
    
    while true; do
        read -p "请选择 [1/2]: " choice
        case $choice in
            1)
                DROP_TABLES=true
                print_info "已选择：完全重建数据库"
                break
                ;;
            2)
                DROP_TABLES=false
                print_info "已选择：增量更新数据库"
                break
                ;;
            *)
                print_error "无效选择，请输入 1 或 2"
                ;;
        esac
    done
    
    echo ""
}

# 步骤 1a: 删除所有表（可选）
step1a_drop_tables() {
    if [ "$DROP_TABLES" = true ]; then
        print_header "步骤 1/6: 删除所有数据库表"
        
        print_warning "正在删除所有表..."
        python scripts/drop_all_tables.py
        
        if [ $? -eq 0 ]; then
            print_success "所有表已删除"
        else
            print_error "删除表失败"
            exit 1
        fi
        
        echo ""
    else
        print_info "跳过删除表步骤"
        echo ""
    fi
}

# 步骤 1b: 执行数据库迁移
step1b_migrate() {
    if [ "$DROP_TABLES" = true ]; then
        print_header "步骤 2/6: 使用 fba init 初始化系统基础数据"
        
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
    else
        print_header "步骤 1/5: 执行数据库迁移"
        
        print_info "执行 Alembic 迁移..."
        alembic upgrade head
        
        if [ $? -eq 0 ]; then
            print_success "数据库迁移完成"
        else
            print_error "数据库迁移失败"
            exit 1
        fi
    fi
    
    echo ""
}

# 步骤 2: 创建默认租户和看板
step2_default_tenant() {
    if [ "$DROP_TABLES" = true ]; then
        print_header "步骤 3/6: 创建默认租户和看板"
    else
        print_header "步骤 2/5: 创建默认租户和看板"
    fi
    
    print_info "创建 default-tenant 租户和 default-board 看板..."
    python scripts/init_default_tenant.py
    
    if [ $? -eq 0 ]; then
        print_success "默认租户和看板创建完成"
    else
        print_error "默认租户创建失败"
        exit 1
    fi
    
    echo ""
}

# 步骤 3: 初始化业务菜单和角色
step3_business_menus() {
    if [ "$DROP_TABLES" = true ]; then
        print_header "步骤 4/6: 初始化业务菜单和角色"
    else
        print_header "步骤 3/5: 初始化业务菜单和角色"
    fi
    
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
    if [ "$DROP_TABLES" = true ]; then
        print_header "步骤 5/6: 创建测试用户"
    else
        print_header "步骤 4/5: 创建测试用户"
    fi
    
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
    if [ "$DROP_TABLES" = true ]; then
        print_header "步骤 6/6: 验证初始化结果"
    else
        print_header "步骤 5/5: 验证初始化结果"
    fi
    
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
    from backend.app.userecho.model import Tenant, Board, TenantUser, Insight
    
    async with async_db_session() as db:
        # 检查租户
        tenant = await db.scalar(select(Tenant).where(Tenant.id == 'default-tenant'))
        if tenant:
            print(f'  🏢 默认租户: {tenant.name} ({tenant.id}, slug={tenant.slug})')
        
        # 检查看板
        board = await db.scalar(select(Board).where(Board.id == 'default-board'))
        if board:
            print(f'  📋 默认看板: {board.name} ({board.id})')
        
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
        
        # 检查租户用户关联
        tenant_user_count = await db.scalar(select(func.count(TenantUser.id)))
        print(f'  🔗 租户用户关联数量: {tenant_user_count}')
        
        # 检查 Insight 表是否存在
        try:
            insight_count = await db.scalar(select(func.count(Insight.id)))
            print(f'  💡 Insight 表已创建（记录数: {insight_count}）')
        except Exception as e:
            print(f'  ❌ Insight 表检查失败: {e}')
            return False
        
        # 检查 admin 用户
        admin = await db.scalar(select(User).where(User.username == 'admin'))
        if admin:
            print(f'  ✅ admin 超级管理员已创建')
        
        return tenant and board and dept_count > 0 and sys_menu_count > 0 and app_menu_count > 0

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
    
    # 前置检查
    check_directory
    check_venv
    activate_venv
    check_dependencies
    setup_database_environment
    
    echo ""
    
    # 询问用户是否 drop 所有表
    ask_drop_tables
    
    # 最终确认
    if [ "$DROP_TABLES" = true ]; then
        print_warning "⚠️  警告：即将删除数据库中的所有数据 ⚠️"
        echo ""
        print_info "此脚本将执行以下操作："
        echo ""
        echo "  1. 删除所有数据库表"
        echo "  2. 使用 fba init 初始化系统基础数据"
        echo "  3. 创建默认租户和看板"
        echo "  4. 初始化业务菜单和角色"
        echo "  5. 创建测试用户"
        echo "  6. 验证初始化结果"
        echo ""
    else
        print_info "此脚本将执行以下操作："
        echo ""
        echo "  1. 执行数据库迁移（Alembic upgrade head）"
        echo "  2. 创建默认租户和看板（如果不存在）"
        echo "  3. 初始化业务菜单和角色（如果不存在）"
        echo "  4. 创建测试用户（如果不存在）"
        echo "  5. 验证初始化结果"
        echo ""
    fi
    
    read -p "确认继续？按 Enter 键继续，或按 Ctrl+C 取消..." dummy
    echo ""
    
    # 执行初始化步骤
    step1a_drop_tables
    step1b_migrate
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
    echo "  ─────────────────────────────────────────────────────"
    echo "  账号      系统角色        租户角色            菜单权限"
    echo "  ─────────────────────────────────────────────────────"
    echo "  sysadmin  系统管理员      admin               /admin/* 菜单"
    echo "  pm        PM              product_manager     /app/* 全部菜单"
    echo "  cs        CS              customer_success    /app/* 部分菜单"
    echo "  dev       开发            developer           /app/* 只读菜单"
    echo "  boss      老板            admin               /app/* 全部菜单"
    echo "  hybrid    混合角色        admin               全部菜单"
    echo ""
    print_header "🎉 初始化完成，祝您使用愉快！"
}

# 错误处理
trap 'print_error "初始化过程中发生错误，请检查上述输出"; exit 1' ERR

# 执行主函数
main
