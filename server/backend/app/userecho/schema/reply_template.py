"""回复模板 Schema"""

from datetime import datetime

from pydantic import BaseModel, Field


class ReplyTemplateBase(BaseModel):
    """回复模板基础 Schema"""

    name: str = Field(..., max_length=100, description='模板名称')
    description: str | None = Field(None, max_length=255, description='模板描述')
    content: str = Field(..., description='模板内容')
    category: str = Field('general', description='分类: general/bug_fix/feature/improvement')
    tone: str = Field('friendly', description='语气: formal/friendly/concise')
    language: str = Field('zh-CN', description='语言')
    is_active: bool = Field(True, description='是否启用')


class ReplyTemplateCreate(ReplyTemplateBase):
    """创建回复模板请求"""


class ReplyTemplateUpdate(BaseModel):
    """更新回复模板请求"""

    name: str | None = Field(None, max_length=100)
    description: str | None = Field(None, max_length=255)
    content: str | None = None
    category: str | None = None
    tone: str | None = None
    language: str | None = None
    is_active: bool | None = None


class ReplyTemplateOut(ReplyTemplateBase):
    """回复模板输出"""

    id: str
    tenant_id: str
    is_system: bool
    usage_count: int
    created_by: int | None = None
    created_time: datetime
    updated_time: datetime | None = None

    model_config = {'from_attributes': True}


class ReplyTemplateListResponse(BaseModel):
    """回复模板列表响应"""

    items: list[ReplyTemplateOut]
    total: int
