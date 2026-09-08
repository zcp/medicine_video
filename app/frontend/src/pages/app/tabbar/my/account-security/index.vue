<template>
  <view class="page account-security consumer-layout">
    <!-- 账号信息区 -->
    <view class="menu-section">
      <view class="menu-list">
        <view class="menu-item row" @click="onUidTap">
          <text class="menu-label">用户 ID（UID）</text>
          <view class="menu-right">
            <text class="menu-value uid-preview">{{ uidPreview }}</text>
            <text class="menu-suffix muted">查看</text>
            <text class="iconfont icon-arrow-right"></text>
          </view>
        </view>
        <view class="menu-item row" @click="onEmailRebind">
          <text class="menu-label">邮箱</text>
          <view class="menu-right">
            <text class="menu-value">{{ maskedEmail }}</text>
            <text class="menu-suffix">换绑</text>
            <text class="iconfont icon-arrow-right"></text>
          </view>
        </view>
        <view class="menu-item row" @click="onBindPhone">
          <text class="menu-label">手机号</text>
          <view class="menu-right">
            <text class="menu-value" :class="{ unbound: !hasPhone }">{{ maskedPhone }}</text>
            <text class="menu-suffix" :class="{ 'new-bind': !hasPhone }">{{ hasPhone ? '换绑' : '去绑定' }}</text>
            <text class="iconfont icon-arrow-right"></text>
          </view>
        </view>
        <view class="menu-item row" @click="onChangePassword">
          <text class="menu-label">登录密码</text>
          <view class="menu-right">
            <text class="menu-suffix muted">修改密码</text>
            <text class="iconfont icon-arrow-right"></text>
          </view>
        </view>
        <view class="menu-item row" @click="onPrivacy">
          <text class="menu-label">隐私政策</text>
          <view class="menu-right">
            <text class="menu-suffix muted">查看协议</text>
            <text class="iconfont icon-arrow-right"></text>
          </view>
        </view>
      </view>
    </view>

    <!-- 第三方账号区 -->
    <view class="menu-section">
      <view class="section-title">第三方账号</view>
      <view class="menu-list">
        <view class="menu-item row" @click="onThirdPartyTap('微信')">
          <view class="third-party-left">
            <text class="iconfont icon-wechat third-party-icon wechat"></text>
            <text class="menu-label">微信</text>
          </view>
          <view class="menu-right">
            <text class="menu-suffix muted">未绑定</text>
            <text class="iconfont icon-arrow-right"></text>
          </view>
        </view>
        <view class="menu-item row" @click="onThirdPartyTap('Apple')">
          <view class="third-party-left">
            <text class="iconfont icon-apple third-party-icon apple"></text>
            <text class="menu-label">Apple</text>
          </view>
          <view class="menu-right">
            <text class="menu-suffix muted">未绑定</text>
            <text class="iconfont icon-arrow-right"></text>
          </view>
        </view>
      </view>
    </view>

    <view class="danger-block">
      <text class="danger-title">危险操作</text>
      <view class="logout-btn" @click="onLogout">
        <text>退出登录</text>
      </view>
      <view class="danger-btn" @click="onDeleteAccount">
        <text>注销账号</text>
      </view>
    </view>

    <!-- 注销确认：图形验证码弹层 -->
    <view v-if="showCaptchaModal" class="captcha-mask" @tap="cancelDeleteAccount">
      <view class="captcha-modal" @tap.stop>
        <text class="captcha-modal-title">注销确认</text>
        <text class="captcha-modal-desc">请输入图形验证码以确认注销账号</text>
        <view class="captcha-row">
          <input
            v-model="captchaSolution"
            class="captcha-input"
            type="text"
            placeholder="请输入验证码"
            maxlength="8"
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
        <view class="captcha-modal-actions">
          <view class="captcha-btn captcha-btn--cancel" @click="cancelDeleteAccount">
            <text>取消</text>
          </view>
          <view class="captcha-btn captcha-btn--danger" @click="confirmDeleteAccount">
            <text>{{ captchaSubmitting ? '注销中…' : '确认注销' }}</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import { useAuthStore } from '@/store/auth';
import { maskEmail, maskPhone, formatShortPublicId } from '@/utils/userDisplay';
import { deleteUserAccount, getCaptcha } from '@/api/auth';

const authStore = useAuthStore();

