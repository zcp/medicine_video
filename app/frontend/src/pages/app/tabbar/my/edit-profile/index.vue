<template>
  <view class="page">
    <!-- 头像区域 - B站风格：居中 + 相机角标 -->
    <!-- 点击头像 → 预览；点击相机角标 → 更换 -->
    <view class="avatar-section">
      <view class="avatar-wrap" @tap="openPreview">
        <!-- 默认灰色圆形底，始终可见 -->
        <view class="avatar-placeholder" v-if="!authStore.user?.avatar">
          <text class="iconfont icon-my avatar-default-icon"></text>
        </view>
        <image v-else class="avatar-img" :src="displayAvatar" mode="aspectFill" />
        <view class="avatar-camera-badge" @tap.stop="handleChooseAvatar">
          <text class="iconfont icon-edit camera-icon"></text>
        </view>
      </view>
    </view>

    <!-- 基础资料 -->
    <view class="setting-section">
      <view class="section-title">基础资料</view>
      <view class="setting-card">
        <!-- 昵称 -->
        <view class="setting-row">
          <text class="setting-label">昵称</text>
          <view class="setting-value-wrap">
            <input
              v-model="form.nickname"
              class="setting-input"
              placeholder="请输入昵称"
              placeholder-class="input-placeholder"
              maxlength="50"
              @input="errors.nickname = ''"
            />
          </view>
        </view>
        <text v-if="errors.nickname" class="error-text">{{ errors.nickname }}</text>

        <view class="setting-divider" />

        <!-- 简介 -->
        <view class="setting-row setting-row--bio">
          <text class="setting-label">简介</text>
          <view class="setting-value-wrap">
            <textarea
              v-model="form.bio"
              class="setting-textarea"
              placeholder="介绍一下自己吧～"
              placeholder-class="input-placeholder"
              maxlength="200"
              :auto-height="true"
            />
          </view>
        </view>
      </view>
    </view>

    <!-- 账号信息（只读，绑定/换绑请前往账号与安全） -->
    <view class="setting-section">
      <view class="section-title">账号信息</view>
      <view class="setting-card">
        <!-- 用户ID -->
        <view class="setting-row" @tap="handleCopyUid">
          <text class="setting-label">用户ID</text>
          <view class="setting-value-wrap">
            <text class="setting-value uid-text">{{ authStore.user?.user_id || '-' }}</text>
          </view>
        </view>

        <view class="setting-divider" />

        <!-- 手机号 -->
        <view class="setting-row" @tap="goAccountSecurity">
          <text class="setting-label">手机号</text>
          <view class="setting-value-wrap">
            <text class="setting-value">{{ phoneDisplay }}</text>
            <text
              v-if="hasPhone"
              class="iconfont eye-icon"
              :class="revealPhone ? 'icon-eye-slash' : 'icon-eye'"
              @tap.stop="togglePhone"
            ></text>
            <text class="setting-suffix">{{ hasPhone ? '换绑' : '去绑定' }}</text>
            <text class="iconfont icon-arrow-right setting-arrow"></text>
          </view>
        </view>

        <view class="setting-divider" />

        <!-- 邮箱 -->
        <view class="setting-row" @tap="goAccountSecurity">
          <text class="setting-label">邮箱</text>
          <view class="setting-value-wrap">
            <text class="setting-value">{{ emailDisplay }}</text>
            <text
              v-if="hasEmail"
              class="iconfont eye-icon"
              :class="revealEmail ? 'icon-eye-slash' : 'icon-eye'"
              @tap.stop="toggleEmail"
            ></text>
            <text class="setting-suffix">{{ hasEmail ? '换绑' : '去绑定' }}</text>
            <text class="iconfont icon-arrow-right setting-arrow"></text>
          </view>
        </view>
      </view>
      <view class="section-tip">手机号 / 邮箱的绑定与换绑，请前往「账号与安全」</view>
    </view>

    <!-- 保存按钮 -->
    <view class="save-section">
      <button
        class="save-btn"
        :disabled="submitting"
        :class="{ 'save-btn--disabled': submitting }"
        @tap="handleSave"
      >{{ submitting ? '保存中…' : '保存' }}</button>
    </view>

    <AvatarPreview v-model:visible="previewVisible" :src="displayAvatar" @change-avatar="handleChooseAvatar" />
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import { useAuthStore } from '@/store/auth';
import { updateProfile } from '@/api/auth';
import AvatarPreview from '@/components/shared/AvatarPreview.vue';
import { resolveMediaUrl } from '@/utils/url';
import { maskPhone, maskEmail } from '@/utils/userDisplay';

