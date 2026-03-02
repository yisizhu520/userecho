"""任务追踪记录 CRUD"""

from datetime import datetime

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.task.model.task_record import TaskRecord


async def get_task_records(
    db: AsyncSession,
    *,
    tenant_id: str,
    category: str | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[TaskRecord], int]:
    """分页查询任务追踪记录"""
    query = select(TaskRecord).where(TaskRecord.tenant_id == tenant_id)

    if category:
        query = query.where(TaskRecord.task_category == category)
    if status:
        query = query.where(TaskRecord.status == status)

    # 总数
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # 分页
    query = query.order_by(TaskRecord.created_time.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    records = list(result.scalars().all())

    return records, total


async def get_task_record_by_celery_id(
    db: AsyncSession,
    celery_task_id: str,
) -> TaskRecord | None:
    """通过 Celery Task ID 查询"""
    result = await db.execute(select(TaskRecord).where(TaskRecord.celery_task_id == celery_task_id))
    return result.scalars().first()


async def get_task_stats(
    db: AsyncSession,
    *,
    tenant_id: str,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
) -> dict:
    """获取任务统计（仪表盘数据）"""
    base_filter = TaskRecord.tenant_id == tenant_id
    time_filters = []
    if start_time:
        time_filters.append(TaskRecord.created_time >= start_time)
    if end_time:
        time_filters.append(TaskRecord.created_time <= end_time)

    all_filters = [base_filter, *time_filters]

    # 按状态统计
    status_query = (
        select(TaskRecord.status, func.count().label("count"))
        .where(*all_filters)
        .group_by(TaskRecord.status)
    )
    status_result = await db.execute(status_query)
    status_counts = {row.status: row.count for row in status_result}

    # 按分类统计
    category_query = (
        select(
            TaskRecord.task_category,
            func.count().label("total"),
            func.count().filter(TaskRecord.status == "success").label("success"),
            func.count().filter(TaskRecord.status == "failure").label("failure"),
            func.avg(TaskRecord.duration_ms).filter(TaskRecord.status == "success").label("avg_duration_ms"),
        )
        .where(*all_filters)
        .group_by(TaskRecord.task_category)
    )
    category_result = await db.execute(category_query)
    categories = [
        {
            "category": row.task_category,
            "total": row.total,
            "success": row.success,
            "failure": row.failure,
            "avg_duration_ms": round(row.avg_duration_ms) if row.avg_duration_ms else None,
        }
        for row in category_result
    ]

    # 最近失败的任务
    recent_failures_query = (
        select(TaskRecord)
        .where(*all_filters, TaskRecord.status == "failure")
        .order_by(TaskRecord.created_time.desc())
        .limit(5)
    )
    recent_failures_result = await db.execute(recent_failures_query)
    recent_failures = [
        {
            "celery_task_id": r.celery_task_id,
            "task_display_name": r.task_display_name,
            "error_message": (r.error_message or "")[:200],
            "created_time": r.created_time.isoformat() if r.created_time else None,
        }
        for r in recent_failures_result.scalars()
    ]

    return {
        "status_counts": status_counts,
        "categories": categories,
        "recent_failures": recent_failures,
        "total": sum(status_counts.values()),
    }


async def get_task_category_list(
    db: AsyncSession,
    tenant_id: str,
) -> list[dict]:
    """获取所有任务分类（用于筛选下拉）"""
    query = (
        select(TaskRecord.task_category, func.count().label("count"))
        .where(TaskRecord.tenant_id == tenant_id)
        .group_by(TaskRecord.task_category)
        .order_by(text("count DESC"))
    )
    result = await db.execute(query)
    return [{"category": row.task_category, "count": row.count} for row in result]
