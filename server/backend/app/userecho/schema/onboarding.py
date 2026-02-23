"""引导流程 Schema 定义

用于新用户创建租户和看板的引导流程
"""

from datetime import datetime

from pydantic import ConfigDict, Field, field_validator

from backend.common.schema import SchemaBase


class OnboardingStatusOut(SchemaBase):
    """引导状态输出模型"""

    model_config = ConfigDict(from_attributes=True)

    needs_onboarding: bool = Field(description="是否需要引导")
    current_step: str | None = Field(None, description="当前步骤")
    tenant_id: str | None = Field(None, description="租户ID（如果已创建）")
    board_id: str | None = Field(None, description="看板ID（如果已创建）")
    completed_steps: list[str] = Field(default_factory=list, description="已完成的步骤列表")


class CreateTenantParam(SchemaBase):
    """创建租户参数"""

    name: str = Field(..., min_length=2, max_length=100, description="公司/团队名称")
    slug: str = Field(..., min_length=2, max_length=100, description="URL标识，如 acme-corp")

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """验证 slug 格式：只允许小写字母、数字和连字符"""
        import re

        if not re.match(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$|^[a-z0-9]$", v):
            raise ValueError("URL标识只能包含小写字母、数字和连字符，且不能以连字符开头或结尾")
        if "--" in v:
            raise ValueError("URL标识不能包含连续的连字符")
        return v


class CreateTenantOut(SchemaBase):
    """创建租户返回模型"""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="租户ID")
    name: str = Field(description="租户名称")
    slug: str = Field(description="URL标识")
    created_time: datetime = Field(description="创建时间")


class CreateBoardParam(SchemaBase):
    """创建看板参数"""

    name: str = Field(..., min_length=2, max_length=100, description="看板名称")
    description: str | None = Field(None, max_length=500, description="看板描述")
    access_mode: str = Field(default="private", description="访问模式: private, public, restricted")

    @field_validator("access_mode")
    @classmethod
    def validate_access_mode(cls, v: str) -> str:
        """验证访问模式"""
        allowed = ["private", "public", "restricted"]
        if v not in allowed:
            raise ValueError(f"访问模式必须是 {allowed} 之一")
        return v


class CreateBoardOut(SchemaBase):
    """创建看板返回模型"""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="看板ID")
    tenant_id: str = Field(description="租户ID")
    name: str = Field(description="看板名称")
    url_name: str = Field(description="URL名称")
    description: str | None = Field(None, description="看板描述")
    access_mode: str = Field(description="访问模式")
    created_time: datetime = Field(description="创建时间")


class SlugCheckParam(SchemaBase):
    """Slug 可用性检查参数"""

    slug: str = Field(..., min_length=2, max_length=100, description="要检查的 slug")


class SlugCheckOut(SchemaBase):
    """Slug 可用性检查返回"""

    slug: str = Field(description="检查的 slug")
    available: bool = Field(description="是否可用")
    suggestion: str | None = Field(None, description="如果不可用，推荐的替代 slug")


class OnboardingCompleteOut(SchemaBase):
    """引导完成返回模型"""

    success: bool = Field(description="是否成功")
    tenant_id: str = Field(description="租户ID")
    board_id: str = Field(description="看板ID")
    redirect_path: str = Field(description="重定向路径")
