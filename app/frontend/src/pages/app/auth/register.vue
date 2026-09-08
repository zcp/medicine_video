<template>
  <view class="register-page auth-page">
    <!-- 页面内容 -->
    <view class="auth-container">
      <view class="auth-main">
        <!-- 标题区域 -->
        <view class="auth-title">
          <text class="title-main">创建您的账号</text>
          <text class="title-subtitle">快速注册，开启医学直播之旅</text>
        </view>

        <!-- 表单区域 -->
        <view class="auth-form">
          <!-- 注册方式 Tab -->
          <view class="reg-tabs">
            <view class="reg-tab" :class="{ active: activeTab === 'email' }" @click="activeTab = 'email'">
              <text>邮箱注册</text>
            </view>
            <view class="reg-tab" :class="{ active: activeTab === 'phone' }" @click="activeTab = 'phone'">
              <text>手机号注册</text>
            </view>
          </view>

          <!-- 用户名（仅邮箱模式） -->
          <view class="form-group" :class="{ 'form-group--error': errors.username }" v-if="activeTab === 'email'">
            <input
              v-model="formData.username"
              class="form-input"
              type="text"
              placeholder="请输入用户名"
              maxlength="50"
              @blur="validateField('username')"
            />
            <text v-if="errors.username" class="error-text">{{ errors.username }}</text>
            <text class="hint-text">2-50字符，字母/数字/下划线</text>
          </view>

          <!-- 邮箱（仅邮箱模式） -->
          <view class="form-group" :class="{ 'form-group--error': errors.email }" v-if="activeTab === 'email'">
            <input
              v-model="formData.email"
              class="form-input"
              type="text"
              placeholder="请输入邮箱"
              @blur="validateField('email')"
            />
            <text v-if="errors.email" class="error-text">{{ errors.email }}</text>
          </view>

          <!-- 手机号（仅手机模式） -->
          <view class="form-group" v-if="activeTab === 'phone'">
            <input
              v-model="phoneNumber"
              class="form-input"
              type="text"
              placeholder="请输入手机号"
              maxlength="20"
              @input="handlePhoneInput"
              @blur="validatePhoneField"
            />
            <text v-if="errors.phone_number" class="error-text">{{ errors.phone_number }}</text>
          </view>

          <!-- 图形验证码（手机模式发送短信前需要） -->
          <view class="form-group" v-if="activeTab === 'phone'">
            <view class="captcha-row">
              <input
                v-model="phoneCaptchaSolution"
                class="form-input captcha-input"
                type="text"
                placeholder="图形验证码"
                maxlength="8"
              />
              <view class="captcha-image" @click="refreshPhoneCaptcha">
                <image
                  v-if="phoneCaptchaImage"
                  :src="phoneCaptchaImage"
                  class="captcha-img"
                  mode="aspectFit"
                />
                <view v-else class="captcha-loading">
                  <text class="loading-text">加载中</text>
                </view>
              </view>
            </view>
          </view>

          <!-- 短信验证码（仅手机模式） -->
          <view class="form-group" v-if="activeTab === 'phone'">
            <view class="otp-row">
              <input
                v-model="smsOtpCode"
                class="form-input otp-input"
                type="text"
                placeholder="短信验证码"
                maxlength="6"
              />
              <button
                class="otp-btn"
                :class="{ disabled: otpCountdown > 0 }"
                :disabled="otpCountdown > 0 || !phoneNumber"
                @click="handleSendSmsOtp"
              >
                <text v-if="otpCountdown > 0">{{ otpCountdown }}s</text>
                <text v-else>获取验证码</text>
              </button>
            </view>
          </view>

          <!-- 密码 -->
          <view class="form-group" :class="{ 'form-group--error': errors.password }">
            <view class="input-wrapper">
              <input
                v-model="formData.password"
                class="form-input"
                :type="showPassword ? 'text' : 'password'"
                placeholder="请输入密码"
                @input="calculatePasswordStrength"
                @blur="validateField('password')"
              />
              <text 
                class="iconfont input-icon" 
                :class="showPassword ? 'icon-eye-slash' : 'icon-eye'"
                @tap="togglePasswordVisibility"
              ></text>
            </view>
            <text v-if="errors.password" class="error-text">{{ errors.password }}</text>
            
            <!-- 密码强度指示器 -->
            <view v-if="formData.password" class="password-strength">
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
                ></view>
              </view>
              <text 
                class="strength-text" 
                :style="{ color: passwordStrength.color }"
              >
                密码强度: {{ passwordStrength.text }}
              </text>
            </view>
          </view>

          <!-- 昵称 -->
          <view class="form-group" :class="{ 'form-group--error': errors.nickname }">
            <input
              v-model="formData.nickname"
              class="form-input"
              type="text"
              placeholder="请输入昵称"
              maxlength="50"
              @blur="validateField('nickname')"
            />
            <text v-if="errors.nickname" class="error-text">{{ errors.nickname }}</text>
            <text class="hint-text">显示给其他用户看的名称</text>
          </view>

          <!-- 验证码（仅邮箱模式） -->
          <view class="form-group" :class="{ 'form-group--error': errors.captcha_solution }" v-if="activeTab === 'email'">
            <view class="captcha-row">
              <input
                v-model="formData.captcha_solution"
                class="form-input captcha-input"
                type="text"
                placeholder="请输入验证码"
                maxlength="6"
                @blur="validateField('captcha_solution')"
              />
              <view class="captcha-image" @click="refreshCaptcha">
                <image
                  v-if="captchaImage"
                  :src="captchaImage"
                  class="captcha-img"
                  mode="aspectFit"
                ></image>
                <view v-else class="captcha-loading">
                  <text class="loading-text">加载中</text>
                </view>
              </view>
            </view>
            <text v-if="errors.captcha_solution" class="error-text">{{ errors.captcha_solution }}</text>
            <text class="captcha-refresh-link" @click="refreshCaptcha">看不清？换一张</text>
          </view>

          <!-- 注册按钮 -->
          <button
            class="auth-primary-btn"
            :class="{ 'disabled': isSubmitting }"
            :disabled="isSubmitting"
            @click="activeTab === 'email' ? handleSubmit() : handlePhoneRegister()"
          >
            <text v-if="isSubmitting">注册中...</text>
            <text v-else>注 册</text>
          </button>

          <!-- 协议区 -->
          <view class="auth-agreement">
            <text class="agreement-text">注册即表示同意</text>
            <text class="agreement-link" @click="showComingSoon">《用户协议》</text>
            <text class="agreement-text">与</text>
            <text class="agreement-link" @click="showComingSoon">《隐私政策》</text>
          </view>
        </view>

        <!-- 底部提示 -->
        <view class="auth-secondary">
          <text class="secondary-text">已有账号？</text>
          <text class="secondary-link" @click="handleGoToLogin">立即登录</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, reactive, watch, onMounted } from 'vue';
