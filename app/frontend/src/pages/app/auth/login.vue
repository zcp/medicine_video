<template>
  <view class="auth-page">
    <!-- Auth Container：响应式容器 -->
    <view class="auth-container">
      
      <!-- Auth Title：标题区域 -->
      <view class="auth-title">
        <text class="title-main">欢迎回来</text>
        <text class="title-subtitle">登录后体验完整功能</text>
      </view>

      <!-- 登录方式 Tab -->
      <view class="login-tabs">
        <view class="login-tab" :class="{ active: loginMode === 'oneTap' }" @click="loginMode = 'oneTap'">
          <text>一键登录</text>
        </view>
        <view class="login-tab" :class="{ active: loginMode === 'password' }" @click="loginMode = 'password'">
          <text>密码登录</text>
        </view>
        <view class="login-tab" :class="{ active: loginMode === 'phone' }" @click="loginMode = 'phone'">
          <text>手机号登录</text>
        </view>
      </view>

      <!-- 一键登录模式 -->
      <view v-if="loginMode === 'oneTap'" class="one-tap-section">
        <view v-if="isOneKeyChecking" class="one-tap-loading">
          <text>检测登录方式...</text>
        </view>
        <view v-else-if="isOneKeyLoginAvailable">
          <button class="one-tap-btn" :disabled="isLoggingIn" @click="handleOneTapLogin">
            <text>本机号码一键登录</text>
          </button>
          <text class="one-tap-hint">未注册将自动创建账号</text>
        </view>
        <view v-else class="one-tap-unavailable">
          <text class="one-tap-hint">当前设备不支持一键登录，请使用其他方式</text>
        </view>
      </view>

      <!-- 手机号验证码登录模式 -->
      <view v-if="loginMode === 'phone'" class="phone-login-section">
        <!-- 手机号 -->
        <view class="form-group">
          <input
            v-model="phoneNumber"
            class="form-input"
            type="text"
            placeholder="请输入手机号"
            maxlength="20"
            @input="handlePhoneInput"
            @blur="validatePhoneField"
          />
          <text v-if="errors.phone" class="error-text">{{ errors.phone }}</text>
        </view>

        <!-- 短信验证码 -->
        <view class="form-group">
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

        <button class="auth-primary-btn" :class="{ disabled: isLoggingIn }" :disabled="isLoggingIn" @click="handlePhoneLogin">
          <text v-if="isLoggingIn">登录中...</text>
          <text v-else>登录</text>
        </button>
        <text class="phone-login-hint">未注册的手机号验证后将自动创建账号</text>
      </view>

      <!-- 密码登录模式 -->
      <view v-if="loginMode === 'password'">
      <!-- Auth Form：表单区域 -->
      <view class="auth-form">
        <!-- 账号输入 -->
        <view class="form-group">
          <input
            v-model="formData.username"
            class="form-input"
            type="text"
            placeholder="请输入账号"
            :disabled="isLoginDisabled"
            @blur="validateUsername"
          />
          <text v-if="errors.username" class="error-text">{{ errors.username }}</text>
        </view>

        <!-- 密码输入 -->
        <view class="form-group">
          <view class="input-wrapper">
            <input
              v-model="formData.password"
              class="form-input"
              :type="showPassword ? 'text' : 'password'"
              placeholder="请输入密码"
              :disabled="isLoginDisabled"
              @blur="validatePassword"
            />
            <text 
              class="iconfont input-icon" 
              :class="showPassword ? 'icon-eye-slash' : 'icon-eye'"
              @tap="togglePasswordVisibility"
            ></text>
          </view>
          <text v-if="errors.password" class="error-text">{{ errors.password }}</text>
        </view>

        <!-- 验证码输入 -->
        <view class="form-group">
          <view class="captcha-row">
            <input
              v-model="formData.captcha_solution"
              class="form-input captcha-input"
              type="text"
              placeholder="请输入验证码"
              :disabled="isLoginDisabled"
              maxlength="8"
              @blur="validateCaptcha"
            />
            <view class="captcha-image" @click="refreshCaptcha">
              <image
                v-if="captchaUrl"
                :key="captchaUrl"
                :src="captchaUrl"
                class="captcha-img"
                mode="aspectFit"
              ></image>
              <view v-else class="captcha-loading">
                <text class="loading-text">加载中</text>
              </view>
            </view>
          </view>
          <text v-if="errors.captcha" class="error-text">{{ errors.captcha }}</text>
          <text v-if="captchaRetryCount > 0" class="retry-text">
            验证码加载失败 ({{ captchaRetryCount }}/{{ MAX_CAPTCHA_RETRY }})，点击图片重试
          </text>
        </view>

        <!-- 主按钮（文档：pill样式） -->
        <button
          class="auth-primary-btn"
          :class="{ disabled: isLoginDisabled || isLoggingIn }"
          :disabled="isLoginDisabled || isLoggingIn"
          @click="handleLogin"
        >
          <text v-if="isLoggingIn">登录中...</text>
          <text v-else-if="isLoginDisabled">请稍后再试 ({{ lockoutCountdown }}s)</text>
          <text v-else>登录</text>
        </button>
      </view>
      </view>

      <!-- Auth Secondary：次要操作 -->
      <view v-if="loginMode === 'password'" class="auth-secondary">
        <text class="secondary-link" @click="handleGoToRegister">注册账号</text>
        <text class="secondary-link" @click="handleGoToForgetPassword">忘记密码</text>
      </view>

      <!-- Auth Divider：分割线 -->
      <view class="auth-divider">
        <view class="divider-line"></view>
        <text class="divider-text">或使用以下方式登录</text>
        <view class="divider-line"></view>
      </view>

      <!-- Auth OAuth：第三方登录（文档9.2：响应式grid） -->
      <view class="auth-oauth">
        <view class="oauth-grid">
          <view class="oauth-btn" @click="showComingSoon">
            <text class="oauth-text">微信登录</text>
          </view>
          <view class="oauth-btn" @click="showComingSoon">
            <text class="oauth-text">Apple登录</text>
          </view>
        </view>
      </view>

      <!-- Auth Agreement：协议（P0 合规：需主动勾选） -->
      <view class="auth-agreement">
        <view
          class="agree-checkbox"
          :class="{ checked: agreeToTerms }"
          @click="agreeToTerms = !agreeToTerms"
        >
          <text v-if="agreeToTerms" class="checkmark">✓</text>
        </view>
        <text class="agreement-text">我已阅读并同意</text>
        <text class="agreement-link" @click.stop>《用户协议》</text>
        <text class="agreement-text">与</text>
        <text class="agreement-link" @click.stop>《隐私政策》</text>
      </view>

    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, reactive, watch, onMounted, onUnmounted } from 'vue';
