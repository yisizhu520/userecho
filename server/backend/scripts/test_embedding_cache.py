"""测试 Embedding 缓存功能

验证 embedding 的缓存读写和性能提升
"""

import asyncio
import sys
import time
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.app.userecho.crud import crud_feedback
from backend.app.userecho.model.feedback import Feedback
from backend.database.db_mysql import async_db_session
from backend.utils.ai_client import ai_client


async def test_cache_single_feedback():
    """测试单条反馈的缓存读写"""
    print('\n' + '=' * 60)
    print('【测试 1】单条反馈缓存读写')
    print('=' * 60)

    async with async_db_session() as db:
        # 1. 获取一个未聚类的反馈
        feedbacks = await crud_feedback.get_unclustered(db, 'default-tenant', limit=1)
        if not feedbacks:
            print('  ⚠️  没有未聚类的反馈，跳过测试')
            return

        feedback = feedbacks[0]
        print(f'  测试反馈: {feedback.id}')
        print(f'  内容: {feedback.content[:50]}...')

        # 2. 检查是否有缓存
        cached = crud_feedback.get_cached_embedding(feedback)
        print(f'  缓存状态: {"✓ 已缓存" if cached else "✗ 未缓存"}')

        # 3. 如果没有缓存，生成并保存
        if not cached:
            print('  正在生成 embedding...')
            embedding = await ai_client.get_embedding(feedback.content)

            if embedding:
                print(f'  生成成功: {len(embedding)} 维')

                # 保存到缓存
                success = await crud_feedback.update_embedding(
                    db=db,
                    tenant_id='default-tenant',
                    feedback_id=feedback.id,
                    embedding=embedding
                )
                print(f'  缓存保存: {"✓ 成功" if success else "✗ 失败"}')

                # 重新读取验证
                feedbacks_refreshed = await crud_feedback.get_by_id(db, 'default-tenant', feedback.id)
                cached_after = crud_feedback.get_cached_embedding(feedbacks_refreshed)
                print(f'  缓存验证: {"✓ 成功" if cached_after else "✗ 失败"}')
            else:
                print('  ✗ Embedding 生成失败')
        else:
            print(f'  已有缓存: {len(cached)} 维')


async def test_batch_cache():
    """测试批量缓存"""
    print('\n' + '=' * 60)
    print('【测试 2】批量缓存性能')
    print('=' * 60)

    async with async_db_session() as db:
        # 1. 获取 10 条未聚类的反馈
        feedbacks = await crud_feedback.get_unclustered(db, 'default-tenant', limit=10)
        if len(feedbacks) < 2:
            print('  ⚠️  反馈数量不足，跳过测试')
            return

        print(f'  测试反馈数量: {len(feedbacks)}')

        # 2. 清空缓存（仅测试用）
        # 注意：这会清空 ai_metadata，生产环境不要这样做
        for feedback in feedbacks:
            feedback.ai_metadata = None
        await db.commit()
        print('  已清空缓存（测试用）')

        # 3. 第一次运行：无缓存
        print('\n  === 第一次运行（无缓存） ===')
        start = time.time()

        contents = [f.content for f in feedbacks]
        embeddings_batch = await ai_client.get_embeddings_batch(contents, batch_size=10)

        # 保存到缓存
        embeddings_to_cache = {}
        for feedback, embedding in zip(feedbacks, embeddings_batch):
            if embedding:
                embeddings_to_cache[feedback.id] = embedding

        cached_count = await crud_feedback.batch_update_embeddings(
            db=db,
            tenant_id='default-tenant',
            feedback_embeddings=embeddings_to_cache
        )

        elapsed_first = time.time() - start
        print(f'  耗时: {elapsed_first:.2f}s')
        print(f'  缓存数量: {cached_count}/{len(feedbacks)}')

        # 4. 第二次运行：有缓存
        print('\n  === 第二次运行（有缓存） ===')
        start = time.time()

        # 重新获取反馈（刷新 ai_metadata）
        feedbacks_refreshed = await crud_feedback.get_unclustered(db, 'default-tenant', limit=10)

        cache_hit = 0
        for feedback in feedbacks_refreshed:
            cached_embedding = crud_feedback.get_cached_embedding(feedback)
            if cached_embedding:
                cache_hit += 1

        elapsed_second = time.time() - start
        print(f'  耗时: {elapsed_second:.2f}s')
        print(f'  缓存命中: {cache_hit}/{len(feedbacks_refreshed)} ({cache_hit/len(feedbacks_refreshed)*100:.1f}%)')

        # 5. 性能对比
        if elapsed_first > 0 and elapsed_second > 0:
            speedup = elapsed_first / elapsed_second
            print(f'\n  性能提升: {speedup:.1f}x 🎉')
            print(f'  时间节省: {(1 - elapsed_second/elapsed_first)*100:.1f}%')


async def test_clustering_with_cache():
    """测试聚类服务的缓存使用"""
    print('\n' + '=' * 60)
    print('【测试 3】聚类服务缓存使用')
    print('=' * 60)

    from backend.app.userecho.service.clustering_service import clustering_service

    async with async_db_session() as db:
        # 触发聚类
        print('  触发聚类（观察缓存命中率）...')
        result = await clustering_service.trigger_clustering(
            db=db,
            tenant_id='default-tenant',
            max_feedbacks=20
        )

        print(f'\n  聚类状态: {result.get("status")}')
        print(f'  反馈数量: {result.get("feedbacks_count", 0)}')
        print(f'  聚类数量: {result.get("clusters_count", 0)}')
        print(f'  创建主题: {result.get("topics_created", 0)}')

        # 注意：缓存命中率会在聚类服务的日志中显示


async def main():
    print('\n🚀 Embedding 缓存功能测试')

    try:
        # 测试 1：单条缓存
        await test_cache_single_feedback()

        # 测试 2：批量缓存性能
        await test_batch_cache()

        # 测试 3：聚类服务缓存
        await test_clustering_with_cache()

        print('\n' + '=' * 60)
        print('✅ 所有测试完成！')
        print('=' * 60)
        print('\n💡 提示：')
        print('  - 第二次聚类时应该看到 100% 缓存命中率')
        print('  - 查看日志中的 "Embedding cache hit" 信息')
        print('  - 数据库 ai_metadata 字段会存储 embedding 向量')

    except Exception as e:
        print(f'\n❌ 测试失败: {e}')
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(main())
