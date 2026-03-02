"""统一任务追踪 API

提供所有异步任务（单任务 + 批量任务）的查询、统计接口。
替代之前分散在各模块的 task status 查询。
"""

from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Query

from backend.app.task.crud.task_record import (
    get_task_category_list,
    get_task_record_by_celery_id,
    get_task_records,
    get_task_stats,
)
from backend.app.task.registry import TASK_METADATA
from backend.common.response.response_schema import response_base
from backend.common.security.jwt import CurrentTenantId, DependsJwtAuth
from backend.database.db import CurrentSession

router = APIRouter(prefix="/task-records", tags=["任务追踪"], dependencies=[DependsJwtAuth])


@router.get("", summary="查询任务追踪列表")
async def list_task_records(
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
    category: Annotated[str | None, Query(description="任务分类筛选")] = None,
    status: Annotated[str | None, Query(description="状态筛选：pending/started/success/failure/retry")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> Any:
    """
    查询任务追踪记录列表

    支持按分类、状态筛选，分页返回。
    """
    records, total = await get_task_records(
        db,
        tenant_id=tenant_id,
        category=category,
        status=status,
        page=page,
        page_size=page_size,
    )

    items = [
        {
            "id": r.id,
            "celery_task_id": r.celery_task_id,
            "celery_task_name": r.celery_task_name,
            "task_category": r.task_category,
            "task_display_name": r.task_display_name,
            "status": r.status,
            "context": r.context,
            "result_summary": r.result_summary,
            "batch_job_id": r.batch_job_id,
            "duration_ms": r.duration_ms,
            "error_message": r.error_message,
            "created_time": r.created_time.isoformat() if r.created_time else None,
            "started_time": r.started_time.isoformat() if r.started_time else None,
            "completed_time": r.completed_time.isoformat() if r.completed_time else None,
        }
        for r in records
    ]

    return response_base.success(
        data={
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )


@router.get("/stats", summary="任务统计")
async def task_statistics(
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
    start_time: Annotated[datetime | None, Query(description="开始时间")] = None,
    end_time: Annotated[datetime | None, Query(description="结束时间")] = None,
) -> Any:
    """
    获取任务统计数据（仪表盘用）

    返回各分类的成功/失败数量、平均耗时、最近失败记录。
    """
    stats = await get_task_stats(
        db,
        tenant_id=tenant_id,
        start_time=start_time,
        end_time=end_time,
    )
    return response_base.success(data=stats)


@router.get("/categories", summary="获取任务分类列表")
async def list_categories(
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
) -> Any:
    """获取所有任务分类（用于前端筛选下拉）"""
    categories = await get_task_category_list(db, tenant_id)
    return response_base.success(data=categories)


@router.get("/metadata", summary="获取任务元数据定义")
async def list_task_metadata() -> Any:
    """获取所有已注册的任务元数据（前端展示用）"""
    metadata = [
        {
            "task_name": name,
            "category": meta.category,
            "display_name": meta.display_name,
        }
        for name, meta in TASK_METADATA.items()
    ]
    return response_base.success(data=metadata)


@router.get("/{celery_task_id}", summary="查询单个任务详情")
async def get_task_detail(
    celery_task_id: str,
    db: CurrentSession,
) -> Any:
    """
    通过 Celery Task ID 查询任务详情

    同时返回 task_record 审计信息和 Celery 原始状态。
    """
    record = await get_task_record_by_celery_id(db, celery_task_id)

    # 同时查询 Celery 原始状态
    from backend.app.task.celery import celery_app

    celery_result = celery_app.AsyncResult(celery_task_id)
    celery_state = celery_result.state

    if record:
        data = {
            "id": record.id,
            "celery_task_id": record.celery_task_id,
            "celery_task_name": record.celery_task_name,
            "task_category": record.task_category,
            "task_display_name": record.task_display_name,
            "status": record.status,
            "celery_state": celery_state,
            "context": record.context,
            "result_summary": record.result_summary,
            "batch_job_id": record.batch_job_id,
            "duration_ms": record.duration_ms,
            "error_message": record.error_message,
            "created_time": record.created_time.isoformat() if record.created_time else None,
            "started_time": record.started_time.isoformat() if record.started_time else None,
            "completed_time": record.completed_time.isoformat() if record.completed_time else None,
        }
    else:
        # 没有 task_record，只返回 Celery 原始信息
        data = {
            "celery_task_id": celery_task_id,
            "celery_state": celery_state,
            "result": celery_result.result if celery_result.successful() else None,
            "error": str(celery_result.result) if celery_result.failed() else None,
        }

    return response_base.success(data=data)
