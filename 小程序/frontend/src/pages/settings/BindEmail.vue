<template>
  <view class="bind-email-page">
    <view class="form-card">
      <text class="page-title">{{ isReplace ? '更换邮箱' : '绑定邮箱' }}</text>
      <text class="page-desc">
        {{ isReplace ? '更换后可使用新邮箱登录和找回密码' : '绑定邮箱后可用于登录和找回密码' }}
      </text>

      <!-- 邮箱 -->
      <view class="form-item">
        <text class="form-label">邮箱地址</text>
        <input
          v-model="email"
          class="form-input"
          placeholder="请输入邮箱地址"
          type="text"
          :maxlength="200"
          :disabled="submitting"
        />
      </view>

      <!-- 图形验证码 -->
      <view class="form-item">
        <text class="form-label">图形验证码</text>
        <view class="captcha-row">
          <input
            v-model="captchaSolution"
            class="form-input captcha-input"
            placeholder="请输入图形验证码"
            maxlength="10"
            :disabled="submitting"
          />
          <view class="captcha-box" @tap="refreshCaptcha">
            <image v-if="captchaImage" class="captcha-img" :src="captchaImage" mode="aspectFit" />
            <text v-else class="captcha-skeleton">加载中</text>
          </view>
        </view>
      </view>

      <!-- 验证码 -->
      <view class="form-item">
        <text class="form-label">邮箱验证码</text>
        <view class="code-row">
          <input
            v-model="code"
            class="form-input code-input"
            placeholder="请输入6位验证码"
            type="number"
            :maxlength="6"
            :disabled="submitting"
          />
          <button
            class="send-code-btn"
            :class="{ disabled: cooldown > 0 || !email || submitting }"
            :disabled="cooldown > 0 || !email || submitting"
            @tap="handleSendCode"
          >
            {{ cooldown > 0 ? `${cooldown}s` : '获取验证码' }}
          </button>
        </view>
      </view>

      <!-- 确认按钮 -->
      <view
        class="submit-btn"
        :class="{ disabled: !canSubmit || submitting }"
        @tap="handleSubmit"
      >
        <text class="submit-text">{{ submitting ? '提交中...' : '确认' }}</text>
      </view>

      <!-- 错误提示 -->
      <view v-if="errorMsg" class="error-banner">
        <text class="error-text">{{ errorMsg }}</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { useAuthStore } from '@/store/auth'
import { getMyProfile, updateMyEmail } from '@/api/user'
import { sendVerificationCode, getCaptcha } from '@/api/auth'
import { pickCaptchaFields } from '@/utils/captcha'
import { STORAGE_KEYS } from '@/common/constants'
import type { UserInfo } from '@/types/auth'

const authStore = useAuthStore()

const email = ref('')
const code = ref('')
const captchaId = ref('')
const captchaImage = ref('')
const captchaSolution = ref('')
const cooldown = ref(0)
const submitting = ref(false)
const errorMsg = ref<string | null>(null)
let cooldownTimer: ReturnType<typeof setInterval> | null = null

/** 是否为更换邮箱（已有绑定） */
const isReplace = computed(() => {
  return !!authStore.userInfo?.email
})

const canSubmit = computed(() => {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value) && code.value.length === 6 && !submitting.value
})

// ========== 登录守卫 ==========

function checkAuth(): boolean {
  if (authStore.isAuthenticated) return true
  uni.navigateTo({ url: '/pages/auth/OneTapLogin?redirect=/pages/settings/BindEmail' })
  return false
}

// ========== 生命周期 ==========

onShow(() => {
  if (!checkAuth()) return
})

onMounted(() => {
  if (!checkAuth()) return
  if (authStore.userInfo?.email) {
    email.value = authStore.userInfo.email
  }
  refreshCaptcha()
})

async function refreshCaptcha() {
  try {
    const res = await getCaptcha()
    if (res.code === 200 && res.data) {
      const picked = pickCaptchaFields(res.data)
      captchaId.value = picked.captchaId
      captchaImage.value = picked.captchaImage
      captchaSolution.value = ''
    }
  } catch {
    errorMsg.value = '加载图形验证码失败'
  }
}

// ========== 发送验证码 ==========

