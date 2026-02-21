#!/bin/bash
# Alembic 数据库迁移便捷脚本 (Bash 版本)
# 使用方法: ./migrate.sh [command]
# 示例: ./migrate.sh check
#       ./migrate.sh upgrade
#       ./migrate.sh current

set -e

COMMAND=${1:-check}

echo "🔧 执行 Alembic 命令: $COMMAND"
echo ""

# 检测是否在 Git Bash 环境
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows/Git Bash: 使用 python -m alembic
    ALEMBIC_CMD="python -m alembic"
else
    # Linux/Mac: 使用 uv run
    ALEMBIC_CMD="uv run alembic"
fi

case $COMMAND in
    check)
        echo "检查迁移链完整性..."
        $ALEMBIC_CMD check
        ;;
    current)
        echo "查看当前数据库版本..."
        $ALEMBIC_CMD current
        ;;
    history)
        echo "查看迁移历史..."
        $ALEMBIC_CMD history
        ;;
    upgrade)
        echo "⚠️  准备升级数据库到最新版本"
        echo "请确认已备份数据库！"
        read -p "是否继续? (y/N): " confirm
        if [[ $confirm == "y" || $confirm == "Y" ]]; then
            echo "执行升级..."
            $ALEMBIC_CMD upgrade head
            echo "✅ 升级完成！"
        else
            echo "已取消升级"
        fi
        ;;
    upgrade-one)
        echo "升级一个版本..."
        $ALEMBIC_CMD upgrade +1
        ;;
    downgrade)
        echo "⚠️  准备回滚一个版本"
        read -p "是否继续? (y/N): " confirm
        if [[ $confirm == "y" || $confirm == "Y" ]]; then
            echo "执行回滚..."
            $ALEMBIC_CMD downgrade -1
            echo "✅ 回滚完成！"
        else
            echo "已取消回滚"
        fi
        ;;
    heads)
        echo "查看 HEAD 版本..."
        $ALEMBIC_CMD heads
        ;;
    *)
        echo "未知命令: $COMMAND"
        echo ""
        echo "可用命令:"
        echo "  check        - 检查迁移链完整性"
        echo "  current      - 查看当前数据库版本"
        echo "  history      - 查看迁移历史"
        echo "  upgrade      - 升级到最新版本"
        echo "  upgrade-one  - 升级一个版本"
        echo "  downgrade    - 回滚一个版本"
        echo "  heads        - 查看 HEAD 版本"
        exit 1
        ;;
esac