import { useAuthStore } from '@/store/auth';
import { getCaptcha, oneTapLogin, cloudFunctionLogin, sendVerificationCode, verifyCode, loginByPhone } from '@/api/auth';
import type { LoginRequest } from '@/types/auth';
import { validatePhone } from '@/utils/validate';
import { normalizeCnPhone } from '@/utils/phone';
import { ENV_CONFIG } from '@/config/env';

// 常量定义
const MAX_CAPTCHA_RETRY = 3; // 验证码最大重试次数
const LOCKOUT_DURATION = 60; // 429锁定时长（秒）
// 🔴 DCloud univerify Mock 开关
// true: 跳过运营商授权，走 Mock 手机号（审核期间调试用）
// false: 走真实 uni.login + 云函数解密（审核通过后）
// 通过 .env 文件的 VITE_UNIVERIFY_MOCK_ENABLED 控制
const UNIVERIFY_MOCK_ENABLED = ENV_CONFIG.VITE_UNIVERIFY_MOCK_ENABLED;

const loginMode = ref<'password' | 'oneTap' | 'phone'>('oneTap');

// Store
const authStore = useAuthStore();

// 响应式数据
const formData = reactive<LoginRequest>({
  username: '',
  password: '',
  captcha_id: '',
  captcha_solution: ''
});

const errors = reactive({
  username: '',
  password: '',
  captcha: '',
  phone: ''
});

const captchaUrl = ref<string>('');
const showPassword = ref(false);
const agreeToTerms = ref(false); // P0：隐私协议主动勾选
const isLoggingIn = ref(false); // 防止重复点击
const isLoginDisabled = ref(false); // 429限流锁定
const captchaRetryCount = ref(0); // 验证码重试计数
const lockoutCountdown = ref(0); // 锁定倒计时
const captchaLoadTime = ref<number>(0); // 🔍 验证码加载时间戳（用于诊断过期问题）
const lastCaptchaId = ref<string>(''); // 🔍 最后加载的验证码ID（用于诊断ID不匹配）
const passwordFailCount = ref(0); // P1：密码登录失败次数，≥2 时显示验证码
let lockoutTimer: number | null = null;

// 手机号登录状态
const phoneNumber = ref('');
const smsOtpCode = ref('');
const otpCountdown = ref(0);
let otpTimer: ReturnType<typeof setInterval> | null = null;

// 手机号实时校验（输入完成后/失焦时提示，不在输入过程中打扰）
const phoneTouched = ref(false);

/** 手机号失焦/提交前校验 */
const validatePhoneField = () => {
  phoneTouched.value = true;
  if (!phoneNumber.value) {
    errors.phone = '请输入手机号';
    return false;
  }
  if (!validatePhone(phoneNumber.value)) {
    errors.phone = '请输入正确的手机号格式';
    return false;
  }
  errors.phone = '';
  return true;
};

