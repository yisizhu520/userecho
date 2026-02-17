"""修复 updated_time 为 NULL 的历史数据

由于之前 Schema 定义错误，导致已创建的数据 updated_time=NULL，
现在批量修复为 created_time（符合语义）
"""

import asyncio

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.userecho.model.customer import Customer
from backend.app.userecho.model.feedback import Feedback
from backend.app.userecho.model.priority_score import PriorityScore
from backend.app.userecho.model.tenant import Tenant
from backend.app.userecho.model.topic import Topic
from backend.common.log import log
from backend.database.db import async_engine


async def fix_updated_time():
    """修复所有表的 updated_time=NULL 记录"""
    tables = [
        ('topics', Topic),
        ('feedbacks', Feedback),
        ('customers', Customer),
        ('priority_scores', PriorityScore),
        ('tenants', Tenant),
    ]

    async with AsyncSession(async_engine) as db:
        total_fixed = 0

        for table_name, model in tables:
            try:
                # 将 updated_time=NULL 的记录设置为 created_time
                stmt = update(model).where(model.updated_time.is_(None)).values(updated_time=model.created_time)
                result = await db.execute(stmt)
                fixed = result.rowcount

                if fixed > 0:
                    log.info(f'Fixed {fixed} records in {table_name}')
                    total_fixed += fixed
                else:
                    log.debug(f'No records to fix in {table_name}')

            except Exception as e:
                log.error(f'Failed to fix {table_name}: {e}')

        await db.commit()
        log.info(f'Total fixed: {total_fixed} records')
        return total_fixed


async def main() -> None:
    """主函数"""
    log.info('Starting updated_time fix...')
    try:
        count = await fix_updated_time()
        log.info(f'✅ Fix completed: {count} records updated')
    except Exception as e:
        log.error(f'❌ Fix failed: {e}')
        raise


if __name__ == '__main__':
    asyncio.run(main())
