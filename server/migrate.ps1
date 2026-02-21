# Alembic 数据库迁移便捷脚本
# 使用方法: .\migrate.ps1 [command]
# 示例: .\migrate.ps1 check
#       .\migrate.ps1 upgrade
#       .\migrate.ps1 current

param(
    [Parameter(Position=0)]
    [string]$Command = "check"
)

$ErrorActionPreference = "Stop"

Write-Host "🔧 执行 Alembic 命令: $Command" -ForegroundColor Cyan
Write-Host ""

switch ($Command) {
    "check" {
        Write-Host "检查迁移链完整性..." -ForegroundColor Yellow
        uv run alembic check
    }
    "current" {
        Write-Host "查看当前数据库版本..." -ForegroundColor Yellow
        uv run alembic current
    }
    "history" {
        Write-Host "查看迁移历史..." -ForegroundColor Yellow
        uv run alembic history
    }
    "upgrade" {
        Write-Host "⚠️  准备升级数据库到最新版本" -ForegroundColor Red
        Write-Host "请确认已备份数据库！" -ForegroundColor Red
        $confirm = Read-Host "是否继续? (y/N)"
        if ($confirm -eq "y" -or $confirm -eq "Y") {
            Write-Host "执行升级..." -ForegroundColor Green
            uv run alembic upgrade head
            Write-Host "✅ 升级完成！" -ForegroundColor Green
        } else {
            Write-Host "已取消升级" -ForegroundColor Yellow
        }
    }
    "upgrade-one" {
        Write-Host "升级一个版本..." -ForegroundColor Yellow
        uv run alembic upgrade +1
    }
    "downgrade" {
        Write-Host "⚠️  准备回滚一个版本" -ForegroundColor Red
        $confirm = Read-Host "是否继续? (y/N)"
        if ($confirm -eq "y" -or $confirm -eq "Y") {
            Write-Host "执行回滚..." -ForegroundColor Yellow
            uv run alembic downgrade -1
            Write-Host "✅ 回滚完成！" -ForegroundColor Green
        } else {
            Write-Host "已取消回滚" -ForegroundColor Yellow
        }
    }
    "heads" {
        Write-Host "查看 HEAD 版本..." -ForegroundColor Yellow
        uv run alembic heads
    }
    default {
        Write-Host "未知命令: $Command" -ForegroundColor Red
        Write-Host ""
        Write-Host "可用命令:" -ForegroundColor Cyan
        Write-Host "  check        - 检查迁移链完整性"
        Write-Host "  current      - 查看当前数据库版本"
        Write-Host "  history      - 查看迁移历史"
        Write-Host "  upgrade      - 升级到最新版本"
        Write-Host "  upgrade-one  - 升级一个版本"
        Write-Host "  downgrade    - 回滚一个版本"
        Write-Host "  heads        - 查看 HEAD 版本"
    }
}
