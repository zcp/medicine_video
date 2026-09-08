<template>
  <view class="profile-page">
    <view class="hero" :class="{ 'is-guest': !isLoggedIn }" @tap="handleHeaderTap">
      <view class="hero__row">
        <view class="hero__avatar" aria-hidden="true">
          <image
            v-if="!avatarShowIcon"
            class="hero__avatar-img"
            :src="displayAvatar"
            mode="aspectFill"
            @error="onAvatarError"
          />
          <text v-else class="iconfont icon-yonghu"></text>
        </view>

        <view class="hero__info">
          <text class="hero__title">
            {{ isLoggedIn ? (userInfo?.nickname || '已登录用户') : '点击登录' }}
          </text>
          <text v-if="!isLoggedIn" class="hero__sub">登录后享受更多功能</text>
        </view>

        <view class="hero__action">
          <button v-if="isLoggedIn" class="ghost-btn" :disabled="submitting" @tap.stop="handleEditProfile">编辑</button>
          <button v-if="isLoggedIn" class="ghost-btn" :disabled="submitting" @tap.stop="handleLogout">退出</button>
          <uni-icons v-else type="right" size="18" :color="'var(--color-text-tertiary)'" />
        </view>
      </view>
    </view>

    <!-- 管理员不展示收藏等 C 端快捷入口 -->
    <view v-if="!isAdmin" class="card shortcuts-card">
      <view class="shortcuts" aria-label="常用入口">
        <view class="shortcut" role="button" aria-label="收藏" @tap="handleShortcut('favorites')">
          <image class="shortcut__img" src="/static/images/profile/favorite.svg" mode="aspectFit" />
          <text class="shortcut__text">收藏</text>
        </view>
        <view class="shortcut" role="button" aria-label="关注" @tap="handleShortcut('follow')">
          <image class="shortcut__img" src="/static/images/profile/follow.svg" mode="aspectFit" />
          <text class="shortcut__text">关注</text>
        </view>
        <view class="shortcut" role="button" aria-label="观看历史" @tap="handleShortcut('history')">
          <image class="shortcut__img" src="/static/images/profile/history.svg" mode="aspectFit" />
          <text class="shortcut__text">观看历史</text>
        </view>
        <view class="shortcut" role="button" aria-label="订阅" @tap="handleShortcut('subscriptions')">
          <image class="shortcut__img" src="/static/images/profile/subscribe.svg" mode="aspectFit" />
          <text class="shortcut__text">订阅</text>
        </view>
        <view class="shortcut" role="button" aria-label="通知" @tap="handleShortcut('notifications')">
          <image class="shortcut__img" src="/static/images/profile/notify.svg" mode="aspectFit" />
          <text class="shortcut__text">通知</text>
        </view>
      </view>
    </view>

    <!-- 管理员不展示创建直播 / 我的直播 -->
    <view v-if="!isAdmin" class="card section">
      <text class="section-title">直播管理</text>
      <view class="menu">
        <view class="menu-item" @tap="handleLiveMenu('my-live')">
          <text class="label">我的直播</text>
          <uni-icons class="value" type="right" size="18" :color="'var(--color-text-tertiary)'" />
        </view>
        <view
          class="menu-item"
          :class="{ 'is-disabled': isLoggedIn && !canCreateRoom }"
          @tap="handleLiveMenu('create-live')"
        >
          <view class="menu-item-left">
            <text class="label">创建直播</text>
            <text v-if="isLoggedIn && !canCreateRoom" class="hint">开播功能已被禁用</text>
          </view>
          <uni-icons class="value" type="right" size="18" :color="'var(--color-text-tertiary)'" />
        </view>
      </view>
    </view>

    <view class="card section">
      <text class="section-title">更多服务</text>
      <view class="menu">
        <view class="menu-item" @tap="handleMenu('settings')">
          <text class="label">设置</text>
          <uni-icons class="value" type="right" size="18" :color="'var(--color-text-tertiary)'" />
        </view>
      </view>
    </view>

    <!-- 管理功能：仅管理员可见 -->
    <view class="card section" v-if="isLoggedIn && isAdmin">
      <text class="section-title">管理功能</text>
      <view class="menu">
        <view class="menu-item" @tap="handleAdminMenu('featured-content')">
          <text class="label">焦点图管理</text>
          <uni-icons class="value" type="right" size="18" :color="'var(--color-text-tertiary)'" />
        </view>
        <view class="menu-item" @tap="handleAdminMenu('expert-department')">
          <text class="label">专家分类管理</text>
          <uni-icons class="value" type="right" size="18" :color="'var(--color-text-tertiary)'" />
        </view>
        <view class="menu-item" @tap="handleAdminMenu('admin-rooms')">
          <text class="label">直播间运营</text>
          <uni-icons class="value" type="right" size="18" :color="'var(--color-text-tertiary)'" />
        </view>
        <view class="menu-item" @tap="handleAdminMenu('room-message')">
          <text class="label">讨论管理</text>
          <uni-icons class="value" type="right" size="18" :color="'var(--color-text-tertiary)'" />
        </view>
        <view class="menu-item" @tap="handleAdminMenu('tag')">
          <text class="label">标签管理</text>
          <uni-icons class="value" type="right" size="18" :color="'var(--color-text-tertiary)'" />
        </view>
        <view class="menu-item" @tap="handleAdminMenu('user')">
          <text class="label">用户管理</text>
          <uni-icons class="value" type="right" size="18" :color="'var(--color-text-tertiary)'" />
        </view>
        <view class="menu-item" @tap="handleAdminMenu('expert-bind')">
          <text class="label">专家管理</text>
          <uni-icons class="value" type="right" size="18" :color="'var(--color-text-tertiary)'" />
        </view>
        <view class="menu-item" @tap="handleAdminMenu('brand-manage')">
          <text class="label">品牌管理</text>
          <uni-icons class="value" type="right" size="18" :color="'var(--color-text-tertiary)'" />
        </view>
        <view class="menu-item" @tap="handleAdminMenu('content-safety-rules')">
          <text class="label">发布内容设置</text>
          <uni-icons class="value" type="right" size="18" :color="'var(--color-text-tertiary)'" />
        </view>
        <view class="menu-item" @tap="handleAdminMenu('content-safety-logs')">
          <text class="label">发布处理记录</text>
          <uni-icons class="value" type="right" size="18" :color="'var(--color-text-tertiary)'" />
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useAuthStore } from '@/store/auth'
import { onShow } from '@dcloudio/uni-app'
import { setCustomTabBarSelected } from '@/utils/tabbar'
import { getCurrentUser } from '@/api/user'
import { STORAGE_KEYS } from '@/common/constants'
import type { UserInfo } from '@/types/auth'
import { normalizeCanStream } from '@/types/adminUser'
import { resolveAvatarUrl, shouldMarkAvatarBroken } from '@/utils/url'

