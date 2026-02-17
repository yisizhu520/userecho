"""引导流程服务

负责新用户创建租户和看板的引导流程业务逻辑
"""

import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.userecho.model.board import Board
from backend.app.userecho.model.tenant import Tenant
from backend.app.userecho.model.tenant_user import TenantUser
from backend.app.userecho.schema.onboarding import (
    CreateBoardOut,
    CreateBoardParam,
    CreateTenantOut,
    CreateTenantParam,
    OnboardingCompleteOut,
    OnboardingStatusOut,
    SlugCheckOut,
)
from backend.common.log import log
from backend.database.db import uuid4_str


class OnboardingService:
    """引导流程服务"""

    async def get_onboarding_status(
        self,
        db: AsyncSession,
        user_id: int,
    ) -> OnboardingStatusOut:
        """
        获取用户的引导状态

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            引导状态信息
        """
        # 检查用户是否有关联的租户
        stmt = select(TenantUser).where(TenantUser.user_id == user_id, TenantUser.status == 'active')
        result = await db.execute(stmt)
        tenant_user = result.scalar_one_or_none()

        if tenant_user:
            # 用户已有租户，检查是否有看板
            board_stmt = select(Board).where(
                Board.tenant_id == tenant_user.tenant_id,
                Board.is_archived == False,  # noqa: E712
            )
            board_result = await db.execute(board_stmt)
            board = board_result.scalar_one_or_none()

            if board:
                # 已完成所有步骤
                return OnboardingStatusOut(
                    needs_onboarding=False,
                    current_step=None,
                    tenant_id=tenant_user.tenant_id,
                    board_id=board.id,
                    completed_steps=['create-tenant', 'create-board', 'complete'],
                )
            # 有租户但没有看板
            return OnboardingStatusOut(
                needs_onboarding=True,
                current_step='create-board',
                tenant_id=tenant_user.tenant_id,
                board_id=None,
                completed_steps=['create-tenant'],
            )
        # 没有租户，需要从头开始
        return OnboardingStatusOut(
            needs_onboarding=True, current_step='create-tenant', tenant_id=None, board_id=None, completed_steps=[]
        )

    async def check_slug_available(
        self,
        db: AsyncSession,
        slug: str,
    ) -> SlugCheckOut:
        """
        检查 slug 是否可用

        Args:
            db: 数据库会话
            slug: 要检查的 slug

        Returns:
            可用性信息和建议
        """
        # 查询是否已存在
        stmt = select(Tenant).where(Tenant.slug == slug)
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is None:
            return SlugCheckOut(slug=slug, available=True, suggestion=None)

        # 生成建议的替代 slug
        suggestion = await self._generate_unique_slug(db, slug)
        return SlugCheckOut(slug=slug, available=False, suggestion=suggestion)

    async def _generate_unique_slug(
        self,
        db: AsyncSession,
        base_slug: str,
    ) -> str:
        """
        生成唯一的 slug

        Args:
            db: 数据库会话
            base_slug: 基础 slug

        Returns:
            唯一的 slug
        """
        counter = 1
        while True:
            new_slug = f'{base_slug}-{counter}'
            stmt = select(Tenant).where(Tenant.slug == new_slug)
            result = await db.execute(stmt)
            if result.scalar_one_or_none() is None:
                return new_slug
            counter += 1
            if counter > 100:
                # 防止无限循环
                return f'{base_slug}-{uuid4_str()[:8]}'

    def generate_slug_from_name(self, name: str) -> str:
        """
        从名称生成 slug

        Args:
            name: 公司/团队名称

        Returns:
            生成的 slug
        """
        # 转换为小写
        slug = name.lower()

        # 替换中文字符为拼音（简化处理，只去除中文）
        slug = re.sub(r'[\u4e00-\u9fff]+', '', slug)

        # 替换空格和特殊字符为连字符
        slug = re.sub(r'[^a-z0-9]+', '-', slug)

        # 去除开头和结尾的连字符
        slug = slug.strip('-')

        # 如果为空，生成一个随机的
        if not slug:
            slug = f'team-{uuid4_str()[:8]}'

        return slug[:100]  # 限制长度

    async def create_tenant(
        self,
        db: AsyncSession,
        user_id: int,
        data: CreateTenantParam,
    ) -> CreateTenantOut:
        """
        创建租户

        Args:
            db: 数据库会话
            user_id: 创建者用户ID
            data: 租户创建参数

        Returns:
            创建的租户信息
        """
        # 检查 slug 是否可用
        slug_check = await self.check_slug_available(db, data.slug)
        if not slug_check.available:
            raise ValueError(f'URL标识 "{data.slug}" 已被使用，建议使用: {slug_check.suggestion}')

        # 检查用户是否已有租户
        stmt = select(TenantUser).where(TenantUser.user_id == user_id, TenantUser.status == 'active')
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            raise ValueError('您已经属于一个团队，无法再创建新团队')

        try:
            # 创建租户
            tenant = Tenant(id=uuid4_str(), name=data.name, slug=data.slug, status='active')
            db.add(tenant)
            await db.flush()

            # 创建 TenantUser 关联（设为 admin）
            tenant_user = TenantUser(
                id=uuid4_str(), tenant_id=tenant.id, user_id=user_id, user_type='admin', status='active'
            )
            db.add(tenant_user)
            await db.flush()

            log.info(f'Created tenant "{data.name}" (slug={data.slug}) for user {user_id}')

            return CreateTenantOut(id=tenant.id, name=tenant.name, slug=tenant.slug, created_time=tenant.created_time)

        except Exception as e:
            log.error(f'Failed to create tenant for user {user_id}: {e}')
            raise

    async def create_board(
        self,
        db: AsyncSession,
        user_id: int,
        data: CreateBoardParam,
    ) -> CreateBoardOut:
        """
        创建看板

        Args:
            db: 数据库会话
            user_id: 创建者用户ID
            data: 看板创建参数

        Returns:
            创建的看板信息
        """
        # 获取用户的租户
        stmt = select(TenantUser).where(TenantUser.user_id == user_id, TenantUser.status == 'active')
        result = await db.execute(stmt)
        tenant_user = result.scalar_one_or_none()

        if not tenant_user:
            raise ValueError('请先创建团队')

        # 生成 url_name
        url_name = self._generate_url_name(data.name)

        # 检查 url_name 在租户内是否唯一
        url_name = await self._ensure_unique_url_name(db, tenant_user.tenant_id, url_name)

        try:
            # 创建看板
            board = Board(
                id=uuid4_str(),
                tenant_id=tenant_user.tenant_id,
                name=data.name,
                url_name=url_name,
                description=data.description,
                access_mode=data.access_mode,
                is_archived=False,
            )
            db.add(board)
            await db.flush()

            log.info(f'Created board "{data.name}" for tenant {tenant_user.tenant_id}')

            return CreateBoardOut(
                id=board.id,
                tenant_id=board.tenant_id,
                name=board.name,
                url_name=board.url_name,
                description=board.description,
                access_mode=board.access_mode,
                created_time=board.created_time,
            )

        except Exception as e:
            log.error(f'Failed to create board for user {user_id}: {e}')
            raise

    def _generate_url_name(self, name: str) -> str:
        """
        从名称生成 URL name

        Args:
            name: 看板名称

        Returns:
            生成的 url_name
        """
        # 转换为小写
        url_name = name.lower()

        # 替换中文字符
        url_name = re.sub(r'[\u4e00-\u9fff]+', '', url_name)

        # 替换空格和特殊字符为连字符
        url_name = re.sub(r'[^a-z0-9]+', '-', url_name)

        # 去除开头和结尾的连字符
        url_name = url_name.strip('-')

        # 如果为空，使用默认值
        if not url_name:
            url_name = 'board'

        return url_name[:100]

    async def _ensure_unique_url_name(
        self,
        db: AsyncSession,
        tenant_id: str,
        url_name: str,
    ) -> str:
        """
        确保 url_name 在租户内唯一

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            url_name: 要检查的 url_name

        Returns:
            唯一的 url_name
        """
        original = url_name
        counter = 1

        while True:
            stmt = select(Board).where(Board.tenant_id == tenant_id, Board.url_name == url_name)
            result = await db.execute(stmt)
            if result.scalar_one_or_none() is None:
                return url_name
            url_name = f'{original}-{counter}'
            counter += 1
            if counter > 100:
                return f'{original}-{uuid4_str()[:8]}'

    async def complete_onboarding(
        self,
        db: AsyncSession,
        user_id: int,
    ) -> OnboardingCompleteOut:
        """
        完成引导流程

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            完成信息
        """
        # 获取用户的租户和看板
        stmt = select(TenantUser).where(TenantUser.user_id == user_id, TenantUser.status == 'active')
        result = await db.execute(stmt)
        tenant_user = result.scalar_one_or_none()

        if not tenant_user:
            raise ValueError('请先创建团队')

        # 检查是否有看板
        board_stmt = select(Board).where(
            Board.tenant_id == tenant_user.tenant_id,
            Board.is_archived == False,  # noqa: E712
        )
        board_result = await db.execute(board_stmt)
        board = board_result.scalar_one_or_none()

        if not board:
            raise ValueError('请先创建看板')

        log.info(f'User {user_id} completed onboarding for tenant {tenant_user.tenant_id}')

        return OnboardingCompleteOut(
            success=True, tenant_id=tenant_user.tenant_id, board_id=board.id, redirect_path='/dashboard'
        )


onboarding_service = OnboardingService()
