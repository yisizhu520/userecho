# Feedalyze MVP 功能测试指南

> **版本:** v1.0  
> **创建日期:** 2025-12-21  
> **用途:** 手把手指导 MVP 阶段的功能测试

---

## 📋 文档概览

本文档将指导你完成 Feedalyze MVP 的完整功能测试，包括：
- 环境准备与检查
- 核心业务流程测试
- 异常场景测试
- 性能基准验证
- 测试结果记录

**预计测试时间:** 2-3 小时

---

## 🚀 快速启动指南（5分钟）

如果你已经配置好环境，只是想快速启动服务进行测试：

### 后端启动

```bash
# 1. 进入 server 目录
cd server

# 2. 激活虚拟环境
source .venv/Scripts/activate  # Windows Git Bash
# .venv\Scripts\activate.bat   # Windows CMD
# source .venv/bin/activate     # Linux/macOS

# 3. 启动服务（注意：必须在 server 目录，不是 backend 子目录）
source .venv/Scripts/activate && python -m backend.run

# 看到以下输出表示成功（约 2-3 秒启动）：
# INFO: Uvicorn running on http://127.0.0.1:8000
# INFO: Application startup complete
```

**✅ 关于 Redis（已配置 Upstash）：**
- **项目已配置 Upstash Redis**（云端托管，无需本地启动）
- 服务器启动时会自动连接 Upstash Redis（约 2-3 秒）
- 如需测试 Redis 连接，运行：
  ```bash
  cd server
  source .venv/Scripts/activate
  python test_upstash_redis.py
  ```
- 如果想切换到本地 Redis，修改 `.env` 中的 `REDIS_URL` 为空，并配置 `REDIS_HOST`

### 前端启动

```bash
# 新开一个终端窗口
cd front

# 启动开发服务器
pnpm dev:antd

# 看到以下输出表示成功：
# Local: http://localhost:5555
```

### 验证

- 访问后端文档：http://localhost:8000/docs
- 访问前端页面：http://localhost:5555
- 登录用户名：`admin`（密码根据你的配置）

**如果启动失败，请跳转到"第一部分：测试前准备"进行完整的环境检查。**

---

## 第一部分：测试前准备 (15分钟)

### 1.0 依赖安装（首次运行必做）

在开始测试之前，必须确保所有依赖已正确安装：

```bash
# 1. 后端依赖安装
cd server

# 如果没有虚拟环境，创建一个
# python -m venv .venv  # 或使用 uv venv

# 激活虚拟环境
source .venv/Scripts/activate  # Windows Git Bash
# 或 .venv\Scripts\activate.bat  # Windows CMD
# 或 source .venv/bin/activate   # Linux/macOS

# 安装依赖（推荐使用 uv，更快）
uv sync

# 或使用传统 pip
pip install -r requirements.txt

# 验证依赖完整性
python check_dependencies.py
# 预期输出: ✅ 所有第三方依赖都已正确声明!

# 2. 前端依赖安装
cd ../front

# 安装依赖
pnpm install

# 验证安装
pnpm list vxe-table ant-design-vue
```

**依赖清单（参考）：**

后端核心依赖：
- FastAPI 生态：`fastapi`, `uvicorn`, `pydantic`
- 数据库：`sqlalchemy`, `alembic`, `asyncpg`/`pymysql`
- AI 功能：`openai`, `numpy`, `scikit-learn`, `pandas`
- 其他：`pyyaml`, `python-dotenv`, `redis`, `celery`

前端核心依赖：
- Vue 生态：`vue`, `vue-router`, `pinia`
- UI 框架：`ant-design-vue`, `vxe-table`
- 工具库：`axios`, `dayjs`, `lodash-es`

**预期结果：**
- ✅ 后端虚拟环境已激活
- ✅ 所有 Python 依赖已安装（无 ModuleNotFoundError）
- ✅ 依赖检查脚本通过
- ✅ 前端 node_modules 已生成
- ✅ 前端依赖验证通过

**故障排查：**
```bash
# 如果 uv sync 失败，尝试清理后重装
cd server
rm -rf .venv
uv venv
uv sync

# 如果 pnpm install 失败
cd front
rm -rf node_modules
rm pnpm-lock.yaml
pnpm install
```

---

### 1.1 环境检查清单

#### ✅ 后端服务检查

**⚠️ 重要提示：**
- 必须先激活虚拟环境
- 必须从 `server` 目录启动（不是 `server/backend`）

