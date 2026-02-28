from fastapi import APIRouter

from backend.app.admin.api.router import v1 as admin_v1
from backend.app.task.api.router import v1 as task_v1
from backend.app.userecho.api.router import v1 as userecho_v1

# 导入批量任务处理器注册（确保处理器在应用启动时被注册）
from backend.app.batch.handler import registry as _  # noqa: F401

router = APIRouter()

router.include_router(admin_v1)
router.include_router(task_v1)
router.include_router(userecho_v1)
