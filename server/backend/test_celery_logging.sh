#!/bin/bash
# 测试 Celery worker 日志功能
#
# 验证目标：
# 1. Celery worker 启动后，logs 目录有文件生成
# 2. 任务执行时的日志能写入 logs/fba_error.log 和 logs/fba_access.log
# 3. 任务失败时的错误日志能正确记录

echo "===== Celery Worker 日志测试 ====="
echo ""

# 1. 清空旧日志（可选）
echo "[1] 清理旧日志文件..."
rm -f ../logs/fba_*.log
echo "    已清空 logs 目录"
echo ""

# 2. 启动 worker（后台运行 10 秒）
echo "[2] 启动 Celery worker（后台运行 10 秒）..."
bash ../start_celery_worker.sh &
WORKER_PID=$!
echo "    Worker PID: $WORKER_PID"
echo ""

# 3. 等待 worker 完全启动
echo "[3] 等待 worker 初始化..."
sleep 3
echo ""

# 4. 检查日志文件是否生成
echo "[4] 检查日志文件..."
if [ -f "../logs/fba_access.log" ]; then
    echo "    ✅ fba_access.log 已生成"
    echo "    文件大小: $(stat -c%s ../logs/fba_access.log 2>/dev/null || stat -f%z ../logs/fba_access.log 2>/dev/null || echo '未知') bytes"
else
    echo "    ❌ fba_access.log 未生成"
fi

if [ -f "../logs/fba_error.log" ]; then
    echo "    ✅ fba_error.log 已生成"
    echo "    文件大小: $(stat -c%s ../logs/fba_error.log 2>/dev/null || stat -f%z ../logs/fba_error.log 2>/dev/null || echo '未知') bytes"
else
    echo "    ❌ fba_error.log 未生成"
fi
echo ""

# 5. 触发一个测试任务（如果有的话）
# echo "[5] 触发测试任务..."
# python -c "from backend.app.task.tasks.userecho.tasks import generate_feedback_embedding_task; generate_feedback_embedding_task.delay('test-id', 'test content', 'test-tenant')"
# sleep 2
# echo ""

# 6. 查看日志内容（最后 10 行）
echo "[5] 查看日志内容（最后 10 行）..."
if [ -f "../logs/fba_access.log" ]; then
    echo "--- fba_access.log ---"
    tail -n 10 ../logs/fba_access.log
fi
echo ""

if [ -f "../logs/fba_error.log" ]; then
    echo "--- fba_error.log ---"
    tail -n 10 ../logs/fba_error.log
fi
echo ""

# 7. 停止 worker
echo "[6] 停止 Celery worker..."
kill $WORKER_PID 2>/dev/null
wait $WORKER_PID 2>/dev/null
echo "    Worker 已停止"
echo ""

echo "===== 测试完成 ====="
echo ""
echo "手动验证步骤："
echo "1. 启动 worker: bash start_celery_worker.sh"
echo "2. 触发一个任务（如创建反馈、聚类等）"
echo "3. 检查 logs/fba_error.log 和 logs/fba_access.log"
echo "4. 确认任务日志已写入文件"
