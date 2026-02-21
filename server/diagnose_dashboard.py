
import asyncio
import os
import sys
from datetime import datetime, timedelta

# 添加项目根目录到 Path
sys.path.append('d:/workspace/indie/userecho/server')

from backend.app.userecho.service.dashboard_service import dashboard_service
from backend.database.db import async_db_session

async def diagnose():
    async with async_db_session() as db:
        tenant_id = 'test-tenant' # 或者从数据库找一个有效的
        # 尝试找一个有效的租户ID
        from sqlalchemy import text
        result = await db.execute(text("SELECT tenant_id FROM feedbacks LIMIT 1"))
        row = result.fetchone()
        if row:
            tenant_id = row[0]
            print(f"Using tenant_id: {tenant_id}")
        else:
            print("No tenant found, using default")

        print("--- Testing get_stats ---")
        try:
            stats = await dashboard_service.get_stats(db, tenant_id)
            import json
            # 检查是否有非 primitive 类型（除了列表和字典）
            def check_types(obj, path=''):
                if isinstance(obj, (str, int, float, bool, type(None))):
                    return
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        check_types(v, f"{path}.{k}")
                elif isinstance(obj, list):
                    for i, v in enumerate(obj):
                        check_types(v, f"{path}[{i}]")
                else:
                    print(f"Non-primitive at {path}: {type(obj)} - {obj}")

            check_types(stats)
            # print(json.dumps(stats, indent=2, default=str))
        except Exception as e:
            print(f"get_stats failed: {e}")

        print("--- Testing get_my_feedbacks ---")
        try:
            # 找一个有效的 submitter_id
            result = await db.execute(text("SELECT submitter_id FROM feedbacks WHERE submitter_id IS NOT NULL LIMIT 1"))
            row = result.fetchone()
            if row:
                user_id = row[0]
                print(f"Using user_id: {user_id}")
                my_feedbacks = await dashboard_service.get_my_feedbacks(db, tenant_id, user_id)
                # print(json.dumps(my_feedbacks, indent=2, default=str))
                check_types(my_feedbacks)
            else:
                print("No submitter found")
        except Exception as e:
            print(f"get_my_feedbacks failed: {e}")

if __name__ == '__main__':
    asyncio.run(diagnose())
