"""Feedback CRUD"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.feedalyze.crud.base import TenantAwareCRUD
from backend.app.feedalyze.model.feedback import Feedback


class CRUDFeedback(TenantAwareCRUD[Feedback]):
    """反馈 CRUD"""

    async def get_unclustered(
        self,
        db: AsyncSession,
        tenant_id: str,
        limit: int = 100,
    ) -> list[Feedback]:
        """
        获取未聚类的反馈（topic_id 为 NULL）
        
        Args:
            db: 数据库会话
            tenant_id: 租户ID
            limit: 返回数量上限
        
        Returns:
            反馈列表
        """
        query = select(self.model).where(
            self.model.tenant_id == tenant_id,
            self.model.topic_id.is_(None),
            self.model.deleted_at.is_(None)
        ).limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def batch_update_topic(
        self,
        db: AsyncSession,
        tenant_id: str,
        feedback_ids: list[str],
        topic_id: str,
    ) -> int:
        """
        批量更新反馈的主题ID（用于聚类后批量关联）
        
        Args:
            db: 数据库会话
            tenant_id: 租户ID
            feedback_ids: 反馈ID列表
            topic_id: 主题ID
        
        Returns:
            更新的记录数量
        """
        from sqlalchemy import update

        stmt = (
            update(self.model)
            .where(
                self.model.id.in_(feedback_ids),
                self.model.tenant_id == tenant_id,
                self.model.deleted_at.is_(None)
            )
            .values(topic_id=topic_id)
        )

        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount

    async def update_embedding(
        self,
        db: AsyncSession,
        tenant_id: str,
        feedback_id: str,
        embedding: list[float],
    ) -> bool:
        """
        更新反馈的 embedding 缓存（写入 VECTOR 字段）

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            feedback_id: 反馈ID
            embedding: embedding 向量

        Returns:
            是否更新成功
        """
        from sqlalchemy import update

        # SQLAlchemy + pgvector 自动处理 list[float] <-> vector 转换
        stmt = (
            update(self.model)
            .where(
                self.model.id == feedback_id,
                self.model.tenant_id == tenant_id,
                self.model.deleted_at.is_(None)
            )
            .values(embedding=embedding)
        )

        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount > 0

    async def batch_update_embeddings(
        self,
        db: AsyncSession,
        tenant_id: str,
        feedback_embeddings: dict[str, list[float]],
    ) -> int:
        """
        批量更新反馈的 embedding 缓存（写入 VECTOR 字段）

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            feedback_embeddings: {feedback_id: embedding} 字典

        Returns:
            更新的记录数量
        """
        if not feedback_embeddings:
            return 0

        updated_count = 0

        # 批量获取反馈
        feedback_ids = list(feedback_embeddings.keys())
        query = select(self.model).where(
            self.model.id.in_(feedback_ids),
            self.model.tenant_id == tenant_id,
            self.model.deleted_at.is_(None)
        )
        result = await db.execute(query)
        feedbacks = result.scalars().all()

        # 更新每个反馈的 embedding
        for feedback in feedbacks:
            if feedback.id in feedback_embeddings:
                embedding = feedback_embeddings[feedback.id]
                
                # SQLAlchemy + pgvector 自动处理类型转换
                feedback.embedding = embedding
                
                updated_count += 1

        await db.commit()
        return updated_count

    def get_cached_embedding(self, feedback: Feedback) -> list[float] | None:
        """
        获取缓存的 embedding（从 VECTOR 字段）

        Args:
            feedback: 反馈实例

        Returns:
            embedding 向量，如果没有缓存则返回 None
        """
        # SQLAlchemy + pgvector 自动转换为 list[float]
        return feedback.embedding

    async def find_similar_feedbacks(
        self,
        db: AsyncSession,
        tenant_id: str,
        query_embedding: list[float],
        limit: int = 10,
        min_similarity: float = 0.7,
    ) -> list[tuple[Feedback, float]]:
        """
        使用 pgvector 查找相似的反馈（向量搜索）

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            query_embedding: 查询向量
            limit: 返回数量
            min_similarity: 最小相似度阈值（0-1）

        Returns:
            [(反馈, 相似度), ...] 按相似度从高到低排序
        """
        from sqlalchemy import text

        # pgvector 需要字符串格式：'[0.1,0.2,...]'
        # 这是 PostgreSQL 的 vector 类型输入格式
        embedding_str = str(query_embedding)

        # 使用 pgvector 余弦相似度搜索
        # <=> 是余弦距离操作符，1 - 余弦距离 = 余弦相似度
        query = text("""
            SELECT 
                id,
                1 - (embedding <=> :query_vector::vector) as similarity
            FROM feedbacks
            WHERE 
                tenant_id = :tenant_id
                AND embedding IS NOT NULL
                AND deleted_at IS NULL
                AND (1 - (embedding <=> :query_vector::vector)) >= :min_similarity
            ORDER BY embedding <=> :query_vector::vector
            LIMIT :limit
        """)

        result = await db.execute(
            query,
            {
                'tenant_id': tenant_id,
                'query_vector': embedding_str,
                'min_similarity': min_similarity,
                'limit': limit
            }
        )

        # 获取完整的反馈对象
        similar_feedbacks = []
        for row in result:
            feedback = await self.get_by_id(db, tenant_id, row.id)
            if feedback:
                similar_feedbacks.append((feedback, float(row.similarity)))

        return similar_feedbacks

    async def get_list_with_relations(
        self,
        db: AsyncSession,
        tenant_id: str,
        skip: int = 0,
        limit: int = 100,
        topic_id: str | None = None,
        customer_id: str | None = None,
        is_urgent: bool | None = None,
        has_topic: bool | None = None,
    ) -> list[dict]:
        """
        获取反馈列表（包含关联的客户名和主题标题）
        
        Args:
            db: 数据库会话
            tenant_id: 租户ID
            skip: 跳过数量
            limit: 返回数量
            topic_id: 过滤主题ID
            customer_id: 过滤客户ID
            is_urgent: 过滤紧急程度
            has_topic: 过滤是否已聚类
        
        Returns:
            反馈列表（包含 customer_name 和 topic_title）
        """
        from backend.app.feedalyze.model.customer import Customer
        from backend.app.feedalyze.model.topic import Topic
        from sqlalchemy.orm import aliased

        # 使用左连接查询
        CustomerAlias = aliased(Customer)
        TopicAlias = aliased(Topic)

        query = (
            select(
                self.model,
                CustomerAlias.name.label('customer_name'),
                TopicAlias.title.label('topic_title')
            )
            .outerjoin(CustomerAlias, self.model.customer_id == CustomerAlias.id)
            .outerjoin(TopicAlias, self.model.topic_id == TopicAlias.id)
            .where(
                self.model.tenant_id == tenant_id,
                self.model.deleted_at.is_(None)
            )
        )

        # 添加过滤条件
        if topic_id is not None:
            query = query.where(self.model.topic_id == topic_id)
        if customer_id is not None:
            query = query.where(self.model.customer_id == customer_id)
        if is_urgent is not None:
            query = query.where(self.model.is_urgent == is_urgent)
        if has_topic is not None:
            if has_topic:
                query = query.where(self.model.topic_id.is_not(None))
            else:
                query = query.where(self.model.topic_id.is_(None))

        query = query.offset(skip).limit(limit)

        result = await db.execute(query)
        rows = result.all()

        # 转换为字典列表
        feedback_list = []
        for row in rows:
            feedback_dict = {
                **{c.name: getattr(row[0], c.name) for c in row[0].__table__.columns},
                'customer_name': row.customer_name,
                'topic_title': row.topic_title
            }
            feedback_list.append(feedback_dict)

        return feedback_list


crud_feedback = CRUDFeedback(Feedback)
