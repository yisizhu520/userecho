<script lang="ts" setup>
import { computed } from 'vue';
import type { PricingTier, BillingPeriod } from './pricing-data';
import { useLandingTheme } from '#/composables/useLandingTheme';

interface Props {
  tier: PricingTier;
  billingPeriod: BillingPeriod;
}

const props = defineProps<Props>();

const { theme } = useLandingTheme();
const isDark = computed(() => theme.value === 'dark');

const displayPrice = computed(() => {
  if (props.tier.isFree) return '免费';
  if (props.tier.id === 'enterprise') return '联系销售';
  return `¥${props.billingPeriod === 'monthly' ? props.tier.monthlyPrice : Math.round(props.tier.yearlyPrice / 12)}`;
});

const pricePeriod = computed(() => {
  if (props.tier.isFree) return '永久免费';
  if (props.tier.id === 'enterprise') return '';
  return props.billingPeriod === 'monthly' ? '/月' : '/年';
});

const originalPrice = computed(() => {
  if (props.tier.isFree || props.tier.id === 'enterprise') return null;
  if (props.billingPeriod === 'yearly') {
    return `¥${props.tier.monthlyPrice * 12}`;
  }
  return null;
});

const savings = computed(() => {
  if (props.tier.isFree || props.tier.id === 'enterprise') return null;
  if (props.billingPeriod === 'yearly') {
    const savingsAmount = props.tier.monthlyPrice * 12 - props.tier.yearlyPrice;
    return `省¥${savingsAmount}`;
  }
  return null;
});

// 滚动到联系区域
const scrollToContact = () => {
  const contactSection = document.getElementById('contact');
  if (contactSection) {
    contactSection.scrollIntoView({ behavior: 'smooth' });
  }
};

const cardClass = computed(() => ({
  'pricing-card': true,
  'recommended': props.tier.isRecommended,
  'enterprise': props.tier.id === 'enterprise',
  'is-dark': isDark.value,
}));
</script>

<template>
  <div :class="cardClass">
    <!-- 推荐标签 -->
    <div v-if="tier.isRecommended" class="recommend-badge">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
      </svg>
      <span>推荐</span>
    </div>

    <!-- 卡片头部 -->
    <div class="card-header">
      <h3 class="tier-name">{{ tier.name }}</h3>
      <p class="tier-tagline">{{ tier.tagline }}</p>
    </div>

    <!-- 价格显示 -->
    <div class="price-section">
      <div v-if="originalPrice" class="original-price">{{ originalPrice }}/年</div>
      <div class="price-display">
        <span class="price-value">{{ displayPrice }}</span>
        <span v-if="pricePeriod" class="price-period">{{ pricePeriod }}</span>
        <span v-if="savings" class="savings-badge">{{ savings }}</span>
      </div>
    </div>

    <!-- CTA 按钮 -->
    <button class="cta-button" :class="{ primary: tier.isRecommended }" @click="scrollToContact">
      {{ tier.ctaText }}
      <svg v-if="tier.id !== 'enterprise'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M5 12h14M12 5l7 7-7 7"/>
      </svg>
    </button>

    <!-- 功能列表 -->
    <div class="features-list">
      <div
        v-for="(feature, index) in tier.features"
        :key="index"
        class="feature-item"
        :class="{ included: feature.included, excluded: !feature.included, highlight: feature.highlight }"
      >
        <svg class="feature-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <polyline v-if="feature.included" points="20 6 9 17 4 12"/>
          <line v-else x1="18" y1="6" x2="6" y2="18"/>
          <line v-if="!feature.included" x1="6" y1="6" x2="18" y2="18"/>
        </svg>
        <span class="feature-text">{{ feature.text }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.pricing-card {
  position: relative;
  background: var(--lp-bg-card);
  border: 1px solid var(--lp-border-default);
  border-radius: 20px;
  padding: 2rem;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  min-height: 700px;
}

.pricing-card.is-dark {
  background: rgba(15, 23, 42, 0.8);
  border-color: rgba(148, 163, 184, 0.15);
}

.pricing-card.is-dark .tier-name {
  color: #f8fafc;
}

.pricing-card.is-dark .tier-tagline {
  color: #94a3b8;
}

.pricing-card.is-dark .price-value {
  color: #f8fafc;
}

.pricing-card.is-dark .feature-item.highlight {
  color: #f8fafc;
}

.pricing-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
}