const authStore = useAuthStore();

const form = ref({ nickname: '', bio: '' });
const errors = ref({ nickname: '' });
const submitting = ref(false);
const previewVisible = ref(false);
const choosingAvatar = ref(false);
const revealPhone = ref(false);
const revealEmail = ref(false);

const hasPhone = computed(() => !!authStore.user?.phone_number);
const hasEmail = computed(() => !!authStore.user?.email);

const phoneDisplay = computed(() => {
  if (!hasPhone.value) return '未绑定';
  const phone = authStore.user!.phone_number!;
  return revealPhone.value ? phone : maskPhone(phone);
});

const emailDisplay = computed(() => {
  if (!hasEmail.value) return '未绑定';
  const email = authStore.user!.email!;
  return revealEmail.value ? email : maskEmail(email);
});

const displayAvatar = computed(() => {
  const avatar = authStore.user?.avatar;
  if (!avatar) return '/static/tabbar/my.png';
  return resolveMediaUrl(avatar) || avatar;
});

onShow(async () => {
  if (!authStore.isAuthenticated) {
    uni.showToast({ title: '请先登录', icon: 'none' });
    uni.navigateBack({
      fail: () => { uni.switchTab({ url: '/pages/app/tabbar/home/index' }); }
    });
    return;
  }
  revealPhone.value = false;
  revealEmail.value = false;
  try {
    await authStore.fetchUserProfile();
  } catch {
    /* 忽略，展示已有缓存 */
  }
  form.value.nickname = authStore.user?.nickname || authStore.user?.username || '';
  form.value.bio = authStore.user?.bio || '';
  errors.value.nickname = '';
});

function togglePhone() {
  revealPhone.value = !revealPhone.value;
}

function toggleEmail() {
  revealEmail.value = !revealEmail.value;
}

function goAccountSecurity() {
  uni.navigateTo({
    url: '/pages/app/tabbar/my/account-security/index'
  });
}

function handleCopyUid() {
  const id = authStore.user?.user_id;
  if (!id) {
    uni.showToast({ title: '暂无用户ID', icon: 'none' });
    return;
  }
  uni.setClipboardData({
    data: id,
    success: () => uni.showToast({ title: '已复制', icon: 'none' })
  });
}

function openPreview() {
  previewVisible.value = true;
}

function handleChooseAvatar() {
  if (choosingAvatar.value) return;
  choosingAvatar.value = true;
  console.log('[avatar] choose image start');
  uni.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success(res) {
      const filePath = res.tempFilePaths?.[0];
      console.log('[avatar] choose image success', { filePath });
      if (!filePath) {
        uni.showToast({ title: '未获取到图片路径', icon: 'none' });
        return;
      }
      setTimeout(() => {
        uni.navigateTo({
          url: `/pages/app/tabbar/my/avatar-crop/index?src=${encodeURIComponent(filePath)}`,
          fail(err: any) {
            console.error('[avatar] navigate to crop failed', err);
            uni.showToast({ title: '无法进入裁剪页', icon: 'none' });
          }
        });
      }, 50);
    },
    fail(err: any) {
      console.error('[avatar] choose image fail', err);
    },
    complete() {
      choosingAvatar.value = false;
    }
  });
}

async function handleSave() {
  if (submitting.value) return;

  errors.value.nickname = '';
  const nick = form.value.nickname.trim();
  if (!nick) {
    errors.value.nickname = '昵称不能为空';
    return;
  }

  submitting.value = true;
  try {
    const payload: { nickname: string; bio?: string; avatar_url?: string } = {
      nickname: nick,
    };

    const bioVal = form.value.bio.trim();
    if (bioVal) payload.bio = bioVal;

    const res = await updateProfile(payload);
    console.log('[edit-profile] updateProfile response', res);
    if (res.code !== 200) {
      uni.showToast({ title: res.message || '保存失败', icon: 'none' });
      return;
    }

    await authStore.fetchUserProfile();
    console.log('[edit-profile] avatar after fetch', authStore.user?.avatar);
    uni.showToast({ title: '保存成功', icon: 'success' });
    setTimeout(() => uni.navigateBack(), 800);
  } catch (e: any) {
    const msg = e?.message || '保存失败，请重试';
    uni.showToast({ title: msg.length > 20 ? msg.slice(0, 20) + '…' : msg, icon: 'none' });
  } finally {
    submitting.value = false;
  }
}
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.page {
  min-height: 100vh;
  background: $color-surface-page;
  padding-bottom: 60rpx;
}

