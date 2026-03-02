from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.common.model import MappedBase, TimeZone
from backend.database.db import uuid4_str
from backend.utils.timezone import timezone

if TYPE_CHECKING:
    from backend.app.userecho.model.merge_suggestion import MergeSuggestion


class Tenant(MappedBase):
    """租户表"""

    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str, comment="租户ID")
    name: Mapped[str] = mapped_column(String(100), comment="租户名称")
    slug: Mapped[str | None] = mapped_column(String(100), unique=True, default=None, comment='URL slug，如 "acme-corp"')
    status: Mapped[str] = mapped_column(String(20), default="active", comment="状态: active, suspended, deleted")
    settings: Mapped[dict | None] = mapped_column(JSON, default=None, comment="租户配置")
    deleted_at: Mapped[datetime | None] = mapped_column(TimeZone, default=None, comment="软删除时间")

    # 时间戳字段
    created_time: Mapped[datetime] = mapped_column(TimeZone, default=timezone.now, comment="创建时间")
    updated_time: Mapped[datetime | None] = mapped_column(
        TimeZone, onupdate=timezone.now, default=None, comment="更新时间"
    )

    # 关联关系
    merge_suggestions: Mapped[list["MergeSuggestion"]] = relationship(
        "MergeSuggestion",
        back_populates="tenant",
        cascade="all, delete-orphan",
    )
