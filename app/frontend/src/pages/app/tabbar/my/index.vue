<template>
  <view class="my-page consumer-layout">
    <!-- 用户信息卡片：克制主色点缀，无高饱和色块 -->
    <view class="user-card" :class="{ 'not-logged-in': !isAuthenticated }">
      <view v-if="isAuthenticated" class="user-info">
        <view class="avatar-wrap" @tap="handleAvatarClick">
          <view v-if="!authStore.user?.avatar" class="avatar-placeholder">
            <text class="iconfont icon-my avatar-default-icon"></text>
          </view>
          <image v-else class="avatar" :src="userAvatar" mode="aspectFill" @error="handleAvatarError" @load="handleAvatarLoad" />
        </view>
        <view class="user-main">
          <view class="user-row user-row--head">
            <view class="nickname-row">
              <text
                class="nickname"
                :class="{ 'nickname--muted': isNicknamePlaceholder }"
              >{{ displayNickname }}</text>
              <view class="edit-btn" @click="handleEditProfile">
                <text class="iconfont icon-edit"></text>
              </view>
            </view>
          </view>
          <view class="user-row user-row--pills">
            <view class="pill pill--status" :class="statusPillClass">
              <text v-if="showStatusCheck" class="pill-status-icon">✓</text>
              <text>{{ statusLabel }}</text>
            </view>
          </view>
          <view class="user-row user-row--bio">
            <text
              class="bio-text"
              :class="{ 'bio-text--placeholder': !hasBioContent }"
            >{{ bioDisplay }}</text>
          </view>
        </view>
      </view>
      <view v-else class="login-prompt" @click="handleLogin">
        <view class="avatar-wrap">
          <view class="avatar-placeholder">
            <text class="iconfont icon-my avatar-default-icon"></text>
          </view>
        </view>
        <view class="login-text">
          <text class="title">点击登录</text>
          <text class="subtitle">登录后享受更多功能</text>
        </view>
      </view>
    </view>

    <!-- 快捷功能区：Icon + 数值 + 文案，点击高度 ≥ 88rpx -->
    <view v-if="!authStore.isAdmin" class="quick-actions">
      <view
        v-for="action in quickActions"
        :key="action.key"
        class="action-item"
        @click="handleQuickAction(action)"
      >
        <view class="icon-wrapper">
          <text class="iconfont quick-icon" :class="action.icon"></text>
          <view v-if="action.badge > 0" class="badge-count">{{ action.badge > 99 ? '99+' : action.badge }}</view>
        </view>
        <text class="action-label">{{ action.label }}</text>
      </view>
    </view>

    <!-- 直播管理区：分组用 spacing，列表行统一（管理员无 owner 房，整区隐藏，统一走全站房间） -->
    <view v-if="!authStore.isAdmin" class="menu-section">
      <view class="section-title">直播管理</view>
      <view class="menu-list">
        <view class="menu-item row" @click="handleMyLive">
          <text class="iconfont icon-video"></text>
          <text class="menu-label">我的直播</text>
          <text class="iconfont icon-arrow-right"></text>
        </view>
        <view class="menu-item row" @click="handleCreateLive">
          <text class="iconfont icon-add"></text>
          <text class="menu-label">创建直播</text>
          <text class="iconfont icon-arrow-right"></text>
        </view>
      </view>
    </view>

    <!-- 管理功能区（仅管理员可见） -->
    <view v-if="authStore.isAdmin" class="menu-section">
      <view class="section-title">管理功能</view>
      <view class="menu-list">
        <view class="menu-item row" @click="handleAdminNav('users')">
          <text class="iconfont icon-my"></text>
          <text class="menu-label">用户管理</text>
          <text class="iconfont icon-arrow-right"></text>
        </view>
        <view class="menu-item row" @click="handleAdminNav('rooms')">
          <text class="iconfont icon-video"></text>
          <text class="menu-label">全站房间</text>
          <text class="iconfont icon-arrow-right"></text>
        </view>
        <view class="menu-item row" @click="handleAdminNav('departments')">
          <text class="iconfont icon-category"></text>
          <text class="menu-label">科室分类管理</text>
          <text class="iconfont icon-arrow-right"></text>
        </view>
        <view class="menu-item row" @click="handleAdminNav('experts')">
          <text class="iconfont icon-expert"></text>
          <text class="menu-label">专家管理</text>
          <text class="iconfont icon-arrow-right"></text>
        </view>
        <view class="menu-item row" @click="handleAdminNav('notification')">
          <text class="iconfont icon-bell"></text>
          <text class="menu-label">推送通知</text>
          <text class="iconfont icon-arrow-right"></text>
        </view>
        <view class="menu-item row" @click="handleAdminNav('featured')">
          <text class="iconfont icon-star-outline"></text>
          <text class="menu-label">焦点图管理</text>
          <text class="iconfont icon-arrow-right"></text>
        </view>
        <view class="menu-item row" @click="handleAdminNav('tags')">
          <text class="iconfont icon-tag"></text>
          <text class="menu-label">标签管理</text>
          <text class="iconfont icon-arrow-right"></text>
        </view>
        <view class="menu-item row" @click="handleAdminNav('brands')">
          <text class="iconfont icon-brand"></text>
          <text class="menu-label">品牌管理</text>
          <text class="iconfont icon-arrow-right"></text>
        </view>
        <view class="menu-item row" @click="handleAdminNav('messages')">
          <text class="iconfont icon-message"></text>
          <text class="menu-label">留言管理</text>
          <text class="iconfont icon-arrow-right"></text>
        </view>
        <view class="menu-item row" @click="handleAdminNav('contentSafety')">
          <text class="iconfont icon-shield"></text>
          <text class="menu-label">内容安全管理</text>
          <text class="iconfont icon-arrow-right"></text>
        </view>
      </view>
    </view>

    <!-- 更多服务区 -->
    <view class="menu-section">
      <view class="section-title">更多服务</view>
      <view class="menu-list">
        <view class="menu-item row" @click="handleSettings">
          <text class="iconfont icon-setting"></text>
          <text class="menu-label">设置</text>
          <text class="iconfont icon-arrow-right"></text>
        </view>
      </view>
    </view>

    <view class="version-info" @click="handleVersionClick">
      <text>版本号 v1.0.0</text>
    </view>

    <CustomTabBar :current="3" />
    <AvatarPreview v-model:visible="previewVisible" :src="userAvatar" @change-avatar="handleChangeAvatarFromPreview" />
  </view>
