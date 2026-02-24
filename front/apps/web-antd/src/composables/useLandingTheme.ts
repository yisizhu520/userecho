import { computed } from 'vue';
import { usePreferences } from '@vben/preferences';
import { preferencesManager } from '@vben/preferences';

export type LandingTheme = 'dark' | 'light';

// 一次性清理旧的主题设置
const OLD_STORAGE_KEY = 'landing-theme';
if (typeof localStorage !== 'undefined' && localStorage.getItem(OLD_STORAGE_KEY)) {
  localStorage.removeItem(OLD_STORAGE_KEY);
}

/**
 * Landing 页面主题管理
 * 统一使用 Vben 的 preferences 系统，确保全站主题一致
 */
export function useLandingTheme() {
  const { theme: vbenTheme, isDark: isVbenDark } = usePreferences();

  // 将 vben 的 theme ('dark' | 'light') 映射为 LandingTheme
  const theme = computed<LandingTheme>(() => vbenTheme.value as LandingTheme);

  const setTheme = (newTheme: LandingTheme) => {
    // 更新 Vben preferences
    preferencesManager.updatePreferences({
      theme: { mode: newTheme },
    });

    // 同步更新 Landing 页面的 CSS class
    document.documentElement.classList.remove('theme-dark', 'theme-light');
    document.documentElement.classList.add(`theme-${newTheme}`);
  };

  const toggleTheme = () => {
    const newTheme = theme.value === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
  };

  // Initialize theme on mount
  const initTheme = () => {
    document.documentElement.classList.add(`theme-${theme.value}`);
  };

  return {
    theme,
    setTheme,
    toggleTheme,
    initTheme,
    isDark: () => isVbenDark.value,
    isLight: () => !isVbenDark.value,
  };
}
