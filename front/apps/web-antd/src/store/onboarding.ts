import type { Component } from 'vue';

import type {
    CreateBoardParams,
    CreateBoardResult,
    CreateTenantParams,
    CreateTenantResult,
    OnboardingStatus,
} from '#/api';

import { computed, ref } from 'vue';

import { defineStore } from 'pinia';

import {
    checkSlugApi,
    completeOnboardingApi,
    createBoardApi,
    createTenantApi,
    generateSlugApi,
    getOnboardingStatusApi,
} from '#/api';

/** 引导步骤定义 */
export interface OnboardingStep {
    id: string;
    name: string;
    description: string;
    order: number;
    required: boolean;
    component?: Component;
}

/** 引导步骤列表 */
const ONBOARDING_STEPS: OnboardingStep[] = [
    {
        id: 'create-tenant',
        name: '创建团队',
        description: '设置您的公司或团队信息',
        order: 1,
        required: true,
    },
    {
        id: 'create-board',
        name: '创建看板',
        description: '创建第一个反馈收集看板',
        order: 2,
        required: true,
    },
    {
        id: 'complete',
        name: '开始使用',
        description: '一切就绪，开始使用',
        order: 3,
        required: true,
    },
];

// 本地存储 key
const STORAGE_KEY = 'onboarding_progress';

/**
 * 引导流程 Store
 */
