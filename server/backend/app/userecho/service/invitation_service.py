"""邀请服务层"""

import secrets
from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.userecho.crud.crud_invitation import invitation_dao
from backend.app.userecho.crud.crud_invitation_usage import invitation_usage_dao
from backend.app.userecho.model.invitation import Invitation
from backend.app.userecho.schema.invitation import InvitationCreateReq, InvitationUpdateReq
from backend.common.exception.errors import NotFoundError
from backend.common.log import log
from backend.core.conf import settings
from backend.utils.timezone import timezone


class InvitationService:
    """邀请管理服务"""

    def generate_token(self) -> str:
        """生成 URL 安全的邀请 token"""
        return secrets.token_urlsafe(24)  # 32 个字符

    def get_invitation_urls(self, token: str) -> tuple[str, str, str]:
        """
        生成邀请相关的所有 URL

        Args:
            token: 邀请 token

        Returns:
            tuple: (url, short_url, qr_code_url)
        """
        base_url = settings.FRONTEND_URL or "http://localhost:5173"
        backend_url = settings.BACKEND_URL or "http://127.0.0.1:8000"

        url = f"{base_url}/register?invite={token}"
        short_url = f"{base_url}/i/{token[:8]}"
        qr_code_url = f"{backend_url}/api/v1/invitations/{token}/qrcode"

        return url, short_url, qr_code_url

    async def create_invitation(
        self, db: AsyncSession, creator_id: int, req: InvitationCreateReq
    ) -> tuple[Invitation, str, str, str]:
        """
        创建邀请

        Returns:
            tuple: (invitation, url, short_url, qr_code_url)
        """
        token = self.generate_token()
        expires_at = timezone.now() + timedelta(days=req.expires_days)

        invitation = Invitation(
            token=token,
            usage_limit=req.usage_limit,
            used_count=0,
            expires_at=expires_at,
            plan_code=req.plan_code,
            trial_days=req.trial_days,
            source=req.source,
            campaign=req.campaign,
            creator_id=creator_id,
            notes=req.notes,
            status="active",
        )

        invitation = await invitation_dao.create(db, invitation)

        # 生成所有 URL
        url, short_url, qr_code_url = self.get_invitation_urls(token)

        log.info(f"Created invitation: id={invitation.id}, token={token[:8]}..., creator={creator_id}")

        return invitation, url, short_url, qr_code_url

    async def validate_invitation(self, db: AsyncSession, token: str) -> tuple[bool, Invitation | None, str | None]:
        """
        验证邀请有效性

        Returns:
            tuple: (is_valid, invitation, error_code)
        """
        invitation = await invitation_dao.get_by_token(db, token)

        if not invitation:
            return False, None, "invitation_not_found"

        if invitation.status != "active":
            return False, invitation, "invitation_disabled"

        now = timezone.now()
        if invitation.expires_at < now:
            # 自动标记为过期
            await invitation_dao.update(db, invitation, {"status": "expired"})
            return False, invitation, "invitation_expired"

        if invitation.used_count >= invitation.usage_limit:
            return False, invitation, "invitation_exhausted"

        return True, invitation, None

    async def get_invitation_detail(self, db: AsyncSession, invitation_id: str) -> Invitation:
        """获取邀请详情"""
        invitation = await invitation_dao.get(db, invitation_id)
        if not invitation:
            raise NotFoundError(msg="邀请不存在")
        return invitation

    async def get_invitation_list(
        self,
        db: AsyncSession,
        status: str | None = None,
        source: str | None = None,
        campaign: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[Invitation], int]:
        """获取邀请列表"""
        skip = (page - 1) * size
        return await invitation_dao.get_list(db, status, source, campaign, skip, size)

    async def update_invitation(self, db: AsyncSession, invitation_id: str, req: InvitationUpdateReq) -> Invitation:
        """更新邀请"""
        invitation = await self.get_invitation_detail(db, invitation_id)

        update_data = {}
        if req.status is not None:
            update_data["status"] = req.status
        if req.usage_limit is not None:
            update_data["usage_limit"] = req.usage_limit
        if req.expires_at is not None:
            update_data["expires_at"] = req.expires_at
        if req.notes is not None:
            update_data["notes"] = req.notes

        invitation = await invitation_dao.update(db, invitation, update_data)
        log.info(f"Updated invitation: id={invitation_id}, changes={list(update_data.keys())}")

        return invitation

    async def delete_invitation(self, db: AsyncSession, invitation_id: str) -> bool:
        """删除邀请（软删除）"""
        success = await invitation_dao.delete(db, invitation_id)
        if success:
            log.info(f"Deleted (disabled) invitation: id={invitation_id}")
        return success

    async def get_invitation_usage_records(
        self, db: AsyncSession, invitation_id: str, page: int = 1, size: int = 20
    ) -> tuple[list, int, dict]:
        """
        获取邀请使用详情

        Returns:
            tuple: (usage_records, total, statistics)
        """
        await self.get_invitation_detail(db, invitation_id)

        # 获取使用记录
        skip = (page - 1) * size
        usage_records, total = await invitation_usage_dao.get_by_invitation(db, invitation_id, skip, size)

        # 统计数据
        completed_count = sum(1 for record in usage_records if record.completed_onboarding)
        conversion_rate = completed_count / total if total > 0 else 0

        statistics = {
            "total_used": total,
            "completed_onboarding": completed_count,
            "conversion_rate": round(conversion_rate, 2),
        }

        return usage_records, total, statistics


invitation_service = InvitationService()
