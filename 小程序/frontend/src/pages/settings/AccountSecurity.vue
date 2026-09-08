<template>
  <view class="account-security-page">
    <!-- 加载态 -->
    <view v-if="loading" class="loading-state">
      <text class="loading-text">加载中...</text>
    </view>

    <!-- 错误态 -->
    <view v-else-if="errorMsg" class="error-state">
      <text class="error-text">{{ errorMsg }}</text>
      <view class="retry-btn" @tap="retryLoad">
        <text class="retry-text">重试</text>
      </view>
    </view>

    <!-- 内容区 -->
    <template v-else>
      <!-- ===== 个人信息（与 Profile 英雄区一致） ===== -->
      <view class="hero" @tap="goEditProfile">
        <view class="hero__row">
          <view class="hero__avatar">
            <image
              v-if="!avatarShowIcon"
              class="hero__avatar-img"
              :src="displayAvatar"
              mode="aspectFill"
              @error="onAvatarError"
            />
            <text v-else class="iconfont icon-yonghu"></text>
          </view>
          <view class="hero__info">
            <text class="hero__title">{{ displayName }}</text>
            <text class="hero__sub">UUID：{{ uuidDisplay }}</text>
          </view>
          <view class="hero__action">
            <text class="hero__action-text">编辑</text>
            <uni-icons type="right" size="16" color="var(--color-text-tertiary)" />
          </view>
        </view>
      </view>

      <!-- ===== 账号绑定 ===== -->
      <view class="section">
        <text class="section-title">账号绑定</text>

        <view class="field-row field-row--readonly">
          <view class="field-left">
            <uni-icons type="person" size="20" color="var(--color-text-secondary)" />
            <view class="field-info">
              <text class="field-label">UUID</text>
              <text class="field-value">{{ uuidDisplay }}</text>
            </view>
          </view>
        </view>

        <view class="field-row field-row--readonly">
          <view class="field-left">
            <uni-icons type="contact" size="20" color="var(--color-text-secondary)" />
            <view class="field-info">
              <text class="field-label">用户名</text>
              <text class="field-value">{{ usernameDisplay }}</text>
            </view>
          </view>
        </view>

        <view class="field-row field-row--readonly">
          <view class="field-left">
            <uni-icons type="calendar" size="20" color="var(--color-text-secondary)" />
            <view class="field-info">
              <text class="field-label">注册时间</text>
              <text class="field-value">{{ createdAtDisplay }}</text>
            </view>
          </view>
        </view>

        <!-- 邮箱 → 跳转 BindEmail -->
        <view class="field-row" @tap="goBindEmail">
          <view class="field-left">
            <uni-icons type="email" size="20" color="var(--color-text-secondary)" />
            <view class="field-info">
              <text class="field-label">邮箱</text>
              <text class="field-value">{{ emailDisplay }}</text>
            </view>
          </view>
          <view class="field-right">
            <text class="field-action-tag">{{ me.email ? '更换' : '绑定' }}</text>
            <uni-icons type="right" size="16" color="var(--color-text-tertiary)" />
          </view>
        </view>

        <!-- 手机号 → 跳转 BindPhone -->
        <view class="field-row" @tap="goBindPhone">
          <view class="field-left">
            <uni-icons type="phone" size="20" color="var(--color-text-secondary)" />
            <view class="field-info">
              <text class="field-label">手机号</text>
              <text class="field-value">{{ phoneDisplay }}</text>
            </view>
          </view>
          <view class="field-right">
            <text class="field-action-tag">{{ me.phone ? '更换' : '绑定' }}</text>
            <uni-icons type="right" size="16" color="var(--color-text-tertiary)" />
          </view>
        </view>
      </view>

      <!-- ===== 安全设置 ===== -->
      <view class="section">
        <text class="section-title">安全设置</text>

        <!-- 修改密码 → 跳转 ChangePassword -->
        <view class="field-row" @tap="goChangePassword">
          <view class="field-left">
            <uni-icons type="locked" size="20" color="var(--color-text-secondary)" />
            <view class="field-info">
              <text class="field-label">修改密码</text>
              <text class="field-value">需图形验证码确认</text>
            </view>
          </view>
          <view class="field-right">
            <uni-icons type="right" size="16" color="var(--color-text-tertiary)" />
          </view>
        </view>

        <view class="field-row" @tap="onPrivacyPolicy">
          <view class="field-left">
            <uni-icons type="info" size="20" color="var(--color-text-secondary)" />
            <view class="field-info">
              <text class="field-label">隐私政策</text>
              <text class="field-value">开发中</text>
            </view>
          </view>
          <view class="field-right">
            <text class="field-action-tag">开发中</text>
            <uni-icons type="right" size="16" color="var(--color-text-tertiary)" />
          </view>
        </view>
      </view>

      <!-- ===== 危险操作 ===== -->
      <view class="section section--danger">
        <text class="section-title">危险操作</text>

        <view class="field-row" @tap="handleDeleteAccount">
          <view class="field-left">
            <uni-icons type="trash" size="20" color="var(--color-error)" />
            <view class="field-info">
              <text class="field-label" style="color: var(--color-error)">注销账号</text>
              <text class="field-value">注销后账号数据将无法恢复，请谨慎操作</text>
            </view>
          </view>
          <view class="field-right">
            <uni-icons type="right" size="16" color="var(--color-text-tertiary)" />
          </view>
        </view>
      </view>
    </template>

    <!-- 注销确认层：图形验证码（样式对齐 Login.vue / auth.scss） -->
    <view v-if="showDeactivateModal" class="deactivate-mask" @tap="closeDeactivateModal">
      <view class="deactivate-panel" @tap.stop>
        <text class="deactivate-title">确认注销账号</text>
        <text class="deactivate-desc">请输入图形验证码以确认注销，此操作不可恢复</text>

        <view class="captcha-row">
          <input
            v-model="deactivateCaptchaSolution"
            class="deactivate-input captcha-input"
            placeholder="图形验证码"
            maxlength="10"
            :disabled="submitting"
          />
          <view class="captcha-box" @tap="refreshDeactivateCaptcha">
            <image
              v-if="deactivateCaptchaImage"
              class="captcha-img"
              :src="deactivateCaptchaImage"
              mode="aspectFit"
            />
            <text v-else class="captcha-skeleton">加载验证码</text>
          </view>
        </view>

        <text v-if="deactivateError" class="deactivate-error">{{ deactivateError }}</text>

        <view class="deactivate-actions">
          <button class="deactivate-btn deactivate-btn--cancel" :disabled="submitting" @tap="closeDeactivateModal">
            取消
          </button>
          <button
            class="deactivate-btn deactivate-btn--confirm"
            :loading="submitting"
            :disabled="submitting"
            @tap="confirmDeactivateAccount"
          >
            确认注销
          </button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { useAuthStore } from '@/store/auth'
