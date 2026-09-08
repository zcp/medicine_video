<template>
  <view v-if="visible" class="login-banner">
    <text class="banner-text">登录后可收藏、关注、订阅您喜爱的直播内容</text>
    <view class="banner-actions">
      <text class="login-link" @tap="handleLogin">登录</text>
      <!-- 触控热区 >= 44x44px：view 容器承载尺寸，uni-text 不响应宽高 -->
      <view class="dismiss-btn" @tap="handleDismiss">
        <text class="dismiss-icon">✕</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useAuthStore } from '@/store/auth';
import { APP_LOGIN_PATH } from '@/constants/routes';
import { getCurrentPagePath } from '@/utils/auth';

const authStore = useAuthStore();

const visible = computed(() => {
  return !authStore.isAuthenticated && !authStore.loginBannerDismissed;
});

function handleLogin() {
  const currentPath = getCurrentPagePath() || '/pages/app/tabbar/home/index';
  uni.setStorageSync('loginRedirectPath', currentPath);
  uni.navigateTo({ url: APP_LOGIN_PATH });
}

function handleDismiss() {
  authStore.loginBannerDismissed = true;
}
</script>

<style lang="scss" scoped>
.login-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16rpx 24rpx;
  /* 轻灰渐变（微光效，克制）：替代高饱和绿色，清洗为中性基调 + 主色点缀 */
  background: linear-gradient(135deg, var(--home-bg), var(--home-badge-featured-bg));
  border-bottom: 1rpx solid rgba(17, 24, 39, 0.06);
}

.banner-text {
  flex: 1;
  font-size: 24rpx;
  color: var(--home-text2);
  line-height: 1.4;
}

.banner-actions {
  display: flex;
  align-items: center;
  gap: 20rpx;
  flex-shrink: 0;
}

.login-link {
  font-size: 26rpx;
  font-weight: 500;
  color: var(--home-primary);
  padding: 8rpx 20rpx;
  border: 2rpx solid var(--home-primary);
  border-radius: 30rpx;
  transition: background-color 0.2s ease, color 0.2s ease;

  &:active {
    background-color: var(--home-primary);
    color: #ffffff;
  }
}

.dismiss-btn {
  /* 触控热区：等效 >= 44x44px */
  width: 56rpx;
  height: 56rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: background-color 0.2s ease;
  flex-shrink: 0;

  &:active {
    background-color: var(--home-action-secondary-bg);
  }
}

.dismiss-icon {
  font-size: 28rpx;
  line-height: 1;
  color: var(--home-text3, var(--home-text2)); /* 弱化辅助色：fallback 语义与全局一致 */
}
</style>