async function handleSendCode() {
  errorMsg.value = null

  if (!email.value) {
    errorMsg.value = '请输入邮箱地址'
    return
  }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value)) {
    errorMsg.value = '请输入正确的邮箱地址'
    return
  }
  if (!captchaId.value || !captchaSolution.value.trim()) {
    errorMsg.value = '请先输入图形验证码'
    return
  }

  try {
    await sendVerificationCode({
      channel: 'EMAIL',
      recipient: email.value,
      scenario: 'BIND_EMAIL',
      captcha_id: captchaId.value,
      captcha_solution: captchaSolution.value.trim()
    })
    uni.showToast({ title: '验证码已发送', icon: 'success' })
    startCooldown()
  } catch (e: any) {
    errorMsg.value = e?.message || '发送验证码失败，请稍后重试'
    refreshCaptcha()
  }
}

function startCooldown() {
  cooldown.value = 60
  cooldownTimer = setInterval(() => {
    cooldown.value--
    if (cooldown.value <= 0 && cooldownTimer) {
      clearInterval(cooldownTimer)
      cooldownTimer = null
    }
  }, 1000)
}

// ========== 提交绑定 ==========

async function handleSubmit() {
  errorMsg.value = null

  if (!email.value) {
    errorMsg.value = '请输入邮箱地址'
    return
  }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value)) {
    errorMsg.value = '请输入正确的邮箱地址'
    return
  }
  if (!code.value || code.value.length !== 6) {
    errorMsg.value = '请输入6位邮箱验证码'
    return
  }

  submitting.value = true
  try {
    await updateMyEmail({ email: email.value, verification_code: code.value })
    uni.showToast({ title: isReplace.value ? '邮箱更换成功' : '邮箱绑定成功', icon: 'success' })

    // 刷新用户信息
    const resp = await getMyProfile()
    if (resp?.data) {
      const merged: UserInfo = {
        ...(authStore.userInfo || { user_id: '', username: '', role: 'user', status: 'active', created_at: '' }),
        ...resp.data
      }
      authStore.userInfo = merged
      uni.setStorageSync(STORAGE_KEYS.USER_INFO, merged)
    }

    setTimeout(() => uni.navigateBack(), 500)
  } catch (e: any) {
    errorMsg.value = e?.message || (isReplace.value ? '更换失败' : '绑定失败')
  } finally {
    submitting.value = false
  }
}
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.bind-email-page {
  min-height: 100vh;
  background: var(--color-background);
  padding: var(--spacing-lg);
}

.form-card {
  background: var(--color-surface);
  border-radius: var(--border-radius-lg);
  padding: var(--spacing-xl);
}

.page-title {
  display: block;
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
  text-align: center;
  margin-bottom: 8px;
}

.page-desc {
  display: block;
  font-size: 13px;
  color: var(--color-text-tertiary);
  text-align: center;
  margin-bottom: 24px;
}

.form-item {
  margin-bottom: 16px;
}

.form-label {
  display: block;
  font-size: 14px;
  color: var(--color-text-secondary);
  margin-bottom: 6px;
}

.form-input {
  width: 100%;
  height: 44px;
  line-height: 44px;
  padding: 0 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-md);
  background: var(--color-background);
  font-size: 15px;
  color: var(--color-text-primary);
  box-sizing: border-box;
}

.captcha-row {
  display: flex;
  gap: 10px;
  align-items: center;
}

.captcha-input {
  flex: 1;
}

.captcha-box {
  width: 120px;
  height: 44px;
  flex-shrink: 0;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-md);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-tertiary);
}

.captcha-img {
  width: 100%;
  height: 100%;
}

.captcha-skeleton {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.code-row {
  display: flex;
  gap: 10px;
}

.code-input {
  flex: 1;
}

.send-code-btn {
  flex-shrink: 0;
  height: 44px;
  line-height: 44px;
  padding: 0 16px;
  font-size: 14px;
  color: var(--color-primary);
  background: var(--color-primary-soft);
  border: none;
  border-radius: var(--border-radius-md);
  white-space: nowrap;

  &.disabled,
  &[disabled] {
    opacity: 0.5;
    color: var(--color-text-tertiary);
  }
}

.submit-btn {
  margin-top: 24px;
  height: 46px;
  line-height: 46px;
  background: var(--color-primary);
  border-radius: var(--border-radius-full);
  text-align: center;

  &.disabled {
    opacity: 0.5;
  }

  &:active {
    opacity: 0.8;
  }
}

.submit-text {
  color: var(--color-text-inverse, #fff);
  font-size: 16px;
  font-weight: 500;
}

.error-banner {
  margin-top: 12px;
  padding: 10px 14px;
  background: #fff2f0;
  border-radius: var(--border-radius-sm);
}

.error-text {
  font-size: 13px;
  color: var(--color-error, #e74c3c);
}
</style>