/** 输入时实时校验：归一化长度 >= 11（视为输入完成）或已失焦过才提示 */
function validatePhoneLive(val: string): void {
  if (!val) {
    if (phoneTouched.value) errors.phone = '请输入手机号';
    return;
  }
  if (normalizeCnPhone(val).length >= 11 || phoneTouched.value) {
    errors.phone = validatePhone(val) ? '' : '请输入正确的手机号格式';
  }
}
watch(phoneNumber, (val) => validatePhoneLive(val));

/** @input 兜底：直接读输入事件值触发校验（不依赖 v-model 更新时序） */
function handlePhoneInput(e: any): void {
  validatePhoneLive(e?.detail?.value ?? e?.target?.value ?? '');
}

// 一键登录状态
const isOneKeyLoginAvailable = ref(false); // 设备是否支持一键登录
const isOneKeyChecking = ref(true); // 预检测中

// 生命周期
onMounted(() => {
  loadCaptcha();
  checkOneTapAvailability();
});

onUnmounted(() => {
  if (lockoutTimer) {
    clearInterval(lockoutTimer);
  }
  if (otpTimer) {
    clearInterval(otpTimer);
    otpTimer = null;
  }
});

// ==================== 一键登录：预检测 ====================

/**
 * 预检测当前设备是否支持一键登录
 * 仅在 APP 真机环境下可调用；模拟器/H5 不支持
 */
const checkOneTapAvailability = async () => {
  // #ifdef APP-PLUS
  try {
    await uni.preLogin({ provider: 'univerify' });
    isOneKeyLoginAvailable.value = true;
  } catch {
    // 不支持一键登录（模拟器、未配置等）
    isOneKeyLoginAvailable.value = false;
  } finally {
    isOneKeyChecking.value = false;
  }
  // #endif
  // #ifndef APP-PLUS
  isOneKeyLoginAvailable.value = false;
  isOneKeyChecking.value = false;
  // #endif
};

// 加载验证码
const loadCaptcha = async () => {
  // 强制使用真实认证API（去掉DEV模式Mock逻辑）
  
  // 🔴 P0: 检查重试次数限制
  if (captchaRetryCount.value >= MAX_CAPTCHA_RETRY) {
    uni.showToast({
      title: `验证码加载失败次数过多，请稍后再试`,
      icon: 'none',
      duration: 3000
    });
    return;
  }

  // ⚠️ 立即清除旧验证码，防止 uni-app APP 平台 <image> 缓存旧图
  captchaUrl.value = '';
  formData.captcha_solution = '';
  errors.captcha = '';

  try {
    const response = await getCaptcha();
    const { captcha_id, image_base64 } = response.data;
    
    formData.captcha_id = captcha_id;
    captchaUrl.value = image_base64;
    captchaRetryCount.value = 0; // 成功后重置计数
    
    // 🔍 记录加载时间和ID（用于诊断）
    captchaLoadTime.value = Date.now();
    lastCaptchaId.value = captcha_id;
    
    console.log('✅ 验证码加载成功', {
      captcha_id: captcha_id,
      load_time: new Date().toLocaleTimeString(),
      image_length: image_base64?.length || 0
    });
  } catch (error: any) {
    captchaRetryCount.value++;
    console.error('❌ 验证码加载失败:', error);
    
    uni.showToast({
      title: '验证码加载失败，请点击图片重试',
      icon: 'none',
      duration: 2000
    });
  }
};

// 刷新验证码
const refreshCaptcha = () => {
  formData.captcha_solution = '';
  errors.captcha = '';
  loadCaptcha();
};

// 切换密码可见性
const togglePasswordVisibility = () => {
  showPassword.value = !showPassword.value;
};

// 表单验证
const validateUsername = () => {
  if (!formData.username.trim()) {
    errors.username = '请输入账号';
    return false;
  }
  errors.username = '';
  return true;
};

const validatePassword = () => {
  if (!formData.password) {
    errors.password = '请输入密码';
    return false;
  }
  if (formData.password.length < 6) {
    errors.password = '密码至少6位';
    return false;
  }
  errors.password = '';
  return true;
};

const validateCaptcha = () => {
  if (!formData.captcha_solution.trim()) {
    errors.captcha = '请输入验证码';
    return false;
  }
  if (formData.captcha_solution.length < 3 || formData.captcha_solution.length > 8) {
    errors.captcha = '验证码长度应为3-8位字符';
    return false;
  }
  errors.captcha = '';
  return true;
};

