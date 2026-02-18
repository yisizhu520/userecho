# userecho 文档中心

欢迎来到 userecho 项目文档！本文档库已按照功能和用途重新组织，方便快速查找。

## 📁 文档结构

### 🏗️ Architecture（架构设计）
系统核心架构设计文档

#### 数据库设计 (`architecture/database/`)
- **complete-er-diagram.md** - 完整的 ER 图设计（MVP 版本）
- **database-redesign.md** - 数据库重新设计方案
- **database-design-qa.md** - 数据库设计问答
- **database_specification.md** - 数据库规范说明

#### 多租户架构 (`architecture/multi-tenant/`)
- **multi-tenant-user-model.md** - 多租户用户模型
- **tenant-config-system.md** - 租户配置系统
- **menu-permission-guide.md** - 菜单权限指南

#### 插件系统 (`architecture/plugin-system/`)
- **plugin-architecture.md** - 插件架构设计

#### 路由设计 (`architecture/`)
- **route-design.md** - 路由设计文档

---

### ⚡ Features（功能实现）
各项核心功能的实现文档

#### AI 聚类 (`features/ai-clustering/`)
- **clustering-implementation-review.md** - 聚类实现评审
- **clustering-refactor-plan.md** - 聚类重构计划
- **clustering-ui-interaction-design.md** - 聚类 UI 交互设计
- **clustering_uiux_design.md** - 聚类 UI/UX 设计
- **feedback-clustering-merge-flow.md** - 反馈聚类合并流程
- **clustering-config-test-guide.md** - 聚类配置测试指南

#### 搜索功能 (`features/search/`)
- **feedback-search-implementation.md** - 反馈搜索实现
- **topic-search-implementation.md** - 主题搜索实现
- **fulltext-search-index-guide.md** - 全文搜索索引指南
- **fulltext-search-quickstart.md** - 全文搜索快速入门
- **feedback-search-ui-fix.md** - 反馈搜索 UI 修复
- **search-mode-animation.md** - 搜索模式动画

#### 截图识别 (`features/screenshot/`)
- **screenshot-async-implementation.md** - 截图异步实现
- **screenshot-recognition-implementation.md** - 截图识别实现
- **screenshot-menu-setup-complete.md** - 截图菜单设置完成

#### 工作空间 (`features/workspace/`)
- **workspace-deployment-guide.md** - 工作空间部署指南
- **workspace-implementation-summary.md** - 工作空间实现总结
- **workspace-testing-guide.md** - 工作空间测试指南

---

### 📚 Guides（操作指南）
开发、部署和配置相关指南

#### 部署指南 (`guides/deployment/`)
- **pgvector-deployment-checklist.md** - pgvector 部署检查清单
- **pgvector-migration-guide.md** - pgvector 迁移指南

#### 开发指南 (`guides/development/`)
- **debug-middleware-guide.md** - 调试中间件指南
- **logging-best-practices.md** - 日志最佳实践
- **feedback-ui-simplification-summary.md** - 反馈 UI 简化总结
- **insights-implementation-summary.md** - 洞察实现总结
- **priority-scoring-implementation-summary.md** - 优先级评分实现总结
- **badge-implementation.md** - 徽章实现

#### 配置指南 (`guides/configuration/`)
- **storage-configuration.md** - 存储配置
- **storage-implementation-summary.md** - 存储实现总结
- **storage-quick-start.md** - 存储快速入门
- **redis-config.md** - Redis 配置
- **celery-db-result-backend.md** - Celery 数据库结果后端
- **upstash-redis-setup.md** - Upstash Redis 设置

#### AI 提供商 (`guides/ai-provider/`)
- **README-VOLCENGINE.md** - 火山引擎说明
- **configuration.md** - AI 提供商配置
- **embedding-support.md** - 嵌入支持
- **quick-start.md** - 快速入门
- **troubleshooting.md** - 故障排除
- **volcengine-config-example.md** - 火山引擎配置示例
- **volcengine-endpoint-setup.md** - 火山引擎端点设置
- **volcengine-quickstart.md** - 火山引擎快速入门
- **volcengine-vision-setup.md** - 火山引擎视觉设置

---

### 🧪 Testing（测试文档）
测试相关指南和文档

- **mvp-testing-guide.md** - MVP 测试指南
- **badge-display-test-guide.md** - 徽章显示测试指南
- **test-users-guide.md** - 测试用户指南

---

### 📋 Planning（规划文档）
产品规划、路线图和竞品分析

#### 路线图 (`planning/roadmap/`)
- **roadmap.md** - 产品路线图
- **china-canny-roadmap.md** - 中国版 Canny 路线图
- **china-canny-technical-plan.md** - 中国版 Canny 技术计划
- **mvp.md** - MVP 规划

#### 竞品分析 (`planning/competitor-analysis/`)
- **canny-competitor-analysis.md** - Canny 竞品分析

#### 其他规划 (`planning/`)
- **wechat-feedback-collect.md** - 微信反馈收集

---

### 🗄️ Archive（已归档）
过时或历史文档归档

- **data-model-comparison.md** - 数据模型对比（已过时）
- **database-design.md** - 旧版数据库设计（已过时）
- **clustering-test-guide.md** - 旧版聚类测试指南（已过时）
- **PERFORMANCE-DIAGNOSIS-REPORT.md** - 性能诊断报告（历史记录）
- **performance-fixes.md** - 性能修复（历史记录）
- **performance-optimization-remote-db.md** - 远程数据库性能优化（历史记录）

---

## 🚀 快速导航

### 新手入门
1. 查看 [MVP 规划](planning/roadmap/mvp.md) 了解项目整体方向
2. 阅读 [完整 ER 图](architecture/database/complete-er-diagram.md) 理解数据模型
3. 参考 [MVP 测试指南](testing/mvp-testing-guide.md) 开始测试

### 功能开发
- **开发 AI 功能**：查看 `features/ai-clustering/` 目录
- **开发搜索功能**：查看 `features/search/` 目录
- **配置存储**：查看 `guides/configuration/storage-*.md`

### 部署运维
- **数据库部署**：查看 `guides/deployment/pgvector-*.md`
- **配置 Redis**：查看 `guides/configuration/redis-config.md`
- **AI 提供商配置**：查看 `guides/ai-provider/` 目录

---

## 📝 文档维护

本文档库于 **2025-12-31** 重新组织，遵循以下原则：
- ✅ 按功能和用途分类，而非按时间或作者
- ✅ 保留所有有价值的文档，过时文档移至 `archive/`
- ✅ 提供清晰的导航和索引
- ✅ 定期更新和维护

如有文档缺失或分类不当，请及时反馈！
