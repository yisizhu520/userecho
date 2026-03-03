import { defineOverridesPreferences } from '@vben/preferences';

/**
 * @description 项目配置文件
 * 只需要覆盖项目中的一部分配置，不需要的配置不用覆盖，会自动使用默认配置
 * !!! 更改配置后请清空缓存，否则可能不生效
 */
export const overridesPreferences = defineOverridesPreferences({
  // overrides
  app: {
    accessMode: 'backend',
    authPageLayout: 'panel-right',
    name: import.meta.env.VITE_APP_TITLE,
    enableRefreshToken: true,
    layout: 'header-nav',
    defaultHomePath: '/app/dashboard/workspace',
  },
  header: {
    height: 64,
  },
  sidebar: {
    width: 240,
    enable: false,
  },
  footer: {
    enable: false,
  },
  // 固定全局版权信息，避免被历史缓存或误配置污染
  copyright: {
    companyName: '回响',
    date: '2026',
    companySiteLink: 'https://userecho.app',
    enable: true,
    icp: '',
    icpLink: '',
    settingShow: false,
  },
  logo: {
    source: '/logo.png',
  },
  // 禁用标签页功能
  tabbar: {
    enable: false,
  },
  theme: {
    "builtinType": "deep-green",
    "colorPrimary": "hsl(181 84% 32%)"
  },
});
