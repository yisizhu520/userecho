"""测试系统通知功能

验证新增的两个通知触发点：
1. 批量回复生成完成
2. 批量截图识别完成
"""

import asyncio

from backend.app.userecho.crud.crud_system_notification import crud_system_notification
from backend.database.db import async_db_session


async def test_notification_creation():
    """测试通知创建功能"""
    
    async with async_db_session() as db:
        async with db.begin():
            # 测试租户
            tenant_id = "test_tenant"
            
            print("\n" + "="*60)
            print("Test 1: Create topic completed notification")
            print("="*60)
            
            notification1 = await crud_system_notification.create_topic_completed_notification(
                db=db,
                tenant_id=tenant_id,
                topic_id="test_topic_123",
                topic_title="测试议题：增加批量功能",
                pending_count=15,
                user_id=None,  # 全员通知
            )
            print(f"[OK] Created: {notification1.title}")
            print(f"     Message: {notification1.message}")
            print(f"     Action URL: {notification1.action_url}")
            print(f"     Type: {notification1.type}")
            
            print("\n" + "="*60)
            print("Test 2: Create batch reply completed notification")
            print("="*60)
            
            notification2 = await crud_system_notification.create_batch_reply_completed_notification(
                db=db,
                tenant_id=tenant_id,
                topic_id="test_topic_456",
                topic_title="测试议题：优化用户体验",
                success_count=23,
                failed_count=2,
                user_id=None,
            )
            print(f"[OK] Created: {notification2.title}")
            print(f"     Message: {notification2.message}")
            print(f"     Action URL: {notification2.action_url}")
            print(f"     Extra data: {notification2.extra_data}")
            
            print("\n" + "="*60)
            print("Test 3: Create screenshot batch completed notification")
            print("="*60)
            
            notification3 = await crud_system_notification.create_screenshot_batch_completed_notification(
                db=db,
                tenant_id=tenant_id,
                total_count=50,
                success_count=48,
                failed_count=2,
                user_id=None,
            )
            print(f"[OK] Created: {notification3.title}")
            print(f"     Message: {notification3.message}")
            print(f"     Action URL: {notification3.action_url}")
            print(f"     Extra data: {notification3.extra_data}")
            
            print("\n" + "="*60)
            print("Test 4: Query all unread notifications")
            print("="*60)
            
            notifications = await crud_system_notification.get_user_notifications(
                db=db,
                tenant_id=tenant_id,
                user_id=1,  # 测试用户
                unread_only=True,
            )
            
            print(f"[OK] Found {len(notifications)} unread notifications:")
            for idx, notif in enumerate(notifications, 1):
                print(f"\n   {idx}. {notif.title}")
                print(f"      Message: {notif.message}")
                print(f"      Type: {notif.type}")
                print(f"      Is Read: {notif.is_read}")
            
            print("\n" + "="*60)
            print("ALL TESTS PASSED!")
            print("="*60)


if __name__ == "__main__":
    asyncio.run(test_notification_creation())
