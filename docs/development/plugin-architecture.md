# 插件系统架构问题与解决方案

## 问题诊断

### 当前架构的缺陷

当前"插件系统"存在以下致命问题：

1. **强依赖耦合**：所有插件依赖必须写在主项目的 `pyproject.toml` 中
2. **无优雅降级**：任何插件加载失败都会导致整个应用崩溃
3. **名不副实**：这不是真正的插件系统，只是带独立文件夹的模块

```python
# 原始代码问题
def inject_app_router(...):
    try:
        module = import_module_cached(module_path)  # 依赖缺失直接崩溃
        ...
    except Exception as e:
        raise PluginInjectError(...)  # 任何错误都中断应用启动
```

### Linus 式评价

> "如果插件的依赖必须写在主项目里，那它根本不是插件，只是个带独立文件夹的模块罢了。
> 这不是插件系统，这是'假装模块化'的自欺欺人。"

**真正的插件系统应该**：
1. 插件可以独立安装/卸载
2. 插件不可用时系统不崩溃
3. 依赖按需加载

---

## 解决方案

### 方案一：短期修复（已实施）✅

**核心思想**：优雅降级，缺少依赖的插件自动跳过

**实现**：修改 `inject_app_router()` 和 `inject_extend_router()`：

```python
def inject_app_router(plugin: dict[str, Any], target_router: APIRouter) -> None:
    plugin_name: str = plugin['plugin']['name']
    module_path = f'backend.plugin.{plugin_name}.api.router'
    try:
        module = import_module_cached(module_path)
        ...
    except ModuleNotFoundError as e:
        # 插件依赖缺失，记录警告但不影响主应用启动
        log.warning(f'Plugin {plugin_name} skipped due to missing dependency: {e}')
    except (PluginConfigError, PluginInjectError):
        # 插件配置错误，应该中断启动
        raise
    except Exception as e:
        # 其他错误，记录但不中断
        log.error(f'Plugin {plugin_name} failed to load: {e}')
        log.warning(f'Plugin {plugin_name} will be disabled')
```

**优点**：
- ✅ 无需改动现有架构
- ✅ 主应用不会因插件问题而崩溃
- ✅ 立即可用

**缺点**：
- ❌ 仍需在主项目声明所有潜在插件依赖
- ❌ 不是真正的插件隔离

**适用场景**：
- 快速解决生产问题
- 不想大幅重构的情况

---

### 方案二：正确的插件系统（推荐）🎯

**核心思想**：使用 uv dependency groups 实现真正的可选依赖

#### 2.1 依赖组织方式

```toml
# server/pyproject.toml
[project]
dependencies = [
    # 只包含核心依赖
    "fastapi>=0.123.5",
    "sqlalchemy>=2.0.44",
    ...
]

[dependency-groups]
# 核心功能（必需）
core = []

# 插件依赖（可选）
plugin-email = [
    "aiosmtplib>=3.0.2",
]
plugin-oauth2 = [
    "fastapi-oauth20>=0.0.2",
]
plugin-ai = [
    "openai>=2.14.0",
]

# 所有插件（开发环境）
dev = [
    {include-group = "plugin-email"},
    {include-group = "plugin-oauth2"},
    {include-group = "plugin-ai"},
]
```

#### 2.2 安装方式

```bash
# 生产环境：只装核心 + 需要的插件
uv sync --only-group core
uv sync --only-group plugin-email

# 开发环境：装所有插件
uv sync --group dev
```

#### 2.3 插件加载逻辑

保持当前的优雅降级机制（方案一），这样即使依赖缺失也不会崩溃。

#### 2.4 插件独立性

每个插件目录保留 `requirements.txt` 作为**文档说明**：

```
# backend/plugin/email/requirements.txt
# This plugin requires:
aiosmtplib>=3.0.2

# Installation:
# uv sync --only-group plugin-email
```

**优点**：
- ✅ 插件依赖明确隔离
- ✅ 生产环境可按需安装
- ✅ 开发环境可全装
- ✅ 符合插件系统的本质

**缺点**：
- ❌ 需要重构 `pyproject.toml`
- ❌ 需要更新部署文档

**适用场景**：
- 长期维护的项目
- 需要真正的插件隔离
- 插件会频繁增删

---

### 方案三：插件包独立（终极方案）🚀

**核心思想**：每个插件作为独立的 Python 包发布

#### 3.1 架构设计

```
userecho/                    # 主项目
userecho-plugin-email/       # 独立插件包
  ├── pyproject.toml          # 独立的依赖管理
  └── userecho_plugin_email/
      └── ...

userecho-plugin-oauth2/      # 另一个独立插件包
  ├── pyproject.toml
  └── ...
```

