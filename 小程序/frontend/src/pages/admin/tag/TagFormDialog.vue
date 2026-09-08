<!--
 * TagFormDialog - 标签新增/编辑弹窗
 * @description 管理端标签的新增和编辑表单弹窗
 * @author 直播SaaS团队
 -->
<template>
  <view class="dialog-overlay" v-if="visible" @click="handleClose">
    <view class="dialog-container" @click.stop>
      <!-- 弹窗头部 -->
      <view class="dialog-header">
        <text class="dialog-title">{{ mode === 'create' ? '新增标签' : '编辑标签' }}</text>
        <view class="dialog-close" @click="handleClose">
          <text class="close-icon">✕</text>
        </view>
      </view>

      <!-- 表单内容 -->
      <view class="dialog-body">
        <view class="form">
          <!-- 标签名称 -->
          <view class="form-item">
            <view class="form-label">
              <text class="label-text">标签名称</text>
              <text class="label-required">*</text>
            </view>
            <view class="form-control">
              <input
                v-model="formData.name"
                class="form-input"
                placeholder="请输入标签名称（1-100字符）"
                maxlength="100"
              />
            </view>
            <view v-if="errors.name" class="form-error">
              <text class="error-text">{{ errors.name }}</text>
            </view>
          </view>

          <!-- 英文标识 -->
          <view class="form-item">
            <view class="form-label">
              <text class="label-text">英文标识</text>
              <text class="label-required">*</text>
            </view>
            <view class="form-control">
              <input
                v-model="formData.slug"
                class="form-input"
                placeholder="请输入英文标识（如 xinxiguan）"
                maxlength="100"
              />
            </view>
            <view class="form-hint">
              <text class="hint-text">只能用小写英文、数字和横线</text>
            </view>
            <view v-if="errors.slug" class="form-error">
              <text class="error-text">{{ errors.slug }}</text>
            </view>
          </view>

          <!-- 描述 -->
          <view class="form-item">
            <view class="form-label">
              <text class="label-text">描述</text>
            </view>
            <view class="form-control">
              <textarea
                v-model="formData.description"
                class="form-textarea"
                placeholder="标签描述（可选）"
                maxlength="500"
              />
            </view>
            <view v-if="errors.description" class="form-error">
              <text class="error-text">{{ errors.description }}</text>
            </view>
          </view>

          <!-- 启用状态 -->
          <view class="form-item">
            <view class="form-label">
              <text class="label-text">启用状态</text>
            </view>
            <view class="form-control">
              <switch
                :checked="formData.is_active"
                @change="formData.is_active = $event.detail.value"
                color="var(--color-primary)"
              />
            </view>
          </view>
        </view>
      </view>

      <!-- 弹窗底部 -->
      <view class="dialog-footer">
        <view class="btn-cancel" @click="handleClose">
          <text class="btn-text">取消</text>
        </view>
        <view class="btn-confirm" :class="{ 'is-loading': submitting }" @click="handleSubmit">
          <text class="btn-text">{{ submitting ? '提交中...' : (mode === 'create' ? '创建' : '保存') }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { logger } from '@/logs/logger'
import { createTag, updateTag } from '@/api/tags'
import type { Tag } from '@/types/tags'

const props = defineProps<{
  visible: boolean
  mode: 'create' | 'edit'
  initialData: Tag | null
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  success: []
}>()

const submitting = ref(false)

const formData = reactive({
  name: '',
  slug: '',
  description: '',
  is_active: true
})

const errors = reactive({
  name: '',
  slug: '',
  description: ''
})

/** 监听初始数据，用于编辑模式填充表单 */
watch(
  () => props.initialData,
  (data) => {
    if (data && props.mode === 'edit') {
      formData.name = data.name
      formData.slug = data.slug || ''
      formData.description = data.description || ''
      formData.is_active = data.is_active
      logger.info('system', '标签弹窗加载编辑数据', {
        mode: props.mode,
        tag: { id: data.id, name: data.name, slug: data.slug }
      })
    }
  },
  { immediate: true }
)

/** 监听visible变化，重置表单 */
watch(
  () => props.visible,
  (val) => {
    if (!val) {
      resetForm()
    }
  }
)

/** 重置表单 */
function resetForm() {
  formData.name = ''
  formData.slug = ''
  formData.description = ''
  formData.is_active = true
  errors.name = ''
  errors.slug = ''
  errors.description = ''
}

/** 关闭弹窗 */
function handleClose() {
  emit('update:visible', false)
}

/** 验证表单 */
function validateForm(): boolean {
  let isValid = true
  errors.name = ''
  errors.slug = ''
  errors.description = ''

  // 名称验证
  if (!formData.name.trim()) {
    errors.name = '请输入标签名称'
    isValid = false
  } else if (formData.name.length < 1 || formData.name.length > 100) {
    errors.name = '长度在1-100个字符'
    isValid = false
  }

  // Slug验证（必填）
  if (!formData.slug.trim()) {
    errors.slug = '请输入Slug'
    isValid = false
  } else if (!/^[a-z0-9-]+$/.test(formData.slug)) {
    errors.slug = '只能包含小写字母、数字和连字符'
    isValid = false
  } else if (formData.slug.length > 100) {
    errors.slug = '长度不超过100个字符'
    isValid = false
  }

  // 描述验证
  if (formData.description && formData.description.length > 500) {
    errors.description = '长度不超过500个字符'
    isValid = false
  }

  if (!isValid) {
    logger.warn('system', '标签表单校验失败', {
      mode: props.mode,
      errors: { name: errors.name, slug: errors.slug, description: errors.description }
    })
  }

  return isValid
}

/** 提交 */
async function handleSubmit() {
  if (submitting.value) return
  if (!validateForm()) return

  submitting.value = true
  try {
    const payload = {
      name: formData.name.trim(),
      slug: formData.slug.trim(),
      description: formData.description.trim() || undefined,
      is_active: formData.is_active
    }

    logger.info('network', '提交标签表单', { mode: props.mode, payload })

    if (props.mode === 'create') {
      await createTag(payload)
      uni.showToast({ title: '标签创建成功', icon: 'success' })
    } else {
      await updateTag(props.initialData!.id, payload)
      uni.showToast({ title: '标签更新成功', icon: 'success' })
    }

    emit('update:visible', false)
    emit('success')
  } catch (error) {
    logger.error('system', props.mode === 'create' ? '创建标签失败' : '更新标签失败', error)
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
  max-height: 80vh;
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
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--color-border);

  .dialog-title {
    font-size: 18px;
    font-weight: 600;
    color: var(--color-text-primary);
  }

  .dialog-close {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;

    .close-icon {
      font-size: 18px;
      color: var(--color-text-secondary);
    }
  }
}

.dialog-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-lg);
}