import { getCaptcha, registerUser, sendVerificationCode, verifyCode, registerByPhone } from '@/api/auth';
import { useAuthStore } from '@/store/auth';
import { useFavoriteStore } from '@/store/favorite';
import { useFollowStore } from '@/store/follow';
import type { RegisterForm, PasswordStrength } from '@/types/auth';
import { validateUsername, validateEmail, validatePassword, validateNickname, validatePhone } from '@/utils/validate';
import { normalizeCnPhone } from '@/utils/phone';
import { calculatePasswordStrengthLevel } from '@/utils/password';

// ==================== 状态定义 ====================

/** 注册方式 */
const activeTab = ref<'email' | 'phone'>('email');

/** 手机号注册相关 */
const phoneNumber = ref('');
const smsOtpCode = ref('');
const otpCountdown = ref(0);
let otpTimer: ReturnType<typeof setInterval> | null = null;
const phoneCaptchaId = ref('');
const phoneCaptchaImage = ref('');
const phoneCaptchaSolution = ref('');

/** 表单数据 */
const formData = reactive<RegisterForm>({
  username: '',
  email: '',
  password: '',
  nickname: '',
  captcha_solution: '',
});

/** 表单错误信息 */
const errors = reactive<Record<string, string>>({
  username: '',
  email: '',
  password: '',
  nickname: '',
  captcha_solution: '',
  phone_number: '',
});

