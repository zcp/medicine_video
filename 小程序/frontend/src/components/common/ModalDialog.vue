<!--
 * ModalDialog - 模态对话框组件
 * @description 全局统一的模态对话框
 * @author 直播SaaS团队
 -->
<template>
  <view v-if="visible" class="modal-dialog" @click="handleMaskClick">
    <view class="modal-dialog__mask"></view>
    <view class="modal-dialog__container" @click.stop>
      <!-- 关闭按钮 -->
      <view v-if="showClose" class="modal-dialog__close" @click="handleClose">
        <uni-icons type="closeempty" size="24" :color="'var(--color-text-tertiary)'" />
      </view>
      
      <!-- 标题 -->
      <view v-if="title || $slots.title" class="modal-dialog__header">
        <slot name="title">
          <text class="modal-dialog__title">{{ title }}</text>
        </slot>
      </view>
      
      <!-- 内容 -->
      <view class="modal-dialog__body">
        <slot>
          <text>{{ content }}</text>
        </slot>
      </view>
      
      <!-- 底部操作区 -->
      <view v-if="showFooter" class="modal-dialog__footer">
        <slot name="footer">
          <AppButton
            v-if="showCancel"
            type="secondary"
            :text="cancelText"
            @click="handleCancel"
          />
          <AppButton
            type="primary"
            :text="confirmText"
            :loading="confirmLoading"
            @click="handleConfirm"
          />
        </slot>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import AppButton from './AppButton.vue'

/**
 * 组件Props定义
 */
interface Props {
  /** 是否显示 */
  visible: boolean
  /** 对话框标题 */
  title?: string
  /** 对话框内容 */
  content?: string
  /** 是否显示关闭按钮 */
  showClose?: boolean
  /** 是否显示底部 */
  showFooter?: boolean
  /** 是否显示取消按钮 */
  showCancel?: boolean
  /** 取消按钮文字 */
  cancelText?: string
  /** 确认按钮文字 */
  confirmText?: string
  /** 确认按钮加载状态 */
  confirmLoading?: boolean
  /** 点击蒙层是否关闭 */
  maskClosable?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showClose: true,
  showFooter: true,
  showCancel: true,
  cancelText: '取消',
  confirmText: '确定',
  confirmLoading: false,
  maskClosable: true
})

/**
 * 组件Emits定义
 */
const emit = defineEmits<{
  /** 更新visible状态 */
  'update:visible': [value: boolean]
  /** 关闭事件 */
  close: []
  /** 取消事件 */
  cancel: []
  /** 确认事件 */
  confirm: []
}>()

/**
 * 处理蒙层点击
 */
const handleMaskClick = () => {
  if (props.maskClosable) {
    handleClose()
  }
}

/**
 * 处理关闭
 */
const handleClose = () => {
  emit('update:visible', false)
  emit('close')
}

/**
 * 处理取消
 */
const handleCancel = () => {
  emit('cancel')
  handleClose()
}

/**
 * 处理确认
 */
const handleConfirm = () => {
  emit('confirm')
}
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.modal-dialog {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  
  &__mask {
    position: absolute;
    inset: 0;
    background-color: rgba(0, 0, 0, 0.5);
    animation: fadeIn var(--duration-base) var(--ease-in-out);
  }
  
  &__container {
    position: relative;
    width: 100%;
    max-width: 400px;
    background-color: var(--color-bg-primary);
    border-radius: var(--border-radius-md);
    animation: slideUp var(--duration-base) var(--ease-in-out);
    max-height: 80vh;
    display: flex;
    flex-direction: column;
  }
  
  &__close {
    position: absolute;
    top: 16px;
    right: 16px;
    cursor: pointer;
    z-index: 1;
  }
  
  &__header {
    padding: 20px 20px 16px;
    border-bottom: 1px solid var(--color-border);
  }
  
  &__title {
    font-size: 18px;
    font-weight: 600;
    color: var(--color-text-primary);
  }
  
  &__body {
    flex: 1;
    padding: 20px;
    overflow-y: auto;
    font-size: 14px;
    color: var(--color-text-secondary);
    line-height: 1.6;
  }
  
  &__footer {
    display: flex;
    gap: 12px;
    padding: 16px 20px 20px;
    border-top: 1px solid var(--color-border);
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
