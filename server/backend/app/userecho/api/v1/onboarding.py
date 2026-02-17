"""引导流程 API 端点

提供新用户创建租户和看板的引导流程接口
"""

from typing import Annotated

from fastapi import APIRouter, Query, Request

from backend.app.userecho.schema.onboarding import (
    CreateBoardOut,
    CreateBoardParam,
    CreateTenantOut,
    CreateTenantParam,
    OnboardingCompleteOut,
    OnboardingStatusOut,
    SlugCheckOut,
)
from backend.app.userecho.service.onboarding_service import onboarding_service
from backend.common.response.response_code import CustomResponse
from backend.common.response.response_schema import ResponseSchemaModel, response_base
from backend.common.security.jwt import DependsJwtAuth
from backend.database.db import CurrentSession, CurrentSessionTransaction

router = APIRouter(prefix='/onboarding', tags=['UserEcho - 引导流程'])


@router.get('/status', summary='获取引导状态', dependencies=[DependsJwtAuth])
async def get_onboarding_status(
    request: Request,
    db: CurrentSession,
) -> ResponseSchemaModel[OnboardingStatusOut]:
    """
    获取当前用户的引导状态

    返回用户是否需要完成引导流程，以及当前进行到哪个步骤
    """
    user_id = request.user.id
    status = await onboarding_service.get_onboarding_status(db=db, user_id=user_id)
    return response_base.success(data=status)


@router.get('/check-slug', summary='检查 Slug 可用性', dependencies=[DependsJwtAuth])
async def check_slug_available(
    db: CurrentSession,
    slug: Annotated[str, Query(min_length=2, max_length=100, description='要检查的 slug')],
) -> ResponseSchemaModel[SlugCheckOut]:
    """
    检查 URL 标识是否可用

    如果不可用，会返回一个建议的替代标识
    """
    result = await onboarding_service.check_slug_available(db=db, slug=slug)
    return response_base.success(data=result)


@router.get('/generate-slug', summary='根据名称生成 Slug', dependencies=[DependsJwtAuth])
async def generate_slug(
    name: Annotated[str, Query(min_length=1, max_length=100, description='公司/团队名称')],
):
    """
    根据公司/团队名称生成 URL 标识建议
    """
    slug = onboarding_service.generate_slug_from_name(name)
    return response_base.success(data={'slug': slug})


@router.post('/tenant', summary='创建租户', dependencies=[DependsJwtAuth])
async def create_tenant(
    request: Request,
    db: CurrentSessionTransaction,
    data: CreateTenantParam,
) -> ResponseSchemaModel[CreateTenantOut]:
    """
    创建租户（团队/公司）

    创建后，当前用户会自动成为该租户的管理员
    """
    try:
        user_id = request.user.id
        tenant = await onboarding_service.create_tenant(db=db, user_id=user_id, data=data)
        return response_base.success(data=tenant)
    except ValueError as e:
        return response_base.fail(res=CustomResponse(code=400, msg=str(e)))


@router.post('/board', summary='创建看板', dependencies=[DependsJwtAuth])
async def create_board(
    request: Request,
    db: CurrentSessionTransaction,
    data: CreateBoardParam,
) -> ResponseSchemaModel[CreateBoardOut]:
    """
    创建第一个看板

    看板用于组织和管理用户反馈
    """
    try:
        user_id = request.user.id
        board = await onboarding_service.create_board(db=db, user_id=user_id, data=data)
        return response_base.success(data=board)
    except ValueError as e:
        return response_base.fail(res=CustomResponse(code=400, msg=str(e)))


@router.post('/complete', summary='完成引导', dependencies=[DependsJwtAuth])
async def complete_onboarding(
    request: Request,
    db: CurrentSession,
) -> ResponseSchemaModel[OnboardingCompleteOut]:
    """
    完成引导流程

    验证租户和看板已创建，返回重定向路径
    """
    try:
        user_id = request.user.id
        result = await onboarding_service.complete_onboarding(db=db, user_id=user_id)
        return response_base.success(data=result)
    except ValueError as e:
        return response_base.fail(res=CustomResponse(code=400, msg=str(e)))
