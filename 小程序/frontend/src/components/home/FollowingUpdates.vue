<!--
 * FollowingUpdates - 我的关注更新组件
 * @description 展示关注的专家动态
 * @author 直播SaaS团队
 -->
<template>
  <view v-if="experts.length > 0" class="following-updates">
    <view class="following-updates__header">
      <text class="header__title">我的关注</text>
      <text class="header__more" @click="handleViewAll">全部 ></text>
    </view>
    
    <scroll-view class="following-updates__list" scroll-x>
      <view
        v-for="expert in experts"
        :key="expert.id"
        class="expert-item"
        @click="handleExpertClick(expert)"
      >
        <image
          :class="['expert-item__avatar', expert.status]"
          :src="avatarSrc(expert)"
          mode="aspectFill"
          @error="onAvatarError(expert.id, expert.avatar)"
        />
        <view v-if="expert.status === 'live'" class="expert-item__live-badge">LIVE</view>
        <text class="expert-item__name">{{ expert.name }}</text>
        <text :class="['expert-item__status', expert.status]">
          {{ getStatusText(expert.status) }}
        </text>
      </view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { resolveAvatarUrl, shouldMarkAvatarBroken } from '@/utils/url'

/**
 * 组件Props定义
 */
interface Expert {
  id: string
  name: string
  avatar: string
  status: 'live' | 'scheduled' | 'offline'
  sessionId?: string
}

interface Props {
  /** 关注的专家列表 */
  experts: Expert[]
}

defineProps<Props>()

const brokenAvatarIds = ref<Record<string, true>>({})

function avatarSrc(expert: Expert): string {
  return resolveAvatarUrl(expert.avatar, !!brokenAvatarIds.value[expert.id])
}

function onAvatarError(expertId: string, raw?: string | null) {
  const id = String(expertId || '').trim()
  if (!id || brokenAvatarIds.value[id]) return
  if (!shouldMarkAvatarBroken(raw, !!brokenAvatarIds.value[id])) return
  brokenAvatarIds.value = { ...brokenAvatarIds.value, [id]: true }
}

/**
 * 组件Emits定义
 */
const emit = defineEmits<{
  /** 点击专家 */
  'expert-click': [expert: Expert]
  /** 查看全部 */
  'view-all': []
}>()

const getStatusText = (status: string) => {
  const map = {
    live: '🔴 直播中',
    scheduled: '预告',
    offline: '离线'
  }
  return map[status as keyof typeof map] || '离线'
}

const handleExpertClick = (expert: Expert) => {
  emit('expert-click', expert)
}

const handleViewAll = () => {
  emit('view-all')
}
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.following-updates {
  background-color: var(--color-bg-primary);
  padding: 12px 0;
  margin-bottom: 8px;
  
  &__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 16px 12px;
    
    .header__title {
      font-size: 16px;
      font-weight: 600;
      color: var(--color-text-primary);
    }
    
    .header__more {
      font-size: 14px;
      color: var(--color-text-tertiary);
    }
  }
  
  &__list {
    display: flex;
    white-space: nowrap;
    padding: 0 16px;
  }
}

.expert-item {
  position: relative;
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  margin-right: 16px;
  width: 64px;
  
  &__avatar {
    width: 56px;
    height: 56px;
    border-radius: 50%;
    border: 2px solid transparent;
    
    &.live {
      border-color: var(--color-live);
    }
  }
  
  &__live-badge {
    position: absolute;
    top: 0;
    right: 0;
    padding: 2px 4px;
    background-color: var(--color-live);
    border-radius: 4px;
    font-size: 10px;
    color: var(--color-text-inverse);
    font-weight: 600;
  }
  
  &__name {
    font-size: 12px;
    color: var(--color-text-primary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    width: 100%;
    text-align: center;
  }
  
  &__status {
    font-size: 11px;
    
    &.live {
      color: var(--color-live);
    }
    
    &.scheduled {
      color: var(--color-primary);
    }
    
    &.offline {
      color: var(--color-text-tertiary);
    }
  }
}
</style>
