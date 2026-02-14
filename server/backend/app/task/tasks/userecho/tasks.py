import asyncio
import os
import uuid

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


@celery_app.task(
    name='userecho_analyze_screenshot',
    bind=True,
    max_retries=2,
    default_retry_delay=5,
    time_limit=120,  # 2分钟硬超时
)
def analyze_screenshot_task(
    self,
    file_path: str,
    content_type: str,
    tenant_id: str,
    original_filename: str,
) -> dict:
    """
    异步分析截图
    
    说明：
    - 从临时文件读取 → 上传 OSS → AI 识别 → 清理临时文件
    - 失败自动重试（最多 2 次）
    - 手动管理 event loop（与聚类任务相同）
    
    Args:
        file_path: 临时文件路径
        content_type: 文件 MIME 类型
        tenant_id: 租户 ID
        original_filename: 原始文件名
    
    Returns:
        {
            'screenshot_url': str,
            'extracted': {...}  # AI 提取的信息
        }
    """
    from backend.utils.storage import storage
    from backend.utils.ai_client import ai_client
    from backend.common.log import log
    
    async def _async_run():
        """异步执行上传和识别"""
        try:
            # 1. 读取临时文件
            if not os.path.exists(file_path):
                raise FileNotFoundError(f'临时文件不存在: {file_path}')
            
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            # 2. 上传到 OSS
            file_ext = original_filename.split('.')[-1].lower() if '.' in original_filename else 'jpg'
            storage_path = f'screenshots/{tenant_id}/{uuid.uuid4()}.{file_ext}'
            
            from io import BytesIO
            file_obj = BytesIO(file_content)
            
            log.info(f'[Task {self.request.id}] Uploading screenshot to OSS: {storage_path}')
            screenshot_url = await storage.upload(file_obj, storage_path, content_type=content_type)
            log.info(f'[Task {self.request.id}] Screenshot uploaded: {screenshot_url}')
            
            # 3. AI 识别
            log.info(f'[Task {self.request.id}] Analyzing screenshot with AI')
            extracted_data = await ai_client.analyze_screenshot(screenshot_url)
            log.info(f'[Task {self.request.id}] Analysis completed: confidence={extracted_data.get("confidence", 0)}')
            
            return {
                'screenshot_url': screenshot_url,
                'extracted': extracted_data,
            }
            
        finally:
            # 4. 清理临时文件（无论成功或失败）
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    log.info(f'[Task {self.request.id}] Cleaned up temp file: {file_path}')
                except Exception as e:
                    log.warning(f'[Task {self.request.id}] Failed to remove temp file: {e}')
    
    # 手动管理 event loop（与聚类任务相同模式）
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    # 运行异步任务
    try:
        return loop.run_until_complete(_async_run())
    except Exception as e:
        log.error(f'[Task {self.request.id}] Screenshot analysis failed: {e}')
        # 重试机制（Celery 会自动处理）
        raise self.retry(exc=e)

