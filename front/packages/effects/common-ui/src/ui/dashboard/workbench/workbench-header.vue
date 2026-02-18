<script lang="ts" setup>
import { VbenAvatar } from '@vben-core/shadcn-ui';

interface HeaderStats {
  pendingTopics: number;
  totalTopics: number;
  weeklyFeedbacks: number;
  totalFeedbacks: number;
}

interface Props {
  avatar?: string;
  stats?: HeaderStats;
}

defineOptions({
  name: 'WorkbenchHeader',
});

withDefaults(defineProps<Props>(), {
  avatar: '',
  stats: () => ({
    pendingTopics: 0,
    totalTopics: 0,
    weeklyFeedbacks: 0,
    totalFeedbacks: 0,
  }),
});
</script>
<template>
  <div class="card-box p-4 py-6 lg:flex">
    <VbenAvatar :src="avatar" class="size-20" />
    <div
      v-if="$slots.title || $slots.description"
      class="flex flex-col justify-center md:ml-6 md:mt-0"
    >
      <h1 v-if="$slots.title" class="text-md font-semibold md:text-xl">
        <slot name="title"></slot>
      </h1>
      <span v-if="$slots.description" class="text-foreground/80 mt-1">
        <slot name="description"></slot>
      </span>
    </div>
    <div class="mt-4 flex flex-1 justify-end md:mt-0">
      <div class="flex flex-col justify-center text-right">
        <span class="text-foreground/80"> 待处理 </span>
        <span class="text-2xl">{{ stats?.pendingTopics ?? 0 }}/{{ stats?.totalTopics ?? 0 }}</span>
      </div>

      <div class="mx-12 flex flex-col justify-center text-right md:mx-16">
        <span class="text-foreground/80"> 本周新增 </span>
        <span class="text-2xl">{{ stats?.weeklyFeedbacks ?? 0 }}</span>
      </div>
      <div class="mr-4 flex flex-col justify-center text-right md:mr-10">
        <span class="text-foreground/80"> 反馈总数 </span>
        <span class="text-2xl">{{ stats?.totalFeedbacks ?? 0 }}</span>
      </div>
    </div>
  </div>
</template>
