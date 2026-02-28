"""批量任务 API 接口"""

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from pydantic import BaseModel

from backend.common.security.jwt import CurrentTenantId, CurrentUserId
from backend.app.batch.service.batch_service import (
    cancel_batch_job,
    create_batch_job,
    enqueue_batch_job,
    get_batch_progress,
    list_batch_jobs,
)
from backend.common.response.response_schema import response_base
from backend.database.db import CurrentSession

router = APIRouter(prefix="/batch", tags=["批量任务"])


class BatchJobCreate(BaseModel):
    """创建批量任务请求"""

    task_type: str
    name: str | None = None
    items: list[dict]
    config: dict | None = None


@router.post("/jobs", summary="创建批量任务")
async def create_job(
    data: BatchJobCreate,
    background_tasks: BackgroundTasks,
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
    user_id: str = CurrentUserId,
):
    """
    创建批量任务（通用接口）

    Request Body:
    ```json
    {
      "task_type": "screenshot_recognition",
      "name": "批量导入截图 2024-01-26",
      "items": [
        {"image_url": "https://..."},
        {"image_url": "https://..."}
      ],
      "config": {
        "max_retries": 3
      }
    }
    ```
    """

    try:
        batch_job = await create_batch_job(
            db=db,
            tenant_id=tenant_id,
            task_type=data.task_type,
            items=data.items,
            name=data.name,
            config=data.config,
            created_by=user_id,
        )

        background_tasks.add_task(enqueue_batch_job, batch_job.id)
        return response_base.success(data={"batch_id": batch_job.id, "celery_task_id": None})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/jobs/{batch_id}", summary="查询批量任务进度")
async def get_job_progress(
    batch_id: str,
    db: CurrentSession,
):
    """查询批量任务进度（通用接口）"""

    try:
        progress = await get_batch_progress(db, batch_id)
        return response_base.success(data=progress)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/jobs/{batch_id}", summary="取消批量任务")
async def cancel_job(
    batch_id: str,
    db: CurrentSession,
):
    """取消批量任务"""

    try:
        await cancel_batch_job(db, batch_id)
        return response_base.success()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/jobs", summary="查询批量任务列表")
async def list_jobs(
    db: CurrentSession,
    task_type: str | None = None,
    tenant_id: str = CurrentTenantId,
    page: int = 1,
    page_size: int = 20,
):
    """查询批量任务列表"""

    jobs = await list_batch_jobs(
        db=db,
        tenant_id=tenant_id,
        task_type=task_type,
        page=page,
        page_size=page_size,
    )

    return response_base.success(data=jobs)


# ============================================================
# 业务特定的便捷接口
# ============================================================


@router.post("/feedbacks/screenshot-batch-upload", summary="批量上传截图")
async def screenshot_batch_upload(
    db: CurrentSession,
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    board_id: str | None = None,
    tenant_id: str = CurrentTenantId,
    user_id: str = CurrentUserId,
):
    """批量上传截图（便捷接口）"""
    from backend.utils.storage import storage
    from backend.utils.timezone import timezone

    # 1. 上传文件到 OSS
    items = []
    for file in files:
        # 上传到 OSS
        storage_path = f"screenshots/{tenant_id}/{timezone.now().strftime('%Y%m%d')}/{file.filename}"
        image_url = await storage.upload(file.file, storage_path, content_type=file.content_type)

        items.append(
            {
                "image_url": image_url,
                "board_id": board_id,
            }
        )

    # 2. 创建批量任务
    batch_job = await create_batch_job(
        db=db,
        tenant_id=tenant_id,
        task_type="screenshot_recognition",
        items=items,
        name=f"批量截图识别 {timezone.now().strftime('%Y-%m-%d %H:%M')}",
        created_by=user_id,
    )

    background_tasks.add_task(enqueue_batch_job, batch_job.id)

    return response_base.success(
        data={
            "batch_id": batch_job.id,
            "celery_task_id": None,
            "total_count": len(items),
        }
    )
