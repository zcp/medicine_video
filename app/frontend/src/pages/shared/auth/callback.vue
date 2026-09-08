<template>
  <view class="auth-callback">
    <view class="auth-callback__container">
      <view class="auth-callback__loading" v-if="isProcessing">
        <view class="auth-callback__spinner"></view>
        <text class="auth-callback__text">正在处理认证...</text>
      </view>
      
      <view class="auth-callback__success" v-else-if="isSuccess">
        <view class="auth-callback__icon success">✓</view>
        <text class="auth-callback__text">认证成功</text>
        <text class="auth-callback__subtext">正在跳转...</text>
      </view>
      
      <view class="auth-callback__error" v-else-if="isError">
        <view class="auth-callback__icon error">✗</view>
        <text class="auth-callback__text">认证失败</text>
        <text class="auth-callback__subtext">{{ errorMessage }}</text>
        <button class="auth-callback__retry" @click="retryAuth">重试</button>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useAuthStore } from '@/store/auth';
import { LOGIN_URL, APP_BASE_PATH } from '@/constants/api';

const authStore = useAuthStore();
const isProcessing = ref(true);
const isSuccess = ref(false);
const isError = ref(false);
const errorMessage = ref('');

onMounted(async () => {
  try {
    // 从URL参数中获取token
    const pages = getCurrentPages();
    const currentPage = pages[pages.length - 1];
    const options = (currentPage as any).options;
    
    const token = options.token;
    const error = options.error;
    const errorDescription = options.error_description;

    if (error) {
      throw new Error(errorDescription || '认证失败');
    }

    if (!token) {
      throw new Error('未找到认证Token');
    }

    // 验证Token格式
    if (!isValidJWTFormat(token)) {
      throw new Error('Token格式无效');
    }

    // 设置Token
    authStore.setToken(token);
    authStore.parseUserFromToken(token);

    isProcessing.value = false;
    isSuccess.value = true;

    // 延迟跳转
    setTimeout(() => {
      authStore.handleAuthRedirect();
    }, 1500);

  } catch (error) {
    console.error('认证处理失败:', error);
    isProcessing.value = false;
    isError.value = true;
    errorMessage.value = error instanceof Error ? error.message : '未知错误';
  }
});

const isValidJWTFormat = (token: string): boolean => {
  const parts = token.split('.');
  return parts.length === 3;
};

const retryAuth = () => {
  // 重新跳转到登录页面
  //window.location.href = '/pages/auth/login';
  const originDomain = window.location.hostname + (window.location.port ? ':' + window.location.port : '');
  const loginUrl = `${LOGIN_URL}?external_callback=true&origin=${originDomain}&app_path=${APP_BASE_PATH}`;
  window.location.href = loginUrl;
};
</script>

<style scoped lang="scss">
.auth-callback {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: var(--spacing-lg, 24px);

  &__container {
    background-color: var(--nav-bg-color, #ffffff);
    border-radius: var(--border-radius-lg, 8px);
    padding: var(--spacing-xl, 32px);
    text-align: center;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    max-width: 400px;
    width: 100%;
  }

  &__loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--spacing-md, 16px);
  }

  &__success {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--spacing-md, 16px);
  }

  &__error {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--spacing-md, 16px);
  }

  &__spinner {
    width: 40px;
    height: 40px;
    border: 4px solid var(--border-color, #e5e5e5);
    border-top-color: var(--primary-color, #007bff);
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  &__icon {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    font-weight: bold;
    color: var(--text-color-inverse, #ffffff);

    &.success {
      background-color: var(--success-color, #28a745);
    }

    &.error {
      background-color: var(--danger-color, #dc3545);
    }
  }

  &__text {
    font-size: var(--font-size-lg, 18px);
    font-weight: 600;
    color: var(--text-color-primary, #333333);
  }

  &__subtext {
    font-size: var(--font-size-base, 14px);
    color: var(--text-color-secondary, #666666);
  }

  &__retry {
    background-color: var(--primary-color, #007bff);
    color: var(--text-color-inverse, #ffffff);
    border: none;
    border-radius: var(--border-radius-base, 4px);
    padding: var(--spacing-sm, 8px) var(--spacing-md, 16px);
    font-size: var(--font-size-base, 14px);
    cursor: pointer;
    transition: background-color 0.2s ease;

    &:hover {
      background-color: var(--primary-color-hover, #0056b3);
    }
  }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
