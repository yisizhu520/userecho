"""create_task_record_table

Revision ID: a3f7b8c9d0e1
Revises: 1088af5f70cf
Create Date: 2026-02-06 10:00:00.000000

"""

import sqlalchemy as sa

import backend.common.model
from alembic import op

# revision identifiers, used by Alembic.
revision = "a3f7b8c9d0e1"
down_revision = "1088af5f70cf"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "task_record",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False, comment="自增主键"),
        sa.Column("tenant_id", sa.String(36), nullable=False, comment="租户ID"),
        sa.Column("task_category", sa.String(50), nullable=False, comment="任务分类"),
        sa.Column("task_display_name", sa.String(100), nullable=False, comment="任务可读名称"),
        sa.Column("celery_task_id", sa.String(155), nullable=False, comment="Celery任务ID"),
        sa.Column("celery_task_name", sa.String(155), nullable=False, comment="Celery任务注册名"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending", comment="任务状态"),
        sa.Column("context", sa.JSON(), nullable=True, comment="业务上下文"),
        sa.Column("result_summary", sa.JSON(), nullable=True, comment="结果摘要"),
        sa.Column("batch_job_id", sa.String(36), nullable=True, comment="关联批量任务ID"),
        sa.Column("duration_ms", sa.Integer(), nullable=True, comment="执行耗时(ms)"),
        sa.Column("error_message", sa.Text(), nullable=True, comment="错误信息"),
        sa.Column(
            "created_time",
            backend.common.model.TimeZone(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
            comment="创建时间",
        ),
        sa.Column(
            "started_time",
            backend.common.model.TimeZone(timezone=True),
            nullable=True,
            comment="开始时间",
        ),
        sa.Column(
            "completed_time",
            backend.common.model.TimeZone(timezone=True),
            nullable=True,
            comment="完成时间",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("celery_task_id"),
        comment="统一任务追踪记录",
    )

    # 核心查询索引
    op.create_index("idx_task_record_tenant_id", "task_record", ["tenant_id"])
    op.create_index("idx_task_record_tenant_time", "task_record", ["tenant_id", "created_time"])
    op.create_index("idx_task_record_category_time", "task_record", ["task_category", "created_time"])
    op.create_index("idx_task_record_batch_job_id", "task_record", ["batch_job_id"])

    # 部分索引：只索引非成功状态的记录（用于监控告警查询）
    op.execute("CREATE INDEX idx_task_record_status_pending ON task_record (status) WHERE status NOT IN ('success')")


def downgrade():
    op.execute("DROP INDEX IF EXISTS idx_task_record_status_pending")
    op.drop_index("idx_task_record_batch_job_id", table_name="task_record")
    op.drop_index("idx_task_record_category_time", table_name="task_record")
    op.drop_index("idx_task_record_tenant_time", table_name="task_record")
    op.drop_index("idx_task_record_tenant_id", table_name="task_record")
    op.drop_table("task_record")
