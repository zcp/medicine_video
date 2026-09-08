<template>
  <view class="register-page">
    <view class="register-container">
      <view class="register-main">
        <view class="register-title">
          <text class="register-title__h1">创建账号</text>
          <text class="register-title__sub">请选择注册方式</text>
        </view>

        <view class="register-form">
          <button class="register-cta" @tap="goPhoneRegister">手机号注册</button>
          <button class="register-alt" @tap="goEmailRegister">邮箱注册</button>

          <view class="register-secondary">
            <view class="register-links">
              <text class="register-link-text">已有账号？</text>
              <text class="register-link register-link--primary" @tap="goLogin">去登录</text>
            </view>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { AUTH_ROUTES, buildRegisterUrl } from '@/common/authRoutes'

function goPhoneRegister() {
  uni.navigateTo({ url: buildRegisterUrl('phone') })
}

function goEmailRegister() {
  uni.navigateTo({ url: buildRegisterUrl('email') })
}

function goLogin() {
  uni.navigateBack({
    delta: 1,
    fail: () => uni.redirectTo({ url: AUTH_ROUTES.ONE_TAP_LOGIN })
  })
}
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
  gap: var(--spacing-md);
  margin-top: var(--spacing-xl);
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
}

.register-alt {
  width: 100%;
  height: 88rpx;
  border: 1px solid var(--color-primary);
  border-radius: var(--border-radius-full);
  background: transparent;
  color: var(--color-primary);
  font-size: 30rpx;
  font-weight: 500;
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
</style>
