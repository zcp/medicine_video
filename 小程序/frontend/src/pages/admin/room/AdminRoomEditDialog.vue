<!--
 * AdminRoomEditDialog - 管理端直播间内容编辑弹窗
 * 标题 / 简介 / 不公开 / 封面 + 科室 + 子模块入口 + 删房
 -->
<template>
  <view v-if="visible" class="dialog-overlay" @tap="handleClose">
    <view class="dialog-container" @tap.stop>
      <view class="dialog-header">
        <text class="dialog-title">编辑直播间内容</text>
        <view class="dialog-close" @tap="handleClose">
          <text class="close-icon">✕</text>
        </view>
      </view>

      <scroll-view scroll-y class="dialog-body" :show-scrollbar="false">
        <view v-if="loadingDetail" class="loading-inline">
          <text class="loading-text">加载详情中...</text>
        </view>

        <view v-else class="form">
          <view class="form-item">
            <view class="form-label">
              <text class="label-text">标题</text>
              <text class="label-required">*</text>
            </view>
            <view class="form-control">
              <input
                v-model="form.title"
                class="form-input"
                placeholder="请输入直播间标题"
                maxlength="100"
              />
            </view>
            <view v-if="errors.title" class="form-error">
              <text class="error-text">{{ errors.title }}</text>
            </view>
          </view>

          <view class="form-item">
            <view class="form-label">
              <text class="label-text">简介</text>
            </view>
            <view class="form-control">
              <textarea
                v-model="form.description"
                class="form-textarea"
                placeholder="直播间简介（可选）"
                maxlength="2000"
              />
            </view>
          </view>

          <view class="form-item">
            <view class="form-label">
              <text class="label-text">不公开直播间</text>
            </view>
            <view class="form-control switch-row" @tap="form.is_private = !form.is_private">
              <text class="switch-label">{{ form.is_private ? '不公开' : '公开' }}</text>
              <view :class="['switch-track', form.is_private ? 'on' : '']">
                <view class="switch-thumb" />
              </view>
            </view>
            <text class="field-hint">广场/发现列表不可见；持分享链接可观看。管理员列表仍可找到</text>
          </view>

          <view class="form-item">
            <view class="form-label">
              <text class="label-text">封面</text>
            </view>
            <view class="cover-row">
              <view class="cover-preview">
                <image
                  v-if="coverPreview"
                  :src="coverPreview"
                  class="cover-img"
                  mode="aspectFill"
                />
                <view v-else class="cover-placeholder">
                  <text class="cover-text">无封面</text>
                </view>
              </view>
              <view class="cover-actions">
                <view class="action-chip" :class="{ disabled: uploadingCover }" @tap="handlePickCover">
                  <text class="chip-text">{{ uploadingCover ? '上传中...' : '换封面' }}</text>
                </view>
              </view>
            </view>
          </view>

          <view v-if="roomId" class="form-item">
            <RoomCategorySelector :room-id="roomId" />
          </view>

          <view class="form-item">
            <view class="form-label">
              <text class="label-text">快捷操作</text>
            </view>
            <view class="shortcut-row">
              <view class="action-chip" @tap="goTabs">
                <text class="chip-text">Tab 管理</text>
              </view>
              <view class="action-chip" @tap="goMessages">
                <text class="chip-text">讨论管理</text>
              </view>
              <view class="action-chip" @tap="goSessionTags">
                <text class="chip-text">场次标签</text>
              </view>
              <view class="action-chip action-chip--warn" @tap="handleClearMessages">
                <text class="chip-text">清空讨论</text>
              </view>
            </view>
            <text class="field-hint">标签挂在场次上：点「场次标签」进入编辑直播页设置（最多5个，须匹配词库）。品牌绑定也走该页。</text>
          </view>

          <view class="form-item danger-zone">
            <view class="form-label">
              <text class="label-text danger-label">危险操作</text>
            </view>
            <view class="action-chip action-chip--danger" @tap="handleDeleteRoom">
              <text class="chip-text">删除直播间</text>
            </view>
            <text class="field-hint">将删除该房间及相关内容，不可恢复</text>
          </view>
        </view>
      </scroll-view>

      <view class="dialog-footer">
        <view class="btn-cancel" @tap="handleClose">
          <text class="btn-text">取消</text>
        </view>
        <view
          class="btn-confirm"
          :class="{ 'is-loading': submitting }"
          @tap="handleSave"
        >
          <text class="btn-text">{{ submitting ? '保存中...' : '保存' }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import {
  getRoomById,
  updateRoom,
  uploadRoomCover,
  deleteRoom
} from '@/api/room'
import { clearRoomMessages } from '@/api/roomMessage'
import { resolveMediaUrl } from '@/utils/url'
import { handleContentSafetyError, getUserFacingErrorMessage } from '@/utils/contentSafety'
import RoomCategorySelector from '@/components/RoomCategorySelector.vue'

const props = defineProps<{
  visible: boolean
  roomId: string
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  success: []
}>()

const loadingDetail = ref(false)
const submitting = ref(false)
const uploadingCover = ref(false)

const form = reactive({
  title: '',
  description: '',
  is_private: false,
  cover_url: '' as string
})

const errors = reactive({
  title: ''
})

const coverPreview = computed(() => resolveMediaUrl(form.cover_url) || '')

function resetForm() {
  form.title = ''
  form.description = ''
  form.is_private = false
  form.cover_url = ''
  errors.title = ''
}

async function loadDetail() {
  const id = String(props.roomId || '').trim()
  if (!id) return

  loadingDetail.value = true
  try {
    const res = await getRoomById(id)
    if (res.code !== 200 || !res.data) {
      uni.showToast({
        title: res.message || '加载直播间详情失败',
        icon: 'none'
      })
      return
    }
    const r: any = res.data
    form.title = String(r.title || '')
    form.description = String(r.description || r.summary || '')
    form.is_private = Boolean(r.is_private)
    form.cover_url = String(r.cover_url || r.coverUrl || r.cover || '')
  } catch (e: any) {
    uni.showToast({
      title: getUserFacingErrorMessage(e, '加载详情失败'),
      icon: 'none'
    })
  } finally {
    loadingDetail.value = false
  }
}

watch(
  () => props.visible,
  (val) => {
    if (val) {
      resetForm()
      void loadDetail()
    } else {
      resetForm()
    }
  }
)

function handleClose() {
  if (submitting.value || uploadingCover.value) return
  emit('update:visible', false)
}

function validate(): boolean {
  errors.title = ''
  const title = form.title.trim()
  if (!title) {
    errors.title = '请输入直播间标题'
    return false
  }
  if (title.length > 100) {
    errors.title = '标题不超过 100 个字符'
    return false
  }
  return true
}

async function handleSave() {
  if (submitting.value || loadingDetail.value) return
  if (!validate()) return

  const id = String(props.roomId || '').trim()
  if (!id) {
    uni.showToast({ title: '缺少房间 ID', icon: 'none' })
    return
  }

  submitting.value = true
  try {
    const res = await updateRoom(id, {
      title: form.title.trim(),
      description: form.description.trim(),
      is_private: form.is_private
    })
    if (res.code !== 200) {
      if (handleContentSafetyError(res)) return
      uni.showToast({
        title: getUserFacingErrorMessage(res, '保存失败'),
        icon: 'none'
      })
      return
    }
    uni.showToast({ title: '已保存', icon: 'success' })
    emit('success')
    emit('update:visible', false)
  } catch (e: any) {
    if (handleContentSafetyError(e)) return
    uni.showToast({
      title: getUserFacingErrorMessage(e, '保存失败，请稍后再试'),
      icon: 'none'
    })
  } finally {
    submitting.value = false
  }
}

function handlePickCover() {
  if (uploadingCover.value) return
  const id = String(props.roomId || '').trim()
  if (!id) return

  uni.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success: async (chooseRes) => {
      const filePath = chooseRes.tempFilePaths?.[0]
      if (!filePath) return
      uploadingCover.value = true
      try {
        const res = await uploadRoomCover(id, filePath)
        if (res.code !== 200) {
          uni.showToast({
            title: getUserFacingErrorMessage(res, '封面上传失败'),
            icon: 'none'
          })
          return
        }
        const url = String((res.data as any)?.cover_url || '')
        if (url) form.cover_url = url
        uni.showToast({ title: '封面已更新', icon: 'success' })
        emit('success')
      } catch (e: any) {
        uni.showToast({
          title: getUserFacingErrorMessage(e, '封面上传失败'),
          icon: 'none'
        })
      } finally {
        uploadingCover.value = false
      }
    }
  })
}