</template>



<script setup lang="ts">

/**

 * "我的"页面

 * @description 个人中心页面，包含用户信息、快捷功能、直播管理、设置等模块

 */

import { ref, computed, onMounted } from 'vue';

import { onShow } from '@dcloudio/uni-app';

import { useAuthStore } from '@/store/auth';

import { ENV_CONFIG } from '@/config/env';

import { getFavorites } from '@/api/favorite';

import { useFollowStore } from '@/store/follow';

import { mockUserStats } from './mock-data';

import CustomTabBar from '@/components/app/CustomTabBar.vue';

import AvatarPreview from '@/components/shared/AvatarPreview.vue';

import { mapStatusLabel, mapStatusTone } from '@/utils/userDisplay';
import { resolveMediaUrl } from '@/utils/url';



// ========== Store ==========

const authStore = useAuthStore();

const followStore = useFollowStore();



// ========== 响应式数据 ==========

/** 头像预览状态 */
const previewVisible = ref(false);

/** 用户统计数据 */

const userStats = ref({

  favorites_count: 0,

  follow_count: 0,

});



// ========== 计算属性 ==========

/** 🔴 P0: 是否已登录（从Store获取真实状态） */

const isAuthenticated = computed(() => authStore.isAuthenticated);



/** 🔴 P0: 用户头像（优先使用用户真实头像） */

const userAvatar = computed(() => {

  if (!authStore.user?.avatar) {

    return '/static/tabbar/my.png';

  }

  return resolveMediaUrl(authStore.user.avatar) || authStore.user.avatar;

});



/** 展示昵称：优先 nickname → username → email；加载中与「无展示名」区分，避免误显示「用户」 */

const displayNickname = computed(() => {

  if (!authStore.user) {

    if (authStore.isAuthenticated) return '加载中…';

    return '';

  }

  const raw = authStore.user.nickname || authStore.user.username || authStore.user.email;

  if (!raw || !String(raw).trim()) return '未命名用户';

  const s = String(raw).trim();

  return s.length > 18 ? s.slice(0, 18) + '…' : s;

});



