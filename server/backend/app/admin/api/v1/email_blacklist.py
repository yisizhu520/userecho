"""邮箱黑名单管理 API"""

from typing import Annotated, Any

from fastapi import APIRouter, Query

from backend.app.userecho.schema.email_blacklist import (
    EmailBlacklistCreateReq,
    EmailBlacklistSchema,
    EmailBlacklistUpdateReq,
)
from backend.app.userecho.service.email_blacklist_service import (
    email_blacklist_service,
)
from backend.common.response.response_schema import response_base
from backend.common.security.jwt import CurrentUser
from backend.database.db import CurrentSession

router = APIRouter(prefix="/email-blacklist", tags=["Admin - 邮箱黑名单"])


@router.post("", summary="添加黑名单")
async def add_blacklist(
    body: EmailBlacklistCreateReq,
    db: CurrentSession,
    current_user: Annotated[dict, CurrentUser],
) -> Any:
    """添加邮箱域名到黑名单"""
    added_by = current_user.get("id")
    blacklist = await email_blacklist_service.add_blacklist(db, body, added_by)
    return response_base.success(data=EmailBlacklistSchema.model_validate(blacklist))


@router.get("", summary="黑名单列表")
async def get_blacklist_list(
    db: CurrentSession,
    _: Annotated[dict, CurrentUser],
    type: str | None = Query(None, description="类型筛选"),
    is_active: bool | None = Query(None, description="启用状态筛选"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(100, ge=1, le=500, description="每页数量"),
) -> Any:
    """获取邮箱黑名单列表"""
    items, total = await email_blacklist_service.get_blacklist_list(db, type, is_active, page, size)

    data = {
        "items": [EmailBlacklistSchema.model_validate(item) for item in items],
        "total": total,
        "page": page,
        "size": size,
    }

    return response_base.success(data=data)


@router.patch("/{blacklist_id}", summary="更新黑名单")
async def update_blacklist(
    blacklist_id: str,
    body: EmailBlacklistUpdateReq,
    db: CurrentSession,
    _: Annotated[dict, CurrentUser],
) -> Any:
    """更新黑名单状态"""
    blacklist = await email_blacklist_service.update_blacklist(db, blacklist_id, body)
    return response_base.success(data=EmailBlacklistSchema.model_validate(blacklist))


@router.delete("/{blacklist_id}", summary="删除黑名单")
async def delete_blacklist(
    blacklist_id: str,
    db: CurrentSession,
    _: Annotated[dict, CurrentUser],
) -> Any:
    """从黑名单中删除域名"""
    success = await email_blacklist_service.delete_blacklist(db, blacklist_id)
    return response_base.success(data={"success": success})
