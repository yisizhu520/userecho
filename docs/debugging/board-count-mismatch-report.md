# 看板计数与反馈列表数据不一致问题排查报告

## 问题描述

用户反馈：左侧栏看板筛选显示的数字（`board.feedback_count`）与反馈列表实际显示的数据条数对不上。

## 问题分析

### 1. 左侧栏计数来源

**位置**: `FeedbackFilterPanel.vue`

```vue
<Checkbox v-for="board in boards" :value="board.id">
  <span>{{ board.name }}</span>
  <span>({{ board.feedback_count }})</span>  <!-- 来自数据库 boards 表 -->
</Checkbox>
```

**计数逻辑**: `board.feedback_count` 由数据库触发器自动更新

**触发器位置**: `2026-01-02-00_15_00-add_board_stats_triggers.py`

```sql
CREATE OR REPLACE FUNCTION update_board_feedback_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE boards SET
        feedback_count = (
            SELECT COUNT(*) FROM feedbacks
            WHERE board_id = v_board_id AND deleted_at IS NULL  -- 只统计未删除的
        )
    WHERE id = v_board_id;
END;
$$ LANGUAGE plpgsql;
```

**统计范围**: 该看板下所有 `deleted_at IS NULL` 的反馈

### 2. 反馈列表数据来源

**位置**: `feedback/list.vue` + `feedback_service.get_list`

**筛选条件**:
```javascript
const filterValues = {
  search_query: '',
  is_urgent: ['true', 'false'],  // 默认显示紧急和常规
  derived_status: [],  // 空数组表示不筛选
  board_ids: [],  // 空数组，但会自动选中第一个看板
  date_range: null,
}
```

**API 筛选逻辑**: `crud_feedback._apply_filters`

```python
# 多选过滤：derived_status（派生状态筛选）
if derived_status is not None and len(derived_status) > 0:
    conditions = []
    for status in derived_status:
        if status == "pending":
            conditions.append(self.model.topic_id.is_(None))
        elif status == "review":
            conditions.append((self.model.topic_id.is_not(None)) & (TopicAlias.status == "pending"))
        # ... 其他状态
    query = query.where(or_(*conditions))
```

**统计范围**: 
- 基础条件: `deleted_at IS NULL`
- 可选筛选: `is_urgent`, `derived_status`, `board_ids`, `search_query`, `date_range`

### 3. 诊断结果

运行 `diagnose_board_count_mismatch.py` 的结果：

```
看板: 默认看板 (ID: default-board)
   触发器统计: 38 条
   实际统计（未删除）: 48 条
   警告: 触发器计数与实际不符！差异: -10
   
   详细分析：
      - 紧急: 0 条
      - 常规: 48 条
      - 待处理（未关联主题）: 48 条
      - 已关联主题: 0 条
```

**发现的问题**:
1. 触发器统计的数量与实际数量不符（38 vs 48，差异 -10）
2. 所有反馈都是"待处理"状态（未关联主题）

## 根本原因

### 主要原因 1: 触发器计数不准确

数据库触发器 `update_board_feedback_count` 的计数与实际不符，可能原因：
- 触发器未正确触发
- 存在并发更新导致的计数偏差
- 某些操作绕过了触发器（如直接 SQL 更新）

### 主要原因 2: 前端默认筛选条件

虽然前端默认不筛选 `derived_status`，但如果用户曾经手动选择过筛选条件，这些条件会被持久化到 localStorage：

```javascript
const { state: filterValues } = useFilterStorage({
  key: 'feedback_filter_values',  // 持久化到 localStorage
  defaultValue: { ... }
});
```

如果用户之前选择了某些派生状态（如"待处理"），下次打开页面时仍会保持这些筛选条件。

### 主要原因 3: 数据迁移或批量操作

从诊断结果看，除了默认看板外，其他看板的触发器计数与实际不符：
- "功能建议": 触发器 32，实际 0，差异 32
- "Bug 反馈": 触发器 33，实际 0，差异 33
- "性能优化": 触发器 35，实际 0，差异 35
- "用户体验": 触发器 29，实际 0，差异 29

这说明可能存在：
- 批量删除操作未正确触发触发器
- 反馈被批量移动到其他看板
- 数据库迁移过程中的不一致

## 解决方案

### 方案 1: 修复触发器计数（推荐）

运行修复脚本刷新所有看板的统计数据：

```bash
cd server
python backend/scripts/refresh_board_stats.py
```

