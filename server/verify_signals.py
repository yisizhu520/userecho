"""
快速验证脚本：检查信号处理器是否正常工作

这个脚本会：
1. 导入 celery_app（触发信号处理器注册）
2. 显示预期的日志输出
"""

print("\n" + "=" * 70)
print("步骤 1: 导入 Celery App（观察信号处理器注册日志）")
print("=" * 70)

from backend.app.task.celery import celery_app

print("\n" + "=" * 70)
print("步骤 2: 验证信号处理器")
print("=" * 70)

# 检查关键配置
print(f"\n✅ Celery App 名称: {celery_app.main}")
print(f"✅ Broker URL: {celery_app.conf.broker_url}")
print(f"✅ Result Backend: {celery_app.conf.result_backend}")

# 检查任务注册
user_tasks = [k for k in celery_app.tasks.keys() if not k.startswith("celery.")]
print(f"✅ 已注册用户任务数: {len(user_tasks)}")

print("\n" + "=" * 70)
print("预期日志检查清单：")
print("=" * 70)

expected_logs = [
    "[Celery Init] Registering signal handlers...",
    "[Celery Signals] Installing signal handlers...",
    "[Celery Signals] ✅ Signal handlers installed successfully",
    "[Celery Init] Signal handlers registered",
]

print("\n请确认上面的输出中包含以下日志：")
for log in expected_logs:
    print(f"  ☐ {log}")

print("\n" + "=" * 70)
print("下一步：重启 Celery Worker")
print("=" * 70)
print("""
如果上面的日志都出现了，说明信号处理器已经注册。

现在重启你的 Celery Worker，你应该会看到：

1. 启动时的日志：
   [Celery Worker] 🔧 Worker initializing...
   [Celery Worker] 🚀 Worker READY! Waiting for tasks...

2. 发送任务时的日志：
   [Celery Publish] 📤 Publishing task: xxx
   [Celery Publish] ✅ Published task: xxx

3. 执行任务时的日志：
   [Celery Worker] 📥 Received task: xxx
   [Celery Worker] ▶️  Starting task: xxx
   [Celery Worker] ⏹️  Finished task: xxx
   [Celery Worker] ✅ Task succeeded: xxx

如果看不到 Worker 相关日志，检查：
- Worker 进程是否真的重启了？
- Supervisord 配置的启动命令是否正确？
- Worker 日志输出到哪里了？（stdout? 文件?）
""")

print("=" * 70)
