"""Tenant CRUD"""
from backend.app.feedalyze.crud.base import TenantAwareCRUD
from backend.app.feedalyze.model.tenant import Tenant


class CRUDTenant(TenantAwareCRUD[Tenant]):
    """租户 CRUD（租户自身不需要租户过滤，但继承基类以保持一致性）"""
    pass


crud_tenant = CRUDTenant(Tenant)
