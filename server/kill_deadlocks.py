"""终止所有死锁的数据库连接"""
import asyncio
from sqlalchemy import text
from backend.database.db import async_db_session


async def kill_deadlocked_sessions():
    async with async_db_session() as db:
        # 终止所有这些死锁的会话
        pids_to_kill = [11325, 11359, 11433, 11613, 11788, 12367, 12672]
        
        for pid in pids_to_kill:
            try:
                query = text(f"SELECT pg_terminate_backend({pid})")
                result = await db.execute(query)
                killed = result.scalar()
                if killed:
                    print(f"✅ 成功终止 PID {pid}")
                else:
                    print(f"⚠️ PID {pid} 已经不存在或无法终止")
            except Exception as e:
                print(f"❌ 终止 PID {pid} 失败: {e}")
        
        await db.commit()
        print("\n所有死锁会话已处理完毕")


if __name__ == "__main__":
    asyncio.run(kill_deadlocked_sessions())
