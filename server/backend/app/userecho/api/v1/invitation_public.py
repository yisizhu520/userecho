"""邀请公开 API（用户端）"""

from typing import Any

from fastapi import APIRouter, Request

from backend.app.userecho.schema.invitation import InvitationValidateResp
from backend.app.userecho.service.invitation_service import invitation_service
from backend.common.response.response_schema import response_base
from backend.database.db import CurrentSession

router = APIRouter(prefix="/invitations", tags=["UserEcho - 邀请（公开）"])


@router.get("/{token}/validate", summary="验证邀请有效性")
async def validate_invitation(
    token: str,
    db: CurrentSession,
) -> Any:
    """验证邀请链接是否有效（公开接口，无需登录）"""
    is_valid, invitation, error_code = await invitation_service.validate_invitation(db, token)

    if not is_valid:
        error_messages = {
            "invitation_not_found": "邀请不存在",
            "invitation_disabled": "邀请已被禁用",
            "invitation_expired": "邀请已过期",
            "invitation_exhausted": "邀请使用次数已用完",
        }

        return response_base.success(
            data=InvitationValidateResp(
                valid=False,
                plan=None,
                expires_at=None,
                remaining_usage=None,
                error_code=error_code,
                error_message=error_messages.get(error_code, "邀请无效"),
            )
        )

    # 构造成功响应
    plan_info = {
        "code": invitation.plan_code,
        "name": "专业版" if invitation.plan_code == "pro" else "启航版",
        "trial_days": invitation.trial_days,
    }

    return response_base.success(
        data=InvitationValidateResp(
            valid=True,
            plan=plan_info,
            expires_at=invitation.expires_at,
            remaining_usage=invitation.usage_limit - invitation.used_count,
            error_code=None,
            error_message=None,
        )
    )
