"""需求主题 API 端点"""

from fastapi import APIRouter, Depends

from backend.app.userecho.schema.topic import (
    TopicCreate,
    TopicListParams,
    TopicOut,
    TopicStatusUpdateParam,
    TopicUpdate,
)
from backend.app.userecho.service import topic_service
from backend.common.response.response_code import CustomResponse
from backend.common.response.response_schema import response_base
from backend.common.security.jwt import CurrentTenantId
from backend.database.db import CurrentSession

router = APIRouter(prefix='/topics', tags=['UserEcho - 需求主题'])


def get_current_user_id() -> int:
    """获取当前用户ID"""
    # TODO: 从 JWT token 中提取
    return 1


@router.get('', summary='获取主题列表')
async def get_topics(
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
    skip: int = 0,
    limit: int = 100,
    status: str | None = None,
    category: str | None = None,
    sort_by: str = 'created_time',
    sort_order: str = 'desc',
):
    """
    获取主题列表（支持排序和过滤）

    - **status**: 过滤状态 (pending/planned/in_progress/completed/ignored)
    - **category**: 过滤分类 (bug/improvement/feature/performance/other)
    - **sort_by**: 排序字段 (created_time/feedback_count/total_score)
    - **sort_order**: 排序方向 (asc/desc)
    """
    topics = await topic_service.get_list_sorted(
        db=db,
        tenant_id=tenant_id,
        skip=skip,
        limit=limit,
        status=status,
        category=category,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    # ✅ Pydantic 自动将 ORM 对象列表转换为 TopicOut 列表（排除 centroid）
    topics_out = [TopicOut.model_validate(topic) for topic in topics]
    return response_base.success(data=topics_out)


@router.get('/{topic_id}', summary='获取主题详情')
async def get_topic_detail(
    topic_id: str,
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
    current_user_id: int = Depends(get_current_user_id),
):
    """
    获取主题详情（包含关联反馈、优先级评分、状态历史）
    """
    detail = await topic_service.get_detail_with_relations(
        db=db,
        tenant_id=tenant_id,
        topic_id=topic_id,
        current_user_id=current_user_id
    )

    if not detail:
        return response_base.fail(res=CustomResponse(code=400, msg='主题不存在'))

    # ✅ 手动转换嵌套结构（ORM → Pydantic）
    from backend.app.userecho.schema.feedback import FeedbackOut
    from backend.app.userecho.schema.priority import PriorityScoreOut
    from backend.app.userecho.schema.status_history import StatusHistoryOut
    
    detail_out = {
        'topic': TopicOut.model_validate(detail['topic']),
        'feedbacks': [FeedbackOut.model_validate(fb) for fb in detail['feedbacks']],
        'priority_score': PriorityScoreOut.model_validate(detail['priority_score']) if detail['priority_score'] else None,
        'status_history': [StatusHistoryOut.model_validate(sh) for sh in detail['status_history']]
    }

    return response_base.success(data=detail_out)


@router.post('', summary='创建主题')
async def create_topic(
    data: TopicCreate,
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
):
    """创建主题（手动创建）"""
    topic = await topic_service.create_topic(
        db=db,
        tenant_id=tenant_id,
        data=data
    )
    # ✅ Pydantic 自动将 ORM 对象转换为 TopicOut（排除 centroid）
    topic_out = TopicOut.model_validate(topic)
    return response_base.success(data=topic_out)


@router.put('/{topic_id}', summary='更新主题')
async def update_topic(
    topic_id: str,
    data: TopicUpdate,
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
):
    """更新主题"""
    topic = await topic_service.update_topic(
        db=db,
        tenant_id=tenant_id,
        topic_id=topic_id,
        data=data
    )
    if not topic:
        return response_base.fail(res=CustomResponse(code=400, msg='主题不存在'))
    # ✅ Pydantic 自动将 ORM 对象转换为 TopicOut
    topic_out = TopicOut.model_validate(topic)
    return response_base.success(data=topic_out)


@router.api_route('/{topic_id}/status', methods=['PUT', 'PATCH'], summary='更新主题状态')
async def update_topic_status(
    topic_id: str,
    data: TopicStatusUpdateParam,
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
    current_user_id: int = Depends(get_current_user_id),
):
    """
    更新主题状态（自动记录状态变更历史）

    - **status**: 新状态 (pending/planned/in_progress/completed/ignored)
    - **reason**: 变更原因（可选）
    """
    topic = await topic_service.update_status_with_history(
        db=db,
        tenant_id=tenant_id,
        topic_id=topic_id,
        data=data,
        current_user_id=current_user_id
    )
    if not topic:
        return response_base.fail(res=CustomResponse(code=400, msg='主题不存在'))
    # ✅ Pydantic 自动将 ORM 对象转换为 TopicOut
    topic_out = TopicOut.model_validate(topic)
    return response_base.success(data=topic_out, res=CustomResponse(code=200, msg='状态更新成功'))