/** 验证码相关 */
const captchaId = ref<string>('');
const captchaImage = ref<string>('');

/** 密码显示/隐藏 */
const showPassword = ref<boolean>(false);

/** 提交状态 */
const isSubmitting = ref<boolean>(false);

/** 密码强度 */
const passwordStrength = ref<PasswordStrength>({
  level: 1,
  text: '密码太短',
  color: '#EF4444',
  score: 0,
});

/** 防抖定时器 */
let debounceTimer: ReturnType<typeof setTimeout> | null = null;

// ==================== Store ====================
const authStore = useAuthStore();

// ==================== 初始化 ====================

/**
 * 页面加载时获取验证码
 */
onMounted(() => {
  loadCaptcha();
  refreshPhoneCaptcha();
});

/**
 * 加载图形验证码
 */
async function loadCaptcha(): Promise<void> {
  try {
    console.log('[Register] 加载验证码...');
    const res = await getCaptcha();
    captchaId.value = res.data.captcha_id;
    captchaImage.value = res.data.image_base64;
    console.log('[Register] 验证码加载成功');
  } catch (error) {
    console.error('[Register] 验证码加载失败', error);
    uni.showToast({ 
      title: '验证码加载失败', 
      icon: 'none' 
    });
  }
}

/**
 * 刷新验证码
 */
function refreshCaptcha(): void {
  formData.captcha_solution = '';
  errors.captcha_solution = '';
  loadCaptcha();
}

// ==================== 表单校验 ====================

/**
 * 校验单个字段
 */
function validateField(field: keyof RegisterForm): boolean {
  let isValid = true;
  errors[field] = '';

  switch (field) {
    case 'username':
      if (!formData.username) {
        errors.username = '请输入用户名';
        isValid = false;
      } else if (!validateUsername(formData.username)) {
        errors.username = '用户名格式不正确（2-50字符，字母/数字/下划线）';
        isValid = false;
      }
      break;

    case 'email':
      if (!formData.email) {
        errors.email = '请输入邮箱';
        isValid = false;
      } else if (!validateEmail(formData.email)) {
        errors.email = '请输入有效的邮箱地址';
        isValid = false;
      }
      break;

    case 'password':
      if (!formData.password) {
        errors.password = '请输入密码';
        isValid = false;
      } else if (!validatePassword(formData.password)) {
        errors.password = '密码强度不足（至少8位，包含大小写字母+数字+特殊字符）';
        isValid = false;
      }
      break;

    case 'nickname':
      if (!formData.nickname) {
        errors.nickname = '请输入昵称';
        isValid = false;
      } else if (!validateNickname(formData.nickname)) {
        errors.nickname = '昵称长度为2-50字符';
        isValid = false;
      }
      break;

    case 'captcha_solution':
      if (!formData.captcha_solution) {
        errors.captcha_solution = '请输入验证码';
        isValid = false;
      }
      break;
  }

  return isValid;
}

/**
 * 校验所有字段
 */
function validateAllFields(): boolean {
  let isValid = true;
  
  (Object.keys(formData) as Array<keyof RegisterForm>).forEach((field) => {
    if (!validateField(field)) {
      isValid = false;
    }
  });
  
  return isValid;
}

// ==================== 密码强度计算 ====================

/**
 * 计算密码强度（带防抖）
 */
