<template>
  <view class="expert-profile">
    <view class="header">
      <image class="avatar" :src="avatarSrc" mode="aspectFill" @error="onAvatarError" />
      <view class="info">
        <view class="name-row">
          <text class="name">{{ name }}</text>
          <text class="title">{{ title }}</text>
        </view>
        <text class="dept">{{ department }}</text>
      </view>
      <view
        class="follow-btn"
        :class="{ active: isFollowing }"
        @tap="onToggle"
        :aria-label="isFollowing ? '已关注' : '关注'"
      >
        <text v-if="pending">处理中...</text>
        <text v-else>{{ isFollowing ? '已关注' : '关注' }}</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { resolveAvatarUrl, shouldMarkAvatarBroken } from '@/utils/url'

interface Stats { followers: number; sessions: number; views: number }

const props = withDefaults(defineProps<{
  avatar?: string | null
  name: string
  title: string
  department: string
  stats?: Stats
  isFollowing?: boolean
  pending?: boolean
}>(), {
  avatar: '',
  isFollowing: false,
  pending: false
})

const emit = defineEmits<{ (e: 'toggle-follow'): void }>()

const avatarBroken = ref(false)

watch(
  () => props.avatar,
  () => {
    avatarBroken.value = false
  }
)

const avatarSrc = computed(() => resolveAvatarUrl(props.avatar, avatarBroken.value))

function onAvatarError() {
  if (!shouldMarkAvatarBroken(props.avatar, avatarBroken.value)) return
  avatarBroken.value = true
}

function onToggle() {
  if (!props.pending) emit('toggle-follow')
}
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.expert-profile { background: var(--color-surface); padding: var(--spacing-lg); }
.header { display: flex; align-items: center; }
.avatar { width: 72px; height: 72px; border-radius: 50%; background: var(--color-bg-tertiary); }
.info { flex: 1; margin: 0 12px; }
.name-row { display: flex; align-items: baseline; }
.name { font-size: 18px; font-weight: 600; color: var(--color-text-primary); }
.title { font-size: 12px; color: var(--color-text-secondary); margin-left: 8px; }
.dept { font-size: 12px; color: var(--color-text-secondary); margin-top: 4px; }
.stats { display: flex; align-items: center; margin-top: 8px; }
.stat { font-size: 12px; color: var(--color-text-tertiary); }
.dot { margin: 0 6px; color: var(--color-border); }
.follow-btn {
  background: var(--color-primary); color: var(--color-text-inverse); font-size: 12px;
  padding: 8px 12px; border-radius: var(--border-radius-full);
  transition: var(--transition-base);
}
.follow-btn.active {
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
  border: 1px solid var(--color-border);
}
</style>
