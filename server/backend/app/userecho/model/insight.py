from datetime import datetime

from sqlalchemy import Date, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import MappedBase, TimeZone
from backend.database.db import uuid4_str
from backend.utils.timezone import timezone


class Insight(MappedBase):
    """洞察实例表（AI 生成的洞察快照）"""

    __tablename__ = 'insights'

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=uuid4_str, comment='洞察ID'
    )
    tenant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey('tenants.id', ondelete='CASCADE'), index=True, comment='租户ID'
    )
    
    # 分类与时间范围
    insight_type: Mapped[str] = mapped_column(
        String(20), index=True, comment='洞察类型: priority_suggestion | high_risk | weekly_report | sentiment_trend'
    )
    time_range: Mapped[str] = mapped_column(
        String(20), comment='时间范围: this_week | this_month | custom'
    )
    start_date: Mapped[datetime] = mapped_column(
        Date, comment='开始日期'
    )
    end_date: Mapped[datetime] = mapped_column(
        Date, comment='结束日期'
    )
    
    # 洞察内容（JSON 存储，不同类型结构不同）
    content: Mapped[dict] = mapped_column(
        JSON, comment='洞察内容（JSON 格式）'
    )
    
    # 元数据
    generated_by: Mapped[str] = mapped_column(
        String(20), comment='生成方式: ai | rule_engine | hybrid'
    )
    confidence: Mapped[float | None] = mapped_column(
        default=None, comment='AI 置信度 (0.0-1.0)'
    )
    execution_time_ms: Mapped[int | None] = mapped_column(
        Integer, default=None, comment='生成耗时（毫秒）'
    )
    
    # 状态
    status: Mapped[str] = mapped_column(
        String(20), default='active', index=True, comment='状态: active | archived | dismissed'
    )
    dismissed_reason: Mapped[str | None] = mapped_column(
        Text, default=None, comment='用户忽略的原因'
    )
    
    # 时间戳字段
    created_time: Mapped[datetime] = mapped_column(
        TimeZone, default=timezone.now, comment='创建时间'
    )
    updated_time: Mapped[datetime | None] = mapped_column(
        TimeZone, onupdate=timezone.now, default=None, comment='更新时间'
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        TimeZone, default=None, comment='软删除时间'
    )
