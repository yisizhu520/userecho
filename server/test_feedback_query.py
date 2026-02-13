"""
测试反馈查询 - 诊断 Celery worker 查不到数据的问题
"""
import asyncio
from sqlalchemy import select, func

from backend.database.db import async_db_session
from backend.app.feedalyze.model.feedback import Feedback
from backend.common.log import log


async def test_feedback_query():
    """测试反馈查询"""
    tenant_id = 'default-tenant'
    
    async with async_db_session() as db:
        # 1. 统计总反馈数
        total_query = select(func.count(Feedback.id)).where(
            Feedback.tenant_id == tenant_id,
            Feedback.deleted_at.is_(None),
        )
        total_result = await db.execute(total_query)
        total_count = total_result.scalar()
        log.info(f'📊 Total feedbacks: {total_count}')
        
        # 2. 统计各状态的反馈数
        status_query = select(
            Feedback.clustering_status,
            func.count(Feedback.id).label('count')
        ).where(
            Feedback.tenant_id == tenant_id,
            Feedback.deleted_at.is_(None),
        ).group_by(Feedback.clustering_status)
        
        status_result = await db.execute(status_query)
        status_counts = {row[0]: row[1] for row in status_result.all()}
        log.info(f'📊 By clustering_status: {status_counts}')
        
        # 3. 统计 topic_id 为 NULL 的反馈数
        no_topic_query = select(func.count(Feedback.id)).where(
            Feedback.tenant_id == tenant_id,
            Feedback.topic_id.is_(None),
            Feedback.deleted_at.is_(None),
        )
        no_topic_result = await db.execute(no_topic_query)
        no_topic_count = no_topic_result.scalar()
        log.info(f'📊 No topic (topic_id IS NULL): {no_topic_count}')
        
        # 4. 统计待聚类的反馈数（完整条件）
        pending_query = select(func.count(Feedback.id)).where(
            Feedback.tenant_id == tenant_id,
            Feedback.topic_id.is_(None),
            Feedback.clustering_status.in_(['pending', 'failed']),
            Feedback.deleted_at.is_(None),
        )
        pending_result = await db.execute(pending_query)
        pending_count = pending_result.scalar()
        log.info(f'📊 Pending clustering (full condition): {pending_count}')
        
        # 5. 查询前10条反馈的详细信息
        sample_query = select(
            Feedback.id,
            Feedback.content,
            Feedback.topic_id,
            Feedback.clustering_status,
        ).where(
            Feedback.tenant_id == tenant_id,
            Feedback.deleted_at.is_(None),
        ).limit(10)
        
        sample_result = await db.execute(sample_query)
        samples = sample_result.all()
        
        log.info(f'\n📋 Sample feedbacks (first 10):')
        for fb in samples:
            log.info(f'  - ID: {fb.id[:8]}... | topic_id: {fb.topic_id or "NULL"} | status: {fb.clustering_status} | content: {fb.content[:50]}...')


if __name__ == '__main__':
    asyncio.run(test_feedback_query())
