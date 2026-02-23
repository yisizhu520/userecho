<script setup lang="ts">
import { ref } from 'vue';
import { useVbenModal } from '@vben/common-ui';
import { message } from 'ant-design-vue';
import { getFeedbackList } from '#/api';

interface Props {
  topicId: string;
}

const props = defineProps<Props>();
const emit = defineEmits(['success']);

// 状态
const loading = ref(false);
const submitting = ref(false);
const feedbacks = ref<any[]>([]);
const selectedFeedbackIds = ref<string[]>([]);
const total = ref(0);

// 搜索条件
const searchParams = ref({
  search_query: '',
  derived_status: ['pending'], // 默认只看待处理的（未关联的）
  skip: 0,
  limit: 20
});

// 加载反馈列表
const loadFeedbacks = async () => {
    loading.value = true;
    try {
        const res = await getFeedbackList({
            ...searchParams.value,
            // 确保不加载已经关联的（虽然 derived_status='pending' 已经涵盖了大部分，但为了保险可以加过滤，不过API暂不支持 exclude_topic_id）
        });
        feedbacks.value = res;
        total.value = res.length; // API 目前返回的是 list，没返回 total，暂时这样
    } catch (error) {
        message.error('加载反馈列表失败');
    } finally {
        loading.value = false;
    }
};

// 搜索处理 (Debounce handled by user input speed naturally, or add proper debounce if needed)
let searchTimer: any;
const handleSearch = () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {
        searchParams.value.skip = 0;
        loadFeedbacks();
    }, 500);
};

// Modal 定义
const [Modal, modalApi] = useVbenModal({
  title: '关联现有反馈',
  fullscreen: false,
  class: 'w-[800px]',
  onOpenChange(isOpen) {
    if (isOpen) {
      selectedFeedbackIds.value = [];
      searchParams.value.search_query = '';
      loadFeedbacks();
    }
  },
  async onConfirm() {
    if (selectedFeedbackIds.value.length === 0) {
        message.warning('请至少选择一条反馈');
        return;
    }
    
    submitting.value = true;
    modalApi.setState({ confirmLoading: true });
    
    try {
        // 调用父组件传递的 API 方法，或者直接在这里引入 API
        // 为了解耦，这里 emit 事件，让父组件处理，或者父组件把 API 传进来
        // 但为了方便，直接在这里调用 API 也可以
        const { linkFeedbacksToTopic } = await import('#/api/userecho/topic');
        await linkFeedbacksToTopic(props.topicId, selectedFeedbackIds.value);
        
        message.success(`成功关联 ${selectedFeedbackIds.value.length} 条反馈`);
        emit('success');
        modalApi.close();
    } catch (error) {
        message.error('关联失败');
    } finally {
        submitting.value = false;
        modalApi.setState({ confirmLoading: false });
    }
  },
});

</script>

<template>
  <Modal>
    <div class="p-4">
      <!-- 搜索栏 -->
      <div class="mb-4 flex gap-4">
        <a-input-search
            v-model:value="searchParams.search_query"
            placeholder="搜索反馈内容..."
            allow-clear
            enter-button
            @search="handleSearch"
            style="width: 100%"
        />
        
        <!-- 过滤器 -->
        <a-select 
            v-model:value="searchParams.derived_status"
            mode="multiple"
            style="min-width: 200px"
            placeholder="状态过滤"
            @change="handleSearch"
        >
            <a-select-option value="pending">未关联 (待处理)</a-select-option>
            <a-select-option value="planned">已计划</a-select-option>
            <a-select-option value="in_progress">进行中</a-select-option>
            <a-select-option value="completed">已完成</a-select-option>
        </a-select>
      </div>

      <!-- 列表 -->
      <a-table
        row-key="id"
        :loading="loading"
        :data-source="feedbacks"
        :pagination="false"
        :scroll="{ y: 400 }"
        :row-selection="{
            selectedRowKeys: selectedFeedbackIds,
            onChange: (keys: string[]) => selectedFeedbackIds = keys
        }"
      >
        <a-table-column title="反馈内容" data-index="content" :width="400">
            <template #default="{ text }">
                <div class="truncate-2-lines" :title="text">{{ text }}</div>
            </template>
        </a-table-column>
        <a-table-column title="提交人" data-index="submitter">
             <template #default="{ record }">
                <span v-if="record.customer_name">{{ record.customer_name }}</span>
                <span v-else-if="record.external_user_name">{{ record.external_user_name }}</span>
                <span v-else>匿名</span>
            </template>
        </a-table-column>
        <a-table-column title="时间" data-index="submitted_at" :width="150">
             <template #default="{ text }">
                {{ text?.substring(0, 10) }}
            </template>
        </a-table-column>
      </a-table>
    </div>
  </Modal>
</template>

<style scoped>
.truncate-2-lines {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    text-overflow: ellipsis;
}
</style>
