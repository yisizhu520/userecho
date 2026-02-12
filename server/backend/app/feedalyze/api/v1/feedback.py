"""反馈 API 端点"""

from io import BytesIO

from fastapi import APIRouter, Depends, File, UploadFile
import pandas as pd

from backend.app.feedalyze.schema.feedback import (
    FeedbackCreate,
    FeedbackListParams,
    FeedbackOut,
    FeedbackUpdate,
)
from backend.app.feedalyze.service import feedback_service, import_service
from backend.common.response.response_code import CustomResponse
from backend.common.response.response_schema import response_base
from backend.database.db import CurrentSession

router = APIRouter(prefix='/feedbacks', tags=['Feedalyze - 反馈管理'])


def get_current_tenant_id() -> str:
    """
    获取当前租户ID
    TODO: 从 JWT token 中提取，暂时返回默认值
    """
    return 'default-tenant'


@router.get('', summary='获取反馈列表')
async def get_feedbacks(
    db: CurrentSession,
    tenant_id: str = Depends(get_current_tenant_id),
    skip: int = 0,
    limit: int = 100,
    topic_id: str | None = None,
    customer_id: str | None = None,
    is_urgent: bool | None = None,
    has_topic: bool | None = None,
):
    """
    获取反馈列表（支持过滤）

    - **topic_id**: 过滤主题ID
    - **customer_id**: 过滤客户ID
    - **is_urgent**: 过滤紧急程度
    - **has_topic**: 过滤是否已聚类 (true=已聚类, false=未聚类)
    """
    feedbacks = await feedback_service.get_list(
        db=db,
        tenant_id=tenant_id,
        skip=skip,
        limit=limit,
        topic_id=topic_id,
        customer_id=customer_id,
        is_urgent=is_urgent,
        has_topic=has_topic,
    )
    return response_base.success(data=feedbacks)


@router.post('', summary='创建反馈')
async def create_feedback(
    data: FeedbackCreate,
    db: CurrentSession,
    tenant_id: str = Depends(get_current_tenant_id),
):
    """创建反馈（自动生成 AI 摘要）"""
    feedback = await feedback_service.create_with_ai_processing(
        db=db,
        tenant_id=tenant_id,
        data=data,
        generate_summary=True
    )
    return response_base.success(data=feedback)


@router.put('/{feedback_id}', summary='更新反馈')
async def update_feedback(
    feedback_id: str,
    data: FeedbackUpdate,
    db: CurrentSession,
    tenant_id: str = Depends(get_current_tenant_id),
):
    """更新反馈"""
    feedback = await feedback_service.update_feedback(
        db=db,
        tenant_id=tenant_id,
        feedback_id=feedback_id,
        data=data
    )
    if not feedback:
        return response_base.fail(res=CustomResponse(code=400, msg='反馈不存在'))
    return response_base.success(data=feedback)


@router.delete('/{feedback_id}', summary='删除反馈')
async def delete_feedback(
    feedback_id: str,
    db: CurrentSession,
    tenant_id: str = Depends(get_current_tenant_id),
):
    """删除反馈（软删除）"""
    success = await feedback_service.delete_feedback(
        db=db,
        tenant_id=tenant_id,
        feedback_id=feedback_id
    )
    if not success:
        return response_base.fail(res=CustomResponse(code=400, msg='反馈不存在或已删除'))
    return response_base.success(res=CustomResponse(code=200, msg='删除成功'))


