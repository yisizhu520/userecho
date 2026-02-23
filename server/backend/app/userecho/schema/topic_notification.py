from datetime import datetime

from pydantic import ConfigDict, Field

from backend.common.schema import SchemaBase


class TopicNotificationBase(SchemaBase):
    """需求通知记录基础模型"""

    recipient_name: str = Field(description="收件人名称")
    recipient_contact: str | None = Field(None, description="联系方式")
    recipient_type: str = Field(default="customer", description="收件人类型: customer/external")
    reply_tone: str = Field(default="friendly", description="回复语气: formal/friendly/concise")
    reply_language: str = Field(default="zh-CN", description="回复语言")


class TopicNotificationCreate(TopicNotificationBase):
    """创建通知记录参数"""

    tenant_id: str = Field(description="租户ID")
    topic_id: str = Field(description="议题ID")
    feedback_id: str = Field(description="反馈ID")
    customer_id: str | None = Field(None, description="客户ID")


class TopicNotificationUpdate(SchemaBase):
    """更新通知记录参数"""

    ai_reply: str | None = Field(None, description="AI 生成的回复内容")
    reply_tone: str | None = Field(None, description="回复语气")
    reply_language: str | None = Field(None, description="回复语言")
    status: str | None = Field(None, description="状态: pending/generated/copied/sent")
    notification_channel: str | None = Field(None, description="通知渠道")
    notes: str | None = Field(None, description="备注")


class TopicNotificationOut(TopicNotificationBase):
    """通知记录输出模型"""

    id: str = Field(description="记录ID")
    tenant_id: str = Field(description="租户ID")
    topic_id: str = Field(description="议题ID")
    feedback_id: str = Field(description="反馈ID")
    customer_id: str | None = Field(None, description="客户ID")
    ai_reply: str | None = Field(None, description="AI 生成的回复内容")
    status: str = Field(description="状态")
    notified_at: datetime | None = Field(None, description="通知时间")
    notified_by: int | None = Field(None, description="操作人员ID")
    notification_channel: str | None = Field(None, description="通知渠道")
    notes: str | None = Field(None, description="备注")
    created_time: datetime = Field(description="创建时间")
    updated_time: datetime | None = Field(None, description="更新时间")

    model_config = ConfigDict(from_attributes=True)


class TopicNotificationListOut(TopicNotificationOut):
    """通知记录列表输出（包含关联信息）"""

    customer_company: str | None = Field(None, description="客户公司名称")
    customer_tier: str | None = Field(None, description="客户等级")
    feedback_summary: str | None = Field(None, description="反馈摘要")
    feedback_content: str | None = Field(None, description="反馈内容")


class GenerateReplyRequest(SchemaBase):
    """生成 AI 回复请求参数"""

    tone: str = Field(default="friendly", description="语气风格: formal/friendly/concise")
    language: str = Field(default="zh-CN", description="输出语言")
    include_release_notes: bool = Field(default=True, description="是否包含发布说明")
    custom_context: str | None = Field(None, description="额外说明")


class GenerateReplyResponse(SchemaBase):
    """生成 AI 回复响应"""

    ai_reply: str = Field(description="生成的回复内容")
    tokens_used: int | None = Field(None, description="使用的 token 数")
    generation_time_ms: int | None = Field(None, description="生成耗时（毫秒）")


class BatchGenerateReplyRequest(SchemaBase):
    """批量生成 AI 回复请求参数"""

    tone: str = Field(default="friendly", description="语气风格")
    language: str = Field(default="zh-CN", description="输出语言")


class MarkNotifiedRequest(SchemaBase):
    """标记已通知请求参数"""

    status: str = Field(default="sent", description="状态: copied/sent")
    notification_channel: str | None = Field(None, description="通知渠道")
    notes: str | None = Field(None, description="备注")
