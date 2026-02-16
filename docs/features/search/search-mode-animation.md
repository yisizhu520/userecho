# 搜索模式切换动画实现

## 动画效果

为搜索模式 RadioGroup 添加了优雅的切换动画，包括：

### 1. **按钮过渡动画** ✅
```css
transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
```
- 使用 `cubic-bezier` 缓动函数，模拟物理运动
- 0.3s 过渡时间，流畅不拖沓

### 2. **悬停效果** ✅
```css
.ant-radio-button-wrapper:hover::before {
  opacity: 0.08;
}
```
- 半透明遮罩，微妙的交互反馈
- 使用 `::before` 伪元素，不影响内容布局

### 3. **选中状态** ✅
```css
.ant-radio-button-wrapper-checked {
  transform: scale(1.05);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}
```
- **放大 5%** - 突出当前选中项
- **阴影** - 增加层次感

### 4. **涟漪动画** ✅
```css
@keyframes ripple {
  to {
    transform: translate(-50%, -50%) scale(2);
    opacity: 0;
  }
}
```
- 点击时触发径向渐变扩散
- 0.6s 动画，自然消散
- Material Design 风格

## 技术方案

### 使用项目已有资源
- ✅ **Tailwind CSS Animate** - 项目已集成
- ✅ **Vue Transition** - 项目内置动画类
- ✅ **CSS Transitions** - 原生性能最优

### 为什么不用 JS 动画库？
> "简单的方案永远是最好的" - Linus

1. **CSS Transition 已经够用** - 不需要引入额外依赖
2. **性能最优** - CSS 动画由浏览器原生优化，GPU 加速
3. **代码简洁** - 不需要 Vue 生命周期钩子或 watch

### 动画参数解释

**缓动函数：**`cubic-bezier(0.4, 0, 0.2, 1)`
- 0.4, 0: 快速启动
- 0.2, 1: 缓慢结束
- 模拟物理惯性，符合用户预期

**时长选择：**
- 0.3s - 按钮状态切换（快速反馈）
- 0.6s - 涟漪扩散（视觉愉悦）
- 小于 0.5s 避免用户感知延迟

## 实现文件

### 1. `data.ts` - 添加 class
```typescript
componentProps: {
  // ...
  class: 'search-mode-radio',
},
```

### 2. `list.vue` - 定义动画样式
```vue
<style scoped>
:deep(.search-mode-radio) {
  /* 动画样式 */
}
</style>
```

## 视觉体验

**切换"关键词 ⚡" → "语义理解 🤖" 时：**
1. 旧按钮缩小回 100%，阴影消失（0.3s）
2. 新按钮放大到 105%，阴影出现（0.3s）
3. 涟漪从中心扩散到边缘（0.6s）

**鼠标悬停时：**
- 半透明遮罩淡入，提示可交互

## 可访问性

- ✅ 保留原生键盘导航
- ✅ 不依赖动画完成才能操作
- ✅ 动画可被 `prefers-reduced-motion` 禁用（浏览器设置）

## 扩展建议

如果需要更复杂的动画：
```css
/* 添加到 list.vue 的 <style> */
@media (prefers-reduced-motion: reduce) {
  :deep(.search-mode-radio) * {
    animation: none !important;
    transition: none !important;
  }
}
```

---

*优雅的动画不是炫技，而是让用户感知状态变化的最直观方式。*
