#!/bin/bash
# Demo 数据初始化/重置脚本（仅创建账号和数据）
# 
# ⚠️  前置条件：
#   - 数据库表已创建（alembic upgrade head）
#   - 系统基础数据已初始化（fba init）
#   - 默认租户已创建（init_default_tenant.py）
#   - 业务菜单已初始化（init_business_menus.py）
#
# 用途：
#   1. 创建 Demo 预置账号和示例数据
#   2. 定时重置 Demo 数据（配合 cron 使用）
#
# 执行方式：
#   chmod +x init_demo_data_only.sh
#   ./init_demo_data_only.sh             # 首次初始化
#   ./init_demo_data_only.sh --reset     # 重置数据
#
# 💡 提示：如果是首次部署 Demo 环境，请使用 setup_demo_full.sh

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

# 解析参数
RESET_MODE=false
SILENT_MODE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --reset)
            RESET_MODE=true
            shift
            ;;
        --silent)
            SILENT_MODE=true
            shift
            ;;
        *)
            echo "未知参数: $1"
            echo "用法: $0 [--reset] [--silent]"
            exit 1
            ;;
    esac
done

# 检查是否在正确的目录
check_directory() {
    if [ ! -f "alembic.ini" ]; then
        print_error "错误：请在 server/backend 目录下执行此脚本"
        echo ""
        echo "正确用法："
        echo "  cd server/backend"
        echo "  ./init_demo_environment.sh"
        exit 1
    fi
}

# 检查 Python 虚拟环境
check_venv() {
    if [ -d "../.venv" ]; then
        VENV_PATH="../.venv"
    elif [ -d ".venv" ]; then
        VENV_PATH=".venv"
    else
        print_error "未找到 Python 虚拟环境"
        exit 1
    fi
}

# 激活虚拟环境
activate_venv() {
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

# 步骤 1: 创建 Demo 预置账号
step1_create_users() {
    print_header "步骤 1/3: 创建 Demo 预置账号"
    
    if [ "$RESET_MODE" = true ]; then
        print_info "重置模式：重建 Demo 账号..."
        python scripts/create_demo_users.py --reset
    else
        print_info "创建 Demo 账号（如已存在则跳过）..."
        python scripts/create_demo_users.py
    fi
    
    if [ $? -eq 0 ]; then
        print_success "Demo 账号创建完成"
    else
        print_error "Demo 账号创建失败"
        exit 1
    fi
    
    echo ""
}

# 步骤 2: 初始化示例数据
step2_init_data() {
    print_header "步骤 2/3: 初始化示例数据"
    
    if [ "$RESET_MODE" = true ]; then
        print_info "重置模式：重建示例数据..."
        python scripts/init_demo_data.py --reset
    else
        print_info "创建示例数据..."
        python scripts/init_demo_data.py
    fi
    
    if [ $? -eq 0 ]; then
        print_success "示例数据初始化完成"
    else
        print_error "示例数据初始化失败"
        exit 1
    fi
    
    echo ""
}

# 步骤 3: 验证初始化结果
step3_verify() {
    print_header "步骤 3/3: 验证初始化结果"
    
    python scripts/verify_demo_data.py
    
    if [ $? -eq 0 ]; then
        print_success "验证通过"
    else
        print_warning "验证未完全通过，请检查上述输出"
    fi
    
    echo ""
}

# 主函数
main() {
    if [ "$SILENT_MODE" = false ]; then
        print_header "🚀 Demo 环境初始化脚本"
        echo ""
    fi
    
    # 前置检查
    check_directory
    check_venv
    activate_venv
    check_env_file
    
    if [ "$RESET_MODE" = true ]; then
        print_warning "⚠️  重置模式：将删除并重建所有 Demo 数据"
        echo ""
    fi
    
    # 执行初始化步骤
    step1_create_users
    step2_init_data
    step3_verify
    
    # 完成提示
    if [ "$SILENT_MODE" = false ]; then
        print_header "✅ Demo 环境初始化完成！"
        echo ""
        print_success "Demo 账号："
        echo ""
        echo "  账号            密码              角色"
        echo "  ─────────────────────────────────────────"
        echo "  demo_po         demo123456        产品负责人"
        echo "  demo_ops        demo123456        用户运营"
        echo "  demo_admin      demo123456        系统管理员"
        echo ""
        print_header "🎉 初始化完成！"
    fi
}

# 错误处理
trap 'print_error "初始化过程中发生错误"; exit 1' ERR

# 执行主函数
main
