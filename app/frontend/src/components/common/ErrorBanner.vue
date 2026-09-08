<template>
  <view v-if="visible" :class="['error-banner', `error-banner--${type}`]" role="alert">
    <view class="error-banner__icon">
      <text>{{ iconText }}</text>
    </view>
    
    <view class="error-banner__content">
      <text v-if="title" class="error-banner__title">{{ title }}</text>
      <text class="error-banner__message">{{ message }}</text>
    </view>
    
    <view v-if="closable" class="error-banner__close" @click="handleClose">
      <text>×</text>
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * 错误提示横幅组件
 * @description 用于展示错误、警告、信息、成功提示
 */
import { ref, computed } from 'vue';

interface Props {
  /** 提示类型 */
  type?: 'error' | 'warning' | 'info' | 'success';
  /** 标题 */
  title?: string;
  /** 消息内容 */
  message: string;
  /** 是否可关闭 */
  closable?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  type: 'error',
  closable: true
});

const emit = defineEmits<{
  close: [];
}>();

/** 是否可见 */
const visible = ref(true);

/** 图标文本 */
const iconText = computed(() => {
  const iconMap = {
    error: '✕',
    warning: '⚠',
    info: 'ℹ',
    success: '✓'
  };
  return iconMap[props.type];
});

/**
 * 处理关闭
 */
function handleClose() {
  visible.value = false;
  emit('close');
}
</script>

<style lang="scss" scoped>
.error-banner {
  display: flex;
  align-items: flex-start;
  gap: 24rpx;
  padding: 24rpx 32rpx;
  border-radius: 16rpx;
  margin: 24rpx;
  
  &--error {
    background-color: #FFF1F0;
    color: #FF4D4F;
  }
  
  &--warning {
    background-color: #FFFBE6;
    color: #FAAD14;
  }
  
  &--info {
    background-color: #E6F7FF;
    color: #1890FF;
  }
  
  &--success {
    background-color: #F6FFED;
    color: #52C41A;
  }
  
  &__icon {
    flex-shrink: 0;
    font-size: 32rpx;
    margin-top: 4rpx;
  }
  
  &__content {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 8rpx;
  }
  
  &__title {
    font-size: 28rpx;
    font-weight: 600;
  }
  
  &__message {
    font-size: 28rpx;
    line-height: 1.5;
  }
  
  &__close {
    flex-shrink: 0;
    font-size: 40rpx;
    opacity: 0.6;
    padding: 0 8rpx;
    
    &:active {
      opacity: 1;
    }
  }
}
</style>
