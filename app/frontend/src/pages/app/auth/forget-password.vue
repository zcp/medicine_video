<template>
  <view class="auth-page">
    <view class="auth-container">
      
      <!-- 标题 -->
      <view class="auth-title">
        <text class="title-main">忘记密码</text>
        <text class="title-subtitle">{{ step === 1 ? '验证您的身份' : '设置新密码' }}</text>
      </view>

      <!-- 步骤1：身份验证 -->
      <view class="auth-form" v-if="step === 1">
        
        <!-- Tab 切换 -->
        <view class="mode-tabs">
          <view class="mode-tab" :class="{ active: mode === 'sms' }" @click="mode = 'sms'">
            <text>短信验证</text>
          </view>
          <view class="mode-tab" :class="{ active: mode === 'email' }" @click="mode = 'email'">
            <text>邮箱找回</text>
          </view>
        </view>

        <!-- 短信验证模式 -->
        <view v-if="mode === 'sms'">
          <!-- 手机号 -->
          <view class="form-group">
            <input
              v-model="phone"
              class="form-input"
              type="text"
              placeholder="请输入手机号"
              maxlength="20"
              @input="handlePhoneInput"
              @blur="validatePhoneField"
            />
            <text v-if="phoneError" class="error-text">{{ phoneError }}</text>
          </view>

          <!-- 图形验证码 -->
          <view class="form-group">
            <view class="captcha-row">
              <input
                v-model="captchaSolution"
                class="form-input captcha-input"
                type="text"
                placeholder="图形验证码"
                maxlength="8"
              />
              <view class="captcha-image" @click="refreshCaptcha">
                <image
                  v-if="captchaImage"
                  :src="captchaImage"
                  class="captcha-img"
                  mode="aspectFit"
                />
                <view v-else class="captcha-loading">
                  <text class="loading-text">加载中</text>
                </view>
              </view>
            </view>
            <text class="captcha-refresh-link" @click="refreshCaptcha">看不清？换一张</text>
          </view>

          <!-- 短信验证码 -->
          <view class="form-group">
            <view class="otp-row">
              <input
                v-model="otpCode"
                class="form-input otp-input"
                type="text"
                placeholder="短信验证码"
                maxlength="6"
              />
              <button
                class="otp-btn"
                :class="{ disabled: countdown > 0 }"
                :disabled="countdown > 0 || !phone"
                @click="sendSmsOtp"
              >
                <text v-if="countdown > 0">{{ countdown }}s 后重发</text>
                <text v-else>获取验证码</text>
              </button>
            </view>
          </view>

          <button class="auth-primary-btn" @click="handleVerifyOtp">
            <text v-if="isVerifying">验证中...</text>
            <text v-else>下一步</text>
          </button>
        </view>

        <!-- 邮箱找回模式（折叠入口） -->
        <view v-if="mode === 'email'">
          <view class="form-group">
            <input
              v-model="email"
              class="form-input"
              type="text"
              placeholder="请输入注册邮箱"
            />
          </view>

          <view class="form-group">
            <view class="captcha-row">
              <input
                v-model="captchaSolution"
                class="form-input captcha-input"
                type="text"
                placeholder="图形验证码"
                maxlength="8"
              />
              <view class="captcha-image" @click="refreshCaptcha">
                <image
                  v-if="captchaImage"
                  :src="captchaImage"
                  class="captcha-img"
                  mode="aspectFit"
                />
                <view v-else class="captcha-loading">
                  <text class="loading-text">加载中</text>
                </view>
              </view>
            </view>
            <text class="captcha-refresh-link" @click="refreshCaptcha">看不清？换一张</text>
          </view>

          <button class="auth-primary-btn" @click="handleSendResetEmail">
            <text v-if="isSending">发送中...</text>
            <text v-else>发送重置邮件</text>
          </button>

          <text class="email-hint">邮件发送后，请点击邮件中的链接重置密码</text>
        </view>
      </view>

      <!-- 步骤2：设置新密码 -->
      <view class="auth-form" v-if="step === 2">
        <view class="form-group">
          <view class="input-wrapper">
            <input
              v-model="newPassword"
              class="form-input"
              :type="showPassword ? 'text' : 'password'"
              placeholder="请输入新密码"
              @input="calculatePasswordStrength"
            />
            <text
              class="iconfont input-icon"
              :class="showPassword ? 'icon-eye-slash' : 'icon-eye'"
              @tap="togglePasswordVisibility"
            />
          </view>
          
          <!-- 密码强度指示器 -->
          <view v-if="newPassword" class="password-strength">
            <view class="strength-bars">
              <view
                v-for="i in 5"
                :key="i"
                class="strength-bar"
                :class="{ 'strength-bar--active': i <= passwordStrength.score }"
                :style="{
                  backgroundColor: i <= passwordStrength.score
                    ? passwordStrength.color
                    : '#E5E7EB'
                }"
              />
            </view>
            <text class="strength-text" :style="{ color: passwordStrength.color }">
              密码强度: {{ passwordStrength.text }}
            </text>
          </view>
        </view>

        <view class="form-group">
          <input
            v-model="confirmPassword"
            class="form-input"
            type="password"
            placeholder="请确认新密码"
          />
          <text v-if="passwordMismatch" class="error-text">两次密码输入不一致</text>
        </view>

        <button
          class="auth-primary-btn"
          :class="{ disabled: isResetting }"
          :disabled="isResetting"
          @click="handleResetPassword"
        >
          <text v-if="isResetting">重置中...</text>
          <text v-else>重置密码</text>
        </button>
      </view>

      <!-- 底部链接 -->
      <view class="auth-secondary">
        <text class="secondary-link" @click="handleGoToLogin">返回登录</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, reactive, watch, onMounted } from 'vue';