.form {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.form-label {
  display: flex;
  align-items: center;
  gap: 4px;

  .label-text {
    font-size: 14px;
    font-weight: 500;
    color: var(--color-text-primary);
  }

  .label-required {
    font-size: 14px;
    color: #ff4d4f;
  }
}

.form-control {
  width: 100%;
}

.form-input {
  width: 100%;
  height: 36px;
  padding: 0 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-base);
  font-size: 14px;
  background-color: var(--color-bg-primary);
  box-sizing: border-box;

  &:focus {
    border-color: var(--color-primary);
  }
}

.form-textarea {
  width: 100%;
  min-height: 80px;
  padding: 8px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-base);
  font-size: 14px;
  background-color: var(--color-bg-primary);
  box-sizing: border-box;

  &:focus {
    border-color: var(--color-primary);
  }
}

.form-error {
  .error-text {
    font-size: 12px;
    color: #ff4d4f;
  }
}

.form-hint {
  .hint-text {
    font-size: 12px;
    color: var(--color-text-secondary);
  }
}

.dialog-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--spacing-md);
  padding: var(--spacing-lg);
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
  cursor: pointer;

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
  background-color: var(--color-primary);
  border-radius: var(--border-radius-base);
  cursor: pointer;

  .btn-text {
    font-size: 14px;
    color: #ffffff;
  }

  &.is-loading {
    opacity: 0.7;
    cursor: not-allowed;
  }
}
</style>
