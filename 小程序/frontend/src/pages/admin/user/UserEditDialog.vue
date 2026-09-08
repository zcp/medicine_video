<!--
 * UserEditDialog - 管理端用户编辑弹窗（V2.1）
 * 操作分离：禁止/恢复开播 | 禁用/恢复账号 | 设为管理员（仅超管）
 -->
<template>
  <view v-if="visible" class="dialog-overlay" @tap="handleClose">
    <view class="dialog-container" @tap.stop>
      <view class="dialog-header">
        <text class="dialog-title">编辑用户</text>
        <view class="dialog-close" @tap="handleClose">
          <text class="close-icon">✕</text>
        </view>
      </view>

      <view class="dialog-body">
        <view class="form">
          <view class="form-item">
            <view class="form-label">
              <text class="label-text">昵称</text>
            </view>
            <view class="form-control">
              <text class="readonly-text">{{ user?.nickname || '—' }}</text>
            </view>
          </view>

          <view class="form-item">
            <view class="form-label">
              <text class="label-text">UID</text>
            </view>
            <view class="form-control">
              <text class="readonly-text readonly-mono">{{ user?.public_id || '—' }}</text>
            </view>
          </view>

          <view class="form-item">
            <view class="form-label">
              <text class="label-text">邮箱</text>
            </view>
            <view class="form-control">
              <text class="readonly-text">{{ user?.email || '未设置' }}</text>
            </view>
          </view>

          <view class="form-item">
            <view class="form-label">
              <text class="label-text">手机</text>
            </view>
            <view class="form-control">
              <text class="readonly-text">{{ user?.phone_number || '未设置' }}</text>
            </view>
          </view>

          <view class="form-item">
            <view class="form-label">
              <text class="label-text">注册时间</text>
            </view>
            <view class="form-control">
              <text class="readonly-text">{{ formatCreatedAt(user?.created_at) }}</text>
            </view>
          </view>

          <view class="form-item">
            <view class="form-label">
              <text class="label-text">开播开关</text>
            </view>
            <view class="form-control switch-row" @tap="formCanStream = !formCanStream">
              <text class="switch-label">{{ formCanStream ? '允许开播' : '已禁止开播' }}</text>
              <view :class="['switch-track', formCanStream ? 'on' : '']">
                <view class="switch-thumb" />
              </view>
            </view>
            <text class="field-hint">默认可播；关闭为紧急禁止（不封号）。恢复后需对方重新登录或刷新后再开播</text>
          </view>

          <view class="form-item">
            <view class="form-label">
              <text class="label-text">账号状态</text>
            </view>
            <view class="form-control">
              <picker
                :value="statusIndex"
                :range="statusOptions"
                range-key="label"
                @change="handleStatusChange"
              >
                <view class="picker-display">
                  <text class="picker-text">{{ statusOptions[statusIndex]?.label || '请选择状态' }}</text>
                  <text class="picker-arrow">▼</text>
                </view>
              </picker>
            </view>
          </view>

          <view v-if="canEditRole" class="form-item">
            <view class="form-label">
              <text class="label-text">后台身份</text>
            </view>
            <view class="form-control">
              <picker
                :value="roleIndex"
                :range="roleOptions"
                range-key="label"
                @change="handleRoleChange"
              >
                <view class="picker-display">
                  <text class="picker-text">{{ roleOptions[roleIndex]?.label || '请选择身份' }}</text>
                  <text class="picker-arrow">▼</text>
                </view>
              </picker>
            </view>
            <text class="field-hint">仅超级管理员可任命或取消管理员</text>
          </view>

        </view>
      </view>

      <view class="dialog-footer">
        <view class="btn-cancel" @tap="handleClose">
          <text class="btn-text">取消</text>
        </view>
        <view class="btn-confirm" :class="{ 'is-loading': submitting }" @tap="handleSubmit">
          <text class="btn-text">{{ submitting ? '保存中...' : '保存' }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { adminUpdateUser } from '@/api/user'
import type { AdminUserResponse, AdminUserRole, AdminEntityStatus, AdminUserUpdatePayload } from '@/types/adminUser'
import {
  ADMIN_USER_ROLE_LABEL,
  ADMIN_USER_STATUS_LABEL,
  canChangeUserRole,
  getDailyStatusOptions,
  getEditableRoleOptions,
  normalizeAdminUserRole,
  normalizeAdminEntityStatus,
  normalizeCanStream
} from '@/types/adminUser'
const props = defineProps<{
  visible: boolean
  user: AdminUserResponse | null
  operatorRole?: string | null
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  success: []
}>()

const submitting = ref(false)
const formRole = ref<AdminUserRole>('REGULAR')
const formStatus = ref<AdminEntityStatus>('NORMAL')
const formCanStream = ref(false)
const initialRole = ref<AdminUserRole>('REGULAR')
const initialStatus = ref<AdminEntityStatus>('NORMAL')
const initialCanStream = ref(false)

function formatCreatedAt(iso?: string | null): string {
  if (!iso) return '—'
  try {
    const d = new Date(iso)
    if (Number.isNaN(d.getTime())) return iso
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
  } catch {
    return iso
  }
}

const canEditRole = computed(() => canChangeUserRole(props.operatorRole))

const roleOptions = computed(() =>
  getEditableRoleOptions(props.operatorRole).map((value) => ({
    label: ADMIN_USER_ROLE_LABEL[value],
    value
  }))
)

const statusOptions = computed(() =>
  getDailyStatusOptions().map((value) => ({
    label: ADMIN_USER_STATUS_LABEL[value],
    value
  }))
)

const roleIndex = computed(() =>
  Math.max(0, roleOptions.value.findIndex((item) => item.value === formRole.value))
)

const statusIndex = computed(() =>
  Math.max(0, statusOptions.value.findIndex((item) => item.value === formStatus.value))
)

watch(
  () => [props.visible, props.user] as const,
  ([visible, user]) => {
    if (!visible || !user) return
    formRole.value = normalizeAdminUserRole(user.role)
    formStatus.value = normalizeAdminEntityStatus(user.status)
    formCanStream.value = normalizeCanStream(user.can_stream)
    initialRole.value = formRole.value
    initialStatus.value = formStatus.value
    initialCanStream.value = formCanStream.value
  },
  { immediate: true }
)

function handleClose() {
  emit('update:visible', false)
}

function handleRoleChange(e: any) {
  const index = Number(e.detail.value)
  formRole.value = roleOptions.value[index]?.value || 'REGULAR'
}

function handleStatusChange(e: any) {
  const index = Number(e.detail.value)
  formStatus.value = statusOptions.value[index]?.value || 'NORMAL'
}

function buildPayload(): AdminUserUpdatePayload | null {
  const payload: AdminUserUpdatePayload = {}
  if (formStatus.value !== initialStatus.value) {
    payload.status = formStatus.value
  }
  if (formCanStream.value !== initialCanStream.value) {
    payload.can_stream = formCanStream.value
  }
  if (canEditRole.value && formRole.value !== initialRole.value) {
    payload.role = formRole.value
  }
  if (Object.keys(payload).length === 0) return null
  return payload
}

async function doSubmit(payload: AdminUserUpdatePayload) {
  if (!props.user) return
  submitting.value = true
  try {
    await adminUpdateUser(props.user.public_id, payload)
    if (payload.can_stream === true) {
      uni.showToast({
        title: '已恢复开播，请对方退出并重新登录（或刷新）后再开播',
        icon: 'none',
        duration: 3200
      })
    } else if (payload.can_stream === false) {
      uni.showToast({ title: '已禁止开播', icon: 'none' })
    } else {
      uni.showToast({ title: '保存成功', icon: 'success' })
    }
    emit('success')
    handleClose()
  } catch (err: any) {
    uni.showToast({ title: err.message || '更新失败', icon: 'none' })
  } finally {
    submitting.value = false
  }
}

async function handleSubmit() {
  if (!props.user) return
  const payload = buildPayload()
  if (!payload) {
    uni.showToast({ title: '未修改任何内容', icon: 'none' })
    return
  }

  const roleChanged = payload.role !== undefined
  if (roleChanged) {
    uni.showModal({
      title: '确认修改后台身份',
      content: `将「${props.user.nickname || props.user.username}」设为「${ADMIN_USER_ROLE_LABEL[payload.role!]}」？`,
      success: (res) => {
        if (res.confirm) void doSubmit(payload)
      }
    })
    return
  }

  await doSubmit(payload)
}

</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: var(--spacing-lg);
  box-sizing: border-box;
}

