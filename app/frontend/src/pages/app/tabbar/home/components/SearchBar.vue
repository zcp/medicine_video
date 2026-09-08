<template>
  <view class="search-bar" :style="searchBarStyle">
    <!-- 左侧：游客显示登录入口，登录后显示头像 -->
    <view class="avatar-wrapper" @tap="handleAvatarClick">
      <view v-if="!authStore.isAuthenticated" class="login-entry">
        <text class="login-entry-text">登录</text>
      </view>
      <image
        v-else-if="avatarSrc && !avatarError"
        class="avatar-image"
        :src="avatarSrc"
        mode="aspectFill"
        @error="handleAvatarError"
      />
      <view v-else class="avatar-placeholder">
        <text class="iconfont icon-my avatar-default-icon"></text>
      </view>
    </view>

    <!-- 中间搜索框（伪输入框：叠加共享B站风格容器，点击跳转搜索页） -->
    <view class="app-search-field search-input-wrapper" @tap="handleSearchClick">
      <text class="search-icon iconfont icon-search"></text>
      <text class="search-placeholder">搜索直播 / 医生 / 医院</text>
    </view>

    <!-- 右侧消息图标 -->
    <view class="message-wrapper" @tap="handleMessageClick">
      <text class="message-icon iconfont icon-bell"></text>
      <view v-if="hasUnreadMessage" class="unread-dot" />
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * 顶部搜索栏组件
 * @description 固定在页面顶部，包含Logo、搜索框、消息入口
 */
import { ref, computed } from 'vue';
import { useAuthStore } from '@/store/auth';
import { APP_LOGIN_PATH } from '@/constants/routes';

const authStore = useAuthStore();

/** Props 定义 */
const props = withDefaults(defineProps<{
  /** 状态栏高度 */
  statusBarHeight?: number;
}>(), {
  statusBarHeight: 0,
});

/** 搜索栏样式 */
const searchBarStyle = computed(() => ({
  paddingTop: `${props.statusBarHeight}px`,
  height: `${props.statusBarHeight + 44}px`,
}));

/** 是否有未读消息 */
const hasUnreadMessage = ref(true);

/** 头像加载失败时显示默认图标 */
const avatarError = ref(false);

/** 用户头像（store 已通过 resolveMediaUrl 解析，此处直接使用） */
const avatarSrc = computed(() => {
  if (!authStore.isAuthenticated) return '';
  return authStore.user?.avatar || '';
});

/**
 * 头像/登录区域点击处理
 * @description 游客跳登录页，已登录可扩展为个人中心入口
 */
function handleAvatarClick(): void {
  if (!authStore.isAuthenticated) {
    uni.navigateTo({ url: APP_LOGIN_PATH });
  }
}

/**
 * 搜索框点击处理
 */
function handleSearchClick(): void {
  uni.navigateTo({ url: '/pages/app/search/index' });
}

/**
 * 消息图标点击处理
 */
function handleMessageClick(): void {
  uni.navigateTo({ url: '/pages/app/notifications/index' });
}

/**
 * 头像图片加载失败处理
 */
function handleAvatarError(): void {
  avatarError.value = true;
}
</script>

<style lang="scss" scoped>
.search-bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 999;
  display: flex;
  align-items: center;
  padding: 0 24rpx;
  background-color: var(--home-card);
  box-sizing: border-box;
}

.avatar-wrapper {
  min-width: 48rpx;
  height: 48rpx;
  margin-right: 16rpx;
  flex-shrink: 0;
}

.avatar-image {
  width: 48rpx;
  height: 48rpx;
  border-radius: 50%;
  background-color: var(--home-border);
}

.avatar-placeholder {
  width: 48rpx;
  height: 48rpx;
  border-radius: 50%;
  background-color: var(--home-border);
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-default-icon {
  font-size: 36rpx;
  color: var(--home-text2);
}

.login-entry {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 48rpx;
  height: 48rpx;
  padding: 0 8rpx;
  flex-shrink: 0;
  border-radius: var(--home-r-pill);

  &:active {
    opacity: 0.7;
  }
}

.login-entry-text {
  font-size: 26rpx;
  font-weight: 500;
  color: var(--home-primary);
}

/* 伪搜索框：叠加共享容器 .app-search-field（B站风格：白底+1rpx细边+胶囊）；
   高度覆盖 64rpx（导航栏档位）；辨识度兜底链（D3）：细边框起手，不足再加深/加轻阴影 */
.search-input-wrapper {
  flex: 1;
  height: 64rpx;
  box-sizing: border-box;

  /* 触控反馈：按压轻微变淡，不改变底色（保持白底细边最终态） */
  &:active {
    opacity: 0.7;
  }
}

.search-icon {
  font-size: 28rpx;
  color: var(--search-icon);
  margin-right: 12rpx;
}

.search-placeholder {
  font-size: 26rpx;
  color: var(--search-placeholder);
}

.message-icon {
  font-size: 40rpx;
  color: var(--home-text1);
  transition: color 0.2s ease;
}

.message-wrapper {
  position: relative;
  width: 48rpx;
  height: 48rpx;
  margin-left: 16rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border-radius: 50%;

  &:active {
    .message-icon {
      color: var(--home-primary);
    }
  }
}

.unread-dot {
  position: absolute;
  top: 4rpx;
  right: 4rpx;
  width: 16rpx;
  height: 16rpx;
  background-color: var(--color-danger);
  border-radius: 50%;
}
</style>
