"""
诊断 Redis 和 PostgreSQL 连接性能

Linus 的第一定律：如果远程数据库慢，90% 是网络延迟，不是数据库的问题。
"""

import asyncio
import sys
import time

from pathlib import Path

# 添加项目根目录到 sys.path
current_file = Path(__file__).resolve()
backend_root = current_file.parent
sys.path.insert(0, str(backend_root))

from sqlalchemy import text

from backend.core.conf import settings
from backend.database.db import async_db_session
from backend.database.redis import RedisCli


async def measure_redis_latency() -> dict:
    """测量 Redis 延迟"""
    print("\n" + "=" * 80)
    print("【Redis 连接诊断】")
    print("=" * 80)

    # 显示配置
    if settings.REDIS_URL:
        # 隐藏密码
        url_display = settings.REDIS_URL.split("@")[-1] if "@" in settings.REDIS_URL else settings.REDIS_URL
        print("连接方式: REDIS_URL")
        print(f"地址: {url_display}")
    else:
        print("连接方式: 独立参数")
        print(f"地址: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        print(f"数据库: {settings.REDIS_DATABASE}")
    print(f"超时设置: {settings.REDIS_TIMEOUT}s")

    # 创建 Redis 客户端
    redis = RedisCli()
    results = {}

    try:
        # 1. 测试连接
        print("\n[1] 测试基础连接...")
        start = time.perf_counter()
        await redis.ping()
        elapsed = (time.perf_counter() - start) * 1000
        results["ping"] = elapsed
        print(f"✅ PING 成功: {elapsed:.2f}ms")

        if elapsed > 100:
            print(f"⚠️  警告: 延迟过高 ({elapsed:.2f}ms > 100ms)")
            print("   这通常意味着你的 Redis 在远程服务器上")
            print("   每次操作都有这个网络延迟开销")

        # 2. 测试简单操作
        print("\n[2] 测试简单操作（SET/GET）...")
        operations = []

        for i in range(10):
            # SET
            start = time.perf_counter()
            await redis.set(f"test:diagnose:{i}", f"value_{i}", ex=10)
            set_time = (time.perf_counter() - start) * 1000

            # GET
            start = time.perf_counter()
            await redis.get(f"test:diagnose:{i}")
            get_time = (time.perf_counter() - start) * 1000

            operations.append({"set": set_time, "get": get_time})

        # 清理
        await redis.delete(*[f"test:diagnose:{i}" for i in range(10)])

        # 统计
        avg_set = sum(op["set"] for op in operations) / len(operations)
        avg_get = sum(op["get"] for op in operations) / len(operations)
        max_set = max(op["set"] for op in operations)
        max_get = max(op["get"] for op in operations)

        results["set_avg"] = avg_set
        results["get_avg"] = avg_get

        print(f"✅ SET 平均: {avg_set:.2f}ms, 最大: {max_set:.2f}ms")
        print(f"✅ GET 平均: {avg_get:.2f}ms, 最大: {max_get:.2f}ms")

        # 3. 测试管道操作
        print("\n[3] 测试管道操作（Pipeline）...")
        start = time.perf_counter()
        async with redis.pipeline() as pipe:
            for i in range(10):
                pipe.set(f"test:pipeline:{i}", f"value_{i}", ex=10)
            await pipe.execute()
        pipeline_time = (time.perf_counter() - start) * 1000
        results["pipeline"] = pipeline_time

        await redis.delete(*[f"test:pipeline:{i}" for i in range(10)])

        print(f"✅ 10 次操作（管道）: {pipeline_time:.2f}ms")
        print(f"   对比 10 次单独操作: ~{(avg_set) * 10:.2f}ms")

        if pipeline_time < avg_set * 10 / 2:
            improvement = (avg_set * 10 - pipeline_time) / (avg_set * 10) * 100
            print(f"✅ 管道优化有效！减少了 {improvement:.1f}% 的时间")

        # 4. 问题诊断
        print("\n" + "-" * 80)
        print("【诊断结果】")
        print("-" * 80)

        if avg_get < 10:
            print("✅ 延迟优秀 (<10ms) - 本地或低延迟网络")
        elif avg_get < 50:
            print("⚠️  延迟一般 (10-50ms) - 同城或近距离网络")
        elif avg_get < 100:
            print("❌ 延迟偏高 (50-100ms) - 跨地域网络")
        else:
            print(f"❌ 延迟过高 (>{avg_get:.0f}ms) - 远程服务器")

        # 计算影响
        if avg_get > 50:
            print("\n⚠️  性能影响分析:")
            print(f"   - 1 次 Redis 操作: ~{avg_get:.0f}ms")
            print(f"   - 10 次操作: ~{avg_get * 10:.0f}ms")
            print(f"   - 100 次操作: ~{avg_get * 100:.0f}ms")
            print(f"   → 如果一个接口调用 Redis 10 次,仅网络延迟就需要 {avg_get * 10:.0f}ms")

        # 优化建议
        if avg_get > 20:
            print("\n💡 优化建议:")
            print("   1. 【最佳方案】使用本地 Redis 或同城 Redis")
            print("   2. 减少 Redis 调用次数（批量操作、缓存聚合）")
            print("   3. 使用管道（Pipeline）合并多次操作")
            print("   4. 考虑使用二级缓存（内存缓存 + Redis）")

    except Exception as e:
        print(f"❌ Redis 连接失败: {e}")
        import traceback

        traceback.print_exc()
    finally:
        await redis.aclose()

    return results


async def measure_postgresql_latency() -> dict:
    """测量 PostgreSQL 延迟"""
    print("\n" + "=" * 80)
    print("【PostgreSQL 连接诊断】")
    print("=" * 80)

    # 显示配置
    print(f"地址: {settings.DATABASE_HOST}:{settings.DATABASE_PORT}")
    print(f"数据库: {settings.DATABASE_SCHEMA}")
    print(f"用户: {settings.DATABASE_USER}")
    print(f"连接池: size={10}, max_overflow={20}")

    results = {}

    try:
        # 1. 测试连接
        print("\n[1] 测试基础连接...")
        start = time.perf_counter()
        async with async_db_session() as session:
            result = await session.execute(text("SELECT 1"))
            result.scalar()
        elapsed = (time.perf_counter() - start) * 1000
        results["connect"] = elapsed
        print(f"✅ 连接成功: {elapsed:.2f}ms")

        if elapsed > 100:
            print(f"⚠️  警告: 延迟过高 ({elapsed:.2f}ms > 100ms)")

        # 2. 测试简单查询
        print("\n[2] 测试简单查询...")
        queries = []

        for _i in range(10):
            start = time.perf_counter()
            async with async_db_session() as session:
                result = await session.execute(text("SELECT NOW()"))
                result.first()
            query_time = (time.perf_counter() - start) * 1000
            queries.append(query_time)

        avg_query = sum(queries) / len(queries)
        max_query = max(queries)
        results["query_avg"] = avg_query

        print(f"✅ 平均查询时间: {avg_query:.2f}ms")
        print(f"   最大查询时间: {max_query:.2f}ms")

        # 3. 测试表查询（如果有表的话）
        print("\n[3] 测试表查询...")
        try:
            start = time.perf_counter()
            async with async_db_session() as session:
                # 尝试查询 sys_user 表（通常存在）
                result = await session.execute(text("SELECT COUNT(*) FROM sys_user LIMIT 1"))
                count = result.scalar()
            table_query_time = (time.perf_counter() - start) * 1000
            results["table_query"] = table_query_time
            print(f"✅ 表查询成功: {table_query_time:.2f}ms (记录数: {count})")
        except Exception as e:
            print(f"⚠️  表查询失败（表可能不存在）: {e}")

        # 4. 测试事务
        print("\n[4] 测试事务...")
        start = time.perf_counter()
        async with async_db_session() as session:
            async with session.begin():
                await session.execute(text("SELECT 1"))
                await session.execute(text("SELECT 2"))
                await session.execute(text("SELECT 3"))
        transaction_time = (time.perf_counter() - start) * 1000
        results["transaction"] = transaction_time
        print(f"✅ 事务（3 条查询）: {transaction_time:.2f}ms")

        # 5. 问题诊断
        print("\n" + "-" * 80)
        print("【诊断结果】")
        print("-" * 80)

        if avg_query < 10:
            print("✅ 延迟优秀 (<10ms) - 本地或低延迟网络")
        elif avg_query < 50:
            print("⚠️  延迟一般 (10-50ms) - 同城或近距离网络")
        elif avg_query < 100:
            print("❌ 延迟偏高 (50-100ms) - 跨地域网络")
        else:
            print(f"❌ 延迟过高 (>{avg_query:.0f}ms) - 远程服务器")

        # 计算影响
        if avg_query > 50:
            print("\n⚠️  性能影响分析:")
            print(f"   - 1 次数据库查询: ~{avg_query:.0f}ms")
            print(f"   - 5 次查询: ~{avg_query * 5:.0f}ms")
            print(f"   - 10 次查询: ~{avg_query * 10:.0f}ms")
            print(f"   → 如果一个接口需要 5 次查询，仅网络延迟就需要 {avg_query * 5:.0f}ms")

        # 优化建议
        if avg_query > 20:
            print("\n💡 优化建议:")
            print("   1. 【最佳方案】使用本地数据库或同城数据库")
            print("   2. 减少数据库查询次数（JOIN 合并查询）")
            print("   3. 使用缓存（Redis）减少数据库访问")
            print("   4. 批量操作替代多次单独操作")
            print("   5. 考虑使用 Read Replica（如果是读多写少场景）")

    except Exception as e:
        print(f"❌ PostgreSQL 连接失败: {e}")
        import traceback

        traceback.print_exc()

    return results


async def analyze_api_performance(redis_results: dict, db_results: dict) -> None:
    """分析 API 性能瓶颈"""
    print("\n" + "=" * 80)
    print("【API 性能分析】")
    print("=" * 80)

    # 模拟一个典型的 API 请求流程
    print("\n假设一个典型的 API 请求:")
    print("  1. JWT 验证（1 次 Redis 查询）")
    print("  2. 查询用户信息（1 次 DB 查询）")
    print("  3. 查询业务数据（2-3 次 DB 查询）")
    print("  4. 更新缓存（1-2 次 Redis 操作）")
    print("  总计: ~2-3 次 Redis + ~3-4 次 DB 查询")

    if "get_avg" in redis_results and "query_avg" in db_results:
        redis_latency = redis_results["get_avg"]
        db_latency = db_results["query_avg"]

        # 计算总延迟
        estimated_total = (redis_latency * 2.5) + (db_latency * 3.5)

        print("\n基于实际测量:")
        print(f"  Redis 单次延迟: {redis_latency:.2f}ms")
        print(f"  DB 单次延迟: {db_latency:.2f}ms")
        print(f"  估算总网络延迟: {estimated_total:.2f}ms")

        if estimated_total > 5000:
            print(f"\n❌ 致命问题: 仅网络延迟就需要 {estimated_total:.0f}ms!")
            print("   这会导致前端超时（通常 30s 超时）")
            print(f"   如果业务逻辑再耗时 100-200ms，总响应时间会超过 {estimated_total + 200:.0f}ms")
        elif estimated_total > 2000:
            print(f"\n⚠️  严重警告: 网络延迟 {estimated_total:.0f}ms 过高")
            print("   用户会明显感觉到延迟")
        elif estimated_total > 1000:
            print(f"\n⚠️  警告: 网络延迟 {estimated_total:.0f}ms 偏高")
            print("   需要优化以提升用户体验")
        else:
            print(f"\n✅ 网络延迟可接受 ({estimated_total:.0f}ms)")


async def main() -> None:
    """主函数"""
    print("\n" + "=" * 80)
    print("  Redis & PostgreSQL 连接性能诊断工具")
    print('  "如果你的数据库在火星，别指望它像本地一样快" - Linus')
    print("=" * 80)

    try:
        # 1. Redis 诊断
        redis_results = await measure_redis_latency()

        # 2. PostgreSQL 诊断
        db_results = await measure_postgresql_latency()

        # 3. API 性能分析
        await analyze_api_performance(redis_results, db_results)

        # 4. 总结
        print("\n" + "=" * 80)
        print("【Linus 的建议】")
        print("=" * 80)
        print("""
数据库性能的第一定律：网络延迟是你无法逃避的物理现实。

如果你的诊断显示高延迟：
  1. 不要试图"优化"数据库配置 - 物理距离是瓶颈
  2. 不要增加连接池 - 这只会让问题更糟
  3. 不要责怪数据库 - Redis 和 PostgreSQL 都很快

你应该做的：
  1. 使用本地或同城数据库（延迟从 200ms 降到 2ms）
  2. 减少网络往返次数（批量操作、JOIN、缓存）
  3. 接受现实：如果必须用远程数据库，就要承担延迟

"The best optimization is not doing the work at all." - Linus Torvalds

详细报告和解决方案请查看：docs/PERFORMANCE-DIAGNOSIS-REPORT.md
        """)

    except KeyboardInterrupt:
        print("\n\n用户中断")
    except Exception as e:
        print(f"\n❌ 诊断失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
