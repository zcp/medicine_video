<!--
 * FeaturedContentFormDialog - 焦点图新增/编辑弹窗
 * @description 管理端焦点图的新增和编辑表单弹窗
 * @author 直播SaaS团队
 -->
<template>
  <view
    class="dialog-overlay"
    v-if="visible"
    @tap="handleOverlayTap"
    @touchmove.stop.prevent
  >
    <view class="dialog-container" @tap.stop="preventBubble" @touchmove.stop>
      <view class="dialog-header">
        <text class="dialog-title">{{ mode === 'create' ? '新增焦点图' : '编辑焦点图' }}</text>
        <view class="dialog-close" @tap.stop="handleClose">
          <text class="close-icon">✕</text>
        </view>
      </view>

      <!-- 对齐 CreateLive：内层 scroll-view 不绑 touchmove，由自身处理滚动 -->
      <scroll-view class="dialog-body" scroll-y :show-scrollbar="false">
        <view class="form">
          <view class="form-item">
            <view class="form-label">
              <text class="label-text">标题</text>
              <text class="label-required">*</text>
            </view>
            <input
              v-model="formData.title"
              class="form-input"
              placeholder="焦点图标题（1-255字符）"
              maxlength="255"
            />
            <view v-if="errors.title" class="form-error">
              <text class="error-text">{{ errors.title }}</text>
            </view>
          </view>

          <view class="form-item">
            <view class="form-label">
              <text class="label-text">焦点图图片</text>
              <text class="label-required">*</text>
            </view>
            <view class="image-upload-area">
              <image
                v-if="formData.image_url"
                :src="resolveMediaUrl(formData.image_url)"
                class="preview-image"
                mode="aspectFill"
                @click="handleChooseImage"
              />
              <view v-else class="upload-placeholder" @click="handleChooseImage">
                <text class="placeholder-icon">+</text>
                <text class="placeholder-text">点击上传 · 建议 750×320</text>
              </view>
              <view v-if="formData.image_url" class="image-actions">
                <view class="btn-rechoose" @click="handleChooseImage">
                  <text class="btn-text">更换图片</text>
                </view>
              </view>
            </view>
            <view v-if="errors.image_url" class="form-error">
              <text class="error-text">{{ errors.image_url }}</text>
            </view>
          </view>

          <view class="form-item">
            <view class="form-label">
              <text class="label-text">跳转类型</text>
            </view>
            <picker
              :value="targetTypeIndex"
              :range="targetTypeOptions"
              range-key="label"
              @change="handleTargetTypeChange"
            >
              <view class="picker-display">
                <text class="picker-text">
                  {{
                    isLegacyTargetType
                      ? '请选择新跳转类型（当前类型已废弃）'
                      : (targetTypeOptions[targetTypeIndex]?.label || '纯展示（不跳转）')
                  }}
                </text>
                <text class="picker-arrow">▼</text>
              </view>
            </picker>
          </view>

          <view class="form-item" v-if="formData.target_type === 'external'">
            <view class="form-label">
              <text class="label-text">外部链接</text>
              <text class="label-required">*</text>
            </view>
            <input
              v-model="formData.target_url"
              class="form-input"
              placeholder="https://example.com"
            />
            <view v-if="errors.target_url" class="form-error">
              <text class="error-text">{{ errors.target_url }}</text>
            </view>
          </view>

          <view class="form-item" v-if="formData.target_type === 'room'">
            <view class="form-label">
              <text class="label-text">关联直播间</text>
              <text class="label-required">*</text>
            </view>
            <RoomTargetSelector
              :model-value="formData.target_id"
              @update:model-value="formData.target_id = $event"
            />
            <view v-if="errors.target_id" class="form-error">
              <text class="error-text">{{ errors.target_id }}</text>
            </view>
          </view>

          <view
            class="form-item"
            v-else-if="formData.target_type && formData.target_type !== 'external'"
          >
            <view class="form-label">
              <text class="label-text">关联资源</text>
              <text class="label-required">*</text>
            </view>
            <TargetSelector
              :target-type="formData.target_type"
              :model-value="formData.target_id"
              @update:model-value="formData.target_id = $event"
            />
            <view v-if="errors.target_id" class="form-error">
              <text class="error-text">{{ errors.target_id }}</text>
            </view>
          </view>

          <view v-if="isLegacyTargetType" class="legacy-hint">
            <text class="legacy-text">当前为已废弃跳转类型，请重新选择跳转类型</text>
          </view>

          <!-- 排序 + 启用：并排压缩高度 -->
          <view class="form-row">
            <view class="form-item form-item--half">
              <view class="form-label">
                <text class="label-text">排序</text>
                <text class="hint-inline">越小越前</text>
              </view>
              <input
                v-model.number="formData.sort_order"
                class="form-input"
                type="number"
                placeholder="0"
              />
            </view>
            <view class="form-item form-item--half form-item--switch">
              <view class="form-label">
                <text class="label-text">启用</text>
              </view>
              <switch
                :checked="formData.is_active"
                @change="formData.is_active = $event.detail.value"
                color="var(--color-primary)"
              />
            </view>
          </view>

          <!-- 上线 / 下线时间并排 -->
          <view class="form-row">
            <view class="form-item form-item--half">
              <view class="form-label">
                <text class="label-text">上线</text>
              </view>
              <picker mode="date" :value="startDateStr" @change="handleStartDateChange">
                <view class="picker-display">
                  <text class="picker-text">{{ startDateStr || '可选' }}</text>
                  <text class="picker-arrow">▼</text>
                </view>
              </picker>
            </view>
            <view class="form-item form-item--half">
              <view class="form-label">
                <text class="label-text">下线</text>
              </view>
              <picker
                mode="date"
                :value="endDateStr"
                :start="startDateStr"
                @change="handleEndDateChange"
              >
                <view class="picker-display">
                  <text class="picker-text">{{ endDateStr || '可选' }}</text>
                  <text class="picker-arrow">▼</text>
                </view>
              </picker>
            </view>
          </view>
        </view>
      </scroll-view>

      <!-- 弹窗底部 -->
      <view class="dialog-footer">
        <view class="btn-cancel" @tap.stop="handleClose">
          <text class="btn-text">取消</text>
        </view>
        <view class="btn-confirm" :class="{ 'is-loading': submitting }" @tap.stop="handleSubmit">
          <text class="btn-text">{{ submitting ? '提交中...' : (mode === 'create' ? '创建' : '保存') }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { DEFAULT_CONFIG } from '@/common/constants'
import { logger } from '@/logs/logger'
import { resolveMediaUrl } from '@/utils/url'
import { createFeaturedContent, updateFeaturedContent, uploadFeaturedContentImage } from '@/api/featuredContent'
import type {
  FeaturedContent,
  FeaturedContentTargetType,
  FeaturedContentLegacyTargetType
} from '@/types/featuredContent'
import { FEATURED_CONTENT_TARGET_TYPE_OPTIONS } from '@/types/featuredContent'
import TargetSelector from '@/components/TargetSelector.vue'
import RoomTargetSelector from './RoomTargetSelector.vue'

const props = defineProps<{
  visible: boolean
  mode: 'create' | 'edit'
  initialData: FeaturedContent | null
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  success: []
}>()

const submitting = ref(false)

const formData = reactive({
  title: '',
  image_url: '',
  target_type: '' as FeaturedContentTargetType | FeaturedContentLegacyTargetType | '',
  target_id: '',
  target_url: '',
  sort_order: 0,
  is_active: true,
  start_at: '',
  end_at: ''
})

const errors = reactive({
  title: '',
  image_url: '',
  target_url: '',
  target_id: ''
})

// 跳转类型选项（全站统一，不含专家/专题）
const targetTypeOptions = FEATURED_CONTENT_TARGET_TYPE_OPTIONS

const isLegacyTargetType = computed(() => {
  return formData.target_type === 'topic' || formData.target_type === 'expert'
})

const targetTypeIndex = computed(() => {
  return targetTypeOptions.findIndex(opt => opt.value === formData.target_type)
})

// 日期格式化（用于 picker 显示）
const startDateStr = computed(() => {
  return formData.start_at ? formData.start_at.slice(0, 10) : ''
})

const endDateStr = computed(() => {
  return formData.end_at ? formData.end_at.slice(0, 10) : ''
})

// 监听初始数据，用于编辑模式填充表单
watch(
  () => props.initialData,
  (data) => {
    if (data && props.mode === 'edit') {
      formData.title = data.title || ''
      formData.image_url = data.image_url || ''
      formData.target_type = data.target_type || ''
      formData.target_id = data.target_id || ''
      formData.target_url = data.target_url || ''
      formData.sort_order = data.sort_order || 0
      formData.is_active = data.is_active
      formData.start_at = data.start_at || ''
      formData.end_at = data.end_at || ''
      logger.info('system', '焦点图弹窗加载编辑数据', {
        mode: props.mode,
        id: data.id,
        title: data.title
      })
    }
  },
  { immediate: true }
)

// 监听visible变化，重置表单
watch(
  () => props.visible,
  (val) => {
    if (!val) {
      resetForm()
    }
  }
)

// 重置表单
function resetForm() {
  formData.title = ''
  formData.image_url = ''
  formData.target_type = ''
  formData.target_id = ''
  formData.target_url = ''
  formData.sort_order = 0
  formData.is_active = true
  formData.start_at = ''
  formData.end_at = ''
  errors.title = ''
  errors.image_url = ''
  errors.target_url = ''
  errors.target_id = ''
}

// 关闭弹窗
function handleClose() {
  emit('update:visible', false)
}

/** 仅点击遮罩关闭；内容区须 @tap.stop，小程序里 @click.stop 常拦不住冒泡 */
function handleOverlayTap() {
  handleClose()
}

function preventBubble() {
  // 占位：配合 @tap.stop，阻止内容点击冒泡到遮罩
}

// 选择图片并上传
async function handleChooseImage() {
  try {
    const res = await new Promise<UniApp.ChooseImageSuccessCallbackResult>((resolve, reject) => {
      uni.chooseImage({
        count: 1,
        sizeType: ['compressed'],
        sourceType: ['album', 'camera'],
        success: resolve,
        fail: reject
      })
    })

    const filePath = res.tempFilePaths[0]
    if (!filePath) return

    // 先本地预览
    formData.image_url = filePath
    errors.image_url = ''
    logger.info('user', '选择焦点图图片', { path: filePath })

    // 如果是编辑模式且已有ID，立即上传到服务器
    if (props.mode === 'edit' && props.initialData?.id) {
      uni.showLoading({ title: '上传中...', mask: true })
      try {
        const uploadRes = await uploadFeaturedContentImage(props.initialData.id, filePath)
        // 兼容多种后端返回格式：data.image_url / image_url / data.url
        const serverUrl = uploadRes?.data?.image_url
          || (uploadRes?.data as any)?.url
          || (uploadRes as any)?.image_url
        logger.info('network', '编辑模式图片上传响应', {
          serverUrl,
          rawResponse: JSON.stringify(uploadRes)
        })
        if (serverUrl) {
          formData.image_url = serverUrl
          logger.info('network', '图片上传成功，使用服务器URL', { serverUrl })
        } else {
          logger.warn('system', '上传成功但未获取到服务器URL，保留本地预览', {
            response: JSON.stringify(uploadRes)
          })
        }
      } catch (error) {
        logger.error('system', '图片上传失败', error)
        uni.showToast({ title: '图片上传失败', icon: 'none' })
        // 上传失败，清除预览
        formData.image_url = ''
      } finally {
        uni.hideLoading()
      }
    }
    // 创建模式下，图片会在提交后由后端处理
  } catch {
    // 用户取消选择
  }
}

// 跳转类型变更
function handleTargetTypeChange(e: any) {
  const index = e.detail.value
  formData.target_type = targetTypeOptions[index].value as FeaturedContentTargetType | ''
  formData.target_id = ''
  formData.target_url = ''
}

// 上线时间变更
function handleStartDateChange(e: any) {
  const dateStr = e.detail.value
  formData.start_at = dateStr ? `${dateStr}T00:00:00` : ''
}

// 下线时间变更
function handleEndDateChange(e: any) {
  const dateStr = e.detail.value
  formData.end_at = dateStr ? `${dateStr}T23:59:59` : ''
}

// 验证表单
function validateForm(): boolean {
  let isValid = true
  errors.title = ''
  errors.image_url = ''
  errors.target_url = ''
  errors.target_id = ''

  // 标题验证
  if (!formData.title.trim()) {
    errors.title = '请输入标题'
    isValid = false
  } else if (formData.title.length > 255) {
    errors.title = '长度不超过255个字符'
    isValid = false
  }

  // 图片验证
  if (!formData.image_url) {
    errors.image_url = '请上传焦点图图片'
    isValid = false
  }

  // 外部链接验证
  if (formData.target_type === 'external') {
    if (!formData.target_url.trim()) {
      errors.target_url = '请输入外部链接'
      isValid = false
    } else if (!/^https?:\/\/.+/.test(formData.target_url)) {
      errors.target_url = '请输入有效的URL（以http://或https://开头）'
      isValid = false
    }
  }

  // 内部资源ID验证
  if (formData.target_type && formData.target_type !== 'external' && !formData.target_id.trim()) {
    errors.target_id = '请输入关联资源ID'
    isValid = false
  }

  // 废弃类型须重新选择
  if (isLegacyTargetType.value) {
    uni.showToast({ title: '请重新选择跳转类型', icon: 'none' })
    isValid = false
  }

  return isValid
}

// 提交
async function handleSubmit() {
  if (submitting.value) return
  if (!validateForm()) return

  submitting.value = true
  try {
    // 判断 image_url 是否为本地临时路径
    const isLocalPath = formData.image_url && (
      formData.image_url.startsWith('http://tmp') ||
      formData.image_url.startsWith('https://tmp') ||
      formData.image_url.startsWith('_') ||
      formData.image_url.includes('tmp/') ||
      (!formData.image_url.startsWith('http') && !formData.image_url.startsWith('/media'))
    )

    // 构建 payload
    const payload: any = {
      title: formData.title.trim(),
      sort_order: formData.sort_order,
      is_active: formData.is_active,
      start_at: formData.start_at || null,
      end_at: formData.end_at || null
    }

    // 只有当 image_url 是有效的服务器URL时才包含
    if (!isLocalPath && formData.image_url) {
      payload.image_url = formData.image_url
    }

    // 跳转目标
    if (formData.target_type) {
      payload.target_type = formData.target_type
      if (formData.target_type === 'external') {
        payload.target_url = formData.target_url.trim()
      } else {
        payload.target_id = formData.target_id.trim()
      }
    }

    logger.info('network', '提交焦点图表单', {
      mode: props.mode,
      title: payload.title,
      hasLocalImage: isLocalPath,
      hasImageUrl: !!payload.image_url
    })

    if (props.mode === 'create') {
      // 创建焦点图（必须有 image_url，使用占位图）
      if (!payload.image_url) {
        payload.image_url = DEFAULT_CONFIG.DEFAULT_BANNER // 占位图
      }
      const createRes = await createFeaturedContent(payload)
      const newId = createRes?.data?.id

      // 如果有本地图片且创建成功，上传真实图片并回写URL
      if (isLocalPath && newId) {
        uni.showLoading({ title: '上传图片...', mask: true })
        try {
          const uploadRes = await uploadFeaturedContentImage(newId, formData.image_url)
          // 兼容多种后端返回格式：data.image_url / image_url / data.url
          const serverUrl = uploadRes?.data?.image_url
            || (uploadRes?.data as any)?.url
            || (uploadRes as any)?.image_url
          if (serverUrl) {
            // 将服务器返回的图片URL回写到数据库
            await updateFeaturedContent(newId, { image_url: serverUrl })
            logger.info('network', '创建后图片上传并回写成功', { contentId: newId, serverUrl })
          } else {
            logger.error('system', '上传成功但未返回服务器URL', { contentId: newId, response: uploadRes })
            uni.showToast({ title: '图片上传异常，请编辑重新上传', icon: 'none', duration: 3000 })
          }
        } catch (uploadError) {
          logger.error('system', '创建后图片上传失败', uploadError)
          uni.showToast({ title: '图片上传失败，请编辑重新上传', icon: 'none', duration: 3000 })
        } finally {
          uni.hideLoading()
        }
      }

      uni.showToast({ title: '焦点图创建成功', icon: 'success' })
    } else {
      // 更新焦点图
      await updateFeaturedContent(props.initialData!.id, payload)
      uni.showToast({ title: '焦点图更新成功', icon: 'success' })
    }

    emit('update:visible', false)
    emit('success')
  } catch (error) {
    logger.error('system', props.mode === 'create' ? '创建焦点图失败' : '更新焦点图失败', error)
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
  inset: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 24px 16px;
  box-sizing: border-box;
  overscroll-behavior: none;
}

.dialog-container {
  width: 100%;
  max-width: 420px;
  max-height: 86vh;
  background-color: var(--color-bg-primary);
  border-radius: var(--border-radius-lg);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-sizing: border-box;
  overscroll-behavior: contain;
}

.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;

  .dialog-title {
    font-size: 16px;
    font-weight: 600;
    color: var(--color-text-primary);
  }

  .dialog-close {
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;

    .close-icon {
      font-size: 16px;
      color: var(--color-text-secondary);
    }
  }
}

.dialog-body {
  flex: 1;
  min-height: 0;
  height: 62vh;
  max-height: 62vh;
  padding: 12px 16px;
  box-sizing: border-box;
  width: 100%;
  overscroll-behavior: contain;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
  box-sizing: border-box;
  overflow-x: hidden;
}

.form-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  width: 100%;
  box-sizing: border-box;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  width: 100%;
  min-width: 0;
  box-sizing: border-box;

  &--half {
    flex: 1;
  }

  &--switch {
    align-items: flex-start;
  }
}

