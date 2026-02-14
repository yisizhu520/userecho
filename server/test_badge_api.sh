#!/bin/bash
# 快速测试 badge API 端点

echo "🔍 测试 Badge API 端点..."
echo "================================"

# 检查后端是否运行
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ 后端服务未运行！请先启动后端服务。"
    echo "   cd server && source .venv/Scripts/activate && python run.py"
    exit 1
fi

echo "✅ 后端服务运行中"
echo ""

# 测试 API 端点（不带认证，仅测试路由是否正确）
echo "📡 测试路由顺序..."
echo "请求: GET /api/v1/app/topics/stats/pending-count"
echo ""

RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" http://localhost:8000/api/v1/app/topics/stats/pending-count)
HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_CODE:/d')

echo "响应状态: $HTTP_CODE"
echo "响应内容: $BODY"
echo ""

if [ "$HTTP_CODE" = "401" ] || [ "$HTTP_CODE" = "403" ]; then
    echo "✅ 路由正确（需要认证，这是预期行为）"
    echo "   状态码 $HTTP_CODE 表示路由匹配成功，但需要登录"
elif [ "$HTTP_CODE" = "404" ]; then
    echo "❌ 路由错误！API 端点未找到"
    echo "   检查 server/backend/app/userecho/api/v1/topic.py"
    echo "   确保 /stats/pending-count 在 /{topic_id} 之前定义"
elif [ "$HTTP_CODE" = "200" ]; then
    echo "✅ API 端点工作正常！"
    echo "   返回数据: $BODY"
else
    echo "⚠️  未预期的状态码: $HTTP_CODE"
fi

echo ""
echo "================================"
echo "提示：完整测试需要登录并获取 JWT token"
echo "      详见: docs/testing/badge-display-test-guide.md"