.pricing-card.recommended {
  border-color: var(--lp-accent-cyan);
  box-shadow: 0 0 40px var(--lp-glow-cyan);
}

.pricing-card.enterprise {
  border-color: var(--lp-accent-purple);
  background: linear-gradient(135deg, var(--lp-bg-card) 0%, rgba(139, 92, 246, 0.05) 100%);
}

/* 推荐标签 */
.recommend-badge {
  position: absolute;
  top: -12px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.4rem 1rem;
  background: var(--lp-gradient-cool);
  border-radius: 100px;
  font-size: 0.8rem;
  font-weight: 600;
  color: #ffffff;
  box-shadow: 0 4px 12px var(--lp-glow-cyan);
}

.recommend-badge svg {
  width: 14px;
  height: 14px;
}

/* 卡片头部 */
.card-header {
  text-align: center;
  margin-bottom: 0.5rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--lp-border-subtle);
  height: 160px;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  padding-top: 0.5rem;
}

.tier-name {
  display: block;
  font-family: var(--lp-font-display);
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--lp-text-primary);
  margin-bottom: 1.5rem;
  letter-spacing: -0.01em;
  line-height: 1.3;
}

.pricing-card.recommended .tier-name {
  background: var(--lp-gradient-cool);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.tier-tagline {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  font-size: 0.9rem;
  color: var(--lp-text-tertiary);
  line-height: 1.4;
}

/* 价格区域 */
.price-section {
  text-align: center;
  margin-bottom: 1.5rem;
  min-height: 110px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.original-price {
  font-size: 0.9rem;
  color: var(--lp-text-muted);
  text-decoration: line-through;
  margin-bottom: 0.25rem;
}

.price-display {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.price-value {
  font-family: var(--lp-font-display);
  font-size: 3rem;
  font-weight: 800;
  color: var(--lp-text-primary);
  flex-shrink: 0;
}

.pricing-card.recommended .price-value {
  background: var(--lp-gradient-hero);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.price-period {
  font-size: 1rem;
  color: var(--lp-text-tertiary);
}

.savings-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  background: var(--lp-accent-emerald);
  color: #ffffff;
  border-radius: 100px;
  font-size: 0.8rem;
  font-weight: 600;
}

/* CTA 按钮 */
.cta-button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  width: 100%;
  padding: 1rem;
  background: var(--lp-bg-tertiary);
  border: 1px solid var(--lp-border-default);
  border-radius: 12px;
  color: var(--lp-text-primary);
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-top: auto;
  margin-bottom: 1.5rem;
}

.cta-button:hover {
  background: var(--lp-bg-elevated);
  border-color: var(--lp-primary-400);
  transform: translateY(-2px);
}

.cta-button.primary {
  background: var(--lp-gradient-cool);
  border: none;
  color: #ffffff;
  box-shadow: 0 4px 16px var(--lp-glow-cyan);
}

.cta-button.primary:hover {
  box-shadow: 0 8px 24px var(--lp-glow-primary);
}

.cta-button svg {
  transition: transform 0.3s ease;
}

.cta-button:hover svg {
  transform: translateX(4px);
}

/* 功能列表 */
.features-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  flex: 1;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.9rem;
  color: var(--lp-text-secondary);
  transition: all 0.2s ease;
}

.feature-item.excluded {
  opacity: 0.4;
}

.feature-item.highlight {
  color: var(--lp-text-primary);
  font-weight: 500;
}

.feature-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  color: var(--lp-accent-emerald);
}

.feature-item.excluded .feature-icon {
  color: var(--lp-text-muted);
}

.feature-text {
  line-height: 1.4;
}

/* 响应式 */
@media (max-width: 768px) {
  .pricing-card {
    padding: 1.5rem;
  }

  .tier-name {
    font-size: 1.3rem;
  }

  .price-value {
    font-size: 2.5rem;
  }
}
</style>
