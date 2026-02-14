"""反馈 API 端点"""

from io import BytesIO

from fastapi import APIRouter, Depends, File, UploadFile
import pandas as pd

from backend.app.userecho.schema.feedback import (
    FeedbackCreate,
    FeedbackListParams,
    FeedbackOut,
    FeedbackUpdate,
    ScreenshotAnalyzeResponse,
    ExtractedScreenshotData,
    ScreenshotFeedbackCreate,
)
from backend.app.userecho.service import feedback_service, import_service
from backend.common.response.response_code import CustomResponse
from backend.common.response.response_schema import response_base
from backend.common.security.jwt import CurrentTenantId
from backend.database.db import CurrentSession

router = APIRouter(prefix='/feedbacks', tags=['UserEcho - 反馈管理'])


@router.get('', summary='获取反馈列表')
async def get_feedbacks(
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
    skip: int = 0,
    limit: int = 100,
    topic_id: str | None = None,
    customer_id: str | None = None,
    is_urgent: bool | None = None,
    has_topic: bool | None = None,
    clustering_status: str | None = None,
):
    """
    获取反馈列表（支持过滤）

    - **topic_id**: 过滤主题ID
    - **customer_id**: 过滤客户ID
    - **is_urgent**: 过滤紧急程度
    - **has_topic**: 过滤是否已聚类 (true=已聚类, false=未聚类)
    - **clustering_status**: 过滤聚类状态 (pending/processing/clustered/failed)
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
        clustering_status=clustering_status,
    )
    # ✅ 关联查询返回字典（包含 customer_name, topic_title），已在 CRUD 层处理
    # 字典可以直接被 Pydantic 验证（FeedbackOut 支持 from_attributes）
    feedbacks_out = [FeedbackOut.model_validate(fb) for fb in feedbacks]
    return response_base.success(data=feedbacks_out)


@router.post('', summary='创建反馈')
async def create_feedback(
    data: FeedbackCreate,
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
):
    """创建反馈（自动生成 AI 摘要）"""
    feedback = await feedback_service.create_with_ai_processing(
        db=db,
        tenant_id=tenant_id,
        data=data,
        generate_summary=True
    )
    # ✅ Pydantic 自动将 ORM 对象转换为 FeedbackOut（排除 embedding）
    feedback_out = FeedbackOut.model_validate(feedback)
    return response_base.success(data=feedback_out)


@router.put('/{feedback_id}', summary='更新反馈')
async def update_feedback(
    feedback_id: str,
    data: FeedbackUpdate,
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
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
    # ✅ Pydantic 自动将 ORM 对象转换为 FeedbackOut
    feedback_out = FeedbackOut.model_validate(feedback)
    return response_base.success(data=feedback_out)


@router.delete('/{feedback_id}', summary='删除反馈')
async def delete_feedback(
    feedback_id: str,
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
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
    tenant_id: str = CurrentTenantId,
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
    tenant_id: str = CurrentTenantId,
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
    from backend.app.userecho.model.feedback import Feedback
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


# ==================== 截图智能识别相关接口 ====================


@router.post('/screenshot/analyze', summary='截图智能识别（异步）')
async def analyze_screenshot(
    file: UploadFile = File(..., description='截图文件（PNG/JPG/JPEG/WEBP，最大 10MB）'),
    tenant_id: str = CurrentTenantId,
):
    """
    上传截图并 AI 智能识别（异步处理）
    
    流程：
    1. 验证文件格式和大小
    2. 保存到临时目录
    3. 提交 Celery 异步任务
    4. 立即返回 task_id
    
    前端轮询：
    - 使用返回的 task_id 调用 GET /api/v1/task/{task_id} 查询状态
    - 状态：PENDING → STARTED → SUCCESS/FAILURE
    
    返回：
    - task_id: 任务 ID
    - status: processing（处理中）
    - status_url: 状态查询 URL
    """
    from backend.common.log import log
    import os
    import tempfile
    import uuid
    
    # 1. 验证文件
    if not file.filename:
        return response_base.fail(res=CustomResponse(code=400, msg='文件名不能为空'))
    
    # 验证文件类型
    allowed_extensions = {'png', 'jpg', 'jpeg', 'webp'}
    file_ext = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
    if file_ext not in allowed_extensions:
        return response_base.fail(res=CustomResponse(
            code=400, 
            msg=f'不支持的文件格式，仅支持: {", ".join(allowed_extensions)}'
        ))
    
    # 验证文件大小（10MB）
    max_size = 10 * 1024 * 1024  # 10MB
    
    # 读取并验证大小
    content = await file.read()
    file_size = len(content)
    
    if file_size > max_size:
        return response_base.fail(res=CustomResponse(
            code=400, 
            msg=f'文件过大（{file_size / 1024 / 1024:.1f}MB），最大支持 10MB'
        ))
    
    try:
        # 2. 保存到临时目录
        temp_dir = tempfile.gettempdir()
        screenshots_dir = os.path.join(temp_dir, 'screenshots')
        os.makedirs(screenshots_dir, exist_ok=True)
        
        temp_filename = f'screenshot_{uuid.uuid4()}.{file_ext}'
        temp_file_path = os.path.join(screenshots_dir, temp_filename)
        
        with open(temp_file_path, 'wb') as f:
            f.write(content)
        
        log.info(f'Saved temp screenshot for tenant {tenant_id}: {temp_file_path}')
        
        # 3. 提交 Celery 任务
        from backend.app.task.tasks.userecho.tasks import analyze_screenshot_task
        
        task = analyze_screenshot_task.delay(
            file_path=temp_file_path,
            content_type=file.content_type or f'image/{file_ext}',
            tenant_id=tenant_id,
            original_filename=file.filename,
        )
        
        log.info(f'Submitted screenshot analysis task: {task.id} for tenant {tenant_id}')
        
        # 4. 返回 task_id 和状态查询 URL
        return response_base.success(data={
            'task_id': task.id,
            'status': 'processing',
            'status_url': f'/api/v1/task/{task.id}',
        })
        
    except Exception as e:
        log.error(f'Failed to submit screenshot analysis task for tenant {tenant_id}: {e}')
        import traceback
        log.error(f'Traceback: {traceback.format_exc()}')
        
        # 清理临时文件（如果存在）
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception:
                pass
        
        return response_base.fail(res=CustomResponse(
            code=500, 
            msg=f'提交识别任务失败: {str(e)}'
        ))


@router.get('/screenshot/task/{task_id}', summary='查询截图分析任务状态')
async def get_screenshot_task_status(
    task_id: str,
    tenant_id: str = CurrentTenantId,
):
    """
    查询截图分析任务状态
    
    返回字段：
    - task_id: 任务 ID
    - state: PENDING / STARTED / SUCCESS / FAILURE / RETRY
    - result: 成功时返回截图分析结果
        - screenshot_url: 截图 OSS URL
        - extracted: 提取的反馈信息
            - platform: 平台类型
            - user_name: 用户昵称
            - user_id: 用户 ID
            - content: 反馈内容
            - feedback_type: 反馈类型
            - sentiment: 情感倾向
            - confidence: 置信度
    - error: 失败时返回错误信息
    """
    from backend.app.task.celery import celery_app
    
    _ = tenant_id  # 租户鉴权由依赖保证
    r = celery_app.AsyncResult(task_id)
    data: dict = {'task_id': task_id, 'state': r.state}
    
    if r.successful():
        data['result'] = r.result
    elif r.failed():
        data['error'] = str(r.result)
    
    return response_base.success(data=data)


@router.post('/screenshot/create', summary='从截图创建反馈')
async def create_feedback_from_screenshot(
    data: ScreenshotFeedbackCreate,
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
):
    """
    从截图识别结果创建反馈
    
    字段说明：
    - content: 反馈内容（必填）
    - screenshot_url: 截图 URL（必填）
    - source_platform: 来源平台（必填）
    - source_user_name: 平台用户昵称
    - source_user_id: 平台用户 ID
    - ai_confidence: AI 识别置信度
    - customer_id: 关联的客户 ID（可选，MVP 阶段通常为空）
    """
    from backend.app.userecho.model.feedback import Feedback
    from backend.utils.ai_client import ai_client
    from backend.common.log import log
    from backend.utils.timezone import timezone
    
    try:
        # 1. 创建反馈记录
        feedback = Feedback(
            tenant_id=tenant_id,
            customer_id=data.customer_id,
            anonymous_author=data.source_user_name or '匿名用户',
            anonymous_source=data.source_platform,
            content=data.content,
            source='screenshot',
            screenshot_url=data.screenshot_url,
            source_platform=data.source_platform,
            source_user_name=data.source_user_name,
            source_user_id=data.source_user_id,
            ai_confidence=data.ai_confidence,
            submitted_at=timezone.now(),
        )
        
        # 2. 生成 AI 摘要
        try:
            ai_summary = await ai_client.generate_summary(data.content, max_length=20)
            feedback.ai_summary = ai_summary
        except Exception as e:
            log.warning(f'Failed to generate summary for screenshot feedback: {e}')
        
        # 3. 保存到数据库
        db.add(feedback)
        await db.commit()
        await db.refresh(feedback)
        
        log.info(f'Created feedback from screenshot: id={feedback.id}, tenant={tenant_id}, platform={data.source_platform}')
        
        # 4. 返回结果
        feedback_out = FeedbackOut.model_validate(feedback)
        return response_base.success(data=feedback_out)
        
    except Exception as e:
        log.error(f'Failed to create feedback from screenshot for tenant {tenant_id}: {e}')
        import traceback
        log.error(f'Traceback: {traceback.format_exc()}')
        await db.rollback()
        return response_base.fail(res=CustomResponse(
            code=500, 
            msg=f'创建反馈失败: {str(e)}'
        ))
