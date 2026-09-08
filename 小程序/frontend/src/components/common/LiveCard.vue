<!--
 * LiveCard - 直播卡片组件
 * @description 展示直播间信息的卡片组件，用于首页Feed流
 * @author 直播SaaS团队
 -->
<template>
  <view class="live-card" @click="handleClick">
    <!-- 封面图片 -->
    <view class="live-card__cover">
      <image
        class="live-card__cover-image"
        :src="displayCoverUrl"
        mode="aspectFill"
        :lazy-load="lazyLoad"
        @error="handleCoverError"
      />

      <!-- 分类角标：右上角 -->
      <view v-if="categoryName" class="live-card__category-badge">
        <text class="category-badge__text">{{ categoryName }}</text>
      </view>
    </view>

    <!-- 卡片内容：标题两行 + 头像/名字/医院 -->
    <view class="live-card__content">
      <text class="live-card__title">{{ title }}</text>
      <view class="live-card__host">
        <image
          class="host__avatar"
          :src="displayHostAvatar"
          mode="aspectFill"
          @error="handleHostAvatarError"
        />
        <view class="host__meta">
          <text class="host__name">{{ host?.name || '主讲专家' }}</text>
          <text v-if="hostHospital" class="host__hospital">{{ hostHospital }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { logger } from '@/logs/logger'
import {
  resolveAvatarUrl,
  resolveCoverUrl,
  shouldMarkAvatarBroken,
  shouldMarkCoverBroken
} from '@/utils/url'

/**
 * 组件Props定义
 */
interface Props {
  /** 直播间ID */
  id: string
  /** 直播标题 */
  title: string
  summary?: string | null
  coverUrl?: string | null
  rawCoverUrl?: string | null
  /** 分类（用于展示角标） */
  category?: {
    id?: string
    name: string
    icon?: string | null
  } | null
  /** 直播状态 */
  liveStatus: 'live' | 'scheduled' | 'replay'
  /** 主讲专家信息 */
  host?: {
    name: string
    avatarUrl?: string | null
    title?: string | null
    hospital?: string | null
  } | null
  /** 观看人数（保留 props 兼容，首页不再展示） */
  viewerCount?: number | null
  /** 点赞/播放数（保留 props 兼容，首页不再展示） */
  likeCount?: number | null
  /** 热度值 */
  heat?: number | null
  /** 是否懒加载图片 */
  lazyLoad?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  lazyLoad: true
})

const coverBroken = ref(false)
const hostAvatarBroken = ref(false)

watch(
  () => props.coverUrl,
  () => {
    coverBroken.value = false
  }
)

watch(
  () => props.host?.avatarUrl,
  () => {
    hostAvatarBroken.value = false
  }
)

const displayCoverUrl = computed(() => resolveCoverUrl(props.coverUrl, coverBroken.value))

const displayHostAvatar = computed(() =>
  resolveAvatarUrl(props.host?.avatarUrl, hostAvatarBroken.value)
)

const categoryName = computed(() => {
  const name = (props.category as any)?.name
  return name ? String(name) : ''
})

const hostHospital = computed(() => {
  const hospital = props.host?.hospital ? String(props.host.hospital).trim() : ''
  return hospital
})

/**
 * 组件Emits定义
 */
const emit = defineEmits<{
  /** 点击事件 */
  click: [id: string]
}>()

/**
 * 处理图片加载错误
 */
const handleCoverError = () => {
  if (!shouldMarkCoverBroken(props.coverUrl, coverBroken.value)) return
  logger.warn('system', 'cover_load_failed', {
    component: 'LiveCard',
    imageSlot: 'room-cover',
    roomId: props.id,
    title: props.title,
    liveStatus: props.liveStatus,
    rawCoverUrl: props.rawCoverUrl || null,
    resolvedCoverUrl: displayCoverUrl.value || null
  })
  coverBroken.value = true
}

const handleHostAvatarError = () => {
  if (!shouldMarkAvatarBroken(props.host?.avatarUrl, hostAvatarBroken.value)) return
  hostAvatarBroken.value = true
}

/**
 * 处理点击事件
 */
const handleClick = () => {
  emit('click', props.id)
}
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.live-card {
  width: 100%;
  max-width: 100%;
  background-color: var(--color-bg-primary);
  border-radius: var(--border-radius-md);
  overflow: hidden;
  cursor: pointer;
  transition: transform var(--duration-base) var(--ease-in-out);
  box-sizing: border-box;

  &:active {
    transform: scale(0.98);
  }

  &__cover {
    position: relative;
    width: 100%;
    height: 0;
    padding-bottom: 56.25%; /* 16:9 */
    background-color: var(--color-bg-tertiary);
    overflow: hidden;
  }

  &__category-badge {
    position: absolute;
    top: 8px;
    right: 8px;
    max-width: 60%;
    padding: 0;
    background-color: transparent;
    border-radius: 0;
    overflow: hidden;

    .category-badge__text {
      font-size: 24rpx;
      color: var(--color-text-inverse);
      white-space: nowrap;
      text-overflow: ellipsis;
      overflow: hidden;
      text-shadow: 0 2rpx 6rpx rgba(0, 0, 0, 0.35);
    }
  }

  &__cover-image {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
  }

  &__content {
    padding: 16rpx 12rpx 20rpx;
    display: flex;
    flex-direction: column;
    gap: 14rpx;
    box-sizing: border-box;
  }

  /* 双列卡片：正文字号抬到手机可读区间，避免过小发糊 */
  &__title {
    display: -webkit-box;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 2;
    overflow: hidden;
    word-break: break-word;
    font-size: 30rpx;
    font-weight: 600;
    color: var(--color-text-primary);
    line-height: 1.4;
    min-height: calc(30rpx * 1.4 * 2);
  }

  &__host {
    display: flex;
    align-items: center;
    gap: 14rpx;
    min-width: 0;
  }

  .host__avatar {
    width: 72rpx;
    height: 72rpx;
    border-radius: var(--border-radius-full);
    background-color: var(--color-bg-tertiary);
    flex: 0 0 auto;
    border: 1rpx solid var(--color-border);
  }

  .host__meta {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    justify-content: center;
    gap: 6rpx;
  }

  .host__name {
    font-size: 26rpx;
    font-weight: 500;
    color: var(--color-text-primary);
    line-height: 1.25;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .host__hospital {
    font-size: 24rpx;
    color: var(--color-text-secondary);
    line-height: 1.25;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}
</style>
