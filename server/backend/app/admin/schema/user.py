from datetime import datetime
from typing import Annotated, Any

from pydantic import ConfigDict, Field, HttpUrl, PlainSerializer, model_validator
from typing_extensions import Self

from backend.app.admin.schema.dept import GetDeptDetail
from backend.app.admin.schema.role import GetRoleWithRelationDetail
from backend.common.enums import StatusType
from backend.common.schema import CustomEmailStr, CustomPhoneNumber, SchemaBase, ser_string


class AuthSchemaBase(SchemaBase):
    """用户认证基础模型"""

    username: str = Field(description='用户名')
    password: str = Field(description='密码')


class AuthLoginParam(SchemaBase):
    """用户登录参数"""

    email: str = Field(..., max_length=256, description='邮箱')
    password: str = Field(..., description='密码')
    uuid: str | None = Field(None, description='验证码 UUID')
    captcha: str | None = Field(None, description='验证码')


class AddUserParam(AuthSchemaBase):
    """添加用户参数"""

    nickname: str | None = Field(None, description='昵称')
    email: CustomEmailStr | None = Field(None, description='邮箱')
    phone: CustomPhoneNumber | None = Field(None, description='手机号码')
    dept_id: int = Field(description='部门 ID')
    roles: list[int] = Field(description='角色 ID 列表')


class AddUserRoleParam(SchemaBase):
    """添加用户角色"""

    user_id: int = Field(description='用户 ID')
    role_id: int = Field(description='角色 ID')


class AddOAuth2UserParam(AuthSchemaBase):
    """添加 OAuth2 用户参数"""

    password: str | None = Field(None, description='密码')
    nickname: str | None = Field(None, description='昵称')
    email: CustomEmailStr | None = Field(None, description='邮箱')
    avatar: Annotated[HttpUrl, PlainSerializer(ser_string)] | None = Field(None, description='头像地址')


class ResetPasswordParam(SchemaBase):
    """重置密码参数"""

    old_password: str = Field(description='旧密码')
    new_password: str = Field(description='新密码')
    confirm_password: str = Field(description='确认密码')


class UserInfoSchemaBase(SchemaBase):
    """用户信息基础模型"""

    dept_id: int | None = Field(None, description='部门 ID')
    username: str = Field(description='用户名')
    nickname: str = Field(description='昵称')
    avatar: Annotated[HttpUrl, PlainSerializer(ser_string)] | None = Field(None, description='头像地址')
    email: CustomEmailStr | None = Field(None, description='邮箱')
    phone: CustomPhoneNumber | None = Field(None, description='手机号')


class UpdateUserParam(UserInfoSchemaBase):
    """更新用户参数"""

    roles: list[int] = Field(description='角色 ID 列表')


class GetUserInfoDetail(UserInfoSchemaBase):
    """用户信息详情"""

    model_config = ConfigDict(from_attributes=True)

    dept_id: int | None = Field(None, description='部门 ID')
    id: int = Field(description='用户 ID')
    uuid: str = Field(description='用户 UUID')
    tenant_id: str | None = Field(default='default-tenant', description='租户 ID')
    status: StatusType = Field(description='状态')
    is_superuser: bool = Field(description='是否超级管理员')
    is_staff: bool = Field(description='是否管理员')
    is_multi_login: bool = Field(description='是否允许多端登录')
    join_time: datetime = Field(description='加入时间')
    last_login_time: datetime | None = Field(None, description='最后登录时间')


class GetUserInfoWithRelationDetail(GetUserInfoDetail):
    """用户信息关联详情"""

    model_config = ConfigDict(from_attributes=True)

    dept: GetDeptDetail | None = Field(None, description='部门信息')
    roles: list[GetRoleWithRelationDetail] = Field(description='角色列表')


class GetCurrentUserInfoWithRelationDetail(GetUserInfoWithRelationDetail):
    """当前用户信息关联详情"""

    model_config = ConfigDict(from_attributes=True)

    dept: str | None = Field(None, description='部门名称')
    roles: list[str] = Field(description='角色名称列表')
    homePath: str = Field(description='用户首页路径')
    tenantPermissions: list[str] = Field(default_factory=list, description='租户权限码列表')
    userType: str | None = Field(None, description='用户类型: admin, staff, business, hybrid')
    hasSystemRole: bool | None = Field(None, description='是否有系统角色')
    hasBusinessRole: bool | None = Field(None, description='是否有业务角色')

    @model_validator(mode='before')
    @classmethod
    def handel(cls, data: Any) -> Self:
        """处理部门、角色数据和计算首页路径"""
        # 处理部门
        dept = data['dept']
        if dept:
            data['dept'] = dept['name']

        # 处理角色
        raw_roles = data['roles']
        role_names = []
        if raw_roles:
            role_names = [role['name'] for role in raw_roles]
            data['roles'] = role_names

        # 计算 homePath - 根据角色类型
        data.get('is_superuser', False)

        if raw_roles:
            for role in raw_roles:
                role_type = role.get('role_type', 'business')
                if role_type == 'system' or role_type == 'business':
                    pass

        # 首页路径 - 统一跳转到工作台
        data['homePath'] = '/app/dashboard/workspace'

        return data
