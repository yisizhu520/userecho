"""演示模式相关 Schema"""

from pydantic import Field

from backend.common.schema import SchemaBase


class SwitchRoleParam(SchemaBase):
    """切换角色参数"""

    role_key: str = Field(..., description="角色 key，可选值：product_owner, user_ops, admin")
