from datetime import datetime

from pydantic import Field

from backend.common.schema import SchemaBase


class CustomerBase(SchemaBase):
    """客户基础模型"""

    name: str = Field(description="客户名称")
    customer_type: str = Field(
        default="normal", description="客户类型: normal=普通, paid=付费, major=大客户, strategic=战略客户"
    )
    business_value: int = Field(default=1, ge=1, le=10, description="商业价值权重 (1-10)")


class CustomerCreate(CustomerBase):
    """创建客户参数"""


class CustomerUpdate(SchemaBase):
    """更新客户参数"""

    name: str | None = Field(None, description="客户名称")
    customer_type: str | None = Field(None, description="客户类型")
    business_value: int | None = Field(None, ge=1, le=10, description="商业价值权重")


class CustomerOut(CustomerBase):
    """客户输出模型"""

    model_config = {"from_attributes": True}

    id: str = Field(description="客户ID")
    tenant_id: str = Field(description="租户ID")
    created_time: datetime = Field(description="创建时间")
    updated_time: datetime | None = Field(None, description="更新时间")
    deleted_at: datetime | None = Field(None, description="删除时间")
