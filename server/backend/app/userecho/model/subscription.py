"""订阅体系模型

提供多层级订阅管理：
1. SubscriptionPlan - 套餐定义（系统级配置）
2. TenantSubscription - 租户订阅记录
3. SubscriptionHistory - 订阅变更历史
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import MappedBase
from backend.database.db import uuid4_str
from backend.utils.timezone import timezone


class PlanCode(str, Enum):
    """套餐代号枚举"""

    STARTER = 'starter'  # 启航版
    PRO = 'pro'  # 专业版
    FLAGSHIP = 'flagship'  # 旗舰版
    ENTERPRISE = 'enterprise'  # 定制版


class SubscriptionStatus(str, Enum):
    """订阅状态枚举"""

    TRIAL = 'trial'  # 试用期
    ACTIVE = 'active'  # 活跃
    EXPIRED = 'expired'  # 已过期
    CANCELED = 'canceled'  # 已取消


class SubscriptionSource(str, Enum):
    """订阅来源枚举"""

    MANUAL = 'manual'  # 手动添加
    STRIPE = 'stripe'  # Stripe 支付（预留）
    WECHAT = 'wechat'  # 微信支付（预留）
    ALIPAY = 'alipay'  # 支付宝（预留）


class SubscriptionAction(str, Enum):
    """订阅操作类型"""

    CREATED = 'created'  # 创建
    UPGRADED = 'upgraded'  # 升级
    DOWNGRADED = 'downgraded'  # 降级
    RENEWED = 'renewed'  # 续费
    CANCELED = 'canceled'  # 取消
    EXPIRED = 'expired'  # 过期
    EXTENDED = 'extended'  # 延期


class SubscriptionPlan(MappedBase):
    """订阅套餐定义（系统级配置）"""

    __tablename__ = 'subscription_plans'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str, comment='ID')
    code: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, comment='套餐代号: starter/pro/flagship/enterprise'
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False, comment='套餐名称（启航版、专业版...）')
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment='套餐描述')

    # 定价（单位：分）
    price_monthly: Mapped[int] = mapped_column(Integer, nullable=False, comment='月付价格（分）')
    price_yearly: Mapped[int] = mapped_column(Integer, nullable=False, comment='年付价格（分）')

    # 限制
    seat_limit: Mapped[int] = mapped_column(Integer, default=1, nullable=False, comment='席位上限（-1 表示不限）')
    feedback_limit: Mapped[int] = mapped_column(
        Integer, default=1000, nullable=False, comment='反馈存储上限（-1 表示不限）'
    )
    ai_credits_monthly: Mapped[int] = mapped_column(Integer, default=500, nullable=False, comment='月度 AI 积分')

    # 功能配置（JSON）
    features: Mapped[dict] = mapped_column(JSONB, nullable=False, comment='功能开关和配置')

    # 管理字段
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False, comment='是否启用')
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment='排序权重')

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=timezone.now, nullable=False, comment='创建时间'
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=timezone.now, nullable=True, comment='更新时间'
    )

    __table_args__ = (Index('idx_subscription_plan_code', 'code'), Index('idx_subscription_plan_active', 'is_active'))


class TenantSubscription(MappedBase):
    """租户订阅记录"""

    __tablename__ = 'tenant_subscriptions'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str, comment='ID')
    tenant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, index=True, comment='租户ID'
    )
    plan_id: Mapped[str] = mapped_column(
        String(36), ForeignKey('subscription_plans.id', ondelete='RESTRICT'), nullable=False, comment='套餐ID'
    )

    # 订阅状态
    status: Mapped[str] = mapped_column(
        String(20), default=SubscriptionStatus.TRIAL, nullable=False, index=True, comment='订阅状态'
    )

    # 时间周期
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=timezone.now, nullable=False, comment='订阅开始时间'
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, comment='订阅到期时间')
    trial_ends_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment='试用期结束时间'
    )
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, comment='取消时间')

    # 来源和支付（预留）
    source: Mapped[str] = mapped_column(
        String(20), default=SubscriptionSource.MANUAL, nullable=False, comment='订阅来源'
    )
    payment_id: Mapped[str | None] = mapped_column(String(100), nullable=True, comment='支付订单ID（预留）')

    # 管理信息
    created_by: Mapped[str | None] = mapped_column(String(36), nullable=True, comment='创建人（手动添加时为管理员ID）')
    notes: Mapped[str | None] = mapped_column(Text, nullable=True, comment='管理备注')

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=timezone.now, nullable=False, comment='创建时间'
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=timezone.now, nullable=True, comment='更新时间'
    )

    __table_args__ = (
        Index('idx_tenant_subscription_tenant', 'tenant_id'),
        Index('idx_tenant_subscription_status', 'status'),
        Index('idx_tenant_subscription_expires', 'expires_at'),
    )


class SubscriptionHistory(MappedBase):
    """订阅变更历史"""

    __tablename__ = 'subscription_history'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str, comment='ID')
    tenant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, index=True, comment='租户ID'
    )
    subscription_id: Mapped[str] = mapped_column(
        String(36), ForeignKey('tenant_subscriptions.id', ondelete='CASCADE'), nullable=False, comment='订阅ID'
    )

    # 操作信息
    action: Mapped[str] = mapped_column(String(20), nullable=False, comment='操作类型')
    old_plan_code: Mapped[str | None] = mapped_column(String(20), nullable=True, comment='变更前套餐代号')
    new_plan_code: Mapped[str] = mapped_column(String(20), nullable=False, comment='变更后套餐代号')

    # 操作人和原因
    changed_by: Mapped[str | None] = mapped_column(String(36), nullable=True, comment='操作人ID')
    reason: Mapped[str | None] = mapped_column(Text, nullable=True, comment='变更原因/备注')

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=timezone.now, nullable=False, comment='创建时间'
    )

    __table_args__ = (
        Index('idx_subscription_history_tenant', 'tenant_id'),
        Index('idx_subscription_history_subscription', 'subscription_id'),
        Index('idx_subscription_history_created', 'created_at'),
    )