const maskedEmail = computed(() => maskEmail(authStore.user?.email));
const uidPreview = computed(() => formatShortPublicId(authStore.user?.user_id));
const hasPhone = computed(() => !!authStore.user?.phone_number);
const maskedPhone = computed(() => maskPhone(authStore.user?.phone_number));

// 注销验证码弹层状态
const showCaptchaModal = ref(false);
const captchaUrl = ref('');
const captchaId = ref('');
const captchaSolution = ref('');
const captchaSubmitting = ref(false);

async function loadCaptcha() {
  try {
    const res = await getCaptcha();
    captchaId.value = res.data.captcha_id;
    captchaUrl.value = res.data.image_base64;
    captchaSolution.value = '';
  } catch (e) {
    uni.showToast({ title: '验证码加载失败，请点击图片重试', icon: 'none' });
  }
}

function refreshCaptcha() {
  captchaSolution.value = '';
  loadCaptcha();
}

function onUidTap() {
  const id = authStore.user?.user_id;
  if (!id) {
    uni.showToast({ title: '暂无 UID', icon: 'none' });
    return;
  }
  uni.showModal({
    title: '用户 ID（UID）',
    content: id,
    confirmText: '复制',
    cancelText: '关闭',
    success: (res) => {
      if (res.confirm) {
        uni.setClipboardData({
          data: id,
          success: () => uni.showToast({ title: '已复制', icon: 'none' })
        });
      }
    }
  });
}

onShow(async () => {
  if (!authStore.isAuthenticated) {
    uni.showToast({ title: '请先登录', icon: 'none' });
    uni.navigateBack({
      fail: () => { uni.switchTab({ url: '/pages/app/tabbar/home/index' }); }
    });
    return;
  }
  try {
    await authStore.fetchUserProfile();
  } catch {
    /* 忽略，展示已有缓存 */
  }
});

function onEmailRebind() {
  uni.showToast({ title: '邮箱换绑功能开发中', icon: 'none' });
}

function onBindPhone() {
  uni.navigateTo({
    url: '/pages/app/tabbar/my/account-security/bind-phone'
  });
}

function onChangePassword() {
  uni.navigateTo({
    url: '/pages/app/tabbar/my/account-security/change-password'
  });
}

function onPrivacy() {
  uni.navigateTo({
    url: '/pages/shared/webview/index?url=' + encodeURIComponent('https://example.com/privacy')
  });
}

function onThirdPartyTap(name: string) {
  uni.showToast({ title: `${name}绑定功能即将上线`, icon: 'none' });
}

function onLogout() {
  uni.showModal({
    title: '提示',
    content: '确定要退出登录吗？',
    success: (res) => {
      if (res.confirm) {
        authStore.logout();
      }
    }
  });
}

function onDeleteAccount() {
  uni.showModal({
    title: '注销账号',
    content: '注销后账号数据将无法恢复，确定继续？',
    confirmText: '确定注销',
    confirmColor: '#b91c1c',
    success: async (res) => {
      if (!res.confirm) return;
      // 加载图形验证码，弹出验证码确认层
      showCaptchaModal.value = true;
      await loadCaptcha();
    }
  });
}

async function confirmDeleteAccount() {
  if (!captchaSolution.value.trim()) {
    uni.showToast({ title: '请输入验证码', icon: 'none' });
    return;
  }
  if (captchaSubmitting.value) return;
  captchaSubmitting.value = true;
  try {
    const r = await deleteUserAccount({
      captcha_id: captchaId.value,
      captcha_solution: captchaSolution.value.trim(),
    });
    if (r.code !== 200) {
      throw new Error(r.message || '注销失败');
    }
    showCaptchaModal.value = false;
    authStore.clearAuth();
    uni.removeStorageSync('refresh_token');
    uni.showToast({ title: '账号已注销', icon: 'success' });
    setTimeout(() => {
      uni.reLaunch({ url: '/pages/app/auth/login' });
    }, 600);
  } catch (e: any) {
    // 验证码错误/过期时刷新验证码
    refreshCaptcha();
    const msg = e?.message || '暂时无法注销';
    uni.showToast({ title: msg.length > 20 ? msg.slice(0, 20) + '…' : msg, icon: 'none' });
  } finally {
    captchaSubmitting.value = false;
  }
}

function cancelDeleteAccount() {
  showCaptchaModal.value = false;
}
</script>

