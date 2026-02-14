from datetime import date

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.userecho.crud.base import TenantAwareCRUD
from backend.app.userecho.model.insight import Insight


class CRUDInsight(TenantAwareCRUD[Insight]):
    """洞察 CRUD"""

    async def get_cached_insight(
        self,
        db: AsyncSession,
        tenant_id: str,
        insight_type: str,
        time_range: str,
        start_date: date,
        end_date: date,
    ) -> Insight | None:
        """
        获取缓存的洞察（避免重复生成）
        
        Args:
            db: 数据库会话
            tenant_id: 租户ID
            insight_type: 洞察类型
            time_range: 时间范围
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            洞察实例或 None
        """
        query = select(Insight).where(
            and_(
                Insight.tenant_id == tenant_id,
                Insight.insight_type == insight_type,
                Insight.time_range == time_range,
                Insight.start_date == start_date,
                Insight.end_date == end_date,
                Insight.status == 'active'
            )
        ).order_by(Insight.created_time.desc())
        
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def create_insight(
        self,
        db: AsyncSession,
        tenant_id: str,
        insight_type: str,
        time_range: str,
        start_date: date,
        end_date: date,
        content: dict,
        generated_by: str = 'hybrid',
        confidence: float | None = None,
        execution_time_ms: int | None = None,
    ) -> Insight:
        """
        创建新的洞察实例
        
        Args:
            db: 数据库会话
            tenant_id: 租户ID
            insight_type: 洞察类型
            time_range: 时间范围
            start_date: 开始日期
            end_date: 结束日期
            content: 洞察内容
            generated_by: 生成方式
            confidence: AI 置信度
            execution_time_ms: 生成耗时
        
        Returns:
            洞察实例
        """
        return await self.create(
            db=db,
            tenant_id=tenant_id,
            insight_type=insight_type,
            time_range=time_range,
            start_date=start_date,
            end_date=end_date,
            content=content,
            generated_by=generated_by,
            confidence=confidence,
            execution_time_ms=execution_time_ms,
        )

    async def dismiss_insight(
        self,
        db: AsyncSession,
        insight_id: str,
        tenant_id: str,
        reason: str,
    ) -> Insight:
        """
        忽略洞察
        
        Args:
            db: 数据库会话
            insight_id: 洞察ID
            tenant_id: 租户ID
            reason: 忽略原因
        
        Returns:
            更新后的洞察实例
        """
        insight = await self.get_by_id(db, tenant_id, insight_id)
        
        if not insight:
            raise ValueError(f'Insight {insight_id} not found')
        
        insight.status = 'dismissed'
        insight.dismissed_reason = reason
        
        await db.commit()
        await db.refresh(insight)
        
        return insight


crud_insight = CRUDInsight(Insight)
