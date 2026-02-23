"""回复模板 API 端点"""

from fastapi import APIRouter, Depends

from backend.app.userecho.crud.crud_reply_template import crud_reply_template
from backend.app.userecho.model.reply_template import ReplyTemplate
from backend.app.userecho.schema.reply_template import (
    ReplyTemplateCreate,
    ReplyTemplateListResponse,
    ReplyTemplateOut,
    ReplyTemplateUpdate,
)
from backend.common.response.response_code import CustomResponse
from backend.common.response.response_schema import response_base
from backend.common.security.jwt import CurrentTenantId
from backend.database.db import CurrentSession

router = APIRouter(prefix='/reply-templates', tags=['UserEcho - 回复模板'])


def get_current_user_id() -> int:
    """获取当前用户ID"""
    # TODO: 从 JWT token 中提取
    return 1


@router.get('', summary='获取回复模板列表')
async def get_templates(
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
    category: str | None = None,
    tone: str | None = None,
):
    """
    获取回复模板列表

    - **category**: 分类筛选 (general/bug_fix/feature/improvement)
    - **tone**: 语气筛选 (formal/friendly/concise)
    """
    templates = await crud_reply_template.get_active_templates(db=db, tenant_id=tenant_id, category=category, tone=tone)

    templates_out = [ReplyTemplateOut.model_validate(t) for t in templates]

    return response_base.success(data=ReplyTemplateListResponse(items=templates_out, total=len(templates_out)))


@router.get('/{template_id}', summary='获取模板详情')
async def get_template(
    template_id: str,
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
):
    """获取模板详情"""
    template = await crud_reply_template.get_by_id(db, tenant_id, template_id)
    if not template:
        return response_base.fail(res=CustomResponse(code=400, msg='模板不存在'))

    return response_base.success(data=ReplyTemplateOut.model_validate(template))


@router.post('', summary='创建回复模板')
async def create_template(
    data: ReplyTemplateCreate,
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
    current_user_id: int = Depends(get_current_user_id),
):
    """创建回复模板"""
    template = ReplyTemplate(
        tenant_id=tenant_id,
        name=data.name,
        description=data.description,
        content=data.content,
        category=data.category,
        tone=data.tone,
        language=data.language,
        is_active=data.is_active,
        is_system=False,
        created_by=current_user_id,
    )

    db.add(template)
    await db.commit()
    await db.refresh(template)

    return response_base.success(
        data=ReplyTemplateOut.model_validate(template),
        res=CustomResponse(code=200, msg='创建成功'),
    )


@router.put('/{template_id}', summary='更新回复模板')
async def update_template(
    template_id: str,
    data: ReplyTemplateUpdate,
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
):
    """更新回复模板"""
    template = await crud_reply_template.get_by_id(db, tenant_id, template_id)
    if not template:
        return response_base.fail(res=CustomResponse(code=400, msg='模板不存在'))

    # 系统模板不允许修改
    if template.is_system:
        return response_base.fail(res=CustomResponse(code=403, msg='系统模板不允许修改'))

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(template, key, value)

    await db.commit()
    await db.refresh(template)

    return response_base.success(
        data=ReplyTemplateOut.model_validate(template),
        res=CustomResponse(code=200, msg='更新成功'),
    )


@router.delete('/{template_id}', summary='删除回复模板')
async def delete_template(
    template_id: str,
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
):
    """删除回复模板"""
    template = await crud_reply_template.get_by_id(db, tenant_id, template_id)
    if not template:
        return response_base.fail(res=CustomResponse(code=400, msg='模板不存在'))

    # 系统模板不允许删除
    if template.is_system:
        return response_base.fail(res=CustomResponse(code=403, msg='系统模板不允许删除'))

    await db.delete(template)
    await db.commit()

    return response_base.success(res=CustomResponse(code=200, msg='删除成功'))


@router.post('/{template_id}/use', summary='使用模板（增加使用次数）')
async def use_template(
    template_id: str,
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
):
    """使用模板，增加使用次数计数"""
    template = await crud_reply_template.increment_usage(db, tenant_id, template_id)
    if not template:
        return response_base.fail(res=CustomResponse(code=400, msg='模板不存在'))

    return response_base.success(data={'content': template.content})
