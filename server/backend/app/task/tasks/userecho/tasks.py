import asyncio
import os
import pathlib
import uuid

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from celery import shared_task
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.userecho.service.clustering_service import clustering_service
from backend.database.db import SQLALCHEMY_DATABASE_URL, create_async_engine_and_session


def _get_or_create_event_loop() -> asyncio.AbstractEventLoop:
    """获取或创建事件循环（Celery 任务复用）"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop


@asynccontextmanager
async def local_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    创建本地数据库会话（用于 Celery 任务）- 自动管理事务

    解决问题：
    全局 `async_engine` 绑定在主线程/主进程的事件循环上。
    Celery 任务运行时（特别是手动管理 loop 时），会因为 loop 不匹配导致
    `RuntimeError: Task ... got Future ... attached to a different loop`。

    此上下文管理器会在每次调用时创建一个全新的 engine 和 session，
    确保它们绑定到当前任务的 event loop 上。

    ✅ Linus 优化：使用 .begin() 自动管理事务
    - 进入上下文：自动 begin()
    - 退出上下文：自动 commit()（无异常）或 rollback()（有异常）
    - 禁止手动 commit()/rollback()，消除特殊情况
    """
    engine, session_maker = create_async_engine_and_session(SQLALCHEMY_DATABASE_URL)
    try:
        async with session_maker.begin() as session:
            yield session
    finally:
        await engine.dispose()


# ============================================================
# 向量预生成任务（反馈/需求创建后异步触发）
# ============================================================


@shared_task(
    name="userecho.generate_feedback_embedding",
    bind=True,
    max_retries=2,
    default_retry_delay=10,
    time_limit=60,
)
def generate_feedback_embedding_task(
    self: Any,
    feedback_id: str,
    content: str,
    tenant_id: str,
) -> dict:
    """
    异步生成反馈 embedding（创建后触发）

    策略：反馈创建后立即触发，将 AI 能力潜移默化地赋能给用户。
    这样在下次聚类时可以直接使用缓存，无需等待 AI 调用。

    Args:
        self: Task 实例
        feedback_id: 反馈ID
        content: 反馈内容
        tenant_id: 租户ID

    Returns:
        {'feedback_id': str, 'success': bool}
    """
    from backend.app.userecho.crud import crud_feedback
    from backend.common.log import log
    from backend.utils.ai_client import ai_client

    async def _async_run() -> dict:
        try:
            log.info(f"[Task {self.request.id}] Checking existing embedding for feedback {feedback_id}")

            async with local_db_session() as db:
                # 1. 检查是否已经有了 embedding（例如通过 API 创建时已带入或导入数据）
                feedback = await crud_feedback.get_by_id(db, tenant_id, feedback_id)
                if not feedback:
                    log.warning(f"[Task {self.request.id}] Feedback {feedback_id} not found")
                    return {"feedback_id": feedback_id, "success": False}

                if feedback.embedding is not None:
                    log.info(
                        f"[Task {self.request.id}] Embedding already exists for feedback {feedback_id}, skipping calculation"
                    )
                    return {"feedback_id": feedback_id, "success": True, "skipped": True}

                # 2. 生成 embedding
                log.info(f"[Task {self.request.id}] Generating embedding for feedback {feedback_id}")
                embedding = await ai_client.get_embedding(content)
                if not embedding:
                    log.warning(f"[Task {self.request.id}] Failed to get embedding for feedback {feedback_id}")
                    return {"feedback_id": feedback_id, "success": False}

                # 3. 写入数据库
                await crud_feedback.update_embedding(
                    db=db,
                    tenant_id=tenant_id,
                    feedback_id=feedback_id,
                    embedding=embedding,
                )

            log.info(f"[Task {self.request.id}] Embedding generated for feedback {feedback_id}")

            # 4. 记录积分消耗
            try:
                from backend.app.userecho.service.credits_service import credits_service

                async with local_db_session() as db:
                    await credits_service.consume(
                        db=db,
                        tenant_id=tenant_id,
                        operation_type="embedding",
                        count=1,
                        description="向量化：反馈创建后预生成",
                        extra_data={"feedback_id": feedback_id, "source": "pre_generate"},
                    )
            except Exception as e:
                log.warning(f"Failed to record credits for embedding task: {e}")
                # 积分记录失败不应导致任务整体失败
                return {"feedback_id": feedback_id, "success": True}
            else:
                return {"feedback_id": feedback_id, "success": True}

        except Exception as e:
            log.error(f"[Task {self.request.id}] Failed to generate embedding for feedback {feedback_id}: {e}")
            raise self.retry(exc=e)

    loop = _get_or_create_event_loop()
    return loop.run_until_complete(_async_run())


