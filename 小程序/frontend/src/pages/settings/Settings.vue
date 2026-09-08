<template>
  <view class="settings-page">
    <!-- 账号与安全 -->
    <view class="section">
      <text class="section-title">账号</text>
      <view class="menu-item" @tap="goTo('/pages/settings/AccountSecurity')">
        <view class="menu-left">
          <uni-icons type="locked" size="20" color="var(--color-text-secondary)" />
          <text class="menu-label">账号与安全</text>
        </view>
        <uni-icons type="right" size="16" color="var(--color-text-tertiary)" />
      </view>
      <view class="menu-item" @tap="goTo('/pages/profile/ProfileEdit')">
        <view class="menu-left">
          <uni-icons type="person" size="20" color="var(--color-text-secondary)" />
          <text class="menu-label">个人信息</text>
        </view>
        <uni-icons type="right" size="16" color="var(--color-text-tertiary)" />
      </view>
    </view>

    <!-- 通用设置 -->
    <view class="section">
      <text class="section-title">通用</text>
      <view class="menu-item" @tap="goTo('/pages/about/About')">
        <view class="menu-left">
          <uni-icons type="info" size="20" color="var(--color-text-secondary)" />
          <text class="menu-label">关于我们</text>
        </view>
        <uni-icons type="right" size="16" color="var(--color-text-tertiary)" />
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { useAuthStore } from '@/store/auth'

/**
 * 设置页面
 * 账号与安全需登录：未登录直接进登录页，带 redirect 回跳
 */

const authStore = useAuthStore()

const AUTH_REQUIRED_PATHS = new Set(['/pages/settings/AccountSecurity'])

function goTo(url: string) {
  if (AUTH_REQUIRED_PATHS.has(url) && !authStore.isAuthenticated) {
    uni.navigateTo({
      url: `/pages/auth/OneTapLogin?redirect=${encodeURIComponent(url)}`,
      fail: () => {
        uni.showToast({ title: '页面跳转失败', icon: 'none' })
      }
    })
    return
  }
  uni.navigateTo({
    url,
    fail: () => {
      uni.showToast({ title: '页面跳转失败', icon: 'none' })
    }
  })
}
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.settings-page {
  min-height: 100vh;
  background: var(--color-background);
  padding-bottom: calc(var(--spacing-lg) + constant(safe-area-inset-bottom));
  padding-bottom: calc(var(--spacing-lg) + env(safe-area-inset-bottom));
}

.section {
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  padding: var(--spacing-md) var(--spacing-lg);
}

.section-title {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-sm);
}

.menu-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 0;
  border-bottom: 1px solid var(--color-border);

  &:last-child {
    border-bottom: none;
  }

  &:active {
    background: var(--color-bg-secondary);
  }
}

.menu-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.menu-label {
  font-size: 15px;
  color: var(--color-text-primary);
}
</style>

