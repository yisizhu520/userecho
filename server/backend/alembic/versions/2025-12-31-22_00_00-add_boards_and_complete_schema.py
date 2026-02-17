"""add boards tenant_users and complete schema

Revision ID: 20251231b
Revises: 20251231a
Create Date: 2025-12-31 22:00:00.000000

根据 final-complete-schema.md 完成完整改造：
1. 新建 boards 表（看板表）
2. 新建 tenant_users 表（租户-用户关联表）
3. 新建 tenant_user_roles 表（租户用户角色关联表）
4. tenants 表新增 slug、settings 字段
5. customers 表新增多个字段
6. feedbacks 表新增 board_id、title 等字段
7. topics 表新增 board_id、tech_lead_id 等字段
8. 更新触发器以支持 Board 统计
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20251231b'
down_revision: str | None = '20251231a'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """完整数据库改造"""

    print('🔧 开始完整数据库改造...')

    # 1. 创建 boards 表
    print('   ├─ [1/7] 创建 boards 表...')
    op.create_table(
        'boards',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False, comment='看板名称'),
        sa.Column('url_name', sa.String(100), nullable=False, comment='URL slug'),
        sa.Column('description', sa.Text(), nullable=True, comment='看板描述'),
        sa.Column('access_mode', sa.String(20), server_default='private', comment='访问模式'),
        sa.Column('allowed_user_ids', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('category', sa.String(50), nullable=True, comment='看板分类'),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('feedback_count', sa.Integer(), server_default='0'),
        sa.Column('topic_count', sa.Integer(), server_default='0'),
        sa.Column('settings', postgresql.JSONB(), nullable=True),
        sa.Column('sort_order', sa.Integer(), server_default='0'),
        sa.Column('is_archived', sa.Boolean(), server_default='false'),
        sa.Column('created_time', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_time', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('tenant_id', 'url_name', name='uq_board_tenant_url'),
    )
    op.create_index('idx_boards_tenant', 'boards', ['tenant_id'])
    op.create_index('idx_boards_category', 'boards', ['category'])

    # 2. 创建 tenant_users 表
    print('   ├─ [2/7] 创建 tenant_users 表...')
    op.create_table(
        'tenant_users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.BigInteger(), sa.ForeignKey('sys_user.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_type', sa.String(20), server_default='member', comment='用户类型'),
        sa.Column('department_id', sa.BigInteger(), sa.ForeignKey('sys_dept.id', ondelete='SET NULL'), nullable=True),
        sa.Column('feedback_count', sa.Integer(), server_default='0'),
        sa.Column('status', sa.String(20), server_default='active'),
        sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('last_active_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('tenant_id', 'user_id', name='uq_tenant_user'),
    )
    op.create_index('idx_tenant_users_tenant', 'tenant_users', ['tenant_id'])
    op.create_index('idx_tenant_users_user', 'tenant_users', ['user_id'])

    # 3. 创建 tenant_user_roles 表
    print('   ├─ [3/7] 创建 tenant_user_roles 表...')
    op.create_table(
        'tenant_user_roles',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column(
            'tenant_user_id', sa.String(36), sa.ForeignKey('tenant_users.id', ondelete='CASCADE'), nullable=False
        ),
        sa.Column('role_id', sa.BigInteger(), sa.ForeignKey('sys_role.id', ondelete='CASCADE'), nullable=False),
        sa.Column('assigned_by', sa.BigInteger(), sa.ForeignKey('sys_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('assigned_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('tenant_user_id', 'role_id', name='uq_tenant_user_role'),
    )
    op.create_index('idx_tenant_user_roles_tenant_user', 'tenant_user_roles', ['tenant_user_id'])

    # 4. tenants 表新增字段
    print('   ├─ [4/7] tenants 表新增 slug、settings 字段...')
    op.add_column('tenants', sa.Column('slug', sa.String(100), unique=True, nullable=True))
    op.add_column('tenants', sa.Column('settings', postgresql.JSONB(), nullable=True))

    # 5. customers 表新增字段
    print('   ├─ [5/7] customers 表新增多个字段...')
    op.add_column('customers', sa.Column('company_name', sa.String(200), nullable=True))
    op.add_column('customers', sa.Column('contact_email', sa.String(255), nullable=True))
    op.add_column('customers', sa.Column('contact_phone', sa.String(50), nullable=True))
    op.add_column('customers', sa.Column('customer_tier', sa.String(20), server_default='normal'))
    op.add_column('customers', sa.Column('arr', sa.Numeric(10, 2), nullable=True))
    op.add_column('customers', sa.Column('churn_risk', sa.String(20), server_default='low'))
    op.add_column('customers', sa.Column('contract_start_date', sa.Date(), nullable=True))
    op.add_column('customers', sa.Column('contract_end_date', sa.Date(), nullable=True))
    op.add_column('customers', sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True))
    op.add_column('customers', sa.Column('source', sa.String(50), nullable=True))
    op.add_column('customers', sa.Column('notes', sa.Text(), nullable=True))

    # 6. feedbacks 表新增字段
    print('   ├─ [6/7] feedbacks 表新增 board_id、title 等字段...')
    op.add_column(
        'feedbacks', sa.Column('board_id', sa.String(36), sa.ForeignKey('boards.id', ondelete='CASCADE'), nullable=True)
    )
    op.add_column('feedbacks', sa.Column('title', sa.String(400), nullable=True))
    op.add_column('feedbacks', sa.Column('is_anonymous', sa.Boolean(), server_default='false'))
    op.add_column('feedbacks', sa.Column('anonymous_email', sa.String(255), nullable=True))
    op.add_column('feedbacks', sa.Column('images_metadata', postgresql.JSONB(), nullable=True))
    op.add_column('feedbacks', sa.Column('priority', sa.String(20), nullable=True))
    op.create_index('idx_feedbacks_board', 'feedbacks', ['board_id'])

    # 7. topics 表新增字段
    print('   ├─ [7/7] topics 表新增 board_id、tech_lead_id 等字段...')
    op.add_column(
        'topics', sa.Column('board_id', sa.String(36), sa.ForeignKey('boards.id', ondelete='CASCADE'), nullable=True)
    )
    op.add_column(
        'topics',
        sa.Column('tech_lead_id', sa.BigInteger(), sa.ForeignKey('sys_user.id', ondelete='SET NULL'), nullable=True),
    )
    op.add_column('topics', sa.Column('actual_release_date', sa.Date(), nullable=True))
    op.add_column('topics', sa.Column('total_arr', sa.Numeric(10, 2), server_default='0'))
    op.add_column('topics', sa.Column('high_risk_customer_count', sa.Integer(), server_default='0'))
    op.add_column('topics', sa.Column('slug', sa.String(200), unique=True, nullable=True))
    op.add_column('topics', sa.Column('is_public', sa.Boolean(), server_default='false'))
    op.create_index('idx_topics_board', 'topics', ['board_id'])

    # 8. 创建 Board 统计触发器（仅 PostgreSQL）
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        print('   ├─ [8/8] 创建 Board 统计触发器...')

        op.execute("""
            CREATE OR REPLACE FUNCTION update_board_stats()
            RETURNS TRIGGER AS $$
            DECLARE
                v_board_id VARCHAR(36);
            BEGIN
                IF TG_OP = 'DELETE' THEN
                    v_board_id := OLD.board_id;
                ELSE
                    v_board_id := NEW.board_id;
                END IF;

                IF v_board_id IS NOT NULL THEN
                    UPDATE boards SET
                        feedback_count = (
                            SELECT COUNT(*) FROM feedbacks
                            WHERE board_id = v_board_id AND deleted_at IS NULL
                        ),
                        topic_count = (
                            SELECT COUNT(*) FROM topics
                            WHERE board_id = v_board_id AND deleted_at IS NULL
                        ),
                        updated_time = NOW()
                    WHERE id = v_board_id;
                END IF;

                RETURN COALESCE(NEW, OLD);
            END;
            $$ LANGUAGE plpgsql;
        """)

        # 先删除旧触发器
        op.execute('DROP TRIGGER IF EXISTS trigger_update_board_stats_from_feedbacks ON feedbacks')

        # 创建新触发器
        op.execute("""
            CREATE TRIGGER trigger_update_board_stats_from_feedbacks
            AFTER INSERT OR UPDATE OF board_id, deleted_at OR DELETE ON feedbacks
            FOR EACH ROW
            EXECUTE FUNCTION update_board_stats()
        """)

        # 先删除旧触发器
        op.execute('DROP TRIGGER IF EXISTS trigger_update_board_stats_from_topics ON topics')

        # 创建新触发器
        op.execute("""
            CREATE TRIGGER trigger_update_board_stats_from_topics
            AFTER INSERT OR UPDATE OF board_id, deleted_at OR DELETE ON topics
            FOR EACH ROW
            EXECUTE FUNCTION update_board_stats()
        """)

    print('✅ 完整数据库改造完成！')
    print()
    print('📊 新增表：')
    print('   - boards: 看板表')
    print('   - tenant_users: 租户-用户关联表')
    print('   - tenant_user_roles: 租户用户角色关联表')
    print()
    print('📝 更新表：')
    print('   - tenants: +2 字段')
    print('   - customers: +11 字段')
    print('   - feedbacks: +6 字段')
    print('   - topics: +7 字段')


def downgrade() -> None:
    """回滚完整数据库改造"""

    print('🔧 开始回滚...')

    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute('DROP TRIGGER IF EXISTS trigger_update_board_stats_from_topics ON topics')
        op.execute('DROP TRIGGER IF EXISTS trigger_update_board_stats_from_feedbacks ON feedbacks')
        op.execute('DROP FUNCTION IF EXISTS update_board_stats')

    # topics 表
    op.drop_index('idx_topics_board', table_name='topics')
    op.drop_column('topics', 'is_public')
    op.drop_column('topics', 'slug')
    op.drop_column('topics', 'high_risk_customer_count')
    op.drop_column('topics', 'total_arr')
    op.drop_column('topics', 'actual_release_date')
    op.drop_column('topics', 'tech_lead_id')
    op.drop_column('topics', 'board_id')

    # feedbacks 表
    op.drop_index('idx_feedbacks_board', table_name='feedbacks')
    op.drop_column('feedbacks', 'priority')
    op.drop_column('feedbacks', 'images_metadata')
    op.drop_column('feedbacks', 'anonymous_email')
    op.drop_column('feedbacks', 'is_anonymous')
    op.drop_column('feedbacks', 'title')
    op.drop_column('feedbacks', 'board_id')

    # customers 表
    op.drop_column('customers', 'notes')
    op.drop_column('customers', 'source')
    op.drop_column('customers', 'tags')
    op.drop_column('customers', 'contract_end_date')
    op.drop_column('customers', 'contract_start_date')
    op.drop_column('customers', 'churn_risk')
    op.drop_column('customers', 'arr')
    op.drop_column('customers', 'customer_tier')
    op.drop_column('customers', 'contact_phone')
    op.drop_column('customers', 'contact_email')
    op.drop_column('customers', 'company_name')

    # tenants 表
    op.drop_column('tenants', 'settings')
    op.drop_column('tenants', 'slug')

    # 删除新表
    op.drop_table('tenant_user_roles')
    op.drop_table('tenant_users')
    op.drop_index('idx_boards_category', table_name='boards')
    op.drop_index('idx_boards_tenant', table_name='boards')
    op.drop_table('boards')

    print('✅ 回滚完成！')
