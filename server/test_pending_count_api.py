"""测试待确认主题数量 API

快速测试脚本，验证新增的 pending-count 接口是否正常工作
"""

import asyncio
import sys

from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from backend.database.db_postgres import async_session

from backend.app.userecho.service import topic_service


async def test_pending_count():
    """测试获取待确认主题数量"""

    # 测试租户 ID（假设存在）
    test_tenant_id = 'default_tenant'

    print(f'🔍 测试获取租户 {test_tenant_id} 的待确认主题数量...')

    async with async_session() as db:
        try:
            count = await topic_service.get_pending_count(db=db, tenant_id=test_tenant_id)

            print(f'✅ 成功获取待确认主题数量: {count}')

            # 验证返回值类型
            assert isinstance(count, int), f'返回值类型错误: {type(count)}'
            assert count >= 0, f'数量不能为负数: {count}'

            print('✅ 数据验证通过')

            return count

        except Exception as e:
            print(f'❌ 测试失败: {e}')
            raise


async def main() -> None:
    """主测试函数"""
    print('=' * 60)
    print('测试待确认主题数量 API')
    print('=' * 60)

    try:
        count = await test_pending_count()

        print('\n' + '=' * 60)
        print('测试总结')
        print('=' * 60)
        print('✅ 所有测试通过')
        print(f'📊 待确认主题数量: {count}')

    except Exception as e:
        print(f'\n❌ 测试失败: {e}')
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
