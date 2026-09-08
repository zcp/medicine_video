<!--
 * AppButton - 统一按钮组件
 * @description 全局统一的按钮组件，支持多种类型、尺寸和状态
 * @author 直播SaaS团队
 -->
<template>
  <button
    :class="['app-button', `app-button--${type}`, `app-button--${size}`, { 'is-disabled': disabled, 'is-loading': loading, 'is-block': block }]"
    :disabled="disabled || loading"
    :aria-label="ariaLabel"
    :aria-busy="loading"
    @click="handleClick"
  >
    <!-- 加载图标 -->
    <view v-if="loading" class="app-button__loading">
      <uni-icons type="spinner-cycle" size="16" color="currentColor" />
    </view>
    
    <!-- 前置图标 -->
    <view v-if="icon && !loading" class="app-button__icon">
      <uni-icons :type="icon" :size="iconSize" color="currentColor" />
    </view>
    
    <!-- 按钮文本 -->
    <text v-if="$slots.default || text" class="app-button__text">
      <slot>{{ text }}</slot>
    </text>
    
    <!-- 后置图标 -->
    <view v-if="iconRight && !loading" class="app-button__icon-right">
      <uni-icons :type="iconRight" :size="iconSize" color="currentColor" />
    </view>
  </button>
</template>

<script setup lang="ts">
import { computed } from 'vue'

/**
 * 组件Props定义
 */
interface Props {
  /** 按钮类型 */
  type?: 'primary' | 'secondary' | 'success' | 'warning' | 'danger' | 'text'
  /** 按钮尺寸 */
  size?: 'large' | 'medium' | 'small'
  /** 按钮文本 */
  text?: string
  /** 前置图标 */
  icon?: string
  /** 后置图标 */
  iconRight?: string
  /** 是否禁用 */
  disabled?: boolean
  /** 是否加载中 */
  loading?: boolean
  /** 是否块级按钮 */
  block?: boolean
  /** 无障碍标签 */
  ariaLabel?: string
}

const props = withDefaults(defineProps<Props>(), {
  type: 'primary',
  size: 'medium',
  disabled: false,
  loading: false,
  block: false
})

/**
 * 组件Emits定义
 */
const emit = defineEmits<{
  /** 点击事件 */
  click: []
}>()

/**
 * 计算图标尺寸
 */
const iconSize = computed(() => {
  const sizeMap = {
    large: 20,
    medium: 16,
    small: 14
  }
  return sizeMap[props.size]
})

/**
 * 处理点击事件
 */
const handleClick = () => {
  if (!props.disabled && !props.loading) {
    emit('click')
  }
}
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.app-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: $spacing-sm;
  border: none;
  border-radius: $border-radius-base;
  font-weight: $font-weight-medium;
  cursor: pointer;
  transition: var(--transition-base);
  white-space: nowrap;
  user-select: none;

  &:focus-visible {
    outline: none;
    box-shadow: 0 0 0 6rpx var(--color-focus-ring);
  }
  
  /* 尺寸 */
  &--large {
    height: $button-height-lg;
    padding: 0 $spacing-xl;
    font-size: $font-size-lg;
  }
  
  &--medium {
    height: $button-height-base;
    padding: 0 $spacing-lg;
    font-size: $font-size-base;
  }
  
  &--small {
    height: $button-height-sm;
    padding: 0 $spacing-md;
    font-size: $font-size-sm;
  }
  
  /* 类型 - 主要按钮 */
  &--primary {
    background-color: var(--color-primary);
    color: var(--color-text-inverse);
    border-radius: var(--border-radius-full);
    
    &:active {
      opacity: 0.8;
    }
  }
  
  /* 类型 - 次要按钮 */
  &--secondary {
    background-color: var(--color-bg-secondary);
    color: var(--color-text-primary);
    
    &:active {
      background-color: var(--color-bg-tertiary);
    }
  }
  
  /* 类型 - 成功按钮 */
  &--success {
    background-color: var(--color-success);
    color: var(--color-text-inverse);
    
    &:active {
      opacity: 0.8;
    }
  }
  
  /* 类型 - 警告按钮 */
  &--warning {
    background-color: var(--color-warning);
    color: var(--color-text-inverse);
    
    &:active {
      opacity: 0.8;
    }
  }
  
  /* 类型 - 危险按钮 */
  &--danger {
    background-color: var(--color-danger);
    color: var(--color-text-inverse);
    
    &:active {
      opacity: 0.8;
    }
  }
  
  /* 类型 - 文本按钮 */
  &--text {
    background-color: transparent;
    color: var(--color-primary);
    padding: 0 8px;
    
    &:active {
      opacity: 0.6;
    }
  }
  
  /* 状态 - 禁用 */
  &.is-disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  /* 状态 - 加载中 */
  &.is-loading {
    cursor: not-allowed;
  }
  
  /* 块级按钮 */
  &.is-block {
    display: flex;
    width: 100%;
  }
  
  &__loading {
    animation: rotate 1s linear infinite;
  }
  
  &__text {
    flex: 1;
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
