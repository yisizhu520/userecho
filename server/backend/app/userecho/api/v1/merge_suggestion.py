"""合并建议 API"""

from fastapi import APIRouter

from backend.app.userecho.crud.crud_feedback import crud_feedback
from backend.app.userecho.crud.crud_merge_suggestion import crud_merge_suggestion
from backend.app.userecho.crud.crud_topic import crud_topic
from backend.app.userecho.schema.merge_suggestion import (
    BatchProcessResult,
    MergeSuggestionOut,
    ProcessSuggestionRequest,
)
from backend.common.log import log
from backend.common.response.response_schema import response_base
from backend.common.security.jwt import CurrentTenantId, DependsJwtAuth
from backend.database.db import CurrentSession

router = APIRouter(prefix="/merge-suggestions", tags=["Merge Suggestions"])


@router.get("/pending", summary="获取待处理的合并建议")
async def get_pending_merge_suggestions(
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
    _: str = DependsJwtAuth,
) -> dict:
    """
    获取待处理的合并建议

    Returns:
        建议列表
    """
    suggestions = await crud_merge_suggestion.get_pending_suggestions(db=db, tenant_id=tenant_id, skip=0, limit=100)

    results = []
    for s in suggestions:
        results.append(
            MergeSuggestionOut(
                suggestion_id=s.id,
                cluster_label=s.cluster_label,
                suggested_topic_id=s.suggested_topic_id,
                suggested_topic_title=s.suggested_topic_title,
                suggested_topic_status=s.suggested_topic_status,
                similarity=s.similarity,
                feedback_count=s.feedback_count,
                ai_generated_title=s.ai_generated_title,
                status=s.status,
                created_time=s.created_time.isoformat(),
            )
        )

    return response_base.success(data=results)


@router.post("/process", summary="批量处理合并建议")
async def process_suggestions(
    data: ProcessSuggestionRequest,
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
    current_user: str = DependsJwtAuth,
) -> dict:
    """
    批量处理合并建议

    Args:
        data: 处理请求
        - action: accept(关联到已有需求), reject(拒绝), create_new(创建新需求)
        - suggestion_ids: 建议ID列表

    Returns:
        处理结果
    """
    success_count = 0
    failed_count = 0
    errors = []

    for suggestion_id in data.suggestion_ids:
        try:
            # 获取建议
            suggestion = await crud_merge_suggestion.get_by_id(db=db, tenant_id=tenant_id, obj_id=suggestion_id)
            if not suggestion:
                errors.append({"suggestion_id": suggestion_id, "error": "建议不存在"})
                failed_count += 1
                continue

            if data.action == "accept":
                # 关联反馈到已有需求
                await crud_feedback.batch_update_clustering(
                    db=db,
                    tenant_id=tenant_id,
                    feedback_ids=suggestion.feedback_ids,
                    clustering_status="clustered",
                    topic_id=suggestion.suggested_topic_id,
                    clustering_metadata={
                        "suggestion_id": suggestion_id,
                        "processed_action": "accept",
                    },
                )

                # 更新 Topic 反馈数量
                await crud_topic.increment_feedback_count(
                    db=db,
                    tenant_id=tenant_id,
                    topic_id=suggestion.suggested_topic_id,
                    delta=suggestion.feedback_count,
                )

                # 更新建议状态
                await crud_merge_suggestion.update_status(
                    db=db,
                    tenant_id=tenant_id,
                    suggestion_id=suggestion_id,
                    status="accepted",
                    processed_by=current_user,
                )

                success_count += 1

            elif data.action == "reject":
                # 拒绝建议，反馈保持 pending 状态
                await crud_merge_suggestion.update_status(
                    db=db,
                    tenant_id=tenant_id,
                    suggestion_id=suggestion_id,
                    status="rejected",
                    processed_by=current_user,
                )
                success_count += 1

            elif data.action == "create_new":
                # 标记为创建新需求（前端会跳转到创建页面）
                await crud_merge_suggestion.update_status(
                    db=db,
                    tenant_id=tenant_id,
                    suggestion_id=suggestion_id,
                    status="create_new",
                    processed_by=current_user,
                )
                success_count += 1

            else:
                errors.append({"suggestion_id": suggestion_id, "error": f"未知操作类型: {data.action}"})
                failed_count += 1

        except Exception as e:
            log.error(f"Failed to process suggestion {suggestion_id}: {e}")
            errors.append({"suggestion_id": suggestion_id, "error": str(e)})
            failed_count += 1

    result = BatchProcessResult(
        success_count=success_count,
        failed_count=failed_count,
        errors=errors if errors else None,
    )

    return response_base.success(data=result)


@router.get("/count", summary="统计待处理建议数量")
async def count_pending_suggestions(
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
    _: str = DependsJwtAuth,
) -> dict:
    """
    统计待处理建议数量

    Returns:
        待处理数量
    """
    count = await crud_merge_suggestion.count_pending(db=db, tenant_id=tenant_id)
    return response_base.success(data={"count": count})