import { onLoad } from '@dcloudio/uni-app';
import {
  sendVerificationCode,
  verifyCode,
  resetPassword,
  requestPasswordReset,
  getCaptcha
} from '@/api/auth';
import type { PasswordStrength } from '@/types/auth';
import { calculatePasswordStrengthLevel } from '@/utils/password';
import { validatePhone, validatePassword } from '@/utils/validate';
import { normalizeCnPhone } from '@/utils/phone';

// ==================== 状态 ====================

const step = ref<1 | 2>(1);
const mode = ref<'sms' | 'email'>('sms');

// 短信模式
const phone = ref('');
const otpCode = ref('');
const countdown = ref(0);
const isVerifying = ref(false);

// 邮箱模式
const email = ref('');
const isSending = ref(false);

// 验证码
const captchaId = ref('');
const captchaImage = ref('');
const captchaSolution = ref('');

// 新密码
const newPassword = ref('');
const confirmPassword = ref('');
const showPassword = ref(false);
const isResetting = ref(false);
const passwordMismatch = ref(false);

// 凭据（验证后获得）
const resetTicket = ref('');
const resetToken = ref('');

// 密码强度
const passwordStrength = ref<PasswordStrength>({
  level: 1,
  text: '密码太短',
  color: '#EF4444',
  score: 0,
});

let countdownTimer: ReturnType<typeof setInterval> | null = null;
let debounceTimer: ReturnType<typeof setTimeout> | null = null;

// ==================== 初始化 ====================

onLoad((options) => {
  // 邮箱重置回调：从 URL 参数读取 reset_token
  let token = options?.reset_token as string | undefined;
  // #ifdef H5
  // H5 上邮件链接可能直接打开浏览器，从 location.search 读取
  if (!token && typeof window !== 'undefined') {
    const params = new URLSearchParams(window.location.search);
    token = params.get('reset_token') || undefined;
  }
  // #endif
  if (token) {
    resetToken.value = token;
    step.value = 2;
    console.log('📧 [忘记密码] 邮箱回调: 已获取 reset_token');
  }
  loadCaptcha();
});

// ==================== 图形验证码 ====================

async function loadCaptcha(): Promise<void> {
  try {
    const res = await getCaptcha();
    captchaId.value = res.data.captcha_id;
    captchaImage.value = res.data.image_base64;
  } catch {
    uni.showToast({ title: '验证码加载失败', icon: 'none' });
  }
}

function refreshCaptcha(): void {
  captchaSolution.value = '';
  loadCaptcha();
}

// ==================== 密码强度 ====================

function calculatePasswordStrength(): void {
  if (debounceTimer) clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    passwordStrength.value = calculatePasswordStrengthLevel(newPassword.value);
  }, 300);
}

function togglePasswordVisibility(): void {
  showPassword.value = !showPassword.value;
}

// ==================== 短信模式 ====================

/** 手机号实时校验（输入完成后/失焦时提示，不在输入过程中打扰） */
const phoneTouched = ref(false);
const phoneError = ref('');

/** 手机号失焦/提交前校验 */
function validatePhoneField(): boolean {
  phoneTouched.value = true;
  if (!phone.value) {
    phoneError.value = '请输入手机号';
    return false;
  }
  if (!validatePhone(phone.value)) {
    phoneError.value = '请输入正确的手机号格式';
    return false;
  }
  phoneError.value = '';
  return true;
}

