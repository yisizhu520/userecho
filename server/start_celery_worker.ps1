# Celery Worker 启动脚本（PowerShell 版本）

Write-Host "Starting Celery Worker with AsyncIOPool..." -ForegroundColor Green
Write-Host "Note: Make sure virtual environment is activated before running this script" -ForegroundColor Yellow
Write-Host ""

# 设置 celery-aio-pool 环境变量（Celery 5.3+ 要求）
$env:CELERY_CUSTOM_WORKER_POOL = "celery_aio_pool.pool:AsyncIOPool"

# 创建日志目录（如果不存在）
$logDir = "$PSScriptRoot\backend\log"
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

$logFile = "$logDir\celery_worker.log"

Write-Host "Environment Variables:" -ForegroundColor Cyan
Write-Host "  CELERY_CUSTOM_WORKER_POOL = $env:CELERY_CUSTOM_WORKER_POOL" -ForegroundColor Gray
Write-Host ""

Write-Host "Starting worker with parameters:" -ForegroundColor Cyan
Write-Host "  -A backend.app.task.celery:celery_app" -ForegroundColor Gray
Write-Host "  -P custom (AsyncIOPool)" -ForegroundColor Gray
Write-Host "  -c 4 (concurrency)" -ForegroundColor Gray
Write-Host "  -l info (log level)" -ForegroundColor Gray
Write-Host "  Output: Terminal + Log file" -ForegroundColor Gray
Write-Host ""

Write-Host "Log file: $logFile" -ForegroundColor Yellow
Write-Host ""

# 使用 -P custom 启动 worker，Celery 会使用环境变量指定的池
# 使用 Tee-Object 将输出同时写入文件和终端
& "$PSScriptRoot\.venv\Scripts\python.exe" -m celery -A backend.app.task.celery:celery_app worker -P custom -c 4 -l info --without-gossip --without-mingle 2>&1 | Tee-Object -FilePath $logFile
