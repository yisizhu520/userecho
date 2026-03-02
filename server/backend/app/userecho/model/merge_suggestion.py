"""合并建议模型"""

from sqlalchemy import TIMESTAMP, Column, ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION, JSONB
from sqlalchemy.orm import relationship

from backend.common.model import Base


class MergeSuggestion(Base):
    """
    合并建议表 - 聚类后发现的重复需求建议

    当聚类发现某些反馈与已有需求高度相似时（similarity >= 0.80），
    生成合并建议，由用户决策是否关联到已有需求或创建新需求。
    """

    __tablename__ = "merge_suggestion"

    id = Column(String(50), primary_key=True, comment="建议ID")
    tenant_id = Column(
        String(50),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="租户ID",
    )
    cluster_label = Column(Integer, nullable=False, comment="聚类标签")
    suggested_topic_id = Column(
        String(50),
        ForeignKey("topics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="建议关联的需求ID",
    )
    suggested_topic_title = Column(String(500), nullable=False, comment="建议关联的需求标题")
    suggested_topic_status = Column(String(50), nullable=False, comment="建议关联的需求状态")
    suggested_topic_category = Column(String(100), comment="建议关联的需求分类")
    similarity = Column(DOUBLE_PRECISION, nullable=False, comment="语义相似度 (0-1)")
    feedback_ids = Column(JSONB, nullable=False, comment="建议关联的反馈ID列表")
    feedback_count = Column(Integer, nullable=False, default=0, comment="反馈数量")
    ai_generated_title = Column(String(500), comment="AI生成的标题(供参考)")

    # 状态: pending, accepted, rejected, create_new
    status = Column(
        String(50),
        nullable=False,
        default="pending",
        index=True,
        comment="建议状态: pending(待处理), accepted(已接受-关联), rejected(已拒绝), create_new(创建新需求)",
    )
    processed_by = Column(String(50), comment="处理人ID")
    processed_at = Column(TIMESTAMP(timezone=True), comment="处理时间")

    deleted_at = Column(TIMESTAMP(timezone=True), comment="删除时间（软删除）")
    created_time = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        comment="创建时间",
    )
    updated_time = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        comment="更新时间",
    )

    # 关联关系
    tenant = relationship("Tenant", back_populates="merge_suggestions")
    topic = relationship("Topic", back_populates="merge_suggestions")