@shared_task(
    name="userecho.generate_topic_centroid",
    bind=True,
    max_retries=2,
    default_retry_delay=10,
    time_limit=60,
)
def generate_topic_centroid_task(
    self: Any,
    topic_id: str,
    tenant_id: str,
) -> dict:
    """
    异步生成需求 centroid（创建/更新后触发）

    策略：直接用 title + description 生成向量，而非等待反馈聚合。
    这样手动创建的需求也能参与相似度匹配，在下次聚类时可以被检测到。

    Args:
        self: Task 实例
        topic_id: 需求ID
        tenant_id: 租户ID

    Returns:
        {'topic_id': str, 'success': bool}
    """
    from backend.app.userecho.crud import crud_topic
    from backend.common.log import log
    from backend.utils.ai_client import ai_client

    async def _async_run() -> dict:
        try:
            log.info(f"[Task {self.request.id}] Generating centroid for topic {topic_id}")

            async with local_db_session() as db:
                topic = await crud_topic.get_by_id(db, tenant_id, topic_id)
                if not topic:
                    log.warning(f"[Task {self.request.id}] Topic {topic_id} not found")
                    return {"topic_id": topic_id, "success": False}

                # 组合文本：标题 + 描述
                text = topic.title
                if topic.description:
                    text += f"\n{topic.description}"

                # 生成向量
                centroid = await ai_client.get_embedding(text)
                if not centroid:
                    log.warning(f"[Task {self.request.id}] Failed to get centroid for topic {topic_id}")
                    return {"topic_id": topic_id, "success": False}

                # 写入数据库
                await crud_topic.update_centroid(
                    db=db,
                    tenant_id=tenant_id,
                    topic_id=topic_id,
                    centroid=centroid,
                )

            log.info(f"[Task {self.request.id}] Centroid generated for topic {topic_id}")

            # 记录积分消耗
            try:
                from backend.app.userecho.service.credits_service import credits_service

                async with local_db_session() as db:
                    await credits_service.consume(
                        db=db,
                        tenant_id=tenant_id,
                        operation_type="embedding",
                        count=1,
                        description="向量化：需求创建后预生成",
                        extra_data={"topic_id": topic_id, "source": "pre_generate"},
                    )
            except Exception as e:
                log.warning(f"Failed to record credits for centroid task: {e}")
                return {"topic_id": topic_id, "success": False}
            else:
                return {"topic_id": topic_id, "success": True}

        except Exception as e:
            log.error(f"[Task {self.request.id}] Failed to generate centroid for topic {topic_id}: {e}")
            raise self.retry(exc=e)

    loop = _get_or_create_event_loop()
    return loop.run_until_complete(_async_run())


# ============================================================
# 聚类任务
# ============================================================