该脚本会：
1. 检查触发器是否存在
2. 重新计算所有看板的 `feedback_count`
3. 验证修复结果

### 方案 2: 清除前端筛选条件缓存

如果问题是由于用户之前选择的筛选条件导致的，可以：

**方式 1: 用户手动清除**
- 打开浏览器开发者工具 (F12)
- Application/存储 -> Local Storage
- 删除 `feedback_filter_values` 键

**方式 2: 代码添加"重置筛选"按钮**

在 `FeedbackFilterPanel.vue` 中添加重置按钮：

```vue
<template>
  <div class="px-4 py-4">
    <div class="flex justify-between items-center mb-4">
      <h3>筛选条件</h3>
      <VbenButton variant="ghost" size="small" @click="resetFilters">
        重置
      </VbenButton>
    </div>
    <!-- 原有的筛选选项 -->
  </div>
</template>

<script setup>
const resetFilters = () => {
  emit('update:isUrgent', ['true', 'false']);
  emit('update:derivedStatus', []);
  emit('update:boardIds', []);
  emit('update:dateRange', null);
};
</script>
```

### 方案 3: 优化触发器逻辑（长期方案）

当前触发器在每次反馈增删改时都会重新计算整个看板的反馈数量，性能开销较大。可以优化为增量更新：

```sql
CREATE OR REPLACE FUNCTION update_board_feedback_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' OR (TG_OP = 'UPDATE' AND OLD.deleted_at IS NULL AND NEW.deleted_at IS NOT NULL) THEN
        -- 删除或软删除: -1
        UPDATE boards SET feedback_count = feedback_count - 1 WHERE id = OLD.board_id;
    ELSIF TG_OP = 'INSERT' OR (TG_OP = 'UPDATE' AND OLD.deleted_at IS NOT NULL AND NEW.deleted_at IS NULL) THEN
        -- 新增或恢复: +1
        UPDATE boards SET feedback_count = feedback_count + 1 WHERE id = NEW.board_id;
    ELSIF TG_OP = 'UPDATE' AND OLD.board_id != NEW.board_id THEN
        -- 移动看板: 旧看板 -1, 新看板 +1
        UPDATE boards SET feedback_count = feedback_count - 1 WHERE id = OLD.board_id;
        UPDATE boards SET feedback_count = feedback_count + 1 WHERE id = NEW.board_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

### 方案 4: 添加数据一致性检查

在系统管理后台添加"数据一致性检查"功能，定期自动检查并修复：

```python
# backend/app/admin/api/v1/system.py

@router.post("/system/check-data-consistency")
async def check_data_consistency(db: CurrentSession):
    """检查并修复数据一致性"""
    issues = []
    
    # 检查看板计数
    boards = await db.execute(select(Board))
    for board in boards.scalars():
        actual_count = await db.scalar(
            select(func.count(Feedback.id))
            .where(Feedback.board_id == board.id, Feedback.deleted_at.is_(None))
        )
        if board.feedback_count != actual_count:
            issues.append({
                "type": "board_feedback_count",
                "board_id": board.id,
                "board_name": board.name,
                "current": board.feedback_count,
                "actual": actual_count,
            })
            # 自动修复
            board.feedback_count = actual_count
    
    return {"issues": issues, "fixed": len(issues)}
```

## 验证步骤

执行修复后，验证数据是否一致：

1. **检查数据库触发器计数**
   ```bash
   cd server
   python diagnose_board_count_mismatch.py
   ```

2. **检查前端显示**
   - 打开反馈列表页面
   - 清除所有筛选条件
   - 对比左侧栏看板计数和列表总数

3. **检查 API 返回数据**
   ```bash
   # 获取看板列表
   curl http://localhost:8000/api/v1/boards
   
   # 获取反馈列表（不带筛选）
   curl http://localhost:8000/api/v1/feedbacks?board_ids=default-board
   ```

## 总结

**问题根源**: 
1. 数据库触发器计数与实际不一致（主要原因）
2. 前端筛选条件持久化可能导致显示差异（次要原因）

**修复优先级**:
1. 🔴 **立即执行**: 运行 `refresh_board_stats.py` 修复触发器计数
2. 🟡 **短期优化**: 添加"重置筛选"按钮，方便用户清除筛选条件
3. 🟢 **长期优化**: 优化触发器逻辑，改为增量更新，提升性能

**预防措施**:
- 添加定期数据一致性检查任务
- 在系统管理后台提供手动触发修复功能
- 监控触发器执行情况，及时发现异常
