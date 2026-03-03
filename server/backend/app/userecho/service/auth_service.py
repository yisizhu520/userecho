"""认证服务层（邀请注册）"""

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.crud.crud_user import user_dao
from backend.app.admin.model.user import User
from backend.app.admin.utils.password_security import get_hash_password
from backend.app.userecho.crud.crud_email_blacklist import email_blacklist_dao
from backend.app.userecho.crud.crud_invitation import invitation_dao
from backend.app.userecho.crud.crud_invitation_usage import invitation_usage_dao
from backend.app.userecho.crud.crud_subscription import (
    subscription_plan_dao,
    tenant_subscription_dao,
)
from backend.app.userecho.model.invitation import Invitation
from backend.app.userecho.model.invitation_usage import InvitationUsage
from backend.app.userecho.model.subscription import (
    SubscriptionAction,
    SubscriptionHistory,
    SubscriptionSource,
    SubscriptionStatus,
    TenantSubscription,
)
from backend.app.userecho.model.tenant_user import TenantUser
from backend.app.userecho.service.credits_service import credits_service
from backend.app.userecho.service.email_verification_service import (
    email_verification_service,
)
from backend.common.exception.errors import ForbiddenError
from backend.common.log import log
from backend.utils.timezone import timezone


class AuthService:
    """认证服务（邀请注册）"""

    async def register_with_invitation(
        self,
        db: AsyncSession,
        invitation_token: str,
        email: str,
        password: str,
        nickname: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> dict:
        """
        通过邀请码注册

        Returns:
            dict: 包含用户信息和下一步操作的字典

        Raises:
            ForbiddenError: 邀请无效、邮箱已注册、邮箱在黑名单等
        """
        # 1. 验证邀请有效性
        invitation = await self._validate_invitation(db, invitation_token)

        # 2. 检查邮箱黑名单
        email_domain = email.split("@")[1].lower()
        is_blocked = await email_blacklist_dao.is_blocked(db, email_domain)
        if is_blocked:
            log.warning(f"Registration blocked: email domain {email_domain} is blacklisted")
            raise ForbiddenError(msg=f"不支持该邮箱域名注册: {email_domain}")

        # 3. 检查邮箱是否已注册
        existing_user = await user_dao.get_by_email(db, email)
        if existing_user:
            log.warning(f"Registration failed: email {email} already exists")
            raise ForbiddenError(msg="该邮箱已被注册")

        # 4. 检查邮箱是否已被用于领取试用（防止换账号重复领取）
        existing_usage = await invitation_usage_dao.get_by_email(db, email)
        if existing_usage:
            log.warning(f"Registration failed: email {email} already used an invitation")
            raise ForbiddenError(msg="该邮箱已领取过试用订阅")

        # 5. 创建用户（email_verified=False）
        hashed_password = get_hash_password(password, salt=None)
        user = User(
            email=email,
            nickname=nickname,
            password=hashed_password,
            status=1,  # 正常状态
            email_verified=False,  # type: ignore
            invitation_id=invitation.id,  # type: ignore
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)

        # 6. 创建邮箱验证记录并发送验证邮件
        plan_name = "专业版" if invitation.plan_code == "pro" else "启航版"
        verification = await email_verification_service.create_verification(
            db, user.id, email, nickname, plan_name, invitation.trial_days
        )

        # 7. 记录邀请使用
        usage = InvitationUsage(
            invitation_id=invitation.id,
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            registered_email=email,
            completed_onboarding=False,
        )
        await invitation_usage_dao.create(db, usage)

        # 8. 更新邀请使用次数
        await invitation_dao.increment_usage(db, invitation.id)

        # 9. 记录日志
        log.info(
            f"User registered with invitation: user_id={user.id}, email={email}, invitation={invitation_token[:8]}..."
        )

        # TODO: 发送验证邮件（阶段6实现）

        return {
            "user": {
                "id": user.id,
                "email": user.email,
                "nickname": user.nickname,
                "email_verified": False,
            },
            "verification_code": verification.verification_code,  # 临时返回，后续通过邮件发送
            "verification_email_sent": False,  # 邮件服务实现后改为 True
            "next_step": "verify_email",
        }

    async def verify_email_and_activate_subscription(
        self, db: AsyncSession, user_id: int, verification_code: str
    ) -> dict:
        """
        验证邮箱并激活订阅

        核心流程：
        1. 验证 code 有效性
        2. 标记邮箱已验证
        3. 若用户已有租户，分配专业版试用订阅
        4. 若用户暂无租户，等待 onboarding 创建租户后再激活试用
        """
        # 1. 验证邮箱
        success, message = await email_verification_service.verify_email(db, user_id, verification_code)
        if not success:
            raise ForbiddenError(msg=message)

        # 2. 更新用户邮箱验证状态
        user = await user_dao.get(db, user_id)
        if not user:
            raise ForbiddenError(msg="用户不存在")

        await user_dao.update_model(db, user_id, {"email_verified": True})

        # 3. 获取邀请信息
        invitation_id = getattr(user, "invitation_id", None)
        if not invitation_id:
            log.warning(f"User {user_id} verified email but has no invitation")
            return {"verified": True, "message": "邮箱验证成功"}

        invitation = await invitation_dao.get(db, invitation_id)
        if not invitation:
            log.error(f"Invitation {invitation_id} not found for user {user_id}")
            return {"verified": True, "message": "邮箱验证成功"}

        # 4. 检查用户是否已有租户（通过 TenantUser 查询）
        stmt = select(TenantUser).where(TenantUser.user_id == user_id).limit(1)
        result = await db.execute(stmt)
        tenant_user = result.scalar_one_or_none()

        if not tenant_user:
            log.info(
                f"User {user_id} verified email without tenant, waiting onboarding to activate invitation subscription"
            )
            return {
                "verified": True,
                "message": "邮箱验证成功，请先完成团队创建",
                "tenant_id": None,
            }

        tenant_id = tenant_user.tenant_id
        await self._activate_invitation_subscription_for_tenant(db=db, tenant_id=tenant_id, invitation=invitation)

        return {
            "verified": True,
            "message": "邮箱验证成功，订阅已激活",
            "tenant_id": tenant_id,
        }

    async def activate_invitation_trial_for_tenant(self, db: AsyncSession, user_id: int, tenant_id: str) -> bool:
        """在 onboarding 创建租户后，按邀请信息激活试用订阅。"""
        user = await user_dao.get(db, user_id)
        if not user:
            return False

        invitation_id = getattr(user, "invitation_id", None)
        if not invitation_id:
            return False

        if not getattr(user, "email_verified", False):
            log.info(f"Skip invitation trial activation for user {user_id}: email not verified")
            return False

        invitation = await invitation_dao.get(db, invitation_id)
        if not invitation:
            log.warning(f"Skip invitation trial activation for user {user_id}: invitation {invitation_id} not found")
            return False

        await self._activate_invitation_subscription_for_tenant(db=db, tenant_id=tenant_id, invitation=invitation)
        return True

    async def _activate_invitation_subscription_for_tenant(
        self, db: AsyncSession, tenant_id: str, invitation: Invitation
    ) -> None:
        """按邀请配置为指定租户创建或更新试用订阅。"""
        plan = await subscription_plan_dao.get_by_code(db, invitation.plan_code)
        if not plan:
            log.error(f"Plan {invitation.plan_code} not found")
            raise ForbiddenError(msg="套餐配置错误，请联系管理员")

        existing_sub = await tenant_subscription_dao.get_by_tenant(db, tenant_id)

        if existing_sub:
            if existing_sub.status == SubscriptionStatus.TRIAL:
                new_expires = timezone.now() + timedelta(days=invitation.trial_days)
                await tenant_subscription_dao.update(
                    db, existing_sub, {"expires_at": new_expires, "trial_ends_at": new_expires}
                )
                log.info(f"Extended trial subscription for tenant {tenant_id}")
            else:
                log.warning(f"Tenant {tenant_id} already has active subscription")
            return

        expires_at = timezone.now() + timedelta(days=invitation.trial_days)
        subscription = TenantSubscription(
            tenant_id=tenant_id,
            plan_id=plan.id,
            status=SubscriptionStatus.TRIAL,
            started_at=timezone.now(),
            expires_at=expires_at,
            trial_ends_at=expires_at,
            source=SubscriptionSource.MANUAL,
            notes=f"通过邀请注册获得试用订阅（邀请ID: {invitation.id}）",
        )
        await tenant_subscription_dao.create(db, subscription)

        from backend.app.userecho.crud.crud_subscription import subscription_history_dao

        history = SubscriptionHistory(
            tenant_id=tenant_id,
            subscription_id=subscription.id,
            action=SubscriptionAction.CREATED,
            old_plan_code=None,
            new_plan_code=plan.code,
            changed_by=None,
            reason=f"Invitation registration: {invitation.token[:8]}...",
        )
        await subscription_history_dao.create(db, history)

        await credits_service.sync_subscription_plan(db, tenant_id, plan.code, plan.ai_credits_monthly)

        log.info(f"Created trial subscription for tenant {tenant_id}: {plan.code} for {invitation.trial_days} days")

    async def _validate_invitation(self, db: AsyncSession, token: str) -> Invitation:
        """验证邀请有效性"""
        invitation = await invitation_dao.get_by_token(db, token)

        if not invitation:
            raise ForbiddenError(msg="邀请不存在")

        if invitation.status != "active":
            raise ForbiddenError(msg="邀请已失效")

        now = timezone.now()
        if invitation.expires_at < now:
            # 自动标记为过期
            await invitation_dao.update(db, invitation, {"status": "expired"})
            raise ForbiddenError(msg="邀请已过期")

        if invitation.used_count >= invitation.usage_limit:
            raise ForbiddenError(msg="邀请使用次数已用完")

        return invitation


auth_service = AuthService()
