"""UserEcho API 路由"""

from fastapi import APIRouter

from backend.app.userecho.api.v1 import (
    clustering,
    customer,
    feedback,
    priority,
    topic,
)
from backend.core.conf import settings

# 创建 v1 路由 - 使用 /app 前缀（业务功能区）
v1 = APIRouter(prefix=f'{settings.FASTAPI_API_V1_PATH}/app', tags=['Business'])

# 注册所有子路由
v1.include_router(feedback.router)
v1.include_router(topic.router)
v1.include_router(customer.router)
v1.include_router(clustering.router)
v1.include_router(priority.router)
