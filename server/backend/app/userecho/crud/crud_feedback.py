"""Feedback CRUD"""

import numpy as np

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.userecho.crud.base import TenantAwareCRUD
from backend.app.userecho.model.feedback import Feedback

_UNSET = object()


class CRUDFeedback(TenantAwareCRUD[Feedback]):
    """反馈 CRUD"""

    async def get_pending_clustering(
        self,
        db: AsyncSession,
        tenant_id: str,
        limit: int = 100,
        include_failed: bool = True,
        force_recluster: bool = False,
    ) -> list[Feedback]:
        """
        获取待聚类的反馈（避免 topic_id=NULL 的噪声点被反复聚类）

        规则：
        - 仅处理 topic_id IS NULL
        - clustering_status in (pending, failed?)
        """
        from backend.common.log import log

        statuses = ["pending"]
        if include_failed:
            statuses.append("failed")
        if force_recluster:
            # 仅针对 topic_id IS NULL 的反馈，允许重新跑（包括已 clustered 的噪声点）
            statuses.append("clustered")

        query = (
            select(self.model)
            .where(
                self.model.tenant_id == tenant_id,
                self.model.topic_id.is_(None),
                self.model.clustering_status.in_(statuses),
                self.model.deleted_at.is_(None),
            )
            .limit(limit)
        )

        log.debug(f"Query pending clustering: tenant={tenant_id}, statuses={statuses}, limit={limit}")
        result = await db.execute(query)
        feedbacks = list(result.scalars().all())
        log.debug(f"Found {len(feedbacks)} pending feedbacks")
        return feedbacks

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
        # 向后兼容：历史调用方仍然用 get_unclustered，但底层应避免反复处理噪声点
        return await self.get_pending_clustering(db=db, tenant_id=tenant_id, limit=limit, include_failed=True)

    async def batch_update_clustering(
        self,
        db: AsyncSession,
        tenant_id: str,
        feedback_ids: list[str],
        *,
        clustering_status: str,
        topic_id: str | None | object = _UNSET,
        clustering_metadata: dict | None | object = _UNSET,
    ) -> int:
        """
        批量更新聚类字段（支持同时更新 topic_id）

        注意：
        - topic_id / clustering_metadata 默认不更新（用 object 哨兵区分“传了 None”与“不传”）
        """
        from sqlalchemy import update

        if not feedback_ids:
            return 0

        values: dict = {"clustering_status": clustering_status}
        if topic_id is not _UNSET:
            values["topic_id"] = topic_id
        if clustering_metadata is not _UNSET:
            values["clustering_metadata"] = clustering_metadata

        stmt = (
            update(self.model)
            .where(
                self.model.id.in_(feedback_ids),
                self.model.tenant_id == tenant_id,
                self.model.deleted_at.is_(None),
            )
            .values(**values)
        )

        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount

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
            .where(self.model.id.in_(feedback_ids), self.model.tenant_id == tenant_id, self.model.deleted_at.is_(None))
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
            .where(self.model.id == feedback_id, self.model.tenant_id == tenant_id, self.model.deleted_at.is_(None))
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
            self.model.id.in_(feedback_ids), self.model.tenant_id == tenant_id, self.model.deleted_at.is_(None)
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

    def get_cached_embedding(self, feedback: Feedback) -> np.ndarray | None:
        """
        获取缓存的 embedding（从 VECTOR 字段）

        Args:
            feedback: 反馈实例

        Returns:
            embedding 向量（numpy.ndarray），如果没有缓存则返回 None

        Warning:
            返回值是 numpy.ndarray，不能直接用 if 判断，应使用 `is not None`
        """
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
            {"tenant_id": tenant_id, "query_vector": embedding_str, "min_similarity": min_similarity, "limit": limit},
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
        is_urgent: list[str] | None = None,
        derived_status: list[str] | None = None,
        board_ids: list[str] | None = None,
        search_query: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        submitter_id: int | None = None,
    ) -> list[dict]:
        """
        获取反馈列表（包含关联的客户名和主题标题，支持关键词搜索）

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            skip: 跳过数量
            limit: 返回数量
            topic_id: 过滤主题ID
            customer_id: 过滤客户ID
            is_urgent: 过滤紧急程度（多选，值: ['true', 'false']）
            has_topic: 过滤是否已聚类（多选，值: ['true', 'false']）
            clustering_status: 过滤聚类状态（多选）
            board_ids: 过滤看板ID（多选）
            search_query: 搜索关键词（搜索 content 和 ai_summary）
            submitter_id: 过滤提交者ID（用于"我的反馈"）

        Returns:
            反馈列表（包含 customer_name 和 topic_title）
        """
        from sqlalchemy import or_
        from sqlalchemy.orm import aliased

        from backend.app.admin.model.user import User
        from backend.app.userecho.model.customer import Customer
        from backend.app.userecho.model.topic import Topic

        # 使用左连接查询
        CustomerAlias = aliased(Customer)
        TopicAlias = aliased(Topic)

        query = (
            select(
                self.model,
                CustomerAlias.name.label("customer_name"),
                TopicAlias.title.label("topic_title"),
                TopicAlias.status.label("topic_status"),
                User.username.label("submitter_name"),
            )
            .outerjoin(CustomerAlias, self.model.customer_id == CustomerAlias.id)
            .outerjoin(TopicAlias, self.model.topic_id == TopicAlias.id)
            .outerjoin(User, self.model.submitter_id == User.id)
            .where(self.model.tenant_id == tenant_id, self.model.deleted_at.is_(None))
        )

        # 添加过滤条件
        if topic_id is not None:
            query = query.where(self.model.topic_id == topic_id)
        if customer_id is not None:
            query = query.where(self.model.customer_id == customer_id)

        # 多选过滤：is_urgent
        if is_urgent is not None and len(is_urgent) > 0:
            # 将字符串 'true'/'false' 转换为布尔值
            bool_values = [v.lower() == "true" for v in is_urgent]
            query = query.where(self.model.is_urgent.in_(bool_values))

        # 多选过滤：derived_status（派生状态筛选）
        # 派生状态映射（简化版）：
        # - pending: topic_id IS NULL（包含所有未归类的状态）
        # - review: clustered + topic.status = 'pending'
        # - planned: clustered + topic.status = 'planned'
        # - in_progress: clustered + topic.status = 'in_progress'
        # - completed: clustered + topic.status = 'completed'
        # - ignored: clustered + topic.status = 'ignored'
        if derived_status is not None and len(derived_status) > 0:
            conditions = []
            for status in derived_status:
                if status == "pending":
                    # 待处理: 所有未归类到主题的反馈
                    conditions.append(self.model.topic_id.is_(None))
                elif status == "review":
                    conditions.append((self.model.topic_id.is_not(None)) & (TopicAlias.status == "pending"))
                elif status == "planned":
                    conditions.append((self.model.topic_id.is_not(None)) & (TopicAlias.status == "planned"))
                elif status == "in_progress":
                    conditions.append((self.model.topic_id.is_not(None)) & (TopicAlias.status == "in_progress"))
                elif status == "completed":
                    conditions.append((self.model.topic_id.is_not(None)) & (TopicAlias.status == "completed"))
                elif status == "ignored":
                    conditions.append((self.model.topic_id.is_not(None)) & (TopicAlias.status == "ignored"))
            if conditions:
                query = query.where(or_(*conditions))

        # 多选过滤：board_ids
        if board_ids is not None and len(board_ids) > 0:
            query = query.where(self.model.board_id.in_(board_ids))

        # 关键词搜索（搜索 content + ai_summary）
        if search_query:
            search_pattern = f"%{search_query}%"
            query = query.where(
                or_(self.model.content.ilike(search_pattern), self.model.ai_summary.ilike(search_pattern))
            )

        # 日期范围筛选（基于 submitted_at）
        if date_from:
            from datetime import datetime

            date_from_dt = datetime.fromisoformat(date_from)
            query = query.where(self.model.submitted_at >= date_from_dt)
        if date_to:
            from datetime import datetime, timedelta

            # date_to 包含当天结束时间
            date_to_dt = datetime.fromisoformat(date_to) + timedelta(days=1)
            query = query.where(self.model.submitted_at < date_to_dt)

        # 过滤提交者（用于"我的反馈"模式）
        if submitter_id is not None:
            query = query.where(self.model.submitter_id == submitter_id)

        # 默认按提交时间倒序排序（最新在前）
        query = query.order_by(self.model.submitted_at.desc())
        query = query.offset(skip).limit(limit)

        result = await db.execute(query)
        rows = result.all()

        # 转换为字典列表（排除 embedding 向量字段，避免序列化失败）
        feedback_list = []
        for row in rows:
            feedback_dict = {
                **{c.name: getattr(row[0], c.name) for c in row[0].__table__.columns if c.name != "embedding"},
                "customer_name": row.customer_name,
                "topic_title": row.topic_title,
                "topic_status": row.topic_status,
                "submitter_name": row.submitter_name,
            }
            feedback_list.append(feedback_dict)

        return feedback_list

    async def search_by_semantic(
        self,
        db: AsyncSession,
        tenant_id: str,
        query_embedding: list[float],
        skip: int = 0,
        limit: int = 100,
        topic_id: str | None = None,
        customer_id: str | None = None,
        is_urgent: bool | None = None,
        has_topic: bool | None = None,
        clustering_status: str | None = None,
        min_similarity: float = 0.85,
    ) -> list[dict]:
        """
        使用 pgvector 语义搜索反馈（包含关联查询）

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            query_embedding: 查询向量
            skip: 跳过数量
            limit: 返回数量
            min_similarity: 最小相似度阈值（0-1，默认 0.85，越高越精确）
            topic_id: 过滤主题ID
            customer_id: 过滤客户ID
            is_urgent: 过滤紧急程度
            has_topic: 过滤是否已聚类
            clustering_status: 过滤聚类状态

        Returns:
            反馈列表（包含 customer_name, topic_title, similarity_score）
        """
        from sqlalchemy import text

        # 将 embedding 向量转换为 PostgreSQL vector 格式字符串
        embedding_str = str(query_embedding)

        # 构建过滤条件 SQL（使用 f-string 直接嵌入，避免参数绑定问题）
        filter_conditions = [
            f"f.tenant_id = '{tenant_id}'",
            "f.embedding IS NOT NULL",
            "f.deleted_at IS NULL",
            f"(1 - (f.embedding <=> '{embedding_str}'::vector)) >= {min_similarity}",
        ]

        # 添加过滤条件
        if topic_id is not None:
            filter_conditions.append(f"f.topic_id = '{topic_id}'")
        if customer_id is not None:
            filter_conditions.append(f"f.customer_id = '{customer_id}'")
        if is_urgent is not None:
            filter_conditions.append(f"f.is_urgent = {is_urgent}")
        if has_topic is not None:
            if has_topic:
                filter_conditions.append("f.topic_id IS NOT NULL")
            else:
                filter_conditions.append("f.topic_id IS NULL")
        if clustering_status is not None:
            filter_conditions.append(f"f.clustering_status = '{clustering_status}'")

        where_clause = " AND ".join(filter_conditions)

        # pgvector 相似度搜索 + 关联查询
        query_sql = f"""
            SELECT
                f.id, f.tenant_id, f.customer_id, f.anonymous_author, f.anonymous_source,
                f.topic_id, f.content, f.source, f.ai_summary, f.is_urgent, f.ai_metadata,
                f.screenshot_url, f.source_platform, f.source_user_name, f.source_user_id,
                f.ai_confidence, f.submitter_id, f.sentiment, f.sentiment_score, f.sentiment_reason,
                f.clustering_status, f.clustering_metadata, f.submitted_at, f.deleted_at,
                f.created_time, f.updated_time,
                c.name as customer_name,
                t.title as topic_title,
                (1 - (f.embedding <=> '{embedding_str}'::vector)) as similarity_score
            FROM feedbacks f
            LEFT JOIN customers c ON f.customer_id = c.id
            LEFT JOIN topics t ON f.topic_id = t.id
            WHERE {where_clause}
            ORDER BY f.embedding <=> '{embedding_str}'::vector
            LIMIT {limit} OFFSET {skip}
        """

        result = await db.execute(text(query_sql))
        rows = result.all()

        # 转换为字典列表
        feedback_list = []
        for row in rows:
            # 将 Row 对象转换为字典
            row_dict = dict(row._mapping)
            # 排除 embedding 字段（SQL 中未查询）
            feedback_list.append(row_dict)

        return feedback_list


crud_feedback = CRUDFeedback(Feedback)
