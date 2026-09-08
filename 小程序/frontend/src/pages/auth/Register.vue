<template>
  <view v-if="mode" class="register-page">
    <view class="register-container">
      <view class="register-top">
        <text class="register-top__kicker">注册</text>
      </view>

      <view class="register-main">
        <view class="register-title">
          <text class="register-title__h1">创建账号</text>
          <text class="register-title__sub">
            {{ mode === 'phone' ? '使用手机号快速注册' : '使用邮箱注册' }}
          </text>
        </view>

        <view class="register-form">
          <!-- ===== 手机注册（默认） ===== -->
          <template v-if="mode === 'phone'">
            <view class="register-field">
              <input
                v-model="phoneForm.phone"
                class="register-input"
                type="number"
                placeholder="手机号"
                maxlength="11"
                :disabled="submitting"
              />
            </view>

            <view class="register-field">
              <input
                v-model="phoneForm.nickname"
                class="register-input"
                placeholder="昵称（1-50字符）"
                maxlength="50"
                :disabled="submitting"
              />
            </view>

            <view class="register-field register-captcha-row">
              <input
                v-model="phoneForm.captcha_solution"
                class="register-input register-input--captcha"
                placeholder="图形验证码"
                maxlength="10"
                :disabled="submitting"
              />
              <view class="register-captcha-box" @tap="refreshCaptcha">
                <image
                  v-if="captchaImage"
                  :src="captchaImage"
                  class="register-captcha-img"
                  mode="aspectFit"
                />
                <text v-else class="register-captcha-skeleton">加载验证码</text>
              </view>
            </view>

            <view class="register-field register-verify-row">
              <input
                v-model="phoneForm.otp_code"
                class="register-input register-input--verify"
                placeholder="短信验证码"
                maxlength="6"
                :disabled="submitting"
              />
              <view
                class="register-send-btn"
                :class="{ 'is-disabled': cooldown > 0 || submitting }"
                @tap="handlePhoneSendCode"
              >
                <text class="register-send-text">{{ cooldown > 0 ? `${cooldown}s` : '发送验证码' }}</text>
              </view>
            </view>

            <view class="register-field register-password-row">
              <input
                v-model="phoneForm.password"
                class="register-input register-input--password"
                placeholder="密码（8位+大小写+数字+特殊符号）"
                :password="!showPassword"
                maxlength="100"
                :disabled="submitting"
              />
              <text class="register-link" @tap="showPassword = !showPassword">
                {{ showPassword ? '隐藏' : '显示' }}
              </text>
            </view>

            <view v-if="phoneForm.password" class="register-strength">
              <view :class="['register-strength-item', { met: phonePasswordChecks.length }]"><text>8位以上</text></view>
              <view :class="['register-strength-item', { met: phonePasswordChecks.upper }]"><text>大写字母</text></view>
              <view :class="['register-strength-item', { met: phonePasswordChecks.lower }]"><text>小写字母</text></view>
              <view :class="['register-strength-item', { met: phonePasswordChecks.digit }]"><text>数字</text></view>
              <view :class="['register-strength-item', { met: phonePasswordChecks.special }]"><text>特殊符号</text></view>
            </view>

            <view class="register-field register-password-row">
              <input
                v-model="phoneForm.confirmPassword"
                class="register-input register-input--password"
                placeholder="确认密码"
                :password="!showConfirmPassword"
                maxlength="100"
                :disabled="submitting"
              />
              <text class="register-link" @tap="showConfirmPassword = !showConfirmPassword">
                {{ showConfirmPassword ? '隐藏' : '显示' }}
              </text>
            </view>

            <button class="register-cta" :loading="submitting" :disabled="submitting" @tap="handlePhoneRegister">
              {{ submitting ? '注册中...' : '注册' }}
            </button>
          </template>

          <!-- ===== 邮箱注册 ===== -->
          <template v-else-if="mode === 'email'">
            <view class="register-field">
              <input
                v-model="emailForm.email"
                class="register-input"
                placeholder="邮箱地址"
                maxlength="200"
                :disabled="submitting"
              />
            </view>

            <view class="register-field">
              <input
                v-model="emailForm.nickname"
                class="register-input"
                placeholder="昵称（1-100字符）"
                maxlength="100"
                :disabled="submitting"
              />
            </view>

            <view class="register-field register-captcha-row">
              <input
                v-model="emailForm.captcha_solution"
                class="register-input register-input--captcha"
                placeholder="图形验证码"
                maxlength="10"
                :disabled="submitting"
              />
              <view class="register-captcha-box" @tap="refreshCaptcha">
                <image
                  v-if="captchaImage"
                  :src="captchaImage"
                  class="register-captcha-img"
                  mode="aspectFit"
                />
                <text v-else class="register-captcha-skeleton">加载验证码</text>
              </view>
            </view>

            <view class="register-field register-verify-row">
              <input
                v-model="emailForm.verification_code"
                class="register-input register-input--verify"
                placeholder="邮箱验证码"
                maxlength="6"
                :disabled="submitting"
              />
              <view
                class="register-send-btn"
                :class="{ 'is-disabled': cooldown > 0 || submitting }"
                @tap="handleEmailSendCode"
              >
                <text class="register-send-text">{{ cooldown > 0 ? `${cooldown}s` : '发送验证码' }}</text>
              </view>
            </view>

            <view class="register-field register-password-row">
              <input
                v-model="emailForm.password"
                class="register-input register-input--password"
                placeholder="密码（8位+大小写+数字+特殊符号）"
                :password="!showPassword"
                maxlength="100"
                :disabled="submitting"
              />
              <text class="register-link" @tap="showPassword = !showPassword">
                {{ showPassword ? '隐藏' : '显示' }}
              </text>
            </view>

            <view v-if="emailForm.password" class="register-strength">
              <view :class="['register-strength-item', { met: emailPasswordChecks.length }]"><text>8位以上</text></view>
              <view :class="['register-strength-item', { met: emailPasswordChecks.upper }]"><text>大写字母</text></view>
              <view :class="['register-strength-item', { met: emailPasswordChecks.lower }]"><text>小写字母</text></view>
              <view :class="['register-strength-item', { met: emailPasswordChecks.digit }]"><text>数字</text></view>
              <view :class="['register-strength-item', { met: emailPasswordChecks.special }]"><text>特殊符号</text></view>
            </view>

            <view class="register-field register-password-row">
              <input
                v-model="emailForm.confirmPassword"
                class="register-input register-input--password"
                placeholder="确认密码"
                :password="!showConfirmPassword"
                maxlength="100"
                :disabled="submitting"
              />
              <text class="register-link" @tap="showConfirmPassword = !showConfirmPassword">
                {{ showConfirmPassword ? '隐藏' : '显示' }}
              </text>
            </view>

            <button class="register-cta" :loading="submitting" :disabled="submitting" @tap="handleEmailRegister">
              {{ submitting ? '注册中...' : '注册' }}
            </button>
          </template>

          <view class="register-secondary">
            <view class="register-links">
              <text class="register-link register-link--primary" @tap="goRegisterChoice">切换注册方式</text>
            </view>
            <view class="register-links">
              <text class="register-link-text">已有账号？</text>
              <text class="register-link register-link--primary" @tap="goLogin">去登录</text>
            </view>
          </view>

          <view v-if="errorMsg" class="register-error-slot">
            <text class="register-error">{{ errorMsg }}</text>
          </view>

          <view class="auth-agreement" :class="{ 'auth-agreement--highlight': agreementHighlight }">
            <checkbox-group @change="onAgreementChange">
              <label class="auth-agreement__label">
                <checkbox value="agree" :checked="agreedToTerms" color="var(--color-primary)" />
                <text class="auth-agreement__text">我已阅读并同意《用户协议》与《隐私政策》</text>
              </label>
            </checkbox-group>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { getCaptcha, register } from '@/api/auth'