```bash
# 1. 进入 server 目录并激活虚拟环境
cd server
source .venv/Scripts/activate  # Windows Git Bash
# 或 .venv\Scripts\activate.bat  # Windows CMD
# 或 source .venv/bin/activate   # Linux/macOS

# 2. 检查依赖是否完整（可选，首次运行推荐）
source .venv/Scripts/activate && python check_dependencies.py
# 预期输出: ✅ 所有第三方依赖都已正确声明!

# 3. 检查数据库连接
cd backend
python -c "from database.db import async_engine; print('Database OK')"
cd ..

# 4. 检查环境变量
python -c "from backend.core.conf import settings; print(f'AI Provider: {settings.AI_DEFAULT_PROVIDER}')"

# 5. 检查 AI API 密钥（不显示完整密钥）
python -c "from backend.core.conf import settings; key = settings.DEEPSEEK_API_KEY or settings.OPENAI_API_KEY or settings.GLM_API_KEY; print(f'API Key: {key[:10]}...{key[-4:]}' if key else 'NOT SET')"

# 6. 启动后端服务（确保在 server 目录下）
source .venv/Scripts/activate && python -m backend.run
# 预期输出: 
#   INFO: Uvicorn running on http://127.0.0.1:8000
#   INFO: Application startup complete
# 访问: http://localhost:8000/docs 应该能看到 Swagger 文档
```

**预期结果:**
- ✅ 虚拟环境已激活（命令提示符前显示 `(.venv)`）
- ✅ 所有依赖已安装
- ✅ 数据库连接成功
- ✅ AI API 密钥已配置
- ✅ 服务启动在 8000 端口
- ✅ `/docs` 可以访问并显示 Feedalyze 相关接口

**常见启动问题：**

| 错误信息 | 原因 | 解决方案 |
|---------|------|---------|
| `ModuleNotFoundError: No module named 'backend'` | 在错误的目录运行 | 确保在 `server` 目录，不是 `server/backend` |
| `ModuleNotFoundError: No module named 'numpy'` | 依赖未安装 | 运行 `uv sync` 或 `pip install -r requirements.txt` |
| `ModuleNotFoundError: No module named 'openai'` | 缺失 AI 相关依赖 | 运行 `uv sync` 重新安装依赖 |
| 虚拟环境找不到命令 | 未激活虚拟环境 | 先执行 `source .venv/Scripts/activate` |
| ~~`Redis TimeoutError`~~ (已修复) | ~~Redis 未启动~~ | **已优化**：现在即使 Redis 未启动也能秒级启动 |

#### ✅ 前端服务检查

```bash
# 1. 进入前端目录
cd front

# 2. 检查依赖
pnpm list vxe-table ant-design-vue

# 3. 启动前端服务
pnpm dev:antd
# 预期输出: Local: http://localhost:5555
```

**预期结果:**
- ✅ 前端服务启动在 5555 端口
- ✅ 浏览器自动打开登录页面

#### ✅ 数据库检查

```bash
# 连接数据库（根据你的数据库类型选择）
# MySQL:
mysql -u root -p fba

# PostgreSQL:
psql -U postgres -d fba
```

执行检查 SQL：
```sql
-- 1. 检查 Feedalyze 表是否存在
SHOW TABLES LIKE '%tenant%';
SHOW TABLES LIKE '%feedback%';
SHOW TABLES LIKE '%topic%';

-- 2. 检查默认租户是否存在
SELECT * FROM tenants WHERE id = 'default-tenant';

-- 3. 检查 sys_user 是否有 tenant_id
SELECT id, username, tenant_id FROM sys_user LIMIT 5;
```

**预期结果:**
- ✅ 7 张 Feedalyze 表存在（tenants, customers, feedbacks, topics, priority_scores, status_history, manual_adjustments）
- ✅ 默认租户存在且状态为 'active'
- ✅ sys_user 表有 tenant_id 列

---

### 1.2 测试数据准备

#### 创建测试租户和用户

```sql
-- 1. 确保默认租户存在
INSERT INTO tenants (id, name, status, created_time, updated_time) 
VALUES ('default-tenant', '默认租户', 'active', NOW(), NOW())
ON DUPLICATE KEY UPDATE name = '默认租户';

-- 2. 更新现有用户的 tenant_id
UPDATE sys_user SET tenant_id = 'default-tenant' WHERE tenant_id IS NULL;

-- 3. 查看测试用户
SELECT id, username, tenant_id FROM sys_user WHERE username = 'admin';
```

#### 准备测试 Excel 文件

创建文件 `test_feedbacks.xlsx`，包含以下内容：

