<template>
  <view class="register-page">
    <view class="register-container">
      <view class="register-main">
        <view class="register-title">
          <text class="register-title__h1">重置密码</text>
          <text class="register-title__sub">{{ subtitle }}</text>
        </view>

        <view class="register-form">
          <button class="register-alt register-alt--top" :disabled="submitting" @tap="toggleMode">
            {{ mode === 'email' ? '手机号重置' : '邮箱重置' }}
          </button>

          <!-- 邮箱模式 -->
          <template v-if="mode === 'email'">
            <template v-if="step === 1">
              <view class="register-field">
                <input
                  v-model="emailStep1.email"
                  class="register-input"
                  placeholder="注册邮箱"
                  maxlength="200"
                  :disabled="submitting"
                />
              </view>

              <view class="register-field register-captcha-row">
                <input
                  v-model="emailStep1.captcha_solution"
                  class="register-input register-input--captcha"
                  placeholder="图形验证码"
                  maxlength="10"
                  :disabled="submitting"
                />
                <view class="register-captcha-box" @tap="refreshCaptcha">
                  <image v-if="captchaImage" :src="captchaImage" class="register-captcha-img" mode="aspectFit" />
                  <text v-else class="register-captcha-skeleton">加载验证码</text>
                </view>
              </view>

              <button class="register-cta" :loading="submitting" :disabled="submitting" @tap="handleEmailRequestReset">
                发送重置邮件
              </button>
            </template>

            <template v-else>
              <view class="register-hint">
                <text class="register-hint__text">重置邮件已发送，请查收并输入邮件中的重置令牌</text>
              </view>

              <view class="register-field">
                <input
                  v-model="emailStep2.reset_token"
                  class="register-input"
                  placeholder="重置令牌"
                  :disabled="submitting"
                />
              </view>

              <view class="register-field">
                <input
                  v-model="emailStep2.new_password"
                  class="register-input"
                  placeholder="新密码（至少8位）"
                  :password="true"
                  maxlength="100"
                  :disabled="submitting"
                />
              </view>

              <view class="register-field">
                <input
                  v-model="emailStep2.confirm_password"
                  class="register-input"
                  placeholder="确认新密码"
                  :password="true"
                  maxlength="100"
                  :disabled="submitting"
                />
              </view>

              <button class="register-cta" :loading="submitting" :disabled="submitting" @tap="handleEmailResetPassword">
                重置密码
              </button>
            </template>
          </template>

          <!-- 短信模式 -->
          <template v-else>
            <template v-if="step === 1">
              <view class="register-field">
                <input
                  v-model="smsStep1.phone"
                  class="register-input"
                  type="number"
                  placeholder="注册手机号"
                  maxlength="11"
                  :disabled="submitting"
                />
              </view>

              <view class="register-field register-captcha-row">
                <input
                  v-model="smsStep1.captcha_solution"
                  class="register-input register-input--captcha"
                  placeholder="图形验证码"
                  maxlength="10"
                  :disabled="submitting"
                />
                <view class="register-captcha-box" @tap="refreshCaptcha">
                  <image v-if="captchaImage" :src="captchaImage" class="register-captcha-img" mode="aspectFit" />
                  <text v-else class="register-captcha-skeleton">加载验证码</text>
                </view>
              </view>

              <button class="register-cta" :loading="submitting" :disabled="submitting" @tap="handleSmsSendCode">
                发送短信验证码
              </button>
            </template>

            <template v-else>
              <view class="register-hint">
                <text class="register-hint__text">验证码已发送，请输入短信验证码与新密码</text>
              </view>

              <view class="register-field">
                <input
                  v-model="smsStep2.otp_code"
                  class="register-input"
                  placeholder="短信验证码"
                  maxlength="6"
                  :disabled="submitting"
                />
              </view>

              <view class="register-field">
                <input
                  v-model="smsStep2.new_password"
                  class="register-input"
                  placeholder="新密码（至少8位）"
                  :password="true"
                  maxlength="100"
                  :disabled="submitting"
                />
              </view>

              <view class="register-field">
                <input
                  v-model="smsStep2.confirm_password"
                  class="register-input"
                  placeholder="确认新密码"
                  :password="true"
                  maxlength="100"
                  :disabled="submitting"
                />
              </view>

              <button class="register-cta" :loading="submitting" :disabled="submitting" @tap="handleSmsResetPassword">
                重置密码
              </button>
            </template>
          </template>

          <view class="register-error-slot">
            <text v-if="errorMsg" class="register-error">{{ errorMsg }}</text>
          </view>
        </view>

        <view class="register-secondary">
          <view class="register-links">
            <text class="register-link-text">想起密码了？</text>
            <text class="register-link register-link--primary" @tap="goLogin">返回登录</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { reactive, ref, computed, onMounted } from 'vue'
