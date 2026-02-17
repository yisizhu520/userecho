"""Priority Score CRUD"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.userecho.crud.base import TenantAwareCRUD
from backend.app.userecho.model.priority_score import PriorityScore


class CRUDPriorityScore(TenantAwareCRUD[PriorityScore]):
    """优先级评分 CRUD"""

    async def get_by_topic(
        self,
        db: AsyncSession,
        tenant_id: str,
        topic_id: str,
    ) -> PriorityScore | None:
        """
        根据主题ID获取优先级评分

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            topic_id: 主题ID

        Returns:
            优先级评分 或 None
        """
        query = select(self.model).where(self.model.tenant_id == tenant_id, self.model.topic_id == topic_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def upsert(
        self,
        db: AsyncSession,
        tenant_id: str,
        topic_id: str,
        impact_scope: int,
        business_value: int,
        dev_cost: int,
        urgency_factor: float = 1.0,
    ) -> PriorityScore:
        """
        创建或更新优先级评分

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            topic_id: 主题ID
            impact_scope: 影响范围
            business_value: 商业价值
            dev_cost: 开发成本
            urgency_factor: 紧急系数

        Returns:
            优先级评分实例
        """
        # 计算总分: (影响 × 价值) / 成本 × 紧急系数
        total_score = (impact_scope * business_value) / dev_cost * urgency_factor

        # 检查是否已存在
        existing = await self.get_by_topic(db, tenant_id, topic_id)

        if existing:
            # 更新
            existing.impact_scope = impact_scope
            existing.business_value = business_value
            existing.dev_cost = dev_cost
            existing.urgency_factor = urgency_factor
            existing.total_score = total_score
            await db.commit()
            await db.refresh(existing)
            return existing
        # 创建
        return await self.create(
            db=db,
            tenant_id=tenant_id,
            topic_id=topic_id,
            impact_scope=impact_scope,
            business_value=business_value,
            dev_cost=dev_cost,
            urgency_factor=urgency_factor,
            total_score=total_score,
        )


crud_priority_score = CRUDPriorityScore(PriorityScore)