/** 输入时实时校验：归一化长度 >= 11（视为输入完成）或已失焦过才提示 */
function validatePhoneLive(val: string): void {
  if (!val) {
    if (phoneTouched.value) phoneError.value = '请输入手机号';
    return;
  }
  if (normalizeCnPhone(val).length >= 11 || phoneTouched.value) {
    phoneError.value = validatePhone(val) ? '' : '请输入正确的手机号格式';
  }
}
watch(phone, (val) => validatePhoneLive(val));

/** @input 兜底：直接读输入事件值触发校验（不依赖 v-model 更新时序） */
function handlePhoneInput(e: any): void {
  validatePhoneLive(e?.detail?.value ?? e?.target?.value ?? '');
}

async function sendSmsOtp(): Promise<void> {
  if (!phone.value) {
    uni.showToast({ title: '请输入手机号', icon: 'none' });
    return;
  }
  if (!validatePhone(phone.value)) {
    uni.showToast({ title: '手机号格式不正确', icon: 'none' });
    return;
  }
  if (!captchaSolution.value) {
    uni.showToast({ title: '请输入图形验证码', icon: 'none' });
    return;
  }
  try {
    await sendVerificationCode({
      channel: 'SMS',
      recipient: normalizeCnPhone(phone.value),
      scenario: 'RESET_PASSWORD',
      captcha_id: captchaId.value,
      captcha_solution: captchaSolution.value,
    });
    uni.showToast({ title: '验证码已发送', icon: 'success' });
    startCountdown();
    refreshCaptcha();
  } catch (e: any) {
    const msg = e?.data?.message || e?.message || '发送失败';
    uni.showToast({ title: msg, icon: 'none' });
    refreshCaptcha();
  }
}

function startCountdown(): void {
  countdown.value = 60;
  countdownTimer = setInterval(() => {
    countdown.value--;
    if (countdown.value <= 0 && countdownTimer) {
      clearInterval(countdownTimer);
    }
  }, 1000);
}

async function handleVerifyOtp(): Promise<void> {
  if (!otpCode.value) {
    uni.showToast({ title: '请输入短信验证码', icon: 'none' });
    return;
  }
  isVerifying.value = true;
  try {
    const res = await verifyCode({
      channel: 'SMS',
      recipient: normalizeCnPhone(phone.value),
      scenario: 'RESET_PASSWORD',
      code: otpCode.value,
    });
    resetTicket.value = res.data.ticket;
    step.value = 2;
  } catch (e: any) {
    const msg = e?.data?.message || e?.message || '验证失败';
    uni.showToast({ title: msg, icon: 'none' });
  } finally {
    isVerifying.value = false;
  }
}

// ==================== 邮箱模式 ====================

async function handleSendResetEmail(): Promise<void> {
  if (!email.value) {
    uni.showToast({ title: '请输入邮箱', icon: 'none' });
    return;
  }
  if (!captchaSolution.value) {
    uni.showToast({ title: '请输入图形验证码', icon: 'none' });
    return;
  }
  isSending.value = true;
  try {
    await requestPasswordReset({
      email: email.value,
      captcha_id: captchaId.value,
      captcha_solution: captchaSolution.value,
    });
    uni.showToast({ title: '重置邮件已发送，请查收', icon: 'success', duration: 3000 });
  } catch (e: any) {
    const msg = e?.data?.message || e?.message || '发送失败';
    uni.showToast({ title: msg, icon: 'none' });
  } finally {
    isSending.value = false;
  }
}

// ==================== 重置密码 ====================

async function handleResetPassword(): Promise<void> {
  if (!newPassword.value) {
    uni.showToast({ title: '请输入新密码', icon: 'none' });
    return;
  }
  if (!validatePassword(newPassword.value)) {
    uni.showToast({ title: '密码强度不足（至少8位，包含大小写字母+数字+特殊字符）', icon: 'none', duration: 2500 });
    return;
  }
  if (newPassword.value !== confirmPassword.value) {
    passwordMismatch.value = true;
    return;
  }
  passwordMismatch.value = false;
  isResetting.value = true;

  try {
    // 优先使用 reset_ticket（短信 OTP 路径），其次 reset_token（邮箱路径）
    await resetPassword({
      reset_ticket: resetTicket.value || undefined,
      reset_token: resetToken.value || undefined,
      new_password: newPassword.value,
    });
    uni.showToast({ title: '密码重置成功，请重新登录', icon: 'success', duration: 2000 });
    setTimeout(() => {
      uni.navigateTo({ url: '/pages/app/auth/login' });
    }, 2000);
  } catch (e: any) {
    const msg = e?.data?.message || e?.message || '重置失败';
    uni.showToast({ title: msg, icon: 'none' });
  } finally {
    isResetting.value = false;
  }
}

