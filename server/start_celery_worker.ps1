# Celery Worker 启动脚本（PowerShell 版本）

Write-Host "Starting Celery Worker with AsyncIOPool..." -ForegroundColor Green
Write-Host "Note: Make sure virtual environment is activated before running this script" -ForegroundColor Yellow
Write-Host ""

# 设置 celery-aio-pool 环境变量（Celery 5.3+ 要求）
$env:CELERY_CUSTOM_WORKER_POOL = "celery_aio_pool.pool:AsyncIOPool"

# 使用 -P custom 启动 worker，Celery 会使用环境变量指定的池
& "$PSScriptRoot\.venv\Scripts\python.exe" -m celery -A backend.app.task.celery:celery_app worker -P custom -c 4 -l info --without-gossip --without-mingle
