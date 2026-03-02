"""add merge suggestion table

Revision ID: 202602050100
Revises: bb76b0b29f3d
Create Date: 2026-02-05 01:00:00

持久化合并建议表，支持聚类后的重复需求检测和用户决策追溯
"""

from alembic import op

revision = "202602050100"
down_revision = "bb76b0b29f3d"  # 指向正确的父节点
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建 merge_suggestion 表
    op.execute("""
        CREATE TABLE IF NOT EXISTS merge_suggestion (
            id VARCHAR(50) PRIMARY KEY,
            tenant_id VARCHAR(50) NOT NULL,
            cluster_label INTEGER NOT NULL,
            suggested_topic_id VARCHAR(50) NOT NULL,
            suggested_topic_title VARCHAR(500) NOT NULL,
            suggested_topic_status VARCHAR(50) NOT NULL,
            suggested_topic_category VARCHAR(100),
            similarity DOUBLE PRECISION NOT NULL,
            feedback_ids JSONB NOT NULL,
            feedback_count INTEGER NOT NULL DEFAULT 0,
            ai_generated_title VARCHAR(500),
            status VARCHAR(50) NOT NULL DEFAULT 'pending',
            processed_by VARCHAR(50),
            processed_at TIMESTAMP WITH TIME ZONE,
            deleted_at TIMESTAMP WITH TIME ZONE,
            created_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT fk_merge_suggestion_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
            CONSTRAINT fk_merge_suggestion_topic FOREIGN KEY (suggested_topic_id) REFERENCES topics(id) ON DELETE CASCADE
        );
    """)

    # 创建索引
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_merge_suggestion_tenant 
        ON merge_suggestion(tenant_id) 
        WHERE deleted_at IS NULL;
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_merge_suggestion_status 
        ON merge_suggestion(tenant_id, status) 
        WHERE deleted_at IS NULL;
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_merge_suggestion_topic 
        ON merge_suggestion(suggested_topic_id) 
        WHERE deleted_at IS NULL;
    """)

    # 添加注释（分开执行，asyncpg 不支持多语句）
    op.execute("COMMENT ON TABLE merge_suggestion IS '合并建议表 - 聚类后发现的重复需求建议'")
    op.execute(
        "COMMENT ON COLUMN merge_suggestion.status IS '建议状态: pending(待处理), accepted(已接受-关联), rejected(已拒绝), create_new(创建新需求)'"
    )
    op.execute("COMMENT ON COLUMN merge_suggestion.similarity IS '语义相似度 (0-1)'")
    op.execute("COMMENT ON COLUMN merge_suggestion.feedback_ids IS '建议关联的反馈ID列表'")
    op.execute("COMMENT ON COLUMN merge_suggestion.ai_generated_title IS 'AI生成的标题(供参考)'")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS merge_suggestion;")
