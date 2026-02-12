"""优先级评分服务

负责主题优先级评分的计算和管理
"""

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.feedalyze.crud import crud_priority_score
from backend.app.feedalyze.schema.priority import PriorityScoreCreate
from backend.common.log import log


class PriorityService:
    """优先级评分服务"""

    async def calculate_and_save(
        self,
        db: AsyncSession,
        tenant_id: str,
        data: PriorityScoreCreate,
    ):
        """
        计算并保存优先级评分

        公式: (影响范围 × 商业价值) / 开发成本 × 紧急系数

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            data: 评分数据

        Returns:
            优先级评分实例
        """
        try:
            return await crud_priority_score.upsert(
                db=db,
                tenant_id=tenant_id,
                topic_id=data.topic_id,
                impact_scope=data.impact_scope,
                business_value=data.business_value,
                dev_cost=data.dev_cost,
                urgency_factor=data.urgency_factor
            )

        except Exception as e:
            log.error(f'Failed to calculate priority score for topic {data.topic_id}, tenant {tenant_id}: {e}')
            raise

    async def get_ranking(
        self,
        db: AsyncSession,
        tenant_id: str,
        limit: int = 50,
    ) -> list[dict]:
        """
        获取优先级排行榜（按总分降序）

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            limit: 返回数量

        Returns:
            排行榜列表
        """
        try:
            from sqlalchemy import select
            from backend.app.feedalyze.model.priority_score import PriorityScore
            from backend.app.feedalyze.model.topic import Topic

            # 关联查询主题和评分
            query = (
                select(PriorityScore, Topic)
                .join(Topic, PriorityScore.topic_id == Topic.id)
                .where(
                    PriorityScore.tenant_id == tenant_id,
                    Topic.deleted_at.is_(None)
                )
                .order_by(PriorityScore.total_score.desc())
                .limit(limit)
            )

            result = await db.execute(query)
            rows = result.all()

            ranking = []
            for idx, (score, topic) in enumerate(rows, 1):
                ranking.append({
                    'rank': idx,
                    'topic_id': topic.id,
                    'topic_title': topic.title,
                    'topic_status': topic.status,
                    'category': topic.category,
                    'feedback_count': topic.feedback_count,
                    'total_score': score.total_score,
                    'impact_scope': score.impact_scope,
                    'business_value': score.business_value,
                    'dev_cost': score.dev_cost,
                    'urgency_factor': score.urgency_factor,
                })

            return ranking

        except Exception as e:
            log.error(f'Failed to get priority ranking for tenant {tenant_id}: {e}')
            return []


priority_service = PriorityService()
