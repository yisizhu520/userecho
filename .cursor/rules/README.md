# Feedalyze Cursor 规则

本目录包含 Feedalyze 项目的 Cursor AI 辅助开发规则，采用模块化组织方式，便于维护和更新。

## 规则文件列表

| 文件 | 描述 | 标签 |
|------|------|------|
| [01-project-overview.mdc](./01-project-overview.mdc) | 项目概述、技术栈和项目结构 | `overview`, `architecture`, `structure` |
| [02-frontend-standards.mdc](./02-frontend-standards.mdc) | 前端代码规范（Vue、TypeScript） | `frontend`, `vue`, `typescript`, `coding-standards` |
| [03-backend-standards.mdc](./03-backend-standards.mdc) | 后端代码规范（FastAPI、Python） | `backend`, `fastapi`, `python`, `coding-standards` |
| [04-git-and-api.mdc](./04-git-and-api.mdc) | Git 提交规范和 RESTful API 设计 | `git`, `api`, `rest`, `conventions` |
| [05-security-performance.mdc](./05-security-performance.mdc) | 安全规范和性能优化 | `security`, `performance`, `optimization` |
| [06-testing-docs.mdc](./06-testing-docs.mdc) | 测试规范和文档编写 | `testing`, `documentation`, `best-practices` |
| [07-commands-env.mdc](./07-commands-env.mdc) | 常用命令和环境变量 | `commands`, `environment`, `configuration` |
| [08-ai-guidelines.mdc](./08-ai-guidelines.mdc) | AI 辅助开发指南 | `ai`, `guidelines`, `best-practices` |

## 使用说明

### 文件格式

所有规则文件使用 `.mdc` 格式（Markdown with metadata），包含：

- **frontmatter**: YAML 格式的元数据（description、tags）
- **content**: Markdown 格式的规则内容

示例：

```markdown
---
description: 文件描述
tags: [tag1, tag2, tag3]
---

# 规则标题

规则内容...
```

### 如何添加新规则

1. 在 `.cursor/rules/` 目录下创建新的 `.mdc` 文件
2. 添加 frontmatter 元数据
3. 使用 Markdown 编写规则内容
4. 更新本 README.md，添加新规则的说明

### 如何修改规则

直接编辑对应的 `.mdc` 文件即可。Cursor 会自动加载更新后的规则。

## 规则组织原则

### 模块化

- 每个文件专注于一个特定领域
- 文件大小适中，易于阅读和维护
- 使用编号前缀保持逻辑顺序

### 清晰的元数据

- `description`: 简短描述文件内容
- `tags`: 便于搜索和分类的标签

### 实用性

- 提供具体的代码示例
- 包含 ✅ 推荐和 ❌ 避免的对比
- 说明"为什么"而不仅仅是"怎么做"

## 常见使用场景

### 🎯 开发新功能

参考以下规则：
- `01-project-overview.mdc` - 了解项目架构
- `02-frontend-standards.mdc` 或 `03-backend-standards.mdc` - 代码规范
- `04-git-and-api.mdc` - API 设计规范

### 🐛 修复 Bug

参考以下规则：
- `08-ai-guidelines.mdc` - Bug 修复建议
- `05-security-performance.mdc` - 安全和性能相关

### ✅ 代码审查

参考以下规则：
- `02-frontend-standards.mdc` / `03-backend-standards.mdc` - 代码规范
- `05-security-performance.mdc` - 安全检查
- `08-ai-guidelines.mdc` - 代码审查清单

### 📝 编写文档

参考以下规则：
- `06-testing-docs.mdc` - 文档规范

### 🚀 部署

参考以下规则：
- `07-commands-env.mdc` - 部署命令和环境配置

## 维护指南

### 定期更新

- 当项目依赖更新时，同步更新相关规则
- 当团队采用新的最佳实践时，及时补充
- 定期审查和优化规则内容

### 版本控制

- 在文件末尾标注最后更新日期
- 重大变更时在 Git 提交信息中说明

### 反馈机制

如果发现规则有问题或需要补充：
1. 在团队会议上讨论
2. 创建 issue 或 PR
3. 直接修改并提交

## 迁移说明

本项目已从根目录的 `.cursorrules` 文件迁移到 `.cursor/rules/*.mdc` 模块化结构：

**优势**：
- ✅ 更好的组织和分类
- ✅ 更易于维护和更新
- ✅ 支持按需查阅特定领域的规则
- ✅ 更清晰的文件结构

**兼容性**：
- Cursor 会自动识别 `.cursor/rules/` 目录下的规则文件
- 无需额外配置

---

**最后更新**: 2025-12-20