// ==================== 导航 ====================

function handleGoToLogin(): void {
  uni.navigateTo({ url: '/pages/app/auth/login' });
}
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.auth-page {
  min-height: 100vh;
  background: #ffffff; // consumer 白底（与登录页一致）
  display: flex;
  align-items: flex-start;
  justify-content: center;
}

.auth-container {
  width: 92vw;
  max-width: 420px;
  margin: 0 auto;
  padding: 12vh 24rpx 48rpx; // 文档0.3：consumer 靠上 12vh
  box-sizing: border-box;

  // Tablet: 480px ~ 900px
  @media (min-width: 480px) and (max-width: 899px) {
    width: 420px;
    max-width: 460px;
    padding-top: 14vh;
  }

  // Desktop: >= 900px
  @media (min-width: 900px) {
    width: 420px;
    max-width: 460px;
    padding-top: 18vh; // 文档0.3：Desktop 更居中 18vh
  }
}

// ==================== 标题区域（与登录页同一层级） ====================
.auth-title {
  margin-bottom: $spacing-3xl;
  text-align: left;
}

.title-main {
  display: block;
  font-size: 48rpx; // 文档0.4：Mobile标题 48-56rpx
  font-weight: 600;
  color: $color-text-primary;
  line-height: 1.3;
  margin-bottom: $spacing-sm;

  @media (min-width: 900px) {
    font-size: 32px; // 文档0.4：Desktop标题 32px
  }
}

.title-subtitle {
  display: block;
  font-size: 26rpx; // 文档0.4：Mobile副标题 26-28rpx
  color: #666666; // 登录页视觉DNA中性色
  line-height: 1.5;

  @media (min-width: 900px) {
    font-size: 14px; // 文档0.4：Desktop副标题 14-16px
  }
}

.auth-form {
  margin-bottom: $spacing-3xl;
}

/* ========== 模式 Tab（与登录页 tabs 同款） ========== */
.mode-tabs {
  display: flex;
  margin-bottom: $spacing-2xl;
  border-radius: 16rpx; // 登录页视觉DNA
  background: #F3F4F6;
  padding: 6rpx;
}

.mode-tab {
  flex: 1;
  text-align: center;
  padding: 16rpx 0;
  border-radius: $radius-md;
  font-size: $font-md;
  color: #6B7280;
  transition: all $motion-fast;

  &.active {
    background: #ffffff;
    color: #1F2937;
    font-weight: 500;
    box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.06);
  }

  &:active {
    opacity: 0.8;
  }
}

/* ========== 表单元素（轻边框 + focus ring，文档13） ========== */
.form-group {
  margin-bottom: $spacing-md; // 文档0.4：输入框间距 16rpx

  @media (min-width: 900px) {
    margin-bottom: 14px; // 文档0.4：Desktop 14-16px
  }
}

.form-input {
  width: 100%;
  height: 88rpx; // 文档0.4：Mobile按钮高度 88rpx
  background: $color-surface-input;
  border: 1px solid $color-border-input; // 文档13：轻边框
  border-radius: $radius-md;
  padding: 0 24rpx;
  font-size: $font-md;
  color: #333333;
  box-sizing: border-box;
  transition: all $motion-fast; // 文档13：180-220ms

  &:focus,
  &:focus-within {
    background: $color-surface-card;
    border-color: $color-primary; // 色彩清洗：原 #6366F1 → 品牌主色
    box-shadow: 0 0 0 3px $color-primary-light; // focus ring（box-shadow 实现，无 layout shift）
    outline: none;
  }

  &::placeholder {
    color: $color-text-tertiary;
  }

  &:disabled {
    background: $color-surface-page;
    color: $color-text-tertiary;
  }

  @media (min-width: 900px) {
    height: 44px; // 文档0.4：Desktop 44-48px
  }
}

.input-wrapper {
  position: relative;

  .form-input {
    padding-right: 80rpx;
  }

  .input-icon {
    position: absolute;
    right: 24rpx;
    top: 50%;
    transform: translateY(-50%);
    font-size: 36rpx;
    color: $color-text-tertiary;
    cursor: pointer;
    transition: color $motion-fast;
    padding: 8rpx;
    z-index: 10;
  }

  .input-icon:active {
    opacity: 0.7;
  }

  .icon-eye,
  .icon-eye-slash {
    color: $color-primary;
  }
}