.form-label {
  display: flex;
  align-items: center;
  gap: 4px;

  .label-text {
    font-size: 13px;
    font-weight: 500;
    color: var(--color-text-primary);
  }

  .label-required {
    font-size: 13px;
    color: #ff4d4f;
  }

  .hint-inline {
    font-size: 11px;
    color: var(--color-text-secondary);
    font-weight: 400;
  }
}

.form-input {
  width: 100%;
  height: 34px;
  padding: 0 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-base);
  font-size: 13px;
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

.legacy-hint {
  padding: 8px 10px;
  background-color: #fffbe6;
  border: 1px solid #ffe58f;
  border-radius: var(--border-radius-base);
  box-sizing: border-box;

  .legacy-text {
    font-size: 12px;
    color: #ad6800;
  }
}

.image-upload-area {
  display: flex;
  flex-direction: column;
  gap: 6px;
  width: 100%;
  box-sizing: border-box;
}

.preview-image {
  width: 100%;
  height: 96px;
  border-radius: var(--border-radius-sm);
  display: block;
  box-sizing: border-box;
}

.upload-placeholder {
  width: 100%;
  height: 96px;
  border: 1px dashed var(--color-border);
  border-radius: var(--border-radius-sm);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  cursor: pointer;
  box-sizing: border-box;

  .placeholder-icon {
    font-size: 22px;
    color: var(--color-text-secondary);
  }

  .placeholder-text {
    font-size: 12px;
    color: var(--color-text-secondary);
  }
}

