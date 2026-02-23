"""租户角色 API"""

from typing import Annotated

from fastapi import APIRouter, Query

from backend.app.userecho.schema.tenant_rbac import (
    TenantPermissionOut,
    TenantRoleCreate,
    TenantRoleOut,
    TenantRolePermissionUpdate,
    TenantRoleUpdate,
)
from backend.app.userecho.service.tenant_role_service import tenant_role_service
from backend.common.response.response_schema import ResponseModel, ResponseSchemaModel
from backend.common.security.jwt import CurrentTenantId, DependsJwtAuth
from backend.database.db import CurrentSession

router = APIRouter()


@router.get("", summary="获取角色列表", dependencies=[DependsJwtAuth])
async def get_role_list(
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
    status: Annotated[str | None, Query(description="角色状态")] = None,
) -> ResponseSchemaModel[list[TenantRoleOut]]:
    """获取当前租户的角色列表"""
    roles = await tenant_role_service.get_list(db, tenant_id, status=status)
    return ResponseSchemaModel(data=[TenantRoleOut.model_validate(r) for r in roles])


@router.get("/permissions", summary="获取权限列表", dependencies=[DependsJwtAuth])
async def get_permission_list(db: CurrentSession) -> ResponseSchemaModel[list[TenantPermissionOut]]:
    """获取所有权限点"""
    permissions = await tenant_role_service.get_permissions(db)
    return ResponseSchemaModel(data=[TenantPermissionOut.model_validate(p) for p in permissions])


@router.get("/{role_id}", summary="获取角色详情", dependencies=[DependsJwtAuth])
async def get_tenant_role(db: CurrentSession, role_id: str) -> ResponseSchemaModel[TenantRoleOut]:
    """获取角色详情"""
    role = await tenant_role_service.get(db, role_id)
    return ResponseSchemaModel(data=TenantRoleOut.model_validate(role))


@router.get("/{role_id}/permissions", summary="获取角色权限", dependencies=[DependsJwtAuth])
async def get_role_permissions(db: CurrentSession, role_id: str) -> ResponseSchemaModel[list[TenantPermissionOut]]:
    """获取角色的权限列表"""
    permissions = await tenant_role_service.get_role_permissions(db, role_id)
    return ResponseSchemaModel(data=[TenantPermissionOut.model_validate(p) for p in permissions])


@router.post("", summary="创建角色", dependencies=[DependsJwtAuth])
async def create_tenant_role(
    db: CurrentSession,
    body: TenantRoleCreate,
    tenant_id: str = CurrentTenantId,
) -> ResponseSchemaModel[TenantRoleOut]:
    """创建角色"""
    role = await tenant_role_service.create(
        db,
        tenant_id=tenant_id,
        name=body.name,
        code=body.code,
        description=body.description,
        permission_ids=body.permission_ids,
    )
    await db.commit()
    return ResponseSchemaModel(data=TenantRoleOut.model_validate(role))


@router.put("/{role_id}", summary="更新角色", dependencies=[DependsJwtAuth])
async def update_tenant_role(
    db: CurrentSession,
    role_id: str,
    body: TenantRoleUpdate,
) -> ResponseSchemaModel[TenantRoleOut]:
    """更新角色"""
    role = await tenant_role_service.update(
        db,
        role_id,
        name=body.name,
        description=body.description,
        status=body.status,
    )
    await db.commit()
    return ResponseSchemaModel(data=TenantRoleOut.model_validate(role))


@router.put("/{role_id}/permissions", summary="更新角色权限", dependencies=[DependsJwtAuth])
async def update_role_permissions(
    db: CurrentSession,
    role_id: str,
    body: TenantRolePermissionUpdate,
) -> ResponseModel:
    """更新角色权限"""
    await tenant_role_service.update_permissions(db, role_id, body.permission_ids)
    await db.commit()
    return ResponseModel()


@router.delete("/{role_id}", summary="删除角色", dependencies=[DependsJwtAuth])
async def delete_role(db: CurrentSession, role_id: str) -> ResponseModel:
    """删除角色"""
    await tenant_role_service.delete(db, role_id)
    await db.commit()
    return ResponseModel()