const validateForm = (): boolean => {
  const isUsernameValid = validateUsername();
  const isPasswordValid = validatePassword();
  const isCaptchaValid = validateCaptcha();
  
  return isUsernameValid && isPasswordValid && isCaptchaValid;
};

// 处理登录
const handleLogin = async () => {
  console.log('');
  console.log('═══════════════════════════════════════════════════');
  console.log('🔐 登录流程开始');
  console.log('═══════════════════════════════════════════════════');
  
  // 强制使用真实认证API（去掉DEV模式Mock逻辑）
  
  // 🔴 P0: 防止重复点击
  if (isLoggingIn.value) {
    console.log('⚠️ 登录中，请勿重复点击');
    return;
  }

  // 🔴 P0: 检查429限流锁定
  if (isLoginDisabled.value) {
    uni.showToast({
      title: `请求过于频繁，请${lockoutCountdown.value}秒后再试`,
      icon: 'none',
      duration: 2000
    });
    return;
  }

  // 🔴 P0: 隐私协议勾选检查
  if (!agreeToTerms.value) {
    uni.showToast({
      title: '请先阅读并同意用户协议与隐私政策',
      icon: 'none',
      duration: 2000
    });
    return;
  }

  // 表单验证
  console.log('📋 [步骤1] 表单验证');
  if (!validateForm()) {
    console.log('❌ [步骤1] 表单验证失败');
    return;
  }
  console.log('✅ [步骤1] 表单验证通过');

  // 设置登录中状态
  isLoggingIn.value = true;

  try {
    console.log('🔐 [步骤2] 调用登录API');
    
    // 🔍 计算验证码已存在时长
    const captchaAge = captchaLoadTime.value ? Date.now() - captchaLoadTime.value : 0;
    
    // 🔍 检查验证码ID是否被意外修改
    const idMatches = formData.captcha_id === lastCaptchaId.value;
    if (!idMatches) {
      console.warn('⚠️ [诊断] 验证码ID不匹配！', {
        current_id: formData.captcha_id,
        loaded_id: lastCaptchaId.value
      });
    }
    
    console.log('📤 [步骤2] 登录参数:', {
      username: formData.username,
      password: '******', // 🔒 安全：隐藏密码
      password_length: formData.password.length,
      captcha_id: formData.captcha_id,
      captcha_id_matches: idMatches ? '✅' : '❌',
      captcha_solution: formData.captcha_solution,
      captcha_solution_length: formData.captcha_solution.length,
      captcha_age_seconds: Math.floor(captchaAge / 1000) // 🔍 验证码已存在多少秒
    });
    
    await authStore.login(formData);
    
    console.log('✅ [步骤3] authStore.login() 执行成功');
    console.log('📊 [步骤3] 当前认证状态:', {
      isAuthenticated: authStore.isAuthenticated,
      hasUser: !!authStore.user,
      username: authStore.user?.username,
      hasToken: !!authStore.token,
      tokenPreview: authStore.token ? authStore.token.substring(0, 30) + '...' : 'null'
    });
    
    // 验证token是否成功保存到storage
    const storedToken = uni.getStorageSync('jwt_token');
    console.log('💾 [步骤3] Storage验证:', {
      hasStoredToken: !!storedToken,
      tokenMatch: storedToken === authStore.token,
      storedTokenPreview: storedToken ? storedToken.substring(0, 30) + '...' : 'null'
    });
    
    passwordFailCount.value = 0; // P1：登录成功，重置失败计数
    uni.showToast({
      title: '登录成功',
      icon: 'success',
      duration: 1500
    });

    // 延迟跳转以显示成功提示
    setTimeout(() => {
      console.log('⏰ [步骤4] 1.5秒延迟结束，准备执行跳转...');
      console.log('📍 [步骤4] 准备调用 handleAuthRedirect()');
      authStore.handleAuthRedirect();
      console.log('✅ [步骤4] handleAuthRedirect() 调用完成');
      console.log('═══════════════════════════════════════════════════');
      console.log('🎉 登录流程完成');
      console.log('═══════════════════════════════════════════════════');
      console.log('');
    }, 1500);
    
  } catch (error: any) {
    console.error('❌ 登录失败:', error);
    
    // 🔴 P0: 处理429限流错误
    if (error.code === 4029 || error.statusCode === 429) {
      isLoginDisabled.value = true;
      lockoutCountdown.value = LOCKOUT_DURATION;
      
      // 启动倒计时
      lockoutTimer = setInterval(() => {
        lockoutCountdown.value--;
        if (lockoutCountdown.value <= 0) {
          isLoginDisabled.value = false;
          if (lockoutTimer) {
            clearInterval(lockoutTimer);
            lockoutTimer = null;
          }
        }
      }, 1000) as unknown as number;
      
      uni.showToast({
        title: `请求过于频繁，请${LOCKOUT_DURATION}秒后再试`,
        icon: 'none',
        duration: 3000
      });
      
      // 🔴 P0: 自动刷新验证码
      refreshCaptcha();
      return;
    }
    
    // P1：非429错误，递增密码失败计数
    passwordFailCount.value++;
    
    // 处理其他错误码
    console.log('❌ [登录] 登录失败，错误详情:', {
      code: error.code,
      statusCode: error.statusCode,
      message: error.message,
      data: error.data,
      errMsg: error.errMsg,
      fullError: error
    });
    
    console.log('🔍 [诊断] 检查登录参数:');
    console.log('  - username:', formData.username);
    console.log('  - username长度:', formData.username.length);
    console.log('  - username包含空格?', formData.username.includes(' '));
    console.log('  - 密码长度:', formData.password.length);
    console.log('  - 密码包含空格?', formData.password.includes(' '));
    console.log('  - 密码首字符类型:', /^[a-zA-Z]/.test(formData.password) ? '字母' : /^[0-9]/.test(formData.password) ? '数字' : '特殊字符');
    console.log('  - 验证码ID:', formData.captcha_id);
    console.log('  - 验证码答案:', formData.captcha_solution);
    
    const errorMessages: Record<number, string> = {
      3001: '用户名或密码错误',
      3002: '账号已注销或不存在，请先注册',
      4003: '验证码验证失败或已过期',
      4004: '用户名或密码错误',
      4005: '账号已被禁用'
    };
    
    const errorMessage = errorMessages[error.code] || error.message || '登录失败，请稍后重试';
    console.log('📋 [错误处理] 错误码:', error.code, '错误消息:', errorMessage);
    
    // 🔴 优化：根据错误类型显示不同的处理
    if (error.code === 3002) {
      // 账号已注销/状态异常：提示用户注册
      uni.showModal({
        title: '账号不存在',
        content: '该账号已注销或不存在，请先注册新账号。',
        confirmText: '去注册',
        cancelText: '取消',
        success: (res) => {
          if (res.confirm) {
            uni.navigateTo({ url: '/pages/app/auth/register' });
          }
        }
      });
    } else if (error.code === 4003) {
      // 🔍 验证码错误诊断
      const ageSeconds = captchaLoadTime.value ? Math.floor((Date.now() - captchaLoadTime.value) / 1000) : 0;
      console.log('🔄 [登录] 验证码错误，已清空输入框并刷新验证码', {
        error_message: errorMessage,
        captcha_existed_seconds: ageSeconds,
        possible_reason: ageSeconds > 60 ? '可能已过期（>60秒）' : '可能输入错误',
        suggestion: ageSeconds > 60 ? '建议缩短输入时间' : '建议仔细核对验证码'
      });
      
      // 验证码错误：在输入框下方显示错误
      errors.captcha = errorMessage;
      // 清空验证码输入框
      formData.captcha_solution = '';
      // 自动刷新验证码
      refreshCaptcha();
      uni.showToast({
        title: errorMessage,
        icon: 'none',
        duration: 2000
      });
    } else if (error.code === 3001 || error.code === 4004) {
      // 用户名或密码错误：在对应输入框显示错误
      errors.password = errorMessage;
      uni.showToast({
        title: errorMessage,
        icon: 'none',
        duration: 2000
      });
    } else {
      // 其他错误：显示toast提示
      uni.showToast({
        title: errorMessage,
        icon: 'none',
        duration: 2000
      });
      // 自动刷新验证码
      refreshCaptcha();
    }
    
  } finally {
    isLoggingIn.value = false;
  }
};

