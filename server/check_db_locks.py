"""检查数据库锁和活跃事务"""
import asyncio
from sqlalchemy import text
from backend.database.db import async_db_session


async def check_locks():
    async with async_db_session() as db:
        # 1. 检查所有活跃的锁
        lock_query = text("""
            SELECT 
                pid,
                usename,
                application_name,
                state,
                query,
                pg_blocking_pids(pid) as blocking_pids,
                NOW() - query_start AS duration
            FROM pg_stat_activity
            WHERE state != 'idle'
              AND pid != pg_backend_pid()
            ORDER BY duration DESC
        """)
        
        result = await db.execute(lock_query)
        rows = result.all()
        
        print("=== 活跃事务 ===")
        if rows:
            for row in rows:
                print(f"PID: {row.pid}, User: {row.usename}, App: {row.application_name}")
                print(f"  State: {row.state}, Duration: {row.duration}")
                print(f"  Query: {row.query[:100] if row.query else 'None'}")
                print(f"  Blocking PIDs: {row.blocking_pids}")
                print()
        else:
            print("没有活跃事务")
        
        # 2. 检查锁定的 feedback 记录
        feedback_lock_query = text("""
            SELECT 
                l.pid,
                l.mode,
                l.granted,
                a.usename,
                a.application_name,
                a.state,
                NOW() - a.query_start AS duration
            FROM pg_locks l
            JOIN pg_stat_activity a ON l.pid = a.pid
            JOIN pg_class c ON l.relation = c.oid
            WHERE c.relname = 'feedback'
              AND l.pid != pg_backend_pid()
            ORDER BY a.query_start
        """)
        
        result2 = await db.execute(feedback_lock_query)
        rows2 = result2.all()
        
        print("\n=== Feedback 表的锁 ===")
        if rows2:
            for row in rows2:
                print(f"PID: {row.pid}, Mode: {row.mode}, Granted: {row.granted}")
                print(f"  User: {row.usename}, App: {row.application_name}")
                print(f"  State: {row.state}, Duration: {row.duration}")
                print()
        else:
            print("Feedback 表没有被锁定")


if __name__ == "__main__":
    asyncio.run(check_locks())
