"""Topic CRUD"""

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.userecho.crud.base import TenantAwareCRUD
from backend.app.userecho.model.topic import Topic


class CRUDTopic(TenantAwareCRUD[Topic]):
    """需求主题 CRUD"""

    async def update_centroid(
        self,
        db: AsyncSession,
        tenant_id: str,
        topic_id: str,
        centroid: list[float] | None,
    ) -> bool:
        """更新主题中心向量（用于增量匹配/合并建议）"""
        stmt = (
            update(self.model)
            .where(
                self.model.id == topic_id,
                self.model.tenant_id == tenant_id,
                self.model.deleted_at.is_(None),
            )
            .values(centroid=centroid)
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount > 0

    async def update_cluster_quality(
        self,
        db: AsyncSession,
        tenant_id: str,
        topic_id: str,
        cluster_quality: dict | None,
        *,
        is_noise: bool | None = None,
    ) -> bool:
        """更新聚类质量指标（可选同时更新 is_noise）"""
        values: dict = {'cluster_quality': cluster_quality}
        if is_noise is not None:
            values['is_noise'] = is_noise

        stmt = (
            update(self.model)
            .where(
                self.model.id == topic_id,
                self.model.tenant_id == tenant_id,
                self.model.deleted_at.is_(None),
            )
            .values(**values)
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount > 0

    async def get_with_feedbacks(
        self,
        db: AsyncSession,
        tenant_id: str,
        topic_id: str,
    ) -> dict | None:
        """
        获取主题详情（包含关联反馈）

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            topic_id: 主题ID

        Returns:
            包含 topic 和 feedbacks 的字典，或 None
        """
        from backend.app.userecho.model.feedback import Feedback
        from backend.app.userecho.model.customer import Customer
        from backend.app.admin.model.user import User

        # 获取主题
        topic = await self.get_by_id(db, tenant_id, topic_id)
        if not topic:
            return None

        # 获取关联反馈（关联查询 Customer 和 User）
        query = (
            select(
                Feedback, 
                Customer.name.label('customer_name'),
                User.username.label('submitter_name')
            )
            .outerjoin(Customer, Feedback.customer_id == Customer.id)
            .outerjoin(User, Feedback.submitter_id == User.id)
            .where(
                Feedback.tenant_id == tenant_id,
                Feedback.topic_id == topic_id,
                Feedback.deleted_at.is_(None),
            )
        )
        result = await db.execute(query)
        rows = result.all()

        feedbacks = []
        for feedback_obj, customer_name, submitter_name in rows:
            fb_dict = {c.name: getattr(feedback_obj, c.name) for c in feedback_obj.__table__.columns}
            fb_dict['customer_name'] = customer_name
            fb_dict['submitter_name'] = submitter_name
            feedbacks.append(fb_dict)

        return {'topic': topic, 'feedbacks': feedbacks}

    async def update_status(
        self,
        db: AsyncSession,
        tenant_id: str,
        topic_id: str,
        new_status: str,
    ) -> Topic | None:
        """
        更新主题状态

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            topic_id: 主题ID
            new_status: 新状态

        Returns:
            更新后的主题 或 None
        """
        return await self.update(db, tenant_id, topic_id, status=new_status)

    async def increment_feedback_count(
        self,
        db: AsyncSession,
        tenant_id: str,
        topic_id: str,
        delta: int = 1,
    ) -> bool:
        """
        增加/减少反馈计数

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            topic_id: 主题ID
            delta: 变化量（正数增加，负数减少）

        Returns:
            是否成功
        """
        topic = await self.get_by_id(db, tenant_id, topic_id)
        if not topic:
            return False

        topic.feedback_count = max(0, topic.feedback_count + delta)
        await db.commit()
        return True

    async def get_list_sorted(
        self,
        db: AsyncSession,
        tenant_id: str,
        skip: int = 0,
        limit: int = 100,
        status: list[str] | None = None,
        category: list[str] | None = None,
        board_ids: list[str] | None = None,
        sort_by: str = 'created_time',
        sort_order: str = 'desc',
        search_query: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[Topic]:
        """
        获取主题列表（支持排序、过滤和关键词搜索）

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            skip: 跳过数量
            limit: 返回数量
            status: 过滤状态（多选）
            category: 过滤分类（多选）
            board_ids: 过滤看板ID（多选）
            sort_by: 排序字段
            sort_order: 排序方向（asc/desc）
            search_query: 搜索关键词（搜索 title 和 description）

        Returns:
            主题列表（包含 priority_score 关联）
        """
        from sqlalchemy import or_
        from sqlalchemy.orm import joinedload

        query = (
            select(self.model)
            .options(joinedload(self.model.priority_score))  # 加载关联的评分
            .where(self.model.tenant_id == tenant_id, self.model.deleted_at.is_(None))
        )

        # 添加过滤条件（多选）
        if status and len(status) > 0:
            query = query.where(self.model.status.in_(status))
        if category and len(category) > 0:
            query = query.where(self.model.category.in_(category))
        if board_ids and len(board_ids) > 0:
            query = query.where(self.model.board_id.in_(board_ids))

        # 关键词搜索（搜索 title + description）- 中文分词后 OR 匹配
        if search_query:
            import jieba

            from backend.common.log import log

            # 使用 jieba 分词，支持中文自动分词
            # "睡眠模式" -> ["睡眠", "模式"]
            keywords = [kw for kw in jieba.cut(search_query.strip()) if kw.strip() and len(kw.strip()) > 0]
            # 过滤掉单字符（通常是停用词或无意义词）
            keywords = [kw for kw in keywords if len(kw) > 1 or not kw.isalpha()]
            log.info(f'[SEARCH_DEBUG] CRUD Layer - Applying keyword search filter (jieba): keywords={keywords!r}')

            if keywords:
                # 每个关键词构建一个 OR 条件：title LIKE '%kw%' OR description LIKE '%kw%'
                keyword_conditions = []
                for kw in keywords:
                    search_pattern = f'%{kw}%'
                    keyword_conditions.append(
                        or_(self.model.title.ilike(search_pattern), self.model.description.ilike(search_pattern))
                    )
                # 所有关键词之间是 OR 关系
                query = query.where(or_(*keyword_conditions))
        else:
            from backend.common.log import log

            log.info('[SEARCH_DEBUG] CRUD Layer - No search_query, skipping filter')

        # 日期范围筛选（基于 created_time）
        if date_from:
            from datetime import datetime

            date_from_dt = datetime.fromisoformat(date_from)
            query = query.where(self.model.created_time >= date_from_dt)
        if date_to:
            from datetime import datetime, timedelta

            # date_to 包含当天结束时间
            date_to_dt = datetime.fromisoformat(date_to) + timedelta(days=1)
            query = query.where(self.model.created_time < date_to_dt)

        # 添加排序
        sort_column = getattr(self.model, sort_by, self.model.created_time)
        query = query.order_by(sort_column.desc()) if sort_order == 'desc' else query.order_by(sort_column.asc())

        query = query.offset(skip).limit(limit)

        result = await db.execute(query)
        return list(result.scalars().unique().all())  # unique() 防止 joinedload 产生重复

    async def search_by_semantic(
        self,
        db: AsyncSession,
        tenant_id: str,
        query_embedding: list[float],
        skip: int = 0,
        limit: int = 100,
        status: list[str] | None = None,
        category: list[str] | None = None,
        board_ids: list[str] | None = None,
        min_similarity: float = 0.70,
    ) -> list[Topic]:
        """
        使用 pgvector 语义搜索主题（基于中心向量）

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            query_embedding: 查询向量
            skip: 跳过数量
            limit: 返回数量
            status: 过滤状态（多选）
            category: 过滤分类（多选）
            board_ids: 过滤看板ID（多选）
            min_similarity: 最小相似度阈值（0-1，默认 0.70，主题搜索阈值较低）

        Returns:
            主题列表（包含 priority_score 关联和相似度评分）
        """
        from sqlalchemy import text

        from backend.common.log import log

        # 将 embedding 向量转换为 PostgreSQL vector 格式字符串
        embedding_str = str(query_embedding)

        # 构建过滤条件 SQL
        filter_conditions = [
            f"t.tenant_id = '{tenant_id}'",
            't.centroid IS NOT NULL',
            't.deleted_at IS NULL',
            f"(1 - (t.centroid <=> '{embedding_str}'::vector)) >= {min_similarity}",
        ]

        # 添加过滤条件（多选）
        if status is not None and len(status) > 0:
            status_conditions = ' OR '.join([f"t.status = '{s}'" for s in status])
            filter_conditions.append(f'({status_conditions})')
        if category is not None and len(category) > 0:
            category_conditions = ' OR '.join([f"t.category = '{c}'" for c in category])
            filter_conditions.append(f'({category_conditions})')
        if board_ids is not None and len(board_ids) > 0:
            board_conditions = ' OR '.join([f"t.board_id = '{b}'" for b in board_ids])
            filter_conditions.append(f'({board_conditions})')

        where_clause = ' AND '.join(filter_conditions)

        # pgvector 相似度搜索 + 关联查询
        query_sql = f"""
            SELECT
                t.id, t.tenant_id, t.title, t.category, t.status, t.description,
                t.ai_generated, t.ai_confidence, t.feedback_count, t.cluster_quality,
                t.is_noise, t.deleted_at, t.created_time, t.updated_time,
                ps.id as ps_id, ps.tenant_id as ps_tenant_id, ps.topic_id as ps_topic_id,
                ps.impact_scope, ps.business_value, ps.dev_cost, ps.urgency_factor,
                ps.total_score, ps.details, ps.created_time as ps_created_time,
                ps.updated_time as ps_updated_time,
                (1 - (t.centroid <=> '{embedding_str}'::vector)) as similarity_score
            FROM topics t
            LEFT JOIN priority_scores ps ON t.id = ps.topic_id
            WHERE {where_clause}
            ORDER BY t.centroid <=> '{embedding_str}'::vector
            LIMIT {limit} OFFSET {skip}
        """

        try:
            result = await db.execute(text(query_sql))
            rows = result.all()

            # 转换为 Topic 对象列表（包含关联的 priority_score）
            topics = []
            for row in rows:
                from backend.app.userecho.model.priority_score import PriorityScore

                # 创建 Topic 对象
                topic = Topic(
                    id=row.id,
                    tenant_id=row.tenant_id,
                    title=row.title,
                    category=row.category,
                    status=row.status,
                    description=row.description,
                    ai_generated=row.ai_generated,
                    ai_confidence=row.ai_confidence,
                    feedback_count=row.feedback_count,
                    cluster_quality=row.cluster_quality,
                    is_noise=row.is_noise,
                    deleted_at=row.deleted_at,
                    created_time=row.created_time,
                    updated_time=row.updated_time,
                )

                # 如果有 priority_score，创建关联对象
                if row.ps_id:
                    topic.priority_score = PriorityScore(
                        id=row.ps_id,
                        tenant_id=row.ps_tenant_id,
                        topic_id=row.ps_topic_id,
                        impact_scope=row.impact_scope,
                        business_value=row.business_value,
                        dev_cost=row.dev_cost,
                        urgency_factor=row.urgency_factor,
                        total_score=row.total_score,
                        details=row.details,
                        created_time=row.ps_created_time,
                        updated_time=row.ps_updated_time,
                    )

                # 附加相似度评分（用于调试和展示）
                topic.similarity_score = float(row.similarity_score)  # type: ignore

                topics.append(topic)

            return topics

        except Exception as e:
            log.error(f'Semantic search failed for topics: {e}')
            # Fallback: 返回空列表
            return []


crud_topic = CRUDTopic(Topic)