/* ========== 图形验证码（文档10 统一规则） ========== */
.captcha-row {
  display: flex;
  gap: $spacing-md;
  align-items: center;

  .captcha-input {
    flex: 1;
  }
}

.captcha-image {
  width: 240rpx; // 文档10.1：固定宽度 240rpx
  height: 88rpx;
  border-radius: 16rpx; // 文档10.2：radius 16rpx
  overflow: hidden; // 文档10.2：overflow hidden
  flex-shrink: 0;
  border: 1px solid $color-border-input; // 文档10.2：border 1px
  background: #F8FAFC; // 文档10.2：background
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;

  &:active {
    opacity: 0.8;
  }

  @media (min-width: 900px) {
    width: 160px; // 文档10.1：Desktop 160px
    height: 44px;
  }

  .captcha-img {
    width: 100%;
    height: 100%;
  }
}

.captcha-loading {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #F3F4F6;

  .loading-text {
    font-size: $font-sm;
    color: $color-text-tertiary;
  }
}

.captcha-refresh-link {
  font-size: $font-sm;
  color: $color-primary; // 色彩清洗：原 #6366F1 → 品牌主色
  margin-top: $spacing-sm;
  padding: 8rpx 0; // 触控热区提升
  display: inline-block;
  cursor: pointer;
  transition: opacity $motion-fast;

  &:active {
    opacity: 0.7;
  }
}

/* ========== 短信验证码（与登录页 otp 同款） ========== */
.otp-row {
  display: flex;
  gap: $spacing-md;
  align-items: center;

  .otp-input {
    flex: 1;
  }
}

.otp-btn {
  flex-shrink: 0;
  height: 88rpx;
  padding: 0 28rpx;
  border-radius: $radius-md;
  background: $color-primary; // 色彩清洗：原 #6366F1 → 品牌主色
  color: #ffffff;
  font-size: 26rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  cursor: pointer;
  transition: all $motion-fast;

  &.disabled {
    background: #d9d9d9;
    color: #999;
  }

  &:active:not(.disabled) {
    opacity: 0.85;
  }

  @media (min-width: 900px) {
    height: 44px;
    padding: 0 18px;
  }
}

/* ========== 密码强度 ========== */
.password-strength {
  margin-top: $spacing-md;
}

.strength-bars {
  display: flex;
  gap: 8rpx;
  margin-bottom: 8rpx;
}

.strength-bar {
  flex: 1;
  height: 8rpx;
  border-radius: 4rpx;
  background: #E5E7EB;
}

.strength-text {
  font-size: $font-sm;
}

/* ========== 主按钮（pill，色彩清洗） ========== */
.auth-primary-btn {
  width: 100%;
  height: 88rpx; // 文档0.4：Mobile CTA 88rpx
  background: linear-gradient(135deg, $color-primary 0%, #0d5f58 100%); // 与登录页同款
  border-radius: $radius-full; // pill 样式
  color: #ffffff;
  font-size: $font-xl;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  margin-top: $spacing-lg;
  box-shadow: $shadow-button-primary;
  transition: all $motion-fast;

  &:active:not(.disabled) {
    transform: scale(0.98);
    box-shadow: 0 4rpx 12rpx rgba(15, 118, 110, 0.2);
  }

  &.disabled {
    background: #d9d9d9;
    box-shadow: none;
    color: #999;
  }

  @media (min-width: 900px) {
    height: 48px; // 文档0.4：Desktop 44-48px
  }
}

/* ========== 错误提示 ========== */
.error-text {
  color: $color-state-error;
  font-size: $font-sm;
  margin-top: $spacing-xs;
  display: block;
  line-height: 1.4;
}

/* ========== 提示文字 ========== */
.email-hint {
  display: block;
  text-align: center;
  font-size: $font-sm;
  color: $color-text-tertiary;
  margin-top: $spacing-lg;
}

/* ========== 底部链接 ========== */
.auth-secondary {
  text-align: center;
  margin-top: $spacing-3xl;
}

.secondary-link {
  color: $color-primary; // 色彩清洗：原 #6366F1 → 品牌主色
  font-size: $font-md;
  padding: 8rpx;
  cursor: pointer;
  transition: opacity $motion-fast;

  &:active {
    opacity: 0.7;
  }
}
</style>
