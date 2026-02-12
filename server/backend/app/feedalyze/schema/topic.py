from datetime import datetime

from pydantic import Field

from backend.common.schema import SchemaBase


class TopicBase(SchemaBase):
    """需求主题基础模型"""

    title: str = Field(description='主题标题')
    category: str = Field(
        default='other',
        description='分类: bug=缺陷, improvement=体验优化, feature=新功能, performance=性能, other=其他'
    )
    status: str = Field(
        default='pending',
        description='状态: pending=待处理, planned=计划中, in_progress=进行中, completed=已完成, ignored=已忽略'
    )
    description: str | None = Field(None, description='详细描述')


class TopicCreate(TopicBase):
    """创建主题参数"""
    pass


class TopicUpdate(SchemaBase):
    """更新主题参数"""

    title: str | None = Field(None, description='主题标题')
    category: str | None = Field(None, description='分类')
    status: str | None = Field(None, description='状态')
    description: str | None = Field(None, description='详细描述')


class TopicOut(TopicBase):
    """主题输出模型"""

    id: str = Field(description='主题ID')
    tenant_id: str = Field(description='租户ID')
    ai_generated: bool = Field(description='是否AI生成')
    ai_confidence: float | None = Field(None, description='AI置信度 (0-1)')
    feedback_count: int = Field(description='关联反馈数量')
    created_time: datetime = Field(description='创建时间')
    updated_time: datetime = Field(description='更新时间')
    deleted_at: datetime | None = Field(None, description='删除时间')


class TopicDetailOut(TopicOut):
    """主题详情输出（包含关联数据）"""

    feedbacks: list['FeedbackOut'] = Field(default_factory=list, description='关联反馈列表')
    priority_score: 'PriorityScoreOut | None' = Field(None, description='优先级评分')
    status_history: list['StatusHistoryOut'] = Field(default_factory=list, description='状态变更历史')


class TopicListParams(SchemaBase):
    """主题列表查询参数"""

    status: str | None = Field(None, description='过滤：状态')
    category: str | None = Field(None, description='过滤：分类')
    sort_by: str = Field(default='created_time', description='排序字段: created_time, priority, feedback_count')
    sort_order: str = Field(default='desc', description='排序方向: asc, desc')


class TopicStatusUpdateParam(SchemaBase):
    """更新主题状态参数"""

    status: str = Field(description='新状态')
    reason: str | None = Field(None, description='变更原因')


# 避免循环导入，在文件末尾导入
from backend.app.feedalyze.schema.feedback import FeedbackOut  # noqa: E402
from backend.app.feedalyze.schema.priority import PriorityScoreOut  # noqa: E402
from backend.app.feedalyze.schema.status_history import StatusHistoryOut  # noqa: E402

TopicDetailOut.model_rebuild()
