<template>
  <view class="skeleton-card">
    <!-- 左侧封面骨架 -->
    <view class="skeleton-cover skeleton-shimmer"></view>
    
    <!-- 右侧信息骨架 -->
    <view class="skeleton-info">
      <!-- 标题骨架（2行） -->
      <view class="skeleton-title skeleton-shimmer"></view>
      <view class="skeleton-title-short skeleton-shimmer"></view>
      
      <!-- 专家信息骨架 -->
      <view class="skeleton-author">
        <view class="skeleton-avatar skeleton-shimmer"></view>
        <view class="skeleton-text-group">
          <view class="skeleton-text skeleton-shimmer"></view>
          <view class="skeleton-text-small skeleton-shimmer"></view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
// 纯展示组件，无需逻辑
</script>

<style lang="scss" scoped>
// 骨架屏闪烁动画
@keyframes shimmer {
  0% {
    background-position: -468rpx 0;
  }
  100% {
    background-position: 468rpx 0;
  }
}

.skeleton-shimmer {
  animation: shimmer 1.5s infinite linear;
  background: linear-gradient(
    to right,
    #f0f0f0 0%,
    #e8e8e8 20%,
    #f0f0f0 40%,
    #f0f0f0 100%
  );
  background-size: 800rpx 100%;
}

.skeleton-card {
  display: flex;
  background-color: #ffffff;
  border-radius: 8rpx;
  margin-bottom: 20rpx;
  padding: 20rpx;
  overflow: hidden;
}

.skeleton-cover {
  width: 240rpx;
  height: 150rpx;
  flex-shrink: 0;
  border-radius: 8rpx;
}

.skeleton-info {
  flex: 1;
  margin-left: 20rpx;
  margin-right: 60rpx;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.skeleton-title {
  height: 40rpx;
  border-radius: 4rpx;
  margin-bottom: 12rpx;
}

.skeleton-title-short {
  height: 40rpx;
  width: 60%;
  border-radius: 4rpx;
  margin-bottom: 16rpx;
}

.skeleton-author {
  display: flex;
  align-items: center;
  margin-top: auto;
}

.skeleton-avatar {
  width: 48rpx;
  height: 48rpx;
  border-radius: 50%;
  margin-right: 12rpx;
  flex-shrink: 0;
}

.skeleton-text-group {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.skeleton-text {
  height: 24rpx;
  width: 200rpx;
  border-radius: 4rpx;
}

.skeleton-text-small {
  height: 20rpx;
  width: 160rpx;
  border-radius: 4rpx;
}
</style>