| 反馈内容 | 客户名称 | 客户类型 | 商业价值 | 紧急程度 | 提交时间 |
|---------|---------|---------|---------|---------|---------|
| 登录页面加载速度太慢，每次都要等10秒以上 | 小米科技 | strategic | 10 | high | 2025-01-15 |
| 登录太慢了，希望能优化一下 | 华为技术 | major | 8 | medium | 2025-01-16 |
| 能否支持导出PDF格式的报表？ | 字节跳动 | strategic | 9 | low | 2025-01-17 |
| 希望能一键导出所有数据为PDF | 阿里巴巴 | major | 7 | medium | 2025-01-18 |
| 数据导出功能不够强大，建议增加PDF | 腾讯科技 | paid | 5 | low | 2025-01-19 |
| 手机端界面需要适配横屏模式 | 小米科技 | strategic | 10 | low | 2025-01-20 |
| 建议优化移动端的横屏显示效果 | 华为技术 | major | 8 | low | 2025-01-21 |
| 能否添加深色主题模式？护眼 | OPPO | paid | 4 | low | 2025-01-22 |
| 希望增加暗黑模式，晚上用眼睛累 | vivo | paid | 4 | low | 2025-01-23 |
| 夜间模式很有必要，建议尽快上线 | 荣耀 | trial | 2 | low | 2025-01-24 |

**Excel 列说明:**
- 反馈内容 (必填): 用户的原始反馈文本
- 客户名称 (必填): 客户公司名称
- 客户类型: strategic/major/paid/trial（默认 paid）
- 商业价值: 1-10 的数字（默认 5）
- 紧急程度: high/medium/low（默认 medium）
- 提交时间: 日期格式（默认当前时间）

**下载测试文件:**
将上表复制到 Excel，保存为 `test_feedbacks.xlsx`，放在桌面或已知位置。

---

## 第二部分：核心功能测试 (60分钟)

### 测试用例 1: 用户登录与权限验证

#### 步骤：
1. 打开浏览器访问 `http://localhost:5555`
2. 输入用户名 `admin`，密码（你设置的密码）
3. 点击登录

#### 预期结果：
- ✅ 登录成功，跳转到首页
- ✅ 左侧菜单栏显示 "Feedalyze" 菜单组
- ✅ 子菜单包含：反馈管理、需求主题、客户管理

#### 检查点：
```bash
# 查看浏览器 Console (F12)
# 应该没有报错信息
# Network 面板应该看到 /api/v1/auth/login 返回 200
```

#### 故障排查：
- ❌ 登录失败：检查用户名密码是否正确
- ❌ 菜单不显示：检查路由配置是否注册（`router/routes/modules/userecho.ts`）
- ❌ 权限错误：确认用户 tenant_id 不为空

---

### 测试用例 2: 客户管理 - CRUD 操作

#### 2.1 创建客户

**步骤：**
1. 点击左侧菜单 "Feedalyze" → "客户管理"
2. 点击工具栏 "新建客户" 按钮
3. 填写表单：
   - 客户名称: 测试客户A
   - 客户类型: 战略客户 (strategic)
   - 商业价值: 10
   - 行业: 互联网
   - 联系人: 张三
   - 邮箱: zhangsan@test.com
4. 点击 "确定"

**预期结果：**
- ✅ 弹出成功提示 "创建成功"
- ✅ 表格中新增一行记录
- ✅ 客户类型显示为蓝色标签 "战略客户"
- ✅ 商业价值显示为 10

**数据库验证：**
```sql
SELECT * FROM customers WHERE name = '测试客户A' AND tenant_id = 'default-tenant';
-- 应该返回 1 条记录
-- 检查 id、tenant_id、created_time 字段不为空
```

#### 2.2 编辑客户

**步骤：**
1. 找到刚创建的 "测试客户A"
2. 点击操作列的 "编辑" 按钮
3. 修改商业价值为 9
4. 点击 "确定"

**预期结果：**
- ✅ 弹出成功提示 "更新成功"
- ✅ 表格中商业价值更新为 9

#### 2.3 删除客户

**步骤：**
1. 点击 "测试客户A" 的 "删除" 按钮
2. 确认删除

**预期结果：**
- ✅ 弹出成功提示 "删除成功"
- ✅ 表格中记录消失

**数据库验证：**
```sql
SELECT deleted_at FROM customers WHERE name = '测试客户A';
-- deleted_at 应该不为 NULL（软删除）
```

---

### 测试用例 3: 反馈管理 - 手动创建

#### 步骤：
1. 点击左侧菜单 "反馈管理"
2. 点击 "新建反馈" 按钮
3. 填写表单：
   - 反馈内容: 这是一条测试反馈，用于验证手动创建功能
   - 来源: 手动输入
   - 紧急程度: 高
   - 匿名提交者: 测试用户
   - 提交时间: 选择今天
4. 点击 "确定"

#### 预期结果：
- ✅ 弹出成功提示 "创建成功"
- ✅ 表格中新增一行
- ✅ 反馈内容显示完整
- ✅ AI 摘要列显示 "生成中..." 或已生成的摘要（如果 AI 调用成功）

