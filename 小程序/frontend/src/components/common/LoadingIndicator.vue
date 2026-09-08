<!--
 * LoadingIndicator - 加载指示器组件
 * @description 全局统一的加载状态展示
 * @author 直播SaaS团队
 -->
<template>
  <view :class="['loading-indicator', `loading-indicator--${type}`, { 'is-fullscreen': fullscreen }]">
    <view class="loading-indicator__spinner">
      <uni-icons type="spinner-cycle" :size="size" :color="color" />
    </view>
    <text v-if="text" class="loading-indicator__text">{{ text }}</text>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'

/**
 * 组件Props定义
 */
interface Props {
  /** 加载器类型 */
  type?: 'default' | 'overlay'
  /** 加载文本 */
  text?: string
  /** 图标尺寸 */
  size?: number
  /** 图标颜色 */
  color?: string
  /** 是否全屏 */
  fullscreen?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  type: 'default',
  text: '加载中...',
  size: 24,
  color: 'var(--color-primary)',
  fullscreen: false
})
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.loading-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 20px;
  
  &--overlay {
    position: fixed;
    inset: 0;
    background-color: rgba(0, 0, 0, 0.5);
    z-index: 9999;
  }
  
  &.is-fullscreen {
    position: fixed;
    inset: 0;
    background-color: var(--color-bg-primary);
    z-index: 9998;
  }
  
  &__spinner {
    animation: rotate 1s linear infinite;
  }
  
  &__text {
    font-size: 14px;
    color: var(--color-text-secondary);
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
