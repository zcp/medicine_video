<!--
 * UserBubbleMenu - 用户气泡菜单
 * @description 从底部导航栏头像弹出的用户菜单，支持登录/未登录状态
 -->
<template>
  <view v-if="visible" class="bubble-overlay" @tap="handleClose">
    <view class="bubble-card" @tap.stop>
      <!-- 关闭按钮 -->
      <view class="bubble-close" @tap="handleClose">
        <text class="bubble-close__icon">×</text>
      </view>

      <!-- 未登录状态 -->
      <view v-if="!isLoggedIn" class="bubble-guest">
        <view class="bubble-avatar bubble-avatar--guest">
          <text class="iconfont icon-yonghu bubble-avatar__icon" />
        </view>
        <text class="bubble-guest__title">欢迎访问直播间</text>
        <text class="bubble-guest__sub">登录后享受更多功能</text>
        <view class="bubble-login-btn" @tap="handleLogin">
          <text class="bubble-login-btn__text">登录 / 注册</text>
        </view>
      </view>

      <!-- 已登录状态 -->
      <view v-else class="bubble-user">
        <!-- 用户信息头部 -->
        <view class="bubble-user__header">
          <view class="bubble-avatar">
            <image
              v-if="!avatarShowIcon"
              class="bubble-avatar__img"
              :src="displayAvatar"
              mode="aspectFill"
              @error="onAvatarError"
            />
            <text v-else class="iconfont icon-yonghu bubble-avatar__icon" />
          </view>
          <view class="bubble-user__info">
            <text class="bubble-user__name">{{ displayName }}</text>
            <text v-if="userRole" class="bubble-user__role">{{ userRole }}</text>
          </view>
        </view>

        <!-- 菜单列表 -->
        <view class="bubble-menu">
          <view class="bubble-menu-item" @tap="handleNavigate('/pages/profile/Profile')">
            <text class="iconfont icon-yonghu bubble-menu-item__icon" />
            <text class="bubble-menu-item__label">我的主页</text>
            <text class="bubble-menu-item__arrow">›</text>
          </view>
          <view class="bubble-menu-item" @tap="handleNavigate('/pages/profile/SubscriptionList')">
            <text class="iconfont icon-shoucang bubble-menu-item__icon" />
            <text class="bubble-menu-item__label">我的订阅</text>
            <text class="bubble-menu-item__arrow">›</text>
          </view>
          <view class="bubble-menu-item" @tap="handleNavigate('/pages/settings/AccountSecurity')">
            <text class="iconfont icon-shezhi bubble-menu-item__icon" />
            <text class="bubble-menu-item__label">账号设置</text>
            <text class="bubble-menu-item__arrow">›</text>
          </view>

          <!-- 管理员功能 -->
          <template v-if="isAdmin">
            <view class="bubble-menu-divider" />
            <view class="bubble-menu-item" @tap="handleNavigate('/pages/admin/expertDepartment/ExpertDepartmentList')">
              <text class="iconfont icon-shezhi bubble-menu-item__icon" />
              <text class="bubble-menu-item__label">专家分类管理</text>
              <text class="bubble-menu-item__arrow">›</text>
            </view>
            <view class="bubble-menu-item" @tap="handleNavigate('/pages/admin/roomMessage/RoomMessageList')">
              <text class="iconfont icon-xiaoxi bubble-menu-item__icon" />
              <text class="bubble-menu-item__label">讨论管理</text>
              <text class="bubble-menu-item__arrow">›</text>
            </view>
          </template>
        </view>

        <!-- 退出登录 -->
        <view class="bubble-logout" @tap="handleLogout">
          <text class="bubble-logout__text">退出登录</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import type { UserInfo } from '@/types/auth'
import { resolveAvatarUrl, shouldMarkAvatarBroken } from '@/utils/url'

const props = defineProps<{
  /** 是否可见 */
  visible: boolean
  /** 用户信息 */
  userInfo?: UserInfo | null
  /** 是否已登录 */
  isLoggedIn: boolean
  /** 是否管理员 */
  isAdmin: boolean
}>()

const emit = defineEmits<{
  close: []
  navigate: [path: string]
  logout: []
}>()

const avatarBroken = ref(false)
const avatarShowIcon = ref(false)

const displayAvatar = computed(() => resolveAvatarUrl(props.userInfo?.avatar_url, avatarBroken.value))

