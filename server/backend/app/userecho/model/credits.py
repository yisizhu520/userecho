"""积分系统模型

通用积分消耗体系，支持月度自动刷新和可配置的消耗规则
"""

from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import MappedBase
from backend.database.db import uuid4_str
from backend.utils.timezone import timezone


class CreditsOperationType(str, Enum):
    """积分消耗类型（可扩展）"""

    CLUSTERING = 'clustering'  # AI 聚类
    SCREENSHOT = 'screenshot'  # 截图识别
    SUMMARY = 'summary'  # AI 摘要生成
    EMBEDDING = 'embedding'  # 向量化
    INSIGHT = 'insight'  # 洞察报告
    # 未来扩展
    EXPORT = 'export'  # 数据导出
    API_CALL = 'api_call'  # API 调用


class TenantCredits(MappedBase):
    """租户积分配置"""

    __tablename__ = 'tenant_credits'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str, comment='ID')
    tenant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey('tenants.id', ondelete='CASCADE'),
        unique=True,
        nullable=False,
        comment='租户ID',
    )
    plan_type: Mapped[str] = mapped_column(
        String(20), default='starter', nullable=False, comment='订阅类型: starter/pro/team/enterprise'
    )
    monthly_quota: Mapped[int] = mapped_column(Integer, default=500, nullable=False, comment='月度积分额度')
    current_balance: Mapped[int] = mapped_column(Integer, default=500, nullable=False, comment='当前剩余积分')
    total_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment='累计使用积分')
    last_refresh_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True, comment='上次刷新时间')
    next_refresh_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True, comment='下次刷新时间')

    __table_args__ = (Index('idx_tenant_credits_refresh', 'next_refresh_at'),)


class CreditsUsageLog(MappedBase):
    """积分消耗记录"""

    __tablename__ = 'credits_usage_log'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str, comment='ID')
    tenant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, comment='租户ID'
    )
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, comment='操作用户ID')
    operation_type: Mapped[str] = mapped_column(String(50), nullable=False, comment='操作类型')
    credits_cost: Mapped[int] = mapped_column(Integer, nullable=False, comment='消耗积分')
    description: Mapped[str | None] = mapped_column(String(255), nullable=True, comment='操作描述')
    extra_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True, comment='扩展信息')
    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), default=timezone.now, nullable=False, comment='创建时间'
    )

    __table_args__ = (
        Index('idx_credits_usage_tenant_date', 'tenant_id', 'created_at'),
        Index('idx_credits_usage_type', 'operation_type'),
    )


class CreditsConfig(MappedBase):
    """积分配置（系统级，Admin 管理）

    存储各操作类型的积分消耗值和各套餐的月度额度
    """

    __tablename__ = 'credits_config'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str, comment='ID')
    config_key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment='配置键')
    config_value: Mapped[int] = mapped_column(Integer, nullable=False, comment='配置值（整数）')
    config_type: Mapped[str] = mapped_column(
        String(20), nullable=False, comment='配置类型: operation_cost / plan_quota'
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment='配置说明')

    __table_args__ = (Index('idx_credits_config_type', 'config_type'),)
