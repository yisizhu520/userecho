from datetime import date, datetime
from typing import Any

from pydantic import Field

from backend.common.schema import SchemaBase


class InsightBase(SchemaBase):
    """洞察基础 Schema"""
    
    insight_type: str = Field(..., description='洞察类型: priority_suggestion | high_risk | weekly_report | sentiment_trend')
    time_range: str = Field(..., description='时间范围: this_week | this_month | custom')
    start_date: date = Field(..., description='开始日期')
    end_date: date = Field(..., description='结束日期')
    content: dict[str, Any] = Field(..., description='洞察内容（JSON）')
    generated_by: str = Field(..., description='生成方式: ai | rule_engine | hybrid')
    confidence: float | None = Field(None, description='AI 置信度 (0.0-1.0)')
    execution_time_ms: int | None = Field(None, description='生成耗时（毫秒）')


class InsightCreate(InsightBase):
    """创建洞察 Schema"""
    pass


class InsightUpdate(SchemaBase):
    """更新洞察 Schema"""
    
    status: str | None = Field(None, description='状态: active | archived | dismissed')
    dismissed_reason: str | None = Field(None, description='用户忽略的原因')


class InsightInDB(InsightBase):
    """数据库洞察 Schema"""
    
    id: str
    tenant_id: str
    status: str
    dismissed_reason: str | None
    created_time: datetime
    updated_time: datetime | None


class InsightResponse(InsightInDB):
    """洞察响应 Schema"""
    pass


class GenerateInsightRequest(SchemaBase):
    """生成洞察请求 Schema"""
    
    insight_type: str = Field(..., description='洞察类型')
    time_range: str = Field('this_week', description='时间范围')
    force_refresh: bool = Field(False, description='是否强制刷新')


class DashboardInsightsResponse(SchemaBase):
    """工作台洞察响应 Schema"""
    
    priority_suggestions: dict[str, Any] | None = Field(None, description='优先级建议')
    high_risk_topics: dict[str, Any] | None = Field(None, description='高风险需求')
    sentiment_summary: dict[str, Any] | None = Field(None, description='满意度趋势')