#### 数据库验证：
```sql
SELECT id, content, ai_summary, embedding 
FROM feedbacks 
WHERE content LIKE '%测试反馈%' 
  AND tenant_id = 'default-tenant';
-- 检查记录是否存在
-- ai_summary 应该有内容（如果 AI 调用成功）
-- embedding 应该是一个向量（JSON 格式或二进制）
```

#### 检查 AI 调用：
```bash
# 查看后端日志
# 应该看到类似输出：
# INFO: Calling AI API for summary generation...
# INFO: Summary generated successfully
```

#### 故障排查：
- ❌ AI 摘要为空：检查 DEEPSEEK_API_KEY 是否配置正确
- ❌ 创建失败：查看后端日志，检查数据库连接
- ❌ Embedding 为空：检查 AI API 是否支持 embedding 接口

---

### 测试用例 4: 反馈管理 - Excel 批量导入 ⭐

**这是 MVP 的核心功能，需要重点测试！**

#### 4.1 正常导入流程

**步骤：**
1. 在反馈列表页，点击工具栏 "导入反馈" 按钮
2. 在弹出的对话框中，点击 "选择文件"
3. 选择准备好的 `test_feedbacks.xlsx`
4. 点击 "开始导入"
5. 等待进度条完成（可能需要 10-30 秒）

**预期结果：**
- ✅ 进度条显示导入进度
- ✅ 导入完成后显示成功数量（如：成功 10 条，失败 0 条）
- ✅ 表格自动刷新，显示新导入的反馈
- ✅ 每条反馈都有 AI 摘要
- ✅ 客户列表自动创建了 Excel 中的客户（小米科技、华为技术等）

**数据库验证：**
```sql
-- 1. 检查导入的反馈数量
SELECT COUNT(*) FROM feedbacks WHERE tenant_id = 'default-tenant';
-- 应该 >= 10

-- 2. 检查自动创建的客户
SELECT name, customer_type, business_value FROM customers WHERE tenant_id = 'default-tenant';
-- 应该看到：小米科技、华为技术、字节跳动等

-- 3. 检查反馈是否关联了客户
SELECT f.content, c.name as customer_name
FROM feedbacks f
LEFT JOIN customers c ON f.customer_id = c.id
WHERE f.tenant_id = 'default-tenant'
LIMIT 5;
-- 客户名称应该不为空
```

#### 4.2 测试导入验证

**准备一个错误的 Excel 文件 `test_feedbacks_error.xlsx`：**

| 反馈内容 | 客户名称 | 客户类型 | 商业价值 |
|---------|---------|---------|---------|
| （留空） | 测试客户 | strategic | 10 |
| 正常反馈 | 测试客户 | invalid_type | 99 |

**步骤：**
1. 导入 `test_feedbacks_error.xlsx`

**预期结果：**
- ✅ 第一行导入失败（反馈内容为空）
- ✅ 第二行导入失败或使用默认值（客户类型无效、商业价值超出范围）
- ✅ 显示错误信息列表
- ✅ 成功的数据仍然被导入

---

### 测试用例 5: AI 聚类功能 ⭐⭐⭐

**这是 MVP 的最核心功能！**

#### 5.1 触发聚类

**前提条件：**
- 已导入至少 10 条反馈
- 反馈内容有相似性（如测试数据中的登录慢、PDF 导出、深色主题）

**步骤：**
1. 在反馈列表页，点击工具栏 "AI 聚类" 按钮
2. 在确认对话框中点击 "确定"
3. 等待聚类完成（可能需要 30-60 秒）

**预期结果：**
- ✅ 显示 "聚类任务已提交" 提示
- ✅ 后台开始执行聚类（查看后端日志）
- ✅ 聚类完成后显示 "聚类完成，生成了 X 个主题" 提示

**后端日志检查：**
```bash
# 应该看到类似输出：
# INFO: Starting clustering for tenant: default-tenant
# INFO: Found 10 unclustered feedbacks
# INFO: Extracting embeddings...
# INFO: Running DBSCAN clustering...
# INFO: Generated 3 clusters
# INFO: Creating topics...
# INFO: Topic created: 登录性能优化
# INFO: Topic created: PDF导出功能
# INFO: Topic created: 深色主题需求
# INFO: Clustering completed successfully
```

#### 5.2 验证聚类结果

**数据库验证：**
```sql
-- 1. 检查生成的主题数量
SELECT COUNT(*) FROM topics WHERE tenant_id = 'default-tenant';
-- 应该 >= 1（具体数量取决于反馈相似度）

-- 2. 查看主题详情
SELECT id, title, feedback_count, avg_urgency, status
FROM topics
WHERE tenant_id = 'default-tenant'
ORDER BY feedback_count DESC;
-- title 应该是有意义的中文标题（AI 生成）
-- feedback_count 应该 > 0
-- status 应该是 'pending'

-- 3. 检查反馈是否关联了主题
SELECT topic_id, COUNT(*) as cnt
FROM feedbacks
WHERE tenant_id = 'default-tenant' AND topic_id IS NOT NULL
GROUP BY topic_id;
-- 每个 topic_id 应该至少有 2 条反馈（CLUSTERING_MIN_SAMPLES=2）
```

