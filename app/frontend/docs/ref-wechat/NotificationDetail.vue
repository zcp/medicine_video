<template>
  <view class="page">
    <ErrorBanner v-if="error" :message="error" @close="error = null" />

    <LoadingIndicator v-if="loading" fullscreen text="鍔犺浇涓?.." />

    <view v-else-if="item" class="content">
      <view class="card">
        <!-- 绫诲瀷鏍囩 -->
        <view class="type-row">
          <view class="type-tag" :class="'type-' + (item.notification_type || 'system')">
            {{ typeLabel }}
          </view>
          <text class="time">{{ format(item.created_at) }}</text>
        </view>

        <!-- 鏍囬 -->
        <text class="title">{{ item.title || '閫氱煡' }}</text>

        <!-- 姝ｆ枃 -->
        <view class="body">
          <text class="body-text">{{ item.content || '鏆傛棤鍐呭' }}</text>
        </view>

        <!-- 鍏宠仈淇℃伅锛堝鏋滄湁锛?-->
        <view v-if="item.related_id && item.related_type" class="related">
          <text class="related-label">鐩稿叧鍐呭锛?/text>
          <text class="related-link" @tap="openRelated">{{ relatedLabel }}</text>
        </view>
      </view>

      <!-- 闄勫姞鍏冧俊鎭?-->
      <view class="meta-card">
        <view class="meta-row">
          <text class="meta-k">宸茶鐘舵€?/text>
          <text class="meta-v">{{ item.is_read ? '宸茶' : '鏈' }}</text>
        </view>
        <view class="meta-row">
          <text class="meta-k">鎺ユ敹鏃堕棿</text>
          <text class="meta-v">{{ format(item.created_at) }}</text>
        </view>
      </view>
    </view>

    <!-- 鏈壘鍒?-->
    <view v-else-if="!loading && notFound" class="empty">
      <text class="empty-title">閫氱煡涓嶅瓨鍦?/text>
      <text class="empty-desc">璇ラ€氱煡鍙兘宸茶鍒犻櫎</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { getNotificationDetail, markNotificationAsRead } from '@/api/notifications'
import { logger } from '@/logs/logger'
import { formatDateTime } from '@/utils/time'
import LoadingIndicator from '@/components/common/LoadingIndicator.vue'
import ErrorBanner from '@/components/common/ErrorBanner.vue'

type NotificationItem = {
  id: string
  title: string
  content: string
  notification_type: string
  related_id: string | null
  related_type: string | null
  is_read: boolean
  created_at: string
}

const TYPE_LABELS: Record<string, string> = {
  system: '绯荤粺閫氱煡',
  live_start: '鐩存挱寮€濮?,
  live_end: '鐩存挱缁撴潫',
  live: '鐩存挱鎻愰啋',
  follow: '鍏虫敞',
  like: '鐐硅禐',
  comment: '璇勮',
  message: '绉佷俊',
  announcement: '鍏憡'
}

const item = ref<NotificationItem | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)
const notFound = ref(false)

const typeLabel = computed(() => {
  if (!item.value) return ''
  return TYPE_LABELS[item.value.notification_type] || item.value.notification_type || '閫氱煡'
})

const relatedLabel = computed(() => {
  if (!item.value?.related_type) return ''
  const map: Record<string, string> = {
    session: '鏌ョ湅鐩存挱闂?,
    room: '鏌ョ湅鎴块棿',
    expert: '鏌ョ湅涓撳',
    brand: '鏌ョ湅鍝佺墝',
    topic: '鏌ョ湅涓撻'
  }
  return map[item.value.related_type] || '鏌ョ湅璇︽儏'
})

function format(t: string) {
  try {
    return formatDateTime(t)
  } catch {
    return t
  }
}

function openRelated() {
  if (!item.value?.related_id || !item.value?.related_type) return
  const { related_type: type, related_id: id } = item.value
  const routes: Record<string, string> = {
    session: `/pages/live/LiveView?sessionId=${encodeURIComponent(id)}`,
    room: `/pages/live/LiveView?roomId=${encodeURIComponent(id)}`,
    expert: `/pages/expert/ExpertDetail?id=${encodeURIComponent(id)}`,
    brand: `/pages/brand/BrandDetail?id=${encodeURIComponent(id)}`
  }
  const url = routes[type]
  if (url) {
    logger.info('user', '鐐瑰嚮閫氱煡鍏宠仈鍐呭', {
      notificationId: item.value.id,
      relatedId: id,
      relatedType: type,
      targetUrl: url
    })
    uni.navigateTo({ url })
  }
}

