<!--
 * Banner3D - 3D焦点轮播图组件
 * @description 首页顶部 3D 卡片轮播（左右预览 + 中间放大），对齐移动端设计文档 H3.1
 -->
<template>
  <view class="banner-3d">
    <swiper
      class="banner-3d__swiper"
      :current="currentIndex"
      :indicator-dots="false"
      :autoplay="innerAutoplay"
      :interval="interval"
      :duration="duration"
      :circular="canLoop"
      :previous-margin="sidePeek"
      :next-margin="sidePeek"
      @change="handleChange"
      @touchstart="handleTouchStart"
      @touchend="handleTouchEnd"
    >
      <swiper-item v-for="(banner, index) in banners" :key="banner.id">
        <view
          class="banner-card"
          :class="getCardClass(index)"
          @tap="handleCardClick(banner, index)"
        >
          <image
            class="banner-card__image"
            :src="getBannerImageUrl(banner)"
            mode="aspectFill"
            @error="handleImageError(banner.id)"
          />
          <view v-if="banner.title" class="banner-card__title">{{ banner.title }}</view>
        </view>
      </swiper-item>
    </swiper>

    <view v-if="banners.length > 1" class="banner-3d__indicators">
      <view
        v-for="(banner, index) in banners"
        :key="`dot-${banner.id}`"
        class="banner-3d__dot"
        :class="{ 'is-active': index === currentIndex }"
        @tap.stop="handleDotClick(index)"
      />
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from 'vue'
import { logger } from '@/logs/logger'
import { resolveBannerUrl, shouldMarkBannerBroken } from '@/utils/url'

interface Banner {
  id: string
  image_url: string
  title?: string
  link?: string
}

interface Props {
  banners: Banner[]
  autoplay?: boolean
  interval?: number
  duration?: number
}

const props = withDefaults(defineProps<Props>(), {
  autoplay: true,
  interval: 4000,
  duration: 300
})

const emit = defineEmits<{
  change: [index: number]
  click: [banner: Banner]
}>()

const currentIndex = ref(0)
const brokenBannerIds = ref<Record<string, true>>({})
const innerAutoplay = ref(props.autoplay)
let pauseTimer: ReturnType<typeof setTimeout> | null = null

const bannerCount = computed(() => (Array.isArray(props.banners) ? props.banners.length : 0))
/** 微信 circular 在单张时会异常；少于 2 张关闭循环与左右露出 */
const canLoop = computed(() => bannerCount.value >= 2)
const sidePeek = computed(() => (bannerCount.value >= 2 ? '72rpx' : '0rpx'))

watch(
  () => props.autoplay,
  (v) => {
    innerAutoplay.value = v
  }
)

watch(bannerCount, (count) => {
  if (count <= 0) {
    currentIndex.value = 0
    return
  }
  if (currentIndex.value >= count) {
    currentIndex.value = 0
  }
})

function clearPauseTimer() {
  if (pauseTimer) {
    clearTimeout(pauseTimer)
    pauseTimer = null
  }
}

function handleTouchStart() {
  innerAutoplay.value = false
  clearPauseTimer()
}

function handleTouchEnd() {
  if (!props.autoplay || bannerCount.value < 2) return
  clearPauseTimer()
  pauseTimer = setTimeout(() => {
    innerAutoplay.value = true
  }, 8000)
}

function handleChange(e: any) {
  const next = Number(e?.detail?.current ?? 0)
  currentIndex.value = Number.isFinite(next) ? next : 0
  emit('change', currentIndex.value)
}

function handleDotClick(index: number) {
  if (index === currentIndex.value) return
  currentIndex.value = index
}

function handleCardClick(banner: Banner, index: number) {
  // 点击侧边卡片：先切到中间，不触发业务跳转
  if (index !== currentIndex.value) {
    currentIndex.value = index
    return
  }
  emit('click', banner)
}

function handleImageError(bannerId: string) {
  if (brokenBannerIds.value[bannerId]) return
  const banner = props.banners.find(item => item.id === bannerId)
  const raw = banner?.image_url || ''
  if (!shouldMarkBannerBroken(raw, !!brokenBannerIds.value[bannerId])) return
  logger.warn('system', 'banner_image_load_failed', {
    component: 'Banner3D',
    imageSlot: 'banner-image',
    bannerId,
    bannerTitle: banner?.title || '',
    rawImageUrl: raw
  })
  brokenBannerIds.value = {
    ...brokenBannerIds.value,
    [bannerId]: true
  }
}

function getBannerImageUrl(banner: Banner): string {
  if (!banner?.id) return resolveBannerUrl(null)
  return resolveBannerUrl(banner.image_url, !!brokenBannerIds.value[banner.id])
}

function getCardClass(index: number): string {
  const len = bannerCount.value
  if (len <= 1) return 'is-center'

  const diff = (index - currentIndex.value + len) % len
  if (diff === 0) return 'is-center'
  if (diff === 1) return 'is-right'
  if (diff === len - 1) return 'is-left'
  return 'is-hidden'
}

onUnmounted(() => {
  clearPauseTimer()
})
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.banner-3d {
  position: relative;
  margin: var(--spacing-base) 0;
  padding: 0;
  overflow: visible;

  &__swiper {
    width: 100%;
    height: 360rpx;
    overflow: visible;
  }

  &__indicators {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 16rpx;
    margin-top: 16rpx;
  }

  &__dot {
    width: 12rpx;
    height: 12rpx;
    border-radius: 9999rpx;
    background: rgba(0, 0, 0, 0.2);
    transition: width 0.2s ease, background 0.2s ease;

    &.is-active {
      width: 16rpx;
      height: 16rpx;
      background: var(--color-primary);
    }
  }
}

.banner-card {
  position: relative;
  width: 100%;
  height: 100%;
  border-radius: 24rpx;
  overflow: hidden;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1),
    opacity 0.3s cubic-bezier(0.4, 0, 0.2, 1),
    filter 0.3s cubic-bezier(0.4, 0, 0.2, 1);

  &.is-center {
    transform: scale(1);
    opacity: 1;
    filter: brightness(1);
    z-index: 10;
    box-shadow: 0 16rpx 48rpx rgba(0, 0, 0, 0.15);
  }

  &.is-left,
  &.is-right {
    transform: scale(0.85);
    opacity: 0.65;
    filter: brightness(0.82);
    z-index: 5;
    box-shadow: 0 8rpx 24rpx rgba(0, 0, 0, 0.1);
  }

  &.is-hidden {
    opacity: 0;
    transform: scale(0.8);
    z-index: 0;
  }

  &__image {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    display: block;
  }

  &__title {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    padding: var(--spacing-base) var(--spacing-lg);
    background: linear-gradient(to top, rgba(0, 0, 0, 0.6), transparent);
    color: var(--color-text-inverse);
    font-size: 16px;
    font-weight: 600;
  }
}
</style>
