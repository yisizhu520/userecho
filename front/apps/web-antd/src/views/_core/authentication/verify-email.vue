<script lang="ts" setup>
import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import { Button, Card, message } from '@vben/common-ui';

import {
  resendVerificationEmail,
  verifyEmail,
} from '#/api/userecho/invitation';

defineOptions({ name: 'VerifyEmail' });

const route = useRoute();
const router = useRouter();

const email = ref('');
const verificationCode = ref('');
const loading = ref(false);
const resending = ref(false);
const countdown = ref(0);
const timer = ref<any>(null);

onMounted(() => {
  email.value = (route.query.email as string) || '';

  // 从 URL 获取验证码（邮件链接点击进来时）
  const codeFromUrl = route.query.code as string;
  if (codeFromUrl) {
    verificationCode.value = codeFromUrl;
    handleVerify();
  }
});

async function handleVerify() {
  if (!verificationCode.value) {
    message.error('请输入验证码');
    return;
  }

  try {
    loading.value = true;

    await verifyEmail({
      verification_code: verificationCode.value,
    });

    message.success('邮箱验证成功！');

    // 跳转到引导页面
    setTimeout(() => {
      router.push('/onboarding');
    }, 1000);
  } catch (error: any) {
    const errorMsg
      = error.response?.data?.msg || error.message || '验证失败';
    message.error(errorMsg);
  } finally {
    loading.value = false;
  }
}

async function handleResend() {
  if (!email.value) {
    message.error('缺少邮箱信息');
    return;
  }

  if (countdown.value > 0) {
    message.warning(`请在 ${countdown.value} 秒后重试`);
    return;
  }

  try {
    resending.value = true;

    await resendVerificationEmail({
      email: email.value,
    });

    message.success('验证邮件已发送');

    // 开始60秒倒计时
    startCountdown();
  } catch (error: any) {
    const errorMsg
      = error.response?.data?.msg || error.message || '发送失败';
    message.error(errorMsg);
  } finally {
    resending.value = false;
  }
}

function startCountdown() {
  countdown.value = 60;

  timer.value = setInterval(() => {
    countdown.value--;

    if (countdown.value <= 0) {
      clearInterval(timer.value);
    }
  }, 1000);
}

const resendButtonText = computed(() => {
  return countdown.value > 0
    ? `重新发送 (${countdown.value}s)`
    : '重新发送验证邮件';
});

// 清理定时器
onMounted(() => {
  return () => {
    if (timer.value) {
      clearInterval(timer.value);
    }
  };
});
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-background p-4">
    <Card class="w-full max-w-md">
      <div class="p-6 text-center">
        <!-- 图标 -->
        <div class="mb-6 flex justify-center">
          <div class="flex h-16 w-16 items-center justify-center rounded-full bg-primary/10 text-4xl">
            📧
          </div>
        </div>

        <!-- 标题 -->
        <h2 class="mb-2 text-2xl font-bold">
          验证邮箱以激活试用订阅
        </h2>

        <!-- 说明 -->
        <div class="text-muted-foreground mb-6">
          <p v-if="email" class="mb-2">
            我们已向 <span class="font-semibold">{{ email }}</span> 发送验证邮件
          </p>
          <p>
            请点击邮件中的链接完成验证。<br>
            验证后即可获得专业版 3 个月试用。
          </p>
        </div>

        <!-- 验证码输入框（备用方式） -->
        <div class="mb-6">
          <div class="mb-2 text-left text-sm font-medium">
            或者输入验证码
          </div>
          <div class="flex gap-2">
            <input
              v-model="verificationCode"
              class="bg-accent text-accent-foreground placeholder:text-muted-foreground focus-visible:ring-ring flex h-10 w-full rounded-md border px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              placeholder="请输入验证码"
              type="text"
              @keyup.enter="handleVerify"
            >
            <Button
              :loading="loading"
              type="button"
              @click="handleVerify"
            >
              验证
            </Button>
          </div>
        </div>

        <!-- 帮助信息 -->
        <div class="border-muted rounded-lg border p-4 text-left text-sm">
          <div class="mb-2 font-semibold">
            没收到邮件？
          </div>
          <ul class="text-muted-foreground space-y-1">
            <li>1. 检查垃圾邮件箱</li>
            <li>2. 等待 1-2 分钟</li>
            <li>3. 确认邮箱地址是否正确</li>
          </ul>
        </div>

        <!-- 重新发送按钮 -->
        <div class="mt-6 flex gap-2">
          <Button
            :disabled="countdown > 0"
            :loading="resending"
            class="flex-1"
            variant="outline"
            @click="handleResend"
          >
            {{ resendButtonText }}
          </Button>
          <Button
            class="flex-1"
            variant="ghost"
            @click="router.push('/auth/login')"
          >
            返回登录
          </Button>
        </div>
      </div>
    </Card>
  </div>
</template>