function onAvatarError() {
  if (avatarShowIcon.value) return
  const raw = props.userInfo?.avatar_url
  if (avatarBroken.value || !shouldMarkAvatarBroken(raw, avatarBroken.value)) {
    avatarShowIcon.value = true
    return
  }
  avatarBroken.value = true
}

const displayName = computed(() => {
  if (!props.userInfo) return '已登录'
  return props.userInfo.nickname || props.userInfo.username || props.userInfo.phone || '已登录用户'
})

const userRole = computed(() => {
  return props.userInfo?.role || ''
})

function handleClose() {
  emit('close')
}

function handleLogin() {
  emit('navigate', '/pages/auth/OneTapLogin')
  emit('close')
}

function handleNavigate(path: string) {
  emit('navigate', path)
  emit('close')
}

function handleLogout() {
  emit('logout')
}
</script>

<style lang="scss" scoped>
.bubble-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 160;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
}

.bubble-card {
  position: relative;
  width: 560rpx;
  background: var(--color-surface, #ffffff);
  border-radius: 24rpx;
  box-shadow: 0 8rpx 40rpx rgba(0, 0, 0, 0.18);
  padding: 40rpx 36rpx;
  box-sizing: border-box;
}

.bubble-close {
  position: absolute;
  top: 16rpx;
  right: 20rpx;
  width: 48rpx;
  height: 48rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1;
}

.bubble-close:active {
  opacity: 0.6;
}

.bubble-close__icon {
  font-size: 36rpx;
  color: var(--color-text-tertiary, #c0c4cc);
  line-height: 1;
}

/* 未登录 */
.bubble-guest {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20rpx 0;
}

.bubble-guest__title {
  font-size: 30rpx;
  font-weight: 600;
  color: var(--color-text-primary, #333333);
  margin-top: 20rpx;
}

.bubble-guest__sub {
  font-size: 24rpx;
  color: var(--color-text-secondary, #909399);
  margin-top: 8rpx;
}

.bubble-login-btn {
  margin-top: 32rpx;
  width: 100%;
  height: 76rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary, #0f766e);
  border-radius: 40rpx;
}

.bubble-login-btn:active {
  opacity: 0.85;
}

.bubble-login-btn__text {
  font-size: 28rpx;
  color: #ffffff;
  font-weight: 500;
}

/* 头像 */
.bubble-avatar {
  width: 96rpx;
  height: 96rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--color-primary, #0f766e), #0d9488);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  flex-shrink: 0;
}

.bubble-avatar--guest {
  width: 120rpx;
  height: 120rpx;
}

.bubble-avatar__img {
  width: 100%;
  height: 100%;
}

.bubble-avatar__icon {
  font-size: 44rpx;
  color: #ffffff;
  line-height: 1;
}

/* 已登录 */
.bubble-user {
  display: flex;
  flex-direction: column;
}

.bubble-user__header {
  display: flex;
  align-items: center;
  gap: 20rpx;
  padding-bottom: 28rpx;
  border-bottom: 1px solid var(--color-border, #ebeef5);
}

.bubble-user__info {
  flex: 1;
  min-width: 0;
}

.bubble-user__name {
  display: block;
  font-size: 30rpx;
  font-weight: 600;
  color: var(--color-text-primary, #333333);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.bubble-user__role {
  display: block;
  font-size: 22rpx;
  color: var(--color-text-secondary, #909399);
  margin-top: 4rpx;
}

/* 菜单 */
.bubble-menu {
  padding: 12rpx 0;
}

.bubble-menu-divider {
  height: 1px;
  background: var(--color-border, #ebeef5);
  margin: 8rpx 0;
}

.bubble-menu-item {
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 22rpx 0;
}

.bubble-menu-item:active {
  opacity: 0.7;
}

.bubble-menu-item__icon {
  font-size: 34rpx;
  color: var(--color-text-secondary, #909399);
  width: 40rpx;
  text-align: center;
}

.bubble-menu-item__label {
  flex: 1;
  font-size: 28rpx;
  color: var(--color-text-primary, #333333);
}

.bubble-menu-item__arrow {
  font-size: 30rpx;
  color: var(--color-text-tertiary, #c0c4cc);
}

/* 退出登录 */
.bubble-logout {
  margin-top: 12rpx;
  padding-top: 20rpx;
  border-top: 1px solid var(--color-border, #ebeef5);
  display: flex;
  align-items: center;
  justify-content: center;
}

.bubble-logout:active {
  opacity: 0.7;
}

.bubble-logout__text {
  font-size: 26rpx;
  color: var(--color-danger, #ff4d4f);
}
</style>
