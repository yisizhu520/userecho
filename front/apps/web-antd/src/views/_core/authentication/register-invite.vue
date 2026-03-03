<script lang="ts" setup>
import type { VbenFormSchema } from '@vben/common-ui';

import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import { AuthenticationRegister, z } from '@vben/common-ui';
import { useAccessStore, useUserStore } from '@vben/stores';

import { message } from 'ant-design-vue';

import { getAccessCodesApi, getUserInfoApi } from '#/api';
import { registerWithInvitation, validateInvitation } from '#/api/userecho/invitation';

defineOptions({ name: 'RegisterInvite' });

const route = useRoute();
const router = useRouter();
const accessStore = useAccessStore();
const userStore = useUserStore();

const loading = ref(false);
const validating = ref(true);
const invitationValid = ref(false);
const invitationInfo = ref<any>(null);
const errorMessage = ref('');
const inviteToken = ref('');

// 从 URL 获取邀请 token
onMounted(async () => {
  inviteToken.value = (route.query.invite as string) || '';

  if (!inviteToken.value) {
    errorMessage.value = '缺少邀请链接参数';
    validating.value = false;
    return;
  }

  // 验证邀请有效性
  try {
    const result = await validateInvitation(inviteToken.value);
    if (result.valid) {
      invitationValid.value = true;
      invitationInfo.value = result;
    } else {
      errorMessage.value = result.error_message || '邀请无效';
    }
  } catch (error: any) {
    errorMessage.value = error.message || '验证邀请失败';
  } finally {
    validating.value = false;
  }
});

const formSchema = computed((): VbenFormSchema[] => {
  return [
    {
      component: 'VbenInput',
      componentProps: {
        placeholder: '请输入邮箱',
      },
      fieldName: 'email',
      label: '邮箱',
      rules: z.string().email({ message: '请输入有效的邮箱地址' }),
    },
    {
      component: 'VbenInput',
      componentProps: {
        placeholder: '请输入昵称',
      },
      fieldName: 'nickname',
      label: '昵称',
      rules: z.string().min(1, { message: '请输入昵称' }).max(64, { message: '昵称不能超过64个字符' }),
    },
    {
      component: 'VbenInputPassword',
      componentProps: {
        passwordStrength: true,
        placeholder: '请输入密码（至少8位）',
      },
      fieldName: 'password',
      label: '密码',
      renderComponentContent() {
        return {
          strengthText: () => '密码强度',
        };
      },
      rules: z.string().min(8, { message: '密码至少8位' }).max(128, { message: '密码最多128位' }),
    },
    {
      component: 'VbenInputPassword',
      componentProps: {
        placeholder: '请再次输入密码',
      },
      dependencies: {
        rules(values) {
          const { password } = values;
          return z
            .string({ required_error: '请输入确认密码' })
            .min(1, { message: '请输入确认密码' })
            .refine((value) => value === password, {
              message: '两次输入的密码不一致',
            });
        },
        triggerFields: ['password'],
      },
      fieldName: 'confirmPassword',
      label: '确认密码',
    },
  ];
});

async function handleSubmit(values: any) {
  if (!inviteToken.value) {
    message.error('缺少邀请链接参数');
    return;
  }

  try {
    loading.value = true;

    const result = await registerWithInvitation({
      invitation_token: inviteToken.value,
      email: values.email,
      password: values.password,
      nickname: values.nickname,
    });

    if (result.access_token) {
      accessStore.setAccessToken(result.access_token);
      accessStore.setAccessSessionUuid(result.session_uuid);

      const [userInfo, accessCodes] = await Promise.all([
        getUserInfoApi(),
        getAccessCodesApi(),
      ]);

      userStore.setUserInfo(userInfo);
      accessStore.setAccessCodes(accessCodes);

      message.success('注册成功！正在进入引导页...');

      await router.push('/onboarding');
    }
  } catch (error: any) {
    const errorMsg = error.response?.data?.msg || error.message || '注册失败';
    message.error(errorMsg);
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <AuthenticationRegister
    :form-schema="invitationValid ? formSchema : []"
    :loading="loading || validating"
    :show-forget-password="false"
    :show-register-link="false"
    @submit="handleSubmit"
  >
    <template #title>
      <div class="mb-6 text-center">
        <h2 class="text-2xl font-bold">你已被邀请加入回响</h2>
      </div>
    </template>

    <!-- 加载中 -->
    <div v-if="validating" class="mb-6 text-center">
      <div class="text-muted-foreground">验证邀请信息中...</div>
    </div>

    <!-- 邀请无效 -->
    <div v-else-if="!invitationValid" class="mb-6 rounded-lg bg-destructive/10 p-4 text-destructive">
      <div class="font-semibold">邀请无效</div>
      <div class="mt-1 text-sm">{{ errorMessage }}</div>
      <div class="mt-4">
        <a href="/auth/login" class="text-primary hover:underline">返回登录</a>
      </div>
    </div>

    <!-- 邀请有效，显示权益 -->
    <div v-else class="mb-6 rounded-lg bg-primary/10 p-4">
      <div class="mb-2 font-semibold text-primary">🎉 邀请权益</div>
      <div class="space-y-1 text-sm">
        <div class="flex items-center">
          <span class="mr-2">✅</span>
          <span>{{ invitationInfo?.plan?.name || '专业版' }}功能免费体验 {{ invitationInfo?.plan?.trial_days || 90 }} 天</span>
        </div>
        <div class="flex items-center">
          <span class="mr-2">✅</span>
          <span>无限反馈收集</span>
        </div>
        <div class="flex items-center">
          <span class="mr-2">✅</span>
          <span>AI 智能聚类</span>
        </div>
        <div class="flex items-center">
          <span class="mr-2">✅</span>
          <span>500 AI 积分/月</span>
        </div>
      </div>
    </div>
  </AuthenticationRegister>
</template>
