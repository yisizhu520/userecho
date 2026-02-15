<script lang="ts" setup>
import { computed } from 'vue';
import type { BillingPeriod } from './pricing-data';

interface Props {
  modelValue: BillingPeriod;
}

interface Emits {
  (e: 'update:modelValue', value: BillingPeriod): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

const isMonthly = computed(() => props.modelValue === 'monthly');

const setMonthly = () => {
  emit('update:modelValue', 'monthly');
};

const setYearly = () => {
  emit('update:modelValue', 'yearly');
};
</script>

<template>
  <div class="billing-toggle">
    <button
      class="toggle-button"
      :class="{ active: isMonthly }"
      @click="setMonthly"
    >
      <span class="button-text">月付</span>
    </button>
    <button
      class="toggle-button"
      :class="{ active: !isMonthly }"
      @click="setYearly"
    >
      <span class="button-text">年付</span>
      <span class="discount-badge">省20%</span>
    </button>
    <div class="toggle-slider" :class="{ yearly: !isMonthly }"></div>
  </div>
</template>

<style scoped>
.billing-toggle {
  position: relative;
  display: flex;
  align-items: center;
  background: var(--lp-bg-tertiary);
  border-radius: 12px;
  padding: 4px;
  margin: 0 auto 3rem;
  width: fit-content;
}

.toggle-button {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  min-width: 140px;
  padding: 0.85rem 2rem;
  background: transparent;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 1.05rem;
  font-weight: 500;
  color: var(--lp-text-tertiary);
}

.toggle-button.active {
  color: var(--lp-text-primary);
  font-weight: 600;
}

.toggle-button:hover:not(.active) {
  color: var(--lp-text-secondary);
}

.button-text {
  position: relative;
  z-index: 1;
}

.discount-badge {
  display: inline-block;
  padding: 0.2rem 0.5rem;
  background: var(--lp-accent-emerald);
  color: #ffffff;
  border-radius: 100px;
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
}

.toggle-slider {
  position: absolute;
  top: 4px;
  left: 4px;
  width: calc(50% - 4px);
  height: calc(100% - 8px);
  background: var(--lp-bg-card);
  border-radius: 10px;
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.toggle-slider.yearly {
  transform: translateX(calc(100% + 4px));
}

@media (max-width: 768px) {
  .billing-toggle {
    width: 100%;
    max-width: 340px;
    margin-left: auto;
    margin-right: auto;
  }

  .toggle-button {
    min-width: auto;
    flex: 1;
    padding: 0.75rem 1rem;
    font-size: 0.95rem;
  }

  .discount-badge {
    font-size: 0.7rem;
    padding: 0.15rem 0.4rem;
  }
}
</style>
