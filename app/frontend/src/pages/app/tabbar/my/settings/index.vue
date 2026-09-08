<template>
  <view class="settings-page consumer-layout">
    <view class="menu-section">
      <view class="menu-list">
        <view class="menu-item row" @click="handleAccountSecurity">
          <text class="iconfont icon-privacy"></text>
          <text class="menu-label">账号与安全</text>
          <text class="iconfont icon-arrow-right"></text>
        </view>
        <view class="menu-item row" @click="handleAbout">
          <text class="iconfont icon-more"></text>
          <text class="menu-label">关于我们</text>
          <text class="iconfont icon-arrow-right"></text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { requireAuth } from '@/utils/auth';

function handleAccountSecurity() {
  if (!requireAuth()) return;
  uni.navigateTo({ url: '/pages/app/tabbar/my/account-security/index' });
}

function handleAbout() {
  uni.navigateTo({ url: '/pages/app/tabbar/my/about/index' });
}
</script>

<style lang="scss" scoped>
.consumer-layout {
  min-height: 100vh;
  background-color: var(--home-bg);
  padding: 0 var(--home-spacing-page) 48rpx;
  box-sizing: border-box;
}

.menu-section {
  margin-bottom: 48rpx;
}

.menu-list {
  background: transparent;
}

.menu-item {
  display: flex;
  align-items: center;
  min-height: 96rpx;
  padding: 24rpx 0;
  border-bottom: 1rpx solid rgba(0, 0, 0, 0.06);

  &:last-child {
    border-bottom: none;
  }

  &:active {
    opacity: 0.75;
  }

  .iconfont {
    font-size: 40rpx;
    color: var(--home-text2);

    &.icon-arrow-right {
      font-size: 28rpx;
      color: var(--home-text2);
    }
  }

  .menu-label {
    flex: 1;
    margin-left: 24rpx;
    font-size: var(--home-fs-card-title, 30rpx);
    color: var(--home-text1);
  }
}
</style>
