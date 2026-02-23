from datetime import datetime

from pydantic import ConfigDict, Field

from backend.common.schema import SchemaBase


class SystemNotificationBase(SchemaBase):
    """系统提醒基础模型"""

    type: str = Field(
        description='通知类型: topic_completed/notification_pending/feedback_imported/clustering_completed'
    )
    title: str = Field(description='通知标题')
    message: str = Field(description='通知内容')
    avatar: str | None = Field(None, description='头像URL')
    action_url: str | None = Field(None, description='点击跳转URL')
    extra_data: dict | None = Field(None, description='额外元数据')


class SystemNotificationCreate(SystemNotificationBase):
    """创建系统提醒参数"""

    tenant_id: str = Field(description='租户ID')
    user_id: int | None = Field(None, description='接收用户ID（NULL表示发送给租户所有用户）')


class SystemNotificationOut(SystemNotificationBase):
    """系统提醒输出模型"""

    id: str = Field(description='通知ID')
    tenant_id: str = Field(description='租户ID')
    user_id: int | None = Field(None, description='接收用户ID')
    is_read: bool = Field(description='是否已读')
    read_at: datetime | None = Field(None, description='阅读时间')
    created_time: datetime = Field(description='创建时间')

    # 兼容前端 NotificationItem 格式的计算字段
    date: str | None = Field(None, description='相对时间（如"刚刚"、"3小时前"）')

    model_config = ConfigDict(from_attributes=True)


class SystemNotificationListResponse(SchemaBase):
    """系统提醒列表响应"""

    total: int = Field(description='总数')
    unread_count: int = Field(description='未读数量')
    items: list[SystemNotificationOut] = Field(description='通知列表')