import { getMyProfile, deleteMyAccount } from '@/api/user'
import { getCaptcha } from '@/api/auth'
import { pickCaptchaFields } from '@/utils/captcha'
import { STORAGE_KEYS } from '@/common/constants'
import type { UserInfo } from '@/types/auth'
import { resolveAvatarUrl, shouldMarkAvatarBroken } from '@/utils/url'

const authStore = useAuthStore()
const ACCOUNT_SECURITY_PATH = '/pages/settings/AccountSecurity'
/** 防止 onShow / 多入口并发跳登录导致 navigateTo timeout */
let loginRedirecting = false

const loading = ref(false)
const errorMsg = ref<string | null>(null)
const submitting = ref(false)
const showDeactivateModal = ref(false)
const deactivateCaptchaId = ref('')
const deactivateCaptchaImage = ref('')
const deactivateCaptchaSolution = ref('')
const deactivateError = ref('')

async function refreshDeactivateCaptcha() {
  try {
    const res = await getCaptcha()
    if (res.code === 200 && res.data) {
      const { captchaId, captchaImage } = pickCaptchaFields(res.data)
      deactivateCaptchaId.value = captchaId
      deactivateCaptchaImage.value = captchaImage
      deactivateCaptchaSolution.value = ''
      deactivateError.value = ''
    } else {
      throw new Error(res.message || '获取验证码失败')
    }
  } catch (e: any) {
    deactivateCaptchaId.value = ''
    deactivateCaptchaImage.value = ''
    deactivateError.value = e?.message || '获取验证码失败'
  }
}

function closeDeactivateModal() {
  if (submitting.value) return
  showDeactivateModal.value = false
  deactivateError.value = ''
  deactivateCaptchaSolution.value = ''
}

function openDeactivateModal() {
  showDeactivateModal.value = true
  deactivateError.value = ''
  refreshDeactivateCaptcha()
}

const me = reactive<Partial<UserInfo>>({
  user_id: '',
  public_id: undefined,
  username: '',
  email: null,
  phone: null,
  nickname: null,
  avatar_url: null,
  created_at: ''
})

// ========== 计算属性 ==========

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

const displayName = computed(() => {
  const nick = String(me.nickname || '').trim()
  return nick || '已登录用户'
})

const uuidDisplay = computed(() => {
  const uid = String(me.public_id || me.user_id || '').trim()
  return uid || '--'
})

const usernameDisplay = computed(() => {
  const name = String(me.username || '').trim()
  return name || '--'
})

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

function onPrivacyPolicy() {
  uni.showToast({ title: '隐私政策开发中', icon: 'none' })
}

