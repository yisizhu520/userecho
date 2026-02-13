"""客户服务

负责客户的 CRUD 和业务逻辑
"""

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.userecho.crud import crud_customer
from backend.app.userecho.schema.customer import CustomerCreate, CustomerUpdate
from backend.common.log import log
from backend.database.db import uuid4_str


class CustomerService:
    """客户服务"""

    async def create_customer(
        self,
        db: AsyncSession,
        tenant_id: str,
        data: CustomerCreate,
    ):
        """
        创建客户

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            data: 客户创建数据

        Returns:
            创建的客户实例
        """
        try:
            return await crud_customer.create(
                db=db,
                tenant_id=tenant_id,
                id=uuid4_str(),
                name=data.name,
                customer_type=data.customer_type,
                business_value=data.business_value
            )

        except Exception as e:
            log.error(f'Failed to create customer "{data.name}" for tenant {tenant_id}: {e}')
            raise

    async def update_customer(
        self,
        db: AsyncSession,
        tenant_id: str,
        customer_id: str,
        data: CustomerUpdate,
    ):
        """
        更新客户

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            customer_id: 客户ID
            data: 更新数据

        Returns:
            更新后的客户实例
        """
        update_dict = data.model_dump(exclude_unset=True)
        return await crud_customer.update(
            db=db,
            tenant_id=tenant_id,
            id=customer_id,
            **update_dict
        )

    async def get_list(
        self,
        db: AsyncSession,
        tenant_id: str,
        skip: int = 0,
        limit: int = 100,
    ):
        """
        获取客户列表

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            skip: 跳过数量
            limit: 返回数量

        Returns:
            客户列表
        """
        return await crud_customer.get_multi(
            db=db,
            tenant_id=tenant_id,
            skip=skip,
            limit=limit
        )

    async def delete_customer(
        self,
        db: AsyncSession,
        tenant_id: str,
        customer_id: str,
    ) -> bool:
        """
        删除客户（软删除）

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            customer_id: 客户ID

        Returns:
            是否成功
        """
        return await crud_customer.delete(
            db=db,
            tenant_id=tenant_id,
            id=customer_id,
            soft=True
        )


customer_service = CustomerService()