import { useOtpTicket, isValidCnPhone, validateStrongPassword } from '@/composables/useOtpTicket'
import { useAuthRedirect } from '@/composables/useAuthRedirect'
import { useAuthStore } from '@/store/auth'
import { AUTH_ROUTES } from '@/common/authRoutes'
import type { RegisterRequest } from '@/types/auth'
import { pickCaptchaFields } from '@/utils/captcha'
import { REGEX_PATTERNS } from '@/utils/validator'

type RegisterMode = 'phone' | 'email'

const authStore = useAuthStore()
const { finishAuth } = useAuthRedirect()
const { cooldown, sendOtp, verifyOtp, clearCooldown, handleTicketError } = useOtpTicket()

const mode = ref<RegisterMode | null>(null)
const submitting = ref(false)
const errorMsg = ref<string | null>(null)
const captchaId = ref('')
const captchaImage = ref('')
const showPassword = ref(false)
const showConfirmPassword = ref(false)
const agreedToTerms = ref(false)
const agreementHighlight = ref(false)

function onAgreementChange(e: { detail: { value: string[] } }) {
  agreedToTerms.value = e.detail.value.includes('agree')
  if (agreedToTerms.value) agreementHighlight.value = false
}

const phoneForm = reactive({
  phone: '',
  nickname: '',
  captcha_solution: '',
  otp_code: '',
  password: '',
  confirmPassword: ''
})