.image-actions {
  .btn-rechoose {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    height: 26px;
    padding: 0 10px;
    border: 1px solid var(--color-border);
    border-radius: var(--border-radius-sm);
    background-color: transparent;
    cursor: pointer;

    .btn-text {
      font-size: 12px;
      color: var(--color-text-secondary);
    }
  }
}

.picker-display {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 34px;
  padding: 0 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-base);
  background-color: var(--color-bg-primary);
  box-sizing: border-box;
  width: 100%;
  min-width: 0;
  gap: 6px;

  .picker-text {
    flex: 1;
    min-width: 0;
    font-size: 13px;
    color: var(--color-text-primary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .picker-arrow {
    font-size: 10px;
    color: var(--color-text-secondary);
    flex-shrink: 0;
  }
}

.dialog-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  padding: 10px 16px;
  border-top: 1px solid var(--color-border);
  flex-shrink: 0;
  box-sizing: border-box;
}

.btn-cancel,
.btn-confirm {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 34px;
  padding: 0 16px;
  border-radius: var(--border-radius-base);
  cursor: pointer;

  .btn-text {
    font-size: 13px;
  }
}

.btn-cancel {
  background-color: var(--color-bg-secondary);

  .btn-text {
    color: var(--color-text-primary);
  }
}

.btn-confirm {
  background-color: var(--color-primary);

  .btn-text {
    color: #ffffff;
  }

  &.is-loading {
    opacity: 0.7;
    cursor: not-allowed;
  }
}
</style>