const authStore = useAuthStore()

let lastSyncAt = 0
const SYNC_TTL = 5 * 60 * 1000

const isLoggedIn = computed(() => authStore.isAuthenticated)
const userInfo = computed(() => authStore.userInfo)
const isAdmin = computed(() => authStore.isAdmin)
const canCreateRoom = computed(() => authStore.canCreateRoom)

const avatarBroken = ref(false)
const avatarShowIcon = ref(false)

/** 未登录（含 Token 软过期）一律走兜底，勿读残留 userInfo.avatar_url */
const displayAvatar = computed(() =>
  resolveAvatarUrl(isLoggedIn.value ? userInfo.value?.avatar_url : null, avatarBroken.value)
)

watch(isLoggedIn, () => {
  avatarBroken.value = false
  avatarShowIcon.value = false
})

function onAvatarError() {
  if (avatarShowIcon.value) return
  const raw = isLoggedIn.value ? userInfo.value?.avatar_url : null
  if (avatarBroken.value || !shouldMarkAvatarBroken(raw, avatarBroken.value)) {
    avatarShowIcon.value = true
    return
  }
  avatarBroken.value = true
}

const submitting = ref(false)

onShow(() => {
  setCustomTabBarSelected(3)
  authStore.clearAuthIfExpired()
  if (isLoggedIn.value && Date.now() - lastSyncAt > SYNC_TTL) void syncUserInfo()
})

