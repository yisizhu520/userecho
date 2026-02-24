/**
 * 环境变量工具
 *
 * 统一管理前端环境变量，避免到处散落 import.meta.env
 */

/**
 * 是否为 Demo 模式
 */
export const isDemoMode = import.meta.env.VITE_DEMO_MODE === 'true';

/**
 * 是否为开发环境
 */
export const isDev = import.meta.env.DEV;

/**
 * 是否为生产环境
 */
export const isProd = import.meta.env.PROD;

/**
 * API 基础 URL
 */
export const apiBaseUrl = import.meta.env.VITE_GLOB_API_URL || '/api';

/**
 * 应用标题
 */
export const appTitle = import.meta.env.VITE_APP_TITLE || '回响';

/**
 * Turnstile Site Key
 */
export const turnstileSiteKey = import.meta.env.VITE_TURNSTILE_SITE_KEY || '';
