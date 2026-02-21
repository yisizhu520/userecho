import asyncio
import os
import pathlib
import uuid
from typing import Any

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
    from backend.common.log import log
    from backend.utils.ai_client import ai_client
    from backend.utils.storage import storage

    async def _async_run():
        """异步执行上传和识别"""
        try:
            # 1. 读取临时文件
            if not os.path.exists(file_path):
                raise FileNotFoundError(f'临时文件不存在: {file_path}')

            file_content = pathlib.Path(file_path).read_bytes()

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

            # 4. 记录积分消耗
            try:
                from backend.app.userecho.service.credits_service import credits_service

                async with async_db_session() as db:
                    await credits_service.consume(
                        db=db,
                        tenant_id=tenant_id,
                        operation_type='screenshot',
                        count=1,
                        description='截图识别',
                        extra_data={'confidence': extracted_data.get('confidence', 0)},
                    )
            except Exception as e:
                log.warning(f'Failed to record credits for screenshot task: {e}')

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


@celery_app.task(
    name='userecho.generate_insight_report',
    bind=True,
    time_limit=300,  # 5分钟硬超时
    soft_time_limit=270,  # 4.5分钟软超时
)
async def generate_insight_report(self, tenant_id: str, time_range: str = 'this_week', format: str = 'markdown'):
    """
    按需生成洞察报告（用户触发）

    使用 celery-aio-pool 的 AsyncIOPool，任务可以直接定义为 async def，
    celery-aio-pool 会自动管理事件循环。

    Args:
        tenant_id: 租户ID
        time_range: 时间范围
        format: 导出格式

    Returns:
        生成的报告内容
    """
    from backend.app.userecho.crud.crud_insight import crud_insight
    from backend.app.userecho.service.insight_service import insight_service
    from backend.common.log import log

    try:
        # 更新任务状态为进行中
        self.update_state(state='PROGRESS', meta={'current': 0, 'total': 100, 'status': '正在生成报告...'})

        async with async_db_session() as db:
            log.info(f'[Task {self.request.id}] Starting insight report generation for tenant: {tenant_id}')

            # 生成洞察（直接调用内部方法，避免触发新的异步任务）
            start_date, end_date = insight_service._parse_time_range(time_range)
            content = await insight_service._generate_weekly_report(
                db=db,
                tenant_id=tenant_id,
                start_date=start_date,
                end_date=end_date,
            )

            # 持久化到缓存
            await crud_insight.create_insight(
                db=db,
                tenant_id=tenant_id,
                insight_type='weekly_report',
                time_range=time_range,
                start_date=start_date.date(),
                end_date=end_date.date(),
                content=content,
                generated_by='hybrid',
                execution_time_ms=0,
            )

            await db.commit()

            log.info(f'[Task {self.request.id}] Completed insight report generation for tenant: {tenant_id}')

            # 返回结果 - 同时返回 markdown 和 结构化数据
            return {
                'markdown': content.get('markdown', ''),
                'data': content.get('data', {}),
                'generated_at': content.get('generated_at', ''),
                'format': format,
                'status': 'success',
            }

    except Exception as e:
        log.error(f'[Task {self.request.id}] Failed to generate insight report for tenant {tenant_id}: {e}')
        raise


@celery_app.task(
    name='userecho.generate_feedback_summary',
    bind=True,
    max_retries=3,
    default_retry_delay=10,
    time_limit=60,  # 1分钟硬超时
)
def generate_feedback_summary_task(
    self: Any,
    feedback_id: str,
    content: str,
    tenant_id: str,
) -> dict:
    """
    异步生成反馈摘要

    Args:
        self: Task 实例
        feedback_id: 反馈ID
        content: 反馈内容
        tenant_id: 租户ID

    Returns:
        {
            'feedback_id': str,
            'summary': str
        }
    """
    from backend.app.userecho.crud import crud_feedback
    from backend.common.log import log
    from backend.utils.ai_client import ai_client

    async def _async_run() -> dict:
        """异步执行摘要生成"""
        try:
            # 1. 生成摘要
            log.info(f'[Task {self.request.id}] Generating summary for feedback {feedback_id} (tenant={tenant_id})')
            # 限制摘要生成的最长内容，避免过长文本消耗过多 Token
            summary = await ai_client.generate_summary(content, max_length=20)

            # 2. 更新数据库
            async with async_db_session() as db:
                await crud_feedback.update(db=db, tenant_id=tenant_id, id=feedback_id, ai_summary=summary)

            log.info(f'[Task {self.request.id}] Summary generated for feedback {feedback_id}: {summary}')

            # 记录积分消耗
            try:
                from backend.app.userecho.service.credits_service import credits_service

                async with async_db_session() as db:
                    await credits_service.consume(
                        db=db,
                        tenant_id=tenant_id,
                        operation_type='summary',
                        count=1,
                        description='AI 摘要生成',
                        extra_data={'feedback_id': feedback_id},
                    )
            except Exception as e:
                log.warning(f'Failed to record credits for summary task: {e}')

            return {'feedback_id': feedback_id, 'summary': summary}

        except Exception as e:
            log.error(f'[Task {self.request.id}] Failed to generate summary for feedback {feedback_id}: {e}')
            raise self.retry(exc=e)

    # 手动管理 event loop（与其他任务相同模式）
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # 运行异步任务
    return loop.run_until_complete(_async_run())
