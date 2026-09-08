<template>
  <view class="change-password-page">
    <view class="form-card">
      <text class="page-title">修改密码</text>
      <text class="page-desc">修改后需重新登录，建议定期更换密码</text>

      <!-- 当前密码 -->
      <view class="form-item">
        <text class="form-label">当前密码</text>
        <view class="input-wrapper">
          <input
            v-model="oldPassword"
            class="form-input"
            :class="{ 'has-eye': true }"
            placeholder="请输入当前密码"
            :password="!showOldPwd"
            :maxlength="100"
            :disabled="submitting"
          />
          <view class="eye-toggle" @tap="showOldPwd = !showOldPwd">
            <uni-icons
              :type="showOldPwd ? 'eye' : 'eye-slash'"
              size="20"
              :color="showOldPwd ? 'var(--color-primary)' : 'var(--color-text-tertiary)'"
            />
            <text class="eye-label">{{ showOldPwd ? '隐藏' : '显示' }}</text>
          </view>
        </view>
      </view>

      <!-- 新密码 -->
      <view class="form-item">
        <text class="form-label">新密码</text>
        <view class="input-wrapper">
          <input
            v-model="newPassword"
            class="form-input"
            :class="{ 'has-eye': true }"
            placeholder="至少8位，含大小写+数字+特殊符号"
            :password="!showNewPwd"
            :maxlength="100"
            :disabled="submitting"
          />
          <view class="eye-toggle" @tap="showNewPwd = !showNewPwd">
            <uni-icons
              :type="showNewPwd ? 'eye' : 'eye-slash'"
              size="20"
              :color="showNewPwd ? 'var(--color-primary)' : 'var(--color-text-tertiary)'"
            />
            <text class="eye-label">{{ showNewPwd ? '隐藏' : '显示' }}</text>
          </view>
        </view>

        <!-- 密码强度提示 -->
        <view v-if="newPassword" class="pwd-strength">
          <view :class="['strength-item', { met: checks.length }]">
            <text>8位以上</text>
          </view>
          <view :class="['strength-item', { met: checks.upper }]">
            <text>大写字母</text>
          </view>
          <view :class="['strength-item', { met: checks.lower }]">
            <text>小写字母</text>
          </view>
          <view :class="['strength-item', { met: checks.digit }]">
            <text>数字</text>
          </view>
          <view :class="['strength-item', { met: checks.special }]">
            <text>特殊符号</text>
          </view>
        </view>
      </view>

      <!-- 确认新密码 -->
      <view class="form-item">
        <text class="form-label">确认新密码</text>
        <view class="input-wrapper">
          <input
            v-model="confirmPassword"
            class="form-input"
            :class="{ 'has-eye': true }"
            placeholder="请再次输入新密码"
            :password="!showConfirmPwd"
            :maxlength="100"
            :disabled="submitting"
          />
          <view class="eye-toggle" @tap="showConfirmPwd = !showConfirmPwd">
            <uni-icons
              :type="showConfirmPwd ? 'eye' : 'eye-slash'"
              size="20"
              :color="showConfirmPwd ? 'var(--color-primary)' : 'var(--color-text-tertiary)'"
            />
            <text class="eye-label">{{ showConfirmPwd ? '隐藏' : '显示' }}</text>
          </view>
        </view>
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

      <!-- 确认按钮 -->
      <view
        class="submit-btn"
        :class="{ disabled: !canSubmit || submitting }"
        @tap="handleSubmit"
      >
        <text class="submit-text">{{ submitting ? '提交中...' : '确认修改' }}</text>
      </view>

      <!-- 错误提示 -->
      <view v-if="errorMsg" class="error-banner">
        <text class="error-text">{{ errorMsg }}</text>
      </view>

      <!-- 底部提示 -->
      <view class="footer-hint">
        <text class="hint-text">修改成功后需重新登录账户</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { useAuthStore } from '@/store/auth'
import { changeMyPassword } from '@/api/user'
import { getCaptcha } from '@/api/auth'
import { pickCaptchaFields } from '@/utils/captcha'

const authStore = useAuthStore()

const oldPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const captchaId = ref('')
const captchaImage = ref('')
const captchaSolution = ref('')
const submitting = ref(false)
const errorMsg = ref<string | null>(null)

const showOldPwd = ref(false)
const showNewPwd = ref(false)
const showConfirmPwd = ref(false)

// ========== 登录守卫 ==========

function checkAuth(): boolean {
  if (authStore.isAuthenticated) return true
  uni.navigateTo({ url: '/pages/auth/OneTapLogin?redirect=/pages/settings/ChangePassword' })
  return false
}