**前端验证：**
1. 回到反馈列表
2. 检查 "所属主题" 列是否有值
3. 点击主题标签，应该跳转到主题详情页

---

### 测试用例 6: 需求主题管理

#### 6.1 查看主题列表

**步骤：**
1. 点击左侧菜单 "需求主题"
2. 查看主题列表

**预期结果：**
- ✅ 显示聚类生成的主题（如：登录性能优化、PDF导出功能等）
- ✅ 每个主题显示卡片，包含：
  - 主题标题
  - 反馈数量
  - 平均紧急程度
  - 当前状态（待处理）
  - 创建时间
- ✅ 卡片可以点击进入详情

#### 6.2 主题详情页 ⭐

**步骤：**
1. 点击任意主题卡片
2. 进入主题详情页

**预期结果：**
- ✅ **主题信息卡片** 显示：
  - 主题标题
  - 反馈数量
  - 平均紧急程度
  - 当前状态
  - 创建时间、更新时间
  
- ✅ **关联反馈列表** 显示：
  - 该主题下的所有反馈
  - 每条反馈的内容、客户、提交时间
  - 可以点击查看反馈详情
  
- ✅ **优先级评分卡片** 显示：
  - 评分表单（影响范围、业务价值、实现成本、紧急系数）
  - 计算后的优先级分数
  
- ✅ **状态变更历史** 显示：
  - 时间线展示状态变更记录
  - 包含：旧状态 → 新状态、变更时间、操作人

#### 6.3 主题评分 ⭐

**步骤：**
1. 在主题详情页，找到 "优先级评分" 卡片
2. 填写评分表单：
   - 影响范围: 8
   - 业务价值: 9
   - 实现成本: 3
   - 紧急系数: 1.5
3. 点击 "计算评分" 按钮

**预期结果：**
- ✅ 显示计算后的优先级分数
- ✅ 公式：(影响 × 价值) / 成本 × 紧急系数 = (8 × 9) / 3 × 1.5 = 36
- ✅ 评分保存成功提示
- ✅ 返回主题列表，该主题的优先级分数已更新

**数据库验证：**
```sql
SELECT topic_id, impact, value, cost, urgency_factor, final_score
FROM priority_scores
WHERE topic_id = '主题ID';
-- final_score 应该 = 36
```

#### 6.4 更新主题状态 ⭐

**步骤：**
1. 在主题详情页，点击 "更新状态" 按钮
2. 选择新状态：进行中 (in_progress)
3. 填写备注：开始开发登录优化功能
4. 点击 "确定"

**预期结果：**
- ✅ 状态更新成功提示
- ✅ 主题状态显示为 "进行中"
- ✅ 状态变更历史增加一条记录
- ✅ 记录显示：待处理 → 进行中，备注：开始开发登录优化功能

**数据库验证：**
```sql
-- 检查主题状态
SELECT id, title, status FROM topics WHERE id = '主题ID';
-- status 应该是 'in_progress'

-- 检查状态历史
SELECT old_status, new_status, note, created_time
FROM status_history
WHERE topic_id = '主题ID'
ORDER BY created_time DESC
LIMIT 1;
-- 应该有一条新记录
```

---

### 测试用例 7: 筛选与搜索

#### 7.1 反馈列表筛选

**步骤：**
1. 回到反馈列表页
2. 使用工具栏的筛选功能：
   - 按主题筛选：选择 "登录性能优化"
   - 按紧急程度筛选：选择 "高"

**预期结果：**
- ✅ 表格只显示符合条件的反馈
- ✅ 筛选条件可以组合使用
- ✅ 清除筛选后恢复全部数据

#### 7.2 主题列表排序

**步骤：**
1. 在主题列表页
2. 点击 "按优先级排序" 按钮

**预期结果：**
- ✅ 主题按优先级分数降序排列
- ✅ 已评分的主题排在前面
- ✅ 未评分的主题排在后面

---

## 第三部分：异常场景测试 (30分钟)

### 测试用例 8: AI API 失败处理

#### 8.1 模拟 AI API 失败

**步骤：**
1. 停止后端服务
2. 编辑 `.env` 文件，将 `DEEPSEEK_API_KEY` 改为无效值
3. 重启后端服务
4. 创建一条新反馈

