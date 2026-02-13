# UserEcho 文档中心

## 📚 文档导航

### 🎯 设计文档 (`design/`)

核心架构和系统设计文档。

- [数据库设计](design/database-design.md) - 完整的数据库表结构和关系设计
- [路由设计](design/route-design.md) - 前后端路由规范和隔离策略
- [MVP 方案](design/mvp.md) - 最小可行产品功能定义和实现计划

### ⚙️ 配置指南 (`guides/`)

系统配置和使用指南。

#### AI Provider 配置

- [配置说明](guides/ai-provider/configuration.md) - AI Provider 完整配置指南
- [快速开始](guides/ai-provider/quick-start.md) - 快速配置和测试
- [故障排查](guides/ai-provider/troubleshooting.md) - 常见问题和解决方案
- [Embedding 支持](guides/ai-provider/embedding-support.md) - 各 Provider 的 Embedding 能力
- [火山引擎端点配置](guides/ai-provider/volcengine-endpoint-setup.md) - 火山引擎特定配置

#### Redis 配置

- [Redis 配置](guides/redis-config.md) - Redis 基础配置
- [Upstash Redis 配置](guides/upstash-redis-setup.md) - Upstash 云端 Redis 设置指南

### 🧪 测试文档 (`testing/`)

测试指南和测试用户管理。

- [MVP 测试指南](testing/mvp-testing-guide.md) - 完整的功能测试清单和测试步骤
- [测试用户指南](testing/test-users-guide.md) - 测试用户创建和管理

### 🚀 开发文档 (`development/`)

开发计划和路线图。

- [产品路线图](development/roadmap.md) - 功能开发优先级和里程碑规划

---

## 📖 文档使用建议

### 新成员快速上手

1. 从 [MVP 方案](design/mvp.md) 了解项目核心功能
2. 阅读 [数据库设计](design/database-design.md) 理解数据模型
3. 查看 [路由设计](design/route-design.md) 了解前后端交互规范
4. 根据需要配置 [AI Provider](guides/ai-provider/configuration.md) 和 [Redis](guides/redis-config.md)

### 开发者日常参考

- **设计决策**：查阅 `design/` 目录下的架构文档
- **功能配置**：参考 `guides/` 目录下的配置指南
- **测试验证**：使用 `testing/` 目录下的测试清单
- **规划排期**：查看 `development/roadmap.md` 了解开发优先级

### 运维部署

- Redis 部署：参考 [guides/redis-config.md](guides/redis-config.md)
- AI 服务配置：参考 [guides/ai-provider/](guides/ai-provider/) 目录下文档
- 故障排查：查看 [guides/ai-provider/troubleshooting.md](guides/ai-provider/troubleshooting.md)

---

## 🔧 维护说明

### 文档更新原则

1. **及时更新**：功能变更后立即更新相关文档
2. **保持简洁**：避免创建临时性的进度报告文档
3. **分类清晰**：按照现有目录结构归档新文档
4. **删除过期**：定期清理已失效的文档内容

### 文档类型定义

- **设计文档**：长期有效，描述架构和核心设计决策
- **配置指南**：操作手册，提供具体配置步骤
- **测试文档**：测试清单和测试流程
- **开发文档**：开发计划、路线图等前瞻性文档

**避免创建**：完成报告、迁移报告、实现进度等临时性文档

---

**最后更新**：2025-12-22
