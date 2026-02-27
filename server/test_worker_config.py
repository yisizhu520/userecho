"""
Celery Worker 启动调试脚本

显示详细的启动日志和配置信息
"""
import sys

# 确保 worker 参数在 argv 中，触发信号处理器
sys.argv = ['celery', 'worker', '-A', 'backend.app.task.celery:celery_app']

from backend.app.task.celery import celery_app

print("\n" + "=" * 60)
print("Celery Worker Configuration")
print("=" * 60)

print(f"\n📋 App Name: {celery_app.main}")
print(f"📋 Broker: {celery_app.conf.broker_url}")
print(f"📋 Result Backend: {celery_app.conf.result_backend}")
print(f"📋 Timezone: {celery_app.conf.timezone}")

# 检查 broker 连接
print("\n🔌 Testing Broker Connection...")
try:
    # 尝试获取 broker 连接
    with celery_app.connection_or_acquire() as conn:
        conn.default_channel.queue_declare(
            queue='celery',  # 默认队列名
            durable=True,
            auto_delete=False,
        )
    print("✅ Broker connection successful!")
except Exception as e:
    print(f"❌ Broker connection failed: {e}")
    import traceback
    traceback.print_exc()

# 打印注册的任务
user_tasks = [k for k in celery_app.tasks.keys() if not k.startswith('celery.')]
print(f"\n📝 Registered Tasks ({len(user_tasks)}):")
for i, task_name in enumerate(sorted(user_tasks), 1):
    print(f"   {i:2d}. {task_name}")

print("\n" + "=" * 60)
print("✅ Configuration Check Complete")
print("=" * 60)

print("\n💡 To start worker, run:")
print("   cd server && .venv/Scripts/python.exe -m celery -A backend.app.task.celery:celery_app worker -P custom -c 4 -l info")
