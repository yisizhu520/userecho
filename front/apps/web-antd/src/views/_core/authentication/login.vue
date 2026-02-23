<script lang="ts" setup>
import type { VbenFormSchema } from '@vben/common-ui';

import { computed, h, onMounted, onUnmounted, ref } from 'vue';

import { AuthenticationLogin, z } from '@vben/common-ui';
import { $t } from '@vben/locales';
import { useAccessStore } from '@vben/stores';

import { Image } from 'ant-design-vue';


import { useAuthStore } from '#/store';

defineOptions({ name: 'Login' });

const authStore = useAuthStore();
const accessStore = useAccessStore();

const imageSrc = ref('');
const captchaEnabled = ref(false);
const captchaExpireSeconds = ref(0);
let refreshTimer: null | ReturnType<typeof setTimeout> = null;

const refreshCaptcha = async () => {
  try {
    const captcha = await authStore.captcha();
    captchaEnabled.value = captcha.is_enabled;
    captchaExpireSeconds.value = captcha.expire_seconds;
    imageSrc.value = `data:image/png;base64, ${captcha.image}`;

    if (refreshTimer) {
      clearTimeout(refreshTimer);
      refreshTimer = null;
    }

    // 自动刷新（提前3秒刷新）
    if (captcha.is_enabled && captcha.expire_seconds > 0) {
      const refreshDelay = Math.max((captcha.expire_seconds - 3) * 1000, 1000);
      refreshTimer = setTimeout(() => {
        refreshCaptcha();
      }, refreshDelay);
    }
  } catch (error) {
    console.error(error);
  }
};

const formSchema = computed((): VbenFormSchema[] => {
  const baseFields: VbenFormSchema[] = [
    {
      component: 'VbenInput',
      componentProps: {
        placeholder: '请输入邮箱',
        type: 'email',
      },
      fieldName: 'email',
      label: '邮箱',
      rules: z.string().email({ message: '请输入有效的邮箱地址' }).min(1, { message: '请输入邮箱' }),
    },
    {
      component: 'VbenInputPassword',
      componentProps: {
        placeholder: $t('authentication.password'),
      },
      fieldName: 'password',
      label: $t('authentication.password'),
      rules: z.string().min(1, { message: $t('authentication.passwordTip') }),
    },
  ];

  if (captchaEnabled.value) {
    baseFields.push(
      {
        component: 'VbenInput',
        componentProps: {
          placeholder: $t('page.auth.captchaPlaceholder'),
        },
        fieldName: 'captcha',
        label: $t('authentication.password'),
        rules: z
          .string()
          .min(1, { message: $t('page.auth.captchaRequired') })
          .optional()
          .default(''),
        formItemClass: 'w-2/3',
      },
      {
        component: 'VbenInput',
        fieldName: 'uuid',
        formItemClass: 'hidden',
        dependencies: {
          trigger: (_, form) => {
            form.setValues({
              uuid: accessStore.captchaUuid,
            });
          },
          triggerFields: ['captchaImg'],
        },
      },
      {
        component: h(Image),
        componentProps: {
          src: imageSrc.value,
          width: 120,
          height: 40,
          preview: false,
          onClick: refreshCaptcha,
        },
        fieldName: 'captchaImg',
        formItemClass: 'ml-auto -mt-[74px]',
      },
    );
  }

  return baseFields;
});

onMounted(() => {
  refreshCaptcha();
});

onUnmounted(() => {
  if (refreshTimer) {
    clearTimeout(refreshTimer);
    refreshTimer = null;
  }
});
</script>

<template>
  <AuthenticationLogin
    :form-schema="formSchema"
    :loading="authStore.loginLoading"
    :show-code-login="false"
    :show-qrcode-login="false"
    :show-third-party-login="false"
    @submit="authStore.authLogin"
  >

  </AuthenticationLogin>
</template>
