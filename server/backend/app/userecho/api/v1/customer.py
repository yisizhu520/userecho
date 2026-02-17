"""客户 API 端点"""

from fastapi import APIRouter

from backend.app.userecho.schema.customer import CustomerCreate, CustomerUpdate
from backend.app.userecho.service import customer_service
from backend.common.response.response_code import CustomResponse
from backend.common.response.response_schema import response_base
from backend.common.security.jwt import CurrentTenantId
from backend.database.db import CurrentSession

router = APIRouter(prefix='/customers', tags=['UserEcho - 客户管理'])


@router.get('', summary='获取客户列表')
async def get_customers(
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
    skip: int = 0,
    limit: int = 100,
):
    """获取客户列表"""
    customers = await customer_service.get_list(db=db, tenant_id=tenant_id, skip=skip, limit=limit)
    return response_base.success(data=customers)


@router.post('', summary='创建客户')
async def create_customer(
    data: CustomerCreate,
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
):
    """
    创建客户

    - **name**: 客户名称
    - **customer_type**: 客户类型 (normal/paid/major/strategic)
    - **business_value**: 商业价值权重 (1-10)
    """
    customer = await customer_service.create_customer(db=db, tenant_id=tenant_id, data=data)
    return response_base.success(data=customer)


@router.put('/{customer_id}', summary='更新客户')
async def update_customer(
    customer_id: str,
    data: CustomerUpdate,
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
):
    """更新客户"""
    customer = await customer_service.update_customer(db=db, tenant_id=tenant_id, customer_id=customer_id, data=data)
    if not customer:
        return response_base.fail(res=CustomResponse(code=400, msg='客户不存在'))
    return response_base.success(data=customer)


@router.delete('/{customer_id}', summary='删除客户')
async def delete_customer(
    customer_id: str,
    db: CurrentSession,
    tenant_id: str = CurrentTenantId,
):
    """删除客户（软删除）"""
    success = await customer_service.delete_customer(db=db, tenant_id=tenant_id, customer_id=customer_id)
    if not success:
        return response_base.fail(res=CustomResponse(code=400, msg='客户不存在或已删除'))
    return response_base.success(res=CustomResponse(code=200, msg='删除成功'))
