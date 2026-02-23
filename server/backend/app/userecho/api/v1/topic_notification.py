"""需求通知 API 端点"""

from fastapi import APIRouter, Depends

from backend.app.userecho.crud.crud_topic_notification import crud_topic_notification
from backend.app.userecho.schema.topic_notification import (
    BatchGenerateReplyRequest,
    GenerateReplyRequest,
    GenerateReplyResponse,
    MarkNotifiedRequest,
    TopicNotificationListOut,
    TopicNotificationOut,
)
from backend.common.log import log
from backend.common.response.response_code import CustomResponse
from backend.common.response.response_schema import response_base
from backend.common.security.jwt import CurrentTenantId
from backend.database.db import CurrentSession

router = APIRouter(prefix="/topics", tags=["UserEcho - 需求通知"])


def get_current_user_id() -> int:
    """获取当前用户ID"""
    # TODO: 从 JWT token 中提取
    return 1


@router.get("/{topic_id}/notifications", summary="获取议题的待通知用户列表")
async def get_topic_notifications(
    topic_id: str,
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
    status: str | None = None,
    skip: int = 0,
    limit: int = 100,
):
    """
    获取议题的待通知用户列表

    - **status**: 状态筛选 (pending/generated/copied/sent)
    """
    notifications = await crud_topic_notification.get_with_details(db=db, tenant_id=tenant_id, topic_id=topic_id)

    # 应用状态筛选
    if status:
        notifications = [n for n in notifications if n.get("status") == status]

    notifications_out = [TopicNotificationListOut.model_validate(n) for n in notifications]

    # 统计各状态数量
    stats = {
        "total": len(notifications_out),
        "pending": len([n for n in notifications_out if n.status == "pending"]),
        "generated": len([n for n in notifications_out if n.status == "generated"]),
        "sent": len([n for n in notifications_out if n.status in ("copied", "sent")]),
    }

    return response_base.success(data={"items": notifications_out, "stats": stats})


@router.post("/{topic_id}/notifications/{notification_id}/generate-reply", summary="生成 AI 回复")
async def generate_reply(
    topic_id: str,
    notification_id: str,
    request: GenerateReplyRequest,
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
):
    """
    为单个用户生成 AI 个性化回复

    - **tone**: 语气风格 (formal=正式商务, friendly=亲切友好, concise=简洁高效)
    - **language**: 输出语言 (zh-CN, en-US)
    - **include_release_notes**: 是否包含发布说明
    - **custom_context**: 额外说明
    """
    import time

    from backend.app.userecho.service.notification_service import notification_service

    start_time = time.time()

    try:
        ai_reply = await notification_service.generate_reply(
            db=db,
            tenant_id=tenant_id,
            notification_id=notification_id,
            tone=request.tone,
            language=request.language,
            custom_context=request.custom_context,
        )

        generation_time_ms = int((time.time() - start_time) * 1000)

        return response_base.success(
            data=GenerateReplyResponse(
                ai_reply=ai_reply,
                tokens_used=None,  # TODO: 从 AI 服务获取
                generation_time_ms=generation_time_ms,
            )
        )
    except ValueError as e:
        return response_base.fail(res=CustomResponse(code=400, msg=str(e)))
    except Exception as e:
        log.error(f"Failed to generate reply for notification {notification_id}: {e}")
        return response_base.fail(res=CustomResponse(code=500, msg="生成回复失败，请稍后重试"))


@router.post("/{topic_id}/notifications/batch-generate", summary="批量生成 AI 回复")
async def batch_generate_replies(
    topic_id: str,
    request: BatchGenerateReplyRequest,
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
):
    """
    为所有待处理用户批量生成 AI 回复

    - **tone**: 语气风格
    - **language**: 输出语言
    """
    from backend.app.userecho.service.notification_service import notification_service

    try:
        result = await notification_service.batch_generate_replies(
            db=db,
            tenant_id=tenant_id,
            topic_id=topic_id,
            tone=request.tone,
            language=request.language,
        )

        return response_base.success(
            data=result,
            res=CustomResponse(code=200, msg=f"成功生成 {result['success']} 条回复"),
        )
    except Exception as e:
        log.error(f"Failed to batch generate replies for topic {topic_id}: {e}")
        return response_base.fail(res=CustomResponse(code=500, msg="批量生成失败，请稍后重试"))


@router.patch("/{topic_id}/notifications/{notification_id}", summary="更新通知记录")
async def update_notification(
    topic_id: str,
    notification_id: str,
    request: MarkNotifiedRequest,
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
    current_user_id: int = Depends(get_current_user_id),
):
    """
    更新通知记录（标记为已复制/已通知）

    - **status**: 状态 (copied/sent)
    - **notification_channel**: 通知渠道 (wechat/email/sms/manual)
    - **notes**: 备注
    """
    notification = await crud_topic_notification.mark_as_notified(
        db=db,
        tenant_id=tenant_id,
        notification_id=notification_id,
        notified_by=current_user_id,
        status=request.status,
        notification_channel=request.notification_channel,
        notes=request.notes,
    )

    if not notification:
        return response_base.fail(res=CustomResponse(code=400, msg="通知记录不存在"))

    return response_base.success(
        data=TopicNotificationOut.model_validate(notification),
        res=CustomResponse(code=200, msg="更新成功"),
    )