async function syncUserInfo() {
  lastSyncAt = Date.now()
  try {
    const resp = await getCurrentUser()
    const data: any = resp?.data || {}
    const merged: UserInfo = {
      ...(authStore.userInfo || { user_id: String(data.user_id || ''), username: data.username || '', role: 'user', status: 'active', created_at: data.created_at || new Date().toISOString() }),
      ...data,
      can_stream: normalizeCanStream(
        data?.can_stream != null ? data.can_stream : authStore.userInfo?.can_stream
      )
    }
    authStore.userInfo = merged
    uni.setStorageSync(STORAGE_KEYS.USER_INFO, merged)
  } catch {
    // ignore
  }
}

function goLogin(redirectUrl = '/pages/profile/Profile') {
  uni.navigateTo({ url: `/pages/auth/OneTapLogin?redirect=${encodeURIComponent(redirectUrl)}` })
}

function handleHeaderTap() {
  if (!isLoggedIn.value) {
    goLogin('/pages/profile/Profile')
    return
  }
  uni.navigateTo({ url: '/pages/profile/ProfileEdit' })
}

function handleEditProfile() {
  if (!requireLoginOrNavigate('/pages/profile/ProfileEdit')) return
  uni.navigateTo({ url: '/pages/profile/ProfileEdit' })
}

async function handleLogout() {
  submitting.value = true
  try {
    await authStore.logout()
    uni.showToast({ title: '已退出登录', icon: 'success' })
  } finally {
    submitting.value = false
  }
}

function requireLoginOrNavigate(redirectUrl: string): boolean {
  if (isLoggedIn.value) return true
  goLogin(redirectUrl)
  return false
}

function handleShortcut(key: 'favorites' | 'follow' | 'history' | 'subscriptions' | 'notifications') {
  switch (key) {
    case 'favorites':
      if (!requireLoginOrNavigate('/pages/profile/CollectionList')) return
      uni.navigateTo({ url: '/pages/profile/CollectionList' })
      return
    case 'history':
      if (!requireLoginOrNavigate('/pages/profile/ViewHistory')) return
      uni.navigateTo({ url: '/pages/profile/ViewHistory' })
      return
    case 'subscriptions':
      if (!requireLoginOrNavigate('/pages/profile/SubscriptionList')) return
      uni.navigateTo({ url: '/pages/profile/SubscriptionList' })
      return
    case 'follow':
      if (!requireLoginOrNavigate('/pages/profile/FollowedExperts')) return
      uni.navigateTo({ url: '/pages/profile/FollowedExperts' })
      return
    case 'notifications':
      if (!requireLoginOrNavigate('/pages/profile/Notifications')) return
      uni.navigateTo({ url: '/pages/profile/Notifications' })
      return
  }
}

function handleLiveMenu(key: 'my-live' | 'create-live') {
  switch (key) {
    case 'my-live':
      if (!requireLoginOrNavigate('/pages/my-live/MyLive')) return
      uni.navigateTo({ url: '/pages/my-live/MyLive' })
      return
    case 'create-live':
      if (!requireLoginOrNavigate('/pages/live/CreateLive')) return
      if (!authStore.canCreateRoom) {
        uni.showToast({ title: '开播功能已被禁用', icon: 'none' })
        return
      }
      uni.navigateTo({ url: '/pages/live/CreateLive' })
      return
  }
}

function handleMenu(key: 'settings') {
  if (key === 'settings') {
    uni.navigateTo({ url: '/pages/settings/Settings' })
  }
}