function goTabs() {
  const id = String(props.roomId || '').trim()
  if (!id) return
  emit('update:visible', false)
  uni.navigateTo({
    url: `/pages/admin/roomTab/RoomTabManagerShell?roomId=${encodeURIComponent(id)}`
  })
}

function goMessages() {
  const id = String(props.roomId || '').trim()
  if (!id) return
  emit('update:visible', false)
  uni.navigateTo({
    url: `/pages/admin/roomMessage/RoomMessageList?roomId=${encodeURIComponent(id)}`
  })
}

/** 标签属场次能力，复用 CreateLive 编辑页（含 #解析 / 词库匹配） */
function goSessionTags() {
  const id = String(props.roomId || '').trim()
  if (!id) return
  emit('update:visible', false)
  uni.navigateTo({
    url: `/pages/live/CreateLive?mode=edit&roomId=${encodeURIComponent(id)}`
  })
}

function handleClearMessages() {
  const id = String(props.roomId || '').trim()
  if (!id) return
  uni.showModal({
    title: '清空讨论',
    content: '确定清空该直播间全部讨论？此操作不可恢复。',
    confirmText: '清空',
    confirmColor: '#ff4d4f',
    success: async (modalRes) => {
      if (!modalRes.confirm) return
      try {
        const res = await clearRoomMessages(id)
        if (res.code !== 200) {
          uni.showToast({
            title: getUserFacingErrorMessage(res, '清空失败'),
            icon: 'none'
          })
          return
        }
        uni.showToast({ title: '已清空讨论', icon: 'success' })
      } catch (e: any) {
        uni.showToast({
          title: getUserFacingErrorMessage(e, '清空失败'),
          icon: 'none'
        })
      }
    }
  })
}

