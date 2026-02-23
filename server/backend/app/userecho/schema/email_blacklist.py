"""邮箱黑名单 Schemas"""

from pydantic import BaseModel, ConfigDict, Field

from backend.common.schema import SchemaBase


class EmailBlacklistCreateReq(BaseModel):
    """添加邮箱黑名单请求"""

    domain: str = Field(..., description="邮箱域名", max_length=256)
    type: str = Field("disposable", description="类型: disposable/spam/banned")
    reason: str | None = Field(None, description="加入黑名单的原因")


class EmailBlacklistUpdateReq(BaseModel):
    """更新邮箱黑名单请求"""

    is_active: bool = Field(..., description="是否启用")
    reason: str | None = Field(None, description="原因")


class EmailBlacklistSchema(SchemaBase):
    """邮箱黑名单响应模型"""

    domain: str = Field(..., description="邮箱域名")
    type: str = Field(..., description="类型")
    reason: str | None = Field(None, description="原因")
    added_by: int | None = Field(None, description="添加人ID")
    is_active: bool = Field(..., description="是否启用")

    model_config = ConfigDict(from_attributes=True)