// 显示即将上线提示
const showComingSoon = () => {
  uni.showToast({
    title: '该功能即将上线',
    icon: 'none',
    duration: 2000
  });
};

// ==================== 一键登录：核心流程 ====================

/**
 * 一键登录（DCloud univerify）
 *
 * 流程：
 *  ① uni.login({provider:'univerify'}) → 唤起运营商授权
 *  ② 云函数 get-phone-number → 解密手机号 → 调后端签发 JWT
 *  ③ authStore.loginWithTokens() → 存 token + 获取用户信息
 *
 * 前置条件：
 *  - 用户已勾选隐私协议（agreeToTerms）
 *  - 已在 manifest.json 启用 univerify
 *  - 需在真机上测试（模拟器不支持）
 */
const handleOneTapLogin = async () => {
  if (isLoggingIn.value) return;

  // 🔴 P0: 隐私协议勾选检查
  if (!agreeToTerms.value) {
    uni.showToast({
      title: '请先阅读并同意用户协议与隐私政策',
      icon: 'none',
      duration: 2000
    });
    return;
  }

  // #ifndef APP-PLUS
  uni.showToast({ title: '当前平台不支持一键登录', icon: 'none' });
  return;
  // #endif

  // #ifdef APP-PLUS
  isLoggingIn.value = true;

  // 🔴 开发模式：审核通过前用 Mock 模拟手机号，测试后端完整链路
  if (UNIVERIFY_MOCK_ENABLED) {
    try {
      console.log('【一键登录-Mock】模拟手机号登录');
      const mockRes = await oneTapLogin({
        carrier_token: 'mock:+8613800138000',
        provider: 'dcloud'
      });
      const { access_token: jwt, refresh_token } = mockRes.data;
      await authStore.loginWithTokens(jwt, refresh_token);
      uni.showToast({ title: mockRes.data.is_new_user ? '欢迎加入' : '欢迎回来', icon: 'success', duration: 1500 });
      setTimeout(() => authStore.handleAuthRedirect(), 1500);
    } catch (e: any) {
      uni.showToast({ title: (e?.message || '一键登录失败') + '，请使用密码或短信登录', icon: 'none', duration: 3000 });
    } finally {
      isLoggingIn.value = false;
    }
    return;
  }

  try {
    // ① 唤起运营商授权界面
    console.log('【一键登录】正在唤起运营商授权...');
    const loginRes = await uni.login({ provider: 'univerify' });
    const { access_token, openid } = loginRes.authResult || {};
    console.log('【一键登录】运营商授权成功', { has_access_token: !!access_token, has_openid: !!openid });

    if (!access_token || !openid) {
      throw { message: '获取运营商授权信息失败' };
    }

    // ② 调云函数解密手机号（仅解密，不代理后端）
    console.log('【一键登录】调云函数解密手机号...');
    const cloudRes = await uniCloud.callFunction({
      name: 'get-phone-number',
      data: { access_token, openid }
    });

    const { result } = cloudRes;
    console.log('【一键登录】云函数返回:', result);

    // 关闭运营商授权界面
    uni.closeAuthView();

    if (!result || result.code !== 0 || !result.phone || !result.sign) {
      throw { message: result?.msg || '手机号解密或签名失败' };
    }

    // ③ 用云函数返回的 phone + HMAC 签名调后端签发 JWT
    console.log('【一键登录】调后端签发 JWT...');
    const loginRes_backend = await cloudFunctionLogin({
      phone: result.phone,
      sign: result.sign,
      timestamp: result.timestamp
    });

    const { access_token: jwtToken, refresh_token } = loginRes_backend.data;
    if (!jwtToken) {
      throw { message: '未获取到登录凭证' };
    }

    // ④ 使用 store 统一处理 token 存储、用户信息获取
    await authStore.loginWithTokens(jwtToken, refresh_token);

    const isNewUser = loginRes_backend.data.is_new_user;
    const welcomeMsg = isNewUser ? '欢迎加入' : '欢迎回来';
    uni.showToast({ title: welcomeMsg, icon: 'success', duration: 1500 });

    setTimeout(() => {
      authStore.handleAuthRedirect();
    }, 1500);

  } catch (e: any) {
    // 如果授权界面还开着则关闭
    try { uni.closeAuthView(); } catch {}

    console.error('【一键登录】失败:', e);

    // 用户取消授权（运营商界面主动关闭）
    if (e.errMsg?.includes('cancel') || e.code === 1001) {
      uni.showToast({ title: '已取消', icon: 'none' });
      return;
    }

    const msg = e?.message || '一键登录失败';
    uni.showToast({
      title: msg + '，请使用密码或短信登录',
      icon: 'none',
      duration: 3000
    });
  } finally {
    isLoggingIn.value = false;
  }
  // #endif
};

