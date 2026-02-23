from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import ARRAY, Date, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import MappedBase, TimeZone
from backend.database.db import uuid4_str
from backend.utils.timezone import timezone


class Customer(MappedBase):
    """客户表（Tenant 的终端用户，不是平台用户，由 Tenant 管理）"""

    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str, comment="客户ID")
    tenant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tenants.id", ondelete="CASCADE"), index=True, comment="租户ID"
    )

    # 客户基础信息
    name: Mapped[str] = mapped_column(String(100), comment="客户名称")
    company_name: Mapped[str | None] = mapped_column(String(200), default=None, comment="公司名称")
    contact_email: Mapped[str | None] = mapped_column(String(255), default=None, comment="联系邮箱")
    contact_phone: Mapped[str | None] = mapped_column(String(50), default=None, comment="联系电话")

    # 客户分类
    customer_type: Mapped[str] = mapped_column(
        String(20), default="normal", comment="客户类型: normal, paid, vip, strategic"
    )
    customer_tier: Mapped[str] = mapped_column(
        String(20), default="normal", comment="客户等级: free, normal, paid, vip, strategic"
    )
    business_value: Mapped[int] = mapped_column(default=1, comment="商业价值权重 (1-10)")

    # 商业数据
    mrr: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), default=None, comment="月收入 (MRR)")
    arr: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), default=None, comment="年收入 (ARR)")
    churn_risk: Mapped[str] = mapped_column(String(20), default="low", comment="流失风险: low, medium, high")
    contract_start_date: Mapped[date | None] = mapped_column(Date, default=None, comment="合同开始日期")
    contract_end_date: Mapped[date | None] = mapped_column(Date, default=None, comment="合同结束日期")

    # 客户标签和来源
    tags: Mapped[list | None] = mapped_column(ARRAY(String), default=None, comment="客户标签数组")
    source: Mapped[str | None] = mapped_column(
        String(50), default=None, comment="客户来源: direct, referral, marketing"
    )
    notes: Mapped[str | None] = mapped_column(Text, default=None, comment="客户备注")

    deleted_at: Mapped[datetime | None] = mapped_column(TimeZone, default=None, comment="软删除时间")

    # 时间戳字段
    created_time: Mapped[datetime] = mapped_column(TimeZone, default=timezone.now, comment="创建时间")
    updated_time: Mapped[datetime | None] = mapped_column(
        TimeZone, onupdate=timezone.now, default=None, comment="更新时间"
    )