**预期结果：**
- ✅ 反馈创建成功（不因 AI 失败而失败）
- ✅ AI 摘要字段为空或显示 "生成失败"
- ✅ 后端日志显示 AI API 调用失败的警告
- ✅ 不影响后续操作

**恢复：**
将 API Key 改回正确值，重启服务

---

### 测试用例 9: 并发操作测试

#### 步骤：
1. 打开两个浏览器标签页，都登录同一账号
2. 标签页A：触发聚类
3. 立即在标签页B：再次触发聚类

**预期结果：**
- ✅ 第二次聚类被拒绝或等待第一次完成
- ✅ 不会生成重复的主题
- ✅ 系统不会崩溃

---

### 测试用例 10: 数据边界测试

#### 10.1 导入空文件

**步骤：**
1. 创建一个空的 Excel 文件（只有表头，没有数据）
2. 尝试导入

**预期结果：**
- ✅ 显示 "文件为空" 或 "没有可导入的数据"
- ✅ 不报错

#### 10.2 导入超大文件

**步骤：**
1. 创建一个包含 1000 行数据的 Excel 文件
2. 尝试导入

**预期结果：**
- ✅ 如果超过 `IMPORT_MAX_FILE_SIZE`，显示文件过大错误
- ✅ 如果未超过，正常导入（可能较慢）

#### 10.3 特殊字符处理

**步骤：**
1. 创建反馈，内容包含特殊字符：
   ```
   测试<script>alert('xss')</script>反馈
   包含emoji的反馈 😀🎉🚀
   超长文本... (复制一段 5000 字的文本)
   ```

**预期结果：**
- ✅ 特殊字符被正确转义（不触发 XSS）
- ✅ Emoji 正常显示
- ✅ 超长文本被截断或正常保存

---

## 第四部分：性能基准测试 (20分钟)

### 测试用例 11: 性能指标验证

#### 11.1 导入性能测试

**目标:** 导入 100 条反馈 < 5 秒（不含 AI 调用）

**步骤：**
1. 准备 100 行数据的 Excel 文件
2. 开始计时
3. 导入文件
4. 记录完成时间

**测量方法：**
```bash
# 查看后端日志中的时间戳
# 或使用浏览器 Network 面板查看接口响应时间
```

**预期结果：**
- ✅ 纯数据导入时间 < 5 秒
- ✅ 包含 AI 调用的总时间 < 60 秒（取决于 AI API 速度）

#### 11.2 聚类性能测试

**目标:** AI 聚类 100 条反馈 < 30 秒

**步骤：**
1. 确保有 100 条未聚类的反馈
2. 开始计时
3. 触发聚类
4. 等待完成，记录时间

**预期结果：**
- ✅ 聚类完成时间 < 30 秒
- ✅ 生成的主题数量合理（5-15 个）

#### 11.3 列表加载性能

**目标:** 列表加载 < 1 秒

**步骤：**
1. 打开浏览器开发者工具 (F12)
2. 切换到 Network 面板
3. 访问反馈列表页
4. 查看接口响应时间

**预期结果：**
- ✅ GET /api/v1/userecho/feedbacks 响应时间 < 1000ms
- ✅ 前端渲染时间 < 500ms

---

## 第五部分：多租户隔离测试 (15分钟)

### 测试用例 12: 租户数据隔离

**⚠️ 注意:** MVP 阶段使用硬编码 'default-tenant'，此测试需要手动修改数据库数据

#### 步骤：
```sql
-- 1. 创建第二个测试租户
INSERT INTO tenants (id, name, status, created_time, updated_time)
VALUES ('test-tenant-2', '测试租户2', 'active', NOW(), NOW());

-- 2. 创建一条属于 test-tenant-2 的反馈
INSERT INTO feedbacks (id, tenant_id, content, source, submitted_at, created_time, updated_time)
VALUES (UUID(), 'test-tenant-2', '这是租户2的反馈', 'manual', NOW(), NOW(), NOW());

-- 3. 查询验证
SELECT tenant_id, COUNT(*) FROM feedbacks GROUP BY tenant_id;
-- 应该看到两个租户的数据
```

**前端验证：**
1. 刷新反馈列表页
2. 应该只看到 'default-tenant' 的反馈
3. 不应该看到 'test-tenant-2' 的反馈

**数据库验证：**
```sql
-- API 查询应该自动添加 tenant_id 过滤
-- 检查 API 日志，确认所有查询都包含 tenant_id 条件
```

---

## 第六部分：测试结果记录

### 测试检查清单

将测试结果记录在下表：

