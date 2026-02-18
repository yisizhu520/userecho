from datetime import datetime
from typing import Literal

from pydantic import ConfigDict, Field

from backend.common.schema import SchemaBase


class FeedbackBase(SchemaBase):
    """反馈基础模型"""

    content: str = Field(description='反馈内容')
    source: str = Field(default='manual', description='来源: manual=手动, import=导入, api=API')
    is_urgent: bool = Field(default=False, description='是否紧急')


class FeedbackCreate(FeedbackBase):
    """创建反馈参数"""

    board_id: str = Field(description='看板ID (必填)')
    customer_id: str | None = Field(None, description='客户ID (可选，若未指定则根据 customer_name 自动创建)')
    customer_name: str = Field(description='客户名称 (必填)')
    customer_type: str | None = Field(None, description='客户类型 (新建客户时使用): normal/paid/major/strategic')
    topic_id: str | None = Field(None, description='关联主题ID (手动关联)')
    screenshots: list[str] | None = Field(None, description='截图URL列表 (最多3张)')


class FeedbackUpdate(SchemaBase):
    """更新反馈参数"""

    content: str | None = Field(None, description='反馈内容')
    topic_id: str | None = Field(None, description='关联主题ID')
    is_urgent: bool | None = Field(None, description='是否紧急')


class FeedbackOut(FeedbackBase):
    """反馈输出模型"""

    id: str = Field(description='反馈ID')
    tenant_id: str = Field(description='租户ID')
    board_id: str | None = Field(None, description='看板ID')
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
    updated_time: datetime | None = Field(None, description='更新时间')
    deleted_at: datetime | None = Field(None, description='删除时间')

    # ✅ 支持从 ORM/dict 创建（自动排除 embedding 字段）
    model_config = ConfigDict(from_attributes=True)


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
    clustering_status: str | None = Field(None, description='过滤：聚类状态 (pending/processing/clustered/failed)')


# ==================== 截图识别相关 Schema ====================


class ExtractedScreenshotData(SchemaBase):
    """AI 提取的截图数据"""

    platform: Literal['wechat', 'xiaohongshu', 'appstore', 'weibo', 'other'] = Field(description='平台类型')
    user_name: str = Field(default='', description='用户昵称')
    user_id: str = Field(default='', description='平台用户 ID')
    content: str = Field(description='提取的反馈内容')
    feedback_type: Literal['bug', 'feature', 'complaint', 'other'] = Field(default='other', description='反馈类型')
    sentiment: Literal['positive', 'neutral', 'negative'] = Field(default='neutral', description='情感倾向')
    confidence: float = Field(ge=0.0, le=1.0, description='AI 识别置信度')


class ScreenshotAnalyzeResponse(SchemaBase):
    """截图识别响应"""

    screenshot_url: str = Field(description='截图 URL')
    extracted: ExtractedScreenshotData = Field(description='AI 提取的信息')


class ScreenshotFeedbackCreate(SchemaBase):
    """从截图创建反馈"""

    content: str = Field(description='反馈内容')
    screenshot_url: str = Field(description='截图 URL')
    source_type: Literal['screenshot'] = Field(default='screenshot', description='来源类型')
    source_platform: Literal['wechat', 'xiaohongshu', 'appstore', 'weibo', 'other'] = Field(description='来源平台')
    source_user_name: str = Field(default='', description='平台用户昵称')
    source_user_id: str = Field(default='', description='平台用户 ID')
    ai_confidence: float | None = Field(None, ge=0.0, le=1.0, description='AI 识别置信度')
    customer_id: str | None = Field(None, description='关联的客户 ID（可选）')
