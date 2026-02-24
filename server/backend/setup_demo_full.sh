#!/bin/bash
# Demo 环境完整初始化脚本 - 从零到可用
# 
# 用途：
#   一键完成 Demo 环境的全流程初始化，包括：
#   1. 数据库表结构迁移
#   2. 系统基础数据（角色、菜单、部门）
#   3. 业务基础数据（租户、看板、权限）
#   4. Demo 预置账号和示例数据
#
# 执行方式：
#   chmod +x setup_demo_full.sh
#   ./setup_demo_full.sh              # 首次初始化
#   ./setup_demo_full.sh --reset      # 重置所有数据（危险！）
#   ./setup_demo_full.sh --skip-migration  # 跳过数据库迁移
#
# 前置条件：
#   - PostgreSQL 数据库已创建
#   - Redis 已启动
#   - .env 文件已配置
#   - Python 虚拟环境已安装依赖

set -e  # 遇到错误立即退出

# ==================== 颜色定义 ====================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ==================== 打印函数 ====================
print_header() {
    echo ""
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC} ${BLUE}$1${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════════════════╝${NC}"
}

print_step() {
    echo ""
    echo -e "${MAGENTA}▶ $1${NC}"
    echo ""
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

# ==================== 参数解析 ====================
RESET_MODE=false
SKIP_MIGRATION=false
SILENT_MODE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --reset)
            RESET_MODE=true
            shift
            ;;
        --skip-migration)
            SKIP_MIGRATION=true
            shift
            ;;
        --silent)
            SILENT_MODE=true
            shift
            ;;
        *)
            echo "未知参数: $1"
            echo "用法: $0 [--reset] [--skip-migration] [--silent]"
            exit 1
            ;;
    esac
done

# ==================== 前置检查 ====================

check_directory() {
    if [ ! -f "alembic.ini" ]; then
        print_error "错误：请在 server/backend 目录下执行此脚本"
        echo ""
        echo "正确用法："
        echo "  cd server/backend"
        echo "  ./setup_demo_full.sh"
        exit 1
    fi
}

check_venv() {
    if [ -d "../.venv" ]; then
        VENV_PATH="../.venv"
    elif [ -d ".venv" ]; then
        VENV_PATH=".venv"
    else
        print_error "未找到 Python 虚拟环境"
        print_info "请先执行: cd server && uv sync"
        exit 1
    fi
}

setup_python() {
    # 设置 Python 可执行文件路径
    if [ -f "$VENV_PATH/Scripts/python.exe" ]; then
        # Windows
        PYTHON="$VENV_PATH/Scripts/python.exe"
    elif [ -f "$VENV_PATH/bin/python" ]; then
        # Linux/Mac
        PYTHON="$VENV_PATH/bin/python"
    else
        print_error "无法找到虚拟环境 Python"
        exit 1
    fi
    
    # 验证 Python 是否可用
    if ! "$PYTHON" --version >/dev/null 2>&1; then
        print_error "Python 无法执行: $PYTHON"
        exit 1
    fi
}

check_env_file() {
    # 检查 .env.demo 文件是否存在
    if [ -f "../.env.demo" ]; then
        export ENV_FILE="../.env.demo"
        print_success "使用配置文件: .env.demo"
    elif [ -f ".env.demo" ]; then
        export ENV_FILE=".env.demo"
        print_success "使用配置文件: .env.demo"
    else
        print_error "未找到 .env.demo 配置文件"
        print_info "请在 server 目录或 server/backend 目录下创建 .env.demo"
        exit 1
    fi
}

check_database_connection() {
    print_step "检查数据库连接..."
    
    "$PYTHON" -c "
import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
sys.path.insert(0, '.')
from sqlalchemy import text
from backend.database.db import async_db_session
import asyncio

async def check():
    try:
        async with async_db_session() as db:
            await db.execute(text('SELECT 1'))
        print('OK')
        return True
    except Exception as e:
        print(f'ERROR: {e}', file=sys.stderr)
        return False

if not asyncio.run(check()):
    sys.exit(1)
" || {
        print_error "数据库连接失败，请检查 .env.demo 配置"
        exit 1
    }
    print_success "数据库连接正常"
}