<style lang="scss" scoped>
.consumer-layout {
  min-height: 100vh;
  background-color: var(--home-bg);
  padding: 0 var(--home-spacing-page) 48rpx;
  box-sizing: border-box;
}

.menu-section {
  margin-bottom: 48rpx;
}

.menu-list {
  background: transparent;
}

.menu-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 96rpx;
  padding: 24rpx 0;
  border-bottom: 1rpx solid rgba(0, 0, 0, 0.06);

  &:last-child {
    border-bottom: none;
  }

  &:active {
    opacity: 0.75;
  }
}

.menu-label {
  font-size: var(--home-fs-card-title, 30rpx);
  color: var(--home-text1);
  flex-shrink: 0;
}

.menu-right {
  display: flex;
  align-items: center;
  gap: 12rpx;
  min-width: 0;
  flex: 1;
  justify-content: flex-end;
}

.menu-value {
  font-size: 26rpx;
  color: var(--home-text2);
  max-width: 360rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.menu-suffix {
  font-size: 26rpx;
  color: var(--home-primary);

  &.muted {
    color: var(--home-text2);
  }
}

.icon-arrow-right {
  font-size: 28rpx !important;
  color: var(--home-text2) !important;
}

.section-title {
  font-size: 26rpx;
  color: var(--home-text2);
  margin-bottom: 8rpx;
}

.third-party-left {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.third-party-icon {
  font-size: 40rpx;

  &.wechat {
    color: #07c160;
  }

  &.apple {
    color: #1a1a1a;
  }
}

.menu-value.unbound {
  color: var(--home-text2);
  font-style: italic;
}

.menu-suffix.new-bind {
  color: var(--home-primary);
  font-weight: 500;
}

.danger-block {
  margin-top: 24rpx;
  padding-top: 16rpx;
}

.danger-title {
  display: block;
  font-size: 26rpx;
  color: var(--home-text2);
  margin-bottom: 20rpx;
}

.logout-btn {
  text-align: center;
  padding: 28rpx;
  border-radius: 16rpx;
  background: transparent;
  border: 1rpx solid rgba(220, 38, 38, 0.35);
  margin-bottom: 20rpx;

  text {
    font-size: 30rpx;
    font-weight: 500;
    color: #b91c1c;
  }

  &:active {
    opacity: 0.85;
  }
}

.danger-btn {
  text-align: center;
  padding: 28rpx;
  border-radius: 16rpx;
  background: rgba(220, 38, 38, 0.08);
  border: 1rpx solid rgba(220, 38, 38, 0.35);

  text {
    font-size: 30rpx;
    font-weight: 500;
    color: #b91c1c;
  }

  &:active {
    opacity: 0.85;
  }
}

/* 注销验证码弹层 */
.captcha-mask {
  position: fixed;
  inset: 0;
  z-index: 999;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
}

.captcha-modal {
  width: 600rpx;
  background: #fff;
  border-radius: 20rpx;
  padding: 40rpx 32rpx 32rpx;
  box-sizing: border-box;
}

.captcha-modal-title {
  display: block;
  font-size: 34rpx;
  font-weight: 600;
  color: var(--home-text1);
  text-align: center;
}

.captcha-modal-desc {
  display: block;
  font-size: 26rpx;
  color: var(--home-text2);
  text-align: center;
  margin: 16rpx 0 32rpx;
}

.captcha-row {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.captcha-input {
  flex: 1;
  height: 84rpx;
  padding: 0 24rpx;
  border: 1rpx solid rgba(0, 0, 0, 0.12);
  border-radius: 12rpx;
  font-size: 28rpx;
  box-sizing: border-box;
}

.captcha-image {
  width: 200rpx;
  height: 84rpx;
  border-radius: 12rpx;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f5;
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
  font-size: 22rpx;
  color: var(--home-text2);
}

.captcha-modal-actions {
  display: flex;
  gap: 20rpx;
  margin-top: 36rpx;
}

.captcha-btn {
  flex: 1;
  text-align: center;
  padding: 24rpx 0;
  border-radius: 12rpx;
  font-size: 28rpx;
  font-weight: 500;

  &--cancel {
    background: #f5f5f5;
    color: var(--home-text2);
  }

  &--danger {
    background: #b91c1c;
    color: #fff;
  }

  &:active {
    opacity: 0.85;
  }
}
</style>
