<script lang="ts" setup>
import { computed } from 'vue';
import { useLandingTheme } from '#/composables/useLandingTheme';

const { theme, toggleTheme } = useLandingTheme();

const isDark = computed(() => theme.value === 'dark');
</script>

<template>
  <button
    class="theme-toggle"
    :class="{ 'is-dark': isDark, 'is-light': !isDark }"
    @click="toggleTheme"
    :title="isDark ? '切换到浅色主题' : '切换到深色主题'"
  >
    <span class="toggle-track">
      <span class="toggle-thumb">
        <svg v-if="isDark" class="icon-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <svg v-else class="icon-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <circle cx="12" cy="12" r="5" stroke-width="2"/>
          <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" stroke-width="2" stroke-linecap="round"/>
        </svg>
      </span>
    </span>
    <span class="toggle-label">{{ isDark ? '深色' : '浅色' }}</span>
  </button>
</template>

<style scoped>
.theme-toggle {
  position: fixed;
  top: 1rem;
  right: 1rem;
  z-index: 1001;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  background: var(--lp-bg-elevated);
  border: 1px solid var(--lp-border-default);
  border-radius: 100px;
  cursor: pointer;
  transition: all 0.3s ease;
  backdrop-filter: blur(12px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.theme-toggle:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.15);
}

.theme-toggle:active {
  transform: translateY(0);
}

.toggle-track {
  position: relative;
  width: 48px;
  height: 26px;
  background: var(--lp-bg-tertiary);
  border-radius: 100px;
  transition: background 0.3s ease;
}

.theme-toggle.is-dark .toggle-track {
  background: rgba(59, 130, 246, 0.2);
}

.theme-toggle.is-light .toggle-track {
  background: rgba(251, 191, 36, 0.2);
}

.toggle-thumb {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #3b82f6, #06b6d4);
  border-radius: 50%;
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.4);
}

.theme-toggle.is-dark .toggle-thumb {
  transform: translateX(0);
}

.theme-toggle.is-light .toggle-thumb {
  transform: translateX(22px);
  background: linear-gradient(135deg, #f59e0b, #ef4444);
  box-shadow: 0 2px 8px rgba(245, 158, 11, 0.4);
}

.toggle-thumb svg {
  width: 12px;
  height: 12px;
  color: #ffffff;
}

.toggle-label {
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--lp-text-secondary);
  padding-right: 0.25rem;
  transition: color 0.3s ease;
}

.theme-toggle:hover .toggle-label {
  color: var(--lp-text-primary);
}

/* Responsive */
@media (max-width: 768px) {
  .theme-toggle {
    top: auto;
    bottom: 1rem;
    right: 1rem;
  }

  .toggle-label {
    display: none;
  }
}

/* For navbar with login button, position below it */
@media (min-width: 769px) {
  .theme-toggle {
    top: 5rem;
  }
}
</style>
