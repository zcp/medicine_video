<!--
 * TabEditDialog - Tab新增/编辑弹窗
 * @description 支持新增和编辑Tab，所有Tab均支持图文内容
 -->
<template>
  <view class="dialog-overlay" @click="handleClose">
    <view class="dialog" @click.stop>
      <view class="dialog__header">
        <text class="dialog__title">{{ isEdit ? '编辑Tab' : '新增Tab' }}</text>
        <view class="dialog__close" @click="handleClose">
          <text class="dialog__close-text">✕</text>
        </view>
      </view>

      <view class="dialog__body">
        <!-- tab_key (只允许 intro 类型) -->
        <view class="field">
          <text class="field__label"><text class="required">*</text>Tab类型</text>
          <view
            class="field__input field__select"
            :class="{ 'field__input--disabled': isEdit }"
          >
            <text class="field__select-text">{{ form.tab_key === 'intro' ? 'intro（介绍）' : '请选择Tab类型' }}</text>
          </view>
          <text class="field__hint">{{ isEdit ? '创建后不可修改' : 'intro 类型' }}</text>
        </view>

        <!-- 标题 -->
        <view class="field">
          <text class="field__label"><text class="required">*</text>标题</text>
          <input
            class="field__input"
            v-model="form.title"
            placeholder="请输入Tab标题"
            maxlength="128"
          />
          <text class="field__count">{{ form.title.length }}/128</text>
        </view>

        <!-- 文字内容 -->
        <view class="field">
          <text class="field__label">文字内容</text>
          <textarea
            class="field__textarea"
            v-model="form.text_content"
            placeholder="请输入文本内容"
            :maxlength="50000"
          />
        </view>

        <!-- 配图 -->
        <view class="field">
          <text class="field__label">配图</text>
          <view class="field__image-area">
            <image
              v-if="imagePreviewUrl"
              class="field__image"
              :src="imagePreviewUrl"
              mode="aspectFill"
            />
            <view v-else class="field__image-placeholder">
              <text class="field__image-placeholder-text">未上传图片</text>
            </view>
          </view>
          <view class="field__image-actions">
            <view class="ghost-btn" @click="handlePickImage">
              <text class="ghost-btn__text">选择图片</text>
            </view>
            <view v-if="form.image_url" class="ghost-btn ghost-btn--danger" @click="handleClearImage">
              <text class="ghost-btn__text">删除图片</text>
            </view>
          </view>
          <text class="field__hint">支持 jpg/png/webp，最大 2MB</text>
        </view>

        <!-- 排序 -->
        <view class="field">
          <text class="field__label">排序权重</text>
          <input
            class="field__input"
            v-model.number="form.sort_order"
            type="number"
            placeholder="0"
          />
          <text class="field__hint">数值越小越靠前</text>
        </view>

        <!-- 启用状态 -->
        <view class="field field--switch">
          <text class="field__label">启用</text>
          <view
            :class="['switch', form.is_active ? 'switch--on' : 'switch--off']"
            @click="form.is_active = !form.is_active"
          >
            <view class="switch__thumb" />
          </view>
        </view>
      </view>

      <view class="dialog__footer">
        <view class="ghost-btn" @click="handleClose">
          <text class="ghost-btn__text">取消</text>
        </view>
        <view class="primary-btn" :class="{ 'primary-btn--disabled': saving }" @click="handleSave">
          <text class="primary-btn__text">{{ saving ? '保存中...' : '保存' }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { createTab, updateTab, uploadTabImage } from '@/api/tabs'
import type { LiveRoomTab, LiveRoomTabContentType, LiveRoomTabCreate, LiveRoomTabUpdate } from '@/api/tabs'
import { resolveMediaUrl } from '@/utils/url'
import { handleContentSafetyError, getUserFacingErrorMessage } from '@/utils/contentSafety'

/**
 * 组件Props
 */
const props = defineProps<{
  /** 编辑的Tab（null表示新增） */
  tab: LiveRoomTab | null
  /** 房间ID */
  roomId: string
}>()

/**
 * 组件Emits
 */
const emit = defineEmits<{
  close: []
  saved: []
}>()

/** 是否编辑模式 */
const isEdit = computed(() => !!props.tab)

/** 表单数据 */
const form = ref({
  tab_key: 'intro',  // 默认为 intro 类型
  title: '',
  content_type: 'mixed' as LiveRoomTabContentType,
  text_content: '',
  image_url: '',
  sort_order: 0,
  is_active: true
})

/** 图片预览URL */
const imagePreviewUrl = computed(() => resolveMediaUrl(form.value.image_url) || '')

/** 保存中 */
const saving = ref(false)

/**
 * 初始化表单
 */
onMounted(() => {
  if (props.tab) {
    form.value = {
      tab_key: props.tab.tab_key || 'intro',
      title: props.tab.title || '',
      content_type: 'mixed',
      text_content: props.tab.text_content || '',
      image_url: props.tab.image_url || '',
      sort_order: props.tab.sort_order ?? 0,
      is_active: props.tab.is_active !== false
    }
  }
})

/**
 * 选择图片并上传
 */
async function handlePickImage() {
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

    // 校验文件大小（2MB）
    const fileInfo = await new Promise<UniApp.GetFileInfoSuccessCallbackResult>((resolve, reject) => {
      uni.getFileInfo({
        filePath,
        success: resolve,
        fail: reject
      })
    })
    if (fileInfo.size > 2 * 1024 * 1024) {
      uni.showToast({ title: '图片不能超过2MB', icon: 'none' })
      return
    }

    // 上传到后端（小程序使用 uni.uploadFile）
    saving.value = true
    const uploadRes = await uploadTabImage(props.roomId, filePath)
    const imageUrl = uploadRes.data?.image_url
    if (imageUrl) {
      form.value.image_url = imageUrl
      uni.showToast({ title: '图片上传成功', icon: 'success' })
    }
  } catch {
    uni.showToast({ title: '图片上传失败', icon: 'none' })
  } finally {
    saving.value = false
  }
}

