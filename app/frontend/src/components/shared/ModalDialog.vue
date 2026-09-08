<template>
  <view v-if="props.visible" class="modal-overlay" @click="handleOverlayClick">
    <view class="modal-container" @click.stop>
      <!-- 模态框头部 -->
      <view class="modal-header">
        <view class="modal-title">
          <text class="modal-icon iconfont icon-video"></text>
          <text class="title-text">{{ props.title }}</text>
        </view>
        <text class="modal-close" @click="$emit('cancel')">×</text>
      </view>
      
      <!-- 分割线 -->
      <view class="modal-divider"></view>
      
      <!-- 模态框内容：壳内滚动，保证头/底常驻可见 -->
      <scroll-view class="modal-content" scroll-y>
        <slot></slot>
      </scroll-view>
      
      <!-- 模态框底部 -->
      <view class="modal-footer">
        <view class="button-group">
          <button 
            class="btn-cancel" 
            @click="$emit('cancel')"
            :disabled="props.confirmLoading"
          >
            取消
          </button>
          <button 
            class="btn-confirm" 
            @click="$emit('confirm')"
            :disabled="props.confirmLoading"
          >
            <text v-if="props.confirmLoading" class="loading-text">处理中...</text>
            <text v-else>{{ props.confirmText }}</text>
          </button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
const props = withDefaults(defineProps<{
  visible: boolean;
  title?: string;
  confirmText?: string;
  confirmLoading?: boolean;
}>(), {
  confirmText: '确认',
  confirmLoading: false,
});

defineEmits<{
  'update:visible': [value: boolean];
  'confirm': [];
  'cancel': [];
}>();

const handleOverlayClick = () => {
  // 点击遮罩层关闭模态框
};
</script>

<style lang="scss" scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.modal-container {
  background: var(--color-background-light);
  border-radius: var(--radius-large);
  box-shadow: var(--shadow-large);
  min-width: 360px;
  max-width: 90vw;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-sizing: border-box;
  animation: modalSlideIn 0.3s ease-out;
}

.modal-header {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-xlarge);
  border-bottom: 1px solid var(--color-border);
  
  .modal-title {
    display: flex;
    align-items: center;
    
    .modal-icon {
      font-size: 20px;
      margin-right: var(--spacing-medium);
    }
    
    .title-text {
      font-size: var(--font-size-large);
      font-weight: bold;
      color: var(--color-text-primary);
    }
  }
  
  .modal-close {
    font-size: 24px;
    color: var(--color-text-secondary);
    cursor: pointer;
    padding: var(--spacing-small);
    border-radius: var(--radius-base);
    transition: var(--transition-base);
    
    &:hover {
      color: var(--color-primary);
      background: var(--color-primary-light-1);
    }
  }
}

.modal-divider {
  flex-shrink: 0;
  height: 1px;
  background: var(--color-border);
  margin: 0 var(--spacing-xlarge);
}

.modal-content {
  flex: 1 1 auto;
  min-height: 0;
  /* 为头/底预留空间：避免再出现「内容 75vh + chrome 超屏」裁切 */
  max-height: 60vh;
  padding: var(--spacing-xlarge);
  box-sizing: border-box;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;

  /* 统一输入框样式 */
  :deep(.form-input),
  :deep(.form-textarea) {
    width: 100%;
    border: 1px solid var(--color-border);
    border-radius: var(--radius-base);
    padding: 10px 12px;
    font-size: var(--font-size-medium);
    color: var(--color-text-primary);
    background: var(--color-background-light);
    transition: var(--transition-base);
    box-sizing: border-box;

    &:hover {
      border-color: var(--color-primary);
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.12);
    }

    &:focus {
      border-color: var(--color-primary);
      box-shadow: 0 0 0 3px rgba(15, 118, 110, 0.15);
      outline: none;
    }
  }
}

.modal-footer {
  flex-shrink: 0;
  padding: var(--spacing-xlarge);
  border-top: 1px solid var(--color-border);
  background: var(--color-background);
  
  .button-group {
    display: flex;
    justify-content: flex-end;
    gap: var(--spacing-large);
    
    .btn-cancel {
      background: var(--color-background-light);
      color: var(--color-text-secondary);
      border: 1px solid var(--color-border);
      border-radius: var(--radius-base);
      padding: 8px 24px;
      font-size: var(--font-size-medium);
      cursor: pointer;
      transition: var(--transition-base);
      
      &:hover:not(:disabled) {
        background: var(--color-border);
        color: var(--color-text-primary);
      }
      
      &:disabled {
        opacity: 0.6;
        cursor: not-allowed;
      }
    }
    
    .btn-confirm {
      background: var(--color-primary);
      color: var(--color-text-on-primary);
      border: none;
      border-radius: var(--radius-base);
      padding: 8px 32px;
      font-size: var(--font-size-medium);
      font-weight: bold;
      cursor: pointer;
      transition: var(--transition-base);
      box-shadow: var(--shadow-base);
      
      &:hover:not(:disabled) {
        background: var(--color-primary-hover);
        box-shadow: var(--shadow-large);
      }
      
      &:disabled {
        opacity: 0.6;
        cursor: not-allowed;
      }
      
      .loading-text {
        display: flex;
        align-items: center;
        justify-content: center;
        
        &::before {
          content: '';
          width: 12px;
          height: 12px;
          border: 2px solid transparent;
          border-top: 2px solid currentColor;
          border-radius: 50%;
          animation: spin 1s linear infinite;
          margin-right: var(--spacing-small);
        }
      }
    }
  }
}
</style>