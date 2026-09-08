<template>
  <view class="auth-page">
    <view class="auth-container">
      <view class="auth-main">
        <view class="auth-title">
          <text class="auth-title__h1">验证码登录</text>
          <text class="auth-title__sub">{{ subtitle }}</text>
        </view>

        <view class="auth-primary">
          <view class="auth-form">
            <input
              v-model="account"
              class="auth-input"
              type="text"
              placeholder="手机号 / 邮箱"
              maxlength="200"
              :disabled="submitting"
            />

            <view class="captcha-row">
              <input
                v-model="captchaSolution"
                class="auth-input captcha-input"
                placeholder="请输入图形验证码"
                maxlength="10"
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

            <view class="auth-verify-row">
              <input
                v-model="otpCode"
                class="auth-input auth-input--verify"
                type="number"
                :placeholder="otpPlaceholder"
                maxlength="6"
                :disabled="submitting"
              />
              <button
                class="auth-send-btn"
                :class="{ 'is-disabled': cooldown > 0 || submitting }"
                :disabled="cooldown > 0 || submitting"
                @tap="handleSendCode"
              >
                {{ cooldown > 0 ? `${cooldown}s` : '获取验证码' }}
              </button>
            </view>

            <button class="auth-cta" :loading="submitting" :disabled="submitting" @tap="handleLogin">
              登录
            </button>

            <view class="auth-footer-links">
              <text class="auth-link" @tap="goRegisterChoice">注册账号</text>
            </view>
          </view>
        </view>

        <view class="auth-secondary">
          <button class="auth-alt" :disabled="submitting" @tap="goOneTapLogin">一键登录</button>
          <button class="auth-alt" :disabled="submitting" @tap="goPasswordLogin">密码登录</button>
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
import { computed, onMounted, ref } from 'vue'
import { getCaptcha } from '@/api/auth'
import { AUTH_ROUTES } from '@/common/authRoutes'
import { useAuthRedirect } from '@/composables/useAuthRedirect'
import { useOtpTicket, validateLoginRecipient } from '@/composables/useOtpTicket'
import { useAuthStore } from '@/store/auth'
import { pickCaptchaFields } from '@/utils/captcha'

const authStore = useAuthStore()
const { redirectQuery, finishAuth } = useAuthRedirect()
const { cooldown, sendOtp, verifyOtp, handleTicketError } = useOtpTicket()

const account = ref('')
const captchaId = ref('')
const captchaImage = ref('')
const captchaSolution = ref('')
const otpCode = ref('')
const submitting = ref(false)
const errorText = ref('')
const agreedToTerms = ref(false)
const agreementHighlight = ref(false)

function onAgreementChange(e: { detail: { value: string[] } }) {
  agreedToTerms.value = e.detail.value.includes('agree')
  if (agreedToTerms.value) agreementHighlight.value = false
}

const detectedRecipient = computed(() => validateLoginRecipient(account.value))

const subtitle = computed(() => {
  if (detectedRecipient.value.ok) {
    return detectedRecipient.value.value.type === 'email'
      ? '验证码将发送至您的邮箱'
      : '验证码将发送至您的手机'
  }
  return '验证码将发送至您的手机或邮箱'
})

const otpPlaceholder = computed(() =>
  detectedRecipient.value.ok && detectedRecipient.value.value.type === 'email'
    ? '邮箱验证码'
    : '短信验证码'
)

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
    errorText.value = (e as Error)?.message || '加载图形验证码失败'
  }
}

function getValidatedRecipient() {
  const result = validateLoginRecipient(account.value)
  if (!result.ok) {
    errorText.value = result.message
    return null
  }
  return result.value
}

async function handleSendCode() {
  errorText.value = ''
  const recipient = getValidatedRecipient()
  if (!recipient) return

  if (!captchaId.value || !captchaSolution.value.trim()) {
    errorText.value = '请先输入图形验证码'
    return
  }

  try {
    await sendOtp({
      channel: recipient.channel,
      recipient: recipient.recipient,
      scenario: 'LOGIN',
      captchaId: captchaId.value,
      captchaSolution: captchaSolution.value.trim()
    })
    const sentTip = recipient.type === 'email' ? '验证码已发送至邮箱' : '验证码已发送至手机'
    uni.showToast({ title: sentTip, icon: 'success' })
    // 发码已消耗图形验证码，刷新供重发使用
    await refreshCaptcha()
  } catch (e: unknown) {
    errorText.value = (e as Error)?.message || '发送验证码失败'
    await refreshCaptcha()
  }
}

async function handleLogin() {
  errorText.value = ''
  const recipient = getValidatedRecipient()
  if (!recipient) return

  if (!otpCode.value || otpCode.value.length < 4) {
    errorText.value = recipient.type === 'email' ? '请输入邮箱验证码' : '请输入短信验证码'
    return
  }

  if (!agreedToTerms.value) {
    agreementHighlight.value = true
    errorText.value = '请先同意服务条款和隐私政策'
    return
  }

  submitting.value = true
  try {
    const loginTicket = await verifyOtp({
      channel: recipient.channel,
      recipient: recipient.recipient,
      scenario: 'LOGIN',
      code: otpCode.value.trim()
    })
    await authStore.loginByOtpTicket(loginTicket, recipient.channel, true)
    uni.showToast({ title: '登录成功', icon: 'success' })
    setTimeout(() => finishAuth(), 400)
  } catch (e: unknown) {
    const err = e as { message?: string; code?: number }
    if (err.code === 3002) {
      agreementHighlight.value = true
      errorText.value = '请先同意服务条款和隐私政策'
    } else {
      errorText.value = handleTicketError(e)
    }
  } finally {
    submitting.value = false
  }
}

function goOneTapLogin() {
  uni.navigateTo({ url: `${AUTH_ROUTES.ONE_TAP_LOGIN}?${redirectQuery()}` })
}

function goPasswordLogin() {
  uni.navigateTo({ url: `${AUTH_ROUTES.PASSWORD_LOGIN}?${redirectQuery()}` })
}

function goRegisterChoice() {
  uni.navigateTo({ url: AUTH_ROUTES.REGISTER_CHOICE })
}

function handleCancel() {
  uni.navigateBack()
}

onMounted(() => {
  refreshCaptcha()
})
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';
@import '@/common/auth.scss';

.auth-verify-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.auth-input--verify {
  flex: 1;
}

.auth-send-btn {
  flex-shrink: 0;
  height: 80rpx;
  padding: 0 var(--spacing-md);
  font-size: 26rpx;
  color: var(--color-primary);
  background: var(--color-primary-soft, #e8f4ff);
  border: none;
  border-radius: var(--border-radius-md);
  line-height: 80rpx;

  &.is-disabled,
  &[disabled] {
    opacity: 0.5;
    color: var(--color-text-tertiary);
  }
}

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
