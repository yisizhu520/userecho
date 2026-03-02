"""检查是否有已存在的相似主题"""

import asyncio
import numpy as np
from backend.database.db import async_db_session
from sqlalchemy import select
from backend.app.userecho.model.feedback import Feedback
from backend.app.userecho.crud.crud_topic import crud_topic


async def check_similar_topics():
    async with async_db_session.begin() as db:
        # 1. 获取这48条反馈
        feedbacks_query = (
            select(Feedback)
            .where(
                Feedback.tenant_id == "default-tenant",
                Feedback.deleted_at.is_(None),
                Feedback.topic_id.is_(None),
                Feedback.board_id == "default-board",
            )
            .limit(48)
        )

        result = await db.execute(feedbacks_query)
        feedbacks = list(result.scalars().all())

        if not feedbacks:
            print("没有找到反馈")
            return

        # 2. 提取 embeddings
        embeddings = []
        for f in feedbacks:
            if f.embedding is not None:
                embeddings.append(f.embedding)

        if not embeddings:
            print("没有 embedding")
            return

        # 3. 计算中心向量
        embeddings_array = np.array(embeddings)
        centroid = np.mean(embeddings_array, axis=0).astype(float).tolist()

        print(f"计算了 {len(embeddings)} 条反馈的中心向量")

        # 4. 搜索相似主题
        similar_topics = await crud_topic.search_by_semantic(
            db=db,
            tenant_id="default-tenant",
            query_embedding=centroid,
            limit=5,
            min_similarity=0.80,
        )

        print(f"\n=== 找到 {len(similar_topics)} 个相似主题（min_similarity=0.80）===")

        if similar_topics:
            for topic in similar_topics:
                similarity = getattr(topic, "similarity_score", "unknown")
                print(f"\n主题 ID: {topic.id}")
                print(f"  标题: {topic.title}")
                print(f"  状态: {topic.status}")
                print(f"  分类: {topic.category}")
                print(f"  相似度: {similarity}")
                print(f"  反馈数: {topic.feedback_count}")
                print(f"  创建时间: {topic.created_time}")
        else:
            print("没有找到相似主题")


if __name__ == "__main__":
    asyncio.run(check_similar_topics())
