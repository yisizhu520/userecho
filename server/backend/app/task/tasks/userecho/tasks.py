import asyncio

from backend.app.task.celery import celery_app
from backend.app.userecho.service.clustering_service import clustering_service
from backend.database.db import async_db_session


@celery_app.task(
    name='userecho_clustering_batch',
    bind=True,
    time_limit=600,  # 10分钟硬超时
    soft_time_limit=540,  # 9分钟软超时（优雅退出）
)
def userecho_clustering_batch(
    self,  # bind=True 提供 task 实例
    tenant_id: str,
    max_feedbacks: int = 100,
    force_recluster: bool = False,
) -> dict:
    """
    UserEcho 聚类批处理任务

    说明：
    - Celery 标准 Worker（非 gevent）不支持原生 async def，需要手动管理 event loop
    - 任务结果会写入 Celery result_backend（DB），前端可通过 task_id 轮询状态
    - time_limit: 10分钟硬超时，防止任务卡死
    - soft_time_limit: 9分钟软超时，给予任务优雅退出的机会
    
    Event Loop 管理：
    - 不使用 asyncio.run()，因为它会关闭 loop 导致第二次任务失败
    - 手动获取或创建 event loop，复用同一个 loop
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
    
    # 手动管理 event loop，避免 asyncio.run() 关闭 loop 的问题
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    # 运行异步任务，但不关闭 loop（让 Celery 管理生命周期）
    return loop.run_until_complete(_async_run())