// 跳转到注册页面
const handleGoToRegister = () => {
  uni.navigateTo({
    url: '/pages/app/auth/register'
  });
};

// 跳转到忘记密码页面
const handleGoToForgetPassword = () => {
  uni.navigateTo({
    url: '/pages/app/auth/forget-password'
  });
};

// ==================== 手机号验证码登录 ====================

const handleSendSmsOtp = async () => {
  if (otpCountdown.value > 0) return;
  if (!phoneNumber.value) {
    uni.showToast({ title: '请输入手机号', icon: 'none' });
    return;
  }
  if (!validatePhone(phoneNumber.value)) {
    uni.showToast({ title: '手机号格式不正确', icon: 'none' });
    return;
  }
  try {
    await sendVerificationCode({
      channel: 'SMS',
      recipient: normalizeCnPhone(phoneNumber.value),
      scenario: 'LOGIN',
    });
    uni.showToast({ title: '验证码已发送', icon: 'success' });
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
  }
};

const handlePhoneLogin = async () => {
  if (isLoggingIn.value) return;

  // 🔴 P0: 隐私协议勾选检查
  if (!agreeToTerms.value) {
    uni.showToast({
      title: '请先阅读并同意用户协议与隐私政策',
      icon: 'none',
      duration: 2000
    });
    return;
  }

  if (!phoneNumber.value) {
    uni.showToast({ title: '请输入手机号', icon: 'none' });
    return;
  }
  if (!smsOtpCode.value) {
    uni.showToast({ title: '请输入短信验证码', icon: 'none' });
    return;
  }
  isLoggingIn.value = true;
  try {
    const verifyRes = await verifyCode({
      channel: 'SMS',
      recipient: normalizeCnPhone(phoneNumber.value),
      scenario: 'LOGIN',
      code: smsOtpCode.value,
    });

    const res = await loginByPhone({ login_ticket: verifyRes.data.ticket });
    const { access_token, refresh_token, phone_masked } = res.data;

    // 🔴 使用 store 统一方法处理 token 存储、用户信息获取、收藏关注加载
    await authStore.loginWithTokens(access_token, refresh_token);

    const welcomeMsg = phone_masked ? `欢迎回来，${phone_masked}` : '登录成功';
    uni.showToast({ title: welcomeMsg, icon: 'success' });
    setTimeout(() => {
      authStore.handleAuthRedirect();
    }, 1500);
  } catch (e: any) {
    const code = e?.code || e?.data?.code;
    const msg = e?.data?.message || e?.message || '登录失败';

    // 与密码登录一致的错误码映射
    const errorMessages: Record<number, string> = {
      3001: '用户名或密码错误',
      3002: '该账号不存在或已注销',
      4003: '验证码验证失败或已过期',
      4004: '验证码错误或已过期',
      4005: '账号已被禁用',
    };
    const displayMsg = errorMessages[code] || msg;
    uni.showToast({ title: displayMsg, icon: 'none' });
  } finally {
    isLoggingIn.value = false;
  }
};
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

