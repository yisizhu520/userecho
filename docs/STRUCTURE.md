# userecho 文档目录结构

```
docs/
│
├── 📄 README.md                                    # 文档中心索引
├── 📄 REORGANIZATION-SUMMARY.md                    # 重组总结
│
├── 🏗️ architecture/                                # 架构设计
│   ├── 📄 route-design.md                          # 路由设计
│   │
│   ├── 💾 database/                                # 数据库设计
│   │   ├── complete-er-diagram.md                  # 完整 ER 图（MVP）
│   │   ├── database-redesign.md                    # 数据库重设计
│   │   ├── database-design-qa.md                   # 设计问答
│   │   └── database_specification.md               # 数据库规范
│   │
│   ├── 👥 multi-tenant/                            # 多租户架构
│   │   ├── multi-tenant-user-model.md              # 用户模型
│   │   ├── tenant-config-system.md                 # 配置系统
│   │   └── menu-permission-guide.md                # 菜单权限
│   │
│   └── 🔌 plugin-system/                           # 插件系统
│       └── plugin-architecture.md                  # 插件架构
│
├── ⚡ features/                                     # 功能实现
│   │
│   ├── 🤖 ai-clustering/                           # AI 聚类
│   │   ├── clustering-implementation-review.md     # 实现评审
│   │   ├── clustering-refactor-plan.md             # 重构计划
│   │   ├── clustering-ui-interaction-design.md     # UI 交互设计
│   │   ├── clustering_uiux_design.md               # UI/UX 设计
│   │   ├── feedback-clustering-merge-flow.md       # 合并流程
│   │   └── clustering-config-test-guide.md         # 配置测试
│   │
│   ├── 🔍 search/                                  # 搜索功能
│   │   ├── feedback-search-implementation.md       # 反馈搜索
│   │   ├── topic-search-implementation.md          # 主题搜索
│   │   ├── fulltext-search-index-guide.md          # 全文搜索索引
│   │   ├── fulltext-search-quickstart.md           # 快速入门
│   │   ├── feedback-search-ui-fix.md               # UI 修复
│   │   └── search-mode-animation.md                # 搜索动画
│   │
│   ├── 📸 screenshot/                              # 截图识别
│   │   ├── screenshot-async-implementation.md      # 异步实现
│   │   ├── screenshot-recognition-implementation.md # 识别实现
│   │   └── screenshot-menu-setup-complete.md       # 菜单设置
│   │
│   └── 🗂️ workspace/                               # 工作空间
│       ├── workspace-deployment-guide.md           # 部署指南
│       ├── workspace-implementation-summary.md     # 实现总结
│       └── workspace-testing-guide.md              # 测试指南
│
├── 📚 guides/                                       # 操作指南
│   │
│   ├── 🚀 deployment/                              # 部署指南
│   │   ├── pgvector-deployment-checklist.md        # pgvector 部署检查清单
│   │   └── pgvector-migration-guide.md             # pgvector 迁移指南
│   │
│   ├── 💻 development/                             # 开发指南
│   │   ├── debug-middleware-guide.md               # 调试中间件
│   │   ├── logging-best-practices.md               # 日志最佳实践
│   │   ├── feedback-ui-simplification-summary.md   # UI 简化
│   │   ├── insights-implementation-summary.md      # 洞察实现
│   │   ├── priority-scoring-implementation-summary.md # 优先级评分
│   │   └── badge-implementation.md                 # 徽章实现
│   │
│   ├── ⚙️ configuration/                           # 配置指南
│   │   ├── storage-configuration.md                # 存储配置
│   │   ├── storage-implementation-summary.md       # 存储实现
│   │   ├── storage-quick-start.md                  # 存储快速入门
│   │   ├── redis-config.md                         # Redis 配置
│   │   ├── celery-db-result-backend.md             # Celery 配置
│   │   └── upstash-redis-setup.md                  # Upstash Redis
│   │
│   └── 🧠 ai-provider/                             # AI 提供商
│       ├── README-VOLCENGINE.md                    # 火山引擎说明
│       ├── configuration.md                        # 配置
│       ├── embedding-support.md                    # 嵌入支持
│       ├── quick-start.md                          # 快速入门
│       ├── troubleshooting.md                      # 故障排除
│       ├── volcengine-config-example.md            # 配置示例
│       ├── volcengine-endpoint-setup.md            # 端点设置
│       ├── volcengine-quickstart.md                # 快速入门
│       └── volcengine-vision-setup.md              # 视觉设置
│
├── 🧪 testing/                                      # 测试文档
│   ├── mvp-testing-guide.md                        # MVP 测试指南
│   ├── badge-display-test-guide.md                 # 徽章测试
│   └── test-users-guide.md                         # 测试用户指南
│
├── 📋 planning/                                     # 规划文档
│   ├── 📄 wechat-feedback-collect.md               # 微信反馈收集
│   │
│   ├── 🗺️ roadmap/                                 # 路线图
│   │   ├── roadmap.md                              # 产品路线图
│   │   ├── china-canny-roadmap.md                  # 中国版路线图
│   │   ├── china-canny-technical-plan.md           # 技术计划
│   │   └── mvp.md                                  # MVP 规划
│   │
│   └── 📊 competitor-analysis/                     # 竞品分析
│       └── canny-competitor-analysis.md            # Canny 竞品分析
│
└── 🗄️ archive/                                      # 已归档
    ├── PERFORMANCE-DIAGNOSIS-REPORT.md             # 性能诊断（历史）
    ├── performance-fixes.md                        # 性能修复（历史）
    ├── performance-optimization-remote-db.md       # 性能优化（历史）
    ├── data-model-comparison.md                    # 数据模型对比（过时）
    ├── database-design.md                          # 旧版数据库设计（过时）
    └── clustering-test-guide.md                    # 旧版测试指南（过时）
```

## 📊 统计信息

- **总文件数**: 66 个文档
- **顶级目录**: 6 个
- **二级目录**: 14 个
- **最大深度**: 3 层

## 🎯 设计原则

1. **功能优先**: 按功能和用途分类，而非按时间或作者
2. **清晰层级**: 最多 3 层目录，避免过深嵌套
3. **语义化**: 目录名称清晰表达内容类型
4. **可扩展**: 预留了足够的扩展空间

## 🔍 快速查找

### 我想了解...
- **数据库设计** → `architecture/database/`
- **AI 功能** → `features/ai-clustering/`
- **搜索功能** → `features/search/`
- **如何部署** → `guides/deployment/`
- **如何配置** → `guides/configuration/`
- **产品规划** → `planning/roadmap/`
- **测试方法** → `testing/`

### 我想开发...
- **新功能** → 先看 `planning/roadmap/mvp.md`
- **数据库相关** → 先看 `architecture/database/complete-er-diagram.md`
- **AI 相关** → 先看 `features/ai-clustering/` 和 `guides/ai-provider/`
- **前端 UI** → 搜索 `*-ui-*.md` 或 `*-uiux-*.md`

---

**最后更新**: 2025-12-31
