"""统一任务中心 API"""

from fastapi import APIRouter, HTTPException

from backend.app.task.schema.unified_task import TaskStatus, TaskType
from backend.app.task.service.unified_task_service import (
    cancel_unified_task,
    get_unified_task_by_id,
    get_unified_tasks,
    retry_unified_task,
)
from backend.common.response.response_schema import response_base
from backend.common.security.jwt import CurrentTenantId
from backend.database.db import CurrentSession

router = APIRouter(prefix="/tasks", tags=["统一任务中心"])


@router.get("", summary="获取任务列表")
async def list_tasks(
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
    task_type: TaskType | None = None,
    status: TaskStatus | None = None,
    page: int = 1,
    page_size: int = 20,
):
    """
    获取所有任务列表（批处理 + 单任务）

    - 统一展示批处理任务和单任务
    - 支持按类型和状态筛选
    - 按创建时间倒序排列
    """

    tasks = await get_unified_tasks(
        db=db,
        tenant_id=tenant_id,
        task_type=task_type,
        status=status,
        page=page,
        page_size=page_size,
    )

    return response_base.success(data=tasks.model_dump())


@router.get("/{task_id}", summary="获取任务详情")
async def get_task(
    task_id: str,
    db: CurrentSession,
):
    """获取任务详情（自动识别批处理任务或单任务）"""

    task = await get_unified_task_by_id(db, task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return response_base.success(data=task.model_dump())


@router.post("/{task_id}/cancel", summary="取消任务")
async def cancel_task(
    task_id: str,
    db: CurrentSession,
):
    """取消任务（支持批处理任务和单任务）"""

    success = await cancel_unified_task(db, task_id)

    if not success:
        raise HTTPException(status_code=404, detail="Task not found or cannot be cancelled")

    return response_base.success()


@router.post("/{task_id}/retry", summary="重试任务")
async def retry_task(
    task_id: str,
    db: CurrentSession,
):
    """重试失败的任务（支持批处理任务和单任务）"""

    new_task_id = await retry_unified_task(db, task_id)

    if not new_task_id:
        raise HTTPException(status_code=404, detail="Task not found or cannot be retried")

    return response_base.success(data={"new_task_id": new_task_id})
