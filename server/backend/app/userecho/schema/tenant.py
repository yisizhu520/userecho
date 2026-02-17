from datetime import datetime

from pydantic import Field

from backend.common.schema import SchemaBase


class TenantBase(SchemaBase):
    """租户基础模型"""

    name: str = Field(description='租户名称')
    status: str = Field(default='active', description='状态: active, suspended, deleted')


class TenantCreate(TenantBase):
    """创建租户参数"""


class TenantUpdate(SchemaBase):
    """更新租户参数"""

    name: str | None = Field(None, description='租户名称')
    status: str | None = Field(None, description='状态')


class TenantOut(TenantBase):
    """租户输出模型"""

    id: str = Field(description='租户ID')
    created_time: datetime = Field(description='创建时间')
    updated_time: datetime | None = Field(None, description='更新时间')
    deleted_at: datetime | None = Field(None, description='删除时间')
