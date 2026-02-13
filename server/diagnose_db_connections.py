"""
数据库连接诊断脚本
检查连接池状态、活跃连接数、是否有连接泄漏
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from backend.database.db import async_engine
from backend.common.log import log


async def diagnose_connections():
    """诊断数据库连接状态"""
    log.info("=" * 80)
    log.info("🔍 开始诊断数据库连接状态")
    log.info("=" * 80)
    
    # 1. 连接池配置
    pool = async_engine.pool
    log.info(f"\n📊 连接池配置:")
    log.info(f"  - pool_size (基础连接数): {pool.size()}")
    log.info(f"  - overflow (溢出连接数): {pool.overflow()}")
    log.info(f"  - timeout (超时时间): {pool._timeout}s")
    log.info(f"  - recycle (回收时间): {pool._recycle}s")
    
    # 2. 当前连接状态
    log.info(f"\n🔗 当前连接状态:")
    log.info(f"  - 已签出连接数 (checked out): {pool.checkedout()}")
    log.info(f"  - 池中可用连接数 (checked in): {pool.checkedin()}")
    
    # 3. 计算总连接数
    checked_out = pool.checkedout()
    checked_in = pool.checkedin()
    
    # 注意：overflow() 返回的是当前溢出数量（可能为负）
    # 真正的最大连接数应该从配置获取
    max_overflow = getattr(pool, '_max_overflow', 20)  # 默认20
    total_possible = pool.size() + max_overflow
    
    log.info(f"\n📈 连接使用情况:")
    log.info(f"  - 理论最大连接数: {total_possible} (pool_size + max_overflow)")
    log.info(f"  - 当前总连接数: {checked_out + checked_in}")
    if total_possible > 0:
        log.info(f"  - 使用率: {checked_out}/{total_possible} ({checked_out/total_possible*100:.1f}%)")
    else:
        log.error(f"  - ❌ 连接池配置异常！total_possible = {total_possible}")
    
    # 4. 判断是否有问题
    log.info(f"\n⚠️  问题诊断:")
    
    if checked_out >= total_possible * 0.9:
        log.error(f"  ❌ 连接池接近满载！({checked_out}/{total_possible})")
        log.error(f"     可能原因:")
        log.error(f"     1. 有数据库连接未正确释放（连接泄漏）")
        log.error(f"     2. 并发请求过多，连接池太小")
        log.error(f"     3. 存在慢查询长时间占用连接")
    elif checked_out >= total_possible * 0.7:
        log.warning(f"  ⚠️  连接使用率较高 ({checked_out}/{total_possible})")
        log.warning(f"     建议监控是否持续增长")
    else:
        log.info(f"  ✅ 连接池状态正常")
    
    # 5. 测试数据库连接
    log.info(f"\n🧪 测试数据库连接:")
    try:
        async with async_engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            row = result.fetchone()
            if row and row[0] == 1:
                log.info(f"  ✅ 数据库连接正常")
            else:
                log.error(f"  ❌ 数据库查询返回异常")
    except Exception as e:
        log.error(f"  ❌ 数据库连接失败: {e}")
    
    # 6. 查询数据库侧的连接数（PostgreSQL）
    log.info(f"\n🗄️  数据库服务器连接状态:")
    try:
        async with async_engine.connect() as conn:
            from sqlalchemy import text
            
            # PostgreSQL 查询
            result = await conn.execute(text("""
                SELECT 
                    COUNT(*) as total_connections,
                    COUNT(*) FILTER (WHERE state = 'active') as active_connections,
                    COUNT(*) FILTER (WHERE state = 'idle') as idle_connections,
                    COUNT(*) FILTER (WHERE state = 'idle in transaction') as idle_in_transaction
                FROM pg_stat_activity
                WHERE datname = current_database()
            """))
            row = result.fetchone()
            
            log.info(f"  - 总连接数: {row[0]}")
            log.info(f"  - 活跃连接: {row[1]}")
            log.info(f"  - 空闲连接: {row[2]}")
            log.info(f"  - 事务中空闲: {row[3]}")
            
            if row[3] > 0:
                log.warning(f"  ⚠️  发现 {row[3]} 个空闲事务连接，可能存在连接泄漏！")
                
                # 查看这些连接的详情
                result2 = await conn.execute(text("""
                    SELECT 
                        pid,
                        usename,
                        application_name,
                        state,
                        query_start,
                        state_change,
                        query
                    FROM pg_stat_activity
                    WHERE datname = current_database()
                    AND state = 'idle in transaction'
                    ORDER BY state_change
                    LIMIT 5
                """))
                
                log.warning(f"\n  空闲事务连接详情（最多显示5个）:")
                for r in result2:
                    log.warning(f"    PID={r[0]} | User={r[1]} | App={r[2]}")
                    log.warning(f"    Query Start: {r[4]}")
                    log.warning(f"    Last Query: {r[6][:100]}...")
                    log.warning(f"    ---")
            
    except Exception as e:
        log.warning(f"  ⚠️  无法查询数据库连接状态: {e}")
    
    log.info("=" * 80)
    log.info("✅ 诊断完成")
    log.info("=" * 80)


async def main():
    try:
        await diagnose_connections()
    except Exception as e:
        log.error(f"诊断过程出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理资源
        await async_engine.dispose()


if __name__ == "__main__":
    # 需要导入 text
    from sqlalchemy import text
    asyncio.run(main())

