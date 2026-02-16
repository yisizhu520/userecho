import { ref, watch, onMounted } from 'vue';

interface UseFilterStorageOptions<T> {
    key: string;
    defaultValue: T;
}

/**
 * 筛选状态持久化 Hook
 * @param options 配置项
 */
export function useFilterStorage<T>(options: UseFilterStorageOptions<T>) {
    const { key, defaultValue } = options;
    const state = ref<T>(defaultValue);

    // 初始化从 localStorage 读取
    const init = () => {
        const stored = localStorage.getItem(key);
        if (stored) {
            try {
                const parsed = JSON.parse(stored);
                // 合并默认值和存储值，防止后续增加字段导致问题
                if (typeof defaultValue === 'object' && defaultValue !== null) {
                    state.value = { ...defaultValue, ...parsed };
                } else {
                    state.value = parsed;
                }
            } catch (e) {
                console.error(`Failed to parse filter storage for key: ${key}`, e);
                state.value = defaultValue;
            }
        } else {
            state.value = defaultValue;
        }
    };

    // 监听变化并保存
    watch(
        state,
        (newValue) => {
            localStorage.setItem(key, JSON.stringify(newValue));
        },
        { deep: true }
    );

    onMounted(() => {
        init();
    });

    return {
        state,
    };
}
