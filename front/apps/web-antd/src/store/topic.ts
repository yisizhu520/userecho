import { ref } from 'vue';

import { defineStore } from 'pinia';

import { getPendingTopicCount } from '#/api';

/**
 * Topic Store - 管理主题相关的全局状态
 */
export const useTopicStore = defineStore('topic', () => {
    // 待确认的主题数量
    const pendingCount = ref<number>(0);

    // 是否正在加载
    const loading = ref(false);

    /**
     * 刷新待确认主题数量
     */
    async function refreshPendingCount() {
        try {
            loading.value = true;
            const result = await getPendingTopicCount();
            pendingCount.value = result.count;
        } catch (error) {
            console.error('Failed to refresh pending topic count:', error);
        } finally {
            loading.value = false;
        }
    }

    /**
     * 重置状态
     */
    function $reset() {
        pendingCount.value = 0;
        loading.value = false;
    }

    return {
        $reset,
        pendingCount,
        loading,
        refreshPendingCount,
    };
});