const isNicknamePlaceholder = computed(() => {

  const v = displayNickname.value;

  return v === '加载中…' || v === '未命名用户';

});



/** 状态为「正常」时在标签前展示对勾，与身份标签区分 */

const showStatusCheck = computed(() => authStore.user?.status === 'NORMAL');



const hasBioContent = computed(() => {

  const b = authStore.user?.bio;

  return !!(b && String(b).trim());

});



const bioDisplay = computed(() => {

  if (hasBioContent.value && authStore.user?.bio) return String(authStore.user.bio).trim();

  return '还没有写简介～快来介绍一下自己吧！';

});



const statusLabel = computed(() => mapStatusLabel(authStore.user?.status));



const statusPillClass = computed(() => {

  const tone = mapStatusTone(authStore.user?.status);

  return `pill--st-${tone}`;

});

// ========== 快捷功能配置 ==========

/** 快捷功能区配置 - 使用动态badge数据 */

interface QuickAction {

  key: string;

  icon: string;

  label: string;

  badge: number;

  path: string;

  requireAuth: boolean;

}



const quickActions = computed<QuickAction[]>(() => [

  { 

    key: 'favorites', 

    icon: 'icon-star-outline', 

    label: '收藏', 

    badge: 0, 

    path: '/pages/app/tabbar/my/favorites/index', 

    requireAuth: true 

  },

  { 

    key: 'follow', 

    icon: 'icon-heart', 

    label: '关注', 

    badge: 0, 

    path: '/pages/app/tabbar/my/follows/index', 

    requireAuth: true 

  },

  { 

    key: 'watch-history', 

    icon: 'icon-history', 

    label: '观看历史', 

    badge: 0, 

    path: '/pages/app/tabbar/my/watch-history/index', 

    requireAuth: true 

  },

  { 

    key: 'subscriptions', 

    icon: 'icon-sub-outline', 

    label: '订阅', 

    badge: 0, 

    path: '/pages/app/tabbar/my/subscriptions/index', 

    requireAuth: true 

  },

  { 

    key: 'notifications', 

    icon: 'icon-bell', 

    label: '通知', 

    badge: 0, 

    path: '/pages/app/notifications/index', 

    requireAuth: true 

  },

]);



// ========== 数据获取函数（Mock/API切换） ==========



/**

 * 获取用户统计数据

 * @description 与首页保持一致的Mock/API切换模式

 */

async function fetchUserStats() {

  // Mock模式：使用本地数据

  if (ENV_CONFIG.VITE_USE_MOCK) {

    return mockUserStats;

  }

  

  // 真实API模式：调用后端接口

  try {

    const favRes = await getFavorites({ page: 1, size: 1 });

    

    return {

      favorites_count: favRes.data?.total || 0,

      follow_count: followStore.followCount || 0,

    };

  } catch (error) {

    console.error('获取用户统计数据失败:', error);

    // 失败时降级到Mock数据

    return mockUserStats;

  }

}



/**

 * 加载用户数据（登录后调用：统计等；个人信息来自 authStore + GET /users/me）

 */

async function loadUserData() {

  if (!isAuthenticated.value) return;

  const stats = await fetchUserStats();

  userStats.value = stats;

}



// ========== 生命周期 ==========

onMounted(async () => {

  console.log('📱 "我的"页面加载');

  await loadUserData();

});



onShow(async () => {

  console.log('👀 "我的"页面显示');

  // 每次显示页面时刷新数据

  await loadUserData();

  // 🔴 P0: 如果用户已登录但没有用户信息，尝试获取

  if (authStore.isAuthenticated && !authStore.user) {

    console.log('🔄 检测到已登录但缺少用户信息，尝试获取...');

    try {

      await authStore.fetchUserProfile();

      console.log('✅ 用户信息补充成功');

      // 重新加载页面数据

      await loadUserData();

    } catch (error) {

      console.error('❌ 获取用户信息失败:', error);

    }

  }

});



// ========== 事件处理方法 ==========



/**

 * 需要登录的操作统一使用此函数

 */

function requireAuth(callback: () => void) {

  if (!isAuthenticated.value) {

    uni.showToast({ title: '请先登录', icon: 'none' });

    return;

  }

  callback();

}



