<template>
  <button
    class="app-button"
    :class="[
      `app-button--${type}`,
      `app-button--${size}`,
      { 'is-disabled': disabled, 'is-loading': loading }
    ]"
    :disabled="disabled || loading"
    @click="handleClick"
  >
    <view v-if="loading" class="app-button__loading-indicator"></view>
    <view class="app-button__content">
      <slot />
    </view>
  </button>
</template>

<script setup lang="ts">
const props = withDefaults(defineProps<{
  type?: 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'default';
  size?: 'large' | 'medium' | 'small' | 'mini';
  loading?: boolean;
  disabled?: boolean;
}>(), {
  type: 'default',
  size: 'medium',
  loading: false,
  disabled: false,
});

const emit = defineEmits(['click']);

function handleClick(e: Event) {
  if (!props.disabled && !props.loading) {
    emit('click', e);
  }
}
</script>

<style scoped lang="scss">
.app-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid transparent;
  text-align: center;
  vertical-align: middle;
  cursor: pointer;
  user-select: none;
  transition: all 0.3s ease-in-out;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  font-weight: 500;
  box-shadow: none;
  outline: none;
  position: relative;
  border-radius: 4px;
  min-width: 80px;
  white-space: nowrap;

  &:hover:not(.is-disabled):not(.is-loading) {
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  }

  &:active:not(.is-disabled):not(.is-loading) {
    transform: translateY(0);
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
  }

  &.is-disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none !important;
    box-shadow: none !important;
  }

  &.is-loading {
    opacity: 0.8;
    cursor: wait;
    transform: none !important;
    box-shadow: none !important;
  }

  /* 默认按钮 - 白色背景 */
  &--default {
    background-color: #ffffff;
    border-color: #dcdfe6;
    color: #606266;

    &:hover:not(.is-disabled):not(.is-loading) {
      background-color: #f5f7fa;
      border-color: #c2c7cc;
      color: #606266;
    }

    &:active:not(.is-disabled):not(.is-loading) {
      background-color: #e4e7ed;
      border-color: #b3b7bf;
      color: #606266;
    }
  }

  /* 主要按钮 - 蓝色背景 */
  &--primary {
    background-color: #409eff;
    border-color: #409eff;
    color: #ffffff;

    &:hover:not(.is-disabled):not(.is-loading) {
      background-color: #66b1ff;
      border-color: #66b1ff;
      color: #ffffff;
    }

    &:active:not(.is-disabled):not(.is-loading) {
      background-color: #3a8ee6;
      border-color: #3a8ee6;
      color: #ffffff;
    }
  }

  /* 成功按钮 - 绿色背景 */
  &--success {
    background-color:rgb(58, 153, 11);
    border-color: rgb(58, 153, 11);
    color: #ffffff;

    &:hover:not(.is-disabled):not(.is-loading) {
      background-color: rgb(58, 153, 11);
      border-color: rgb(58, 153, 11);
      color: #ffffff;
    }

    &:active:not(.is-disabled):not(.is-loading) {
      background-color: #5daf34;
      border-color: #5daf34;
      color: #ffffff;
    }
  }

  /* 警告按钮 - 橙色背景 */
  &--warning {
    background-color: #e6a23c;
    border-color: #e6a23c;
    color: #ffffff;

    &:hover:not(.is-disabled):not(.is-loading) {
      background-color: #ebb563;
      border-color: #ebb563;
      color: #ffffff;
    }

    &:active:not(.is-disabled):not(.is-loading) {
      background-color: #cf9236;
      border-color: #cf9236;
      color: #ffffff;
    }
  }

  /* 危险按钮 - 红色背景 */
  &--danger {
    background-color: #f56c6c;
    border-color: #f56c6c;
    color: #ffffff;

    &:hover:not(.is-disabled):not(.is-loading) {
      background-color: #f78989;
      border-color: #f78989;
      color: #ffffff;
    }

    &:active:not(.is-disabled):not(.is-loading) {
      background-color: #dd6161;
      border-color: #dd6161;
      color: #ffffff;
    }
  }

  /* 信息按钮 - 灰色背景 */
  &--info {
    background-color: #909399;
    border-color: #909399;
    color: #ffffff;

    &:hover:not(.is-disabled):not(.is-loading) {
      background-color: #a6a9ad;
      border-color: #a6a9ad;
      color: #ffffff;
    }

    &:active:not(.is-disabled):not(.is-loading) {
      background-color: #82848a;
      border-color: #82848a;
      color: #ffffff;
    }
  }

  /* 尺寸设计 */
  &--large {
    height: 40px;
    padding: 0 20px;
    font-size: 14px;
    border-radius: 4px;
  }

  &--medium {
    height: 32px;
    padding: 0 15px;
    font-size: 12px;
    border-radius: 4px;
  }

  &--small {
    height: 28px;
    padding: 0 12px;
    font-size: 12px;
    border-radius: 3px;
    min-width: 60px;
  }

  &--mini {
    height: 24px;
    padding: 0 8px;
    font-size: 11px;
    border-radius: 3px;
    min-width: 50px;
  }

  /* 加载指示器 */
  &__loading-indicator {
    width: 14px;
    height: 14px;
    margin-right: 6px;
    border: 2px solid currentColor;
    border-top-color: transparent;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
    opacity: 0.8;
  }

  /* 内容区域 */
  &__content {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 4px;
    line-height: 1;
  }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>