function calculatePasswordStrength(): void {
  if (debounceTimer) {
    clearTimeout(debounceTimer);
  }
  
  debounceTimer = setTimeout(() => {
    passwordStrength.value = calculatePasswordStrengthLevel(formData.password);
  }, 300);
}

/**
 * 切换密码显示/隐藏
 */
function togglePasswordVisibility(): void {
  showPassword.value = !showPassword.value;
}

// ==================== 表单提交 ====================

/**
 * 提交注册表单
 */
async function handleSubmit(): Promise<void> {
  // 1. 前端校验
  if (!validateAllFields()) {
    uni.showToast({ 
      title: '请检查表单填写', 
      icon: 'none' 
    });
    return;
  }

  // 2. 开始提交
  isSubmitting.value = true;

  try {
    console.log('[Register] 开始注册...');
    
    // 3. 调用注册API
    const res = await registerUser({
      username: formData.username,
      email: formData.email,
      password: formData.password,
      nickname: formData.nickname,
      captcha_id: captchaId.value,
      captcha_solution: formData.captcha_solution,
    });

    // 4. 注册成功
    console.log('[Register] 注册成功', res.data);
    uni.showToast({ 
      title: '注册成功，正在登录...', 
      icon: 'success', 
      duration: 2000 
    });

    // 5. 注册成功，跳转到登录页
    setTimeout(() => {
      uni.showToast({ 
        title: '注册成功，请登录', 
        icon: 'success',
        duration: 1500
      });
      setTimeout(() => {
        uni.navigateBack();
      }, 1500);
    }, 500);

  } catch (error: any) {
    console.error('[Register] 注册失败', error);
    
    // 解析错误信息
    const errorCode = error.code || error.response?.data?.code;
    const errorMsg = error.message || error.response?.data?.message || '注册失败，请重试';
    
    // 根据错误码处理
    handleRegisterError(errorCode, errorMsg);

    // 刷新验证码
    refreshCaptcha();

  } finally {
    isSubmitting.value = false;
  }
}

// ==================== 手机号注册 ====================

/** 手机号实时校验（输入完成后/失焦时提示，不在输入过程中打扰） */
const phoneTouched = ref(false);

/** 手机号失焦/提交前校验 */
function validatePhoneField(): boolean {
  phoneTouched.value = true;
  if (!phoneNumber.value) {
    errors.phone_number = '请输入手机号';
    return false;
  }
  if (!validatePhone(phoneNumber.value)) {
    errors.phone_number = '请输入正确的手机号格式';
    return false;
  }
  errors.phone_number = '';
  return true;
}

/** 输入时实时校验：归一化长度 >= 11（视为输入完成）或已失焦过才提示 */
function validatePhoneLive(val: string): void {
  if (!val) {
    if (phoneTouched.value) errors.phone_number = '请输入手机号';
    return;
  }
  if (normalizeCnPhone(val).length >= 11 || phoneTouched.value) {
    errors.phone_number = validatePhone(val) ? '' : '请输入正确的手机号格式';
  }
}
watch(phoneNumber, (val) => validatePhoneLive(val));

/** @input 兜底：直接读输入事件值触发校验（不依赖 v-model 更新时序） */
function handlePhoneInput(e: any): void {
  validatePhoneLive(e?.detail?.value ?? e?.target?.value ?? '');
}

