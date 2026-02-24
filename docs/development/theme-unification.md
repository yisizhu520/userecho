# 主题系统统一改造

## 背景

### 问题描述

在改造前，应用存在两套独立的主题系统：

1. **Landing 页面主题**
   - 存储位置：`localStorage['landing-theme']`
   - 默认值：`dark`
   - 管理方式：自定义的 `useLandingTheme` composable

2. **应用内主题**（登录后）
   - 存储位置：`localStorage['preferences-theme']`
   - 默认值：`dark`
   - 管理方式：Vben 框架的 `@vben/preferences` 系统

### 核心问题

> "这是个典型的数据结构问题 - 两套独立的状态管理同一件事。" - Linus 式思考

**违反单一数据源原则**：
- 用户期望"一个主题设置"，但实际上有两个独立的主题状态
- 在 Landing 页面调整主题，不影响应用内主题
- 在应用内调整主题，不影响 Landing 页面主题
- 用户体验不一致，容易造成困惑

## 解决方案

### 架构改进

**统一主题源**：让 Landing 页面也使用 Vben 的 `preferences` 系统

**优势**：
- ✅ 全站只有一个主题状态
- ✅ 用户调整主题，Landing 和应用内同步变化
- ✅ 消除了数据同步的复杂性
- ✅ 减少了存储空间占用
- ✅ 降低了代码维护成本

### 实现细节

#### 1. 修改默认主题为亮色

```typescript
// front/packages/@core/preferences/src/config.ts
theme: {
  mode: 'light', // 从 'dark' 改为 'light'
  // ... 其他配置
}
```

#### 2. 重写 `useLandingTheme`

```typescript
// front/apps/web-antd/src/composables/useLandingTheme.ts
import { computed } from 'vue';
import { usePreferences } from '@vben/preferences';
import { preferencesManager } from '@vben/preferences';

export function useLandingTheme() {
  const { theme: vbenTheme, isDark: isVbenDark } = usePreferences();

  // 将 vben 的 theme 映射为 LandingTheme
  const theme = computed<LandingTheme>(() => vbenTheme.value as LandingTheme);

  const setTheme = (newTheme: LandingTheme) => {
    // 更新 Vben preferences
    preferencesManager.updatePreferences({
      theme: { mode: newTheme },
    });

    // 同步更新 Landing 页面的 CSS class
    document.documentElement.classList.remove('theme-dark', 'theme-light');
    document.documentElement.classList.add(`theme-${newTheme}`);
  };

  // ... 其他方法
}
```

#### 3. 兼容性保证

**API 接口保持不变**：
- `theme`：响应式主题值
- `setTheme(theme)`：设置主题
- `toggleTheme()`：切换主题
- `initTheme()`：初始化主题
- `isDark()`：判断是否为深色
- `isLight()`：判断是否为浅色

**无需修改现有组件**：
- `HeroSection.vue`
- `LandingNavbar.vue`
- `PricingCard.vue`
- `ThemeToggle.vue`
- `landing/index.vue`

#### 4. 迁移逻辑

自动清理旧的主题设置：

```typescript
// 一次性清理旧的主题设置
const OLD_STORAGE_KEY = 'landing-theme';
if (typeof localStorage !== 'undefined' && localStorage.getItem(OLD_STORAGE_KEY)) {
  localStorage.removeItem(OLD_STORAGE_KEY);
}
```

## 影响范围

### 对用户的影响

**首次访问**：
- 新用户将看到亮色主题（更符合现代企业应用习惯）
- 可通过 Landing 页面或应用内的主题切换按钮调整

**现有用户**：
- 旧的 `landing-theme` 设置将被自动清理
- 如果之前在应用内设置过主题，将继续使用该设置
- 如果从未设置过，将使用新的默认值（亮色）

### 对开发的影响

**简化**：
- 减少了一套主题管理系统
- 消除了状态同步的复杂性
- 降低了 bug 出现的可能性

**维护**：
- 未来只需维护一套主题系统
- 新增主题相关功能更简单

## 验证

### 类型检查

```bash
cd front && pnpm check:type
# ✅ Tasks: 1 successful, 1 total
```

### 功能测试

- [ ] Landing 页面默认显示亮色主题
- [ ] Landing 页面主题切换按钮工作正常
- [ ] 登录后应用内主题与 Landing 页面一致
- [ ] 应用内调整主题后，返回 Landing 页面主题同步
- [ ] 刷新页面主题设置保持不变

## 后续优化

### 可选增强

1. **跟随系统主题**
   ```typescript
   theme: {
     mode: 'auto', // 'dark' | 'light' | 'auto'
   }
   ```
   - 自动检测用户系统的深色模式设置
   - 尊重用户的系统级偏好

2. **主题切换动画**
   - 平滑的主题过渡效果
   - 提升用户体验

3. **主题预设**
   - 提供多种配色方案
   - 允许用户自定义品牌色

## 总结

这次改造遵循了 Linus 的核心哲学：

> "好品味是一种直觉 - 从不同角度看问题，重写它让特殊情况消失，变成正常情况。"

**消除了"Landing 主题"和"应用主题"的特殊情况**，统一为"应用主题"，让代码更简洁、逻辑更清晰、用户体验更一致。

---

**改造时间**：2026-01-21  
**影响文件**：
- `front/packages/@core/preferences/src/config.ts`
- `front/apps/web-antd/src/composables/useLandingTheme.ts`
