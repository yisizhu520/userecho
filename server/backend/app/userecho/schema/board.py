"""Board Schema 定义"""

from datetime import datetime

from pydantic import BaseModel, Field


class BoardBase(BaseModel):
    """Board 基础信息"""

    name: str = Field(..., description="看板名称")
    url_name: str = Field(..., description="URL slug")
    description: str | None = Field(None, description="看板描述")
    category: str | None = Field(None, description="看板分类")


class BoardCreate(BaseModel):
    """创建看板"""

    name: str = Field(..., min_length=1, max_length=100, description="看板名称")
    url_name: str = Field(..., min_length=1, max_length=100, description="URL slug")
    description: str | None = Field(None, description="看板描述")
    category: str | None = Field(None, max_length=50, description="看板分类")
    sort_order: int = Field(0, description="排序顺序")


class BoardUpdate(BaseModel):
    """更新看板"""

    name: str | None = Field(None, min_length=1, max_length=100, description="看板名称")
    description: str | None = Field(None, description="看板描述")
    category: str | None = Field(None, max_length=50, description="看板分类")
    sort_order: int | None = Field(None, description="排序顺序")
    is_archived: bool | None = Field(None, description="是否归档")


class BoardOut(BoardBase):
    """Board 输出模型"""

    id: str = Field(..., description="看板ID")
    tenant_id: str = Field(..., description="租户ID")
    feedback_count: int = Field(0, description="反馈数量")
    topic_count: int = Field(0, description="主题数量")
    is_archived: bool = Field(False, description="是否归档")
    created_time: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True


class BoardListOut(BaseModel):
    """Board 列表输出"""

    boards: list[BoardOut] = Field(default_factory=list, description="看板列表")
    total: int = Field(0, description="总数")
