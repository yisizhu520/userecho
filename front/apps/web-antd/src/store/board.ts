/**
 * Board Store
 * 
 * 管理 Board 列表状态，支持反馈变更后自动刷新数量
 */
import { defineStore } from 'pinia';
import { ref } from 'vue';
import { getBoardList, type BoardApi } from '#/api';

export const useBoardStore = defineStore('board', () => {
    // 状态
    const boards = ref<BoardApi.Board[]>([]);
    const loading = ref(false);
    const lastRefreshTime = ref<number>(0);

    // 缓存时间（毫秒）- 5秒内不重复请求
    const CACHE_TTL = 5000;

    /**
     * 刷新 Board 列表
     * @param force 是否强制刷新（忽略缓存）
     */
    async function refreshBoards(force = false) {
        // 缓存判断：避免短时间内重复请求
        if (!force && Date.now() - lastRefreshTime.value < CACHE_TTL && boards.value.length > 0) {
            return;
        }

        try {
            loading.value = true;
            const response = await getBoardList();
            boards.value = response.boards || [];
            lastRefreshTime.value = Date.now();
        } catch (error) {
            console.error('Failed to refresh boards:', error);
        } finally {
            loading.value = false;
        }
    }

    /**
     * 强制刷新（用于增删操作后）
     */
    async function forceRefresh() {
        return refreshBoards(true);
    }

    /**
     * 重置状态
     */
    function $reset() {
        boards.value = [];
        loading.value = false;
        lastRefreshTime.value = 0;
    }

    return {
        // 状态
        boards,
        loading,
        lastRefreshTime,
        // 方法
        refreshBoards,
        forceRefresh,
        $reset,
    };
});
