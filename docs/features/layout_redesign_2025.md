# 页面布局重构设计方案 (Layout Redesign Proposal)

> **创建日期**: 2025-12-31
> **状态**: 待审核 (Draft)
> **目标**: 优化现有布局，引入 Board (板块) 选择功能，并对标 Canny 的交互体验，同时适配中国用户习惯。

## 1. 背景与问题

目前系统的布局结构为：
- **左侧 Sidebar**: 功能模块导航 (Feedback, Topic, AI Discovery 等)。
- **顶部 Navbar**: 操作选项与筛选 (推测)。

**痛点**:
- 缺乏显性的 **Boards (板块)** 选择入口。随着多板块功能的引入，用户无法直观地在不同产品线/板块间切换。
- 筛选与操作分散，甚至可能占据了顶部导航的宝贵垂直空间。
- 与主流竞品 (如 Canny) 的心智模型不一致，Canny 采用 "顶部导航(模块) + 左侧侧边栏(上下文/筛选)" 的经典布局。

## 2. 设计理念

基于 "资深视觉交互设计师" 的视角，本次重构遵循以下原则：

1.  **上下文优先 (Context First)**: 左侧侧边栏是用户定义 "我在看什么数据" 的最佳区域（即：Board 选择 + 过滤器）。
2.  **模块全局化 (Global Modules)**: 顶部导航栏用于定义 "我在使用什么功能"（即：Feedback, Roadmap, User 等）。
3.  **沉浸式阅读 (Immersive Reading)**: 将垂直空间最大程度留给内容列表。

## 3. 重构方案详解

我们将采用 **"顶部分区，左侧分层"** 的布局策略。

### 3.1 整体框架 (The Framework)

| 区域 |原来位置 | **新的位置** | 内容 |
| :--- | :--- | :--- | :--- |
| **一级导航** | 左侧 Sidebar | **顶部 Navbar (左侧)** | Feedback (反馈), Roadmap (路线路), AI Discovery (智能发现), Users (用户) |
| **Board 选择** | 无 | **左侧 Sidebar (顶部)** | Board 切换器 / Board 多选列表 |
| **过滤器/视图** | 顶部 Navbar | **左侧 Sidebar (中下部)** | 状态筛选 (Status), 标签 (Tags), 用户分群 (Segments) |
| **全局功能** | 顶部 Navbar (右侧) | **顶部 Navbar (右侧)** | 搜索, 通知, 个人中心, 设置 |

### 3.2 详细设计说明

#### A. 顶部导航栏 (Top Navbar) - 功能维度的切换
*高度建议*: 60px - 64px
*背景*: 白色或极淡的灰色 (适配 Light Mode)，深色 (适配 Dark Mode)。

*   **Logo 区**: 最左侧，点击回首页。
*   **模块导航**: 紧随 Logo。
    *   使用文字 Tab 或 弱化图标+文字。
    *   **选中态**:底部高亮条 (Underline) 或 加粗字体 + 品牌色文字。
    *   *适配点*: 我们的 Feedback, Topic, AI Discovery 直接平铺在此。
*   **右侧操作区**:
    *   全局搜索 (Search)。
    *   新建按钮 (Create Post) - *主要行动点 (CTA)*，建议使用品牌色实心按钮。
    *   头像与通知。

#### B. 左侧侧边栏 (Left Sidebar) - 数据维度的控制
*宽度建议*: 240px - 260px (固定或可折叠)

这个区域是本次改动的**核心**，我们将它分为三个逻辑区块：

**1. 空间/板块选择器 (Boards Selector)**
*位置*: Sidebar 最上方。
*交互模式*:
*   **模式 A (Canny 风格 - 聚合视图)**: 如果用户需要同时看所有 Board 的反馈。
    *   标题: "Boards"
    *   内容: Checkbox 列表 (多选框)。
    *   *默认*: 全选 (All Boards) 或 记住上次选择。
    *   *优点*: 适合 Board 数量较少 (1-10个) 且互相关联的场景。
*   **模式 B (且/或 切换器 - 独立视图)**: 类似 Discord/Slack 或此时的 Project 切换。
    *   组件: 下拉选择框 (Dropdown Select) 或 带有图标的列表项。
    *   *场景*: 如果 Board 之间隔离性很强 (例如 "To B 产品" 和 "To C 产品")。
*   **推荐方案**: 采用 **Canny 风格 (Checkbox List)**，但在列表上方加一个 "Select All / Clear" 的快捷操作。这符合 userecho 作为统一反馈平台的定位。

**2. 筛选与视图 (Filters & Views)**
*位置*: Boards 下方。
*内容*:
*   **Status (状态)**: Open, In Progress, Planned, Completed 等。使用 Checkbox 实现多选过滤。
*   **Date Range (时间)**: 下拉选择 (All time, Last 30 days...)。
*   **Segments (用户分群)**: 付费用户, 免费用户等。

**3. 底部操作 (Footer Actions)**
*位置*: Sidebar 底部（可选）。
*内容*: "Powered by userecho" 或 页面级的快捷设置 (如 "Board Settings" 如果当前只选了一个 Board)。

#### C. 内容区域 (Main Content)
*   左对齐，留白适中。
*   **AI 发现中心 (AI Discovery)** 页面特殊处理:
    *   保持左侧 Sidebar 的 Board 筛选逻辑一致。因为 AI 洞察也需要在特定 Board 范围内进行分析。
    *   中间内容区展示聚类后的 "Topic Cards"。

### 4. 视觉风格建议 (Visual Guidelines)

*   **留白 (Whitespace)**: 增加模块间的间距，避免密集感。Sidebar 的 Item 高度建议 32px-36px，增加点击热区。
*   **层级 (Hierarchy)**:
    *   Top Navbar 阴影: `box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);` (轻微分割)
    *   Sidebar 边框: 右侧 `1px solid #E5E7EB` (极细边框，无需阴影)。
*   **色彩 (Colors)**:
    *   选中色: 使用我们的品牌主色 (Brand Primary)。
    *   辅助色: 灰色系用于非活跃文本。

## 5. 预期效果

1.  **清晰的层级**: 用户一眼就能明白：我在 *哪个功能模块* (Top)，看 *哪些板块的数据* (Left)。
2.  **扩展性**: 未来如果增加 "Roadmap" 或 "Changelog"，直接在 Top Navbar 加一个 Tab 即可，不破坏整体布局。
3.  **专业感**: 对齐国际一流 SaaS (Linear, Canny, Intercom) 的布局范式。

## 6. 技术实现策略 (Technical Strategy)

经代码库调研，userecho 使用的 Vben Admin 5.0 框架原生支持 **混合导航 (Mixed Nav)** 模式，这与我们要实现的 "Top Nav + Left Sidebar" 布局完美契合。

*   **配置**: 修改 `preferences.ts` 将布局模式设置为 `mixed-nav`。
    *   这将自动把一级菜单（Feedback, Roadmap 等）置于顶部。
    *   将侧边栏保留在左侧。
*   **定制**:
    *   通过 `BasicLayout` 的插槽 (Slots) 机制（如 `#mixed-menu` 或 `#side-extra`），将默认的子菜单替换为我们将要开发的 `<BoardSelector />` 和 `<SidebarFilters />` 组件。
    *   这属于框架支持的扩展能力，**不需要** 对核心框架代码进行破坏性修改 (Magic Modify)，维护成本低。

**结论**: 改动量适中且可控，推荐按原设计方案推进。

---

*请 Review 此方案，确认后我们将开始代码层面的布局迁移。*
