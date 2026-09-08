<template>
  <view class="placeholder-page">
    <view class="content">
      <text class="iconfont icon-more icon"></text>
      <text class="title">关于我们</text>
      <text class="description">应用版本 v1.0.0</text>
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * 关于我们页面
 * @description 占位页面，后续实现完整功能
 * 功能规划：
 * - 应用版本信息
 * - 开发团队介绍
 * - 联系方式
 * - 更新日志
 */
</script>

<style lang="scss" scoped>
.placeholder-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #F5F5F5;
}

.content {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 64rpx;
}

.icon {
  font-size: 120rpx;
  color: #CCCCCC;
  margin-bottom: 32rpx;
}

.title {
  font-size: 36rpx;
  color: #333333;
  margin-bottom: 16rpx;
}

.description {
  font-size: 28rpx;
  color: #999999;
}
</style>
