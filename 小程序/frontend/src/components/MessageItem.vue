<!--
 * MessageItem - 单条留言组件
 * @description 直播间留言列表中的单条消息展示
 * 对齐 V1.5 / 后端 V3：优先 user.*，回退 user_display_name；头像空用默认图
 * 长按：本人/管理员可删除；任何人可复制
 -->
<template>
  <view
    v-if="message"
    class="msg-item"
    :class="{ 'msg-item--own': isOwnMessage }"
    @longpress="handleLongPress"
  >
    <view class="msg-avatar">
      <image
        class="msg-avatar__img"
        :src="avatarSrc"
        mode="aspectFill"
        @error="onAvatarError"
      />
    </view>

    <view class="msg-body">
      <view class="msg-header">
        <text class="msg-name">{{ displayName }}</text>
        <text v-if="isOwnMessage" class="msg-own-tag">我</text>
        <text class="msg-time">{{ formatTime(message?.created_at || '') }}</text>
      </view>
      <text class="msg-content">{{ message?.content }}</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { RoomMessageItem } from '@/types/roomMessage'
import {
  normalizeRoomMessageItem,
  resolveMessageDisplayName
} from '@/utils/roomMessageNormalize'
import { resolveAvatarUrl, shouldMarkAvatarBroken } from '@/utils/url'

const props = defineProps<{
  message?: RoomMessageItem | null
  currentUserId?: string
  isAdmin?: boolean
}>()

const emit = defineEmits<{
  delete: [message: RoomMessageItem]
}>()

const avatarBroken = ref(false)

const normalized = computed(() => {
  if (!props.message) return null
  return normalizeRoomMessageItem(props.message, {
    user_id: props.currentUserId
  })
})

const displayName = computed(() =>
  normalized.value ? resolveMessageDisplayName(normalized.value) : ''
)

const avatarSrc = computed(() =>
  resolveAvatarUrl(normalized.value?.user?.avatar_url, avatarBroken.value)
)

const isOwnMessage = computed(() => {
  const uid = props.currentUserId
  if (!uid || !props.message) return false
  return String(uid) === String(props.message.user_id)
})

const canDelete = computed(() => {
  if (props.isAdmin) return true
  return isOwnMessage.value
})

watch(avatarSrc, () => {
  avatarBroken.value = false
})

/** 真实头像失败 → 默认图；默认图再失败不再切字母/蓝底，避免与兜底图叠层 */
function onAvatarError() {
  const raw = normalized.value?.user?.avatar_url
  if (!shouldMarkAvatarBroken(raw, avatarBroken.value)) return
  avatarBroken.value = true
}

function handleLongPress() {
  if (!props.message) return
  const itemList = canDelete.value ? ['复制', '删除讨论'] : ['复制']
  uni.showActionSheet({
    itemList,
    itemColor: '#333333',
    success: (res) => {
      if (canDelete.value) {
        if (res.tapIndex === 0) copyContent()
        if (res.tapIndex === 1) handleDelete()
      } else if (res.tapIndex === 0) {
        copyContent()
      }
    }
  })
}

function copyContent() {
  const text = String(props.message?.content || '')
  if (!text) {
    uni.showToast({ title: '无内容可复制', icon: 'none' })
    return
  }
  uni.setClipboardData({
    data: text,
    success: () => uni.showToast({ title: '已复制', icon: 'success' }),
    fail: () => uni.showToast({ title: '复制失败', icon: 'none' })
  })
}

function formatTime(iso: string): string {
  if (!iso) return ''
  const diffMs = Date.now() - new Date(iso).getTime()
  const min = Math.floor(diffMs / 60000)
  if (min < 1) return '刚刚'
  if (min < 60) return `${min}分钟前`
  const hr = Math.floor(min / 60)
  if (hr < 24) return `${hr}小时前`
  const day = Math.floor(hr / 24)
  if (day < 7) return `${day}天前`
  return new Date(iso).toLocaleDateString('zh-CN', {
    month: 'numeric',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit'
  })
}

function handleDelete() {
  if (!props.message) return
  emit('delete', props.message)
}
</script>

<style lang="scss" scoped>
.msg-item {
  display: flex;
  gap: 16rpx;
  padding: 20rpx 0;
  border-bottom: 1rpx solid var(--color-border);
}

.msg-item:last-child {
  border-bottom: none;
}

.msg-avatar {
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
  /* 中性底，避免半透明 DEFAULT_AVATAR 透出蓝渐变造成「两层头像」 */
  background: var(--color-bg-tertiary, #f0f2f5);
  display: flex;
  align-items: center;
  justify-content: center;
}

.msg-avatar__img {
  width: 100%;
  height: 100%;
}

.msg-body {
  flex: 1;
  min-width: 0;
}

.msg-header {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-bottom: 6rpx;
}

.msg-name {
  font-size: 24rpx;
  color: var(--color-text-secondary);
  font-weight: 500;
  max-width: 360rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.msg-own-tag {
  font-size: 18rpx;
  color: #1890ff;
  background: rgba(24, 144, 255, 0.15);
  padding: 2rpx 10rpx;
  border-radius: 6rpx;
  line-height: 1.4;
  flex-shrink: 0;
}

.msg-time {
  font-size: 20rpx;
  color: var(--color-text-tertiary);
  margin-left: auto;
  flex-shrink: 0;
}

.msg-content {
  font-size: 28rpx;
  color: var(--color-text-primary);
  line-height: 1.5;
  word-break: break-word;
  white-space: pre-wrap;
}
</style>
