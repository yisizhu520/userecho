"""邮箱验证 CRUD"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.userecho.model.email_verification import EmailVerification
from backend.utils.timezone import timezone


class CRUDEmailVerification:
    """邮箱验证 CRUD"""

    async def get(self, db: AsyncSession, verification_id: str) -> EmailVerification | None:
        """根据ID获取验证记录"""
        query = select(EmailVerification).where(EmailVerification.id == verification_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_code(self, db: AsyncSession, verification_code: str) -> EmailVerification | None:
        """根据验证码获取记录"""
        query = select(EmailVerification).where(EmailVerification.verification_code == verification_code)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_user(self, db: AsyncSession, user_id: int, is_verified: bool = False) -> EmailVerification | None:
        """获取用户的验证记录"""
        query = select(EmailVerification).where(
            EmailVerification.user_id == user_id, EmailVerification.is_verified.is_(is_verified)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, obj_in: EmailVerification) -> EmailVerification:
        """创建验证记录"""
        db.add(obj_in)
        await db.flush()
        await db.refresh(obj_in)
        return obj_in

    async def update(self, db: AsyncSession, db_obj: EmailVerification, obj_in: dict) -> EmailVerification:
        """更新验证记录"""
        for field, value in obj_in.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        db_obj.updated_at = timezone.now()
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def mark_verified(self, db: AsyncSession, verification_id: str) -> EmailVerification | None:
        """标记为已验证"""
        verification = await self.get(db, verification_id)
        if verification:
            verification.is_verified = True
            verification.verified_at = timezone.now()
            verification.updated_at = timezone.now()
            await db.flush()
            await db.refresh(verification)
        return verification

    async def increment_send_count(self, db: AsyncSession, verification_id: str) -> EmailVerification | None:
        """增加发送次数"""
        verification = await self.get(db, verification_id)
        if verification:
            verification.send_count += 1
            verification.last_sent_at = timezone.now()
            verification.updated_at = timezone.now()
            await db.flush()
            await db.refresh(verification)
        return verification

    async def delete_by_user(self, db: AsyncSession, user_id: int, is_verified: bool = False) -> bool:
        """删除用户的未验证记录（创建新验证前）"""
        query = select(EmailVerification).where(
            EmailVerification.user_id == user_id, EmailVerification.is_verified.is_(is_verified)
        )
        result = await db.execute(query)
        verifications = result.scalars().all()

        if verifications:
            for verification in verifications:
                await db.delete(verification)
            await db.flush()
            return True
        return False


email_verification_dao = CRUDEmailVerification()
