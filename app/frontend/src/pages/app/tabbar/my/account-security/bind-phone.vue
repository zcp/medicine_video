<template>
  <view class="bind-phone-page">
    <view class="auth-container">
      <view class="auth-main">
        <view class="auth-title">
          <text class="title-main">{{ isRebind ? '更换手机号' : '绑定手机号' }}</text>
          <text class="title-subtitle">{{ isRebind ? '绑定新手机号后，原手机号将解除绑定' : '绑定手机号后可通过手机号登录账号' }}</text>
        </view>

        <view class="auth-form">
          <!-- 手机号输入 -->
          <view class="form-group" :class="{ 'form-group--error': errors.phone_number }">
            <text class="field-label">手机号</text>
            <view class="input-wrapper">
              <text class="country-code">+86</text>
              <input
                v-model="form.phone_number"
                class="form-input phone-input"
                type="number"
                placeholder="请输入手机号"
                maxlength="11"
                @input="handlePhoneInput"
                @blur="validatePhone"
              />
            </view>
            <text v-if="errors.phone_number" class="error-text">{{ errors.phone_number }}</text>
          </view>

          <!-- 图形验证码 -->
          <view class="form-group" :class="{ 'form-group--error': errors.captcha }">
            <text class="field-label">图形验证码</text>
            <view class="captcha-row">
              <input
                v-model="form.captcha_solution"
                class="form-input captcha-input"
                type="text"
                placeholder="请输入图形验证码"
                maxlength="8"
                @input="clearFieldError('captcha')"
              />
              <view class="captcha-image" @click="refreshCaptcha">
                <image
                  v-if="captchaUrl"
                  :src="captchaUrl"
                  class="captcha-img"
                  mode="aspectFit"
                />
                <view v-else class="captcha-loading">
                  <text class="loading-text">加载中</text>
                </view>
              </view>
            </view>
            <text v-if="errors.captcha" class="error-text">{{ errors.captcha }}</text>
          </view>

          <!-- 短信验证码 -->
          <view class="form-group" :class="{ 'form-group--error': errors.verification_code }">
            <text class="field-label">短信验证码</text>
            <view class="sms-row">
              <input
                v-model="form.verification_code"
                class="form-input sms-input"
                type="number"
                placeholder="请输入短信验证码"
                maxlength="6"
                @input="clearFieldError('verification_code')"
              />
              <view
                class="sms-btn"
                :class="{ disabled: countdown > 0 || sendingOtp }"
                @click="handleSendOtp"
              >
                <text v-if="countdown > 0">{{ countdown }}s 后重发</text>
                <text v-else-if="sendingOtp">发送中...</text>
                <text v-else>发送验证码</text>
              </view>
            </view>
            <text v-if="errors.verification_code" class="error-text">{{ errors.verification_code }}</text>
          </view>

          <button
            class="auth-primary-btn"
            :class="{ disabled: submitting }"
            :disabled="submitting"
            @click="handleSubmit"
          >
            <text v-if="submitting">提交中...</text>
            <text v-else>{{ isRebind ? '确认换绑' : '确认绑定' }}</text>
          </button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted, onUnmounted } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import { useAuthStore } from '@/store/auth';
import { getCaptcha, sendVerificationCode, verifyCode, bindPhone } from '@/api/auth';
import { isValidCnPhone, normalizeCnPhone } from '@/utils/phone';

const authStore = useAuthStore();

const isRebind = computed(() => !!authStore.user?.phone_number);

const form = reactive({
  phone_number: '',
  captcha_solution: '',
  verification_code: ''
});

const errors = reactive({
  phone_number: '',
  captcha: '',
  verification_code: ''
});

const captchaUrl = ref('');
const captchaId = ref('');
const countdown = ref(0);
const sendingOtp = ref(false);
const submitting = ref(false);
let countdownTimer: number | null = null;

function clearFieldError(key: 'phone_number' | 'captcha' | 'verification_code') {
  errors[key] = '';
}

onShow(() => {
  if (!authStore.isAuthenticated) {
    uni.showToast({ title: '请先登录', icon: 'none' });
    uni.navigateBack({
      fail: () => { uni.switchTab({ url: '/pages/app/tabbar/home/index' }); }
    });
  }
});

onMounted(() => {
  loadCaptcha();
});

onUnmounted(() => {
  if (countdownTimer) clearInterval(countdownTimer);
});

