#!/bin/bash
# 使用 .env 配置初始化数据脚本
# 执行方式：chmod +x init_data.sh && ./init_data.sh

set -e

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# 打印函数
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# 确保使用 .env 而不是 .env.demo
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export ENV_FILE="$SCRIPT_DIR/.env"

print_info "使用配置文件: $ENV_FILE"
echo ""

# 激活虚拟环境
if [ -f "../.venv/Scripts/activate" ]; then
    source "../.venv/Scripts/activate"
    PYTHON="../.venv/Scripts/python.exe"
elif [ -f "../.venv/bin/activate" ]; then
    source "../.venv/bin/activate"
    PYTHON="../.venv/bin/python"
else
    PYTHON="python"
fi

print_info "使用 Python: $(which $PYTHON)"
echo ""

echo "================================================================================"
echo "🚀 开始初始化数据（使用 .env 配置）"
echo "================================================================================"
echo ""

# 步骤 1: 创建默认租户和看板
echo "步骤 1/5: 创建默认租户和看板"
echo "--------------------------------------------------------------------------------"
$PYTHON scripts/init_default_tenant.py
print_success "默认租户和看板创建完成"
echo ""

# 步骤 2: 初始化业务菜单和角色
echo "步骤 2/5: 初始化业务菜单和角色"
echo "--------------------------------------------------------------------------------"
$PYTHON scripts/init_business_menus.py
print_success "业务菜单和角色初始化完成"
echo ""

# 步骤 3: 添加额外系统管理菜单
echo "步骤 3/5: 添加额外系统管理菜单"
echo "--------------------------------------------------------------------------------"
$PYTHON scripts/init_system_extra_menus.py
print_success "额外系统菜单初始化完成"
echo ""

# 步骤 4: 初始化订阅套餐
echo "步骤 4/5: 初始化订阅套餐"
echo "--------------------------------------------------------------------------------"
$PYTHON scripts/init_subscription_plans.py
print_success "订阅套餐初始化完成"
echo ""

# 步骤 5: 创建测试用户
echo "步骤 5/5: 创建测试用户"
echo "--------------------------------------------------------------------------------"
$PYTHON scripts/create_test_users.py
print_success "测试用户创建完成"
echo ""

# 验证结果
echo "步骤 6/6: 验证初始化结果"
echo "--------------------------------------------------------------------------------"
$PYTHON verify_data.py
echo ""

echo "================================================================================"
echo "✅ 数据初始化完成！"
echo "================================================================================"
echo ""
echo "📝 登录信息："
echo "  超级管理员: admin / Admin123456"
echo "  测试账号: sysadmin, pm, cs, dev, boss, hybrid / Test123456"
echo ""
