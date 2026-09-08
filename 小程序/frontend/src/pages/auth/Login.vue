<template>
  <view class="auth-page">
    <view class="auth-container">
      <view class="auth-main">
        <view class="auth-title">
          <text class="auth-title__h1">密码登录</text>
          <text class="auth-title__sub">可使用手机号或邮箱登录</text>
        </view>

        <view class="auth-primary">
          <view class="auth-form">
            <input
              v-model="username"
              class="auth-input"
              placeholder="手机号 / 邮箱"
              :disabled="submitting"
            />

            <view class="auth-password-row">
              <input
                v-model="password"
                class="auth-input auth-input--password"
                placeholder="请输入密码"
                :password="!showPassword"
                :disabled="submitting"
              />
              <text class="auth-link" @tap="showPassword = !showPassword">
                {{ showPassword ? '隐藏' : '显示' }}
              </text>
            </view>

            <view class="captcha-row">
              <input
                v-model="captchaSolution"
                class="auth-input captcha-input"
                placeholder="请输入图形验证码"
                :disabled="submitting"
              />
              <view class="captcha-box" @tap="refreshCaptcha">
                <image
                  v-if="captchaImage"
                  class="captcha-img"
                  :src="captchaImage"
                  mode="aspectFit"
                />
                <text v-else class="captcha-skeleton">加载验证码</text>
              </view>
            </view>

            <button
              class="auth-cta"
              :loading="submitting"
              :disabled="submitting"
              @tap="handlePasswordLogin"
            >
              登录
            </button>

            <view class="auth-footer-links">
              <text class="auth-link auth-link--primary" @tap="goForgotPassword">忘记密码</text>
              <text class="auth-link" @tap="goRegisterChoice">注册账号</text>
            </view>
          </view>
        </view>

        <view class="auth-secondary">
          <button class="auth-alt" :disabled="submitting" @tap="goOneTapLogin">一键登录</button>
          <button class="auth-alt" :disabled="submitting" @tap="goCodeLogin">验证码登录</button>
          <button class="auth-cancel" :disabled="submitting" @tap="handleCancel">暂不登录</button>

          <view class="auth-error-slot">
            <text v-if="errorText" class="auth-error">{{ errorText }}</text>
          </view>
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
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/store/auth'
import { getCaptcha } from '@/api/auth'
import { AUTH_ROUTES } from '@/common/authRoutes'
import { useAuthRedirect } from '@/composables/useAuthRedirect'
import { pickCaptchaFields } from '@/utils/captcha'
import { isValidCnPhone } from '@/composables/useOtpTicket'
import { REGEX_PATTERNS } from '@/utils/validator'

const authStore = useAuthStore()
const submitting = ref(false)
const errorText = ref('')
const agreedToTerms = ref(false)
const agreementHighlight = ref(false)
const { redirectQuery, finishAuth } = useAuthRedirect()

const username = ref('')
const password = ref('')
const showPassword = ref(false)
const captchaId = ref('')
const captchaImage = ref('')
const captchaSolution = ref('')

function onAgreementChange(e: { detail: { value: string[] } }) {
  agreedToTerms.value = e.detail.value.includes('agree')
  if (agreedToTerms.value) agreementHighlight.value = false
}

async function refreshCaptcha() {
  try {
    const res = await getCaptcha()
    if (res.code === 200 && res.data) {
      const picked = pickCaptchaFields(res.data)
      captchaId.value = picked.captchaId
      captchaImage.value = picked.captchaImage
      captchaSolution.value = ''
    } else {
      throw new Error(res.message || '获取验证码失败')
    }
  } catch (e: unknown) {
    captchaId.value = ''
    captchaImage.value = ''
    captchaSolution.value = ''
    errorText.value = (e as Error)?.message || '获取验证码失败'
  }
}

/** 提交前账号格式预检：含 @ 按邮箱校验，否则按手机号校验 */
function validateAccount(account: string): string | null {
  if (!account) return '请输入账号和密码'
  if (account.includes('@')) {
    if (!REGEX_PATTERNS.EMAIL.test(account)) {
      return '邮箱输入不完整，请输入完整邮箱（需包含@及域名）'
    }
    return null
  }
  if (/^\d+$/.test(account) || account.startsWith('1')) {
    if (!isValidCnPhone(account)) {
      return '请输入正确的11位手机号'
    }
    return null
  }
  // 不再引导用户名登录
  return '请使用手机号或邮箱登录'
}

async function handlePasswordLogin() {
  errorText.value = ''
  const user = username.value.trim()
  const pass = password.value

  if (!user || !pass) {
    errorText.value = '请输入账号和密码'
    return
  }

  const accountErr = validateAccount(user)
  if (accountErr) {
    errorText.value = accountErr
    return
  }

  if (!captchaId.value || !captchaSolution.value.trim()) {
    errorText.value = '请输入图形验证码'
    return
  }

  if (!agreedToTerms.value) {
    agreementHighlight.value = true
    errorText.value = '请先同意服务条款和隐私政策'
    return
  }

  submitting.value = true
  try {
    await authStore.passwordLogin({
      username: user,
      password: pass,
      captcha_id: captchaId.value,
      captcha_solution: captchaSolution.value.trim(),
      agreed_to_terms: true
    })
    uni.showToast({ title: '登录成功', icon: 'success' })
    setTimeout(() => finishAuth(), 300)
  } catch (e: unknown) {
    const err = e as { message?: string; code?: number }
    if (err.code === 3002) {
      agreementHighlight.value = true
      errorText.value = '请先同意服务条款和隐私政策'
    } else {
      errorText.value = err.message || '登录失败'
    }
    await refreshCaptcha()
  } finally {
    submitting.value = false
  }
}

function goOneTapLogin() {
  uni.navigateTo({ url: `${AUTH_ROUTES.ONE_TAP_LOGIN}?${redirectQuery()}` })
}

function goCodeLogin() {
  uni.navigateTo({ url: `${AUTH_ROUTES.CODE_LOGIN}?${redirectQuery()}` })
}

function goRegisterChoice() {
  uni.navigateTo({ url: AUTH_ROUTES.REGISTER_CHOICE })
}

function goForgotPassword() {
  uni.navigateTo({ url: AUTH_ROUTES.FORGOT_PASSWORD })
}

function handleCancel() {
  uni.navigateBack()
}

onMounted(() => refreshCaptcha())
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';
@import '@/common/auth.scss';

.auth-agreement__label {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-xs);
}

.auth-agreement--highlight {
  padding: var(--spacing-xs);
  border-radius: var(--border-radius-sm);
  background: #fff7e6;
}
</style>