export const useOnboardingStore = defineStore('onboarding', () => {
    // 状态
    const steps = ref<OnboardingStep[]>(ONBOARDING_STEPS.map((s) => ({ ...s })));
    const currentStepIndex = ref(0);
    const needsOnboarding = ref(false);
    const isLoading = ref(false);
    const error = ref<string | null>(null);

    // 创建的资源
    const tenantId = ref<string | null>(null);
    const tenantData = ref<CreateTenantResult | null>(null);
    const boardId = ref<string | null>(null);
    const boardData = ref<CreateBoardResult | null>(null);
    const completedSteps = ref<string[]>([]);

    // 计算属性
    const currentStep = computed(() => steps.value[currentStepIndex.value]);
    const currentStepId = computed(() => currentStep.value?.id);
    const isFirstStep = computed(() => currentStepIndex.value === 0);
    const isLastStep = computed(
        () => currentStepIndex.value === steps.value.length - 1,
    );
    const progress = computed(
        () => ((currentStepIndex.value + 1) / steps.value.length) * 100,
    );

    /**
     * 从本地存储恢复进度
     */
    function restoreProgress() {
        try {
            const saved = localStorage.getItem(STORAGE_KEY);
            if (saved) {
                const data = JSON.parse(saved);
                if (data.tenantId) tenantId.value = data.tenantId;
                if (data.boardId) boardId.value = data.boardId;
                if (data.completedSteps)
                    completedSteps.value = data.completedSteps;

                // 根据已完成的步骤确定当前步骤
                if (data.completedSteps?.includes('create-board')) {
                    currentStepIndex.value = 2; // complete
                } else if (data.completedSteps?.includes('create-tenant')) {
                    currentStepIndex.value = 1; // create-board
                }
            }
        } catch {
            // 忽略解析错误
        }
    }

    /**
     * 保存进度到本地存储
     */
    function saveProgress() {
        try {
            localStorage.setItem(
                STORAGE_KEY,
                JSON.stringify({
                    tenantId: tenantId.value,
                    boardId: boardId.value,
                    completedSteps: completedSteps.value,
                    currentStep: currentStepId.value,
                }),
            );
        } catch {
            // 忽略存储错误
        }
    }

    /**
     * 清除存储的进度
     */
    function clearProgress() {
        try {
            localStorage.removeItem(STORAGE_KEY);
        } catch {
            // 忽略错误
        }
    }

    /**
     * 检查引导状态
     */
    async function checkOnboardingStatus(): Promise<boolean> {
        try {
            isLoading.value = true;
            error.value = null;

            const status: OnboardingStatus = await getOnboardingStatusApi();
            needsOnboarding.value = status.needs_onboarding;

            if (status.needs_onboarding) {
                // 恢复之前的进度
                if (status.tenant_id) tenantId.value = status.tenant_id;
                if (status.board_id) boardId.value = status.board_id;
                completedSteps.value = status.completed_steps || [];

                // 设置当前步骤
                if (status.current_step) {
                    const stepIndex = steps.value.findIndex(
                        (s) => s.id === status.current_step,
                    );
                    if (stepIndex >= 0) {
                        currentStepIndex.value = stepIndex;
                    }
                }

                // 同时尝试从本地存储恢复额外数据
                restoreProgress();
            } else {
                // 不需要引导，清除本地存储
                clearProgress();
            }

            return status.needs_onboarding;
        } catch (e: any) {
            error.value = e.message || '检查引导状态失败';
            console.error('Failed to check onboarding status:', e);
            return false;
        } finally {
            isLoading.value = false;
        }
    }

    /**
     * 检查 Slug 可用性
     */
    async function checkSlugAvailable(
        slug: string,
    ): Promise<{ available: boolean; suggestion: string | null }> {
        try {
            const result = await checkSlugApi(slug);
            return {
                available: result.available,
                suggestion: result.suggestion,
            };
        } catch (e: any) {
            console.error('Failed to check slug:', e);
            return { available: false, suggestion: null };
        }
    }

    /**
     * 生成 Slug
     */
    async function generateSlug(name: string): Promise<string> {
        try {
            const result = await generateSlugApi(name);
            return result.slug;
        } catch (e: any) {
            console.error('Failed to generate slug:', e);
            // 返回一个简单的转换结果
            return name
                .toLowerCase()
                .replaceAll(/[\s_]+/g, '-')
                .replaceAll(/[^\da-z-]/g, '')
                .slice(0, 50);
        }
    }

    /**
     * 创建租户
     */
    async function createTenant(data: CreateTenantParams): Promise<boolean> {
        try {
            isLoading.value = true;
            error.value = null;

            const result = await createTenantApi(data);
            tenantId.value = result.id;
            tenantData.value = result;
            completedSteps.value.push('create-tenant');

            // 保存进度
            saveProgress();

            // 进入下一步
            nextStep();

            return true;
        } catch (e: any) {
            error.value = e.message || '创建团队失败';
            console.error('Failed to create tenant:', e);
            return false;
        } finally {
            isLoading.value = false;
        }
    }

    /**
     * 创建看板
     */
    async function createBoard(data: CreateBoardParams): Promise<boolean> {
        try {
            isLoading.value = true;
            error.value = null;

            const result = await createBoardApi(data);
            boardId.value = result.id;
            boardData.value = result;
            completedSteps.value.push('create-board');

            // 保存进度
            saveProgress();

            // 进入下一步
            nextStep();

            return true;
        } catch (e: any) {
            error.value = e.message || '创建看板失败';
            console.error('Failed to create board:', e);
            return false;
        } finally {
            isLoading.value = false;
        }
    }

    /**
     * 完成引导
     */
    async function completeOnboarding(): Promise<string | null> {
        try {
            isLoading.value = true;
            error.value = null;

            const result = await completeOnboardingApi();

            if (result.success) {
                completedSteps.value.push('complete');
                needsOnboarding.value = false;

                // 清除本地存储
                clearProgress();

                return result.redirect_path;
            }

            return null;
        } catch (e: any) {
            error.value = e.message || '完成引导失败';
            console.error('Failed to complete onboarding:', e);
            return null;
        } finally {
            isLoading.value = false;
        }
    }

    /**
     * 下一步
     */
    function nextStep() {
        if (currentStepIndex.value < steps.value.length - 1) {
            currentStepIndex.value++;
            saveProgress();
        }
    }

    /**
     * 上一步
     */
    function prevStep() {
        if (currentStepIndex.value > 0) {
            currentStepIndex.value--;
            saveProgress();
        }
    }

    /**
     * 跳转到指定步骤
     */
    function goToStep(stepId: string) {
        const stepIndex = steps.value.findIndex((s) => s.id === stepId);
        if (stepIndex >= 0) {
            currentStepIndex.value = stepIndex;
            saveProgress();
        }
    }

    /**
     * 重置状态
     */
    function $reset() {
        currentStepIndex.value = 0;
        needsOnboarding.value = false;
        isLoading.value = false;
        error.value = null;
        tenantId.value = null;
        tenantData.value = null;
        boardId.value = null;
        boardData.value = null;
        completedSteps.value = [];
        clearProgress();
    }

    return {
        // 状态
        steps,
        currentStep,
        currentStepId,
        currentStepIndex,
        needsOnboarding,
        isLoading,
        error,
        tenantId,
        tenantData,
        boardId,
        boardData,
        completedSteps,

        // 计算属性
        isFirstStep,
        isLastStep,
        progress,

        // 方法
        checkOnboardingStatus,
        checkSlugAvailable,
        generateSlug,
        createTenant,
        createBoard,
        completeOnboarding,
        nextStep,
        prevStep,
        goToStep,
        $reset,
    };
});