@router.post('/import', summary='导入 Excel 反馈')
async def import_feedbacks(
    db: CurrentSession,
    file: UploadFile = File(...),
    tenant_id: str = Depends(get_current_tenant_id),
):
    """
    导入 Excel 文件

    支持格式: .xlsx, .xls, .csv

    必填列:
    - 反馈内容
    - 客户名称

    可选列:
    - 客户类型 (normal/paid/major/strategic)
    - 提交时间
    - 是否紧急
    """
    from backend.common.log import log
    
    log.info('[DEBUG] Starting import_feedbacks handler')
    
    try:
        result = await import_service.import_excel(
            db=db,
            tenant_id=tenant_id,
            file=file,
            generate_summary=False  # 导入时不生成摘要，避免超时
        )
        log.info(f'[DEBUG] import_excel returned: type={type(result)}, result={result}')

        if result['status'] == 'error':
            log.info('[DEBUG] Returning error response')
            resp = response_base.fail(res=CustomResponse(code=400, msg=result['message']))
            log.info(f'[DEBUG] Error response created: type={type(resp)}, resp={resp}')
            return resp

        log.info('[DEBUG] Returning success response')
        resp = response_base.success(data=result)
        log.info(f'[DEBUG] Success response created: type={type(resp)}, resp={resp}')
        return resp
    except Exception as e:
        log.error(f'[DEBUG] Exception in import_feedbacks: {e}')
        import traceback
        log.error(f'[DEBUG] Traceback: {traceback.format_exc()}')
        raise


@router.get('/import/template', summary='下载导入模板')
async def download_template():
    """下载 Excel 导入模板"""
    from fastapi.responses import StreamingResponse

    template_df = import_service.generate_template()

    # 生成 Excel 文件
    output = BytesIO()
    try:
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            template_df.to_excel(writer, index=False, sheet_name='反馈导入模板')
        output.seek(0)
        return StreamingResponse(
            output,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': 'attachment; filename=feedback_import_template.xlsx'},
        )
    except ImportError:
        csv_text = template_df.to_csv(index=False)
        csv_bytes = csv_text.encode('utf-8-sig')
        return StreamingResponse(
            BytesIO(csv_bytes),
            media_type='text/csv; charset=utf-8',
            headers={'Content-Disposition': 'attachment; filename=feedback_import_template.csv'},
        )


@router.post('/batch-generate-summary', summary='批量生成 AI 摘要')
async def batch_generate_summary(
    db: CurrentSession,
    tenant_id: str = Depends(get_current_tenant_id),
    limit: int = 100,
):
    """
    为没有 AI 摘要的反馈批量生成摘要
    
    适用场景：
    - Excel 导入后批量补充摘要
    - 历史数据补充摘要
    
    Args:
        limit: 最多处理多少条反馈（默认 100）
    """
    from backend.app.feedalyze.model.feedback import Feedback
    from backend.utils.ai_client import ai_client
    from backend.common.log import log
    from sqlalchemy import select
    
    try:
        # 1. 查询没有摘要的反馈 (ai_summary IS NULL)
        query = select(Feedback).where(
            Feedback.tenant_id == tenant_id,
            Feedback.ai_summary.is_(None),
            Feedback.deleted_at.is_(None)
        ).limit(limit)
        
        result = await db.execute(query)
        feedbacks = list(result.scalars().all())
        
        if not feedbacks:
            return response_base.success(data={
                'total': 0,
                'success': 0,
                'failed': 0,
                'message': '没有需要生成摘要的反馈'
            })
        
        # 2. 批量生成摘要
        success_count = 0
        failed_count = 0
        
        for feedback in feedbacks:
            try:
                ai_summary = await ai_client.generate_summary(feedback.content, max_length=20)
                feedback.ai_summary = ai_summary
                success_count += 1
            except Exception as e:
                log.warning(f'Failed to generate summary for feedback {feedback.id}: {e}')
                failed_count += 1
        
        await db.commit()
        
        log.info(f'Batch summary generation completed for tenant {tenant_id}: {success_count} success, {failed_count} failed')
        
        return response_base.success(data={
            'total': len(feedbacks),
            'success': success_count,
            'failed': failed_count,
            'message': f'成功为 {success_count} 条反馈生成摘要'
        })
        
    except Exception as e:
        log.error(f'Batch summary generation failed for tenant {tenant_id}: {e}')
        return response_base.fail(res=CustomResponse(code=500, msg=f'批量生成摘要失败: {str(e)}'))
