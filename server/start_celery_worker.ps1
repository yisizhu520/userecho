# Celery Worker 启动脚本（PowerShell 版本）

Write-Host "Starting Celery Worker..." -ForegroundColor Green
Write-Host "Note: Make sure virtual environment is activated before running this script" -ForegroundColor Yellow
Write-Host ""

# 使用虚拟环境的 Python 通过 -m 调用 celery（避免 Windows 脚本路径问题）
# 使用 threads pool（兼容 asyncio.run()）
& "$PSScriptRoot\.venv\Scripts\python.exe" -m celery -A backend.app.task.celery:celery_app worker -P threads -c 4 -l info --without-gossip --without-mingle
