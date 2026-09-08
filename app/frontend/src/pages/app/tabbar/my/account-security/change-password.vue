<template>
  <view class="change-password-page">
    <view class="auth-container">
      <view class="auth-main">
        <view class="auth-title">
          <text class="title-main">修改登录密码</text>
          <text class="title-subtitle">{{ isPasswordless ? '为当前账号设置登录密码，设置后可使用手机号/邮箱/用户名 + 密码登录' : '请先输入当前密码，再设置符合强度要求的新密码' }}</text>
        </view>

        <view class="auth-form">
          <view v-if="!isPasswordless" class="form-group" :class="{ 'form-group--error': errors.current_password }">
            <text class="field-label">当前密码</text>
            <view class="input-wrapper">
              <input
                v-model="form.current_password"
                class="form-input"
                :type="showCurrent ? 'text' : 'password'"
                placeholder="请输入当前密码"
                @input="clearFieldError('current_password')"
              />
              <text
                class="iconfont input-icon"
                :class="showCurrent ? 'icon-eye-slash' : 'icon-eye'"
                @tap="showCurrent = !showCurrent"
              />
            </view>
            <text v-if="errors.current_password" class="error-text">{{ errors.current_password }}</text>
          </view>

          <view class="form-group" :class="{ 'form-group--error': errors.new_password }">
            <text class="field-label">新密码</text>
            <view class="input-wrapper">
              <input
                v-model="form.new_password"
                class="form-input"
                :type="showNew ? 'text' : 'password'"
                placeholder="请输入新密码"
                @input="clearFieldError('new_password')"
              />
              <text
                class="iconfont input-icon"
                :class="showNew ? 'icon-eye-slash' : 'icon-eye'"
                @tap="showNew = !showNew"
              />
            </view>
            <text v-if="errors.new_password" class="error-text">{{ errors.new_password }}</text>
            <text class="hint-text">至少 8 位，须包含大写、小写、数字与特殊字符</text>
          </view>

          <view class="form-group" :class="{ 'form-group--error': errors.confirm_password }">
            <text class="field-label">确认新密码</text>
            <view class="input-wrapper">
              <input
                v-model="form.confirm_password"
                class="form-input"
                :type="showConfirm ? 'text' : 'password'"
                placeholder="请再次输入新密码"
                @input="clearFieldError('confirm_password')"
              />
              <text
                class="iconfont input-icon"
                :class="showConfirm ? 'icon-eye-slash' : 'icon-eye'"
                @tap="showConfirm = !showConfirm"
              />
            </view>
            <text v-if="errors.confirm_password" class="error-text">{{ errors.confirm_password }}</text>
          </view>

          <button
            class="auth-primary-btn"
            :class="{ disabled: submitting }"
            :disabled="submitting"
            @click="handleSubmit"
          >
            <text v-if="submitting">提交中...</text>
            <text v-else>确认修改</text>
          </button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import { changePassword } from '@/api/auth';
import { useAuthStore } from '@/store/auth';
import { useFavoriteStore } from '@/store/favorite';
import { useFollowStore } from '@/store/follow';
import { validatePassword } from '@/utils/validate';

const authStore = useAuthStore();
const favoriteStore = useFavoriteStore();
const followStore = useFollowStore();

const form = reactive({
  current_password: '',
  new_password: '',
  confirm_password: ''
});

const errors = reactive({
  current_password: '',
  new_password: '',
  confirm_password: ''
});

const showCurrent = ref(false);
const showNew = ref(false);
const showConfirm = ref(false);
const submitting = ref(false);
const isPasswordless = computed(() => !authStore.user?.has_password);

function clearFieldError(key: 'current_password' | 'new_password' | 'confirm_password') {
  errors[key] = '';
}

onShow(async () => {
  if (!authStore.isAuthenticated) {
    uni.showToast({ title: '请先登录', icon: 'none' });
    setTimeout(() => uni.navigateBack(), 400);
    return;
  }
  // 每次进入页面刷新用户信息，确保 has_password 等字段为最新
  try {
    await authStore.fetchUserProfile();
  } catch {
    /* 忽略，使用已有缓存 */
  }
});

