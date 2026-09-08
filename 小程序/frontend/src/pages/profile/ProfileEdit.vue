<template>
  <view class="profile-edit-page">
    <view class="section">
      <text class="section-title">头像</text>
      <view class="avatar-row" role="button" aria-label="更换头像" @tap="handleChangeAvatar">
        <view class="avatar">
          <image
            v-if="!avatarShowIcon"
            class="avatar__img"
            :src="displayAvatar"
            mode="aspectFill"
            @error="onAvatarError"
          />
          <text v-else class="iconfont icon-yonghu avatar__placeholder" aria-hidden="true"></text>
        </view>
        <uni-icons type="right" size="18" :color="'var(--color-text-tertiary)'" />
      </view>
    </view>

    <view class="section">
      <text class="section-title">公开资料</text>

      <view class="field">
        <text class="label">昵称</text>
        <input
          v-model="form.nickname"
          class="input"
          placeholder="请输入昵称"
          :maxlength="100"
        />
      </view>

      <view class="field">
        <text class="label">简介</text>
        <textarea
          v-model="form.bio"
          class="textarea"
          placeholder="介绍一下自己（可选）"
          :maxlength="500"
        />
      </view>

    </view>

    <view class="section">
      <text class="section-title">账号</text>

      <view class="kv">
        <text class="k">注册时间</text>
        <text class="v">{{ createdAtDisplay }}</text>
      </view>
      <view v-if="me.phone" class="kv">
        <text class="k">手机号</text>
        <text class="v">{{ formatPhone(me.phone) }}</text>
      </view>
      <view v-if="me.email" class="kv">
        <text class="k">邮箱</text>
        <text class="v">{{ formatEmail(me.email) }}</text>
      </view>
    </view>

    <view class="action-bar">
      <button class="primary-btn" :disabled="submitting" @tap="handleSave">保存</button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { useAuthStore } from '@/store/auth'
import { getCurrentUser, updateMyProfile, uploadAvatar } from '@/api/user'
import { STORAGE_KEYS } from '@/common/constants'
import type { UserInfo } from '@/types/auth'
import { normalizeCanStream } from '@/types/adminUser'
import { resolveAvatarUrl, shouldMarkAvatarBroken } from '@/utils/url'
import { handleContentSafetyError, getUserFacingErrorMessage } from '@/utils/contentSafety'

const authStore = useAuthStore()

const submitting = ref(false)

const me = reactive<Partial<UserInfo>>({
  user_id: authStore.userInfo?.user_id || '',
  email: authStore.userInfo?.email || null,
  phone: authStore.userInfo?.phone || null,
  nickname: authStore.userInfo?.nickname || null,
  bio: authStore.userInfo?.bio || null,
  avatar_url: authStore.userInfo?.avatar_url || null,
  created_at: authStore.userInfo?.created_at || ''
})

const form = reactive<{ nickname: string; bio: string }>({
  nickname: '',
  bio: ''
})

const avatarBroken = ref(false)
const avatarShowIcon = ref(false)

const displayAvatar = computed(() => resolveAvatarUrl(me.avatar_url, avatarBroken.value))

function onAvatarError() {
  if (avatarShowIcon.value) return
  if (avatarBroken.value || !shouldMarkAvatarBroken(me.avatar_url, avatarBroken.value)) {
    avatarShowIcon.value = true
    return
  }
  avatarBroken.value = true
}

const createdAtDisplay = computed(() => {
  const iso = String(me.created_at || '').trim()
  if (!iso) return '--'
  try {
    const d = new Date(iso)
    if (Number.isNaN(d.getTime())) return iso
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
  } catch {
    return iso
  }
})

let lastLoadErrorMessage = ''
let lastLoadErrorAt = 0

function getProfileActionErrorMessage(action: 'load' | 'save' | 'avatar', error: any): string {
  if (error?.statusCode === 404) {
    if (action === 'avatar') return '当前环境未部署头像上传接口'
    return '当前环境未部署个人资料接口'
  }
  const fallback =
    action === 'save' ? '保存失败，请稍后再试' : action === 'avatar' ? '头像上传失败，请稍后再试' : '加载资料失败，请稍后再试'
  return getUserFacingErrorMessage(error, fallback)
}