check_redis_connection() {
    print_step "检查 Redis 连接..."
    
    "$PYTHON" -c "
import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
sys.path.insert(0, '.')
import asyncio

async def check():
    try:
        from backend.database.redis import redis_client
        await redis_client.ping()
        print('OK')
        return True
    except Exception as e:
        print(f'WARN: {e}', file=sys.stderr)
        return False

if not asyncio.run(check()):
    sys.exit(1)
" && {
        print_success "Redis 连接正常"
    } || {
        print_warning "Redis 连接失败（非致命错误，继续执行）"
    }
}

# ==================== 初始化步骤 ====================

step1_database_migration() {
    print_header "步骤 1/4: 数据库表结构迁移"
    
    if [ "$SKIP_MIGRATION" = true ]; then
        print_warning "已跳过数据库迁移"
        return
    fi
    
    print_info "执行 Alembic 迁移..."
    
    # 直接使用 alembic 命令（避免交互确认）
    "$PYTHON" -m alembic check 2>/dev/null || {
        print_warning "数据库需要更新（正常）"
    }
    
    print_info "升级数据库到最新版本..."
    "$PYTHON" -m alembic upgrade head
    
    if [ $? -eq 0 ]; then
        print_success "数据库迁移完成"
    else
        print_error "数据库迁移失败"
        exit 1
    fi
}