import { getCaptcha, requestPasswordReset, resetPassword } from '@/api/auth'
import { AUTH_ROUTES } from '@/common/authRoutes'
import { useOtpTicket, isValidCnPhone } from '@/composables/useOtpTicket'
import { pickCaptchaFields } from '@/utils/captcha'

type ResetMode = 'email' | 'sms'

const mode = ref<ResetMode>('email')
const step = ref(1)
const submitting = ref(false)
const errorMsg = ref<string | null>(null)
const captchaId = ref('')
const captchaImage = ref('')

const { sendOtp, verifyOtp, clearCooldown, handleTicketError } = useOtpTicket()

const emailStep1 = reactive({ email: '', captcha_solution: '' })
const emailStep2 = reactive({ reset_token: '', new_password: '', confirm_password: '' })
const smsStep1 = reactive({ phone: '', captcha_solution: '' })
const smsStep2 = reactive({ otp_code: '', new_password: '', confirm_password: '' })

const subtitle = computed(() => {
  if (mode.value === 'email') {
    return step.value === 1 ? '输入注册邮箱，我们将发送重置邮件' : '输入邮件中的重置令牌与新密码'
  }
  return step.value === 1 ? '输入注册手机号，我们将发送短信验证码' : '输入短信验证码与新密码'
})

function resetState() {
  step.value = 1
  errorMsg.value = null
  clearCooldown()
  Object.assign(emailStep1, { email: '', captcha_solution: '' })
  Object.assign(emailStep2, { reset_token: '', new_password: '', confirm_password: '' })
  Object.assign(smsStep1, { phone: '', captcha_solution: '' })
  Object.assign(smsStep2, { otp_code: '', new_password: '', confirm_password: '' })
}

function toggleMode() {
  mode.value = mode.value === 'email' ? 'sms' : 'email'
  resetState()
  refreshCaptcha()
}

async function refreshCaptcha() {
  try {
    const res = await getCaptcha()
    if (res.code === 200 && res.data) {
      const picked = pickCaptchaFields(res.data)
      captchaId.value = picked.captchaId
      captchaImage.value = picked.captchaImage
      emailStep1.captcha_solution = ''
      smsStep1.captcha_solution = ''
    }
  } catch {
    errorMsg.value = '加载图形验证码失败'
  }
}

async function handleEmailRequestReset() {
  errorMsg.value = null
  if (!emailStep1.email.trim()) {
    errorMsg.value = '请输入邮箱'
    return
  }
  if (!emailStep1.captcha_solution.trim()) {
    errorMsg.value = '请输入图形验证码'
    return
  }

  submitting.value = true
  try {
    await requestPasswordReset({
      email: emailStep1.email.trim(),
      captcha_id: captchaId.value,
      captcha_solution: emailStep1.captcha_solution.trim()
    })
    uni.showToast({ title: '重置邮件已发送', icon: 'success' })
    step.value = 2
  } catch (e: unknown) {
    errorMsg.value = (e as Error)?.message || '发送失败'
    refreshCaptcha()
  } finally {
    submitting.value = false
  }
}

async function handleEmailResetPassword() {
  errorMsg.value = null
  if (!emailStep2.reset_token.trim()) {
    errorMsg.value = '请输入重置令牌'
    return
  }
  if (emailStep2.new_password.length < 8) {
    errorMsg.value = '密码至少8位'
    return
  }
  if (emailStep2.new_password !== emailStep2.confirm_password) {
    errorMsg.value = '两次密码不一致'
    return
  }

  submitting.value = true
  try {
    await resetPassword({
      reset_token: emailStep2.reset_token.trim(),
      new_password: emailStep2.new_password
    })
    uni.showToast({ title: '密码重置成功，请登录', icon: 'success' })
    setTimeout(() => uni.redirectTo({ url: AUTH_ROUTES.PASSWORD_LOGIN }), 1000)
  } catch (e: unknown) {
    errorMsg.value = (e as Error)?.message || '重置失败，请检查令牌是否正确'
  } finally {
    submitting.value = false
  }
}

