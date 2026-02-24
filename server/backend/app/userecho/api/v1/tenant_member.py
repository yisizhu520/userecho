"""租户成员 API"""

from typing import Annotated

from fastapi import APIRouter, Query

from backend.app.userecho.schema.tenant import TenantOut
from backend.app.userecho.schema.tenant_rbac import (
    TenantMemberCreate,
    TenantMemberOut,
    TenantMemberRoleUpdate,
    TenantMemberUpdate,
)
from backend.app.userecho.service.tenant_member_service import tenant_member_service
from backend.common.response.response_schema import ResponseModel, ResponseSchemaModel
from backend.common.security.jwt import CurrentTenantId, CurrentUserId, DependsJwtAuth
from backend.database.db import CurrentSession

router = APIRouter()


@router.get("/tenant-info", summary="获取当前租户信息", dependencies=[DependsJwtAuth])
async def get_tenant_info(
    db: CurrentSession,
) -> ResponseSchemaModel[TenantOut]:
    """获取当前租户的基本信息"""
    from backend.app.userecho.model.tenant import Tenant
    from backend.common.context import ctx

    # 从上下文获取 tenant_id
    tenant_id = ctx.tenant_id
    if not tenant_id:
        return ResponseSchemaModel(
            code=400,
            msg="租户信息缺失",
            data=None,
        )

    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        return ResponseSchemaModel(
            code=404,
            msg="租户不存在",
            data=None,
        )

    return ResponseSchemaModel(data=TenantOut.model_validate(tenant))


@router.get("", summary="获取成员列表", dependencies=[DependsJwtAuth])
async def get_member_list(
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
    status: Annotated[str | None, Query(description="状态")] = None,
) -> ResponseSchemaModel[list[TenantMemberOut]]:
    """获取当前租户的成员列表"""
    members = await tenant_member_service.get_list(db, tenant_id, status=status)
    return ResponseSchemaModel(data=[TenantMemberOut.model_validate(m) for m in members])


@router.get("/my-permissions", summary="获取我的权限", dependencies=[DependsJwtAuth])
async def get_my_permissions(
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
    user_id: int = CurrentUserId,
) -> ResponseSchemaModel[list[str]]:
    """获取当前用户在当前租户的权限列表"""
    from backend.app.userecho.crud.crud_tenant_member import tenant_member_dao

    member = await tenant_member_dao.get_by_user_id(db, tenant_id, user_id)
    if not member:
        return ResponseSchemaModel(data=[])

    permissions = await tenant_member_service.get_member_permissions(db, member.id)
    return ResponseSchemaModel(data=permissions)


@router.get("/{member_id}", summary="获取成员详情", dependencies=[DependsJwtAuth])
async def get_member(db: CurrentSession, member_id: str) -> ResponseSchemaModel[TenantMemberOut]:
    """获取成员详情"""
    member = await tenant_member_service.get(db, member_id)
    return ResponseSchemaModel(data=TenantMemberOut.model_validate(member))


@router.get("/{member_id}/roles", summary="获取成员角色", dependencies=[DependsJwtAuth])
async def get_member_roles(db: CurrentSession, member_id: str) -> ResponseSchemaModel[list[str]]:
    """获取成员的角色 ID 列表"""
    role_ids = await tenant_member_service.get_member_role_ids(db, member_id)
    return ResponseSchemaModel(data=role_ids)


@router.post("", summary="创建成员", dependencies=[DependsJwtAuth])
async def create_member(
    db: CurrentSession,
    body: TenantMemberCreate,
    tenant_id: str = CurrentTenantId,
    current_user_id: int = CurrentUserId,
) -> ResponseSchemaModel[TenantMemberOut]:
    """创建成员（使用 Email 作为唯一标识）"""
    _, member = await tenant_member_service.create(
        db,
        tenant_id=tenant_id,
        email=body.email,
        nickname=body.nickname,
        password=body.password,
        username=body.username,
        role_ids=body.role_ids,
        created_by=current_user_id,
    )
    await db.commit()
    return ResponseSchemaModel(data=TenantMemberOut.model_validate(member))


@router.put("/{member_id}", summary="更新成员", dependencies=[DependsJwtAuth])
async def update_member(
    db: CurrentSession,
    member_id: str,
    body: TenantMemberUpdate,
    current_user_id: int = CurrentUserId,
) -> ResponseSchemaModel[TenantMemberOut]:
    """更新成员信息"""
    member = await tenant_member_service.update(
        db,
        member_id,
        username=body.username,
        nickname=body.nickname,
        role_ids=body.role_ids,
        user_type=body.user_type,
        status=body.status,
        assigned_by=current_user_id,
    )
    await db.commit()
    return ResponseSchemaModel(data=TenantMemberOut.model_validate(member))


@router.put("/{member_id}/roles", summary="更新成员角色", dependencies=[DependsJwtAuth])
async def update_member_roles(
    db: CurrentSession,
    member_id: str,
    body: TenantMemberRoleUpdate,
    current_user_id: int = CurrentUserId,
) -> ResponseModel:
    """更新成员角色"""
    await tenant_member_service.update_roles(db, member_id, body.role_ids, assigned_by=current_user_id)
    await db.commit()
    return ResponseModel()


@router.delete("/{member_id}", summary="移除成员", dependencies=[DependsJwtAuth])
async def delete_member(db: CurrentSession, member_id: str) -> ResponseModel:
    """移除成员"""
    await tenant_member_service.delete(db, member_id)
    await db.commit()
    return ResponseModel()
