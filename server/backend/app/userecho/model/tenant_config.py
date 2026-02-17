"""租户配置模型"""

from sqlalchemy import JSON, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import MappedBase
from backend.database.db import uuid4_str


class TenantConfig(MappedBase):
    """租户配置表（通用）

    支持多种功能模块的配置，每个功能模块一条记录
    """

    __tablename__ = 'userecho_tenant_config'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str, comment='配置ID')
    tenant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey('tenants.id', ondelete='CASCADE'), index=True, nullable=False, comment='租户ID'
    )
    config_group: Mapped[str] = mapped_column(
        String(32), nullable=False, comment='配置分组（clustering/notification/display...）'
    )
    config_data: Mapped[dict] = mapped_column(JSON, nullable=False, comment='配置数据（JSON 格式）')
    is_active: Mapped[bool] = mapped_column(default=True, comment='是否启用')

    __table_args__ = (
        # 唯一约束：每个租户的每个配置组只能有一条记录
        UniqueConstraint('tenant_id', 'config_group', name='uq_tenant_config'),
    )
