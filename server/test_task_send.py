"""
测试 Celery 任务发送

模拟发送一个聚类任务，观察日志输出
"""
import asyncio

from backend.app.task.celery import celery_app


def test_send_task():
    """测试发送任务到队列"""
    print("\n" + "=" * 60)
    print("Testing Task Send")
    print("=" * 60)
    
    # 测试发送聚类任务
    print("\n📤 Sending userecho_clustering_batch task...")
    
    try:
        result = celery_app.send_task(
            'userecho_clustering_batch',
            args=['test-tenant-id'],
            kwargs={'max_feedbacks': 10, 'force_recluster': False},
        )
        
        print(f"✅ Task sent successfully!")
        print(f"   Task ID: {result.id}")
        print(f"   Task Name: userecho_clustering_batch")
        print(f"   State: {result.state}")
        
        # 等待几秒钟看结果
        print(f"\n⏳ Waiting 5 seconds for task execution...")
        import time
        for i in range(5):
            time.sleep(1)
            print(f"   {i+1}s - State: {result.state}")
            if result.ready():
                print(f"   ✅ Task completed!")
                print(f"   Result: {result.result}")
                break
        else:
            print(f"   ⏸️  Task still pending/running")
            print(f"   You can check task status with: result.id = {result.id}")
        
    except Exception as e:
        print(f"❌ Failed to send task: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_send_task()
