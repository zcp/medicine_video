<!--
 * TopBar - 首页顶部导航栏
 * @description 首页顶部：个人头像、搜索、消息
 * @author 直播SaaS团队
 -->
<template>
  <view class="top-bar" :style="{ paddingTop: statusBarHeight + 'px' }">
    <!-- 第一行：小程序标题（与胶囊按钮同行） -->
    <view class="top-bar__title-bar" :style="{ height: menuButtonHeight + 'px' }">
      <text class="top-bar__app-name">医学直播SaaS平台</text>
    </view>

    <!-- 第二行：头像 + 搜索 + 消息 -->
    <view class="top-bar__header">
      <view class="top-bar__avatar" role="button" aria-label="个人中心" @click="handleAvatar">
        <image class="top-bar__avatar-img" :src="displayAvatarUrl" mode="aspectFill" @error="onAvatarError" />
      </view>

      <view class="top-bar__search" @click="handleSearch">
        <text class="top-bar__search-icon iconfont icon-sousuo"></text>
        <text class="search__placeholder">搜索直播、专家、科室</text>
      </view>

      <view class="top-bar__message" @click="handleMessage">
        <text class="top-bar__message-icon iconfont icon-xiaoxi"></text>
        <view v-if="unreadCount > 0" class="message__badge">
          {{ badgeText }}
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { resolveAvatarUrl, shouldMarkAvatarBroken } from '@/utils/url'

/**
 * 组件Props定义
 */
interface Props {
  /** 未读消息数 */
  unreadCount?: number
  /** 用户头像（未登录可为空，走默认头像） */
  avatarUrl?: string | null
}

const props = withDefaults(defineProps<Props>(), {
  unreadCount: 0,
  avatarUrl: null
})

/**
 * 组件Emits定义
 */
const emit = defineEmits<{
  /** 点击搜索 */
  search: []
  /** 点击消息 */
  message: []
  /** 点击头像 */
  avatar: []
}>()

const avatarBroken = ref(false)

watch(
  () => props.avatarUrl,
  () => {
    avatarBroken.value = false
  }
)

const displayAvatarUrl = computed(() => resolveAvatarUrl(props.avatarUrl, avatarBroken.value))

/** 状态栏高度 */
const statusBarHeight = (() => {
  // #ifdef MP-WEIXIN
  try {
    const windowInfo = (wx as any).getWindowInfo?.()
    return windowInfo?.statusBarHeight || 0
  } catch {
    return 0
  }
  // #endif

  // #ifndef MP-WEIXIN
  return uni.getSystemInfoSync().statusBarHeight || 0
  // #endif
})()

/** 胶囊按钮高度 */
let menuButtonHeight = 32
// #ifdef MP-WEIXIN
try {
  const menuButtonInfo = uni.getMenuButtonBoundingClientRect()
  menuButtonHeight = menuButtonInfo.height
} catch (e) {
  console.warn('获取胶囊按钮信息失败', e)
}
// #endif

/** 徽标文本 */
const badgeText = computed(() => {
  return props.unreadCount > 99 ? '99+' : String(props.unreadCount)
})

const handleSearch = () => {
  emit('search')
}

const handleMessage = () => {
  emit('message')
}

const handleAvatar = () => {
  emit('avatar')
}

const onAvatarError = () => {
  if (!shouldMarkAvatarBroken(props.avatarUrl, avatarBroken.value)) return
  avatarBroken.value = true
}
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.top-bar {
  background-color: var(--color-bg-primary);
  border-bottom: none;
  position: sticky;
  top: 0;
  z-index: 100;

  // #ifdef MP-WEIXIN
  &__title-bar {
    position: relative;
    display: flex;
    align-items: center;
    padding: 0 16px;
    padding-right: 100px;
  }
  // #endif

  // #ifndef MP-WEIXIN
  &__title-bar {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    height: 44px;
    padding: 0 16px;
  }
  // #endif

  &__app-name {
    // #ifdef MP-WEIXIN
    position: absolute;
    left: 50%;
    transform: translateX(-50%);
    // #endif

    font-size: 16px;
    font-weight: 600;
    color: var(--color-text-primary);
  }

  &__header {
    display: flex;
    align-items: center;
    gap: 12px;
    height: 44px;
    padding: 0 16px;
  }

  &__search-icon {
    font-size: 16px;
    line-height: 1;
    color: var(--color-text-tertiary);
  }

  &__message-icon {
    font-size: 20px;
    line-height: 1;
    color: var(--color-text-primary);
  }

  &__avatar {
    flex-shrink: 0;
    width: 36px;
    height: 36px;
    border-radius: 50%;
    overflow: hidden;
    background-color: var(--color-bg-tertiary);
    transition: opacity var(--duration-base) var(--ease-in-out);

    &:active {
      opacity: 0.75;
    }
  }

  &__avatar-img {
    width: 100%;
    height: 100%;
    display: block;
  }

  &__search {
    flex: 1;
    height: 32px;
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 0 12px;
    background-color: var(--color-bg-secondary);
    border-radius: 16px;
    transition: background-color var(--duration-base) var(--ease-in-out);

    &:active {
      background-color: var(--color-bg-tertiary);
    }

    .search__placeholder {
      flex: 1;
      font-size: 14px;
      color: var(--color-text-tertiary);
    }
  }

  &__message {
    position: relative;
    flex-shrink: 0;
    width: 36px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    background-color: rgba(0, 0, 0, 0.02);

    &:active {
      background-color: rgba(0, 0, 0, 0.08);
    }

    .message__badge {
      position: absolute;
      top: 2px;
      right: 2px;
      min-width: 16px;
      height: 16px;
      padding: 0 4px;
      display: flex;
      align-items: center;
      justify-content: center;
      background-color: var(--color-danger);
      border-radius: 8px;
      font-size: 10px;
      color: var(--color-text-inverse);
      font-weight: 600;
      line-height: 1;
      box-shadow: $shadow-xs;
    }
  }
}
</style>