async function handleSmsSendCode() {
  errorMsg.value = null
  if (!isValidCnPhone(smsStep1.phone)) {
    errorMsg.value = '请输入正确的手机号'
    return
  }
  if (!smsStep1.captcha_solution.trim()) {
    errorMsg.value = '请输入图形验证码'
    return
  }

  submitting.value = true
  try {
    await sendOtp({
      channel: 'SMS',
      recipient: smsStep1.phone.trim(),
      scenario: 'PASSWORD_RESET',
      captchaId: captchaId.value,
      captchaSolution: smsStep1.captcha_solution.trim()
    })
    uni.showToast({ title: '验证码已发送', icon: 'success' })
    step.value = 2
  } catch (e: unknown) {
    errorMsg.value = (e as Error)?.message || '发送失败'
    refreshCaptcha()
  } finally {
    submitting.value = false
  }
}

async function handleSmsResetPassword() {
  errorMsg.value = null
  if (!smsStep2.otp_code.trim()) {
    errorMsg.value = '请输入短信验证码'
    return
  }
  if (smsStep2.new_password.length < 8) {
    errorMsg.value = '密码至少8位'
    return
  }
  if (smsStep2.new_password !== smsStep2.confirm_password) {
    errorMsg.value = '两次密码不一致'
    return
  }

  submitting.value = true
  try {
    const resetTicket = await verifyOtp({
      channel: 'SMS',
      recipient: smsStep1.phone.trim(),
      scenario: 'PASSWORD_RESET',
      code: smsStep2.otp_code.trim()
    })
    await resetPassword({
      reset_ticket: resetTicket,
      new_password: smsStep2.new_password
    })
    uni.showToast({ title: '密码重置成功，请登录', icon: 'success' })
    setTimeout(() => uni.redirectTo({ url: AUTH_ROUTES.PASSWORD_LOGIN }), 1000)
  } catch (e: unknown) {
    errorMsg.value = handleTicketError(e)
  } finally {
    submitting.value = false
  }
}

function goLogin() {
  uni.navigateBack({ delta: 1, fail: () => uni.redirectTo({ url: AUTH_ROUTES.PASSWORD_LOGIN }) })
}

onMounted(() => refreshCaptcha())
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.register-page {
  min-height: 100vh;
  background: var(--color-background);
  padding-top: 14vh;
}

.register-container {
  width: 92vw;
  max-width: 420px;
  margin: 0 auto;
  padding: 0 var(--spacing-lg);
  box-sizing: border-box;
}

.register-title__h1 {
  display: block;
  font-size: 48rpx;
  font-weight: 600;
}

.register-title__sub {
  display: block;
  margin-top: var(--spacing-sm);
  font-size: 28rpx;
  color: var(--color-text-secondary);
}

.register-form {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-md);
}

.register-field {
  margin-bottom: var(--spacing-xs);
}

.register-input {
  width: 100%;
  height: 80rpx;
  padding: 0 var(--spacing-md);
  box-sizing: border-box;
  border-radius: var(--border-radius-md);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  font-size: 28rpx;
}

.register-captcha-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.register-input--captcha {
  flex: 1;
}

.register-captcha-box {
  width: 240rpx;
  height: 80rpx;
  border: 1px solid var(--color-border);
  background: var(--color-bg-tertiary);
  border-radius: var(--border-radius-2xl);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.register-captcha-img {
  width: 100%;
  height: 100%;
}

.register-captcha-skeleton {
  font-size: 24rpx;
  color: var(--color-text-secondary);
}

.register-hint {
  padding: var(--spacing-md);
  background: #f6ffed;
  border-radius: var(--border-radius-base);
  margin-bottom: var(--spacing-sm);
}

.register-hint__text {
  font-size: 26rpx;
  color: #52c41a;
  line-height: 1.5;
}

.register-cta {
  width: 100%;
  height: 88rpx;
  border: none;
  border-radius: var(--border-radius-full);
  background: var(--color-primary);
  color: var(--color-text-inverse);
  font-size: 32rpx;
  font-weight: 600;
  margin-top: var(--spacing-sm);
}

.register-alt {
  width: 100%;
  height: 88rpx;
  border: 1px solid var(--color-primary);
  border-radius: var(--border-radius-full);
  background: transparent;
  color: var(--color-primary);
  font-size: 30rpx;
  margin-bottom: var(--spacing-sm);
}

.register-secondary {
  margin-top: var(--spacing-lg);
}

.register-links {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-xs);
}

.register-link-text {
  font-size: 28rpx;
  color: var(--color-text-secondary);
}

.register-link--primary {
  font-size: 28rpx;
  color: var(--color-primary);
  font-weight: 500;
}

.register-error-slot {
  min-height: 40rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.register-error {
  color: var(--color-danger);
  font-size: 24rpx;
}
</style>
