"""认证公开 API（邀请注册和邮箱验证）"""

from typing import Any

from fastapi import APIRouter, Request

from backend.app.userecho.schema.auth import (
    RegisterWithInvitationReq,
    RegisterWithInvitationResp,
)
from backend.app.userecho.schema.email_verification import (
    EmailResendReq,
    EmailResendResp,
    EmailVerifyReq,
    EmailVerifyResp,
)
from backend.app.userecho.service.auth_service import auth_service
from backend.app.userecho.service.email_verification_service import (
    email_verification_service,
)
from backend.common.response.response_schema import response_base
from backend.common.security.jwt import CurrentUser
from backend.database.db import CurrentSession

router = APIRouter(prefix="/auth", tags=["UserEcho - 认证（公开）"])


@router.post("/register/invite", summary="通过邀请码注册")
async def register_with_invitation(
    body: RegisterWithInvitationReq,
    request: Request,
    db: CurrentSession,
) -> Any:
    """通过邀请码注册新用户"""
    # 获取客户端信息
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    result = await auth_service.register_with_invitation(
        db,
        body.invitation_token,
        body.email,
        body.password,
        body.nickname,
        ip_address,
        user_agent,
    )

    return response_base.success(
        data=RegisterWithInvitationResp(
            user=result["user"],
            verification_email_sent=result["verification_email_sent"],
            next_step=result["next_step"],
        ),
        msg="注册成功，请前往邮箱验证",
    )


@router.post("/email/verify", summary="验证邮箱")
async def verify_email(
    body: EmailVerifyReq,
    db: CurrentSession,
    current_user: dict = CurrentUser,
) -> Any:
    """验证邮箱并激活订阅"""
    user_id = current_user.get("id")

    result = await auth_service.verify_email_and_activate_subscription(db, user_id, body.verification_code)

    return response_base.success(
        data=EmailVerifyResp(verified=True, message=result["message"]),
        msg="邮箱验证成功",
    )


@router.post("/email/resend", summary="重新发送验证邮件")
async def resend_verification_email(
    body: EmailResendReq,
    db: CurrentSession,
    current_user: dict = CurrentUser,
) -> Any:
    """重新发送邮箱验证邮件"""
    user_id = current_user.get("id")

    success, message, verification = await email_verification_service.resend_verification(
        db, user_id, body.email
    )

    if not success:
        return response_base.fail(msg=message)

    # TODO: 发送验证邮件（阶段6实现）

    return response_base.success(
        data=EmailResendResp(sent=True, message="验证邮件已发送", retry_after=None),
        msg="验证邮件已发送",
    )
