<!--
 * ErrorBanner - 错误提示横幅
 * @description 用于展示错误信息的横幅组件
 * @author 直播SaaS团队
 -->
<template>
  <view v-if="visible" :class="['error-banner', `error-banner--${type}`]" role="alert" :aria-live="ariaLive">
    <view class="error-banner__icon">
      <uni-icons :type="iconType" size="20" color="currentColor" />
    </view>
    
    <view class="error-banner__content">
      <text v-if="title" class="error-banner__title">{{ title }}</text>
      <text class="error-banner__message">{{ message }}</text>
    </view>
    
    <view v-if="closable" class="error-banner__close" @click="handleClose">
      <uni-icons type="closeempty" size="18" color="currentColor" />
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

/**
 * 组件Props定义
 */
interface Props {
  /** 错误类型 */
  type?: 'error' | 'warning' | 'info' | 'success'
  /** 标题 */
  title?: string
  /** 消息内容 */
  message: string
  /** 是否可关闭 */
  closable?: boolean
  /** 无障碍 - 实时区域类型 */
  ariaLive?: 'polite' | 'assertive'
}

const props = withDefaults(defineProps<Props>(), {
  type: 'error',
  closable: true,
  ariaLive: 'polite'
})

/**
 * 组件Emits定义
 */
const emit = defineEmits<{
  /** 关闭事件 */
  close: []
}>()

const visible = ref(true)

/**
 * 计算图标类型
 */
const iconType = computed(() => {
  const iconMap = {
    error: 'closeempty',
    warning: 'info',
    info: 'info',
    success: 'checkmarkempty'
  }
  return iconMap[props.type]
})

/**
 * 处理关闭
 */
const handleClose = () => {
  visible.value = false
  emit('close')
}
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.error-banner {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 16px;
  border-radius: var(--border-radius-base);
  margin-bottom: 16px;
  
  &--error {
    background-color: var(--color-danger-light);
    color: var(--color-danger);
  }
  
  &--warning {
    background-color: var(--color-warning-light);
    color: var(--color-warning);
  }
  
  &--info {
    background-color: var(--color-info-light);
    color: var(--color-info);
  }
  
  &--success {
    background-color: var(--color-success-light);
    color: var(--color-success);
  }
  
  &__icon {
    flex-shrink: 0;
    margin-top: 2px;
  }
  
  &__content {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  
  &__title {
    font-size: 14px;
    font-weight: 600;
  }
  
  &__message {
    font-size: 14px;
    line-height: 1.5;
  }
  
  &__close {
    flex-shrink: 0;
    cursor: pointer;
    opacity: 0.6;
    
    &:hover {
      opacity: 1;
    }
  }
}
</style>