/* ========================================
   文档0）全局响应式适配规则
   ======================================== */

/* 文档0.1 断点定义 */
$breakpoint-mobile: 480px;  // < 480px
$breakpoint-tablet: 900px;  // 480px ~ 900px
// >= 900px 为 Desktop

/* ========================================
   Auth Page Root
   ======================================== */
.auth-page {
  min-height: 100vh;
  background: #ffffff; // 文档1：白色背景（consumer模式）
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 0;
}

/* ========================================
   文档0.2 容器宽度策略 + 0.3 垂直位置策略
   ======================================== */
.auth-container {
  width: 92vw;
  max-width: 420px;
  margin: 0 auto;
  padding: 12vh 24rpx 48rpx; // 文档0.3：Mobile靠上 12vh
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
    padding-top: 18vh; // 文档0.3：Desktop更居中 18vh
  }
}

/* ========================================
   Auth Title（文档1：Title Area）
   ======================================== */
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
  color: #666666;
  line-height: 1.5;

  @media (min-width: 900px) {
    font-size: 14px; // 文档0.4：Desktop副标题 14-16px
  }
}

/* ========================================
   Auth Form（文档1：Primary Action Area）
   ======================================== */
.auth-form {
  margin-bottom: 32rpx;
}

.form-group {
  margin-bottom: $spacing-md; // 文档0.4：输入框间距 16rpx

  @media (min-width: 900px) {
    margin-bottom: 14px; // 文档0.4：Desktop 14-16px
  }
}

/* 输入框：轻边框 + focus ring */
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
    border-color: $color-primary; // 主色 focus ring
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

/* 密码输入：带图标 */
.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
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

/* ========================================
   文档10）验证码区域（Captcha wireframe）
   ======================================== */
.captcha-row {
  display: flex;
  gap: 16rpx;
  align-items: center;
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
  border-radius: 16rpx; // 文档10.2：radius  overflow: hidden; // 文档10.2：overflow hidden
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
  object-fit: contain;
}

.captcha-loading {
  display: flex;
  align-items: center;
  justify-content: center;
}

.loading-text {
  font-size: 24rpx;
  color: #999999;
}

/* 错误提示 */
.error-text {
  display: block;
  font-size: $font-sm;
  color: $color-state-error;
  margin-top: $spacing-xs;
  line-height: 1.4;
}

.retry-text {
  display: block;
  font-size: $font-sm;
  color: $color-state-warning;
  margin-top: $spacing-xs;
  line-height: 1.4;
}

/* ========================================
   Phase 4：一键登录 + 登录方式 Tab
   ======================================== */
.login-tabs {
  display: flex;
  margin-bottom: 40rpx;
  border-radius: 16rpx;
  background: #F3F4F6;
  padding: 6rpx;
}

