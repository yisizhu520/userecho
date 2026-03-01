# 使用 .env 配置初始化数据脚本（PowerShell 版本）
# 执行方式：.\init_data.ps1

$ErrorActionPreference = "Stop"

# 确保使用 .env 而不是 .env.demo
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:ENV_FILE = Join-Path $ScriptDir ".env"

Write-Host "ℹ️  使用配置文件: $env:ENV_FILE" -ForegroundColor Blue
Write-Host ""

# 设置 Python 路径
$Python = Join-Path $ScriptDir ".." ".venv" "Scripts" "python.exe"

if (-not (Test-Path $Python)) {
    $Python = "python"
}

Write-Host "ℹ️  使用 Python: $Python" -ForegroundColor Blue
Write-Host ""

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "🚀 开始初始化数据（使用 .env 配置）" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# 步骤 1: 创建默认租户和看板
Write-Host "步骤 1/5: 创建默认租户和看板" -ForegroundColor Yellow
Write-Host "--------------------------------------------------------------------------------"
& $Python scripts/init_default_tenant.py
if ($LASTEXITCODE -ne 0) { throw "默认租户创建失败" }
Write-Host "✅ 默认租户和看板创建完成" -ForegroundColor Green
Write-Host ""

# 步骤 2: 初始化业务菜单和角色
Write-Host "步骤 2/5: 初始化业务菜单和角色" -ForegroundColor Yellow
Write-Host "--------------------------------------------------------------------------------"
& $Python scripts/init_business_menus.py
if ($LASTEXITCODE -ne 0) { throw "业务菜单初始化失败" }
Write-Host "✅ 业务菜单和角色初始化完成" -ForegroundColor Green
Write-Host ""

# 步骤 3: 添加额外系统管理菜单
Write-Host "步骤 3/5: 添加额外系统管理菜单" -ForegroundColor Yellow
Write-Host "--------------------------------------------------------------------------------"
& $Python scripts/init_system_extra_menus.py
if ($LASTEXITCODE -ne 0) { throw "额外系统菜单初始化失败" }
Write-Host "✅ 额外系统菜单初始化完成" -ForegroundColor Green
Write-Host ""

# 步骤 4: 初始化订阅套餐
Write-Host "步骤 4/5: 初始化订阅套餐" -ForegroundColor Yellow
Write-Host "--------------------------------------------------------------------------------"
& $Python scripts/init_subscription_plans.py
if ($LASTEXITCODE -ne 0) { throw "订阅套餐初始化失败" }
Write-Host "✅ 订阅套餐初始化完成" -ForegroundColor Green
Write-Host ""

# 步骤 5: 创建测试用户
Write-Host "步骤 5/5: 创建测试用户" -ForegroundColor Yellow
Write-Host "--------------------------------------------------------------------------------"
& $Python scripts/create_test_users.py
if ($LASTEXITCODE -ne 0) { throw "测试用户创建失败" }
Write-Host "✅ 测试用户创建完成" -ForegroundColor Green
Write-Host ""

# 验证结果
Write-Host "步骤 6/6: 验证初始化结果" -ForegroundColor Yellow
Write-Host "--------------------------------------------------------------------------------"
& $Python verify_data.py
Write-Host ""

Write-Host "================================================================================" -ForegroundColor Green
Write-Host "✅ 数据初始化完成！" -ForegroundColor Green
Write-Host "================================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "📝 登录信息：" -ForegroundColor Cyan
Write-Host "  超级管理员: admin / Admin123456"
Write-Host "  测试账号: sysadmin, pm, cs, dev, boss, hybrid / Test123456"
Write-Host ""