/**

 * 格式化badge数量（超过99显示99+）

 */

function formatBadge(count: number): string {

  return count > 99 ? '99+' : String(count);

}



/**

 * 🔴 P0: 处理登录点击（记录来源页面）

 */

function handleLogin() {

  console.log('🔄 跳转到登录页面，记录来源页面');

  

  // 记录当前页面作为登录后的回跳目标

  uni.setStorageSync('loginRedirectPath', '/pages/app/tabbar/my/index');

  

  uni.navigateTo({

    url: '/pages/app/auth/login'

  });

}



/**

 * 处理编辑资料

 */

function handleEditProfile() {

  requireAuth(() => {

    uni.navigateTo({ url: '/pages/app/tabbar/my/edit-profile/index' });

  });

}



/**

 * 处理头像预览

 */

function handleAvatarClick() {

  requireAuth(() => {

    console.log('[我的页面] 🖼️ 点击头像预览, userAvatar:', userAvatar.value);
    previewVisible.value = true;

  });

}

function handleAvatarLoad(e: any) {
  console.log('[我的页面] ✅ 头像加载成功:', { src: userAvatar.value, detail: e.detail });
}

function handleAvatarError(e: any) {
  console.error('[我的页面] ❌ 头像加载失败:', { src: userAvatar.value, errMsg: e?.detail?.errMsg || '未知错误', detail: e?.detail });
}

/**
 * 预览页"更换头像" → 跳转编辑资料页
 */
function handleChangeAvatarFromPreview() {
  uni.navigateTo({ url: '/pages/app/tabbar/my/edit-profile/index' });
}



/**

 * 处理快捷功能点击

 */

function handleQuickAction(action: QuickAction) {

  if (action.requireAuth) {

    requireAuth(() => {

      uni.navigateTo({ url: action.path });

    });

  } else {

    uni.navigateTo({ url: action.path });

  }

}



/**

 * 处理我的直播

 */

function handleMyLive() {

  requireAuth(() => {

    uni.navigateTo({ url: '/pages/app/live-manage/list' });

  });

}



/**

 * 处理创建直播

 */

function handleCreateLive() {

  requireAuth(() => {

    uni.navigateTo({ url: '/pages/app/live-manage/create' });

  });

}



/** 管理面板导航（页面未实现时提示） */

function handleAdminNav(page: string) {
  const adminRoutes: Record<string, string> = {
    users: "/pages/app/admin/users/index",
    rooms: "/pages/app/live-manage/list?mode=admin",
    departments: "/pages/app/admin/departments/index",
    experts: "/pages/app/admin/expert-list/index",
    notification: "/pages/app/admin/notification-push/index",
    featured: "/pages/app/admin/featured/index",
    tags: "/pages/app/admin/tags/index",
    brands: "/pages/app/admin/brands/index",
    messages: "/pages/app/admin/messages/index",
    contentSafety: "/pages/app/admin/content-safety/index",
  };
  const targetUrl = adminRoutes[page];
  if (!targetUrl) {
    uni.showToast({ title: "页面不存在", icon: "none" });
    return;
  }
  uni.navigateTo({
    url: targetUrl,
    fail: () => {
      uni.showToast({ title: "功能开发中", icon: "none" });
    },
  });
}


/**
 * 处理设置入口（跳转到设置页）
 */
function handleSettings() {
  uni.navigateTo({ url: '/pages/app/tabbar/my/settings/index' });
}



/**
 
 * 🔧 开发者调试：点击版本号计数器

 * @description 连续点击5次进入认证状态诊断页面

 */

let versionClickCount = 0;

let versionClickTimer: number | null = null;



function handleVersionClick() {

  versionClickCount++;

  

  if (versionClickTimer) {

    clearTimeout(versionClickTimer);

  }

  

  if (versionClickCount >= 5) {

    console.log('🔧 [开发者] 进入认证诊断页面');

    uni.navigateTo({

      url: '/pages/app/debug/auth-status'

    });

    versionClickCount = 0;

  } else {

    versionClickTimer = setTimeout(() => {

      versionClickCount = 0;

    }, 2000) as unknown as number;

  }

}

</script>



<style lang="scss" scoped>

