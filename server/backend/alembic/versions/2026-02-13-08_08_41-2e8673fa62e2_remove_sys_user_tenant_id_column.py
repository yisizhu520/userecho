"""remove sys_user tenant_id column

Revision ID: 2e8673fa62e2
Revises: 2026021101
Create Date: 2026-02-13 08:08:41.773709

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2e8673fa62e2"
down_revision = "2026021101"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column("sys_user", "tenant_id")


def downgrade():
    op.add_column(
        "sys_user",
        sa.Column("tenant_id", sa.String(length=36), nullable=True, comment="租户ID"),
    )
    op.execute("UPDATE sys_user SET tenant_id = 'default-tenant' WHERE tenant_id IS NULL")