async function loadCaptcha() {
  try {
    const res = await getCaptcha();
    captchaId.value = res.data.captcha_id;
    captchaUrl.value = res.data.image_base64;
  } catch {
    uni.showToast({ title: '验证码加载失败，请点击图片重试', icon: 'none' });
  }
}

function refreshCaptcha() {
  form.captcha_solution = '';
  errors.captcha = '';
  captchaUrl.value = '';
  loadCaptcha();
}

/** 输入时实时校验：归一化长度 >= 11（视为输入完成）或已失焦过才提示 */
const phoneTouched = ref(false);
function validatePhoneLive(val: string): void {
  if (!val) {
    if (phoneTouched.value) errors.phone_number = '请输入手机号';
    return;
  }
  if (normalizeCnPhone(val).length >= 11 || phoneTouched.value) {
    errors.phone_number = isValidCnPhone(val) ? '' : '请输入正确的手机号格式';
  }
}
watch(() => form.phone_number, (val) => validatePhoneLive(val));

/** @input 兜底：直接读输入事件值触发校验（不依赖 v-model 更新时序，兼容 type="number" 平台差异） */
function handlePhoneInput(e: any): void {
  validatePhoneLive(e?.detail?.value ?? e?.target?.value ?? '');
}

function validatePhone(): boolean {
  phoneTouched.value = true;
  const phone = form.phone_number.trim();
  if (!phone) {
    errors.phone_number = '请输入手机号';
    return false;
  }
  if (!isValidCnPhone(phone)) {
    errors.phone_number = '请输入正确的手机号格式';
    return false;
  }
  return true;
}

async function handleSendOtp() {
  if (countdown.value > 0 || sendingOtp.value) return;
  if (!validatePhone()) return;
  if (!form.captcha_solution.trim()) {
    errors.captcha = '请输入图形验证码';
    return;
  }
  if (!captchaId.value) {
    uni.showToast({ title: '验证码未加载，请点击图片刷新', icon: 'none' });
    return;
  }

  sendingOtp.value = true;
  try {
    await sendVerificationCode({
      channel: 'SMS',
      recipient: normalizeCnPhone(form.phone_number.trim()),
      scenario: 'BIND_PHONE',
      captcha_id: captchaId.value,
      captcha_solution: form.captcha_solution.trim()
    });
    uni.showToast({ title: '验证码已发送', icon: 'success' });
    startCountdown();
    refreshCaptcha();
  } catch (e: any) {
    const code = e?.code ?? e?.data?.code;
    const msg = e?.message || '';
    if (code === 3002 || code === 4003 || /验证码/.test(msg)) {
      errors.captcha = '图形验证码错误或已过期';
      refreshCaptcha();
    } else if (code === 409 || /已绑定|已存在/.test(msg)) {
      errors.phone_number = '该手机号已被其他账号绑定';
    } else {
      uni.showToast({ title: e?.message || '发送失败，请稍后重试', icon: 'none' });
    }
  } finally {
    sendingOtp.value = false;
  }
}

function startCountdown() {
  countdown.value = 60;
  countdownTimer = setInterval(() => {
    countdown.value--;
    if (countdown.value <= 0) {
      clearInterval(countdownTimer!);
      countdownTimer = null;
    }
  }, 1000) as unknown as number;
}

async function handleSubmit() {
  if (submitting.value) return;
  errors.phone_number = '';
  errors.verification_code = '';

  if (!validatePhone()) return;
  if (!form.verification_code.trim()) {
    errors.verification_code = '请输入短信验证码';
    return;
  }
  if (form.verification_code.length !== 6) {
    errors.verification_code = '验证码为6位数字';
    return;
  }

  submitting.value = true;
  try {
    const verifyRes = await verifyCode({
      channel: 'SMS',
      recipient: normalizeCnPhone(form.phone_number.trim()),
      scenario: 'BIND_PHONE',
      code: form.verification_code.trim()
    });

    const res = await bindPhone({
      phone_number: normalizeCnPhone(form.phone_number.trim()),
      bind_ticket: verifyRes.data.ticket
    });
    if (res.code !== 200) {
      throw new Error(res.message || '绑定失败');
    }
    if (authStore.user) {
      authStore.user.phone_number = normalizeCnPhone(form.phone_number.trim());
      authStore.user.is_phone_verified = true;
    }
    uni.showToast({ title: isRebind.value ? '手机号换绑成功' : '手机号绑定成功', icon: 'success' });
    setTimeout(() => uni.navigateBack(), 800);
  } catch (e: any) {
    const code = e?.code ?? e?.data?.code;
    const msg = e?.message || '';
    if (code === 4006 || /验证码错误|已过期/.test(msg)) {
      errors.verification_code = '验证码错误或已过期';
    } else if (code === 409 || /已绑定/.test(msg)) {
      errors.phone_number = '该手机号已被其他账号绑定';
    } else {
      uni.showToast({ title: msg || '绑定失败，请稍后重试', icon: 'none' });
    }
  } finally {
    submitting.value = false;
  }
}
</script>