function formatPhone(value: string | null) {
  const raw = String(value || '').trim()
  if (!raw) return ''
  if (raw.includes('*')) return raw
  const digits = raw.replace(/\s+/g, '')
  if (digits.length < 7) return raw
  return `${digits.slice(0, 3)}****${digits.slice(-4)}`
}

function formatEmail(value: string | null) {
  const raw = String(value || '').trim()
  if (!raw) return ''
  const [name, domain] = raw.split('@')
  if (!domain) return raw
  const safeName = name.length <= 2 ? name : name.slice(0, 2)
  return `${safeName}***@${domain}`
}

function goLogin(redirectUrl = '/pages/profile/ProfileEdit') {
  uni.navigateTo({ url: `/pages/auth/OneTapLogin?redirect=${encodeURIComponent(redirectUrl)}` })
}

async function fetchMe() {
  if (!authStore.isAuthenticated) {
    goLogin('/pages/profile/ProfileEdit')
    return
  }

  try {
    const resp = await getCurrentUser()
    const data = resp?.data

    if (data) {
      me.user_id = data.user_id
      me.email = data.email
      me.phone = data.phone
      me.nickname = data.nickname
      me.bio = data.bio ?? null
      me.avatar_url = data.avatar_url
      me.username = data.username
      me.role = data.role
      me.status = data.status
      me.created_at = data.created_at

      form.nickname = me.nickname || ''
      form.bio = me.bio || ''

      const merged: UserInfo = {
        user_id: data.user_id,
        username: data.username,
        email: data.email,
        phone: data.phone,
        nickname: data.nickname,
        avatar_url: data.avatar_url,
        role: data.role,
        status: data.status,
        created_at: data.created_at,
        bio: data.bio ?? null,
        can_stream: normalizeCanStream(
          (data as any)?.can_stream != null
            ? (data as any).can_stream
            : authStore.userInfo?.can_stream
        ),
        public_id: (data as any)?.public_id ?? authStore.userInfo?.public_id
      }
      authStore.userInfo = merged
      uni.setStorageSync(STORAGE_KEYS.USER_INFO, merged)
    }
  } catch (e: any) {
    const message = getProfileActionErrorMessage('load', e)
    const now = Date.now()
    if (message !== lastLoadErrorMessage || now - lastLoadErrorAt > 1500) {
      uni.showToast({ title: message, icon: 'none' })
      lastLoadErrorMessage = message
      lastLoadErrorAt = now
    }
  }
}

async function handleChangeAvatar() {
  if (!authStore.isAuthenticated) {
    goLogin('/pages/profile/ProfileEdit')
    return
  }

  const choose = await uni.chooseImage({ count: 1, sizeType: ['compressed'], sourceType: ['album', 'camera'] })
  const filePath = choose?.tempFilePaths?.[0]
  if (!filePath) return

  submitting.value = true
  try {
    const uploadResp = await uploadAvatar(filePath)
    const urlFromApi = uploadResp?.data?.avatar_url

    if (typeof urlFromApi !== 'string' || !urlFromApi.trim()) {
      throw new Error('头像上传失败：未返回可用地址')
    }

    const avatarUrl = urlFromApi.trim()
    me.avatar_url = avatarUrl

    const merged: UserInfo = {
      user_id: me.user_id || '',
      username: me.username || '',
      email: me.email || null,
      phone: me.phone || null,
      nickname: me.nickname || null,
      avatar_url: avatarUrl,
      role: me.role || 'user',
      status: me.status || 'active',
      created_at: me.created_at || new Date().toISOString()
    }
    authStore.userInfo = merged
    uni.setStorageSync(STORAGE_KEYS.USER_INFO, merged)
    uni.showToast({ title: '头像已更新', icon: 'success' })
  } catch (e: any) {
    if (handleContentSafetyError(e)) return
    uni.showToast({ title: getProfileActionErrorMessage('avatar', e), icon: 'none' })
  } finally {
    submitting.value = false
  }
}

