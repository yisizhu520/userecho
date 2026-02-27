"""
测试 Celery App 初始化
用于诊断 worker 为什么没有日志输出
"""

import sys
import os

print("=" * 60)
print("Celery App 初始化测试")
print("=" * 60)
print()

# 确保在正确的目录
print(f"当前工作目录: {os.getcwd()}")
print(f"Python 路径: {sys.executable}")
print()

# 步骤 1: 导入 celery
print("步骤 1: 导入 celery 模块...")
try:
    import celery

    print(f"✅ celery 版本: {celery.__version__}")
except Exception as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)

# 步骤 2: 导入 celery_app
print("\n步骤 2: 导入 celery_app...")
try:
    from backend.app.task.celery import celery_app

    print("✅ celery_app 导入成功")
except Exception as e:
    print(f"❌ 导入失败: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

# 步骤 3: 检查配置
print("\n步骤 3: 检查 celery_app 配置...")
try:
    print(f"  broker_url: {celery_app.conf.broker_url}")
    print(f"  result_backend: {celery_app.conf.result_backend}")
    print(f"  task_always_eager: {celery_app.conf.task_always_eager}")
    print("✅ 配置读取成功")
except Exception as e:
    print(f"❌ 配置读取失败: {e}")
    sys.exit(1)

# 步骤 4: 检查任务注册
print("\n步骤 4: 检查任务注册...")
try:
    user_tasks = [k for k in celery_app.tasks.keys() if not k.startswith("celery.")]
    print(f"✅ 注册了 {len(user_tasks)} 个用户任务")
    for task in user_tasks[:5]:  # 只显示前 5 个
        print(f"  - {task}")
    if len(user_tasks) > 5:
        print(f"  ... 还有 {len(user_tasks) - 5} 个")
except Exception as e:
    print(f"❌ 任务检查失败: {e}")
    sys.exit(1)

# 步骤 5: 测试 broker 连接
print("\n步骤 5: 测试 broker 连接...")
try:
    conn = celery_app.connection()
    conn.ensure_connection(max_retries=3)
    print("✅ Broker 连接成功")
    conn.release()
except Exception as e:
    print(f"❌ Broker 连接失败: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ 所有测试通过！Celery App 初始化正常")
print("=" * 60)
print("\n如果这个脚本通过，但 worker 仍无法启动，")
print("问题可能出在:")
print("  1. supervisord 配置")
print("  2. 环境变量差异")
print("  3. 文件权限")
print("  4. worker pool 特定问题")