<style lang="scss" scoped>
.bind-phone-page {
  min-height: 100vh;
  background: #ffffff;
}

.auth-container {
  width: 92vw;
  max-width: 420px;
  margin: 0 auto;
  padding: 10vh 0 48rpx;
  box-sizing: border-box;
}

.auth-title {
  margin-bottom: 56rpx;
}

.title-main {
  display: block;
  font-size: 44rpx;
  font-weight: 600;
  color: #1a1a1a;
  line-height: 1.3;
  margin-bottom: 12rpx;
}

.title-subtitle {
  display: block;
  font-size: 26rpx;
  color: #666666;
  line-height: 1.5;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8rpx;

  &.form-group--error .form-input,
  &.form-group--error .input-wrapper {
    border-color: #ff4d4f;
  }
}

.field-label {
  font-size: 26rpx;
  color: #666666;
  margin-bottom: 4rpx;
}

.input-wrapper {
  display: flex;
  align-items: center;
  background: #fafafa;
  border: 1px solid #e8e8e8;
  border-radius: 12rpx;
  overflow: hidden;
}

.country-code {
  padding: 0 20rpx;
  font-size: 28rpx;
  color: #333;
  border-right: 1px solid #e8e8e8;
  line-height: 88rpx;
  flex-shrink: 0;
}

.form-input {
  width: 100%;
  height: 88rpx;
  background: #fafafa;
  border: 1px solid #e8e8e8;
  border-radius: 12rpx;
  padding: 0 24rpx;
  font-size: 28rpx;
  color: #333333;
  box-sizing: border-box;
}

.phone-input {
  flex: 1;
  border: none;
  background: transparent;
  height: 88rpx;
  padding: 0 20rpx;
}

.captcha-row {
  display: flex;
  gap: 16rpx;
  align-items: center;
}

.captcha-input {
  flex: 1;
}

.captcha-image {
  width: 220rpx;
  height: 88rpx;
  flex-shrink: 0;
  border: 1px solid #e8e8e8;
  background: #f8fafc;
  border-radius: 12rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;

  &:active {
    opacity: 0.8;
  }
}

.captcha-img {
  width: 100%;
  height: 100%;
}

.captcha-loading {
  display: flex;
  align-items: center;
  justify-content: center;
}

.loading-text {
  font-size: 24rpx;
  color: #999;
}

.sms-row {
  display: flex;
  gap: 16rpx;
  align-items: center;
}

.sms-input {
  flex: 1;
}

.sms-btn {
  flex-shrink: 0;
  height: 88rpx;
  padding: 0 28rpx;
  background: #0F766E;
  border-radius: 12rpx;
  display: flex;
  align-items: center;
  justify-content: center;

  text {
    font-size: 26rpx;
    color: #fff;
    white-space: nowrap;
  }

  &.disabled {
    background: #d9d9d9;
    text {
      color: #999;
    }
  }

  &:active:not(.disabled) {
    opacity: 0.85;
  }
}

.error-text {
  display: block;
  font-size: 24rpx;
  color: #ff4d4f;
  line-height: 1.4;
}

.auth-primary-btn {
  width: 100%;
  height: 88rpx;
  background: linear-gradient(135deg, #0F766E 0%, #0d5f58 100%);
  border-radius: 44rpx;
  color: #ffffff;
  font-size: 32rpx;
  font-weight: 600;
  border: none;
  margin-top: 16rpx;
  box-shadow: 0 8rpx 20rpx rgba(15, 118, 110, 0.25);

  &:active:not(.disabled) {
    transform: scale(0.98);
  }

  &.disabled {
    background: #d9d9d9;
    box-shadow: none;
    color: #999999;
  }
}
</style>