function handleDeleteRoom() {
  const id = String(props.roomId || '').trim()
  if (!id) return
  uni.showModal({
    title: '删除直播间',
    content: '将删除该房间及相关内容，不可恢复。确定继续？',
    confirmText: '删除',
    confirmColor: '#ff4d4f',
    success: async (modalRes) => {
      if (!modalRes.confirm) return
      try {
        const res = await deleteRoom(id)
        if (res.code !== 200) {
          uni.showToast({
            title: getUserFacingErrorMessage(res, '删除失败'),
            icon: 'none'
          })
          return
        }
        uni.showToast({ title: '已删除', icon: 'success' })
        emit('success')
        emit('update:visible', false)
      } catch (e: any) {
        uni.showToast({
          title: getUserFacingErrorMessage(e, '删除失败'),
          icon: 'none'
        })
      }
    }
  })
}
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.dialog-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.dialog-container {
  width: 100%;
  max-height: 88vh;
  background: var(--color-bg-primary);
  border-radius: 16px 16px 0 0;
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
}

.dialog-title {
  font-size: 17px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.dialog-close {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;

  .close-icon {
    font-size: 16px;
    color: var(--color-text-secondary);
  }
}

.dialog-body {
  flex: 1;
  max-height: 62vh;
  padding: var(--spacing-lg);
  box-sizing: border-box;
}

.loading-inline {
  padding: 40px 0;
  text-align: center;

  .loading-text {
    font-size: 14px;
    color: var(--color-text-secondary);
  }
}

.form {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
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

  .label-text {
    font-size: 14px;
    color: var(--color-text-primary);
    font-weight: 500;
  }

  .label-required {
    font-size: 14px;
    color: #ff4d4f;
  }

  .danger-label {
    color: #ff4d4f;
  }
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
}

.form-textarea {
  width: 100%;
  min-height: 88px;
  padding: 8px 12px;
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

.field-hint {
  font-size: 12px;
  color: var(--color-text-tertiary);
  line-height: 1.4;
}

.switch-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 36px;
}

.switch-label {
  font-size: 14px;
  color: var(--color-text-primary);
}

.switch-track {
  width: 44px;
  height: 24px;
  border-radius: 999px;
  background: var(--color-border);
  position: relative;
  transition: background 0.2s;

  &.on {
    background: var(--color-primary);
  }
}

.switch-thumb {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #fff;
  transition: left 0.2s;

  .switch-track.on & {
    left: 22px;
  }
}

.cover-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.cover-preview {
  width: 88px;
  height: 88px;
  border-radius: var(--border-radius-base);
  overflow: hidden;
  background: var(--color-bg-secondary);
  flex-shrink: 0;
}

.cover-img {
  width: 100%;
  height: 100%;
}

.cover-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;

  .cover-text {
    font-size: 12px;
    color: var(--color-text-tertiary);
  }
}

.shortcut-row,
.cover-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.action-chip {
  height: 32px;
  padding: 0 12px;
  display: flex;
  align-items: center;
  border-radius: var(--border-radius-base);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);

  .chip-text {
    font-size: 13px;
    color: var(--color-text-primary);
  }

  &.disabled {
    opacity: 0.6;
  }

  &--warn {
    border-color: rgba(250, 173, 20, 0.5);

    .chip-text {
      color: #d48806;
    }
  }

  &--danger {
    border-color: rgba(255, 77, 79, 0.45);
    background: rgba(255, 77, 79, 0.06);

    .chip-text {
      color: #ff4d4f;
    }
  }
}

.danger-zone {
  padding-top: 8px;
  border-top: 1px dashed var(--color-border);
}

.dialog-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--spacing-md);
  padding: var(--spacing-lg);
  border-top: 1px solid var(--color-border);
}

.btn-cancel,
.btn-confirm {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 36px;
  padding: 0 20px;
  border-radius: var(--border-radius-base);

  .btn-text {
    font-size: 14px;
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
  }
}
</style>