const emailForm = reactive({
  email: '',
  nickname: '',
  captcha_solution: '',
  verification_code: '',
  password: '',
  confirmPassword: ''
})

/** 与手机注册后端一致：u_{10位十六进制}，满足现网必填 username */
function generateUsername(): string {
  const hex = `${Date.now().toString(16)}${Math.random().toString(16).slice(2)}`.replace(/\./g, '')
  return `u_${hex.slice(0, 10)}`
}

const SPECIAL_CHAR_RE = /[!@#$%^&*(),.?":{}|<>]/

const phonePasswordChecks = computed(() => ({
  length: phoneForm.password.length >= 8,
  upper: /[A-Z]/.test(phoneForm.password),
  lower: /[a-z]/.test(phoneForm.password),
  digit: /\d/.test(phoneForm.password),
  special: SPECIAL_CHAR_RE.test(phoneForm.password)
}))

const emailPasswordChecks = computed(() => ({
  length: emailForm.password.length >= 8,
  upper: /[A-Z]/.test(emailForm.password),
  lower: /[a-z]/.test(emailForm.password),
  digit: /\d/.test(emailForm.password),
  special: SPECIAL_CHAR_RE.test(emailForm.password)
}))

function resetForms() {
  Object.assign(phoneForm, {
    phone: '', nickname: '', captcha_solution: '', otp_code: '', password: '', confirmPassword: ''
  })
  Object.assign(emailForm, {
    email: '', nickname: '', captcha_solution: '', verification_code: '', password: '', confirmPassword: ''
  })
  errorMsg.value = null
  clearCooldown()
}

onLoad((options?: { mode?: string }) => {
  const m = options?.mode
  if (m === 'phone' || m === 'email') {
    mode.value = m
    uni.setNavigationBarTitle({ title: m === 'phone' ? '手机号注册' : '邮箱注册' })
    resetForms()
    refreshCaptcha()
    return
  }
  uni.redirectTo({ url: AUTH_ROUTES.REGISTER_CHOICE })
})

async function refreshCaptcha() {
  try {
    const res = await getCaptcha()
    if (res.code === 200 && res.data) {
      const picked = pickCaptchaFields(res.data)
      captchaId.value = picked.captchaId
      captchaImage.value = picked.captchaImage
      phoneForm.captcha_solution = ''
      emailForm.captcha_solution = ''
    }
  } catch {
    errorMsg.value = '加载图形验证码失败'
  }
}

async function handlePhoneSendCode() {
  errorMsg.value = null
  if (!isValidCnPhone(phoneForm.phone)) {
    errorMsg.value = '请输入正确的手机号'
    return
  }
  if (!phoneForm.captcha_solution.trim()) {
    errorMsg.value = '请先输入图形验证码'
    return
  }
  try {
    await sendOtp({
      channel: 'SMS',
      recipient: phoneForm.phone.trim(),
      scenario: 'REGISTER',
      captchaId: captchaId.value,
      captchaSolution: phoneForm.captcha_solution.trim()
    })
    uni.showToast({ title: '验证码已发送', icon: 'success' })
  } catch (e: unknown) {
    errorMsg.value = (e as Error)?.message || '发送验证码失败'
    refreshCaptcha()
  }
}

async function handlePhoneRegister() {
  errorMsg.value = null
  if (!isValidCnPhone(phoneForm.phone)) {
    errorMsg.value = '请输入正确的手机号'
    return
  }
  if (!phoneForm.nickname.trim() || phoneForm.nickname.length > 50) {
    errorMsg.value = '昵称需1-50个字符'
    return
  }
  if (!phoneForm.otp_code.trim()) {
    errorMsg.value = '请输入短信验证码'
    return
  }
  const pwdErr = validateStrongPassword(phoneForm.password)
  if (pwdErr) {
    errorMsg.value = pwdErr
    return
  }
  if (phoneForm.password !== phoneForm.confirmPassword) {
    errorMsg.value = '两次密码不一致'
    return
  }

  if (!agreedToTerms.value) {
    agreementHighlight.value = true
    errorMsg.value = '请先同意服务条款和隐私政策'
    return
  }

  submitting.value = true
  try {
    const registerTicket = await verifyOtp({
      channel: 'SMS',
      recipient: phoneForm.phone.trim(),
      scenario: 'REGISTER',
      code: phoneForm.otp_code.trim()
    })
    const result = await authStore.registerByPhoneTicket({
      register_ticket: registerTicket,
      password: phoneForm.password,
      nickname: phoneForm.nickname.trim(),
      agreed_to_terms: true
    })
    if (result?.is_new_user) {
      uni.showToast({ title: '注册成功', icon: 'success' })
    } else {
      uni.showToast({ title: '注册成功', icon: 'success' })
    }
    setTimeout(() => finishAuth(), 500)
  } catch (e: unknown) {
    const err = e as { message?: string; code?: number }
    if (err.code === 3002) {
      agreementHighlight.value = true
      errorMsg.value = '请先同意服务条款和隐私政策'
    } else {
      errorMsg.value = handleTicketError(e)
    }
  } finally {
    submitting.value = false
  }
}

async function handleEmailSendCode() {
  errorMsg.value = null
  const email = emailForm.email.trim()
  if (!email) {
    errorMsg.value = '请先输入邮箱'
    return
  }
  if (!REGEX_PATTERNS.EMAIL.test(email)) {
    errorMsg.value = '请输入完整有效的邮箱地址（需包含@及域名）'
    return
  }
  if (!emailForm.captcha_solution.trim()) {
    errorMsg.value = '请先输入图形验证码'
    return
  }
  try {
    await sendOtp({
      channel: 'EMAIL',
      recipient: email,
      scenario: 'REGISTER',
      captchaId: captchaId.value,
      captchaSolution: emailForm.captcha_solution.trim()
    })
    uni.showToast({ title: '验证码已发送', icon: 'success' })
    // 发码已消耗图形验证码；现网注册接口仍需 captcha，刷新供提交使用
    refreshCaptcha()
  } catch (err: unknown) {
    errorMsg.value = (err as Error)?.message || '发送验证码失败'
    refreshCaptcha()
  }
}

async function handleEmailRegister() {
  errorMsg.value = null
  if (!emailForm.nickname.trim() || emailForm.nickname.length > 100) {
    errorMsg.value = '昵称需1-100个字符'
    return
  }
  if (!emailForm.email.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailForm.email)) {
    errorMsg.value = '请输入有效的邮箱地址'
    return
  }
  if (!emailForm.captcha_solution.trim() || !captchaId.value) {
    errorMsg.value = '请先输入图形验证码'
    return
  }
  if (!emailForm.verification_code.trim()) {
    errorMsg.value = '请输入邮箱验证码'
    return
  }
  const pwdErr = validateStrongPassword(emailForm.password)
  if (pwdErr) {
    errorMsg.value = pwdErr
    return
  }
  if (emailForm.password !== emailForm.confirmPassword) {
    errorMsg.value = '两次密码不一致'
    return
  }

  if (!agreedToTerms.value) {
    agreementHighlight.value = true
    errorMsg.value = '请先同意服务条款和隐私政策'
    return
  }

  submitting.value = true
  try {
    const data: RegisterRequest = {
      username: generateUsername(),
      email: emailForm.email.trim(),
      nickname: emailForm.nickname.trim(),
      password: emailForm.password,
      verification_code: emailForm.verification_code.trim(),
      captcha_id: captchaId.value,
      captcha_solution: emailForm.captcha_solution.trim(),
      agreed_to_terms: true
    }
    await register(data)
    uni.showToast({ title: '注册成功，请登录', icon: 'success' })
    setTimeout(() => {
      uni.redirectTo({ url: AUTH_ROUTES.ONE_TAP_LOGIN })
    }, 1000)
  } catch (err: unknown) {
    const e = err as { message?: string; code?: number }
    if (e.code === 3002) {
      agreementHighlight.value = true
      errorMsg.value = '请先同意服务条款和隐私政策'
    } else {
      errorMsg.value = e.message || '注册失败'
    }
    refreshCaptcha()
  } finally {
    submitting.value = false
  }
}

