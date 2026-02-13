"""租户配置 Schema"""

from datetime import datetime

from pydantic import ConfigDict, Field

from backend.common.schema import SchemaBase


class TenantConfigBase(SchemaBase):
    """租户配置基础模型"""

    config_group: str = Field(description='配置分组（clustering/notification/display）')
    config_data: dict = Field(description='配置数据（JSON格式）')
    is_active: bool = Field(default=True, description='是否启用')


class TenantConfigCreate(TenantConfigBase):
    """创建租户配置参数"""

    pass


class TenantConfigUpdate(SchemaBase):
    """更新租户配置参数"""

    config_data: dict | None = Field(None, description='配置数据（JSON格式）')
    is_active: bool | None = Field(None, description='是否启用')


class TenantConfigOut(TenantConfigBase):
    """租户配置输出模型"""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description='配置ID')
    tenant_id: str = Field(description='租户ID')
    created_time: datetime = Field(description='创建时间')
    updated_time: datetime | None = Field(None, description='更新时间')