function handleAdminMenu(
  key:
    | 'featured-content'
    | 'admin-rooms'
    | 'room-message'
    | 'tag'
    | 'user'
    | 'expert-department'
    | 'expert-bind'
    | 'brand-manage'
    | 'content-safety-rules'
    | 'content-safety-logs'
) {
  if (!requireLoginOrNavigate('/pages/profile/Profile')) return
  if (!authStore.isAdmin) {
    uni.showToast({ title: '暂无访问权限', icon: 'none' })
    return
  }

  switch (key) {
    case 'featured-content':
      uni.navigateTo({ url: '/pages/admin/featuredContent/FeaturedContentList' })
      return
    case 'expert-department':
      uni.navigateTo({ url: '/pages/admin/expertDepartment/ExpertDepartmentList' })
      return
    case 'admin-rooms':
      uni.navigateTo({ url: '/pages/admin/room/AdminRoomList' })
      return
    case 'room-message':
      uni.navigateTo({ url: '/pages/admin/roomMessage/RoomMessageList' })
      return
    case 'tag':
      uni.navigateTo({ url: '/pages/admin/tag/TagList' })
      return
    case 'user':
      uni.navigateTo({ url: '/pages/admin/user/UserList' })
      return
    case 'expert-bind':
      uni.navigateTo({ url: '/pages/admin/expert/ExpertAdminList' })
      return
    case 'brand-manage':
      uni.navigateTo({ url: '/pages/admin/brand/BrandAdminList' })
      return
    case 'content-safety-rules':
      uni.navigateTo({ url: '/pages/admin/contentSafety/ContentSafetyRuleList' })
      return
    case 'content-safety-logs':
      uni.navigateTo({ url: '/pages/admin/contentSafety/ContentSafetyLogList' })
      return
  }
}
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.profile-page {
  min-height: 100vh;
  background: var(--color-background);
  padding: 0;
  padding-bottom: calc(100rpx + constant(safe-area-inset-bottom));
  padding-bottom: calc(100rpx + env(safe-area-inset-bottom));
  box-sizing: border-box;
}

.card {
  background: var(--color-surface);
  border-radius: 0;
  padding: var(--spacing-md) var(--spacing-lg);
  box-shadow: none;
  margin-bottom: 0;
  border-bottom: 1px solid var(--color-border);
}

.hero {
  background: linear-gradient(90deg, var(--color-primary-soft), var(--color-bg-secondary));
  border-radius: 0;
  padding: var(--spacing-lg);
  box-shadow: none;
  margin-bottom: 0;
  border-bottom: 1px solid var(--color-border);
}

.hero__row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.hero__avatar {
  width: 48px;
  height: 48px;
  border-radius: 24px;
  background: var(--color-bg-secondary);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.hero__avatar-img {
  width: 100%;
  height: 100%;
}

.hero__avatar .iconfont {
  font-size: 22px;
  color: var(--color-primary);
}

.hero__info {
  flex: 1;
  min-width: 0;
}

.hero__title {
  display: block;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.hero__sub {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: var(--color-text-secondary);
}

.hero__action {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.ghost-btn {
  height: 32px;
  line-height: 32px;
  padding: 0 12px;
  font-size: 12px;
  border-radius: var(--border-radius-full);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  color: var(--color-text-primary);
  transition: var(--transition-base);
}

.ghost-btn:active {
  background: var(--color-bg-secondary);
}

.shortcuts-card {
  padding: var(--spacing-sm) var(--spacing-lg);
  border-top: 1px solid var(--color-border);
}

.shortcuts {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.shortcut {
  width: 20%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 0;
}

.shortcut:active {
  opacity: 0.88;
}

.shortcut__img {
  width: 22px;
  height: 22px;
}

.shortcut__text {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.section-title {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 8px;
}

.menu {
  display: flex;
  flex-direction: column;
}

.menu-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid var(--color-border);
}

.menu-item.is-disabled {
  opacity: 0.55;
}

.menu-item-left {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.menu-item:last-child {
  border-bottom: none;
}

.label {
  color: var(--color-text-primary);
  font-size: 14px;
}

.hint {
  color: var(--color-text-tertiary);
  font-size: 12px;
}

.value {
  color: var(--color-text-tertiary);
  font-size: 12px;
}
</style>