async function handleSave() {
  if (!authStore.isAuthenticated) {
    goLogin('/pages/profile/ProfileEdit')
    return
  }

  const nickname = String(form.nickname || '').trim()
  if (!nickname) {
    uni.showToast({ title: '请填写昵称', icon: 'none' })
    return
  }
  if (nickname.length > 100) {
    uni.showToast({ title: '昵称长度不能超过100个字符', icon: 'none' })
    return
  }

  submitting.value = true
  try {
    const payload: { nickname: string; bio?: string } = { nickname }
    const bio = String(form.bio || '').trim()
    if (bio) payload.bio = bio

    const resp = await updateMyProfile(payload)
    const updated = resp?.data

    me.nickname = typeof updated?.nickname === 'string' ? updated.nickname : nickname
    if (updated?.bio !== undefined) me.bio = updated.bio

    const merged: UserInfo = {
      user_id: me.user_id || '',
      username: me.username || '',
      email: me.email || null,
      phone: me.phone || null,
      nickname: me.nickname || null,
      bio: me.bio ?? null,
      avatar_url: me.avatar_url || null,
      role: me.role || 'user',
      status: me.status || 'active',
      created_at: me.created_at || new Date().toISOString()
    }
    authStore.userInfo = merged
    uni.setStorageSync(STORAGE_KEYS.USER_INFO, merged)

    uni.showToast({ title: '已保存', icon: 'success' })
    setTimeout(() => uni.navigateBack(), 350)
  } catch (e: any) {
    if (handleContentSafetyError(e)) return
    uni.showToast({ title: getProfileActionErrorMessage('save', e), icon: 'none' })
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  fetchMe()
})

onShow(() => {
  // 返回本页时可能从登录页回来，补一次刷新
  if (authStore.isAuthenticated) fetchMe()
})
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.profile-edit-page {
  min-height: 100vh;
  background: var(--color-background);
  padding-bottom: calc(var(--spacing-lg) + constant(safe-area-inset-bottom));
  padding-bottom: calc(var(--spacing-lg) + env(safe-area-inset-bottom));
}

.section {
  background: var(--color-surface);
  border-radius: 0;
  box-shadow: none;
  padding: var(--spacing-md) var(--spacing-lg);
  border-bottom: 1px solid var(--color-border);
}

.section-title {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-sm);
}

.avatar-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.avatar {
  width: 56px;
  height: 56px;
  border-radius: 28px;
  overflow: hidden;
  background: var(--color-bg-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar__img {
  width: 100%;
  height: 100%;
}

.avatar__placeholder {
  font-size: 22px;
  color: var(--color-primary);
}

.field {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) 0;
  border-bottom: 1px solid var(--color-border);
}

.field:last-child {
  border-bottom: none;
}

.label {
  color: var(--color-text-secondary);
  font-size: 12px;
}

.input {
  height: 40px;
  line-height: 40px;
  padding: 0 var(--spacing-sm);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-md);
  background: var(--color-background);
  font-size: 14px;
  color: var(--color-text-primary);
}

.textarea {
  min-height: 72px;
  padding: var(--spacing-sm);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-md);
  background: var(--color-background);
  font-size: 14px;
  color: var(--color-text-primary);
  width: 100%;
  box-sizing: border-box;
}

.kv {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid var(--color-border);
}

.kv:last-child {
  border-bottom: none;
}

.k {
  color: var(--color-text-primary);
  font-size: 14px;
}

.v {
  color: var(--color-text-tertiary);
  font-size: 12px;
}

.action-bar {
  padding: var(--spacing-md) var(--spacing-lg);
  background: var(--color-background);
}

.primary-btn {
  height: 44px;
  line-height: 44px;
  width: 100%;
  border-radius: var(--border-radius-full);
  background: var(--color-primary);
  color: var(--color-text-inverse);
  font-size: 14px;
  font-weight: 600;
  border: none;
}

.primary-btn[disabled] {
  opacity: 0.6;
}
</style>
