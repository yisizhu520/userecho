from pydantic import BaseModel, Field


class TenantRoleCreate(BaseModel):
    """创建租户角色"""

    name: str = Field(..., max_length=64, description="角色名称")
    code: str = Field(..., max_length=64, description="角色代码")
    description: str | None = Field(None, max_length=500, description="角色描述")
    permission_ids: list[str] | None = Field(None, description="权限 ID 列表")


class TenantRoleUpdate(BaseModel):
    """更新租户角色"""

    name: str | None = Field(None, max_length=64, description="角色名称")
    description: str | None = Field(None, max_length=500, description="角色描述")
    status: str | None = Field(None, description="状态")


class TenantRolePermissionUpdate(BaseModel):
    """更新角色权限"""

    permission_ids: list[str] = Field(..., description="权限 ID 列表")


class TenantRoleOut(BaseModel):
    """租户角色输出"""

    id: str
    tenant_id: str
    name: str
    code: str
    description: str | None
    is_builtin: bool
    sort: int
    status: str

    class Config:
        from_attributes = True


class TenantPermissionOut(BaseModel):
    """租户权限输出"""

    id: str
    parent_id: str | None
    name: str
    code: str
    type: str
    sort: int

    class Config:
        from_attributes = True


class TenantMemberCreate(BaseModel):
    """创建租户成员"""

    email: str = Field(..., max_length=256, description="邮箱")
    nickname: str = Field(..., max_length=64, description="昵称")
    password: str = Field(..., min_length=6, max_length=32, description="密码")
    username: str | None = Field(None, max_length=64, description="用户名(可选，用于显示)")
    role_ids: list[str] | None = Field(None, description="角色 ID 列表")


class TenantMemberUpdate(BaseModel):
    """更新租户成员"""

    username: str | None = Field(None, max_length=64, description="用户名")
    nickname: str | None = Field(None, max_length=64, description="昵称")
    role_ids: list[str] | None = Field(None, description="角色 ID 列表")
    user_type: str | None = Field(None, description="用户类型")
    status: str | None = Field(None, description="状态")


class TenantMemberRoleUpdate(BaseModel):
    """更新成员角色"""

    role_ids: list[str] = Field(..., description="角色 ID 列表")


class TenantMemberOut(BaseModel):
    """租户成员输出"""

    id: str
    tenant_id: str
    user_id: int
    user_type: str
    status: str
    feedback_count: int
    username: str | None = None
    nickname: str | None = None
    email: str | None = None
    roles: list[TenantRoleOut] = []

    class Config:
        from_attributes = True