function goLogin() {
  uni.navigateBack({ delta: 1, fail: () => uni.redirectTo({ url: AUTH_ROUTES.ONE_TAP_LOGIN }) })
}

function goRegisterChoice() {
  uni.redirectTo({ url: AUTH_ROUTES.REGISTER_CHOICE })
}
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.register-page {
  min-height: 100vh;
  background: var(--color-background);
  color: var(--color-text-primary);
  padding-top: 14vh;
}

@media (min-width: 900px) {
  .register-page {
    padding-top: 20vh;
  }
}

.register-container {
  width: 92vw;
  max-width: 420px;
  margin: 0 auto;
  padding: 0 var(--spacing-lg);
  box-sizing: border-box;
}

.register-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 44px;
  margin-bottom: var(--spacing-md);
}

.register-top__kicker {
  font-size: 14px;
  color: var(--color-text-secondary);
}

.register-main {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.register-title__h1 {
  display: block;
  font-size: 48rpx;
  font-weight: 600;
  line-height: 1.2;
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
  margin-top: var(--spacing-sm);
}

.register-field {
  position: relative;
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

.register-password-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.register-input--password {
  flex: 1;
}

.register-link {
  color: var(--color-text-secondary);
  font-size: 26rpx;
  flex-shrink: 0;
}

.register-captcha-row,
.register-verify-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.register-input--captcha,
.register-input--verify {
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

.register-send-btn {
  height: 80rpx;
  padding: 0 var(--spacing-md);
  background: var(--color-primary);
  border-radius: var(--border-radius-md);
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;

  &.is-disabled {
    opacity: 0.5;
  }
}

.register-send-text {
  color: #fff;
  font-size: 26rpx;
  font-weight: 500;
  white-space: nowrap;
}

.register-strength {
  display: flex;
  gap: var(--spacing-xs);
  flex-wrap: wrap;
}

.register-strength-item {
  padding: 4rpx 12rpx;
  border-radius: var(--border-radius-sm);
  background: var(--color-bg-secondary);
  font-size: 22rpx;
  color: var(--color-text-hint);

  &.met {
    color: #52c41a;
    background: #f6ffed;
  }
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
  margin-top: var(--spacing-sm);
  border: 1px solid var(--color-primary);
  border-radius: var(--border-radius-full);
  background: transparent;
  color: var(--color-primary);
  font-size: 30rpx;
  font-weight: 500;
}

.register-secondary {
  margin-top: var(--spacing-md);
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

.auth-agreement {
  margin-top: var(--spacing-md);
}

.auth-agreement__label {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-xs);
}

.auth-agreement__text {
  font-size: 24rpx;
  color: var(--color-text-secondary);
  line-height: 1.5;
}

.auth-agreement--highlight {
  padding: var(--spacing-xs);
  border-radius: var(--border-radius-sm);
  background: #fff7e6;
}
</style>