.dialog-container {
  width: 100%;
  max-width: 520px;
  background: var(--color-bg-primary);
  border-radius: var(--border-radius-lg);
  overflow: hidden;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--color-border);
}

.dialog-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.dialog-close {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-icon {
  font-size: 16px;
  color: var(--color-text-secondary);
}

.dialog-body {
  padding: var(--spacing-lg);
}

.form-item {
  margin-bottom: var(--spacing-md);
}

.form-label {
  margin-bottom: var(--spacing-xs);
}

.label-text {
  font-size: 14px;
  color: var(--color-text-primary);
  font-weight: 500;
}

.readonly-text {
  font-size: 14px;
  color: var(--color-text-secondary);
  word-break: break-all;
}

.readonly-mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 12px;
}

.field-hint {
  display: block;
  margin-top: 6px;
  font-size: 12px;
  color: var(--color-text-tertiary, var(--color-text-secondary));
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
  border-radius: 12px;
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
  transition: transform 0.2s;
}

.switch-track.on .switch-thumb {
  transform: translateX(20px);
}

.picker-display {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 36px;
  padding: 0 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-base);
  background-color: var(--color-bg-primary);
}

.picker-text {
  font-size: 14px;
  color: var(--color-text-primary);
}

.picker-arrow {
  font-size: 10px;
  color: var(--color-text-secondary);
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
}

.btn-cancel {
  background-color: var(--color-bg-secondary);

  .btn-text {
    font-size: 14px;
    color: var(--color-text-primary);
  }
}

.btn-confirm {
  background-color: var(--color-primary);

  .btn-text {
    font-size: 14px;
    color: #fff;
  }

  &.is-loading {
    opacity: 0.7;
  }
}
</style>