/** 发送短信验证码 */
async function handleSendSmsOtp(): Promise<void> {
  if (!phoneNumber.value) {
    uni.showToast({ title: '请输入手机号', icon: 'none' });
    return;
  }
  if (!validatePhone(phoneNumber.value)) {
    uni.showToast({ title: '手机号格式不正确', icon: 'none' });
    return;
  }
  if (!phoneCaptchaSolution.value) {
    uni.showToast({ title: '请输入图形验证码', icon: 'none' });
    return;
  }
  try {
    await sendVerificationCode({
      channel: 'SMS',
      recipient: normalizeCnPhone(phoneNumber.value),
      scenario: 'REGISTER',
      captcha_id: phoneCaptchaId.value,
      captcha_solution: phoneCaptchaSolution.value,
    });
    uni.showToast({ title: '验证码已发送', icon: 'success' });
    phoneCaptchaSolution.value = '';
    otpCountdown.value = 60;
    otpTimer = setInterval(() => {
      otpCountdown.value--;
      if (otpCountdown.value <= 0 && otpTimer) {
        clearInterval(otpTimer);
        otpTimer = null;
      }
    }, 1000);
  } catch (e: any) {
    const msg = e?.data?.message || e?.message || '发送失败';
    uni.showToast({ title: msg, icon: 'none' });
    refreshPhoneCaptcha();
  }
}

async function refreshPhoneCaptcha(): Promise<void> {
  try {
    const res = await getCaptcha();
    phoneCaptchaId.value = res.data.captcha_id;
    phoneCaptchaImage.value = res.data.image_base64;
  } catch {
    uni.showToast({ title: '验证码加载失败', icon: 'none' });
  }
}

/** 手机号注册提交 */
async function handlePhoneRegister(): Promise<void> {
  if (!phoneNumber.value) {
    uni.showToast({ title: '请输入手机号', icon: 'none' });
    return;
  }
  if (!smsOtpCode.value) {
    uni.showToast({ title: '请输入短信验证码', icon: 'none' });
    return;
  }
  if (!formData.password) {
    uni.showToast({ title: '请输入密码', icon: 'none' });
    return;
  }
  if (!validatePassword(formData.password)) {
    uni.showToast({ title: '密码强度不足（至少8位，包含大小写字母+数字+特殊字符）', icon: 'none', duration: 2500 });
    return;
  }
  if (!formData.nickname) {
    uni.showToast({ title: '请输入昵称', icon: 'none' });
    return;
  }

  isSubmitting.value = true;
  try {
    const verifyRes = await verifyCode({
      channel: 'SMS',
      recipient: normalizeCnPhone(phoneNumber.value),
      scenario: 'REGISTER',
      code: smsOtpCode.value,
    });

    const regRes = await registerByPhone({
      register_ticket: verifyRes.data.ticket,
      password: formData.password,
      nickname: formData.nickname,
    });

    const { access_token, refresh_token, phone_number: regPhone, is_new_user } = regRes.data;

    await authStore.loginWithTokens(access_token, refresh_token);
    
    // 异步加载收藏和关注列表（不阻塞跳转）
    try {
      const favoriteStore = useFavoriteStore();
      const followStore = useFollowStore();
      Promise.all([
        favoriteStore.loadFavorites(),
        followStore.loadFollowedExperts()
      ]).catch(err => console.warn('[手机注册] 收藏/关注加载失败:', err));
    } catch (err) {
      console.warn('[手机注册] 加载Store失败:', err);
    }
    
    const regMsg = is_new_user ? '注册成功，欢迎加入' : '登录成功';
    uni.showToast({ title: regMsg, icon: 'success', duration: 1500 });
    setTimeout(() => {
      authStore.handleAuthRedirect();
    }, 1500);
  } catch (e: any) {
    const code = e?.code || e?.data?.code;
    const msg = e?.data?.message || e?.message || '注册失败';
    if (code === 4009) {
      uni.showToast({ title: '该手机号已被注册', icon: 'none' });
    } else if (code === 4004 || code === 4005) {
      uni.showToast({ title: '验证码错误或已过期', icon: 'none' });
    } else {
      uni.showToast({ title: msg, icon: 'none' });
    }
  } finally {
    isSubmitting.value = false;
  }
}

/**
 * 统一错误处理
 */