| 测试用例 | 测试时间 | 状态 | 备注 |
|---------|---------|------|------|
| 1. 用户登录 | ______ | ✅❌ | __________ |
| 2. 客户管理 CRUD | ______ | ✅❌ | __________ |
| 3. 手动创建反馈 | ______ | ✅❌ | __________ |
| 4. Excel 批量导入 | ______ | ✅❌ | __________ |
| 5. AI 聚类 | ______ | ✅❌ | __________ |
| 6. 主题管理 | ______ | ✅❌ | __________ |
| 7. 筛选与搜索 | ______ | ✅❌ | __________ |
| 8. AI API 失败处理 | ______ | ✅❌ | __________ |
| 9. 并发操作 | ______ | ✅❌ | __________ |
| 10. 数据边界 | ______ | ✅❌ | __________ |
| 11. 性能基准 | ______ | ✅❌ | __________ |
| 12. 多租户隔离 | ______ | ✅❌ | __________ |

### MVP 验收标准

- [ ] **功能完整性**
  - [ ] 导入功能正常
  - [ ] AI 聚类生成主题
  - [ ] 主题评分计算正确
  - [ ] 状态管理可用
  
- [ ] **性能指标**
  - [ ] 导入 100 条反馈 < 5 秒
  - [ ] AI 聚类 100 条反馈 < 30 秒
  - [ ] 列表加载 < 1 秒
  
- [ ] **准确性**
  - [ ] 聚类准确率 > 80% (手动评估)
  - [ ] AI 摘要质量可接受
  - [ ] 主题标题有意义
  
- [ ] **稳定性**
  - [ ] AI API 失败不影响核心功能
  - [ ] 并发操作不产生脏数据
  - [ ] 异常输入不导致崩溃
  
- [ ] **安全性**
  - [ ] 多租户数据隔离有效
  - [ ] XSS 注入被防御
  - [ ] API 需要认证

---

## 第七部分：常见问题排查

### 问题 0: 后端启动失败 - 缺少依赖 ⭐

**现象:** 启动后端时报错 `ModuleNotFoundError: No module named 'xxx'`

**常见缺失的依赖包:**
- `numpy` - 聚类算法需要
- `scikit-learn` (导入为 `sklearn`) - DBSCAN 聚类
- `openai` - AI API 客户端
- `pandas` - Excel 导入
- `pyyaml` (导入为 `yaml`) - 配置文件解析
- `python-dotenv` (导入为 `dotenv`) - 环境变量加载

**快速修复：**
```bash
cd server
source .venv/Scripts/activate

# 方法 1: 使用 uv 同步（推荐）
uv sync

# 方法 2: 使用 pip 安装
pip install -r requirements.txt

# 验证依赖
python check_dependencies.py
```

**根本原因分析：**

这些依赖在代码中被使用，但之前未在 `pyproject.toml` 中声明。已修复：
- ✅ 添加了 `numpy>=1.26.0`
- ✅ 添加了 `scikit-learn>=1.5.0`
- ✅ 添加了 `openai>=1.67.0`
- ✅ 添加了 `pandas>=2.2.0`
- ✅ 添加了 `pyyaml>=6.0.3`
- ✅ 添加了 `python-dotenv>=1.2.1`
- ✅ 添加了 `typing-extensions>=4.15.0`

**预防措施：**

项目现在包含 `check_dependencies.py` 脚本，可以自动检查所有导入的包是否已声明：

```bash
cd server
python check_dependencies.py
# 输出: ✅ 所有第三方依赖都已正确声明!
```

如果输出显示缺失依赖，需要在 `pyproject.toml` 的 `dependencies` 中添加它们，然后运行 `uv sync`。

---

### 问题 1: 导入 Excel 失败

**现象:** 上传文件后报错 "文件格式不支持"

**排查步骤:**
```bash
# 1. 检查文件扩展名
ls -la test_feedbacks.xlsx

# 2. 检查后端配置
python -c "from backend.core.conf import settings; print(settings.IMPORT_ALLOWED_EXTENSIONS)"

# 3. 查看后端日志
tail -f logs/app.log
```

**可能原因:**
- 文件扩展名不在白名单中
- 文件损坏或格式错误
- 文件大小超过限制

---

### 问题 2: AI 聚类不生成主题

**现象:** 聚类完成但主题数量为 0

**排查步骤:**
```sql
-- 1. 检查反馈是否有 embedding
SELECT id, content, embedding FROM feedbacks WHERE embedding IS NOT NULL LIMIT 5;

-- 2. 检查聚类配置
-- 后端代码中查看 CLUSTERING_MIN_SAMPLES 和 CLUSTERING_SIMILARITY_THRESHOLD
```

```python
# 在 Python 中测试聚类
from backend.utils.clustering import clustering_engine
import numpy as np

# 准备测试数据
embeddings = np.random.rand(10, 768)
labels = clustering_engine.cluster(embeddings)
print(f"Cluster labels: {labels}")
# 应该输出聚类标签，如 [0, 0, 1, 1, -1, 2, 2, -1, 3, 3]
# -1 表示噪声点
```

