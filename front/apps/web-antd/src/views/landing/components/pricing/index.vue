<script lang="ts" setup>
import { ref, computed, onMounted } from 'vue';
import type { BillingPeriod } from './pricing-data';
import { pricingTiers } from './pricing-data';
import PricingHeader from './PricingHeader.vue';
import BillingToggle from './BillingToggle.vue';
import PricingCard from './PricingCard.vue';
import PricingFAQ from './PricingFAQ.vue';

const billingPeriod = ref<BillingPeriod>('monthly');
const sectionRef = ref<HTMLElement>();
const isVisible = ref(false);

// 计算当前计费周期下的定价配置
const computedTiers = computed(() => {
  return pricingTiers.map((tier) => {
    const price = billingPeriod.value === 'monthly' ? tier.monthlyPrice : tier.yearlyPrice;
    return {
      ...tier,
      price,
    };
  });
});

onMounted(() => {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          isVisible.value = true;
        }
      });
    },
    { threshold: 0.1 }
  );

  if (sectionRef.value) {
    observer.observe(sectionRef.value);
  }
});
</script>

<template>
  <section id="pricing" ref="sectionRef" class="pricing-section" :class="{ 'is-visible': isVisible }">
    <div class="section-container">
      <PricingHeader />
      <BillingToggle v-model="billingPeriod" />
      <div class="pricing-cards">
        <PricingCard
          v-for="tier in computedTiers"
          :key="tier.id"
          :tier="tier"
          :billing-period="billingPeriod"
        />
      </div>
      <PricingFAQ />
    </div>
  </section>
</template>

<style scoped>
.pricing-section {
  position: relative;
  padding: 6rem 2rem;
  background: var(--lp-bg-secondary);
  opacity: 0;
  transform: translateY(30px);
  transition: all 0.8s ease-out;
}

.pricing-section.is-visible {
  opacity: 1;
  transform: translateY(0);
}

.pricing-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(59, 130, 246, 0.3), transparent);
}

.section-container {
  max-width: 1200px;
  margin: 0 auto;
}

.pricing-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1.5rem;
  margin-bottom: 2rem;
}

/* 响应式 */
@media (max-width: 1200px) {
  .pricing-cards {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .pricing-section {
    padding: 4rem 1rem;
  }

  .pricing-cards {
    grid-template-columns: 1fr;
    gap: 1.25rem;
  }
}
</style>