async function load(id: string) {
  loading.value = true
  error.value = null
  notFound.value = false

  logger.info('network', '寮€濮嬪姞杞介€氱煡璇︽儏', {
    notificationId: id
  })

  try {
    const resp = await getNotificationDetail(id)
    if (resp.code !== 200 || !resp.data) {
      throw new Error(resp.message || '鍔犺浇澶辫触')
    }
    item.value = resp.data as NotificationItem

    logger.info('network', '閫氱煡璇︽儏鍔犺浇鎴愬姛', {
      notificationId: id,
      notificationType: item.value.notification_type,
      isRead: item.value.is_read,
      relatedId: item.value.related_id,
      relatedType: item.value.related_type
    })

    // 鑷姩鏍囪宸茶
    if (item.value && !item.value.is_read) {
      try {
        const mr = await markNotificationAsRead(id)
        if (mr.code === 200) {
          item.value.is_read = true
          logger.info('network', '閫氱煡璇︽儏鑷姩鏍囪宸茶鎴愬姛', {
            notificationId: id
          })
        } else {
          logger.warn('network', '閫氱煡璇︽儏鑷姩鏍囪宸茶杩斿洖闈?00', {
            notificationId: id,
            code: mr.code,
            message: mr.message
          })
        }
      } catch (err: any) {
        logger.warn('network', '閫氱煡璇︽儏鑷姩鏍囪宸茶澶辫触', {
          notificationId: id,
          message: err?.message || err
        })
      }
    }
  } catch (e: any) {
    const msg = e?.message || '鍔犺浇閫氱煡璇︽儏澶辫触'
    if (msg.includes('404') || msg.includes('涓嶅瓨鍦?)) {
      notFound.value = true
      logger.warn('network', '閫氱煡璇︽儏涓嶅瓨鍦?, {
        notificationId: id,
        message: msg
      })
    } else {
      error.value = msg
      logger.error('network', '閫氱煡璇︽儏鍔犺浇澶辫触', {
        notificationId: id,
        message: msg
      })
    }
  } finally {
    loading.value = false
  }
}

onLoad((options: any) => {
  const id = options?.id
  logger.info('user', '杩涘叆閫氱煡璇︽儏椤?, {
    notificationId: id || ''
  })
  if (id) {
    load(id)
  } else {
    notFound.value = true
    loading.value = false
    logger.warn('user', '閫氱煡璇︽儏缂哄皯id鍙傛暟')
  }
})
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.page {
  min-height: 100vh;
  background: var(--color-background);
  padding: var(--spacing-md);
  box-sizing: border-box;
}

.content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

/* ===== 涓诲崱鐗?===== */
.card {
  background: var(--color-surface);
  border-radius: var(--border-radius-md);
  padding: var(--spacing-lg);
}

.type-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-md);
}

.type-tag {
  display: inline-block;
  padding: 2px 10px;
  border-radius: var(--border-radius-full);
  font-size: 12px;
  font-weight: 500;
  line-height: 20px;

  &.type-system {
    background: var(--color-info-light);
    color: var(--color-info);
  }
  &.type-live,
  &.type-live_start,
  &.type-live_end {
    background: var(--color-success-light);
    color: var(--color-success);
  }
  &.type-follow {
    background: var(--color-primary-light);
    color: var(--color-primary);
    opacity: 0.15;
    color: var(--color-primary);
    background: rgba(15, 118, 110, 0.1);
  }
  &.type-like {
    background: var(--color-danger-light);
    color: var(--color-danger);
  }
  &.type-comment,
  &.type-message {
    background: var(--color-warning-light);
    color: var(--color-warning);
  }
  &.type-announcement {
    background: var(--color-primary-light);
    color: var(--color-primary);
    background: rgba(15, 118, 110, 0.1);
    color: var(--color-primary);
  }
}

.time {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
  line-height: 1.4;
  margin-bottom: var(--spacing-md);
  display: block;
}

.body {
  border-top: 1px solid var(--color-border);
  padding-top: var(--spacing-md);
}

.body-text {
  font-size: 15px;
  color: var(--color-text-regular);
  line-height: 1.75;
  white-space: pre-wrap;
  word-break: break-all;
}

/* ===== 鍏宠仈鍐呭 ===== */
.related {
  margin-top: var(--spacing-lg);
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  gap: 6px;
}

.related-label {
  font-size: 13px;
  color: var(--color-text-secondary);
}

.related-link {
  font-size: 13px;
  color: var(--color-primary);
}

/* ===== 鍏冧俊鎭崱鐗?===== */
.meta-card {
  background: var(--color-surface);
  border-radius: var(--border-radius-md);
  padding: var(--spacing-sm) var(--spacing-lg);
}

.meta-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid var(--color-border);

  &:last-of-type {
    border-bottom: none;
  }
}

.meta-k {
  font-size: 13px;
  color: var(--color-text-secondary);
}

.meta-v {
  font-size: 13px;
  color: var(--color-text-regular);
}

/* ===== 绌烘€?===== */
.empty {
  background: var(--color-surface);
  border-radius: var(--border-radius-md);
  padding: 60px var(--spacing-lg);
  text-align: center;
}

.empty-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.empty-desc {
  display: block;
  margin-top: 8px;
  font-size: 13px;
  color: var(--color-text-secondary);
}
</style>
