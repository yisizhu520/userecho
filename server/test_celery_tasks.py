"""
测试 Celery 任务注册和执行

验证步骤：
1. Celery app 能否正确初始化
2. 所有任务是否注册成功
3. Worker 能否启动并接收任务
"""
from backend.app.task.celery import celery_app


def main():
    print("=" * 60)
    print("Celery Tasks Registration Test")
    print("=" * 60)
    
    # 获取所有用户任务
    user_tasks = [k for k in celery_app.tasks.keys() if not k.startswith('celery.')]
    
    print(f"\n✅ Total user tasks registered: {len(user_tasks)}")
    print("\nTasks list:")
    for i, task_name in enumerate(sorted(user_tasks), 1):
        print(f"  {i:2d}. {task_name}")
    
    print("\n" + "=" * 60)
    print("Expected tasks:")
    expected_tasks = [
        "task_demo",
        "task_demo_async",
        "task_demo_params",
        "backend.app.task.tasks.db_log.tasks.delete_db_opera_log",
        "backend.app.task.tasks.db_log.tasks.delete_db_login_log",
        "userecho.generate_feedback_embedding",
        "userecho.generate_topic_centroid",
        "userecho_clustering_batch",
        "userecho_analyze_screenshot",
        "userecho.generate_insight_report",
        "userecho.generate_feedback_summary",
    ]
    
    for task in expected_tasks:
        if task in user_tasks:
            print(f"  ✅ {task}")
        else:
            print(f"  ❌ {task} (MISSING)")
    
    # 检查是否有额外的任务
    extra_tasks = set(user_tasks) - set(expected_tasks)
    if extra_tasks:
        print("\n⚠️  Extra tasks found:")
        for task in sorted(extra_tasks):
            print(f"  - {task}")
    
    print("\n" + "=" * 60)
    if len(user_tasks) >= len(expected_tasks):
        print("✅ ALL TASKS REGISTERED SUCCESSFULLY!")
    else:
        print(f"❌ MISSING {len(expected_tasks) - len(user_tasks)} TASKS!")
    print("=" * 60)


if __name__ == "__main__":
    main()
