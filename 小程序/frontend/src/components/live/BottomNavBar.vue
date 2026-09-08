<!--
 * BottomNavBar - 直播间底部导航栏
 * @description 5项导航：首页、搜索、用户头像(居中突出)、消息、我的
 -->
<template>
  <view class="bottom-nav">
    <view class="bottom-nav__inner">
      <!-- 首页 -->
      <view class="nav-item" @tap="handleTap('home')">
        <text class="iconfont icon-shipin nav-item__icon" />
        <text class="nav-item__label">首页</text>
      </view>

      <!-- 搜索 -->
      <view class="nav-item" @tap="handleTap('search')">
        <text class="iconfont icon-sousuo nav-item__icon" />
        <text class="nav-item__label">搜索</text>
      </view>

      <!-- 用户头像（居中突出） -->
      <view class="nav-item nav-item--center" @tap="handleAvatarTap">
        <view class="nav-avatar">
          <image
            v-if="!avatarShowIcon"
            class="nav-avatar__img"
            :src="displayAvatar"
            mode="aspectFill"
            @error="onAvatarError"
          />
          <text v-else class="iconfont icon-yonghu nav-avatar__icon" />
        </view>
      </view>

      <!-- 消息 -->
      <view class="nav-item" @tap="handleTap('messages')">
        <text class="iconfont icon-xiaoxi nav-item__icon" />
        <text class="nav-item__label">消息</text>
      </view>

      <!-- 我的 -->
      <view class="nav-item" @tap="handleTap('profile')">
        <text class="iconfont icon-yonghu nav-item__icon" />
        <text class="nav-item__label">我的</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { resolveAvatarUrl, shouldMarkAvatarBroken } from '@/utils/url'

const props = defineProps<{
  /** 用户头像URL（原始或已解析） */
  userAvatar?: string | null
}>()

const avatarBroken = ref(false)
const avatarShowIcon = ref(false)

const displayAvatar = computed(() => resolveAvatarUrl(props.userAvatar, avatarBroken.value))

function onAvatarError() {
  if (avatarShowIcon.value) return
  if (avatarBroken.value || !shouldMarkAvatarBroken(props.userAvatar, avatarBroken.value)) {
    avatarShowIcon.value = true
    return
  }
  avatarBroken.value = true
}

const emit = defineEmits<{
  /** 导航事件 */
  navigate: [tab: string]
  /** 头像点击 */
  'avatar-tap': []
}>()

function handleTap(tab: string) {
  emit('navigate', tab)
}

function handleAvatarTap() {
  emit('avatar-tap')
}
</script>

<style lang="scss" scoped>
.bottom-nav {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 150;
  background: var(--color-surface, #ffffff);
  border-top: 1px solid var(--color-border, #ebeef5);
  /* 适配 iPhone 底部安全区 */
  padding-bottom: constant(safe-area-inset-bottom);
  padding-bottom: env(safe-area-inset-bottom);
}

.bottom-nav__inner {
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  height: 110rpx;
  padding: 0 8rpx;
}

.nav-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4rpx;
  padding: 10rpx 0 6rpx;
  position: relative;
}

.nav-item:active {
  opacity: 0.7;
}

.nav-item__icon {
  font-size: 40rpx;
  color: var(--color-text-secondary, #909399);
  line-height: 1;
}

.nav-item__label {
  font-size: 20rpx;
  color: var(--color-text-secondary, #909399);
  line-height: 1.2;
}

/* 居中头像按钮 */
.nav-item--center {
  position: relative;
  padding-top: 0;
  justify-content: flex-end;
}

.nav-avatar {
  width: 96rpx;
  height: 96rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--color-primary, #0f766e), #0d9488);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  /* 向上突出 */
  transform: translateY(-30rpx);
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.15);
  border: 4rpx solid var(--color-surface, #ffffff);
}

.nav-avatar__img {
  width: 100%;
  height: 100%;
}

.nav-avatar__icon {
  font-size: 44rpx;
  color: #ffffff;
  line-height: 1;
}
</style>
