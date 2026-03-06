"""触发指定看板的聚类"""
import asyncio
import sys
sys.path.insert(0, '.')

BOARD_ID = '67cce548-293e-4d3e-80da-f1bbdb91ceb5'

async def main():
    from backend.database.db import async_db_session
    from sqlalchemy import text

    # 获取 tenant_id
    async with async_db_session() as db:
        r = await db.execute(text(
            'SELECT t.id FROM boards b JOIN tenants t ON t.id = b.tenant_id WHERE b.id = :bid'
        ), {'bid': BOARD_ID})
        row = r.fetchone()
        if not row:
            print('ERROR: board not found')
            return
        tenant_id = str(row[0])
        print(f'tenant_id: {tenant_id}')

    # 触发聚类
    from backend.app.userecho.service.clustering_service import clustering_service
    async with async_db_session() as db:
        result = await clustering_service.trigger_clustering(
            db=db,
            tenant_id=tenant_id,
            board_ids=[BOARD_ID],
            force_recluster=False,
        )
        print('Result:', result)

asyncio.run(main())