const emailDisplay = computed(() => {
  const email = me.email
  if (!email) return '未绑定'
  const [name, domain] = email.split('@')
  if (!domain) return email
  const maskedName = name.length <= 2 ? name : name.slice(0, 2) + '***'
  return `${maskedName}@${domain}`
})

const phoneDisplay = computed(() => {
  const phone = me.phone
  if (!phone) return '未绑定'
  const digits = phone.replace(/\s+/g, '')
  if (digits.length < 7) return phone
  return `${digits.slice(0, 3)}****${digits.slice(-4)}`
})

// ========== 数据加载 ==========

function goLogin(redirectUrl = ACCOUNT_SECURITY_PATH) {
  if (loginRedirecting) return
  loginRedirecting = true
  const url = `/pages/auth/OneTapLogin?redirect=${encodeURIComponent(redirectUrl)}`
  // redirectTo：避免账号页留在栈底，返回时再次 onShow 连环跳转
  uni.redirectTo({
    url,
    fail: () => {
      uni.navigateTo({
        url,
        fail: () => {
          loginRedirecting = false
          uni.showToast({ title: '请先登录', icon: 'none' })
        }
      })
    }
  })
}

async function fetchMe() {
  if (!authStore.isAuthenticated) return
  loading.value = true
  errorMsg.value = null
  try {
    const resp = await getMyProfile()
    const data = resp?.data
    if (data) {
      Object.assign(me, {
        user_id: data.user_id,
        public_id: data.public_id,
        username: data.username,
        email: data.email,
        phone: data.phone,
        nickname: data.nickname,
        avatar_url: data.avatar_url,
        created_at: data.created_at
      })
      // 同步到 store
      const merged: UserInfo = {
        ...(authStore.userInfo || { role: 'user', status: 'active', created_at: data.created_at }),
        ...data
      }
      authStore.userInfo = merged
      uni.setStorageSync(STORAGE_KEYS.USER_INFO, merged)
    }
  } catch {
    errorMsg.value = '加载用户信息失败，请重试'
  } finally {
    loading.value = false
  }
}

function retryLoad() {
  fetchMe()
}

/** 检查登录状态，未登录则跳转登录页 */
function requireLogin(redirectUrl: string): boolean {
  if (authStore.isAuthenticated) return true
  goLogin(redirectUrl)
  return false
}

// ========== 页面导航（含登录守卫） ==========

function goEditProfile() {
  if (!requireLogin('/pages/settings/AccountSecurity')) return
  uni.navigateTo({ url: '/pages/profile/ProfileEdit' })
}

function goBindPhone() {
  if (!requireLogin('/pages/settings/AccountSecurity')) return
  uni.navigateTo({ url: '/pages/settings/BindPhone' })
}

function goBindEmail() {
  if (!requireLogin('/pages/settings/AccountSecurity')) return
  uni.navigateTo({ url: '/pages/settings/BindEmail' })
}

function goChangePassword() {
  if (!requireLogin('/pages/settings/AccountSecurity')) return
  uni.navigateTo({ url: '/pages/settings/ChangePassword' })
}

// ========== 注销账号 ==========

function handleDeleteAccount() {
  if (!authStore.isAuthenticated) {
    goLogin()
    return
  }
  uni.showModal({
    title: '注销账号',
    content: '确定要注销账号吗？注销后所有数据将无法恢复，此操作不可逆！',
    confirmText: '继续',
    confirmColor: '#e74c3c',
    cancelText: '取消',
    success: (res) => {
      if (res.confirm) openDeactivateModal()
    }
  })
}

async function confirmDeactivateAccount() {
  deactivateError.value = ''
  if (!deactivateCaptchaId.value || !deactivateCaptchaSolution.value.trim()) {
    deactivateError.value = '请输入图形验证码'
    return
  }

  submitting.value = true
  try {
    await deleteMyAccount({
      captcha_id: deactivateCaptchaId.value,
      captcha_solution: deactivateCaptchaSolution.value.trim()
    })
    showDeactivateModal.value = false
    uni.showToast({ title: '账号已注销', icon: 'success' })
    setTimeout(async () => {
      await authStore.logout()
      uni.reLaunch({ url: '/pages/home/Home' })
    }, 1500)
  } catch (e: any) {
    const code = e?.data?.code ?? e?.code
    if (code === 4003) {
      deactivateError.value = '图形验证码错误或已过期'
      await refreshDeactivateCaptcha()
    } else if (code === 2002) {
      deactivateError.value = '账户存在活跃订阅，无法注销'
    } else {
      deactivateError.value = e?.message || '注销失败，请稍后重试'
    }
  } finally {
    submitting.value = false
  }
}

