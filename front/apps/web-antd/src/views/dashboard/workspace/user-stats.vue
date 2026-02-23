<script lang="ts" setup>

interface Props {
  stats?: {
    total: number;
    new_count: number;
    active_7d: number;
  };
  loading?: boolean;
}

withDefaults(defineProps<Props>(), {
  stats: () => ({
    total: 0,
    new_count: 0,
    active_7d: 0,
  }),
  loading: false,
});
</script>

<template>
  <div class="grid grid-cols-1 gap-4 md:grid-cols-3">
    <!-- Card 1: Total -->
    <div class="rounded-xl border border-border bg-card p-4 shadow-sm">
      <div class="flex items-center justify-between">
        <span class="text-sm text-muted-foreground">总客户数</span>
        <span class="icon-[lucide--users] text-primary h-4 w-4"></span>
      </div>
      <div class="mt-2 text-2xl font-bold">
        {{ loading ? '-' : stats.total }}
      </div>
      <div class="mt-1 text-xs text-muted-foreground">平台累积客户总数</div>
    </div>

    <!-- Card 2: Active -->
    <div class="rounded-xl border border-border bg-card p-4 shadow-sm">
      <div class="flex items-center justify-between">
        <span class="text-sm text-muted-foreground">近7日活跃客户</span>
        <span class="icon-[lucide--activity] text-success h-4 w-4"></span>
      </div>
      <div class="mt-2 text-2xl font-bold">
        {{ loading ? '-' : stats.active_7d }}
      </div>
      <div class="mt-1 text-xs text-muted-foreground">最近7天提交过反馈的客户</div>
    </div>

    <!-- Card 3: New -->
    <div class="rounded-xl border border-border bg-card p-4 shadow-sm">
      <div class="flex items-center justify-between">
        <span class="text-sm text-muted-foreground">本周新增客户</span>
        <span class="icon-[lucide--user-plus] text-warning h-4 w-4"></span>
      </div>
      <div class="mt-2 text-2xl font-bold">
        {{ loading ? '-' : stats.new_count }}
      </div>
      <div class="mt-1 text-xs text-muted-foreground">最近7天新注册的客户</div>
    </div>
  </div>
</template>
