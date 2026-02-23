"""工作台统计服务"""

import operator

from datetime import datetime, timedelta

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.userecho.model.customer import Customer
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
            # 新增：待决策主题（带 MVP 优先级评分）
            pending_decisions = await DashboardService._get_pending_decisions(db, tenant_id)
            # 新增：客户统计
            customer_stats = await DashboardService._get_customer_stats(db, tenant_id, week_ago)
            # 新增：需求转化漏斗
            conversion_funnel = await DashboardService._get_conversion_funnel(db, tenant_id)

            return {
                "feedback_stats": feedback_stats,
                "topic_stats": topic_stats,
                "urgent_topics": urgent_topics,  # 保留向后兼容
                "pending_decisions": pending_decisions,  # 新增
                "top_topics": top_topics,
                "weekly_trend": weekly_trend,
                "tag_distribution": tag_distribution,
                "customer_stats": customer_stats,
                "conversion_funnel": conversion_funnel,
            }
        except Exception as e:
            log.error(f"Failed to get dashboard stats for tenant {tenant_id}: {e}")
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
            "total": total,
            "pending": pending,
            "weekly_count": weekly_count,
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
            Topic.status == "pending",
        )
        pending = await db.scalar(pending_query) or 0

        # 已完成需求数
        completed_query = select(func.count(Topic.id)).where(
            Topic.tenant_id == tenant_id,
            Topic.deleted_at.is_(None),
            Topic.status == "completed",
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
            "total": total,
            "pending": pending,
            "completed": completed,
            "weekly_count": weekly_count,
        }

    @staticmethod
    async def _get_customer_stats(
        db: AsyncSession,
        tenant_id: str,
        week_ago: datetime,
    ) -> dict:
        """获取客户统计"""
        # 总客户数
        total_query = select(func.count(Customer.id)).where(
            Customer.tenant_id == tenant_id,
            Customer.deleted_at.is_(None),
        )
        total = await db.scalar(total_query) or 0

        # 本周新增客户
        new_query = select(func.count(Customer.id)).where(
            Customer.tenant_id == tenant_id,
            Customer.deleted_at.is_(None),
            Customer.created_time >= week_ago,
        )
        new_count = await db.scalar(new_query) or 0

        # 活跃客户（本周提交过反馈的客户）
        active_query = select(func.count(func.distinct(Feedback.customer_id))).where(
            Feedback.tenant_id == tenant_id,
            Feedback.deleted_at.is_(None),
            Feedback.created_time >= week_ago,
            Feedback.author_type == "customer",
        )
        active_count = await db.scalar(active_query) or 0

        # 客户类型分布
        type_dist_query = (
            select(
                Customer.customer_type,
                func.count(Customer.id).label("count"),
            )
            .where(
                Customer.tenant_id == tenant_id,
                Customer.deleted_at.is_(None),
            )
            .group_by(Customer.customer_type)
            .order_by(desc(func.count(Customer.id)))
        )
        type_dist_result = await db.execute(type_dist_query)
        type_dist_rows = type_dist_result.all()

        type_name_map = {
            "strategic": "战略客户",
            "vip": "VIP客户",
            "paid": "付费客户",
            "normal": "普通客户",
        }
        type_distribution = [
            {
                "type": row.customer_type,
                "name": type_name_map.get(row.customer_type, row.customer_type),
                "count": row.count,
            }
            for row in type_dist_rows
        ]

        # MRR 总额
        mrr_query = select(func.sum(Customer.mrr)).where(
            Customer.tenant_id == tenant_id,
            Customer.deleted_at.is_(None),
            Customer.mrr.isnot(None),
        )
        total_mrr = await db.scalar(mrr_query) or 0

        # 高价值客户 Top 5（按 MRR 排序）
        top_customers_query = (
            select(
                Customer.id,
                Customer.name,
                Customer.company_name,
                Customer.customer_type,
                Customer.mrr,
            )
            .where(
                Customer.tenant_id == tenant_id,
                Customer.deleted_at.is_(None),
                Customer.mrr.isnot(None),
                Customer.mrr > 0,
            )
            .order_by(desc(Customer.mrr))
            .limit(5)
        )
        top_customers_result = await db.execute(top_customers_query)
        top_customers_rows = top_customers_result.all()

        # 获取这些客户的反馈数量
        top_customer_ids = [row.id for row in top_customers_rows]
        feedback_counts: dict[str, int] = {}
        if top_customer_ids:
            feedback_count_query = (
                select(
                    Feedback.customer_id,
                    func.count(Feedback.id).label("count"),
                )
                .where(
                    Feedback.customer_id.in_(top_customer_ids),
                    Feedback.deleted_at.is_(None),
                )
                .group_by(Feedback.customer_id)
            )
            fc_result = await db.execute(feedback_count_query)
            feedback_counts = {row.customer_id: row.count for row in fc_result.all()}

        top_customers = [
            {
                "id": row.id,
                "name": row.company_name or row.name,
                "customer_type": row.customer_type,
                "mrr": float(row.mrr) if row.mrr else 0,
                "feedback_count": feedback_counts.get(row.id, 0),
            }
            for row in top_customers_rows
        ]

        return {
            "total": total,
            "new_count": new_count,
            "active_7d": active_count,
            "type_distribution": type_distribution,
            "total_mrr": float(total_mrr) if total_mrr else 0,
            "top_customers": top_customers,
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
                Topic.status.in_(["pending", "planned", "in_progress"]),
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
                "id": topic.id,
                "title": topic.title,
                "feedback_count": topic.feedback_count,
                "priority_score": (
                    round(priority_score.total_score, 2) if priority_score and priority_score.total_score else None
                ),
                "category": topic.category,
                "status": topic.status,
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
                "id": t.id,
                "title": t.title,
                "feedback_count": t.feedback_count,
                "category": t.category,
                "status": t.status,
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
                func.date(Feedback.created_time).label("date"),
                func.count(Feedback.id).label("count"),
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
                "date": str(row.date),
                "count": row.count,
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
        from backend.app.userecho.model.priority_score import PriorityScore

        # 按标签分组统计
        query = (
            select(
                Topic.category,
                func.count(Topic.id).label("topic_count"),
                func.sum(Topic.feedback_count).label("feedback_count"),
                func.avg(PriorityScore.total_score).label("avg_priority_score"),
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
            "bug": "Bug",
            "improvement": "体验优化",
            "feature": "新功能",
            "performance": "性能问题",
            "other": "其他",
        }

        return [
            {
                "category": row.category,
                "name": category_names.get(row.category, row.category),
                "topic_count": row.topic_count or 0,
                "feedback_count": row.feedback_count or 0,
                "avg_priority_score": (round(row.avg_priority_score, 2) if row.avg_priority_score else None),
            }
            for row in tag_data
        ]

    @staticmethod
    async def _get_pending_decisions(
        db: AsyncSession,
        tenant_id: str,
    ) -> list[dict]:
        """
        获取待决策主题列表 TOP 5（带 MVP 优先级评分）

        用于工作台「今日待决策」卡片
        """
        from backend.app.userecho.api.v1.tenant_config import DEFAULT_STRATEGIC_KEYWORDS
        from backend.app.userecho.service.priority_calculator import priority_calculator
        from backend.app.userecho.service.tenant_config_service import tenant_config_service

        # 1. 获取战略关键词配置
        strategic_config = await tenant_config_service.get_config(
            db=db,
            tenant_id=tenant_id,
            config_group="strategic",
            default={"keywords": DEFAULT_STRATEGIC_KEYWORDS},
        )
        strategic_keywords = strategic_config.get("keywords", [])

        # 2. 查询待决策主题（pending 状态，按反馈数量排序）
        query = (
            select(Topic)
            .where(
                Topic.tenant_id == tenant_id,
                Topic.deleted_at.is_(None),
                Topic.status == "pending",  # 仅待决策的主题
            )
            .order_by(desc(Topic.feedback_count))
            .limit(5)
        )

        result = await db.execute(query)
        topics = result.scalars().all()

        if not topics:
            return []

        # 3. 批量获取每个主题的反馈内容
        topic_ids = [t.id for t in topics]
        feedback_query = select(Feedback.topic_id, Feedback.content, Feedback.created_time).where(
            Feedback.topic_id.in_(topic_ids),
            Feedback.deleted_at.is_(None),
        )
        feedback_result = await db.execute(feedback_query)
        feedback_rows = feedback_result.all()

        # 按主题分组反馈
        feedbacks_by_topic: dict[str, list[tuple[str, datetime]]] = {}
        for topic_id, content, created_time in feedback_rows:
            if topic_id not in feedbacks_by_topic:
                feedbacks_by_topic[topic_id] = []
            feedbacks_by_topic[topic_id].append((content or "", created_time))

        # 4. 计算每个主题的优先级评分
        pending_decisions = []
        for topic in topics:
            topic_feedbacks = feedbacks_by_topic.get(topic.id, [])
            feedback_contents = [f[0] for f in topic_feedbacks]
            last_feedback_time = max((f[1] for f in topic_feedbacks), default=None) if topic_feedbacks else None

            # 计算优先级评分
            priority_data = priority_calculator.calculate_score(
                topic_title=topic.title,
                topic_description=topic.description,
                feedback_contents=feedback_contents,
                strategic_keywords=strategic_keywords,
                last_feedback_time=last_feedback_time,
            )

            pending_decisions.append(
                {
                    "id": topic.id,
                    "title": topic.title,
                    "category": topic.category,
                    "status": topic.status,
                    # MVP 优先级评分数据
                    "priority_score": priority_data["total_score"],
                    "feedback_count": priority_data["feedback_count"],
                    "urgent_ratio": priority_data["urgent_ratio"],
                    "strategic_keywords_matched": priority_data["strategic_keywords_matched"],
                    "last_feedback_days": priority_data["last_feedback_days"],
                    # 商业价值数据（来自 Topic 模型）
                    "total_mrr": float(topic.total_mrr) if topic.total_mrr else 0,
                    "affected_customer_count": topic.affected_customer_count,
                }
            )

        # 按优先级评分排序
        pending_decisions.sort(key=operator.itemgetter("priority_score"), reverse=True)

        return pending_decisions

    @staticmethod
    async def get_my_feedbacks(
        db: AsyncSession,
        tenant_id: str,
        user_id: int,
        limit: int = 10,
    ) -> dict:
        """
        获取当前用户录入的反馈统计

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            user_id: 当前用户ID
            limit: 最近更新列表的数量限制

        Returns:
            包含 summary 和 recent_updates 的字典
        """
        from sqlalchemy.orm import aliased

        # 1. 统计摘要
        # 我录入的反馈总数
        submitted_query = select(func.count(Feedback.id)).where(
            Feedback.tenant_id == tenant_id,
            Feedback.deleted_at.is_(None),
            Feedback.submitter_id == user_id,
        )
        submitted_count = await db.scalar(submitted_query) or 0

        # 已进入排期的数量（关联的主题状态为 planned/in_progress）
        in_progress_query = (
            select(func.count(Feedback.id))
            .join(Topic, Feedback.topic_id == Topic.id)
            .where(
                Feedback.tenant_id == tenant_id,
                Feedback.deleted_at.is_(None),
                Feedback.submitter_id == user_id,
                Topic.status.in_(["planned", "in_progress"]),
            )
        )
        in_progress_count = await db.scalar(in_progress_query) or 0

        # 已完成的数量（关联的主题状态为 completed）
        completed_query = (
            select(func.count(Feedback.id))
            .join(Topic, Feedback.topic_id == Topic.id)
            .where(
                Feedback.tenant_id == tenant_id,
                Feedback.deleted_at.is_(None),
                Feedback.submitter_id == user_id,
                Topic.status == "completed",
            )
        )
        completed_count = await db.scalar(completed_query) or 0

        # 2. 最近更新列表
        TopicAlias = aliased(Topic)
        recent_query = (
            select(
                Feedback.id.label("feedback_id"),
                Feedback.content,
                Feedback.updated_time,
                Feedback.created_time,
                TopicAlias.id.label("topic_id"),
                TopicAlias.title.label("topic_title"),
                TopicAlias.status.label("topic_status"),
            )
            .outerjoin(TopicAlias, Feedback.topic_id == TopicAlias.id)
            .where(
                Feedback.tenant_id == tenant_id,
                Feedback.deleted_at.is_(None),
                Feedback.submitter_id == user_id,
            )
            .order_by(desc(func.coalesce(Feedback.updated_time, Feedback.created_time)))
            .limit(limit)
        )

        result = await db.execute(recent_query)
        recent_rows = result.all()

        recent_updates = [
            {
                "feedback_id": row.feedback_id,
                "content_summary": (row.content[:50] + "..." if row.content and len(row.content) > 50 else row.content),
                "topic_id": row.topic_id,
                "topic_title": row.topic_title,
                "topic_status": row.topic_status,
                "updated_at": str(row.updated_time or row.created_time),
            }
            for row in recent_rows
        ]

        return {
            "summary": {
                "submitted_count": submitted_count,
                "in_progress_count": in_progress_count,
                "completed_count": completed_count,
            },
            "recent_updates": recent_updates,
        }

    @staticmethod
    async def _get_conversion_funnel(
        db: AsyncSession,
        tenant_id: str,
    ) -> dict:
        """
        获取需求转化漏斗数据

        流程：总反馈 → 已聚类 → 待审 → 已排期 → 进行中 → 已完成
        """
        # 1. 总反馈数
        total_feedbacks_query = select(func.count(Feedback.id)).where(
            Feedback.tenant_id == tenant_id,
            Feedback.deleted_at.is_(None),
        )
        total_feedbacks = await db.scalar(total_feedbacks_query) or 0

        # 2. 已聚类反馈数（有 topic_id）
        clustered_query = select(func.count(Feedback.id)).where(
            Feedback.tenant_id == tenant_id,
            Feedback.deleted_at.is_(None),
            Feedback.topic_id.isnot(None),
        )
        clustered = await db.scalar(clustered_query) or 0

        # 3. 按议题状态统计
        status_query = (
            select(
                Topic.status,
                func.count(Topic.id).label("count"),
            )
            .where(
                Topic.tenant_id == tenant_id,
                Topic.deleted_at.is_(None),
            )
            .group_by(Topic.status)
        )
        status_result = await db.execute(status_query)
        status_counts = {row.status: row.count for row in status_result.all()}

        pending_review = status_counts.get("pending", 0)
        planned = status_counts.get("planned", 0)
        in_progress = status_counts.get("in_progress", 0)
        completed = status_counts.get("completed", 0)

        # 4. 计算转化率
        def safe_rate(numerator: int, denominator: int) -> float:
            return round((numerator / denominator * 100), 1) if denominator > 0 else 0.0

        clustering_rate = safe_rate(clustered, total_feedbacks)
        review_rate = safe_rate(pending_review + planned + in_progress + completed, clustered)
        planning_rate = safe_rate(planned + in_progress + completed, pending_review + planned + in_progress + completed)
        completion_rate = safe_rate(completed, planned + in_progress + completed)

        return {
            "total_feedbacks": total_feedbacks,
            "clustered": clustered,
            "pending_review": pending_review,
            "planned": planned,
            "in_progress": in_progress,
            "completed": completed,
            "conversion_rates": {
                "clustering_rate": clustering_rate,
                "review_rate": review_rate,
                "planning_rate": planning_rate,
                "completion_rate": completion_rate,
            },
        }


dashboard_service = DashboardService()