// ===== 头像区域 - B站风格：居中 + 相机角标 =====
.avatar-section {
  display: flex;
  justify-content: center;
  padding: 80rpx 0 $spacing-xl;
}

.avatar-wrap {
  position: relative;
  width: 180rpx;
  height: 180rpx;

  &:active {
    opacity: 0.88;
  }
}

.avatar-img {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  overflow: hidden;
}

// 默认占位圆圈：灰色底+人像图标，始终可见
.avatar-placeholder {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: #e5e7eb;  // 灰色底，确保圆圈始终可见
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-default-icon {
  font-size: 64rpx;
  color: #9ca3af;  // 灰色图标，与背景有对比但不突兀
}

.avatar-camera-badge {
  position: absolute;
  right: -4rpx;
  bottom: -4rpx;
  width: 52rpx;
  height: 52rpx;
  border-radius: 50%;
  background: $color-primary;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.15);
}

.camera-icon {
  font-size: 26rpx;
  color: #fff;
}

// ===== 设置分组 =====
.setting-section {
  margin-top: $spacing-2xl;
}

.section-title {
  font-size: $font-sm;
  color: $color-text-tertiary;
  padding: 0 $spacing-2xl $spacing-sm;
}

.setting-card {
  margin: 0 $spacing-xl;
  background: $color-surface-card;
  border-radius: $radius-md;
  overflow: hidden;
}

.setting-row {
  display: flex;
  align-items: center;
  min-height: 96rpx;
  padding: $spacing-lg $spacing-xl;
  box-sizing: border-box;

  &--bio {
    align-items: flex-start;
    padding-top: $spacing-lg;
    padding-bottom: $spacing-lg;
  }

  &:active {
    background: rgba(0, 0, 0, 0.02);
  }
}

.setting-label {
  font-size: $font-md;
  color: $color-text-primary;
  flex-shrink: 0;
  width: 140rpx;

  &--primary {
    color: $color-primary;
    font-weight: 600;
  }
}

.setting-value-wrap {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: flex-end;
}

.setting-value {
  font-size: $font-md;
  color: $color-text-tertiary;
  text-align: right;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.uid-text {
  color: $color-text-primary;
}

.eye-icon {
  font-size: 32rpx;
  color: $color-text-tertiary;
  margin-left: $spacing-sm;
  flex-shrink: 0;
  padding: 8rpx;

  &:active {
    color: $color-primary;
  }
}

.setting-suffix {
  font-size: $font-sm;
  color: $color-primary;
  margin-left: $spacing-sm;
  flex-shrink: 0;
}

.section-tip {
  padding: $spacing-md $spacing-2xl 0;
  font-size: $font-xs;
  color: $color-text-tertiary;
}

.setting-input {
  flex: 1;
  font-size: $font-md;
  color: $color-text-primary;
  text-align: right;
  height: 48rpx;
  background: transparent;
}

.setting-textarea {
  flex: 1;
  font-size: $font-sm;
  color: $color-text-primary;
  text-align: right;
  min-height: 64rpx;
  line-height: 1.5;
  background: transparent;
}

.setting-arrow {
  font-size: 24rpx;
  color: $color-text-tertiary;
  margin-left: $spacing-sm;
}

.setting-divider {
  height: 1rpx;
  background: $color-border-divider;
  margin: 0 $spacing-xl;
}

.error-text {
  display: block;
  padding: 0 $spacing-xl $spacing-sm;
  font-size: $font-xs;
  color: $color-state-error;
}

.input-placeholder {
  color: $color-text-tertiary;
  font-size: $font-md;
}

// ===== 保存按钮 =====
.save-section {
  margin: $spacing-3xl $spacing-xl 0;
}

.save-btn {
  width: 100%;
  height: 96rpx;
  background: $color-primary;
  border-radius: 48rpx;
  border: none;
  font-size: $font-xl;
  font-weight: 600;
  color: $color-text-white;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: $shadow-button-primary;
  transition: opacity $motion-fast, transform $motion-fast;

  &--disabled {
    opacity: 0.6;
  }

  &:active:not(&--disabled) {
    opacity: 0.88;
    transform: scale(0.98);
  }
}
</style>
