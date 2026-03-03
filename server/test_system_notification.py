"""测试系统提醒功能

用于验证通知系统修复是否成功
"""

import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.userecho.crud import crud_system_notification
from backend.database.db import async_db_session


async def create_test_notification():
    """创建一个测试通知"""
    async with async_db_session.begin() as db:
        # 使用你的租户 ID（从数据库中查询）
        tenant_id = "your-tenant-id-here"  # 请替换为实际的租户 ID
        
        # 创建测试通知
        notification = await crud_system_notification.create_topic_completed_notification(
            db=db,
            tenant_id=tenant_id,
            topic_id="test-topic-id",
            topic_title="测试需求：通知系统修复验证",
            pending_count=5,
            user_id=None,  # 全员通知
        )
        
        print(f"✅ 成功创建测试通知:")
        print(f"  - ID: {notification.id}")
        print(f"  - 标题: {notification.title}")
        print(f"  - 消息: {notification.message}")
        print(f"  - 跳转链接: {notification.action_url}")
        print(f"\n现在可以刷新前端页面，应该能在右上角看到通知了！")


async def list_notifications():
    """列出所有通知"""
    async with async_db_session.begin() as db:
        tenant_id = "your-tenant-id-here"  # 请替换为实际的租户 ID
        user_id = 1  # 当前用户 ID
        
        notifications = await crud_system_notification.get_user_notifications(
            db=db,
            tenant_id=tenant_id,
            user_id=user_id,
            skip=0,
            limit=20,
            unread_only=False,
        )
        
        print(f"📋 找到 {len(notifications)} 条通知:")
        for n in notifications:
            status = "未读" if not n.is_read else "已读"
            print(f"  [{status}] {n.title} - {n.message}")


if __name__ == "__main__":
    print("🔍 测试系统提醒功能\n")
    print("=" * 60)
    
    # 运行测试
    # asyncio.run(create_test_notification())
    # asyncio.run(list_notifications())
    
    print("\n使用说明：")
    print("1. 修改脚本中的 tenant_id 为你的实际租户 ID")
    print("2. 取消注释想要运行的函数")
    print("3. 运行: cd server && python test_system_notification.py")
    print("=" * 60)
