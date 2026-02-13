from backend.app.task.celery import celery_app
from backend.app.feedalyze.service.clustering_service import clustering_service
from backend.database.db import async_db_session


@celery_app.task(name='feedalyze_clustering_batch')
async def feedalyze_clustering_batch(
    tenant_id: str,
    max_feedbacks: int = 100,
    force_recluster: bool = False,
) -> dict:
    """
    Feedalyze 聚类批处理任务

    说明：
    - 复用 clustering_service 的核心逻辑，保证同步/异步行为一致
    - 任务结果会写入 Celery result_backend（DB），前端可通过 task_id 轮询状态
    """
    async with async_db_session() as db:
        return await clustering_service.trigger_clustering(
            db=db,
            tenant_id=tenant_id,
            max_feedbacks=max_feedbacks,
            force_recluster=force_recluster,
        )

