"""邀请管理 API"""

from typing import Annotated, Any

from fastapi import APIRouter, Query

from backend.app.userecho.schema.invitation import (
    InvitationCreateReq,
    InvitationSchema,
    InvitationUpdateReq,
    InvitationUsageDetailResp,
)
from backend.app.userecho.service.invitation_service import invitation_service
from backend.common.response.response_schema import response_base
from backend.common.security.jwt import CurrentUser
from backend.database.db import CurrentSession


router = APIRouter(prefix="/invitations", tags=["Admin - 邀请管理"])


@router.post("", summary="创建邀请")
async def create_invitation(
    body: InvitationCreateReq,
    db: CurrentSession,
    current_user: Annotated[dict, CurrentUser],
) -> Any:
    """创建邀请链接"""
    creator_id = current_user.id

    invitation, url, short_url, qr_code_url = await invitation_service.create_invitation(db, creator_id, body)

    # 提交事务
    await db.commit()

    # 构造详细响应
    data = {
        **InvitationSchema.model_validate(invitation).model_dump(),
        "url": url,
        "short_url": short_url,
        "qr_code_url": qr_code_url,
        "remaining_usage": invitation.usage_limit - invitation.used_count,
    }

    return response_base.success(data=data)


@router.get("", summary="邀请列表")
async def get_invitation_list(
    db: CurrentSession,
    _: Annotated[dict, CurrentUser],
    status: str | None = Query(None, description="状态筛选"),
    source: str | None = Query(None, description="来源筛选"),
    campaign: str | None = Query(None, description="活动筛选"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
) -> Any:
    """获取邀请列表（分页）"""
    items, total = await invitation_service.get_invitation_list(db, status, source, campaign, page, size)

    # 构造响应
    data = {
        "items": [InvitationSchema.model_validate(item) for item in items],
        "total": total,
        "page": page,
        "size": size,
    }

    return response_base.success(data=data)


@router.get("/{invitation_id}", summary="邀请详情")
async def get_invitation_detail(
    invitation_id: str,
    db: CurrentSession,
    _: Annotated[dict, CurrentUser],
) -> Any:
    """获取邀请详情"""
    invitation = await invitation_service.get_invitation_detail(db, invitation_id)

    # 获取所有 URL
    url, short_url, qr_code_url = invitation_service.get_invitation_urls(invitation.token)

    data = {
        **InvitationSchema.model_validate(invitation).model_dump(),
        "url": url,
        "short_url": short_url,
        "qr_code_url": qr_code_url,
        "remaining_usage": invitation.usage_limit - invitation.used_count,
    }

    return response_base.success(data=data)


@router.get("/{invitation_id}/usage", summary="邀请使用详情")
async def get_invitation_usage(
    invitation_id: str,
    db: CurrentSession,
    _: Annotated[dict, CurrentUser],
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
) -> Any:
    """获取邀请的使用记录"""
    invitation = await invitation_service.get_invitation_detail(db, invitation_id)
    usage_records, total, statistics = await invitation_service.get_invitation_usage_records(
        db, invitation_id, page, size
    )

    # 构造响应（包含用户和租户信息）
    from backend.app.admin.crud.crud_user import user_dao
    from backend.app.userecho.crud.crud_tenant import tenant_dao

    usage_list = []
    for record in usage_records:
        # 获取用户信息
        user = await user_dao.get(db, record.user_id)
        user_info = None
        if user:
            user_info = {
                "id": user.id,
                "email": user.email,
                "nickname": user.nickname,
            }

        # 获取租户信息
        tenant_info = None
        if record.created_tenant_id:
            tenant = await tenant_dao.get(db, record.created_tenant_id)
            if tenant:
                tenant_info = {
                    "id": tenant.id,
                    "name": tenant.name,
                }

        usage_list.append(
            {
                **InvitationUsageDetailResp.model_validate(record).model_dump(),
                "user": user_info,
                "created_tenant": tenant_info,
            }
        )

    data = {
        "invitation": InvitationSchema.model_validate(invitation),
        "usage_records": usage_list,
        "statistics": statistics,
        "total": total,
        "page": page,
        "size": size,
    }

    return response_base.success(data=data)


@router.patch("/{invitation_id}", summary="更新邀请")
async def update_invitation(
    invitation_id: str,
    body: InvitationUpdateReq,
    db: CurrentSession,
    _: Annotated[dict, CurrentUser],
) -> Any:
    """更新邀请信息"""
    invitation = await invitation_service.update_invitation(db, invitation_id, body)
    await db.commit()
    return response_base.success(data=InvitationSchema.model_validate(invitation))


@router.delete("/{invitation_id}", summary="删除邀请")
async def delete_invitation(
    invitation_id: str,
    db: CurrentSession,
    _: Annotated[dict, CurrentUser],
) -> Any:
    """删除邀请（软删除，标记为disabled）"""
    success = await invitation_service.delete_invitation(db, invitation_id)
    await db.commit()
    return response_base.success(data={"success": success})
