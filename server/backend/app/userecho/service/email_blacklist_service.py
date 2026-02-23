"""邮箱黑名单服务层"""

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.userecho.crud.crud_email_blacklist import email_blacklist_dao
from backend.app.userecho.model.email_blacklist import EmailBlacklist
from backend.app.userecho.schema.email_blacklist import (
    EmailBlacklistCreateReq,
    EmailBlacklistUpdateReq,
)
from backend.common.exception.errors import ForbiddenError, NotFoundError
from backend.common.log import log
from backend.database.db import uuid4_str


class EmailBlacklistService:
    """邮箱黑名单服务"""

    async def add_blacklist(
        self, db: AsyncSession, req: EmailBlacklistCreateReq, added_by: int
    ) -> EmailBlacklist:
        """添加黑名单"""
        domain = req.domain.lower()

        # 检查是否已存在
        existing = await email_blacklist_dao.get_by_domain(db, domain)
        if existing:
            raise ForbiddenError(msg=f"域名 {domain} 已在黑名单中")

        blacklist = EmailBlacklist(
            id=uuid4_str(),
            domain=domain,
            type=req.type,
            reason=req.reason,
            added_by=added_by,
            is_active=True,
        )

        blacklist = await email_blacklist_dao.create(db, blacklist)
        log.info(f"Added email blacklist: domain={domain}, type={req.type}, added_by={added_by}")

        return blacklist

    async def update_blacklist(
        self, db: AsyncSession, blacklist_id: str, req: EmailBlacklistUpdateReq
    ) -> EmailBlacklist:
        """更新黑名单"""
        blacklist = await email_blacklist_dao.get(db, blacklist_id)
        if not blacklist:
            raise NotFoundError(msg="黑名单记录不存在")

        update_data = {
            "is_active": req.is_active,
        }
        if req.reason is not None:
            update_data["reason"] = req.reason

        blacklist = await email_blacklist_dao.update(db, blacklist, update_data)
        log.info(f"Updated email blacklist: id={blacklist_id}, is_active={req.is_active}")

        return blacklist

    async def delete_blacklist(self, db: AsyncSession, blacklist_id: str) -> bool:
        """删除黑名单"""
        success = await email_blacklist_dao.delete(db, blacklist_id)
        if success:
            log.info(f"Deleted email blacklist: id={blacklist_id}")
        return success

    async def get_blacklist_list(
        self,
        db: AsyncSession,
        type: str | None = None,
        is_active: bool | None = None,
        page: int = 1,
        size: int = 100,
    ) -> tuple[list[EmailBlacklist], int]:
        """获取黑名单列表"""
        skip = (page - 1) * size
        return await email_blacklist_dao.get_list(db, type, is_active, skip, size)

    async def is_email_blocked(self, db: AsyncSession, email: str) -> bool:
        """检查邮箱是否被封禁"""
        domain = email.split("@")[1].lower()
        return await email_blacklist_dao.is_blocked(db, domain)


email_blacklist_service = EmailBlacklistService()