function validateForm(): boolean {
  errors.current_password = '';
  errors.new_password = '';
  errors.confirm_password = '';

  if (!isPasswordless.value && !form.current_password.trim()) {
    errors.current_password = '请输入当前密码';
    return false;
  }
  if (!form.new_password) {
    errors.new_password = '请输入新密码';
    return false;
  }
  if (!validatePassword(form.new_password)) {
    errors.new_password = '密码至少8位，且须包含大小写字母、数字和特殊字符';
    return false;
  }
  if (!isPasswordless.value && form.new_password === form.current_password) {
    errors.new_password = '新密码不能与当前密码相同';
    return false;
  }
  if (!form.confirm_password) {
    errors.confirm_password = '请再次输入新密码';
    return false;
  }
  if (form.confirm_password !== form.new_password) {
    errors.confirm_password = '两次输入的新密码不一致';
    return false;
  }
  return true;
}

function handleBusinessFailure(code: number | undefined, message: string, data: unknown) {
  const errText =
    typeof data === 'object' && data !== null && 'error' in data
      ? String((data as { error?: string }).error || '')
      : '';
  if (code === 4004 || /当前密码/.test(message) || /当前密码/.test(errText)) {
    errors.current_password = '当前密码不正确';
    return;
  }
  if (code === 4001 || (code !== undefined && code >= 4000 && code < 5000)) {
    errors.new_password = errText || message || '请检查新密码是否符合要求';
  }
}

async function handleSubmit() {
  if (submitting.value) return;
  if (!validateForm()) return;

  submitting.value = true;
  try {
    const res = await changePassword({
      ...(isPasswordless.value ? {} : { current_password: form.current_password }),
      new_password: form.new_password
    });

    if (res.code !== 200) {
      handleBusinessFailure(res.code, res.message || '', res.data);
      return;
    }

    uni.showToast({ title: '密码修改成功，请重新登录', icon: 'success', duration: 2000 });
    authStore.clearAuth();
    uni.removeStorageSync('refresh_token');
    try {
      favoriteStore.clear();
      followStore.clear();
    } catch {
      /* 与登出流程一致，避免残留列表态 */
    }
    setTimeout(() => {
      uni.reLaunch({ url: '/pages/app/auth/login' });
    }, 800);
  } catch (e: unknown) {
    const err = e as {
      code?: number;
      message?: string;
      data?: { error?: string };
    };
    handleBusinessFailure(
      err.code,
      err.message || '',
      err.data ?? err
    );
  } finally {
    submitting.value = false;
  }
}
</script>

<style lang="scss" scoped>
.change-password-page {
  min-height: 100vh;
  background: #f9fafb;
}

.auth-container {
  width: 92vw;
  max-width: 420px;
  margin: 0 auto;
  padding: 0;
}

.auth-main {
  padding: 24rpx 0 48rpx;
}

.auth-title {
  text-align: center;
  margin-bottom: 40rpx;
}

.title-main {
  display: block;
  font-size: 36rpx;
  font-weight: 700;
  color: #111827;
  margin-bottom: 12rpx;
}

.title-subtitle {
  display: block;
  font-size: 24rpx;
  color: #6b7280;
  padding: 0 16rpx;
  line-height: 1.35;
}

.auth-form {
  padding: 0 48rpx;
}

.field-label {
  display: block;
  font-size: 26rpx;
  color: #374151;
  margin-bottom: 12rpx;
}

.form-group {
  margin-bottom: 28rpx;
}

.form-group--error .form-input {
  border-color: #ef4444;
}

.form-input {
  width: 100%;
  height: 96rpx;
  padding: 0 88rpx 0 32rpx;
  font-size: 30rpx;
  color: #111827;
  background: #FFFFFF;
  border: 2rpx solid #d1d5db;
  border-radius: 12rpx;
  box-sizing: border-box;
}

.form-input::placeholder {
  color: #9ca3af;
}

.input-wrapper {
  position: relative;
}

.input-icon {
  position: absolute;
  right: 24rpx;
  top: 50%;
  transform: translateY(-50%);
  font-size: 40rpx;
  color: #0f766e;
  padding: 8rpx;
  z-index: 10;
}

.error-text {
  display: block;
  margin-top: 12rpx;
  font-size: 24rpx;
  color: #ef4444;
}

.hint-text {
  display: block;
  margin-top: 12rpx;
  font-size: 24rpx;
  color: #9ca3af;
}

.auth-primary-btn {
  width: 100%;
  height: 96rpx;
  margin-top: 16rpx;
  background: #0f766e;
  border-radius: 48rpx;
  border: none;
  font-size: 32rpx;
  font-weight: 600;
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8rpx 16rpx rgba(15, 118, 110, 0.2);
}

.auth-primary-btn.disabled {
  opacity: 0.6;
}
</style>
