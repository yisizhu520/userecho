"""合并建议 Schema"""

from pydantic import BaseModel, Field


class MergeSuggestionOut(BaseModel):
    """合并建议输出"""

    suggestion_id: str
    cluster_label: int
    suggested_topic_id: str
    suggested_topic_title: str
    suggested_topic_status: str
    similarity: float
    feedback_count: int
    ai_generated_title: str | None = None
    status: str
    created_time: str


class ProcessSuggestionRequest(BaseModel):
    """处理建议请求"""

    action: str = Field(..., description="操作类型: accept(关联), reject(拒绝), create_new(创建新需求)")
    suggestion_ids: list[str] = Field(..., description="建议ID列表（批量处理）")


class BatchProcessResult(BaseModel):
    """批量处理结果"""

    success_count: int
    failed_count: int
    errors: list[dict] | None = None