function handleRegisterError(errorCode: number, errorMsg: string): void {
  switch (errorCode) {
    case 4003:
      // 验证码错误
      errors.captcha_solution = '验证码错误或已过期';
      formData.captcha_solution = '';
      uni.showToast({ title: '验证码错误，请重新输入', icon: 'none' });
      break;
      
    case 4009:
      // 用户名已占用
      errors.username = '用户名已被占用';
      uni.showToast({ title: '用户名已被占用，请更换', icon: 'none' });
      break;
      
    case 4010:
      // 邮箱已注册
      errors.email = '邮箱已被注册';
      uni.showToast({ 
        title: '邮箱已被注册，请更换或前往登录', 
        icon: 'none',
        duration: 3000
      });
      break;
      
    case 4001:
      // 参数校验失败
      uni.showToast({ title: '请检查表单填写', icon: 'none' });
      break;
      
    default:
      // 通用错误处理
      uni.showToast({ title: errorMsg, icon: 'none' });
  }
}

// ==================== 页面导航 ====================

/**
 * 跳转到登录页
 */
function handleGoToLogin(): void {
  uni.navigateTo({ url: '/pages/app/auth/login' });
}

/**
 * 显示"敬请期待"提示
 */
function showComingSoon(): void {
  uni.showToast({
    title: '功能开发中，敬请期待',
    icon: 'none'
  });
}
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.register-page {
  min-height: 100vh;
  background: #ffffff; // 与登录页一致：consumer 白底
  display: flex;
  align-items: flex-start;
  justify-content: center;
}

// ==================== 页面容器（文档0.2/0.3 响应式规则） ====================
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

.auth-main {
  overflow-y: auto;
}

