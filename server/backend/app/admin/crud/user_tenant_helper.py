from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def get_user_primary_tenant_id(db: AsyncSession, user_id: int) -> str | None:
    from backend.app.userecho.model.tenant_user import TenantUser

    stmt = select(TenantUser.tenant_id).where(TenantUser.user_id == user_id).limit(1)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
