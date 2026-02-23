from datetime import datetime

from sqlalchemy import ARRAY, JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import MappedBase, TimeZone
from backend.database.db import uuid4_str
from backend.utils.timezone import timezone


class Board(MappedBase):
    """看板表（支持多维度组织：移动端/Web端/不同产品线）"""

    __tablename__ = "boards"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str, comment="看板ID")
    tenant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tenants.id", ondelete="CASCADE"), index=True, comment="租户ID"
    )

    # Board 基础信息
    name: Mapped[str] = mapped_column(String(100), comment='看板名称，如 "移动端反馈"')
    url_name: Mapped[str] = mapped_column(String(100), comment='URL slug，如 "mobile-feedback"')
    description: Mapped[str | None] = mapped_column(Text, default=None, comment="看板描述")

    # 访问控制
    access_mode: Mapped[str] = mapped_column(
        String(20), default="private", comment="访问模式: public, private, restricted"
    )
    allowed_user_ids: Mapped[list | None] = mapped_column(
        ARRAY(String), default=None, comment="restricted 模式下允许访问的用户 ID 列表"
    )

    # 分类/标签
    category: Mapped[str | None] = mapped_column(String(50), default=None, comment="看板分类，如 mobile, web, api")
    tags: Mapped[list | None] = mapped_column(ARRAY(String), default=None, comment="看板标签")

    # 统计（通过触发器自动更新）
    feedback_count: Mapped[int] = mapped_column(default=0, comment="反馈数量")
    topic_count: Mapped[int] = mapped_column(default=0, comment="主题数量")

    # 配置
    settings: Mapped[dict | None] = mapped_column(JSON, default=None, comment="Board 特定配置")

    # 排序与显示
    sort_order: Mapped[int] = mapped_column(default=0, comment="排序顺序")
    is_archived: Mapped[bool] = mapped_column(default=False, comment="是否归档")

    # 时间戳
    created_time: Mapped[datetime] = mapped_column(TimeZone, default=timezone.now, comment="创建时间")
    updated_time: Mapped[datetime | None] = mapped_column(
        TimeZone, onupdate=timezone.now, default=None, comment="更新时间"
    )
    deleted_at: Mapped[datetime | None] = mapped_column(TimeZone, default=None, comment="软删除时间")

    __table_args__ = (
        # tenant_id + url_name 联合唯一
        {"comment": "看板表（支持多维度组织：移动端/Web端/不同产品线）"},
    )
