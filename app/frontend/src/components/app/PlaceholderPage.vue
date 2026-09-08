<template>
  <view class="placeholder-page">
    <view class="placeholder-content">
      <view class="icon-wrapper">
        <text class="placeholder-icon iconfont" :class="`icon-${icon}`"></text>
      </view>
      <view class="title">{{ title }}</view>
      <view class="description">{{ description }}</view>
      <view class="tips">功能正在开发中，敬请期待</view>
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * 占位页面组件
 * @description 用于未开发完成的页面展示
 */
interface Props {
  /** 页面标题 */
  title?: string;
  /** 页面描述 */
  description?: string;
  /** 图标名称（iconfont 图标，不含 icon- 前缀） */
  icon?: string;
}

withDefaults(defineProps<Props>(), {
  title: '页面开发中',
  description: '该功能即将上线',
  icon: 'setting'
});
</script>

<style scoped>
.placeholder-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f7f8fa;
  padding: 40rpx;
}

.placeholder-content {
  text-align: center;
}

.icon-wrapper {
  margin-bottom: 40rpx;
}

.placeholder-icon {
  font-size: 120rpx;
  color: #ffc107;
}

.title {
  font-size: 36rpx;
  font-weight: 600;
  color: #333333;
  margin-bottom: 20rpx;
}

.description {
  font-size: 28rpx;
  color: #666666;
  margin-bottom: 16rpx;
}

.tips {
  font-size: 24rpx;
  color: #999999;
  margin-top: 40rpx;
  padding: 16rpx 32rpx;
  background-color: #ffffff;
  border-radius: 8rpx;
  display: inline-block;
}
</style>
