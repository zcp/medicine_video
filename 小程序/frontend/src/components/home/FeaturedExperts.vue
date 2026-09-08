<template>
  <view v-if="experts.length > 0" class="featured-experts">
    <view class="featured-experts__header">
      <view class="featured-experts__heading">
        <text class="featured-experts__title">精选专家</text>
      </view>
    </view>

    <scroll-view class="featured-experts__scroll" scroll-x scroll-with-animation enable-flex>
      <view class="featured-experts__track">
        <view
          v-for="expert in experts"
          :key="expert.id"
          class="featured-experts__card"
          @tap="onOpenDetail(expert)"
        >
          <view class="featured-experts__follow" @tap.stop="handleToggleFollow(expert)">
            <text
              class="iconfont featured-experts__star"
              :class="isFollowing(expert.id) ? 'icon-shoucang1 is-active' : 'icon-shoucang'"
            ></text>
          </view>

          <view class="featured-experts__top-row">
            <view class="featured-experts__avatar-wrap">
              <image
                class="featured-experts__avatar"
                :src="avatarSrc(expert)"
                mode="aspectFill"
                @error="onAvatarError(expert.id)"
              />
            </view>

            <view class="featured-experts__name-wrap">
              <text class="featured-experts__name">{{ expert.name }}</text>
            </view>
          </view>

          <view class="featured-experts__meta">
            <view class="featured-experts__title-row">
              <text class="featured-experts__title-text">{{ expert.title || '专家' }}</text>
              <view v-if="isLive(expert)" class="featured-experts__live-badge">
                <view class="featured-experts__live-dot"></view>
                <text class="featured-experts__live-text">直播中</text>
              </view>
            </view>
            <text class="featured-experts__hospital">{{ expert.hospital || expert.department || '平台认证专家' }}</text>
            <text v-if="expert.department" class="featured-experts__department">{{ expert.department }}</text>
          </view>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { resolveAvatarUrl, shouldMarkAvatarBroken } from '@/utils/url'

export interface FeaturedExpertCard {
  id: string
  name: string
  avatarUrl?: string | null
  title?: string | null
  hospital?: string | null
  department?: string | null
  liveStatus?: 'live' | 'scheduled' | 'replay' | string | null
}

interface Props {
  experts: FeaturedExpertCard[]
  followingMap?: Record<string, boolean>
  followPendingId?: string | null
}

const props = withDefaults(defineProps<Props>(), {
  followingMap: () => ({}),
  followPendingId: null
})

const emit = defineEmits<{
  'open-detail': [expert: FeaturedExpertCard]
  'toggle-follow': [expert: FeaturedExpertCard]
}>()

const brokenAvatarIds = ref<Record<string, true>>({})

const isFollowing = (expertId: string) => !!props.followingMap?.[expertId]

const isLive = (expert: FeaturedExpertCard) => {
  const status = String(expert?.liveStatus || '').toLowerCase()
  return status === 'live'
}

const avatarSrc = (expert: FeaturedExpertCard): string => {
  if (!expert?.id) return resolveAvatarUrl(null)
  return resolveAvatarUrl(expert.avatarUrl, !!brokenAvatarIds.value[expert.id])
}

const onAvatarError = (expertId: string) => {
  const id = String(expertId || '').trim()
  if (!id) return
  const expert = props.experts.find((item) => item.id === id)
  if (!shouldMarkAvatarBroken(expert?.avatarUrl, !!brokenAvatarIds.value[id])) return
  brokenAvatarIds.value = { ...brokenAvatarIds.value, [id]: true }
}

const onOpenDetail = (expert: FeaturedExpertCard) => {
  if (!expert?.id) return
  emit('open-detail', expert)
}

const handleToggleFollow = (expert: FeaturedExpertCard) => {
  if (!expert?.id) return
  if (props.followPendingId === expert.id) return
  emit('toggle-follow', expert)
}
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.featured-experts {
  margin-top: 12px;
  padding: 0 12px;
  background: transparent;

  &__header {
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    margin-bottom: 10px;
  }

  &__heading {
    display: flex;
    flex-direction: column;
  }

  &__title {
    font-size: 16px;
    font-weight: 700;
    color: var(--color-text-primary);
  }

  &__scroll {
    width: 100%;
    overflow: hidden;
  }

  &__track {
    display: flex;
    align-items: stretch;
    gap: 12px;
    padding-bottom: 2px;
    white-space: nowrap;
  }

  &__card {
    position: relative;
    flex: 0 0 auto;
    width: 286rpx;
    min-height: 194rpx;
    padding: 18rpx 18rpx 14rpx;
    box-sizing: border-box;
    background: var(--color-bg-primary);
    border: 1px solid var(--color-border);
    border-radius: var(--border-radius-lg);
    overflow: hidden;
    transition: transform var(--duration-fast) var(--ease-in-out), border-color var(--duration-fast) var(--ease-in-out);

    &:active {
      transform: scale(0.98);
    }
  }

  &__follow {
    position: absolute;
    top: 10rpx;
    right: 10rpx;
    width: 42rpx;
    height: 42rpx;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    background: rgba(0, 0, 0, 0.02);
  }

  &__top-row {
    display: flex;
    align-items: center;
    gap: 12rpx;
    padding-right: 56rpx;
    margin-bottom: 12rpx;
  }

  &__avatar-wrap {
    flex-shrink: 0;
  }

  &__avatar {
    width: 72rpx;
    height: 72rpx;
    border-radius: 50%;
    background: var(--color-bg-tertiary);
  }

  &__name-wrap {
    flex: 1;
    min-width: 0;
    display: flex;
    align-items: baseline;
    gap: 8rpx;
  }

  &__meta {
    display: flex;
    flex-direction: column;
    gap: 6rpx;
    min-width: 0;
  }

  &__title-row {
    display: flex;
    align-items: center;
    gap: 8rpx;
    min-width: 0;
  }

  &__name {
    font-size: 16px;
    font-weight: 700;
    color: var(--color-text-primary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  &__title-text,
  &__hospital {
    font-size: 12px;
    color: var(--color-text-secondary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  &__live-badge {
    flex: 0 0 auto;
    display: inline-flex;
    align-items: center;
    gap: 4rpx;
    height: 28rpx;
    padding: 0 8rpx;
    border-radius: var(--border-radius-full);
    background: rgba(255, 77, 79, 0.1);
  }

  &__live-dot {
    width: 10rpx;
    height: 10rpx;
    border-radius: 50%;
    background: var(--color-danger);
  }

  &__live-text {
    font-size: 11px;
    line-height: 1;
    color: var(--color-danger);
    font-weight: 600;
  }

  &__department {
    font-size: 12px;
    color: var(--color-text-tertiary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  &__star {
    font-size: 18px;
    line-height: 1;
    color: var(--color-text-tertiary);

    &.is-active {
      color: var(--color-primary);
    }
  }
}
</style>
