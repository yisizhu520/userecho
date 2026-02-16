"""add weight fields and topic stats trigger

Revision ID: 20251231a
Revises: 2025122911
Create Date: 2025-12-31 21:30:00.000000

根据 final-database-design.md 新增：
1. customers.mrr - 客户月收入
2. feedbacks.customer_mrr, customer_type - 冗余字段用于权重聚合
3. topics 权重聚合字段和产品管理字段
4. 触发器函数自动更新 Topic 统计
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '20251231a'
down_revision: Union[str, None] = '2025122911'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """新增权重相关字段和触发器"""
    
    print('🔧 开始数据库改造...')
    
    # 1. customers 表新增 mrr 字段
    print('   ├─ [1/4] customers 表新增 mrr 字段...')
    op.add_column('customers', sa.Column(
        'mrr', sa.Numeric(10, 2), nullable=True, comment='月收入 (MRR)'
    ))
    
    # 2. feedbacks 表新增冗余字段
    print('   ├─ [2/4] feedbacks 表新增冗余字段...')
    op.add_column('feedbacks', sa.Column(
        'customer_mrr', sa.Numeric(10, 2), nullable=True, 
        comment='客户月收入（冗余字段，便于聚合）'
    ))
    op.add_column('feedbacks', sa.Column(
        'customer_type', sa.String(20), nullable=True, 
        comment='客户类型（冗余字段）'
    ))
    
    # 3. topics 表新增权重聚合字段和产品管理字段
    print('   ├─ [3/4] topics 表新增权重聚合和产品管理字段...')
    # 权重聚合字段
    op.add_column('topics', sa.Column(
        'affected_customer_count', sa.Integer(), nullable=False, server_default='0',
        comment='受影响客户数量（去重）'
    ))
    op.add_column('topics', sa.Column(
        'total_mrr', sa.Numeric(10, 2), nullable=False, server_default='0',
        comment='关联客户 MRR 总和'
    ))
    op.add_column('topics', sa.Column(
        'avg_sentiment_score', sa.Float(), nullable=True,
        comment='平均情感分数'
    ))
    # 产品经理评估字段
    op.add_column('topics', sa.Column(
        'impact_scope', sa.Integer(), nullable=True,
        comment='影响范围评分 (1-10)'
    ))
    op.add_column('topics', sa.Column(
        'dev_cost_estimate', sa.Integer(), nullable=True,
        comment='开发成本评分 (1-10)'
    ))
    op.add_column('topics', sa.Column(
        'product_owner_id', sa.Integer(), sa.ForeignKey('sys_user.id', ondelete='SET NULL'),
        nullable=True, comment='产品负责人'
    ))
    op.add_column('topics', sa.Column(
        'estimated_release_date', sa.Date(), nullable=True,
        comment='预计发布日期'
    ))
    # 外部集成字段
    op.add_column('topics', sa.Column(
        'jira_issue_key', sa.String(50), nullable=True,
        comment='Jira Issue Key'
    ))
    op.add_column('topics', sa.Column(
        'tapd_story_id', sa.String(50), nullable=True,
        comment='Tapd Story ID'
    ))
    
    # 4. 创建触发器函数（仅 PostgreSQL）
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        print('   ├─ [4/4] 创建 Topic 统计触发器...')
        
        # 创建触发器函数
        op.execute('''
            CREATE OR REPLACE FUNCTION update_topic_stats()
            RETURNS TRIGGER AS $$
            DECLARE
                v_topic_id VARCHAR(36);
            BEGIN
                -- 确定需要更新的 topic_id
                IF TG_OP = 'DELETE' THEN
                    v_topic_id := OLD.topic_id;
                ELSIF TG_OP = 'UPDATE' THEN
                    -- 更新时需要处理新旧两个 topic
                    IF OLD.topic_id IS NOT NULL AND OLD.topic_id != COALESCE(NEW.topic_id, '') THEN
                        -- 更新旧 topic 的统计
                        UPDATE topics SET
                            feedback_count = (
                                SELECT COUNT(*) FROM feedbacks 
                                WHERE topic_id = OLD.topic_id AND deleted_at IS NULL
                            ),
                            affected_customer_count = (
                                SELECT COUNT(DISTINCT customer_id) FROM feedbacks 
                                WHERE topic_id = OLD.topic_id AND deleted_at IS NULL AND customer_id IS NOT NULL
                            ),
                            total_mrr = COALESCE((
                                SELECT SUM(customer_mrr) FROM feedbacks 
                                WHERE topic_id = OLD.topic_id AND deleted_at IS NULL
                            ), 0),
                            avg_sentiment_score = (
                                SELECT AVG(sentiment_score) FROM feedbacks 
                                WHERE topic_id = OLD.topic_id AND deleted_at IS NULL AND sentiment_score IS NOT NULL
                            ),
                            updated_time = NOW()
                        WHERE id = OLD.topic_id;
                    END IF;
                    v_topic_id := NEW.topic_id;
                ELSE
                    v_topic_id := NEW.topic_id;
                END IF;
                
                -- 更新新 topic 的统计
                IF v_topic_id IS NOT NULL THEN
                    UPDATE topics SET
                        feedback_count = (
                            SELECT COUNT(*) FROM feedbacks 
                            WHERE topic_id = v_topic_id AND deleted_at IS NULL
                        ),
                        affected_customer_count = (
                            SELECT COUNT(DISTINCT customer_id) FROM feedbacks 
                            WHERE topic_id = v_topic_id AND deleted_at IS NULL AND customer_id IS NOT NULL
                        ),
                        total_mrr = COALESCE((
                            SELECT SUM(customer_mrr) FROM feedbacks 
                            WHERE topic_id = v_topic_id AND deleted_at IS NULL
                        ), 0),
                        avg_sentiment_score = (
                            SELECT AVG(sentiment_score) FROM feedbacks 
                            WHERE topic_id = v_topic_id AND deleted_at IS NULL AND sentiment_score IS NOT NULL
                        ),
                        updated_time = NOW()
                    WHERE id = v_topic_id;
                END IF;
                
                IF TG_OP = 'DELETE' THEN
                    RETURN OLD;
                ELSE
                    RETURN NEW;
                END IF;
            END;
            $$ LANGUAGE plpgsql;
        ''')
        
        # 先删除旧触发器（如果存在）
        op.execute('DROP TRIGGER IF EXISTS trigger_update_topic_stats ON feedbacks')
        
        # 创建新触发器
        op.execute('''
            CREATE TRIGGER trigger_update_topic_stats
            AFTER INSERT OR UPDATE OF topic_id, customer_mrr, deleted_at OR DELETE ON feedbacks
            FOR EACH ROW
            EXECUTE FUNCTION update_topic_stats()
        ''')
        
        print('✅ 数据库改造完成！')
        print('')
        print('📊 新增字段：')
        print('   - customers.mrr: 月收入')
        print('   - feedbacks.customer_mrr, customer_type: 冗余字段')
        print('   - topics: 10 个新字段（权重聚合 + 产品管理 + 外部集成）')
        print('')
        print('🔄 触发器：')
        print('   - trigger_update_topic_stats: 自动更新 Topic 统计')
    else:
        print('   ⚠️  触发器仅支持 PostgreSQL，已跳过')


def downgrade() -> None:
    """回滚：删除新增的字段和触发器"""
    
    print('🔧 开始回滚数据库改造...')
    
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        # 删除触发器和函数
        print('   ├─ 删除触发器...')
        op.execute('DROP TRIGGER IF EXISTS trigger_update_topic_stats ON feedbacks')
        op.execute('DROP FUNCTION IF EXISTS update_topic_stats')
    
    # 删除 topics 表新增字段
    print('   ├─ 删除 topics 表新增字段...')
    op.drop_column('topics', 'tapd_story_id')
    op.drop_column('topics', 'jira_issue_key')
    op.drop_column('topics', 'estimated_release_date')
    op.drop_column('topics', 'product_owner_id')
    op.drop_column('topics', 'dev_cost_estimate')
    op.drop_column('topics', 'impact_scope')
    op.drop_column('topics', 'avg_sentiment_score')
    op.drop_column('topics', 'total_mrr')
    op.drop_column('topics', 'affected_customer_count')
    
    # 删除 feedbacks 表新增字段
    print('   ├─ 删除 feedbacks 表新增字段...')
    op.drop_column('feedbacks', 'customer_type')
    op.drop_column('feedbacks', 'customer_mrr')
    
    # 删除 customers 表新增字段
    print('   ├─ 删除 customers 表新增字段...')
    op.drop_column('customers', 'mrr')
    
    print('✅ 回滚完成！')
