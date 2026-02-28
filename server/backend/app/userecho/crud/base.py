"""多租户感知 CRUD 基类

提供自动租户过滤和软删除支持的 CRUD 基类
"""

from datetime import datetime
from typing import Any, Generic, Protocol, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.db import uuid4_str


class TenantAwareModel(Protocol):
    """多租户模型协议"""

    id: Any
    tenant_id: str
    deleted_at: datetime | None


ModelType = TypeVar("ModelType", bound=TenantAwareModel)


class TenantAwareCRUD(Generic[ModelType]):
    """多租户 CRUD 基类 - 所有查询自动过滤租户和软删除"""

    def __init__(self, model: type[ModelType]) -> None:
        """
        初始化 CRUD 基类

        Args:
            model: SQLAlchemy 模型类
        """
        self.model = model

    async def get_multi(
        self,
        db: AsyncSession,
        tenant_id: str,
        skip: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> list[ModelType]:
        """
        获取列表（自动过滤租户和软删除）

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            skip: 跳过数量
            limit: 返回数量
            **filters: 额外过滤条件

        Returns:
            模型列表
        """
        query = select(self.model).where(
            self.model.tenant_id == tenant_id,
            self.model.deleted_at.is_(None),  # 软删除过滤
        )

        # 添加额外过滤条件
        for key, value in filters.items():
            if value is not None and hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)

        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_by_id(
        self,
        db: AsyncSession,
        tenant_id: str,
        id: str,
    ) -> ModelType | None:
        """
        根据ID获取单条记录

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            id: 记录ID

        Returns:
            模型实例或 None
        """
        query = select(self.model).where(
            self.model.id == id, self.model.tenant_id == tenant_id, self.model.deleted_at.is_(None)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def create(
        self,
        db: AsyncSession,
        tenant_id: str,
        **data: Any,
    ) -> ModelType:
        """
        创建记录（自动注入 tenant_id）

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            **data: 模型字段数据

        Returns:
            创建的模型实例
        """
        from backend.utils.timezone import timezone

        # 自动注入租户ID和UUID主键
        obj_data = {"id": uuid4_str(), "tenant_id": tenant_id, **data}
        obj = self.model(**obj_data)

        # 手动注入时间字段（如果模型支持且未提供）
        now = timezone.now()
        if hasattr(obj, "created_time") and getattr(obj, "created_time") is None:
            obj.created_time = now
        if hasattr(obj, "updated_time") and getattr(obj, "updated_time") is None:
            obj.updated_time = now

        db.add(obj)
        # ❌ 禁止手动 commit 和 refresh (由 get_db 自动管理事务)
        return obj

    async def update(
        self,
        db: AsyncSession,
        tenant_id: str,
        id: str,
        **data: Any,
    ) -> ModelType | None:
        """
        更新记录

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            id: 记录ID
            **data: 更新字段数据

        Returns:
            更新后的模型实例或 None
        """
        obj = await self.get_by_id(db, tenant_id, id)
        if not obj:
            return None

        # 更新字段
        for key, value in data.items():
            if value is not None and hasattr(obj, key):
                setattr(obj, key, value)

        # 手动更新时间字段
        if hasattr(obj, "updated_time"):
            from backend.utils.timezone import timezone

            obj.updated_time = timezone.now()

        # ❌ 禁止手动 commit 和 refresh (由 get_db 自动管理事务)
        return obj

    async def delete(
        self,
        db: AsyncSession,
        tenant_id: str,
        id: str,
        soft: bool = True,
    ) -> bool:
        """
        删除记录（默认软删除）

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            id: 记录ID
            soft: 是否软删除（True=软删除，False=物理删除）

        Returns:
            是否删除成功
        """
        obj = await self.get_by_id(db, tenant_id, id)
        if not obj:
            return False

        if soft:
            # 软删除：设置 deleted_at
            from backend.utils.timezone import timezone

            obj.deleted_at = timezone.now()
        else:
            # 物理删除
            await db.delete(obj)

        # ❌ 禁止手动 commit (由 get_db 自动管理事务)
        return True

    async def count(
        self,
        db: AsyncSession,
        tenant_id: str,
        **filters: Any,
    ) -> int:
        """
        统计记录数量

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            **filters: 过滤条件

        Returns:
            记录数量
        """
        from sqlalchemy import func

        query = select(func.count(self.model.id)).where(
            self.model.tenant_id == tenant_id, self.model.deleted_at.is_(None)
        )

        for key, value in filters.items():
            if value is not None and hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)

        result = await db.execute(query)
        return result.scalar_one()
