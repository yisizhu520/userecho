"""工作台统计服务"""

from datetime import datetime, timedelta

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.userecho.model.feedback import Feedback
from backend.app.userecho.model.topic import Topic
from backend.common.log import log


class DashboardService:
    """工作台统计数据服务"""

    @staticmethod
    async def get_stats(db: AsyncSession, tenant_id: str) -> dict:
        """
        获取工作台所有统计数据
        
        Args:
            db: 数据库会话
            tenant_id: 租户ID
        
        Returns:
            统计数据字典
        """
        try:
            # 计算时间范围
            week_ago = datetime.now() - timedelta(days=7)
            
            # 并行执行所有查询
            feedback_stats = await DashboardService._get_feedback_stats(db, tenant_id, week_ago)
            topic_stats = await DashboardService._get_topic_stats(db, tenant_id, week_ago)
            urgent_topics = await DashboardService._get_urgent_topics(db, tenant_id)
            top_topics = await DashboardService._get_top_topics(db, tenant_id)
            weekly_trend = await DashboardService._get_weekly_trend(db, tenant_id, week_ago)
            tag_distribution = await DashboardService._get_tag_distribution(db, tenant_id)
            
            return {
                'feedback_stats': feedback_stats,
                'topic_stats': topic_stats,
                'urgent_topics': urgent_topics,
                'top_topics': top_topics,
                'weekly_trend': weekly_trend,
                'tag_distribution': tag_distribution,
            }
        except Exception as e:
            log.error(f'Failed to get dashboard stats for tenant {tenant_id}: {e}')
            raise

    @staticmethod
    async def _get_feedback_stats(
        db: AsyncSession,
        tenant_id: str,
        week_ago: datetime,
    ) -> dict:
        """获取反馈统计"""
        # 总反馈数
        total_query = select(func.count(Feedback.id)).where(
            Feedback.tenant_id == tenant_id,
            Feedback.deleted_at.is_(None),
        )
        total = await db.scalar(total_query) or 0
        
        # 待处理反馈数（未聚类）
        pending_query = select(func.count(Feedback.id)).where(
            Feedback.tenant_id == tenant_id,
            Feedback.deleted_at.is_(None),
            Feedback.topic_id.is_(None),
        )
        pending = await db.scalar(pending_query) or 0
        
        # 本周新增反馈数
        weekly_query = select(func.count(Feedback.id)).where(
            Feedback.tenant_id == tenant_id,
            Feedback.deleted_at.is_(None),
            Feedback.created_time >= week_ago,
        )
        weekly_count = await db.scalar(weekly_query) or 0
        
        return {
            'total': total,
            'pending': pending,
            'weekly_count': weekly_count,
        }

    @staticmethod
    async def _get_topic_stats(
        db: AsyncSession,
        tenant_id: str,
        week_ago: datetime,
    ) -> dict:
        """获取需求统计"""
        # 总需求数
        total_query = select(func.count(Topic.id)).where(
            Topic.tenant_id == tenant_id,
            Topic.deleted_at.is_(None),
        )
        total = await db.scalar(total_query) or 0
        
        # 待处理需求数
        pending_query = select(func.count(Topic.id)).where(
            Topic.tenant_id == tenant_id,
            Topic.deleted_at.is_(None),
            Topic.status == 'pending',
        )
        pending = await db.scalar(pending_query) or 0
        
        # 已完成需求数
        completed_query = select(func.count(Topic.id)).where(
            Topic.tenant_id == tenant_id,
            Topic.deleted_at.is_(None),
            Topic.status == 'completed',
        )
        completed = await db.scalar(completed_query) or 0
        
        # 本周新增需求数
        weekly_query = select(func.count(Topic.id)).where(
            Topic.tenant_id == tenant_id,
            Topic.deleted_at.is_(None),
            Topic.created_time >= week_ago,
        )
        weekly_count = await db.scalar(weekly_query) or 0
        
        return {
            'total': total,
            'pending': pending,
            'completed': completed,
            'weekly_count': weekly_count,
        }

    @staticmethod
    async def _get_urgent_topics(
        db: AsyncSession,
        tenant_id: str,
    ) -> list[dict]:
        """
        获取紧急需求列表 TOP 5
        
        优先级排序：
        1. 有 priority_score 的按 total_score 降序
        2. 没有 priority_score 的按 feedback_count 降序
        """
        from sqlalchemy import case
        from backend.app.userecho.model.priority_score import PriorityScore
        
        # 使用显式 LEFT JOIN 而不是 joinedload，这样可以在 ORDER BY 中引用
        query = (
            select(Topic, PriorityScore)
            .outerjoin(PriorityScore, Topic.id == PriorityScore.topic_id)
            .where(
                Topic.tenant_id == tenant_id,
                Topic.deleted_at.is_(None),
                Topic.status.in_(['pending', 'planned', 'in_progress']),
            )
            .order_by(
                # 优先按 priority_score.total_score 排序（有分数的排前面）
                case((PriorityScore.total_score.is_(None), 1), else_=0),
                desc(PriorityScore.total_score),
                # 其次按 feedback_count 排序
                desc(Topic.feedback_count),
            )
            .limit(5)
        )
        
        result = await db.execute(query)
        rows = result.all()
        
        return [
            {
                'id': topic.id,
                'title': topic.title,
                'feedback_count': topic.feedback_count,
                'priority_score': (
                    round(priority_score.total_score, 2)
                    if priority_score and priority_score.total_score
                    else None
                ),
                'category': topic.category,
                'status': topic.status,
            }
            for topic, priority_score in rows
        ]

    @staticmethod
    async def _get_top_topics(
        db: AsyncSession,
        tenant_id: str,
    ) -> list[dict]:
        """获取 TOP 需求主题 TOP 5（按反馈数量排序）"""
        query = (
            select(Topic)
            .where(
                Topic.tenant_id == tenant_id,
                Topic.deleted_at.is_(None),
            )
            .order_by(desc(Topic.feedback_count))
            .limit(5)
        )
        
        result = await db.execute(query)
        topics = result.scalars().all()
        
        return [
            {
                'id': t.id,
                'title': t.title,
                'feedback_count': t.feedback_count,
                'category': t.category,
                'status': t.status,
            }
            for t in topics
        ]

    @staticmethod
    async def _get_weekly_trend(
        db: AsyncSession,
        tenant_id: str,
        week_ago: datetime,
    ) -> list[dict]:
        """获取 7 天反馈趋势（按日期分组）"""
        query = (
            select(
                func.date(Feedback.created_time).label('date'),
                func.count(Feedback.id).label('count'),
            )
            .where(
                Feedback.tenant_id == tenant_id,
                Feedback.deleted_at.is_(None),
                Feedback.created_time >= week_ago,
            )
            .group_by(func.date(Feedback.created_time))
            .order_by(func.date(Feedback.created_time))
        )
        
        result = await db.execute(query)
        trend_data = result.all()
        
        return [
            {
                'date': str(row.date),
                'count': row.count,
            }
            for row in trend_data
        ]

    @staticmethod
    async def _get_tag_distribution(
        db: AsyncSession,
        tenant_id: str,
    ) -> list[dict]:
        """
        获取标签分布统计
        
        返回各标签的：
        - Topic 数量
        - 反馈数量总和
        - 平均优先级分数（如果有评分）
        """
        from sqlalchemy import case
        from backend.app.userecho.model.priority_score import PriorityScore
        
        # 按标签分组统计
        query = (
            select(
                Topic.category,
                func.count(Topic.id).label('topic_count'),
                func.sum(Topic.feedback_count).label('feedback_count'),
                func.avg(PriorityScore.total_score).label('avg_priority_score'),
            )
            .outerjoin(PriorityScore, Topic.id == PriorityScore.topic_id)
            .where(
                Topic.tenant_id == tenant_id,
                Topic.deleted_at.is_(None),
            )
            .group_by(Topic.category)
            .order_by(desc(func.count(Topic.id)))  # 按 Topic 数量降序
        )
        
        result = await db.execute(query)
        tag_data = result.all()
        
        # 标签名称映射
        category_names = {
            'bug': 'Bug',
            'improvement': '体验优化',
            'feature': '新功能',
            'performance': '性能问题',
            'other': '其他',
        }
        
        return [
            {
                'category': row.category,
                'name': category_names.get(row.category, row.category),
                'topic_count': row.topic_count or 0,
                'feedback_count': row.feedback_count or 0,
                'avg_priority_score': (
                    round(row.avg_priority_score, 2)
                    if row.avg_priority_score
                    else None
                ),
            }
            for row in tag_data
        ]


dashboard_service = DashboardService()
