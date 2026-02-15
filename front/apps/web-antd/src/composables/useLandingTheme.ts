import { ref, watch } from 'vue';

export type LandingTheme = 'dark' | 'light';

const STORAGE_KEY = 'landing-theme';

// Global theme state
const currentTheme = ref<LandingTheme>(
  (localStorage.getItem(STORAGE_KEY) as LandingTheme) || 'dark'
);

export function useLandingTheme() {
  const setTheme = (theme: LandingTheme) => {
    currentTheme.value = theme;
    localStorage.setItem(STORAGE_KEY, theme);
    document.documentElement.classList.remove('theme-dark', 'theme-light');
    document.documentElement.classList.add(`theme-${theme}`);
  };

  const toggleTheme = () => {
    setTheme(currentTheme.value === 'dark' ? 'light' : 'dark');
  };

  // Initialize theme on mount
  const initTheme = () => {
    document.documentElement.classList.add(`theme-${currentTheme.value}`);
  };

  return {
    theme: currentTheme,
    setTheme,
    toggleTheme,
    initTheme,
    isDark: () => currentTheme.value === 'dark',
    isLight: () => currentTheme.value === 'light',
  };
}
