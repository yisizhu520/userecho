from datetime import datetime

from pydantic import Field

from backend.common.schema import SchemaBase


class StatusHistoryOut(SchemaBase):
    """状态历史输出模型"""

    id: str = Field(description='历史ID')
    tenant_id: str = Field(description='租户ID')
    topic_id: str = Field(description='主题ID')
    from_status: str = Field(description='原状态')
    to_status: str = Field(description='新状态')
    reason: str | None = Field(None, description='变更原因')
    changed_by: int = Field(description='操作人用户ID')
    changed_by_name: str | None = Field(None, description='操作人姓名 (关联查询)')
    changed_at: datetime = Field(description='变更时间')
    created_time: datetime = Field(description='创建时间')
