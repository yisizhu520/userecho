"""截图识别处理器"""

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.batch.handler.base import BatchTaskHandler, batch_task_handler
from backend.app.batch.model.batch_job import BatchJob, BatchTaskItem
from backend.app.userecho.model.feedback import Feedback
from backend.common.log import log
from backend.database.db import uuid4_str
from backend.utils.ai_client import ai_client
from backend.utils.timezone import timezone


@batch_task_handler("screenshot_recognition")
class ScreenshotRecognitionHandler(BatchTaskHandler):
    """截图识别处理器"""

    async def process(self, task_item: BatchTaskItem, db: AsyncSession) -> dict:
        """处理单个截图识别任务"""

        # 1. 获取输入数据
        image_url = task_item.input_data["image_url"]
        board_id = task_item.input_data.get("board_id")
        author_type = task_item.input_data.get("author_type", "external")

        # 2. 调用 AI 识别
        log.info(f"Analyzing screenshot: {image_url}")
        result = await ai_client.analyze_screenshot(image_url)

        # 提取 AI 识别结果（新格式：返回 feedback_list）
        feedback_list = result.get("feedback_list", [])
        raw_text = result.get("raw_text", "")

        log.info(f"AI recognition result: {len(feedback_list)} feedback(s) found, raw_text length: {len(raw_text)}")

        # 如果识别失败，创建一条空反馈
        if not feedback_list:
            log.warning("No feedback extracted from screenshot, using raw_text as fallback")
            feedback_list = [
                {
                    "content": raw_text or "图像识别失败，请手动填写",
                    "user_name": "",
                    "platform": "",
                    "confidence": 0,
                }
            ]

        # 3. 为每条反馈创建独立的 Feedback 记录
        created_feedbacks = []
        for idx, feedback_data in enumerate(feedback_list):
            ai_content = feedback_data.get("content", "")
            ai_user_name = feedback_data.get("user_name", "")
            ai_platform = feedback_data.get("platform", "")
            ai_confidence = feedback_data.get("confidence", 0)

            log.info(
                f"Creating feedback {idx + 1}/{len(feedback_list)}: "
                f"content={ai_content[:50]}..., user={ai_user_name}, "
                f"platform={ai_platform}, confidence={ai_confidence}"
            )

            # 构建反馈数据（使用 AI 识别 + 预设配置）
            feedback_dict = {
                "id": uuid4_str(),
                "tenant_id": task_item.batch_job.tenant_id,
                "board_id": board_id,
                "content": ai_content,
                "source": "screenshot",
                "images_metadata": {
                    "images": [
                        {
                            "url": image_url,
                            "platform": ai_platform,
                            "user_name": ai_user_name,
                            "confidence": ai_confidence,
                            "uploaded_at": timezone.now().isoformat(),
                            "batch_job_id": task_item.batch_job_id,
                            "batch_mode": True,
                            "feedback_index": idx,  # 同一张图的第几条反馈
                            "total_feedbacks": len(feedback_list),  # 该图共识别出几条
                        }
                    ]
                },
                "screenshot_url": image_url,
                "ai_confidence": ai_confidence,
                "created_time": timezone.now(),
                "updated_time": timezone.now(),
            }

            # 根据来源类型设置字段
            if author_type == "customer":
                # 内部客户模式：使用预设客户名（不再支持，AI 无法识别内部客户）
                default_customer_name = task_item.input_data.get("default_customer_name")
                feedback_dict["external_user_name"] = ai_user_name or default_customer_name
                feedback_dict["author_type"] = "external"  # 强制为外部用户
            else:
                # 外部用户模式：使用 AI 识别 + 预设配置
                source_platform = task_item.input_data.get("source_platform", "wechat")
                default_user_name = task_item.input_data.get("default_user_name")

                feedback_dict["source_platform"] = ai_platform or source_platform
                feedback_dict["source_user_name"] = ai_user_name or default_user_name or "匿名用户"
                feedback_dict["external_user_name"] = ai_user_name or default_user_name or "匿名用户"
                feedback_dict["author_type"] = "external"

            # 创建反馈
            feedback = Feedback(**feedback_dict)
            db.add(feedback)
            created_feedbacks.append(
                {
                    "feedback_id": feedback.id,
                    "content": feedback.content[:100] if feedback.content else "",
                    "confidence": ai_confidence,
                }
            )

        # 4. 记录积分消耗（按识别出的反馈数量计费）
        try:
            from backend.app.userecho.service.credits_service import credits_service

            await credits_service.consume(
                db=db,
                tenant_id=task_item.batch_job.tenant_id,
                operation_type="screenshot",
                count=len(created_feedbacks),
                description=f"批量截图识别（识别出 {len(created_feedbacks)} 条反馈）",
                extra_data={
                    "batch_job_id": task_item.batch_job_id,
                    "feedback_ids": [f["feedback_id"] for f in created_feedbacks],
                },
            )
        except Exception as e:
            log.warning(f"Failed to record credits: {e}")

        # 5. 返回输出数据
        return {
            "screenshot_url": image_url,
            "feedbacks": created_feedbacks,
            "total_feedbacks": len(created_feedbacks),
            "overall_confidence": result.get("overall_confidence", 0),
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

        # 创建系统提醒：批量截图识别完成
        try:
            from backend.app.userecho.crud.crud_system_notification import crud_system_notification

            await crud_system_notification.create_screenshot_batch_completed_notification(
                db=db,
                tenant_id=batch_job.tenant_id,
                total_count=batch_job.total_count,
                success_count=batch_job.completed_count,
                failed_count=batch_job.failed_count,
                user_id=None,  # 全员通知
            )
            log.info(f"Created screenshot batch completed notification for batch {batch_job.id}")
        except Exception as e:
            log.error(f"Failed to create screenshot batch notification for batch {batch_job.id}: {e}")

        # FIXME: task_notification 在 Celery Worker 中会导致 event loop 冲突
        # 临时注释，后续使用同步 Redis Pub/Sub 实现
        # try:
        #     from backend.common.socketio.actions import task_notification
        #     await task_notification(
        #         msg=f"批量截图识别完成：成功 {batch_job.completed_count} 个，失败 {batch_job.failed_count} 个"
        #     )
        # except Exception as e:
        #     log.warning(f"Failed to send notification: {e}")