/** 页面显示时检查登录并按需拉资料（单一入口，避免与 onMounted 双跳） */
onShow(() => {
  if (!authStore.isAuthenticated) {
    goLogin()
    return
  }
  loginRedirecting = false
  // 若已有数据不再重复请求，避免每次 onShow 都 loading
  if (!me.user_id) {
    fetchMe()
  }
})
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.account-security-page {
  min-height: 100vh;
  background: var(--color-background);
  padding-bottom: calc(var(--spacing-lg) + constant(safe-area-inset-bottom));
  padding-bottom: calc(var(--spacing-lg) + env(safe-area-inset-bottom));
}

// ===== 加载/错误态 =====
.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
}

.loading-text,
.error-text {
  font-size: 14px;
  color: var(--color-text-secondary);
}

.retry-btn {
  margin-top: 16px;
  padding: 8px 24px;
  background: var(--color-primary);
  border-radius: var(--border-radius-base);
}

.retry-text {
  color: #fff;
  font-size: 14px;
}

// ===== 个人信息英雄区（与 Profile 一致） =====
.hero {
  background: linear-gradient(90deg, var(--color-primary-soft), var(--color-bg-secondary));
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--color-border);

  &:active {
    opacity: 0.88;
  }
}

.hero__row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.hero__avatar {
  width: 48px;
  height: 48px;
  border-radius: 24px;
  background: var(--color-bg-secondary);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.hero__avatar-img {
  width: 100%;
  height: 100%;
}

.hero__avatar .iconfont {
  font-size: 22px;
  color: var(--color-primary);
}

.hero__info {
  flex: 1;
  min-width: 0;
}

.hero__title {
  display: block;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.hero__sub {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: var(--color-text-secondary);
}

.hero__action {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 4px;
}

.hero__action-text {
  font-size: 13px;
  color: var(--color-text-secondary);
}

// ===== Section 通用 =====
.section {
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  padding: var(--spacing-md) var(--spacing-lg);
}

.section--danger {
  margin-top: var(--spacing-md);
}

.section-title {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-sm);
}

// ===== 字段行 =====
.field-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 0;
  border-bottom: 1px solid var(--color-border);

  &:last-child {
    border-bottom: none;
  }

  &:active {
    background: var(--color-bg-secondary);
  }

  &--readonly:active {
    background: transparent;
  }
}

.field-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.field-info {
  flex: 1;
  min-width: 0;
}

.field-label {
  display: block;
  font-size: 15px;
  color: var(--color-text-primary);
  font-weight: 500;
}

.field-value {
  display: block;
  font-size: 12px;
  color: var(--color-text-tertiary);
  margin-top: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.field-right {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.field-action-tag {
  font-size: 13px;
  color: var(--color-primary);
  font-weight: 500;
}

.field-hint {
  font-size: 12px;
  color: var(--color-text-hint);
}

// ===== 注销验证码层（对齐 auth.scss captcha tokens） =====
.deactivate-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: var(--spacing-lg);
  box-sizing: border-box;
}

.deactivate-panel {
  width: 100%;
  max-width: 420px;
  background: var(--color-surface);
  border-radius: var(--border-radius-lg);
  padding: var(--spacing-xl);
  box-sizing: border-box;
}

.deactivate-title {
  display: block;
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
  text-align: center;
}

.deactivate-desc {
  display: block;
  margin-top: 8px;
  font-size: 13px;
  color: var(--color-text-secondary);
  text-align: center;
  line-height: 1.5;
}

.captcha-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  margin-top: var(--spacing-lg);
}

.deactivate-input {
  flex: 1;
  height: 44px;
  padding: 0 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-md);
  background: var(--color-background);
  font-size: 15px;
  box-sizing: border-box;
}

.captcha-box {
  width: 120px;
  height: 44px;
  border: 1px solid var(--color-border);
  background: var(--color-bg-tertiary);
  border-radius: var(--border-radius-md);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.captcha-img {
  width: 100%;
  height: 100%;
}

.captcha-skeleton {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.deactivate-error {
  display: block;
  margin-top: 10px;
  font-size: 13px;
  color: var(--color-error, #e74c3c);
  text-align: center;
}

.deactivate-actions {
  display: flex;
  gap: 12px;
  margin-top: var(--spacing-lg);
}

.deactivate-btn {
  flex: 1;
  height: 44px;
  line-height: 44px;
  border-radius: var(--border-radius-full);
  font-size: 15px;
  font-weight: 500;
  border: none;

  &--cancel {
    background: var(--color-bg-secondary);
    color: var(--color-text-primary);
  }

  &--confirm {
    background: #e74c3c;
    color: #fff;
  }

  &[disabled] {
    opacity: 0.6;
  }
}
</style>
