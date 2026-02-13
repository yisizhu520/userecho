"""租户配置服务（通用）"""

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.userecho.crud.crud_tenant_config import tenant_config_dao
from backend.common.log import log


class TenantConfigService:
    """租户配置服务（通用）
    
    提供租户级别的配置管理功能
    支持按功能模块分组存储配置
    """
    
    def __init__(self):
        """初始化配置服务"""
        # 简单的内存缓存字典
        # key: f"{tenant_id}:{config_group}"
        # value: config_data (dict)
        self._cache: dict[str, dict] = {}
    
    def _cache_key(self, tenant_id: str, config_group: str) -> str:
        """生成缓存 key"""
        return f"{tenant_id}:{config_group}"
    
    async def get_config(
        self,
        db: AsyncSession,
        tenant_id: str,
        config_group: str,
        default: dict | None = None,
    ) -> dict:
        """
        获取租户配置（带缓存）
        
        Args:
            db: 数据库会话
            tenant_id: 租户 ID
            config_group: 配置分组名称
            default: 默认配置（如果不存在）
            
        Returns:
            配置数据（dict）
        """
        # 检查缓存
        cache_key = self._cache_key(tenant_id, config_group)
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # 从数据库读取
        config = await tenant_config_dao.get_by_group(db, tenant_id, config_group)
        
        if config and config.is_active:
            # 缓存配置
            self._cache[cache_key] = config.config_data
            return config.config_data
        
        # 使用默认配置
        result = default or {}
        
        # 如果有默认值，也缓存起来（避免频繁查数据库）
        if default:
            self._cache[cache_key] = result
        
        return result
    
    async def set_config(
        self,
        db: AsyncSession,
        tenant_id: str,
        config_group: str,
        config_data: dict,
    ) -> None:
        """
        设置租户配置（自动清除缓存）
        
        Args:
            db: 数据库会话
            tenant_id: 租户 ID
            config_group: 配置分组名称
            config_data: 配置数据
        """
        await tenant_config_dao.upsert(
            db=db,
            tenant_id=tenant_id,
            config_group=config_group,
            config_data=config_data
        )
        
        # 清除缓存
        self._clear_cache(tenant_id, config_group)
        
        log.info(f'Updated config for tenant {tenant_id}, group: {config_group}')
    
    def _clear_cache(self, tenant_id: str, config_group: str):
        """清除指定租户和配置组的缓存"""
        cache_key = self._cache_key(tenant_id, config_group)
        if cache_key in self._cache:
            del self._cache[cache_key]
            log.debug(f'Cleared cache for {cache_key}')
    
    def clear_all_cache(self):
        """清除所有缓存（用于测试或维护）"""
        self._cache.clear()
        log.info('Cleared all tenant config cache')


# 全局单例
tenant_config_service = TenantConfigService()

