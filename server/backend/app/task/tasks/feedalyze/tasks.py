import asyncio

from backend.app.task.celery import celery_app
from backend.app.feedalyze.service.clustering_service import clustering_service
from backend.database.db import async_db_session


@celery_app.task(
    name='feedalyze_clustering_batch',
    bind=True,
    time_limit=600,  # 10分钟硬超时
    soft_time_limit=540,  # 9分钟软超时（优雅退出）
)
def feedalyze_clustering_batch(
    self,  # bind=True 提供 task 实例
    tenant_id: str,
    max_feedbacks: int = 100,
    force_recluster: bool = False,
) -> dict:
    """
    Feedalyze 聚类批处理任务

    说明：
    - Celery 标准 Worker（非 gevent）不支持原生 async def，使用 asyncio.run() 包装
    - 任务结果会写入 Celery result_backend（DB），前端可通过 task_id 轮询状态
    - time_limit: 10分钟硬超时，防止任务卡死
    - soft_time_limit: 9分钟软超时，给予任务优雅退出的机会
    
    注意：如果你的 Worker 使用 celery_aio_pool，可以改回 async def
    """
    async def _async_run():
        """异步执行聚类任务"""
        async with async_db_session() as db:
            return await clustering_service.trigger_clustering(
                db=db,
                tenant_id=tenant_id,
                max_feedbacks=max_feedbacks,
                force_recluster=force_recluster,
            )
    
    # 在同步上下文中运行异步代码
    # asyncio.run() 会创建新的事件循环，避免与 Celery 冲突
    return asyncio.run(_async_run())

