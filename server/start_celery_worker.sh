#!/bin/bash
# Celery Worker 启动脚本（兼容 asyncio）

cd backend

# 激活虚拟环境
source ../.venv/Scripts/activate

# 使用 threads pool（兼容 asyncio.run()）
# 
# Pool 选择说明：
#   - threads: 线程池，兼容 asyncio.run()（推荐）
#   - gevent: 协程池，不兼容 asyncio.run()，性能好但有限制
#   - prefork: 进程池，兼容但开销大
#   - solo: 单进程，仅用于调试
#
# 如果你的项目配置了 celery_aio_pool，可以使用 gevent 并改任务为 async def

celery -A backend.app.task.celery:celery_app worker \
  -P threads \
  -c 4 \
  -l info \
  --without-gossip \
  --without-mingle