.my-page.consumer-layout {

  min-height: 100vh;

  background-color: var(--home-bg);

  padding: 0 var(--home-spacing-page) var(--home-spacing-page);

  padding-bottom: 140rpx;

}



/* 用户信息区：个人资料摘要，轻量主色点缀，无整块卡片框 */

.user-card {

  background: var(--home-profile-bg);

  padding: 24rpx 4rpx 20rpx;

  margin-bottom: var(--home-spacing-module);

  border-radius: var(--home-r-md);

  

  &.not-logged-in {

    background: var(--home-profile-bg-muted);

  }

}



.user-info {

  display: flex;

  align-items: flex-start;

}



.avatar-wrap {

  flex-shrink: 0;

  width: 120rpx;

  height: 120rpx;

  border-radius: var(--radius-circle);

  padding: 3rpx;

  background: var(--home-card);

  border: 2rpx solid var(--color-primary-light-1);

  box-sizing: border-box;

  box-shadow: var(--home-fab-shadow);

  .user-card.not-logged-in & {

    background: var(--home-card);

    border-color: var(--home-border);

    box-shadow: var(--home-shadow-card);

  }

}



.avatar {

  width: 100%;

  height: 100%;

  border-radius: var(--radius-circle);

  display: block;

  background: var(--home-action-secondary-bg);

  

  &.default {

    opacity: 0.9;

  }

}



.user-main {

  flex: 1;

  margin-left: 20rpx;

  min-width: 0;

  display: flex;

  flex-direction: column;

  gap: 12rpx;

}



.user-row--head {

  width: 100%;

}



.nickname-row {

  display: flex;

  align-items: center;

}



.nickname {

  font-size: 32rpx;

  font-weight: 600;

  color: var(--home-text1);

}



.nickname--muted {

  font-weight: 500;

  color: var(--home-text2);

}



.edit-btn {

  /* 触控热区 ≥44px：88rpx 方形透明热区，负 margin 抵消，不改变行视觉布局（零 layout shift） */

  display: flex;

  align-items: center;

  justify-content: center;

  width: 88rpx;

  height: 88rpx;

  margin: -24rpx -44rpx -24rpx 8rpx;

  border-radius: var(--radius-circle);

  transition: opacity var(--transition-base);

  

  .iconfont {

    font-size: 30rpx;

    color: var(--home-primary);

  }

  

  &:active {

    opacity: 0.6;

  }

  

  @media (hover: hover) {

    &:hover {

      opacity: 0.85;

    }

  }

}



.user-row--pills {

  display: flex;

  flex-wrap: wrap;

  align-items: center;

  gap: 10rpx;

}



.pill {

  padding: 4rpx 14rpx;

  border-radius: 999rpx;

  font-size: 20rpx;

  line-height: 1.25;

}



/* 身份：中性灰蓝，与状态绿区分 */

.pill--status {


  font-weight: 500;

  display: inline-flex;

  align-items: center;

  gap: 6rpx;

}



.pill-status-icon {

  font-size: 18rpx;

  font-weight: 700;

  opacity: 0.95;

}



.pill--st-normal {

  background: var(--home-badge-verified-bg);

  color: var(--home-badge-verified-text);

}



.pill--st-warning {

  background: var(--home-badge-pending-bg);

  color: var(--home-badge-pending-text);

}



.pill--st-danger {

  background: var(--home-badge-danger-bg);

  color: var(--home-badge-danger-text);

}



.pill--st-muted {

  background: var(--home-badge-muted-bg);

  color: var(--home-badge-muted-text);

}



.user-row--bio {


  width: 100%;

  opacity: 0.98;

}



.bio-text {

  display: -webkit-box;

  -webkit-box-orient: vertical;

  -webkit-line-clamp: 2;

  overflow: hidden;

  font-size: 22rpx;

  color: var(--home-text2);

  line-height: 1.4;

}



.bio-text--placeholder {

  font-style: italic;

  color: var(--color-text-placeholder);

}



.login-prompt {

  display: flex;

  align-items: center;

}



.login-text {

  margin-left: 32rpx;

  

  .title {

    display: block;

    font-size: 36rpx;

    font-weight: 600;

    color: var(--home-text1);

  }

  

  .subtitle {

    display: block;

    font-size: 26rpx;

    color: var(--home-text2);

    margin-top: 8rpx;

  }

}