.login-tab {
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

.one-tap-section {
  margin-bottom: 24rpx;
}

.one-tap-btn {
  width: 100%;
  height: 88rpx;
  background: linear-gradient(135deg, $color-primary 0%, #0d5f58 100%); // 色彩清洗：清除历史亮蓝色 #3B82F6/#2563EB，对齐品牌主色
  border-radius: $radius-full;
  color: $color-text-white;
  font-size: $font-xl;
  font-weight: 600;
  border: none;
  box-shadow: $shadow-button-primary;
  transition: all $motion-fast;

  &:active:not(:disabled) {
    transform: scale(0.98);
    opacity: 0.9;
  }

  &:disabled {
    opacity: 0.6;
  }
}

.one-tap-hint {
  display: block;
  text-align: center;
  font-size: 22rpx;
  color: $color-text-tertiary;
  margin-top: $spacing-xs;
}

.one-tap-loading {
  text-align: center;
  padding: 40rpx 0;
  color: $color-text-tertiary;
  font-size: 26rpx;
}

.one-tap-unavailable {
  padding: 20rpx 0;
}

.phone-login-hint {
  display: block;
  text-align: center;
  font-size: 22rpx;
  color: $color-text-tertiary;
  margin-top: $spacing-md;
}

/* ========================================
   手机号登录：OTP 行 + 获取验证码按钮
   ======================================== */
.phone-login-section {
  margin-bottom: 24rpx;
}

.otp-row {
  display: flex;
  gap: 16rpx;
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

/* ========================================
   Primary Button（文档13：pill样式）
   ======================================== */
.auth-primary-btn {
  width: 100%;
  height: 88rpx; // 文档0.4：Mobile CTA按钮 88rpx
  background: linear-gradient(135deg, $color-primary 0%, #0d5f58 100%); // 主色
  border-radius: $radius-full; // pill样式：完全圆角
  color: $color-text-white;
  font-size: $font-xl;
  font-weight: 600;
  border: none;
  margin-top: $spacing-lg;
  box-shadow: $shadow-button-primary;
  transition: all $motion-fast; // 文档13：180-220ms

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

/* ========================================
   文档1：Secondary Actions
   ======================================== */
.auth-secondary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: $spacing-lg 0 $spacing-3xl;
  padding: 0 8rpx;
}

.secondary-link {
  font-size: 26rpx;
  color: #666666;
  padding: 8rpx;
  cursor: pointer;
  transition: color $motion-fast;

  &:hover {
    color: $color-primary;
  }

  &:active {
    color: $color-primary;
  }
}

/* ========================================
   文档1：Divider
   ======================================== */
.auth-divider {
  display: flex;
  align-items: center;
  margin: $spacing-3xl 0 $spacing-lg;
}

.divider-line {
  flex: 1;
  height: 1px;
  background: $color-border-divider; // 若隐若现分割线（去油腻）
}

.divider-text {
  font-size: $font-sm;
  color: $color-text-tertiary;
  padding: 0 $spacing-md;
  white-space: nowrap;
}

/* ========================================
   文档9）OAuth按钮区（响应式grid）
   ======================================== */
.auth-oauth {
  margin-bottom: 32rpx;
}

.oauth-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr); // 文档9.2：Mobile 2列
  gap: 16rpx; // 文档9.2：gap 16rpx

  @media (min-width: 900px) {
    grid-template-columns: repeat(3, 1fr); // 文档9.2：Desktop 3列（可选）
    gap: 12px; // 文档9.2：Desktop gap 12-16px
  }
}

.oauth-btn {
  height: 72rpx; // 文档9.2：button height 72rpx
  background: $color-surface-input;
  border: 1px solid $color-border-input;
  border-radius: $radius-md;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all $motion-fast;

  &:active {
    background: #f0f0f0;
    border-color: #d9d9d9;
  }

  @media (min-width: 900px) {
    height: 44px; // 文档9.2：Desktop 44px
  }
}

.oauth-text {
  font-size: 26rpx; // 文档9.2：text size 26rpx
  color: #333333;

  @media (min-width: 900px) {
    font-size: 14px;
  }
}

/* ========================================
   文档1：Agreement
   ======================================== */
.auth-agreement {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  font-size: $font-sm;
  color: $color-text-tertiary;
  line-height: 1.6;
  margin-top: $spacing-lg;
  gap: 4rpx;
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

/* 隐私协议勾选框 */
.agree-checkbox {
  width: 32rpx;
  height: 32rpx;
  border: 2rpx solid #d9d9d9;
  border-radius: 6rpx;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all $motion-fast;

  &.checked {
    background: $color-primary;
    border-color: $color-primary;
  }

  &:active {
    opacity: 0.7;
  }
}

.checkmark {
  color: #ffffff;
  font-size: 22rpx;
  font-weight: bold;
}
</style>
