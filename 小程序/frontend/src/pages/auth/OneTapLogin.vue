<template>
  <view class="auth-page">
    <view class="auth-container">
      <view class="auth-main">
        <view class="auth-title">
          <text class="auth-title__h1">欢迎回来</text>
          <text class="auth-title__sub">使用本机一键登录，安全快捷</text>
        </view>

        <view class="auth-primary">
          <button class="auth-cta" :loading="submitting" :disabled="submitting" @tap="handleOneTapLogin">
            一键登录
          </button>
        </view>

        <view class="auth-secondary">
          <button class="auth-alt" :disabled="submitting" @tap="goPasswordLogin">密码登录</button>
          <button class="auth-alt" :disabled="submitting" @tap="goCodeLogin">验证码登录</button>

          <view class="auth-register-link">
            <text class="auth-link" @tap="goRegisterChoice">注册账号</text>
          </view>

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
import { ref } from 'vue'
import { AUTH_ROUTES } from '@/common/authRoutes'
import { useAuthRedirect } from '@/composables/useAuthRedirect'
import { useAuthStore } from '@/store/auth'

const authStore = useAuthStore()
const submitting = ref(false)
const errorText = ref('')
const agreedToTerms = ref(false)
const agreementHighlight = ref(false)
const { redirectQuery, finishAuth } = useAuthRedirect()

function onAgreementChange(e: { detail: { value: string[] } }) {
  agreedToTerms.value = e.detail.value.includes('agree')
  if (agreedToTerms.value) agreementHighlight.value = false
}

async function handleOneTapLogin() {
  errorText.value = ''
  if (!agreedToTerms.value) {
    agreementHighlight.value = true
    errorText.value = '请先同意服务条款和隐私政策'
    return
  }

  submitting.value = true
  try {
    const mockToken = 'mock:+8613800138000'
    const result = await authStore.oneTapLoginAction({
      carrier_token: mockToken,
      agreed_to_terms: true
    })
    if (result?.is_new_user) {
      uni.showToast({ title: '欢迎加入', icon: 'success' })
    } else {
      uni.showToast({ title: '登录成功', icon: 'success' })
    }
    setTimeout(() => finishAuth(), 400)
  } catch (e: unknown) {
    const err = e as { message?: string; code?: number }
    if (err.code === 3002) {
      agreementHighlight.value = true
      errorText.value = '请先同意服务条款和隐私政策'
    } else {
      errorText.value = err.message || '一键登录失败，请尝试其他登录方式'
    }
  } finally {
    submitting.value = false
  }
}

function goPasswordLogin() {
  uni.navigateTo({ url: `${AUTH_ROUTES.PASSWORD_LOGIN}?${redirectQuery()}` })
}

function goCodeLogin() {
  uni.navigateTo({ url: `${AUTH_ROUTES.CODE_LOGIN}?${redirectQuery()}` })
}

function goRegisterChoice() {
  uni.navigateTo({ url: AUTH_ROUTES.REGISTER_CHOICE })
}

function handleCancel() {
  uni.navigateBack()
}
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
