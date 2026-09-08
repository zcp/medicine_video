<!--
 * CategoryFormDialog - 根分类新增/编辑（对齐图六精简表单）
 -->
<template>
  <view class="dialog-overlay" v-if="visible" @click="handleOverlayClick">
    <view class="dialog-container" @click.stop>
      <view class="dialog-header">
        <text class="dialog-title">{{ mode === 'create' ? '新增分类' : '编辑根分类' }}</text>
        <view class="dialog-close" @click="handleClose">
          <text class="close-icon">✕</text>
        </view>
      </view>

      <view class="dialog-body">
        <view class="form">
          <view class="form-item">
            <view class="form-label">
              <text class="label-text">分类名称（标准名）</text>
              <text v-if="mode === 'create'" class="label-required">*</text>
            </view>
            <view class="form-control">
              <input
                v-model="formData.name"
                class="form-input"
                placeholder="请输入分类标准名"
                maxlength="100"
              />
            </view>
            <view v-if="errors.name" class="form-error">
              <text class="error-text">{{ errors.name }}</text>
            </view>
          </view>

          <view class="form-item">
            <view class="form-label">
              <text class="label-text">口语名（C端展示，可选）</text>
            </view>
            <view class="form-control">
              <input
                v-model="formData.display_name"
                class="form-input"
                placeholder="留空则 C 端使用标准名"
                maxlength="100"
              />
            </view>
          </view>

          <view class="form-item">
            <text class="label-text form-label-block">启用分类</text>
            <view class="form-control">
              <switch
                :checked="formData.is_active"
                @change="formData.is_active = $event.detail.value"
                color="#0f766e"
              />
            </view>
          </view>
        </view>
      </view>

      <view class="dialog-footer">
        <view class="btn-cancel" @click="handleClose">
          <text class="btn-text">取消</text>
        </view>
        <view class="btn-confirm" :class="{ 'is-loading': submitting }" @click="handleSubmit">
          <text class="btn-text">{{ submitting ? '提交中...' : '保存' }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { logger } from '@/logs/logger'
import { createCategory, updateCategory } from '@/api/categories'
import type { Category } from '@/types/category'

const props = defineProps<{
  visible: boolean
  mode: 'create' | 'edit'
  initialData?: Category | null
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  success: []
}>()

const submitting = ref(false)

const formData = reactive({
  name: '',
  display_name: '',
  is_active: true
})

const errors = reactive({
  name: ''
})

function slugifyName(name: string) {
  const base = name
    .trim()
    .toLowerCase()
    .replace(/\s+/g, '-')
    .replace(/[^a-z0-9-]/g, '')
  return base || `cat-${Date.now()}`
}

function fillFromInitial(data: Category) {
  formData.name = data.name
  formData.display_name = data.display_name || data.name || ''
  formData.is_active = data.is_active !== false
}

function resetForm() {
  formData.name = ''
  formData.display_name = ''
  formData.is_active = true
  errors.name = ''
}

watch(
  () => [props.visible, props.mode, props.initialData] as const,
  ([val]) => {
    if (!val) {
      resetForm()
      return
    }
    if (props.mode === 'edit' && props.initialData) {
      fillFromInitial(props.initialData)
    } else {
      resetForm()
    }
  },
  { immediate: true }
)

function handleClose() {
  emit('update:visible', false)
}

function handleOverlayClick() {
  handleClose()
}

function validateForm(): boolean {
  errors.name = ''
  if (!formData.name.trim()) {
    errors.name = '请输入分类名称'
    return false
  }
  if (formData.name.length > 100) {
    errors.name = '长度在1-100个字符'
    return false
  }
  return true
}

async function handleSubmit() {
  if (submitting.value) return
  if (!validateForm()) return

  submitting.value = true
  try {
    const displayName = formData.display_name.trim()
    if (props.mode === 'create') {
      await createCategory({
        name: formData.name.trim(),
        slug: slugifyName(formData.name),
        display_name: displayName || undefined,
        is_active: formData.is_active
      } as any)
      uni.showToast({ title: '分类创建成功', icon: 'success' })
    } else {
      await updateCategory(props.initialData!.id, {
        name: formData.name.trim(),
        display_name: displayName || undefined,
        is_active: formData.is_active
      } as any)
      uni.showToast({ title: '分类更新成功', icon: 'success' })
    }
    emit('update:visible', false)
    emit('success')
  } catch (error) {
    logger.error('system', props.mode === 'create' ? '创建分类失败' : '更新分类失败', { error })
    uni.showToast({
      title: props.mode === 'create' ? '创建失败' : '更新失败',
      icon: 'none'
    })
  } finally {
    submitting.value = false
  }
}
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog-container {
  width: 90%;
  max-width: 520px;
  background-color: var(--color-bg-primary);
  border-radius: var(--border-radius-lg);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-bottom: 1px solid var(--color-border);

  .dialog-title {
    font-size: 17px;
    font-weight: 600;
    color: var(--color-text-primary);
  }

  .dialog-close {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;

    .close-icon {
      font-size: 18px;
      color: var(--color-text-secondary);
    }
  }
}

.dialog-body {
  padding: 16px;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-label {
  display: flex;
  align-items: center;
  gap: 4px;
}

.form-label-block {
  display: block;
}

.label-text {
  font-size: 14px;
  color: var(--color-text-secondary);
}

.label-required {
  font-size: 14px;
  color: #ff4d4f;
}

.form-input {
  width: 100%;
  height: 40px;
  padding: 0 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-base);
  font-size: 14px;
  background-color: var(--color-bg-primary);
  box-sizing: border-box;
}

.form-error .error-text {
  font-size: 12px;
  color: #ff4d4f;
}

.dialog-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px;
  border-top: 1px solid var(--color-border);
}

.btn-cancel {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 36px;
  padding: 0 20px;
  background-color: var(--color-bg-secondary);
  border-radius: var(--border-radius-base);

  .btn-text {
    font-size: 14px;
    color: var(--color-text-primary);
  }
}

.btn-confirm {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 36px;
  padding: 0 20px;
  background-color: #0f766e;
  border-radius: var(--border-radius-base);

  .btn-text {
    font-size: 14px;
    color: #ffffff;
  }

  &.is-loading {
    opacity: 0.7;
  }
}
</style>
