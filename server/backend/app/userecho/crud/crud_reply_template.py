"""回复模板 CRUD"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.userecho.crud.base import TenantAwareCRUD
from backend.app.userecho.model.reply_template import ReplyTemplate


class CRUDReplyTemplate(TenantAwareCRUD[ReplyTemplate]):
    """回复模板 CRUD"""

    async def get_active_templates(
        self,
        db: AsyncSession,
        tenant_id: str,
        category: str | None = None,
        tone: str | None = None,
    ) -> list[ReplyTemplate]:
        """获取活跃的模板列表"""
        query = select(self.model).where(
            self.model.tenant_id == tenant_id,
            self.model.is_active == True,  # noqa: E712
        )

        if category:
            query = query.where(self.model.category == category)
        if tone:
            query = query.where(self.model.tone == tone)

        query = query.order_by(self.model.usage_count.desc(), self.model.created_time.desc())

        result = await db.execute(query)
        return list(result.scalars().all())

    async def increment_usage(
        self,
        db: AsyncSession,
        tenant_id: str,
        template_id: str,
    ) -> ReplyTemplate | None:
        """增加使用次数"""
        template = await self.get_by_id(db, tenant_id, template_id)
        if not template:
            return None

        template.usage_count += 1
        await db.commit()
        await db.refresh(template)
        return template

    async def get_system_templates(
        self,
        db: AsyncSession,
    ) -> list[ReplyTemplate]:
        """获取系统预置模板"""
        query = (
            select(self.model)
            .where(
                self.model.is_system == True,  # noqa: E712
                self.model.is_active == True,  # noqa: E712
            )
            .order_by(self.model.category, self.model.name)
        )

        result = await db.execute(query)
        return list(result.scalars().all())


crud_reply_template = CRUDReplyTemplate(ReplyTemplate)