step2_system_base_data() {
    print_header "步骤 2/4: 系统基础数据初始化"
    
    print_info "初始化系统角色、菜单、部门..."
    
    if [ "$RESET_MODE" = true ]; then
        print_warning "重置模式：将重建系统基础数据"
        echo "y" | "$PYTHON" -m backend.main init --force 2>/dev/null || echo "y" | "$PYTHON" -m backend.main init
    else
        # 检查是否已初始化
        ALREADY_INIT=$("$PYTHON" -c "
import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')
from sqlalchemy import select
from backend.database.db import async_db_session
from backend.app.admin.model import Role
import asyncio

async def check():
    async with async_db_session() as db:
        role = await db.scalar(select(Role).limit(1))
        return role is not None

print('yes' if asyncio.run(check()) else 'no')
" 2>/dev/null)
        
        if [ "$ALREADY_INIT" = "yes" ]; then
            print_success "系统基础数据已存在，跳过初始化"
        else
            print_info "首次初始化系统数据..."
            echo "y" | "$PYTHON" -m backend.main init
        fi
    fi
    
    if [ $? -eq 0 ]; then
        print_success "系统基础数据初始化完成"
    else
        print_error "系统基础数据初始化失败"
        exit 1
    fi
}

step3_business_base_data() {
    print_header "步骤 3/4: 业务基础数据初始化"
    
    # 3.1 初始化默认租户
    print_step "3.1 创建默认租户和看板..."
    
    if [ -f "scripts/init_default_tenant.py" ]; then
        "$PYTHON" scripts/init_default_tenant.py
        if [ $? -eq 0 ]; then
            print_success "默认租户创建完成"
        else
            print_error "默认租户创建失败"
            exit 1
        fi
    else
        print_warning "未找到 init_default_tenant.py，跳过"
    fi
    
    # 3.2 初始化业务菜单和权限
    print_step "3.2 初始化租户权限和角色..."
    
    if [ -f "scripts/init_business_menus.py" ]; then
        "$PYTHON" scripts/init_business_menus.py
        if [ $? -eq 0 ]; then
            print_success "业务菜单初始化完成"
        else
            print_error "业务菜单初始化失败"
            exit 1
        fi
    else
        print_warning "未找到 init_business_menus.py，跳过"
    fi
}

step4_demo_data() {
    print_header "步骤 4/4: Demo 预置数据初始化"
    
    # 4.1 创建 Demo 账号
    print_step "4.1 创建 Demo 预置账号..."
    
    if [ "$RESET_MODE" = true ]; then
        "$PYTHON" scripts/create_demo_users.py --reset
    else
        "$PYTHON" scripts/create_demo_users.py
    fi
    
    if [ $? -eq 0 ]; then
        print_success "Demo 账号创建完成"
    else
        print_error "Demo 账号创建失败"
        exit 1
    fi
    
    # 4.2 初始化示例数据
    print_step "4.2 初始化示例数据..."
    
    if [ "$RESET_MODE" = true ]; then
        "$PYTHON" scripts/init_demo_data.py --reset
    else
        "$PYTHON" scripts/init_demo_data.py
    fi
    
    if [ $? -eq 0 ]; then
        print_success "示例数据初始化完成"
    else
        print_error "示例数据初始化失败"
        exit 1
    fi
}

# ==================== 验证步骤 ====================

verify_initialization() {
    print_header "验证初始化结果"
    
    "$PYTHON" scripts/verify_demo_data.py
    
    if [ $? -eq 0 ]; then
        print_success "验证通过"
    else
        print_warning "验证未完全通过，请检查上述输出"
    fi
}

# ==================== 主函数 ====================

main() {
    # 打印标题
    if [ "$SILENT_MODE" = false ]; then
        echo ""
        echo -e "${CYAN}╔════════════════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${CYAN}║                                                                        ║${NC}"
        echo -e "${CYAN}║${NC}  ${BLUE}🚀 Demo 环境完整初始化脚本 - 从零到可用${NC}                          ${CYAN}║${NC}"
        echo -e "${CYAN}║                                                                        ║${NC}"
        echo -e "${CYAN}╚════════════════════════════════════════════════════════════════════════╝${NC}"
        echo ""
    fi
    
    # 前置检查
    print_header "前置检查"
    check_directory
    print_success "工作目录正确"
    
    check_venv
    print_success "虚拟环境已找到: $VENV_PATH"
    
    setup_python
    print_success "Python 已配置: $PYTHON"
    
    check_env_file
    
    check_database_connection
    check_redis_connection
    
    # 重置警告
    if [ "$RESET_MODE" = true ]; then
        echo ""
        print_warning "⚠️  重置模式：将删除并重建所有数据！"
        print_warning "⚠️  此操作不可逆，请确认数据库已备份！"
        echo ""
        read -p "确认继续？(yes/no): " CONFIRM
        if [ "$CONFIRM" != "yes" ]; then
            print_info "已取消操作"
            exit 0
        fi
    fi
    
    # 执行初始化步骤
    step1_database_migration
    step2_system_base_data
    step3_business_base_data
    step4_demo_data
    
    # 验证结果
    verify_initialization
    
    # 完成提示
    if [ "$SILENT_MODE" = false ]; then
        echo ""
        print_header "🎉 Demo 环境初始化完成！"
        echo ""
        print_success "Demo 账号清单："
        echo ""
        echo "  ┌────────────────┬──────────────┬──────────────┬─────────────────────────┐"
        echo "  │ 账号           │ 密码         │ 角色         │ 功能                    │"
        echo "  ├────────────────┼──────────────┼──────────────┼─────────────────────────┤"
        echo "  │ demo_po        │ demo123456   │ 产品负责人   │ 看板、洞察、审批        │"
        echo "  │ demo_ops       │ demo123456   │ 用户运营     │ 反馈、客户、聚类        │"
        echo "  │ demo_admin     │ demo123456   │ 系统管理员   │ 用户、权限、设置        │"
        echo "  └────────────────┴──────────────┴──────────────┴─────────────────────────┘"
        echo ""
        print_info "下一步："
        echo "  1. 启动后端: ENV_FILE=.env.demo uvicorn backend.main:app"
        echo "  2. 启动前端: cd front && pnpm dev"
        echo "  3. 访问: http://localhost:5555/demo"
        echo ""
        print_header "✅ 初始化完成！"
    fi
}

# ==================== 错误处理 ====================

trap 'print_error "初始化过程中发生错误，请检查上述输出"; exit 1' ERR

# ==================== 执行主函数 ====================

main