onShow(() => {
  if (!checkAuth()) return
})

onMounted(() => {
  if (!checkAuth()) return
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

// ========== 密码强度检查 ==========

/** 与后端 AuthService._validate_password_strength 特殊符号集对齐 */
const SPECIAL_CHAR_RE = /[!@#$%^&*(),.?":{}|<>]/

const checks = computed(() => ({
  length: newPassword.value.length >= 8,
  upper: /[A-Z]/.test(newPassword.value),
  lower: /[a-z]/.test(newPassword.value),
  digit: /\d/.test(newPassword.value),
  special: SPECIAL_CHAR_RE.test(newPassword.value)
}))

const canSubmit = computed(() => {
  return (
    oldPassword.value.length > 0 &&
    newPassword.value.length >= 8 &&
    confirmPassword.value.length >= 8 &&
    captchaSolution.value.trim().length > 0 &&
    !submitting.value
  )
})

// ========== 校验 ==========

function validate(): string | null {
  if (!oldPassword.value) return '请输入当前密码'
  if (newPassword.value.length < 8) return '新密码至少8位'
  if (!/[A-Z]/.test(newPassword.value)) return '新密码需包含大写字母'
  if (!/[a-z]/.test(newPassword.value)) return '新密码需包含小写字母'
  if (!/\d/.test(newPassword.value)) return '新密码需包含数字'
  if (!SPECIAL_CHAR_RE.test(newPassword.value)) return '新密码需包含特殊符号'
  if (newPassword.value !== confirmPassword.value) return '两次密码不一致'
  if (newPassword.value === oldPassword.value) return '新密码不能与旧密码相同'
  if (!captchaId.value || !captchaSolution.value.trim()) return '请输入图形验证码'
  return null
}

// ========== 提交 ==========

async function handleSubmit() {
  errorMsg.value = null

  if (!authStore.isAuthenticated) {
    uni.navigateTo({ url: '/pages/auth/OneTapLogin?redirect=/pages/settings/ChangePassword' })
    return
  }

  const validationError = validate()
  if (validationError) {
    errorMsg.value = validationError
    return
  }

  submitting.value = true
  try {
    await changeMyPassword({
      current_password: oldPassword.value,
      new_password: newPassword.value,
      captcha_id: captchaId.value,
      captcha_solution: captchaSolution.value.trim()
    })
    uni.showToast({ title: '密码修改成功，请重新登录', icon: 'success' })

    // 修改密码后自动登出并跳转登录页
    setTimeout(async () => {
      await authStore.logout()
      uni.reLaunch({ url: '/pages/auth/OneTapLogin' })
    }, 1500)
  } catch (e: any) {
    errorMsg.value = e?.message || '修改密码失败，请检查当前密码是否正确'
    refreshCaptcha()
  } finally {
    submitting.value = false
  }
}
</script>

<style lang="scss" scoped>
/* tokens 由 vite.config.ts css.preprocessorOptions.scss.additionalData 注入，勿再 @import uni.scss */

.change-password-page {
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

.input-wrapper {
  position: relative;
}

.form-input {
  width: 100%;
  height: 44px;
  line-height: 44px;
  padding: 0 40px 0 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-md);
  background: var(--color-background);
  font-size: 15px;
  color: var(--color-text-primary);
  box-sizing: border-box;
}

.form-input.has-eye {
  padding-right: 76px;
}

.captcha-row {
  display: flex;
  gap: 10px;
  align-items: center;
}

.captcha-input {
  flex: 1;
  padding-right: 12px;
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

.eye-toggle {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 8px 6px;
  min-width: 44px;
  min-height: 44px;
  justify-content: center;
  border-radius: var(--border-radius-sm);
  /* 增大点击区域 */
  box-sizing: border-box;
}

.eye-toggle:active {
  background: var(--color-bg-secondary);
}

.eye-label {
  font-size: 12px;
  color: var(--color-text-tertiary);
  line-height: 1;
}

// 密码强度
.pwd-strength {
  display: flex;
  gap: 8px;
  margin-top: 8px;
  flex-wrap: wrap;
}

.strength-item {
  padding: 2px 8px;
  border-radius: 4px;
  background: var(--color-bg-secondary);
  font-size: 12px;
  color: var(--color-text-tertiary);

  &.met {
    color: #52c41a;
    background: #f6ffed;
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

.footer-hint {
  margin-top: 16px;
  text-align: center;
}

.hint-text {
  font-size: 12px;
  color: var(--color-text-hint);
}
</style>
