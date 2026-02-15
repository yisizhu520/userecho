<script lang="ts" setup>
import { ref } from 'vue';
import { faqItems } from './pricing-data';

const openItems = ref<Set<number>>(new Set());

const toggleItem = (index: number) => {
  if (openItems.value.has(index)) {
    openItems.value.delete(index);
  } else {
    openItems.value.add(index);
  }
};

const isOpen = (index: number) => openItems.value.has(index);
</script>

<template>
  <div class="pricing-faq">
    <h3 class="faq-title">常见问题</h3>
    <div class="faq-list">
      <div
        v-for="(item, index) in faqItems"
        :key="index"
        class="faq-item"
        :class="{ open: isOpen(index) }"
      >
        <button class="faq-question" @click="toggleItem(index)">
          <span>{{ item.question }}</span>
          <svg class="faq-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="6 9 12 15 18 9"/>
          </svg>
        </button>
        <div class="faq-answer">
          <p>{{ item.answer }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.pricing-faq {
  max-width: 800px;
  margin: 4rem auto 0;
}

.faq-title {
  font-family: var(--lp-font-display);
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--lp-text-primary);
  text-align: center;
  margin-bottom: 2rem;
}

.faq-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.faq-item {
  background: var(--lp-bg-card);
  border: 1px solid var(--lp-border-default);
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s ease;
}

.faq-item.open {
  border-color: var(--lp-primary-400);
}

.faq-question {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 1.25rem 1.5rem;
  background: transparent;
  border: none;
  cursor: pointer;
  text-align: left;
  font-size: 1rem;
  font-weight: 500;
  color: var(--lp-text-primary);
  transition: color 0.2s ease;
}

.faq-question:hover {
  color: var(--lp-primary-400);
}

.faq-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  transition: transform 0.3s ease;
  color: var(--lp-text-tertiary);
}

.faq-item.open .faq-icon {
  transform: rotate(180deg);
  color: var(--lp-primary-400);
}

.faq-answer {
  max-height: 0;
  overflow: hidden;
  transition: max-height 0.3s ease, padding 0.3s ease;
}

.faq-item.open .faq-answer {
  max-height: 200px;
  padding: 0 1.5rem 1.5rem;
}

.faq-answer p {
  font-size: 0.95rem;
  line-height: 1.7;
  color: var(--lp-text-secondary);
}

@media (max-width: 768px) {
  .pricing-faq {
    margin: 3rem auto 0;
  }

  .faq-title {
    font-size: 1.5rem;
  }

  .faq-question {
    padding: 1rem 1.25rem;
    font-size: 0.95rem;
  }

  .faq-item.open .faq-answer {
    padding: 0 1.25rem 1.25rem;
  }
}
</style>
