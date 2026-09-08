<template>
  <view class="page">
    <ErrorBanner v-if="error" :message="error" @close="error = null" />

    <LoadingIndicator v-if="loading" fullscreen text="加载中..." />

    <view v-else-if="item" class="content">
      <view class="card">
        <!-- 类型标签 -->
        <view class="type-row">
          <view class="type-tag" :class="'type-' + (item.notification_type || 'system')">
            {{ typeLabel }}
          </view>
          <text class="time">{{ format(item.created_at) }}</text>
        </view>

        <!-- 标题 -->
        <text class="title">{{ item.title || '通知' }}</text>

        <!-- 正文 -->
        <view class="body">
          <text class="body-text">{{ item.content || '暂无内容' }}</text>
        </view>

        <!-- 关联信息（如果有） -->
        <view v-if="item.related_id && item.related_type" class="related">
          <text class="related-label">相关内容：</text>
          <text class="related-link" @tap="openRelated">{{ relatedLabel }}</text>
        </view>
      </view>

      <!-- 附加元信息 -->
      <view class="meta-card">
        <view class="meta-row">
          <text class="meta-k">已读状态</text>
          <text class="meta-v">{{ item.is_read ? '已读' : '未读' }}</text>
        </view>
        <view class="meta-row">
          <text class="meta-k">接收时间</text>
          <text class="meta-v">{{ format(item.created_at) }}</text>
        </view>
      </view>
    </view>

    <!-- 未找到 -->
    <view v-else-if="!loading && notFound" class="empty">
      <text class="empty-title">通知不存在</text>
      <text class="empty-desc">该通知可能已被删除</text>
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
  system: '系统通知',
  live_start: '直播开始',
  live_end: '直播结束',
  live: '直播提醒',
  follow: '关注',
  like: '点赞',
  comment: '评论',
  message: '私信',
  announcement: '公告'
}

const item = ref<NotificationItem | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)
const notFound = ref(false)

const typeLabel = computed(() => {
  if (!item.value) return ''
  return TYPE_LABELS[item.value.notification_type] || item.value.notification_type || '通知'
})

const relatedLabel = computed(() => {
  if (!item.value?.related_type) return ''
  const map: Record<string, string> = {
    session: '查看直播间',
    room: '查看房间',
    expert: '查看专家',
    brand: '查看品牌',
    topic: '查看专题'
  }
  return map[item.value.related_type] || '查看详情'
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
    logger.info('user', '点击通知关联内容', {
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

  logger.info('network', '开始加载通知详情', {
    notificationId: id
  })

  try {
    const resp = await getNotificationDetail(id)
    if (resp.code !== 200 || !resp.data) {
      throw new Error(resp.message || '加载失败')
    }
    item.value = resp.data as NotificationItem

    logger.info('network', '通知详情加载成功', {
      notificationId: id,
      notificationType: item.value.notification_type,
      isRead: item.value.is_read,
      relatedId: item.value.related_id,
      relatedType: item.value.related_type
    })

    // 自动标记已读
    if (item.value && !item.value.is_read) {
      try {
        const mr = await markNotificationAsRead(id)
        if (mr.code === 200) {
          item.value.is_read = true
          logger.info('network', '通知详情自动标记已读成功', {
            notificationId: id
          })
        } else {
          logger.warn('network', '通知详情自动标记已读返回非200', {
            notificationId: id,
            code: mr.code,
            message: mr.message
          })
        }
      } catch (err: any) {
        logger.warn('network', '通知详情自动标记已读失败', {
          notificationId: id,
          message: err?.message || err
        })
      }
    }
  } catch (e: any) {
    const msg = e?.message || '加载通知详情失败'
    if (msg.includes('404') || msg.includes('不存在')) {
      notFound.value = true
      logger.warn('network', '通知详情不存在', {
        notificationId: id,
        message: msg
      })
    } else {
      error.value = msg
      logger.error('network', '通知详情加载失败', {
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
  logger.info('user', '进入通知详情页', {
    notificationId: id || ''
  })
  if (id) {
    load(id)
  } else {
    notFound.value = true
    loading.value = false
    logger.warn('user', '通知详情缺少id参数')
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

/* ===== 主卡片 ===== */
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

/* ===== 关联内容 ===== */
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

/* ===== 元信息卡片 ===== */
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

/* ===== 空态 ===== */
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