@shared_task(
    name="userecho_clustering_batch",
    bind=True,
    time_limit=600,  # 10分钟硬超时
    soft_time_limit=540,  # 9分钟软超时（优雅退出）
)
def userecho_clustering_batch(
    self: Any,  # bind=True 提供 task 实例
    tenant_id: str,
    max_feedbacks: int = 100,
    force_recluster: bool = False,
    board_ids: list[str] | None = None,
) -> dict:
    """
    UserEcho 聚类批处理任务

    说明：
    - Celery 标准 Worker（非 gevent）不支持原生 async def，需要手动管理 event loop
    - 任务结果会写入 Celery result_backend（DB），前端可通过 task_id 轮询状态
    - time_limit: 10分钟硬超时，防止任务卡死
    - soft_time_limit: 9分钟软超时，给予任务优雅退出的机会

    Args:
        self: Task 实例
        tenant_id: 租户 ID
        max_feedbacks: 最大处理反馈数
        force_recluster: 是否强制重新聚类
        board_ids: 看板 ID 列表

    Event Loop 管理：
    - 不使用 asyncio.run()，因为它会关闭 loop 导致第二次任务失败
    - 手动获取或创建 event loop，复用同一个 loop
    """

    async def _async_run() -> Any:
        """异步执行聚类任务"""
        async with local_db_session() as db:
            result = await clustering_service.trigger_clustering(
                db=db,
                tenant_id=tenant_id,
                max_feedbacks=max_feedbacks,
                force_recluster=force_recluster,
                board_ids=board_ids,
            )
        return result

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


@shared_task(
    name="userecho_analyze_screenshot",
    bind=True,
    max_retries=2,
    default_retry_delay=5,
    time_limit=120,  # 2分钟硬超时
)
def analyze_screenshot_task(
    self: Any,
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
        self: Task 实例
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

    async def _async_run() -> dict:
        """异步执行上传和识别"""
        try:
            # 1. 读取临时文件
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"临时文件不存在: {file_path}")

            file_content = pathlib.Path(file_path).read_bytes()

            # 2. 上传到 OSS
            file_ext = original_filename.split(".")[-1].lower() if "." in original_filename else "jpg"
            storage_path = f"screenshots/{tenant_id}/{uuid.uuid4()}.{file_ext}"

            from io import BytesIO

            file_obj = BytesIO(file_content)

            log.info(f"[Task {self.request.id}] Uploading screenshot to OSS: {storage_path}")
            screenshot_url = await storage.upload(file_obj, storage_path, content_type=content_type)
            log.info(f"[Task {self.request.id}] Screenshot uploaded: {screenshot_url}")

            # 3. AI 识别
            log.info(f"[Task {self.request.id}] Analyzing screenshot with AI")
            extracted_data = await ai_client.analyze_screenshot(screenshot_url)
            log.info(f"[Task {self.request.id}] Analysis completed: confidence={extracted_data.get('confidence', 0)}")

            # 4. 记录积分消耗
            try:
                from backend.app.userecho.service.credits_service import credits_service

                async with local_db_session() as db:
                    await credits_service.consume(
                        db=db,
                        tenant_id=tenant_id,
                        operation_type="screenshot",
                        count=1,
                        description="截图识别",
                        extra_data={"confidence": extracted_data.get("confidence", 0)},
                    )
            except Exception as e:
                log.warning(f"Failed to record credits for screenshot task: {e}")

            return {
                "screenshot_url": screenshot_url,
                "extracted": extracted_data,
            }

        finally:
            # 4. 清理临时文件（无论成功或失败）
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    log.info(f"[Task {self.request.id}] Cleaned up temp file: {file_path}")
                except Exception as e:
                    log.warning(f"[Task {self.request.id}] Failed to remove temp file: {e}")

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
        log.error(f"[Task {self.request.id}] Screenshot analysis failed: {e}")
        # 重试机制（Celery 会自动处理）
        raise self.retry(exc=e)


@shared_task(
    name="userecho_analyze_screenshot_url",
    bind=True,
    max_retries=2,
    default_retry_delay=5,
    time_limit=120,  # 2分钟硬超时
)
def analyze_screenshot_url_task(self: Any, screenshot_url: str, tenant_id: str) -> dict:
    """
    使用截图 URL 进行 AI 识别（前端已直传）
    """
    from backend.common.log import log
    from backend.utils.ai_client import ai_client

    async def _async_run() -> dict:
        try:
            log.info(f"[Task {self.request.id}] Analyzing screenshot url with AI")
            extracted_data = await ai_client.analyze_screenshot(screenshot_url)
            log.info(f"[Task {self.request.id}] Analysis completed: confidence={extracted_data.get('confidence', 0)}")

            try:
                from backend.app.userecho.service.credits_service import credits_service

                async with local_db_session() as db:
                    await credits_service.consume(
                        db=db,
                        tenant_id=tenant_id,
                        operation_type="screenshot",
                        count=1,
                        description="截图识别",
                        extra_data={"confidence": extracted_data.get("confidence", 0)},
                    )
            except Exception as e:
                log.warning(f"Failed to record credits for screenshot url task: {e}")

            return {
                "screenshot_url": screenshot_url,
                "extracted": extracted_data,
            }
        except Exception as e:
            log.error(f"[Task {self.request.id}] Screenshot url analysis failed: {e}")
            raise

    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    try:
        return loop.run_until_complete(_async_run())
    except Exception as e:
        raise self.retry(exc=e)