#### 3.2 插件发现机制

使用 Python entry points：

```toml
# userecho-plugin-email/pyproject.toml
[project.entry-points."userecho.plugins"]
email = "userecho_plugin_email:plugin"
```

主应用加载：

```python
from importlib.metadata import entry_points

def discover_plugins():
    for ep in entry_points(group='userecho.plugins'):
        try:
            plugin = ep.load()
            yield plugin
        except ImportError as e:
            log.warning(f'Plugin {ep.name} not available: {e}')
```

#### 3.3 安装方式

```bash
# 只装主应用
uv pip install userecho

# 需要邮件插件
uv pip install userecho-plugin-email

# 需要 OAuth2 插件
uv pip install userecho-plugin-oauth2
```

**优点**：
- ✅ 完全独立的插件生命周期
- ✅ 插件可独立版本管理
- ✅ 符合 Python 生态标准
- ✅ 真正的"插件"

**缺点**：
- ❌ 需要大幅重构
- ❌ 增加维护复杂度
- ❌ 需要建立插件发布流程

**适用场景**：
- 开源项目，鼓励社区贡献插件
- 插件会独立迭代版本
- 需要插件市场/生态

---

## 当前状态

**已实施**：方案一（优雅降级）

**改动文件**：
- `server/backend/plugin/tools.py` - 添加 ModuleNotFoundError 捕获
- `server/pyproject.toml` - 临时将插件依赖提升到主项目（过渡方案）

**效果**：
- ✅ 应用不会因插件依赖缺失而崩溃
- ✅ 启动日志会显示哪些插件被跳过
- ⚠️ 仍需手动管理所有插件依赖

---

## 推荐路径

### 立即（已完成）
- [x] 实施方案一：优雅降级，确保应用稳定

### 短期（1-2周）
- [ ] 重构为方案二：使用 dependency groups
- [ ] 更新部署文档和 CI/CD
- [ ] 清理主项目依赖，只保留核心

### 长期（按需）
- [ ] 评估方案三的必要性
- [ ] 如果有大量第三方插件需求，再考虑独立包

---

## 实施方案二的步骤

如果决定采用方案二，按以下步骤执行：

### 1. 重构 pyproject.toml

```bash
cd server
```

编辑 `pyproject.toml`：

```toml
[project]
dependencies = [
    # 移除插件专属依赖
    # - "aiosmtplib>=3.0.2",      # 移到 plugin-email
    # - "fastapi-oauth20>=0.0.2", # 移到 plugin-oauth2
    
    # 只保留核心依赖
    "fastapi>=0.123.5",
    "sqlalchemy>=2.0.44",
    ...
]

[dependency-groups]
plugin-email = ["aiosmtplib>=3.0.2"]
plugin-oauth2 = ["fastapi-oauth20>=0.0.2"]
dev = [
    {include-group = "plugin-email"},
    {include-group = "plugin-oauth2"},
]
```

### 2. 更新安装脚本

```bash
# 生产环境：按需安装
uv sync                           # 核心依赖
uv sync --only-group plugin-email # 如果需要邮件功能

# 开发环境：全装
uv sync --group dev
```

### 3. 更新部署文档

修改 `deploy/backend/README.md`，说明如何选择插件。

### 4. 验证

```bash
# 测试核心功能（不装插件）
uv sync --no-dev
python run.py

# 测试插件功能
uv sync --only-group plugin-email
python run.py  # 应该能看到邮件插件加载成功
```

---

## 参考资料

- [uv Dependency Groups 文档](https://docs.astral.sh/uv/concepts/dependencies/)
- [Python Entry Points 教程](https://packaging.python.org/en/latest/specifications/entry-points/)
- [FastAPI Plugin System 示例](https://github.com/tiangolo/fastapi/discussions/3955)

---

## 总结

| 方案 | 独立性 | 改动成本 | 维护成本 | 推荐度 |
|-----|-------|---------|---------|-------|
| 方案一：优雅降级 | ⭐ | 低 | 低 | ⭐⭐⭐ 临时方案 |
| 方案二：Dependency Groups | ⭐⭐⭐ | 中 | 中 | ⭐⭐⭐⭐⭐ **推荐** |
| 方案三：独立包 | ⭐⭐⭐⭐⭐ | 高 | 高 | ⭐⭐⭐ 大型项目 |

**建议**：
1. **现在**：方案一已实施，确保稳定性
2. **未来 1-2 周**：迁移到方案二，获得真正的插件隔离
3. **长期**：如果插件生态发展起来，考虑方案三

