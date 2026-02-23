"""反馈服务

负责反馈的 CRUD 和业务逻辑
"""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.userecho.crud import crud_feedback
from backend.app.userecho.schema.feedback import FeedbackCreate, FeedbackUpdate
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
        submitter_id: int | None = None,
    ):
        """
        创建反馈（自动生成 AI 摘要）

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            data: 反馈创建数据
            generate_summary: 是否生成 AI 摘要
            submitter_id: 提交者用户ID

        Returns:
            创建的反馈实例
        """
        from backend.app.userecho.crud import crud_board, crud_customer
        from backend.utils.timezone import timezone

        try:
            # 1. 验证 Board 归属（board_id 必填）
            board = await crud_board.get_by_id(db, tenant_id, data.board_id)
            if not board:
                raise ValueError(f'Board {data.board_id} not found for tenant {tenant_id}')

            # 2. 根据 author_type 处理不同来源模式
            customer_id = None
            author_type = 'customer'
            external_user_name = None
            external_contact = None
            source_platform = None
            source_user_name = None

            if data.author_type == 'customer':
                # 内部客户模式：关联或创建客户
                customer_id = data.customer_id
                if data.customer_name and not customer_id:
                    from sqlalchemy import select

                    from backend.app.userecho.model.customer import Customer

                    query = select(Customer).where(
                        Customer.tenant_id == tenant_id,
                        Customer.name == data.customer_name,
                        Customer.deleted_at.is_(None),
                    )
                    result = await db.execute(query)
                    customer = result.scalar_one_or_none()

                    if not customer:
                        customer = await crud_customer.create(
                            db=db,
                            tenant_id=tenant_id,
                            id=uuid4_str(),
                            name=data.customer_name,
                            customer_type=data.customer_type or 'normal',
                        )
                        log.info(
                            f'Auto-created customer {customer.id} for feedback: {data.customer_name}, type={data.customer_type or "normal"}'
                        )

                    customer_id = customer.id
            else:
                # 外部用户模式：存储外部用户信息，不入客户表
                author_type = 'external'
                external_user_name = data.external_user_name
                external_contact = data.external_contact
                source_platform = data.source_platform
                source_user_name = data.external_user_name

            # 3. 处理截图（存储到 images_metadata）
            images_metadata = None
            if data.screenshots:
                images_metadata = {
                    'images': [{'url': url, 'uploaded_at': timezone.now().isoformat()} for url in data.screenshots]
                }

            # 4. 生成 AI 摘要（仅长文本，失败不影响创建）
            ai_summary = None
            if generate_summary and data.content and len(data.content) > 150:
                try:
                    ai_summary = await ai_client.generate_summary(data.content, max_length=20)
                except Exception as e:
                    log.warning(f'Failed to generate summary for feedback: {e}')

            # 5. 确定聚类状态
            clustering_status = 'clustered' if data.topic_id else 'pending'

            # 6. 创建反馈
            feedback = await crud_feedback.create(
                db=db,
                tenant_id=tenant_id,
                id=uuid4_str(),
                board_id=data.board_id,
                customer_id=customer_id,
                topic_id=data.topic_id,
                content=data.content,
                source=data.source,
                is_urgent=data.is_urgent,
                ai_summary=ai_summary,
                images_metadata=images_metadata,
                clustering_status=clustering_status,
                submitter_id=submitter_id,
                # 来源类型和外部用户字段
                author_type=author_type,
                external_user_name=external_user_name,
                external_contact=external_contact,
                source_platform=source_platform,
                source_user_name=source_user_name,
            )

            # 7. 异步生成 embedding（不阻塞响应）
            # 将 AI 能力潜移默化地赋能给用户，聚类时可直接使用缓存
            try:
                from backend.app.task.celery import celery_app

                celery_app.send_task(
                    'userecho.generate_feedback_embedding',
                    args=[feedback.id, data.content, tenant_id],
                )
            except Exception as e:
                # 失败不影响主流程
                log.warning(f'Failed to trigger embedding generation for feedback {feedback.id}: {e}')

            return feedback

        except Exception as e:
            log.error(f'Failed to create feedback for tenant {tenant_id}: {e}')
            raise

    async def get_list(
        self,
        db: AsyncSession,
        tenant_id: str,
        skip: int = 0,
        limit: int = 100,
        search_query: str | None = None,
        search_mode: str = 'keyword',
        **filters: Any,
    ) -> list[dict]:
        """
        获取反馈列表（支持关键词搜索和语义搜索）

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            skip: 跳过数量
            limit: 返回数量
            search_query: 搜索关键词
            search_mode: 搜索模式（'keyword' | 'semantic'）
            **filters: 其他过滤条件

        Returns:
            反馈列表
        """
        # 语义搜索模式
        if search_query and search_mode == 'semantic':
            # 1. 生成搜索词的 embedding
            query_embedding = await ai_client.get_embedding(search_query)
            if not query_embedding:
                log.warning(
                    f'Failed to generate embedding for search query: {search_query}, fallback to keyword search'
                )
                # Fallback 到关键词搜索
                search_mode = 'keyword'
            else:
                # 2. 使用 pgvector 语义搜索
                return await crud_feedback.search_by_semantic(
                    db=db, tenant_id=tenant_id, query_embedding=query_embedding, skip=skip, limit=limit, **filters
                )

        # 关键词搜索模式（默认）
        return await crud_feedback.get_list_with_relations(
            db=db,
            tenant_id=tenant_id,
            skip=skip,
            limit=limit,
            search_query=search_query if search_mode == 'keyword' else None,
            **filters,
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
        return await crud_feedback.update(db=db, tenant_id=tenant_id, id=feedback_id, **update_dict)

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
        return await crud_feedback.delete(db=db, tenant_id=tenant_id, id=feedback_id, soft=True)


feedback_service = FeedbackService()