/**
 * 清除图片
 */
function handleClearImage() {
  form.value.image_url = ''
}

/**
 * 关闭弹窗
 */
function handleClose() {
  emit('close')
}

/**
 * 保存
 */
async function handleSave() {
  // 校验
  const tabKey = form.value.tab_key.trim()
  const title = form.value.title.trim()
  if (!tabKey) {
    uni.showToast({ title: '请输入Tab标识', icon: 'none' })
    return
  }
  if (/\s/.test(tabKey)) {
    uni.showToast({ title: 'Tab标识不可包含空格', icon: 'none' })
    return
  }
  if (!title) {
    uni.showToast({ title: '请输入Tab标题', icon: 'none' })
    return
  }

  saving.value = true
  try {
    if (isEdit.value && props.tab) {
      // 更新（部分更新，只发有值的字段，tab_key 创建后不可修改）
      const data: LiveRoomTabUpdate = {
        title,
        content_type: 'mixed',
        text_content: form.value.text_content || undefined,
        image_url: form.value.image_url || undefined,
        sort_order: form.value.sort_order,
        is_active: form.value.is_active
      }
      await updateTab(props.tab.id, data)
      uni.showToast({ title: '保存成功', icon: 'success' })
    } else {
      // 创建
      const data: LiveRoomTabCreate = {
        tab_key: tabKey,
        title,
        content_type: 'mixed',
        text_content: form.value.text_content || undefined,
        image_url: form.value.image_url || undefined,
        sort_order: form.value.sort_order,
        is_active: form.value.is_active
      }
      await createTab(props.roomId, data)
      uni.showToast({ title: '创建成功', icon: 'success' })
    }
    emit('saved')
  } catch (e) {
    if (handleContentSafetyError(e)) return
    uni.showToast({ title: getUserFacingErrorMessage(e, '保存失败，请稍后再试'), icon: 'none' })
  } finally {
    saving.value = false
  }
}
</script>

