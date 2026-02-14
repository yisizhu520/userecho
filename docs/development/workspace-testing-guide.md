# 工作台功能测试指南

## 测试概述

本文档用于测试 UserEcho 工作台页面的功能实现。

## 后端测试

### 1. 重启后端服务器

新的 dashboard API 需要重启后端服务器才能生效。

```bash
# 停止当前运行的服务器（Ctrl+C）
# 然后重新启动
cd server
source .venv/Scripts/activate
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

### 2. 测试统计 API

使用 curl 或浏览器测试统计 API：

```bash
# 方式1：使用 curl（需要替换 TOKEN）
curl -X GET "http://localhost:8000/api/v1/app/dashboard/stats" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# 方式2：直接在浏览器中访问（需要先登录）
# http://localhost:8000/api/v1/app/dashboard/stats
```

**预期返回结构：**

```json
{
  "code": 200,
  "data": {
    "feedback_stats": {
      "total": 120,
      "pending": 30,
      "weekly_count": 15
    },
    "topic_stats": {
      "total": 25,
      "pending": 8,
      "completed": 10,
      "weekly_count": 5
    },
    "urgent_topics": [
      {
        "id": "xxx",
        "title": "登录闪退",
        "feedback_count": 5,
        "priority_score": 9.5,
        "category": "bug",
        "status": "pending"
      }
    ],
    "top_topics": [
      {
        "id": "xxx",
        "title": "加载速度慢",
        "feedback_count": 8,
        "category": "performance",
        "status": "in_progress"
      }
    ],
    "weekly_trend": [
      { "date": "2025-12-22", "count": 10 },
      { "date": "2025-12-23", "count": 15 }
    ]
  }
}
```

### 3. 检查 API 文档

访问 Swagger 文档确认新端点已注册：

```
http://localhost:8000/docs
```

查找 **UserEcho - 工作台** 标签下的 `GET /api/v1/app/dashboard/stats` 端点。

---

## 前端测试

### 1. 启动前端开发服务器

```bash
cd front/apps/web-antd
pnpm dev
```

### 2. 访问工作台页面

在浏览器中访问：

```
http://localhost:5555/app/dashboard/workspace
```

### 3. 功能测试清单

**页面加载测试：**
- [ ] 页面成功加载，无白屏或报错
- [ ] 顶部显示欢迎信息和用户头像
- [ ] 描述栏显示待处理需求数和待聚类反馈数

**指标卡片测试：**
- [ ] 显示 4 个指标卡片（总反馈、本周新增、总需求、已完成）
- [ ] 数字从后端 API 正确加载
- [ ] 数字格式正确（无 NaN 或 undefined）

**紧急需求列表测试：**
- [ ] 左侧显示紧急需求卡片
- [ ] 列表项显示需求标题、反馈数量、优先级分数
- [ ] 分类和状态标签颜色正确
- [ ] 点击列表项能跳转到需求详情页

**趋势图测试：**
- [ ] 左侧下方显示 7 天反馈趋势图
- [ ] 图表正确渲染（无空白或错误）
- [ ] X 轴显示日期（MM-DD 格式）
- [ ] Y 轴显示数量
- [ ] 鼠标悬停显示 tooltip

**快捷操作测试：**
- [ ] 右侧顶部显示快捷操作卡片
- [ ] 显示 4 个快捷操作按钮
- [ ] 点击"导入反馈"跳转到 `/app/feedback/import`
- [ ] 点击"录入反馈"跳转到 `/app/feedback/list`
- [ ] 点击"查看需求"跳转到 `/app/topic/list`
- [ ] 点击"客户管理"跳转到 `/app/customer`

**TOP 需求主题测试：**
- [ ] 右侧下方显示 TOP 需求主题卡片
- [ ] 列表项按反馈数量降序排列
- [ ] 前三名显示金银铜徽章（黄、灰、橙色）
- [ ] 第 4-5 名显示灰色徽章
- [ ] 点击列表项能跳转到需求详情页

**响应式测试：**
- [ ] 在大屏幕上左右布局正确（3/5 和 2/5 分栏）
- [ ] 在小屏幕上自动切换为上下布局

---

## 性能测试

### 1. API 响应时间

后端统计 API 的响应时间应该 < 500ms

```bash
# 使用 curl 测试响应时间
time curl -X GET "http://localhost:8000/api/v1/app/dashboard/stats" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### 2. 前端加载时间

- [ ] 页面首次加载时间 < 1 秒
- [ ] API 请求完成后立即渲染数据
- [ ] 无明显的闪烁或布局抖动

---

## 类型检查

运行前端类型检查，确保无类型错误：

```bash
cd front/apps/web-antd
pnpm check:type
```

预期结果：无错误输出

---

## 常见问题排查

### 1. 后端 API 404 错误

**原因：** 后端服务器未重启，dashboard 路由未加载

**解决：** 重启后端服务器

### 2. 前端页面空白

**原因：** API 请求失败或数据格式不匹配

**解决：** 
1. 打开浏览器开发者工具 Console 查看错误
2. 检查 Network 面板确认 API 请求是否成功
3. 检查返回的数据格式是否与 TypeScript 类型定义一致

### 3. 趋势图不显示

**原因：** weekly_trend 数据为空数组

**解决：** 确保数据库中有最近 7 天的反馈数据

### 4. 点击列表项无跳转

**原因：** 路由配置错误

**解决：** 检查 `/app/topic/detail/:id` 路由是否正确配置

---

## 测试完成标准

所有测试项通过，满足以下条件：
- ✅ 后端 API 返回正确的数据结构
- ✅ 前端页面正常加载，所有卡片显示正常
- ✅ 所有交互功能（点击跳转）正常工作
- ✅ 响应式布局在不同屏幕尺寸下正常
- ✅ API 响应时间 < 500ms
- ✅ 前端页面加载时间 < 1 秒
- ✅ `pnpm check:type` 无错误

---

**文档创建时间:** 2025-12-28  
**功能版本:** v1.0
