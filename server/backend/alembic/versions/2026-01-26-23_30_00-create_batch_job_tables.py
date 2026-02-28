"""create_batch_job_tables

Revision ID: f9a8b7c6d5e4
Revises: e1a0f801a981
Create Date: 2026-01-26 23:30:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import backend.common.model

# revision identifiers, used by Alembic.
revision = "f9a8b7c6d5e4"
down_revision = "e1a0f801a981"
branch_labels = None
depends_on = None


def upgrade():
    # 创建 batch_job 表
    op.create_table(
        "batch_job",
        sa.Column("id", sa.String(length=36), nullable=False, comment="主键ID"),
        sa.Column("tenant_id", sa.String(length=36), nullable=False, comment="租户ID"),
        sa.Column("task_type", sa.String(length=50), nullable=False, comment="任务类型"),
        sa.Column("name", sa.String(length=200), nullable=True, comment="任务名称"),
        sa.Column("description", sa.Text(), nullable=True, comment="任务描述"),
        sa.Column("created_by", sa.String(length=36), nullable=True, comment="创建者ID"),
        sa.Column("total_count", sa.Integer(), nullable=False, server_default="0", comment="总任务数"),
        sa.Column("pending_count", sa.Integer(), nullable=False, server_default="0", comment="待处理数"),
        sa.Column("processing_count", sa.Integer(), nullable=False, server_default="0", comment="处理中数"),
        sa.Column("completed_count", sa.Integer(), nullable=False, server_default="0", comment="已完成数"),
        sa.Column("failed_count", sa.Integer(), nullable=False, server_default="0", comment="失败数"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending", comment="任务状态"),
        sa.Column("celery_task_id", sa.String(length=255), nullable=True, comment="Celery任务ID"),
        sa.Column("config", sa.JSON(), nullable=False, server_default="{}", comment="执行配置"),
        sa.Column("summary", sa.JSON(), nullable=False, server_default="{}", comment="结果汇总"),
        sa.Column(
            "created_time",
            backend.common.model.TimeZone(timezone=True),
            nullable=False,
            comment="创建时间",
        ),
        sa.Column(
            "updated_time",
            backend.common.model.TimeZone(timezone=True),
            nullable=True,
            comment="更新时间",
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
        comment="批量任务表",
    )

    # 创建索引
    op.create_index("idx_batch_job_tenant", "batch_job", ["tenant_id", "created_time"], unique=False)
    op.create_index("idx_batch_job_status", "batch_job", ["status", "created_time"], unique=False)
    op.create_index("idx_batch_job_type", "batch_job", ["task_type", "created_time"], unique=False)
    op.create_index("idx_batch_job_celery_task", "batch_job", ["celery_task_id"], unique=False)

    # 创建 batch_task_item 表
    op.create_table(
        "batch_task_item",
        sa.Column("id", sa.String(length=36), nullable=False, comment="主键ID"),
        sa.Column("batch_job_id", sa.String(length=36), nullable=False, comment="批量任务ID"),
        sa.Column("sequence_no", sa.Integer(), nullable=True, comment="执行顺序"),
        sa.Column("input_data", sa.JSON(), nullable=False, comment="输入数据"),
        sa.Column("output_data", sa.JSON(), nullable=True, comment="输出数据"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending", comment="任务状态"),
        sa.Column("error_message", sa.Text(), nullable=True, comment="错误信息"),
        sa.Column("error_code", sa.String(length=50), nullable=True, comment="错误码"),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0", comment="重试次数"),
        sa.Column("max_retries", sa.Integer(), nullable=False, server_default="3", comment="最大重试次数"),
        sa.Column(
            "created_time",
            backend.common.model.TimeZone(timezone=True),
            nullable=False,
            comment="创建时间",
        ),
        sa.Column(
            "updated_time",
            backend.common.model.TimeZone(timezone=True),
            nullable=True,
            comment="更新时间",
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
        sa.ForeignKeyConstraint(
            ["batch_job_id"],
            ["batch_job.id"],
            name="fk_batch_task_item_batch_job",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        comment="批量任务项表",
    )

    # 创建索引
    op.create_index("idx_task_item_batch", "batch_task_item", ["batch_job_id", "status"], unique=False)
    op.create_index("idx_task_item_status", "batch_task_item", ["status", "created_time"], unique=False)


def downgrade():
    # 删除索引
    op.drop_index("idx_task_item_status", table_name="batch_task_item")
    op.drop_index("idx_task_item_batch", table_name="batch_task_item")

    # 删除表
    op.drop_table("batch_task_item")

    op.drop_index("idx_batch_job_celery_task", table_name="batch_job")
    op.drop_index("idx_batch_job_type", table_name="batch_job")
    op.drop_index("idx_batch_job_status", table_name="batch_job")
    op.drop_index("idx_batch_job_tenant", table_name="batch_job")

    op.drop_table("batch_job")
