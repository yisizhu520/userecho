"""
监控并自动清理长时间未提交的事务（防止死锁）

运行方式：
    python monitor_idle_transactions.py

作用：
1. 每30秒检查一次是否有 "idle in transaction" 状态的会话超过5分钟
2. 自动终止这些会话，防止死锁
3. 记录日志
"""
import asyncio
from datetime import timedelta
from sqlalchemy import text
from backend.database.db import async_db_session
from backend.common.log import log


async def check_and_kill_idle_transactions():
    """检查并终止长时间未提交的事务"""
    async with async_db_session() as db:
        # 查找所有 idle in transaction 超过5分钟的会话
        query = text("""
            SELECT 
                pid,
                usename,
                application_name,
                state,
                NOW() - state_change AS idle_duration,
                NOW() - query_start AS query_duration,
                query
            FROM pg_stat_activity
            WHERE state = 'idle in transaction'
              AND NOW() - state_change > INTERVAL '5 minutes'
              AND pid != pg_backend_pid()
            ORDER BY state_change
        """)
        
        result = await db.execute(query)
        rows = result.all()
        
        if not rows:
            log.debug("No idle transactions found")
            return 0
        
        killed_count = 0
        for row in rows:
            try:
                log.warning(
                    f"Found long idle transaction - PID: {row.pid}, "
                    f"User: {row.usename}, Idle: {row.idle_duration}, "
                    f"Query: {row.query[:100] if row.query else 'None'}"
                )
                
                # 终止这个会话
                kill_query = text(f"SELECT pg_terminate_backend({row.pid})")
                kill_result = await db.execute(kill_query)
                
                if kill_result.scalar():
                    log.info(f"Successfully killed idle transaction PID {row.pid}")
                    killed_count += 1
                else:
                    log.warning(f"Failed to kill PID {row.pid} (already gone?)")
                    
            except Exception as e:
                log.error(f"Error killing PID {row.pid}: {e}")
        
        return killed_count


async def monitor_loop():
    """持续监控循环"""
    log.info("=== Idle Transaction Monitor Started ===")
    log.info("Will check every 30 seconds for transactions idle > 5 minutes")
    
    while True:
        try:
            killed = await check_and_kill_idle_transactions()
            if killed > 0:
                log.warning(f"Killed {killed} idle transactions")
        except Exception as e:
            log.error(f"Error in monitoring loop: {e}")
        
        # 每30秒检查一次
        await asyncio.sleep(30)


if __name__ == "__main__":
    try:
        asyncio.run(monitor_loop())
    except KeyboardInterrupt:
        log.info("Monitor stopped by user")
