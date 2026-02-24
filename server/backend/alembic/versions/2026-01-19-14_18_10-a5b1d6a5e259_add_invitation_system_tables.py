"""add_invitation_system_tables

Revision ID: a5b1d6a5e259
Revises: de3ddd4d73c9
Create Date: 2026-01-19 14:18:10.538110

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a5b1d6a5e259"
down_revision = "de3ddd4d73c9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. 创建邀请表
    op.create_table(
        "invitations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("token", sa.String(64), unique=True, nullable=False, comment="邀请token（URL中的唯一标识）"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False, comment="过期时间"),
        sa.Column("usage_limit", sa.Integer, nullable=False, server_default="10", comment="使用次数限制"),
        sa.Column("used_count", sa.Integer, nullable=False, server_default="0", comment="已使用次数"),
        sa.Column("plan_code", sa.String(20), nullable=False, server_default="pro", comment="赋予的套餐代号"),
        sa.Column("trial_days", sa.Integer, nullable=False, server_default="90", comment="试用天数"),
        sa.Column("source", sa.String(50), nullable=True, comment="来源标签"),
        sa.Column("campaign", sa.String(100), nullable=True, comment="活动标识"),
        sa.Column("creator_id", sa.BigInteger, nullable=True, comment="创建者ID"),
        sa.Column("notes", sa.Text, nullable=True, comment="管理备注"),
        sa.Column(
            "status", sa.String(20), nullable=False, server_default="active", comment="状态: active/expired/disabled"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
            comment="创建时间",
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True, comment="更新时间"),
        sa.ForeignKeyConstraint(["creator_id"], ["sys_user.id"], ondelete="SET NULL"),
    )

    op.create_index("idx_invitations_token", "invitations", ["token"])
    op.create_index("idx_invitations_status", "invitations", ["status"])
    op.create_index("idx_invitations_expires", "invitations", ["expires_at"])
    op.create_index("idx_invitations_creator", "invitations", ["creator_id"])

    # 2. 创建邀请使用记录表
    op.create_table(
        "invitation_usage",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("invitation_id", sa.String(36), nullable=False, comment="邀请ID"),
        sa.Column("user_id", sa.BigInteger, nullable=False, comment="用户ID"),
        sa.Column("registered_email", sa.String(256), nullable=False, comment="注册邮箱"),
        sa.Column("ip_address", sa.String(45), nullable=True, comment="IPv4/IPv6"),
        sa.Column("user_agent", sa.Text, nullable=True, comment="浏览器信息"),
        sa.Column("completed_onboarding", sa.Boolean, nullable=False, server_default="false", comment="是否完成引导"),
        sa.Column("created_tenant_id", sa.String(36), nullable=True, comment="创建的租户ID"),
        sa.Column(
            "used_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()"), comment="使用时间"
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True, comment="更新时间"),
        sa.ForeignKeyConstraint(["invitation_id"], ["invitations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["sys_user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_tenant_id"], ["tenants.id"], ondelete="SET NULL"),
    )

    op.create_index("idx_invitation_usage_invitation", "invitation_usage", ["invitation_id"])
    op.create_index("idx_invitation_usage_user", "invitation_usage", ["user_id"])
    op.create_index("idx_invitation_usage_email", "invitation_usage", ["registered_email"])
    op.create_index("idx_invitation_usage_ip", "invitation_usage", ["ip_address"])
    op.create_index("idx_invitation_usage_date", "invitation_usage", ["used_at"])

    # 3. 创建邮箱黑名单表
    op.create_table(
        "email_blacklist",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("domain", sa.String(256), unique=True, nullable=False, comment="邮箱域名"),
        sa.Column(
            "type", sa.String(20), nullable=False, server_default="disposable", comment="类型: disposable/spam/banned"
        ),
        sa.Column("reason", sa.Text, nullable=True, comment="加入黑名单的原因"),
        sa.Column("added_by", sa.BigInteger, nullable=True, comment="添加人ID"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true", comment="是否启用"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
            comment="创建时间",
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True, comment="更新时间"),
        sa.ForeignKeyConstraint(["added_by"], ["sys_user.id"], ondelete="SET NULL"),
    )

    op.create_index("idx_email_blacklist_domain", "email_blacklist", ["domain"])
    op.create_index(
        "idx_email_blacklist_active", "email_blacklist", ["is_active"], postgresql_where=sa.text("is_active = true")
    )

    # 4. 创建邮箱验证记录表
    op.create_table(
        "email_verifications",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.BigInteger, nullable=False, comment="用户ID"),
        sa.Column("email", sa.String(256), nullable=False, comment="邮箱"),
        sa.Column("verification_code", sa.String(64), nullable=False, comment="验证码/token"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False, comment="验证链接过期时间"),
        sa.Column("is_verified", sa.Boolean, nullable=False, server_default="false", comment="是否已验证"),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True, comment="验证时间"),
        sa.Column("send_count", sa.Integer, nullable=False, server_default="1", comment="发送次数"),
        sa.Column(
            "last_sent_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
            comment="上次发送时间",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
            comment="创建时间",
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True, comment="更新时间"),
        sa.ForeignKeyConstraint(["user_id"], ["sys_user.id"], ondelete="CASCADE"),
    )

    op.create_index("idx_email_verifications_user", "email_verifications", ["user_id"])
    op.create_index("idx_email_verifications_email", "email_verifications", ["email"])
    op.create_index("idx_email_verifications_code", "email_verifications", ["verification_code"])
    op.create_index(
        "idx_email_verifications_active",
        "email_verifications",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("is_verified = false"),
    )

    # 5. 扩展 sys_user 表
    op.execute("""
        ALTER TABLE sys_user 
        ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE
    """)
    op.execute("""
        ALTER TABLE sys_user 
        ADD COLUMN IF NOT EXISTS invitation_id VARCHAR(36)
    """)

    # 创建外键约束（幂等性处理）
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint 
                WHERE conname = 'sys_user_invitation_id_fkey'
            ) THEN
                ALTER TABLE sys_user 
                ADD CONSTRAINT sys_user_invitation_id_fkey 
                FOREIGN KEY (invitation_id) REFERENCES invitations(id) ON DELETE SET NULL;
            END IF;
        END $$;
    """)

    # 创建索引（如果不存在）
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_sys_user_invitation ON sys_user(invitation_id)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_sys_user_email_verified ON sys_user(email_verified)
    """)


def downgrade() -> None:
    # 删除索引和字段
    op.execute("DROP INDEX IF EXISTS idx_sys_user_email_verified")
    op.execute("DROP INDEX IF EXISTS idx_sys_user_invitation")
    op.execute("ALTER TABLE sys_user DROP CONSTRAINT IF EXISTS sys_user_invitation_id_fkey")
    op.execute("ALTER TABLE sys_user DROP COLUMN IF EXISTS invitation_id")
    op.execute("ALTER TABLE sys_user DROP COLUMN IF EXISTS email_verified")

    # 删除表（按依赖顺序）
    op.drop_table("email_verifications")
    op.drop_table("email_blacklist")
    op.drop_table("invitation_usage")
    op.drop_table("invitations")
