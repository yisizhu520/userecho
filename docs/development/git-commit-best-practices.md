# Git Commit 最佳实践（开源项目）

这份文档用于统一 `userecho` 的提交质量，目标是：

- 提交历史可读、可追溯
- 发布说明可自动生成
- 新贡献者可以快速理解改动

## 1. 提交格式标准

采用 Conventional Commits：

```text
type(scope): subject
```

可选的破坏性变更格式：

```text
type(scope)!: subject
```

### 允许的 type

- `feat`: 新功能
- `fix`: 缺陷修复
- `docs`: 文档变更
- `style`: 纯格式调整（不改逻辑）
- `refactor`: 重构（不增功能不修 bug）
- `perf`: 性能优化
- `test`: 测试相关
- `build`: 构建系统、依赖、打包
- `ci`: CI/CD 配置
- `chore`: 杂项维护
- `revert`: 回滚提交
- `security`: 安全修复
- `deps`: 依赖升级/降级

### 书写要求

- header 最长 72 字符
- `subject` 用祈使语气，描述“做了什么”
- 不写无意义消息：`test`、`fix bug`、`update`
- 一个 commit 只做一件事

推荐示例：

```text
feat(feedback): add topic merge operation for admins
fix(auth): handle missing tenant-id during first login
docs(readme): add live website and demo links
security(env): ignore real deployment env files
```

## 2. 本仓库已启用的校验

仓库根目录已添加：

- `lefthook.yml`
- `scripts/git/validate-commit-msg.mjs`

### 首次启用（每台机器一次）

```bash
pnpm install
```

`package.json` 的 `prepare` 会自动执行 `lefthook install`。

## 3. 推荐提交工作流

### 开发分支建议

- `main/master` 保持可发布状态
- 功能分支命名：`feat/<topic>`、`fix/<topic>`、`chore/<topic>`

### 每次提交前

1. 先把改动按功能拆分
2. 再逐个 commit
3. 最后自查提交信息是否准确

## 4. 开源前整理历史（安全做法）

如果要统一近期历史，请优先整理“未发布窗口”的提交，不要全仓库暴力重写。

### 4.1 本地创建备份分支

```bash
git branch backup/before-history-cleanup
```

### 4.2 交互式整理最近 N 条提交

```bash
git rebase -i HEAD~30
```

在编辑器里：

- `pick` 保留
- `reword` 修改提交信息
- `squash` 合并碎片提交

### 4.3 推送时使用安全强推

```bash
git push origin <branch> --force-with-lease
```

不要用 `--force`，避免覆盖他人的新提交。

## 5. 团队协作约定

- 不在共享主干上频繁重写历史
- 合并前确保 commit 信息通过校验
- PR 合并策略优先 `Squash and merge`（保持主干历史干净）

## 6. 快速排查

### 校验失败

报错通常是以下原因：

- type 不在允许列表
- 缺少冒号和空格（`type(scope): subject`）
- header 超过 72 字符

### 临时跳过钩子

不建议。只有紧急修复时才考虑，并在后续补上规范化提交。
