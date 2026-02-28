"""截图识别处理器"""

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.batch.handler.base import BatchTaskHandler, batch_task_handler
from backend.app.batch.model.batch_job import BatchJob, BatchTaskItem
from backend.app.userecho.model.feedback import Feedback
from backend.common import timezone
from backend.common.log import log
from backend.common.uuid import uuid4_str
from backend.utils.ai_client import ai_client


@batch_task_handler("screenshot_recognition")
class ScreenshotRecognitionHandler(BatchTaskHandler):
    """截图识别处理器"""

    async def process(self, task_item: BatchTaskItem, db: AsyncSession) -> dict:
        """处理单个截图识别任务"""

        # 1. 获取输入数据
        image_url = task_item.input_data["image_url"]
        board_id = task_item.input_data.get("board_id")

        # 2. 调用 AI 识别
        log.info(f"Analyzing screenshot: {image_url}")
        result = await ai_client.analyze_screenshot(image_url)

        # 3. 创建反馈
        feedback = Feedback(
            id=uuid4_str(),
            tenant_id=task_item.batch_job.tenant_id,
            board_id=board_id,
            content=result.get("description", ""),
            source="screenshot",
            source_metadata={
                "screenshot_url": image_url,
                "confidence": result.get("confidence", 0),
                "batch_job_id": task_item.batch_job_id,
            },
            screenshot_url=image_url,
            created_time=timezone.now(),
            updated_time=timezone.now(),
        )
        db.add(feedback)

        # 4. 记录积分消耗
        try:
            from backend.app.userecho.service.credits_service import credits_service

            await credits_service.consume(
                db=db,
                tenant_id=task_item.batch_job.tenant_id,
                operation_type="screenshot",
                count=1,
                description="批量截图识别",
                extra_data={"feedback_id": feedback.id, "batch_job_id": task_item.batch_job_id},
            )
        except Exception as e:
            log.warning(f"Failed to record credits: {e}")

        # 5. 返回输出数据
        return {
            "feedback_id": feedback.id,
            "content": feedback.content[:100] if feedback.content else "",  # 截断内容
            "confidence": result.get("confidence", 0),
            "screenshot_url": image_url,
        }

    async def on_batch_start(self, batch_job: BatchJob, db: AsyncSession):
        """批量任务开始前的钩子"""
        log.info(f"Starting screenshot recognition batch: {batch_job.id} ({batch_job.total_count} items)")

    async def on_batch_complete(self, batch_job: BatchJob, db: AsyncSession):
        """批量任务完成后的钩子"""
        log.info(
            f"Completed screenshot recognition batch: {batch_job.id} "
            f"(success={batch_job.completed_count}, failed={batch_job.failed_count})"
        )

        # 更新汇总信息
        batch_job.summary = {
            "total_screenshots": batch_job.total_count,
            "successfully_recognized": batch_job.completed_count,
            "failed": batch_job.failed_count,
        }

        # 发送完成通知
        try:
            from backend.common.socketio.actions import task_notification

            await task_notification(
                msg=f"批量截图识别完成：成功 {batch_job.completed_count} 个，失败 {batch_job.failed_count} 个"
            )
        except Exception as e:
            log.warning(f"Failed to send notification: {e}")
