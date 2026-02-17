"""测试批量 Embedding API

验证所有 AI 提供商（OpenAI, GLM, Volcengine）的批量 embedding 功能
"""

import asyncio
import sys
import time

from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.utils.ai_client import ai_client


async def test_single_embedding():
    """测试单条 embedding（对比基准）"""
    print('\n' + '=' * 60)
    print('【测试 1】单条 Embedding（循环调用）')
    print('=' * 60)

    texts = [
        '登录按钮点不了',
        '注册功能有问题',
        '界面加载很慢',
        '希望增加暗黑模式',
        '导出功能崩溃了',
    ]

    start = time.time()
    results = []

    for i, text in enumerate(texts, 1):
        embedding = await ai_client.get_embedding(text)
        results.append(embedding)
        print(f'  {i}. "{text}" → {"✓" if embedding else "✗"} ({len(embedding) if embedding else 0} 维)')

    elapsed = time.time() - start
    success_count = sum(1 for e in results if e)

    print(f'\n  总耗时: {elapsed:.2f}s')
    print(f'  成功率: {success_count}/{len(texts)}')
    print(f'  平均: {elapsed / len(texts):.2f}s/条')

    return elapsed, results


async def test_batch_embedding():
    """测试批量 embedding"""
    print('\n' + '=' * 60)
    print('【测试 2】批量 Embedding（单次调用）')
    print('=' * 60)

    texts = [
        '登录按钮点不了',
        '注册功能有问题',
        '界面加载很慢',
        '希望增加暗黑模式',
        '导出功能崩溃了',
    ]

    start = time.time()
    results = await ai_client.get_embeddings_batch(texts, batch_size=10)
    elapsed = time.time() - start

    for i, (text, embedding) in enumerate(zip(texts, results), 1):
        print(f'  {i}. "{text}" → {"✓" if embedding else "✗"} ({len(embedding) if embedding else 0} 维)')

    success_count = sum(1 for e in results if e)

    print(f'\n  总耗时: {elapsed:.2f}s')
    print(f'  成功率: {success_count}/{len(texts)}')
    print(f'  平均: {elapsed / len(texts):.2f}s/条')

    return elapsed, results


async def test_large_batch():
    """测试大批量 embedding（模拟实际聚类场景）"""
    print('\n' + '=' * 60)
    print('【测试 3】大批量 Embedding（50 条）')
    print('=' * 60)

    # 模拟 50 条反馈
    base_texts = [
        '登录按钮点不了',
        '注册功能有问题',
        '界面加载很慢',
        '希望增加暗黑模式',
        '导出功能崩溃了',
        '搜索结果不准确',
        '忘记密码功能坏了',
        '移动端体验差',
        '希望支持批量操作',
        '数据统计不对',
    ]

    texts = []
    for i in range(5):
        texts.extend(f'{text} ({i + 1})' for text in base_texts)

    print(f'  文本数量: {len(texts)}')

    start = time.time()
    results = await ai_client.get_embeddings_batch(texts, batch_size=50)
    elapsed = time.time() - start

    success_count = sum(1 for e in results if e)

    print(f'\n  总耗时: {elapsed:.2f}s')
    print(f'  成功率: {success_count}/{len(texts)}')
    print(f'  平均: {elapsed / len(texts) * 1000:.0f}ms/条')

    return elapsed, results


async def test_edge_cases() -> None:
    """测试边界情况"""
    print('\n' + '=' * 60)
    print('【测试 4】边界情况处理')
    print('=' * 60)

    texts = [
        '',  # 空字符串
        '   ',  # 空白字符
        '正常文本',  # 正常文本
        'a' * 3000,  # 超长文本（会被截断到 2000）
        None,  # None（需要过滤）
    ]

    # 过滤 None
    filtered_texts = [t if t is not None else '' for t in texts]

    results = await ai_client.get_embeddings_batch(filtered_texts, batch_size=10)

    for i, (text, embedding) in enumerate(zip(filtered_texts, results), 1):
        text_preview = text[:30] + '...' if len(text) > 30 else text
        print(f'  {i}. "{text_preview}" → {"✓" if embedding else "✗"}')


async def main() -> None:
    print('\n🚀 批量 Embedding API 测试')
    print(f'当前 AI Provider: {ai_client.current_provider.upper()}')

    try:
        # 测试 1：单条 embedding（循环）
        single_time, _ = await test_single_embedding()

        # 测试 2：批量 embedding
        batch_time, _ = await test_batch_embedding()

        # 性能对比
        print('\n' + '=' * 60)
        print('【性能对比】')
        print('=' * 60)
        if single_time > 0 and batch_time > 0:
            speedup = single_time / batch_time
            print(f'  单条循环: {single_time:.2f}s')
            print(f'  批量调用: {batch_time:.2f}s')
            print(f'  性能提升: {speedup:.1f}x 🎉')

        # 测试 3：大批量
        await test_large_batch()

        # 测试 4：边界情况
        await test_edge_cases()

        print('\n' + '=' * 60)
        print('✅ 所有测试完成！')
        print('=' * 60)

    except Exception as e:
        print(f'\n❌ 测试失败: {e}')
        import traceback

        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(main())
