"""租户配置 CRUD 操作"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.userecho.crud.base import TenantAwareCRUD
from backend.app.userecho.model.tenant_config import TenantConfig
from backend.database.db import uuid4_str


class CRUDTenantConfig(TenantAwareCRUD[TenantConfig]):
    """租户配置 CRUD"""

    async def get_by_group(
        self,
        db: AsyncSession,
        tenant_id: str,
        config_group: str,
    ) -> TenantConfig | None:
        """
        根据配置组获取配置
        
        Args:
            db: 数据库会话
            tenant_id: 租户ID
            config_group: 配置分组名称
            
        Returns:
            配置记录或 None
        """
        query = select(TenantConfig).where(
            TenantConfig.tenant_id == tenant_id,
            TenantConfig.config_group == config_group,
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def upsert(
        self,
        db: AsyncSession,
        tenant_id: str,
        config_group: str,
        config_data: dict,
    ) -> TenantConfig:
        """
        创建或更新配置（Upsert）
        
        如果配置已存在，则更新 config_data
        如果不存在，则创建新记录
        
        Args:
            db: 数据库会话
            tenant_id: 租户ID
            config_group: 配置分组名称
            config_data: 配置数据
            
        Returns:
            配置记录
        """
        # 查找现有配置
        existing = await self.get_by_group(db, tenant_id, config_group)
        
        if existing:
            # 更新现有配置
            existing.config_data = config_data
            existing.is_active = True
            await db.commit()
            await db.refresh(existing)
            return existing
        else:
            # 创建新配置
            new_config = TenantConfig(
                id=uuid4_str(),
                tenant_id=tenant_id,
                config_group=config_group,
                config_data=config_data,
                is_active=True,
            )
            db.add(new_config)
            await db.commit()
            await db.refresh(new_config)
            return new_config


# 全局实例
tenant_config_dao = CRUDTenantConfig(TenantConfig)

