"""反馈服务

负责反馈的 CRUD 和业务逻辑
"""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.feedalyze.crud import crud_feedback
from backend.app.feedalyze.schema.feedback import FeedbackCreate, FeedbackUpdate
from backend.common.log import log
from backend.database.db import uuid4_str
from backend.utils.ai_client import ai_client


class FeedbackService:
    """反馈服务"""

    async def create_with_ai_processing(
        self,
        db: AsyncSession,
        tenant_id: str,
        data: FeedbackCreate,
        generate_summary: bool = True,
    ):
        """
        创建反馈（自动生成 AI 摘要）

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            data: 反馈创建数据
            generate_summary: 是否生成 AI 摘要

        Returns:
            创建的反馈实例
        """
        try:
            # 生成 AI 摘要
            ai_summary = None
            if generate_summary and data.content:
                ai_summary = await ai_client.generate_summary(data.content, max_length=20)

            # 创建反馈
            feedback = await crud_feedback.create(
                db=db,
                tenant_id=tenant_id,
                id=uuid4_str(),
                customer_id=data.customer_id,
                anonymous_author=data.anonymous_author,
                anonymous_source=data.anonymous_source,
                content=data.content,
                source=data.source,
                is_urgent=data.is_urgent,
                ai_summary=ai_summary
            )

            return feedback

        except Exception as e:
            log.error(f'Failed to create feedback: {e}')
            raise

    async def get_list(
        self,
        db: AsyncSession,
        tenant_id: str,
        skip: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> list[dict]:
        """
        获取反馈列表（包含关联信息）

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            skip: 跳过数量
            limit: 返回数量
            **filters: 过滤条件

        Returns:
            反馈列表
        """
        return await crud_feedback.get_list_with_relations(
            db=db,
            tenant_id=tenant_id,
            skip=skip,
            limit=limit,
            **filters
        )

    async def update_feedback(
        self,
        db: AsyncSession,
        tenant_id: str,
        feedback_id: str,
        data: FeedbackUpdate,
    ):
        """
        更新反馈

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            feedback_id: 反馈ID
            data: 更新数据

        Returns:
            更新后的反馈实例
        """
        update_dict = data.model_dump(exclude_unset=True)
        return await crud_feedback.update(
            db=db,
            tenant_id=tenant_id,
            id=feedback_id,
            **update_dict
        )

    async def delete_feedback(
        self,
        db: AsyncSession,
        tenant_id: str,
        feedback_id: str,
    ) -> bool:
        """
        删除反馈（软删除）

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            feedback_id: 反馈ID

        Returns:
            是否成功
        """
        return await crud_feedback.delete(
            db=db,
            tenant_id=tenant_id,
            id=feedback_id,
            soft=True
        )


feedback_service = FeedbackService()