@shared_task(
    name="userecho.generate_insight_report",
    bind=True,
    time_limit=300,  # 5分钟硬超时
    soft_time_limit=270,  # 4.5分钟软超时
)
async def generate_insight_report(
    self: Any,
    tenant_id: str,
    time_range: str = "this_week",
    format: str = "markdown",
) -> dict:
    """
    按需生成洞察报告（用户触发）

    使用 celery-aio-pool 的 AsyncIOPool，任务可以直接定义为 async def，
    celery-aio-pool 会自动管理事件循环。

    Args:
        self: Task 实例
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
        self.update_state(state="PROGRESS", meta={"current": 0, "total": 100, "status": "正在生成报告..."})

        # 注意：这里 generate_insight_report 是 async def，说明它可能被配置为使用 celery-aio-pool
        # 如果是这样，它不需要手动管理 loop。
        # 但我们仍然要小心 global engine。
        # 如果这个任务也是并发不安全的，最好也用 local_db_session。
        # 但 async def 任务通常运行在 worker 的主 loop 里（如果是 aio pool）。
        # 这里为了安全起见，也替换为 local_db_session，但要注意 async with 兼容性。

        async with local_db_session() as db:
            log.info(f"[Task {self.request.id}] Starting insight report generation for tenant: {tenant_id}")

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
                insight_type="weekly_report",
                time_range=time_range,
                start_date=start_date.date(),
                end_date=end_date.date(),
                content=content,
                generated_by="hybrid",
                execution_time_ms=0,
            )

            await db.commit()

            log.info(f"[Task {self.request.id}] Completed insight report generation for tenant: {tenant_id}")

            # 返回结果 - 同时返回 markdown 和 结构化数据
            return {
                "markdown": content.get("markdown", ""),
                "data": content.get("data", {}),
                "generated_at": content.get("generated_at", ""),
                "format": format,
                "status": "success",
            }

    except Exception as e:
        log.error(f"[Task {self.request.id}] Failed to generate insight report for tenant {tenant_id}: {e}")
        raise


@shared_task(
    name="userecho.generate_feedback_summary",
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
            log.info(f"[Task {self.request.id}] Generating summary for feedback {feedback_id} (tenant={tenant_id})")
            # 限制摘要生成的最长内容，避免过长文本消耗过多 Token
            summary = await ai_client.generate_summary(content, max_length=20)

            # 2. 更新数据库
            async with local_db_session() as db:
                await crud_feedback.update(db=db, tenant_id=tenant_id, id=feedback_id, ai_summary=summary)

            log.info(f"[Task {self.request.id}] Summary generated for feedback {feedback_id}: {summary}")

            # 记录积分消耗
            try:
                from backend.app.userecho.service.credits_service import credits_service

                async with local_db_session() as db:
                    await credits_service.consume(
                        db=db,
                        tenant_id=tenant_id,
                        operation_type="summary",
                        count=1,
                        description="AI 摘要生成",
                        extra_data={"feedback_id": feedback_id},
                    )
            except Exception as e:
                log.warning(f"Failed to record credits for summary task: {e}")
                return {"feedback_id": feedback_id, "summary": ""}
            else:
                return {"feedback_id": feedback_id, "summary": summary}

        except Exception as e:
            log.error(f"[Task {self.request.id}] Failed to generate summary for feedback {feedback_id}: {e}")
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
