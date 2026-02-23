"""系统提醒 API 端点"""

from fastapi import APIRouter, Depends

from backend.app.userecho.crud.crud_system_notification import crud_system_notification
from backend.app.userecho.schema.system_notification import (
    SystemNotificationListResponse,
    SystemNotificationOut,
)
from backend.common.response.response_code import CustomResponse
from backend.common.response.response_schema import response_base
from backend.common.security.jwt import CurrentTenantId
from backend.database.db import CurrentSession
from backend.utils.timezone import timezone

router = APIRouter(prefix='/notifications', tags=['UserEcho - 系统提醒'])


def get_current_user_id() -> int:
    """获取当前用户ID"""
    # TODO: 从 JWT token 中提取
    return 1


def format_relative_time(dt) -> str:
    """格式化相对时间"""
    if not dt:
        return ''

    now = timezone.now()
    diff = now - dt

    seconds = diff.total_seconds()
    if seconds < 60:
        return '刚刚'
    if seconds < 3600:
        return f'{int(seconds / 60)}分钟前'
    if seconds < 86400:
        return f'{int(seconds / 3600)}小时前'
    if seconds < 604800:
        return f'{int(seconds / 86400)}天前'
    return dt.strftime('%Y-%m-%d')


@router.get('', summary='获取系统提醒列表')
async def get_notifications(
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
    current_user_id: int = Depends(get_current_user_id),
    skip: int = 0,
    limit: int = 20,
    unread_only: bool = False,
):
    """
    获取当前用户的系统提醒列表

    - **unread_only**: 只返回未读通知
    """
    notifications = await crud_system_notification.get_user_notifications(
        db=db,
        tenant_id=tenant_id,
        user_id=current_user_id,
        skip=skip,
        limit=limit,
        unread_only=unread_only,
    )

    unread_count = await crud_system_notification.count_unread(db=db, tenant_id=tenant_id, user_id=current_user_id)

    # 转换为输出格式并添加相对时间
    items_out = []
    for n in notifications:
        n_out = SystemNotificationOut.model_validate(n)
        n_out.date = format_relative_time(n.created_time)
        items_out.append(n_out)

    return response_base.success(
        data=SystemNotificationListResponse(
            total=len(items_out),
            unread_count=unread_count,
            items=items_out,
        )
    )


@router.post('/{notification_id}/read', summary='标记通知为已读')
async def mark_as_read(
    notification_id: str,
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
    current_user_id: int = Depends(get_current_user_id),
):
    """标记单条通知为已读"""
    notification = await crud_system_notification.mark_as_read(
        db=db,
        tenant_id=tenant_id,
        notification_id=notification_id,
        user_id=current_user_id,
    )

    if not notification:
        return response_base.fail(res=CustomResponse(code=400, msg='通知不存在或无权限'))

    return response_base.success(res=CustomResponse(code=200, msg='已标记为已读'))


@router.post('/read-all', summary='标记所有通知为已读')
async def mark_all_as_read(
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
    current_user_id: int = Depends(get_current_user_id),
):
    """标记所有通知为已读"""
    count = await crud_system_notification.mark_all_as_read(db=db, tenant_id=tenant_id, user_id=current_user_id)

    return response_base.success(
        data={'marked_count': count},
        res=CustomResponse(code=200, msg=f'已标记 {count} 条通知为已读'),
    )


@router.delete('/clear', summary='清空所有通知')
async def clear_all_notifications(
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
    current_user_id: int = Depends(get_current_user_id),
):
    """清空当前用户的所有通知"""
    count = await crud_system_notification.clear_all(db=db, tenant_id=tenant_id, user_id=current_user_id)

    return response_base.success(
        data={'deleted_count': count},
        res=CustomResponse(code=200, msg=f'已清空 {count} 条通知'),
    )
