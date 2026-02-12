"""反馈 API 端点"""

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.feedalyze.schema.feedback import (
    FeedbackCreate,
    FeedbackListParams,
    FeedbackOut,
    FeedbackUpdate,
)
from backend.app.feedalyze.service import feedback_service, import_service
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
    return await response_base.success(data=feedbacks)


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
    return await response_base.success(data=feedback)


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
        return await response_base.fail(msg='反馈不存在')
    return await response_base.success(data=feedback)


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
        return await response_base.fail(msg='反馈不存在或已删除')
    return await response_base.success(msg='删除成功')


@router.post('/import', summary='导入 Excel 反馈')
async def import_feedbacks(
    file: UploadFile = File(...),
    db: CurrentSession = Depends(),
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
    result = await import_service.import_excel(
        db=db,
        tenant_id=tenant_id,
        file=file,
        generate_summary=True
    )

    if result['status'] == 'error':
        return await response_base.fail(msg=result['message'])

    return await response_base.success(data=result)


@router.get('/import/template', summary='下载导入模板')
async def download_template():
    """下载 Excel 导入模板"""
    from io import BytesIO
    from fastapi.responses import StreamingResponse

    template_df = import_service.generate_template()

    # 生成 Excel 文件
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        template_df.to_excel(writer, index=False, sheet_name='反馈导入模板')

    output.seek(0)

    return StreamingResponse(
        output,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': 'attachment; filename=feedback_import_template.xlsx'}
    )


# 需要导入 pandas
import pandas as pd
