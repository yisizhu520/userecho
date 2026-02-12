#!/bin/bash
# 创建测试用户脚本 (Linux/Mac Shell 版本)
# 使用方法：chmod +x create_test_users.sh && ./create_test_users.sh

set -e

echo "================================================================================"
echo "测试用户创建脚本"
echo "================================================================================"
echo ""

# 检查是否安装了 psql
if ! command -v psql &> /dev/null; then
    echo "❌ [错误] 未找到 psql 命令，请确保已安装 PostgreSQL 客户端"
    echo ""
    echo "如果使用 Docker，请运行以下命令："
    echo "docker exec -i feedalyze-db psql -U postgres -d feedalyze < sql/postgresql/init_test_users.sql"
    echo ""
    exit 1
fi

# 读取数据库连接信息
read -p "请输入数据库主机 (默认: localhost): " DB_HOST
DB_HOST=${DB_HOST:-localhost}

read -p "请输入数据库端口 (默认: 5432): " DB_PORT
DB_PORT=${DB_PORT:-5432}

read -p "请输入数据库用户名 (默认: postgres): " DB_USER
DB_USER=${DB_USER:-postgres}

read -p "请输入数据库名称 (默认: feedalyze): " DB_NAME
DB_NAME=${DB_NAME:-feedalyze}

echo ""
echo "================================================================================"
echo "正在连接数据库..."
echo "主机: $DB_HOST:$DB_PORT"
echo "用户: $DB_USER"
echo "数据库: $DB_NAME"
echo "================================================================================"
echo ""

# 执行 SQL 脚本
PGPASSWORD=$PGPASSWORD psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f sql/postgresql/init_test_users.sql

if [ $? -eq 0 ]; then
    echo ""
    echo "================================================================================"
    echo "✅ [成功] 测试用户创建完成！"
    echo "================================================================================"
    echo ""
    echo "📝 测试账号清单 - 统一密码：Test123456"
    echo ""
    echo "账号          角色              菜单权限"
    echo "------------- ----------------- ------------------------------------------"
    echo "sysadmin      系统管理员        只能看到 /admin/* 菜单"
    echo "pm            PM                只能看到 /app/* 菜单（全权限）"
    echo "cs            CS                只能看到 /app/* 部分菜单"
    echo "dev           开发              只能看到 /app/* 只读菜单"
    echo "boss          老板              可以看到 /app/* 全部菜单"
    echo "hybrid        系统管理员+PM     可以看到全部菜单 (/admin/* + /app/*)"
    echo ""
    echo "💡 提示：使用上述账号登录前端测试菜单显示功能"
    echo ""
else
    echo ""
    echo "================================================================================"
    echo "❌ [失败] 创建用户失败，请检查数据库连接和权限"
    echo "================================================================================"
    echo ""
    exit 1
fi
