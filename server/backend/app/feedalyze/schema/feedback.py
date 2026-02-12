from datetime import datetime

from pydantic import Field

from backend.common.schema import SchemaBase


class FeedbackBase(SchemaBase):
    """反馈基础模型"""

    content: str = Field(description='反馈内容')
    source: str = Field(default='manual', description='来源: manual=手动, import=导入, api=API')
    is_urgent: bool = Field(default=False, description='是否紧急')


class FeedbackCreate(FeedbackBase):
    """创建反馈参数"""

    customer_id: str | None = Field(None, description='客户ID (与匿名作者二选一)')
    anonymous_author: str | None = Field(None, description='匿名作者名称 (与客户ID二选一)')
    anonymous_source: str | None = Field(None, description='匿名来源平台 (如: 小红书, 微博)')


class FeedbackUpdate(SchemaBase):
    """更新反馈参数"""

    content: str | None = Field(None, description='反馈内容')
    topic_id: str | None = Field(None, description='关联主题ID')
    is_urgent: bool | None = Field(None, description='是否紧急')


class FeedbackOut(FeedbackBase):
    """反馈输出模型"""

    id: str = Field(description='反馈ID')
    tenant_id: str = Field(description='租户ID')
    customer_id: str | None = Field(None, description='客户ID')
    customer_name: str | None = Field(None, description='客户名称 (关联查询)')
    anonymous_author: str | None = Field(None, description='匿名作者')
    anonymous_source: str | None = Field(None, description='匿名来源')
    topic_id: str | None = Field(None, description='关联主题ID')
    topic_title: str | None = Field(None, description='主题标题 (关联查询)')
    ai_summary: str | None = Field(None, description='AI生成摘要')
    ai_metadata: dict | None = Field(None, description='AI元数据')
    submitted_at: datetime = Field(description='提交时间')
    created_time: datetime = Field(description='创建时间')
    updated_time: datetime = Field(description='更新时间')
    deleted_at: datetime | None = Field(None, description='删除时间')


class FeedbackImportRow(SchemaBase):
    """Excel 导入行数据"""

    content: str = Field(alias='反馈内容', description='反馈内容')
    customer_name: str = Field(alias='客户名称', description='客户名称')
    customer_type: str = Field(alias='客户类型', default='normal', description='客户类型')
    submitted_at: datetime | None = Field(alias='提交时间', default=None, description='提交时间')
    is_urgent: bool = Field(alias='是否紧急', default=False, description='是否紧急')


class FeedbackListParams(SchemaBase):
    """反馈列表查询参数"""

    topic_id: str | None = Field(None, description='过滤：主题ID')
    customer_id: str | None = Field(None, description='过滤：客户ID')
    is_urgent: bool | None = Field(None, description='过滤：是否紧急')
    source: str | None = Field(None, description='过滤：来源')
    has_topic: bool | None = Field(None, description='过滤：是否已聚类 (True=已聚类, False=未聚类)')
