from datetime import datetime

from pydantic import ConfigDict, Field

from backend.common.schema import SchemaBase


class PriorityScoreBase(SchemaBase):
    """优先级评分基础模型"""

    impact_scope: int = Field(ge=1, le=10, description="影响范围 (1-10)")
    business_value: int = Field(ge=1, le=10, description="商业价值 (1-10)")
    dev_cost: int = Field(ge=1, le=10, description="开发成本 (1-10)")
    urgency_factor: float = Field(default=1.0, ge=1.0, le=2.0, description="紧急系数 (1.0-2.0)")


class PriorityScoreCreate(PriorityScoreBase):
    """创建优先级评分参数"""

    topic_id: str = Field(description="主题ID")
    details: dict | None = Field(None, description="详细计算结果")


class PriorityScoreUpdate(SchemaBase):
    """更新优先级评分参数"""

    impact_scope: int | None = Field(None, ge=1, le=10, description="影响范围")
    business_value: int | None = Field(None, ge=1, le=10, description="商业价值")
    dev_cost: int | None = Field(None, ge=1, le=10, description="开发成本")
    urgency_factor: float | None = Field(None, ge=1.0, le=2.0, description="紧急系数")
    details: dict | None = Field(None, description="详细计算结果")


class PriorityScoreOut(PriorityScoreBase):
    """优先级评分输出模型"""

    id: str = Field(description="评分ID")
    tenant_id: str = Field(description="租户ID")
    topic_id: str = Field(description="主题ID")
    total_score: float = Field(description="总分")
    details: dict | None = Field(None, description="详细计算结果")
    created_time: datetime = Field(description="创建时间")
    updated_time: datetime | None = Field(None, description="更新时间")

    # ✅ 支持从 ORM 对象创建
    model_config = ConfigDict(from_attributes=True)