<style lang="scss" scoped>
.dialog-overlay {
  position: fixed;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 32rpx;
}

.dialog {
  width: 100%;
  max-height: 80vh;
  background-color: var(--color-bg-primary);
  border-radius: 16rpx;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.dialog__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24rpx 32rpx;
  border-bottom: 1rpx solid var(--color-border);
}

.dialog__title {
  font-size: 32rpx;
  font-weight: 600;
  color: var(--color-text-primary);
}

.dialog__close {
  width: 48rpx;
  height: 48rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.dialog__close-text {
  font-size: 32rpx;
  color: var(--color-text-secondary);
}

.dialog__body {
  flex: 1;
  overflow-y: auto;
  padding: 24rpx 32rpx;
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.field--switch {
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
}

.field__label {
  font-size: 26rpx;
  color: var(--color-text-primary);
  font-weight: 500;
}

.required {
  color: #ff4d4f;
  margin-right: 4rpx;
}

.field__input {
  height: 72rpx;
  padding: 0 20rpx;
  border: 1rpx solid var(--color-border);
  border-radius: 8rpx;
  font-size: 28rpx;
  background-color: var(--color-bg-secondary);

  &--disabled {
    opacity: 0.6;
    color: var(--color-text-tertiary);
  }
}

.field__select {
  display: flex;
  align-items: center;
  background-color: var(--color-bg-secondary);
}

.field__select-text {
  font-size: 28rpx;
  color: var(--color-text-primary);
}

.field__textarea {
  min-height: 200rpx;
  padding: 16rpx 20rpx;
  border: 1rpx solid var(--color-border);
  border-radius: 8rpx;
  font-size: 28rpx;
  background-color: var(--color-bg-secondary);
}

.field__count {
  font-size: 22rpx;
  color: var(--color-text-tertiary);
  text-align: right;
}

.field__hint {
  font-size: 22rpx;
  color: var(--color-text-tertiary);
}

.field__image-area {
  width: 300rpx;
  height: 180rpx;
  border-radius: 8rpx;
  overflow: hidden;
}

.field__image {
  width: 100%;
  height: 100%;
}

.field__image-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--color-bg-secondary);
  border: 1rpx dashed var(--color-border);
}

.field__image-placeholder-text {
  font-size: 24rpx;
  color: var(--color-text-tertiary);
}

.field__image-actions {
  display: flex;
  gap: 16rpx;
  margin-top: 8rpx;
}

.ghost-btn {
  padding: 12rpx 24rpx;
  border: 1rpx solid var(--color-border);
  border-radius: 8rpx;
}

.ghost-btn--danger {
  border-color: #ff4d4f;
  .ghost-btn__text { color: #ff4d4f; }
}

.ghost-btn__text {
  font-size: 24rpx;
  color: var(--color-text-primary);
}

.switch {
  width: 88rpx;
  height: 48rpx;
  border-radius: 24rpx;
  position: relative;
  transition: background-color 0.2s;
}

.switch--on {
  background-color: var(--color-primary);
  .switch__thumb { transform: translateX(40rpx); }
}

.switch--off {
  background-color: var(--color-border);
}

.switch__thumb {
  width: 40rpx;
  height: 40rpx;
  border-radius: 50%;
  background-color: #ffffff;
  position: absolute;
  top: 4rpx;
  left: 4rpx;
  transition: transform 0.2s;
}

.dialog__footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 16rpx;
  padding: 20rpx 32rpx;
  border-top: 1rpx solid var(--color-border);
}

.primary-btn {
  padding: 16rpx 32rpx;
  background-color: var(--color-primary);
  border-radius: 8rpx;

  &--disabled {
    opacity: 0.5;
  }
}

.primary-btn__text {
  font-size: 28rpx;
  color: #ffffff;
}
</style>
