
<template>
  <view class="not-found-page">
    <view class="container">
      <image src="/static/404-illustration.svg" class="illustration" mode="widthFix" />
      <text class="title">页面未找到</text>
      <text class="message">抱歉，您访问的页面不存在或已被移动。</text>
      <AppButton type="primary" @click="goHome">返回首页</AppButton>
    </view>
  </view>
</template>

<script setup lang="ts">
import AppButton from '@/components/shared/AppButton.vue';

const goHome = () => {
  // 使用 reLaunch 跳转到 TabBar 首页，清空页面栈
  // #ifdef H5
  uni.reLaunch({ url: '/pages/h5/room/RoomList' });
  // #endif
  // #ifndef H5
  uni.reLaunch({ url: '/pages/app/tabbar/home/index' });
  // #endif
};
</script>

<style lang="scss" scoped>
.not-found-page {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: var(--color-background);
  text-align: center;
  padding: var(--spacing-large);
}

.container {
  max-width: 320px;
}

.illustration {
  width: 200px;
  margin-bottom: var(--spacing-large);
}

.title {
  display: block;
  font-size: var(--font-size-xlarge);
  font-weight: bold;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-small);
}

.message {
  display: block;
  font-size: var(--font-size-base);
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-xlarge);
}
</style> 