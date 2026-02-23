"""add_tenant_config_table

Revision ID: add_tenant_config_table
Revises: 27752692c03c
Create Date: 2025-12-25 14:00:00.000000

添加租户配置表 (userecho_tenant_config)

支持租户级别的功能配置，采用分组 JSON 存储方式：
- clustering: 聚类配置（预设模式、技术参数）
- notification: 通知配置（未来扩展）
- display: 展示配置（未来扩展）
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "add_tenant_config_table"
down_revision = "27752692c03c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    升级：创建租户配置表
    """
    bind = op.get_bind()

    # 创建表
    op.create_table(
        "userecho_tenant_config",
        sa.Column("id", sa.String(36), primary_key=True, comment="配置ID"),
        sa.Column(
            "tenant_id",
            sa.String(36),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
            comment="租户ID",
        ),
        sa.Column("config_group", sa.String(32), nullable=False, comment="配置分组（clustering/notification/display）"),
        sa.Column(
            "config_data",
            sa.JSON() if bind.dialect.name == "postgresql" else sa.Text(),
            nullable=False,
            comment="配置数据（JSON格式）",
        ),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False, comment="是否启用"),
        sa.Column("created_time", sa.DateTime(), nullable=False, server_default=sa.func.now(), comment="创建时间"),
        sa.Column("updated_time", sa.DateTime(), onupdate=sa.func.now(), comment="更新时间"),
        sa.Column("deleted_at", sa.DateTime(), nullable=True, comment="删除时间（软删除）"),
        sa.Column("del_flag", sa.Boolean(), default=False, nullable=False, comment="删除标记"),
    )

    # 创建唯一约束：每个租户的每个配置组只能有一条记录
    op.create_unique_constraint("uq_tenant_config", "userecho_tenant_config", ["tenant_id", "config_group"])

    # 创建复合索引（用于快速查询）
    op.create_index("idx_tenant_group_active", "userecho_tenant_config", ["tenant_id", "config_group", "is_active"])


def downgrade() -> None:
    """
    降级：删除租户配置表
    """
    # 删除索引
    op.drop_index("idx_tenant_group_active", table_name="userecho_tenant_config")

    # 删除唯一约束
    op.drop_constraint("uq_tenant_config", "userecho_tenant_config", type_="unique")

    # 删除表
    op.drop_table("userecho_tenant_config")
