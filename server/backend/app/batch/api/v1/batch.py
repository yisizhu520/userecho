"""批量任务 API 接口"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.common.security.jwt import CurrentTenantId, CurrentUserId
from backend.app.batch.service.batch_service import (
    cancel_batch_job,
    create_batch_job,
    enqueue_batch_job,
    get_batch_progress,
    get_batch_results,
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
            created_by=str(user_id),
        )
        batch_job_id = batch_job.id

        # 强制提交当前事务，确保数据持久化到数据库
        await db.commit()

        # 现在数据已经在数据库中，触发 Celery 任务
        celery_task_id = await enqueue_batch_job(batch_job_id)

        return response_base.success(data={"batch_id": batch_job_id, "celery_task_id": celery_task_id})
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


@router.get("/jobs/{batch_id}/results", summary="获取批量任务详细结果")
async def get_job_results(
    batch_id: str,
    db: CurrentSession,
    status: str | None = None,
):
    """获取批量任务的详细结果列表"""

    try:
        results = await get_batch_results(db, batch_id, status=status)
        return response_base.success(data=results)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/jobs/{batch_id}/items", summary="获取批量任务项列表")
async def get_job_items(
    batch_id: str,
    db: CurrentSession,
):
    """获取批量任务的所有任务项"""
    from sqlalchemy import select
    from backend.app.batch.model.batch_job import BatchTaskItem

    try:
        result = await db.execute(
            select(BatchTaskItem).where(BatchTaskItem.batch_job_id == batch_id).order_by(BatchTaskItem.sequence_no)
        )
        items = result.scalars().all()

        return response_base.success(
            data=[
                {
                    "id": item.id,
                    "batch_job_id": item.batch_job_id,
                    "sequence_no": item.sequence_no,
                    "input_data": item.input_data,
                    "output_data": item.output_data,
                    "status": item.status,
                    "error_message": item.error_message,
                    "error_code": item.error_code,
                    "retry_count": item.retry_count,
                    "max_retries": item.max_retries,
                    "created_time": item.create_time.isoformat() if item.create_time else None,
                    "started_time": item.started_time.isoformat() if item.started_time else None,
                    "completed_time": item.completed_time.isoformat() if item.completed_time else None,
                }
                for item in items
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/jobs/{batch_id}/retry", summary="重试失败的任务项")
async def retry_job(
    batch_id: str,
    db: CurrentSession,
):
    """重试批量任务中失败的任务项"""
    from sqlalchemy import select
    from backend.app.batch.model.batch_job import BatchJob, BatchTaskItem, TaskItemStatus

    try:
        # 获取批量任务
        batch_job = await db.get(BatchJob, batch_id)
        if not batch_job:
            raise HTTPException(status_code=404, detail=f"Batch job {batch_id} not found")

        # 将失败的任务项重置为待处理
        result = await db.execute(
            select(BatchTaskItem)
            .where(BatchTaskItem.batch_job_id == batch_id)
            .where(BatchTaskItem.status == TaskItemStatus.FAILED)
        )
        failed_items = list(result.scalars())

        if not failed_items:
            return response_base.success(data={"message": "No failed items to retry", "retry_count": 0})

        # 重置失败的任务项
        for item in failed_items:
            item.status = TaskItemStatus.PENDING
            item.error_message = None
            item.error_code = None
            item.started_time = None
            item.completed_time = None

        # 更新批量任务统计
        batch_job.failed_count -= len(failed_items)
        batch_job.pending_count += len(failed_items)

        await db.commit()

        # 重新触发 Celery 任务
        celery_task_id = await enqueue_batch_job(batch_id)

        return response_base.success(
            data={
                "message": f"Retrying {len(failed_items)} failed items",
                "retry_count": len(failed_items),
                "celery_task_id": celery_task_id,
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


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


class ScreenshotBatchUploadRequest(BaseModel):
    """批量截图识别请求"""

    image_urls: list[str]
    board_id: str
    author_type: str  # 'customer' | 'external'
    # 内部客户模式
    default_customer_name: str | None = None
    # 外部用户模式
    source_platform: str | None = None
    default_user_name: str | None = None


@router.post("/feedbacks/screenshot-batch-upload", summary="批量上传截图")
async def screenshot_batch_upload(
    data: ScreenshotBatchUploadRequest,
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
    user_id: str = CurrentUserId,
):
    """
    批量截图识别（前端直传模式）

    前端流程：
    1. 并发上传所有图片到 OSS
    2. 收集所有 CDN URL
    3. 调用本接口传递 URL 列表 + 配置

    后端流程：
    1. 创建批量任务
    2. Celery 异步识别所有截图
    3. 自动创建反馈（使用预设配置）
    """
    from backend.utils.timezone import timezone

    if not data.image_urls:
        raise HTTPException(status_code=400, detail="image_urls cannot be empty")

    if len(data.image_urls) > 50:
        raise HTTPException(status_code=400, detail="最多支持 50 张截图")

    # 构建任务项（每个 URL 一个任务）
    items = []
    for image_url in data.image_urls:
        item = {
            "image_url": image_url,
            "board_id": data.board_id,
            "author_type": data.author_type,
        }

        # 根据来源类型附加配置
        if data.author_type == "customer":
            item["default_customer_name"] = data.default_customer_name
        else:
            item["source_platform"] = data.source_platform
            item["default_user_name"] = data.default_user_name

        items.append(item)

    # 创建批量任务
    batch_job = await create_batch_job(
        db=db,
        tenant_id=tenant_id,
        task_type="screenshot_recognition",
        items=items,
        name=f"批量截图识别 {timezone.now().strftime('%Y-%m-%d %H:%M')}",
        created_by=str(user_id),
    )
    batch_job_id = batch_job.id

    # 强制提交当前事务，确保数据持久化到数据库
    await db.commit()

    # 现在数据已经在数据库中，触发 Celery 任务
    celery_task_id = await enqueue_batch_job(batch_job_id)

    return response_base.success(
        data={
            "batch_id": batch_job_id,
            "celery_task_id": celery_task_id,
            "total_count": len(items),
        }
    )