/* 快捷功能区：去卡片化，通栏 + spacing */

.quick-actions {

  display: flex;

  justify-content: space-around;

  padding: 32rpx 0;

  margin-bottom: var(--home-spacing-module);

}



.action-item {

  display: flex;

  flex-direction: column;

  align-items: center;

  justify-content: flex-start;

  min-width: 100rpx;

  min-height: 88rpx;

  padding-top: 16rpx;

  padding-bottom: 16rpx;

  box-sizing: border-box;

  transition: opacity var(--transition-base), transform var(--transition-base);

  

  &:active {

    opacity: 0.75;

    transform: scale(0.94);

  }

  

  @media (hover: hover) {

    &:hover {

      opacity: 0.88;

    }

  }

}



.icon-wrapper {

  position: relative;

  width: 88rpx;

  height: 88rpx;

  min-width: 88rpx;

  min-height: 88rpx;

  display: flex;

  align-items: center;

  justify-content: center;

  background: var(--color-primary-light-1);

  border: 2rpx solid var(--color-primary-light-1);

  border-radius: var(--radius-circle);

  margin-bottom: 10rpx;

  

  .quick-icon.iconfont {

    font-size: 44rpx;

    color: var(--home-primary);

  }

}



.badge-count {

  position: absolute;

  top: 0;

  right: 0;

  min-width: 36rpx;

  height: 36rpx;

  padding: 0 8rpx;

  background-color: var(--home-primary);

  border-radius: 18rpx;

  font-size: 20rpx;

  color: var(--color-text-on-primary);

  font-weight: 500;

  display: flex;

  align-items: center;

  justify-content: center;

  border: 3rpx solid var(--home-card);

  box-shadow: var(--home-fab-shadow);

}



// 小红点样式（通知用）

.badge-dot {

  position: absolute;

  top: 4rpx;

  right: 4rpx;

  width: 16rpx;

  height: 16rpx;

  background-color: var(--color-danger);

  border-radius: 50%;

  border: 2rpx solid var(--home-card);

}



.action-count {

  font-size: 22rpx;

  color: var(--home-primary);

  font-weight: 500;

  margin-bottom: 2rpx;

  min-height: 28rpx;

  line-height: 1.2;

}



.action-label {

  font-size: 24rpx;

  color: var(--home-text2);

}



/* 菜单区域：去卡片化，通栏 + spacing 分组，divider 极浅 */

.menu-section {

  margin-bottom: var(--home-spacing-module);

}



.section-title {

  padding: 16rpx 0 12rpx;

  font-size: 24rpx;

  font-weight: 500;

  letter-spacing: 2rpx;

  color: var(--home-text2);

}



.menu-list {

  padding: 0;

}



.menu-item {

  display: flex;

  align-items: center;

  min-height: 88rpx;

  padding: 24rpx 0;

  border-bottom: 1rpx solid var(--home-divider);

  transition: background-color var(--transition-base), opacity var(--transition-base);

  

  &:last-child {

    border-bottom: none;

  }

  

  &:active {

    opacity: 0.7;

  }

  

  @media (hover: hover) {

    &:hover {

      background-color: var(--home-action-secondary-bg);

    }

  }

  

  .iconfont {

    font-size: 40rpx;

    color: var(--home-text2);

    

    &.icon-arrow-right {

      font-size: 28rpx;

      color: var(--home-text2);

    }

  }

  

  .menu-label {

    flex: 1;

    margin-left: 24rpx;

    font-size: var(--home-fs-card-title, 30rpx);

    color: var(--home-text1);

  }

  

  switch {

    transform: scale(0.85);

  }

}



/* 版本号 */

.version-info {

  text-align: center;

  padding: 8rpx 0;

  padding-bottom: 40rpx;

  transition: opacity var(--transition-base);

  

  &:active {

    opacity: 0.6;

  }

  

  text {

    font-size: var(--home-fs-meta, 24rpx);

    color: var(--home-text2);

  }

}

.avatar-placeholder {
  width: 100%;
  height: 100%;
  border-radius: var(--radius-circle);
  background: var(--home-border);
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-default-icon {
  font-size: 64rpx;
  color: var(--color-text-placeholder);
}

</style>
