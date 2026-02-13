@echo off
REM Celery Worker 启动脚本（Windows 批处理版本）

cd backend

REM 激活虚拟环境
call ..\.venv\Scripts\activate.bat

REM 使用 threads pool（兼容 asyncio.run()）
celery -A backend.app.task.celery:celery_app worker -P threads -c 4 -l info --without-gossip --without-mingle

pause
