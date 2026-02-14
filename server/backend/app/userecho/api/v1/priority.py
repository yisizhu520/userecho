"""优先级评分 API"""
from fastapi import APIRouter, Depends

from backend.app.userecho.crud.crud_feedback import crud_feedback
from backend.app.userecho.crud.crud_priority import crud_priority_score
from backend.app.userecho.crud.crud_topic import crud_topic
from backend.app.userecho.schema.priority import PriorityScoreCreate, PriorityScoreUpdate
from backend.app.userecho.service.priority_service import priority_service
from backend.common.log import log
from backend.common.response.response_schema import response_base
from backend.common.security.jwt import CurrentTenantId
from backend.database.db import CurrentSession
from backend.utils.ai_client import ai_client

router = APIRouter()


def get_current_user_id() -> int:
    """获取当前用户ID"""
    # TODO: 从 JWT token 中提取
    return 1


@router.post('/topics/{topic_id}/priority/analyze', summary='AI 分析优先级')
async def analyze_priority(
    topic_id: str,
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
    current_user_id: int = Depends(get_current_user_id),
):
    """
    PM 点击「AI 辅助评分」时调用
    触发完整的 AI 分析（包含 LLM 调用）
    
    Returns:
        {
            "impact_scope": {"scope": 5, "confidence": 0.8, "reason": "..."},
            "business_value": {"value": 7, "confidence": 1.0, "reason": "..."},
            "dev_cost": {"days": 3, "confidence": 0.6, "reason": "..."}
        }
    """
    try:
        # 1. 获取 Topic
        topic = await crud_topic.get_by_id(db, tenant_id, topic_id)
        if not topic:
            return response_base.fail(msg='Topic 不存在')
        
        # 2. 获取关联的反馈
        feedbacks = await crud_feedback.get_list_with_relations(
            db=db,
            tenant_id=tenant_id,
            topic_id=topic_id,
            limit=100,
        )
        
        if not feedbacks:
            return response_base.fail(msg='该 Topic 没有关联的反馈')
        
        # 3. 提取客户信息
        try:
            customer_ids = {fb.get('customer_id') for fb in feedbacks if fb.get('customer_id')}
            customer_count = len(customer_ids)
            log.debug(f'Extracted {customer_count} unique customers from feedbacks')
        except Exception as e:
            log.error(f'Failed to extract customer_ids: {e}, feedbacks keys: {[list(fb.keys()) if isinstance(fb, dict) else type(fb) for fb in feedbacks[:1]]}')
            raise
        
        # 4. AI 完整分析
        log.info(f'Analyzing priority for topic {topic_id} with {len(feedbacks)} feedbacks, {customer_count} customers')
        
        # 影响范围：AI 分析
        try:
            impact = await ai_client.suggest_impact_scope_ai(
                feedbacks=[fb.get('content', '') for fb in feedbacks],
                customer_count=customer_count,
                title=topic.title,
                category=topic.category,
            )
        except Exception as e:
            log.error(f'AI impact scope analysis failed: {e}')
            raise
        
        # 开发成本：AI 建议
        dev_cost = await ai_client.suggest_dev_cost_ai(
            title=topic.title,
            category=topic.category,
            feedbacks=[fb.get('content', '') for fb in feedbacks[:5]],
        )
        
        # 商业价值：自动计算（基于客户等级）
        try:
            business_value = await priority_service.calculate_business_value(
                db=db,
                topic_id=topic_id,
                tenant_id=tenant_id,
            )
            log.debug(f'Calculated business_value: {business_value}')
        except Exception as e:
            log.error(f'Failed to calculate business value: {e}')
            raise
        
        return response_base.success(data={
            'impact_scope': impact,
            'business_value': {
                'value': business_value,
                'confidence': 1.0,
                'reason': '基于客户等级自动计算'
            },
            'dev_cost': dev_cost
        })
    
    except Exception as e:
        import traceback
        log.error(f'Analyze priority failed: {e}\n{traceback.format_exc()}')
        return response_base.fail(msg=f'AI 分析失败: {str(e)}')


@router.post('/topics/{topic_id}/priority', summary='创建或更新优先级评分')
async def create_or_update_priority(
    topic_id: str,
    data: PriorityScoreCreate,
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
    current_user_id: int = Depends(get_current_user_id),
):
    """
    PM 确认评分后保存
    
    Args:
        topic_id: 主题ID
        data: 评分数据（impact_scope, business_value, dev_cost, urgency_factor）
    """
    # 验证 Topic 是否存在
    topic = await crud_topic.get_by_id(db, tenant_id, topic_id)
    if not topic:
        return response_base.fail(msg='Topic 不存在')
    
    # 创建或更新评分
    await priority_service.create_or_update_priority_score(
        db=db,
        tenant_id=tenant_id,
        topic_id=topic_id,
        impact_scope=data.impact_scope,
        business_value=data.business_value,
        dev_cost=data.dev_cost,
        urgency_factor=data.urgency_factor,
    )
    
    log.info(f'Priority score saved for topic {topic_id} by user {current_user_id}')
    
    return response_base.success(msg='评分已保存')


@router.get('/topics/{topic_id}/priority', summary='获取优先级评分')
async def get_priority_score(
    topic_id: str,
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
):
    """
    获取 Topic 的优先级评分
    
    Returns:
        PriorityScoreOut 或 null
    """
    score = await crud_priority_score.get_by_topic(db, tenant_id, topic_id)
    
    if not score:
        return response_base.success(data=None)
    
    from backend.app.userecho.schema.priority import PriorityScoreOut
    return response_base.success(data=PriorityScoreOut.model_validate(score))


@router.delete('/topics/{topic_id}/priority', summary='删除优先级评分')
async def delete_priority_score(
    topic_id: str,
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
    current_user_id: int = Depends(get_current_user_id),
):
    """
    删除 Topic 的优先级评分
    """
    score = await crud_priority_score.get_by_topic(db, tenant_id, topic_id)
    
    if not score:
        return response_base.fail(msg='评分不存在')
    
    await crud_priority_score.delete(db, score.id)
    
    log.info(f'Priority score deleted for topic {topic_id} by user {current_user_id}')
    
    return response_base.success(msg='评分已删除')
