<template>
  <view class="expert-card" @tap="$emit('click')">
    <view class="left">
      <image class="avatar" :src="avatarSrc" mode="aspectFill" @error="onAvatarError" />
    </view>
    <view class="content">
      <view class="name-row">
        <view class="name-wrap">
          <text class="name">{{ name }}</text>
          <text class="title">{{ title }}</text>
        </view>
        <view
          class="follow-btn ui-trans"
          :class="{ active: isFollowing, 'is-pending': pending }"
          :aria-disabled="pending ? 'true' : 'false'"
          @tap.stop="onToggle"
        >
          <text v-if="pending">...</text>
          <text v-else>{{ isFollowing ? '已关注' : '关注' }}</text>
        </view>
      </view>
      <text class="dept">{{ department }}</text>
      <text v-if="specialtyText" class="specialty">擅长：{{ specialtyText }}</text>
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
  specialization?: string[] | null
  stats?: Stats
  isFollowing?: boolean
  pending?: boolean
}>(), {
  avatar: '',
  specialization: () => [],
  isFollowing: false,
  pending: false
})

const emit = defineEmits<{ (e: 'click'): void; (e: 'toggle-follow'): void }>()

const avatarBroken = ref(false)

watch(
  () => props.avatar,
  () => {
    avatarBroken.value = false
  }
)

const avatarSrc = computed(() => resolveAvatarUrl(props.avatar, avatarBroken.value))

const specialtyText = computed(() => {
  const list = Array.isArray(props.specialization)
    ? props.specialization.map((s) => String(s || '').trim()).filter(Boolean)
    : []
  if (!list.length) return ''
  const joined = list.join('、')
  return joined.length > 36 ? `${joined.slice(0, 36)}…` : joined
})

function onAvatarError() {
  if (!shouldMarkAvatarBroken(props.avatar, avatarBroken.value)) return
  avatarBroken.value = true
}

function onToggle() {
  emit('toggle-follow')
}
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.expert-card {
  display: flex;
  position: relative;
  padding: var(--spacing-md);
  background: transparent;
  border-radius: 0;
  margin: 0;
  box-shadow: none;
}
.left { margin-right: 12px; }
.avatar {
  width: 64px; height: 64px; border-radius: 50%;
  background: var(--color-bg-tertiary);
}
.content { flex: 1; display: flex; flex-direction: column; }
.name-row {
  position: relative;
  display: flex;
  align-items: center;
  gap: 8px;
  padding-right: var(--layout-list-actioncolumn-width);
}
.name-wrap { flex: 1; min-width: 0; display: flex; align-items: baseline; gap: 6px; }
.name { font-size: 16px; font-weight: 600; color: var(--color-text-primary); max-width: 60%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.title { font-size: 12px; color: var(--color-text-secondary); max-width: 38%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.follow-btn {
  position: absolute;
  right: var(--layout-list-actioncolumn-inset);
  top: 50%;
  transform: translateY(-50%);
  min-width: 72px;
  height: 64rpx;
  min-height: 64rpx;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  color: var(--color-text-secondary);
  font-size: 13px;
  padding: 0 24rpx;
  border-radius: var(--border-radius-full);
  white-space: nowrap;
  box-shadow: none;
  transition: var(--transition-base);
}
.follow-btn.active {
  background: var(--color-primary);
  border-color: transparent;
  color: var(--color-text-inverse);
  box-shadow: none;
}
.follow-btn:active {
  transform: translateY(-50%) scale(0.98);
}
.follow-btn[aria-disabled='true'] {
  opacity: 0.6;
}
.follow-btn.is-pending {
  pointer-events: none;
}
.dept { font-size: 12px; color: var(--color-text-secondary); margin-top: 4px; }
.specialty {
  font-size: 12px;
  color: var(--color-text-tertiary);
  margin-top: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.stats { display: flex; align-items: center; margin-top: 8px; }
.stat { font-size: 12px; color: var(--color-text-tertiary); }
.dot { margin: 0 6px; color: var(--color-border); }
.ui-trans { transition: background-color var(--duration-fast) var(--ease-in-out), border-color var(--duration-fast) var(--ease-in-out), opacity var(--duration-fast) var(--ease-in-out), transform var(--duration-fast) var(--ease-in-out); }

@media (max-width: 767px) {
  .expert-card { padding: var(--spacing-md) var(--spacing-base); }
  .name { max-width: 70%; }
  .title { max-width: 26%; }
}
</style>
