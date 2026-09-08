<template>
  <view :class="['loading-indicator', `loading-indicator--${type}`, { 'is-fullscreen': fullscreen }]">
    <view class="loading-indicator__spinner">
      <view class="spinner"></view>
    </view>
    <text v-if="text" class="loading-indicator__text">{{ text }}</text>
  </view>
</template>

<script setup lang="ts">
/**
 * 加载指示器组件
 * @description 全局统一的加载状态展示
 */

interface Props {
  /** 加载器类型 */
  type?: 'default' | 'overlay';
  /** 加载文本 */
  text?: string;
  /** 图标尺寸 */
  size?: number;
  /** 图标颜色 */
  color?: string;
  /** 是否全屏 */
  fullscreen?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  type: 'default',
  text: '加载中...',
  size: 24,
  color: '#007AFF',
  fullscreen: false
});
</script>

<style lang="scss" scoped>
.loading-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 24rpx;
  padding: 40rpx;

  &--overlay {
    position: fixed;
    inset: 0;
    background-color: rgba(0, 0, 0, 0.5);
    z-index: 9999;
  }

  &.is-fullscreen {
    position: fixed;
    inset: 0;
    background-color: #ffffff;
    z-index: 9998;
  }

  &__spinner {
    .spinner {
      width: 48rpx;
      height: 48rpx;
      border: 4rpx solid #f3f3f3;
      border-top: 4rpx solid #007AFF;
      border-radius: 50%;
      animation: rotate 1s linear infinite;
    }
  }

  &__text {
    font-size: 28rpx;
    color: #8C8C8C;
  }
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