**可能原因:**
- 反馈数量太少（< CLUSTERING_MIN_SAMPLES）
- 反馈相似度太低（< CLUSTERING_SIMILARITY_THRESHOLD）
- Embedding 为空或格式错误

**解决方案:**
- 调低 `CLUSTERING_SIMILARITY_THRESHOLD` (如 0.75 → 0.6)
- 增加更多相似的反馈
- 检查 AI API 是否正常生成 embedding

---

### 问题 3: 前端页面空白

**现象:** 访问 Feedalyze 页面显示空白或加载失败

**排查步骤:**
```bash
# 1. 查看浏览器 Console 错误
# F12 → Console 面板

# 2. 检查 API 接口是否正常
curl http://localhost:8000/api/v1/userecho/feedbacks

# 3. 检查路由配置
cat front/apps/web-antd/src/router/routes/modules/userecho.ts

# 4. 类型检查
cd front
pnpm type-check
```

**可能原因:**
- API 接口返回 401/403（权限问题）
- 路由配置错误
- TypeScript 编译错误
- 组件引入路径错误

---

### 问题 4: 优先级分数计算错误

**现象:** 评分后显示的分数不正确

**排查步骤:**
```python
# 手动计算验证
impact = 8
value = 9
cost = 3
urgency_factor = 1.5

final_score = (impact * value) / cost * urgency_factor
print(f"Expected: {final_score}")  # 应该是 36.0
```

```sql
-- 检查数据库中的评分
SELECT topic_id, impact, value, cost, urgency_factor, final_score
FROM priority_scores
WHERE topic_id = '主题ID';
-- 对比计算结果
```

**可能原因:**
- 后端计算公式错误
- 数据类型转换问题（整数除法）
- 前端显示格式化错误

---

### 问题 5: 状态更新后历史记录未生成

**现象:** 更新主题状态后，状态历史为空

**排查步骤:**
```sql
-- 检查状态历史表
SELECT * FROM status_history 
WHERE topic_id = '主题ID' 
ORDER BY created_time DESC;
-- 应该有记录

-- 检查触发器或 Service 代码
-- 确认 topic_service.update_status_with_history 方法被调用
```

**可能原因:**
- Service 层未正确记录历史
- 数据库事务回滚
- API 调用的不是带历史记录的方法

---

## 第八部分：测试完成后的行动

### 通过验收的下一步

如果所有测试用例通过，MVP 验收标准达成：

1. **更新文档**
   - 标记 `implementation-checklist.md` 中的测试任务为 ✅
   - 记录测试结果和发现的问题
   
2. **准备演示**
   - 整理测试数据
   - 准备功能演示脚本
   - 截图关键页面
   
3. **规划下一步**
   - 识别优化点
   - 收集用户反馈
   - 规划下一版本功能

### 未通过验收的行动

如果存在关键问题：

1. **问题分类**
   - P0: 阻塞发布（如数据丢失、系统崩溃）
   - P1: 影响体验（如性能慢、UI 错乱）
   - P2: 可接受的缺陷（如边界情况）
   
2. **修复优先级**
   - 立即修复 P0 问题
   - 评估 P1 问题的修复时间
   - P2 问题记录到 backlog
   
3. **回归测试**
   - 修复后重新执行相关测试
   - 确保修复不引入新问题

---

## 附录：测试报告模板

```markdown
# Feedalyze MVP 测试报告

**测试人员:** ________  
**测试日期:** 2025-12-21  
**测试环境:**
- 操作系统: Windows 10
- 浏览器: Chrome 120
- 后端版本: v1.0
- 前端版本: v1.0

## 测试概况

- 总测试用例: 12
- 通过: __
- 失败: __
- 阻塞: __

## 关键发现

### 主要问题
1. [问题描述]
2. [问题描述]

### 优化建议
1. [建议内容]
2. [建议内容]

## 性能数据

| 指标 | 目标 | 实际 | 状态 |
|------|------|------|------|
| 导入 100 条 | < 5s | __s | ✅❌ |
| 聚类 100 条 | < 30s | __s | ✅❌ |
| 列表加载 | < 1s | __s | ✅❌ |

## 验收结论

- [ ] 通过验收，可以发布
- [ ] 有缺陷但可接受
- [ ] 需要修复后重新测试

**签字:** ________  
**日期:** ________
```

---

**祝测试顺利！**

如有问题，请查看：
- `docs/database-design.md` - 数据库设计文档
- `docs/template-adaptation-plan.md` - 功能设计文档
- `docs/roadmap.md` - 项目规划文档
- 后端日志: `server/backend/logs/app.log`
- 前端控制台: 浏览器 F12 → Console

**问题反馈:** 将问题记录到项目 Issue 或联系开发团队