// ==================== 标题区域（与登录页同一层级） ====================
.auth-title {
  text-align: left;
  margin-bottom: $spacing-3xl;
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

// ==================== 注册方式 Tab（与登录页 tabs 同款） ====================
.reg-tabs {
  display: flex;
  margin-bottom: $spacing-2xl;
  border-radius: 16rpx; // 登录页视觉DNA
  background: #F3F4F6;
  padding: 6rpx;
}

.reg-tab {
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

// ==================== 表单区域 ====================
.auth-form {
  padding: 0;
}

.form-group {
  margin-bottom: $spacing-md; // 文档0.4：输入框间距 16rpx

  @media (min-width: 900px) {
    margin-bottom: 14px; // 文档0.4：Desktop 14-16px
  }
}

.form-group--error .form-input {
  border-color: $color-state-error;
}

// 输入框：轻边框 + focus ring（文档13，与登录页一致）
.form-input {
  width: 100%;
  height: 88rpx; // 文档0.4：Mobile按钮高度 88rpx
  padding: 0 24rpx;
  font-size: $font-md;
  color: #333333;
  background: $color-surface-input;
  border: 1px solid $color-border-input;
  border-radius: $radius-md;
  box-sizing: border-box;
  transition: all $motion-fast; // 文档13：180-220ms

  &:focus,
  &:focus-within {
    background: $color-surface-card;
    border-color: $color-primary;
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

.error-text {
  display: block;
  margin-top: $spacing-sm;
  font-size: $font-sm;
  color: $color-state-error;
  line-height: 1.4;
}

.hint-text {
  display: block;
  margin-top: $spacing-sm;
  font-size: $font-sm;
  color: $color-text-tertiary;
}

// ==================== 密码输入框 ====================
.input-wrapper {
  position: relative;
}

.input-icon {
  position: absolute;
  right: 32rpx;
  top: 50%;
  transform: translateY(-50%);
  font-size: 40rpx;
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

// ==================== 密码强度指示器 ====================
.password-strength {
  display: flex;
  align-items: center;
  gap: $spacing-lg;
  margin-top: $spacing-md;
}

.strength-bars {
  display: flex;
  gap: 8rpx;
  flex: 1;
}

.strength-bar {
  height: 8rpx;
  flex: 1;
  background: #E5E7EB;
  border-radius: 4rpx;
  transition: background-color $motion-fast;
}

.strength-text {
  font-size: $font-sm;
  font-weight: 500;
  white-space: nowrap;
}

// ==================== 图形验证码（文档10 统一规则） ====================
.captcha-row {
  display: flex;
  align-items: center;
  gap: $spacing-md;
}

.captcha-input {
  flex: 1;
}

.captcha-image {
  width: 240rpx; // 文档10.1：固定宽度 240rpx
  height: 88rpx;
  flex-shrink: 0;
  border: 1px solid $color-border-input; // 文档10.2：border 1px
  background: #F8FAFC; // 文档10.2：background
  border-radius: 16rpx; // 文档10.2：radius 16rpx
  overflow: hidden; // 文档10.2：overflow hidden
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
}

.captcha-img {
  width: 100%;
  height: 100%;
}

.captcha-loading {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #F3F4F6;
}

.loading-text {
  font-size: $font-sm;
  color: $color-text-tertiary;
}

.captcha-refresh-link {
  display: inline-block;
  margin-top: $spacing-sm;
  padding: 8rpx 0; // 触控热区提升
  font-size: $font-sm;
  color: $color-primary;
  cursor: pointer;
  transition: opacity $motion-fast;

  &:active {
    opacity: 0.7;
  }
}

// ==================== 短信验证码（与登录页 otp 同款） ====================
.otp-row {
  display: flex;
  gap: $spacing-md;
  align-items: center;
}

.otp-input {
  flex: 1;
}

.otp-btn {
  flex-shrink: 0;
  height: 88rpx;
  padding: 0 28rpx;
  background: $color-primary;
  border-radius: $radius-md;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  cursor: pointer;
  transition: all $motion-fast;

  text {
    font-size: 26rpx;
    color: #fff;
    white-space: nowrap;
  }

  &.disabled {
    background: #d9d9d9;
    text { color: #999; }
  }

  &:active:not(.disabled) {
    opacity: 0.85;
  }

  @media (min-width: 900px) {
    height: 44px;
    padding: 0 18px;
  }
}

// ==================== 提交按钮（pill 主按钮，文档13） ====================
.auth-primary-btn {
  width: 100%;
  height: 88rpx; // 文档0.4：Mobile CTA 88rpx
  margin-top: $spacing-lg;
  background: linear-gradient(135deg, $color-primary 0%, #0d5f58 100%); // 与登录页同款
  border-radius: $radius-full; // pill 样式
  border: none;
  font-size: $font-xl;
  font-weight: 600;
  color: $color-text-white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: $shadow-button-primary;
  transition: all $motion-fast;

  &:active:not(.disabled) {
    transform: scale(0.98);
    box-shadow: 0 4rpx 12rpx rgba(15, 118, 110, 0.2);
  }

  &.disabled {
    background: #d9d9d9;
    box-shadow: none;
    color: #999999;
  }

  @media (min-width: 900px) {
    height: 48px; // 文档0.4：Desktop 44-48px
  }
}

// ==================== 协议区 ====================
.auth-agreement {
  padding: $spacing-lg 0 0;
  text-align: center;
  font-size: $font-sm;
  color: $color-text-tertiary;
  line-height: 1.6;
}

.agreement-text {
  color: $color-text-tertiary;
}

.agreement-link {
  color: $color-primary;
  cursor: pointer;

  &:active {
    opacity: 0.7;
  }
}

// ==================== 底部提示 ====================
.auth-secondary {
  margin-top: $spacing-3xl;
  padding: 0 0 $spacing-3xl;
  text-align: center;
}

.secondary-text {
  font-size: $font-md;
  color: #6B7280;
}

.secondary-link {
  font-size: $font-md;
  color: $color-primary;
  font-weight: 600;
  cursor: pointer;
  padding: 8rpx;
  transition: opacity $motion-fast;

  &:active {
    opacity: 0.7;
  }
}
</style>
