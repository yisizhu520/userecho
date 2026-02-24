"""邮箱验证服务层"""

import secrets
from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.userecho.crud.crud_email_verification import email_verification_dao
from backend.app.userecho.model.email_verification import EmailVerification
from backend.common.log import log
from backend.core.conf import settings
from backend.database.db import uuid4_str
from backend.plugin.email.utils.send import send_email
from backend.utils.timezone import timezone


class EmailVerificationService:
    """邮箱验证服务"""

    def generate_verification_code(self) -> str:
        """生成验证码"""
        return secrets.token_urlsafe(32)

    async def create_verification(
        self,
        db: AsyncSession,
        user_id: int,
        email: str,
        nickname: str = "",
        plan_name: str = "专业版",
        trial_days: int = 90,
    ) -> EmailVerification:
        """
        创建邮箱验证记录

        如果用户已有未验证记录，先删除再创建新的
        """
        # 删除旧的未验证记录
        await email_verification_dao.delete_by_user(db, user_id, is_verified=False)

        # 创建新记录
        verification_code = self.generate_verification_code()
        expires_at = timezone.now() + timedelta(hours=24)

        verification = EmailVerification(
            id=uuid4_str(),
            user_id=user_id,
            email=email,
            verification_code=verification_code,
            expires_at=expires_at,
            is_verified=False,
            send_count=1,
        )

        verification = await email_verification_dao.create(db, verification)
        log.info(f"Created email verification: user_id={user_id}, email={email}")

        # 发送验证邮件
        await self._send_verification_email(db, email, verification_code, nickname, plan_name, trial_days)

        return verification

    async def verify_email(self, db: AsyncSession, user_id: int, verification_code: str) -> tuple[bool, str]:
        """
        验证邮箱

        Returns:
            tuple: (success, message)
        """
        verification = await email_verification_dao.get_by_code(db, verification_code)

        if not verification or verification.user_id != user_id:
            return False, "验证码无效"

        if verification.is_verified:
            return False, "该验证码已使用"

        now = timezone.now()
        if verification.expires_at < now:
            return False, "验证码已过期"

        # 标记为已验证
        await email_verification_dao.mark_verified(db, verification.id)
        log.info(f"Email verified: user_id={user_id}, email={verification.email}")

        return True, "邮箱验证成功"

    async def can_resend(self, db: AsyncSession, user_id: int) -> tuple[bool, int]:
        """
        检查是否可以重新发送验证邮件

        Returns:
            tuple: (can_resend, retry_after_seconds)
        """
        verification = await email_verification_dao.get_by_user(db, user_id, is_verified=False)

        if not verification:
            return True, 0

        # 检查是否在 1 分钟内
        now = timezone.now()
        elapsed = (now - verification.last_sent_at).total_seconds()

        if elapsed < 60:
            retry_after = int(60 - elapsed)
            return False, retry_after

        return True, 0

    async def resend_verification(
        self, db: AsyncSession, user_id: int, email: str
    ) -> tuple[bool, str, EmailVerification | None]:
        """
        重新发送验证邮件

        Returns:
            tuple: (success, message, verification)
        """
        can_resend, retry_after = await self.can_resend(db, user_id)

        if not can_resend:
            return False, f"请在 {retry_after} 秒后重试", None

        # 获取现有验证记录
        verification = await email_verification_dao.get_by_user(db, user_id, is_verified=False)

        if verification:
            # 更新发送次数和时间
            await email_verification_dao.increment_send_count(db, verification.id)
            log.info(f"Resent verification email: user_id={user_id}, count={verification.send_count + 1}")
            # 刷新对象
            verification = await email_verification_dao.get(db, verification.id)
        else:
            # 创建新的验证记录
            verification = await self.create_verification(db, user_id, email)

        # 重新发送邮件
        if verification:
            await self._send_verification_email(db, email, verification.verification_code, "", "", 0)

        return True, "验证邮件已发送", verification

    async def _send_verification_email(
        self,
        db: AsyncSession,
        email: str,
        verification_code: str,
        nickname: str = "",
        plan_name: str = "专业版",
        trial_days: int = 90,
    ) -> None:
        """
        发送验证邮件（内部方法）
        """
        try:
            # 构建验证链接
            verify_url = f"{settings.FRONTEND_URL}/auth/verify-email?code={verification_code}"

            # 发送邮件
            await send_email(
                db,
                recipients=email,
                subject="验证邮箱 - 回响 UserEcho",
                content={
                    "nickname": nickname or "用户",
                    "code": verification_code,
                    "verify_url": verify_url,
                    "plan_name": plan_name or "专业版",
                    "trial_days": trial_days or 90,
                },
                template="email_verification.html",
            )
            log.info(f"Verification email sent to: {email}")
        except Exception as e:
            log.error(f"Failed to send verification email to {email}: {e}")
            # 不抛出异常，允许用户手动重发


email_verification_service = EmailVerificationService()
