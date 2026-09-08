<template>
  <view class="page">
    <ErrorBanner v-if="error" :message="error" @close="error = null" />

    <LoadingIndicator v-if="loading && !loaded" fullscreen text="加载通知中..." />

    <view v-else class="content">
      <view v-if="!loading && items.length === 0" class="empty">
        <text class="empty-title">暂无通知</text>
        <text class="empty-desc">有新消息时会在这里显示</text>
      </view>

      <view v-else class="list">
        <view v-for="it in items" :key="it.id" class="row" @tap="openOrRead(it)">
          <view class="dot" :class="{ 'is-read': it.is_read }" aria-hidden="true" />
          <view class="meta">
            <text class="title">{{ it.title || '通知' }}</text>
            <text v-if="it.content" class="desc">{{ it.content }}</text>
            <text class="sub">{{ format(it.created_at) }}</text>
          </view>
        </view>

        <view v-if="loadingMore" class="more">加载更多...</view>
        <view v-else-if="!hasMore" class="more">没有更多了</view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { onLoad, onPullDownRefresh, onReachBottom, onShow } from '@dcloudio/uni-app'
import { useAuthStore } from '@/store/auth'
import { getNotificationList, markNotificationAsRead } from '@/api/notifications'
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

const authStore = useAuthStore()

const items = ref<NotificationItem[]>([])
const loading = ref(false)
const loadingMore = ref(false)
const loaded = ref(false)
const error = ref<string | null>(null)

const page = ref(1)
const size = ref(20)
const total = ref(0)
const hasMore = computed(() => page.value * size.value < total.value)

function ensureLoginOrBack(): boolean {
  if (authStore.isAuthenticated) return true
  logger.warn('user', '进入通知列表失败：未登录')
  uni.showToast({ title: '请先登录', icon: 'none' })
  setTimeout(() => uni.navigateBack({ delta: 1 }), 300)
  return false
}

function format(t: string) {
  try {
    return formatDateTime(t)
  } catch {
    return t
  }
}

async function load(refresh = false) {
  if (refresh) {
    page.value = 1
    total.value = 0
  }

  if (!refresh && loaded.value && !hasMore.value) return

  try {
    error.value = null
    if (refresh) loading.value = true
    else loadingMore.value = true

    logger.info('network', '开始加载通知列表', {
      refresh,
      page: page.value,
      size: size.value
    })

    const resp = await getNotificationList({
      page: page.value,
      size: size.value,
      sort: 'created_at:desc'
    })

    if (resp.code !== 200 || !resp.data) {
      throw new Error(resp.message || '加载通知失败')
    }

    const { items: list, total: t, page: p, size: s } = resp.data

    total.value = t
    size.value = s
    page.value = p

    if (refresh) items.value = list as any
    else items.value.push(...(list as any))

    loaded.value = true

    logger.info('network', '通知列表加载成功', {
      refresh,
      page: page.value,
      size: size.value,
      total: total.value,
      loadedCount: items.value.length
    })
  } catch (e: any) {
    error.value = e?.message || '加载通知失败'
    logger.error('network', '通知列表加载失败', e)
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

function openOrRead(it: NotificationItem) {
  logger.info('user', '点击通知条目', {
    notificationId: it.id,
    notificationType: it.notification_type,
    isRead: it.is_read,
    relatedId: it.related_id,
    relatedType: it.related_type
  })

  uni.navigateTo({
    url: `/pages/profile/NotificationDetail?id=${encodeURIComponent(it.id)}`,
    success: () => {
      logger.info('user', '通知详情跳转成功', {
        notificationId: it.id
      })
    },
    fail: () => {
      logger.error('user', '通知详情跳转失败', {
        notificationId: it.id
      })
      uni.showToast({ title: '进入详情失败', icon: 'none' })
    }
  })

  if (it.is_read) return

  void markNotificationAsRead(it.id)
    .then(resp => {
      if (resp.code === 200) {
        it.is_read = true
        logger.info('network', '通知已标记为已读', {
          notificationId: it.id
        })
      } else {
        logger.warn('network', '通知标记已读返回非200', {
          notificationId: it.id,
          code: resp.code,
          message: resp.message
        })
      }
    })
    .catch((err: any) => {
      logger.warn('network', '通知标记已读失败', {
        notificationId: it.id,
        message: err?.message || err
      })
    })
}

/** 首次 onLoad；再次进入 onShow 刷新（N2） */
const initialLoadDone = ref(false)

onLoad(async () => {
  logger.info('user', '进入通知列表页')
  if (!ensureLoginOrBack()) return
  await load(true)
  initialLoadDone.value = true
})

onShow(async () => {
  if (!initialLoadDone.value) return
  if (!authStore.isAuthenticated) return
  logger.info('user', '通知列表 onShow 刷新')
  await load(true)
})

onPullDownRefresh(async () => {
  logger.info('user', '通知列表下拉刷新')
  await load(true)
  uni.stopPullDownRefresh()
})

onReachBottom(async () => {
  if (!hasMore.value) return
  logger.info('user', '通知列表触底加载更多', {
    nextPage: page.value + 1
  })
  page.value += 1
  await load(false)
})
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.page {
  min-height: 100vh;
  background: var(--color-background);
  padding: 0;
  box-sizing: border-box;
}

.top-actions {
  display: flex;
  justify-content: flex-end;
  padding: var(--spacing-sm) var(--spacing-lg);
  margin-bottom: 0;
}

.link {
  background: var(--color-surface);
  color: var(--color-primary);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-full);
}

.list {
  background: var(--color-surface);
  border-top: 1px solid var(--color-border);
  border-bottom: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  gap: 0;
}

.row {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  background: var(--color-surface);
  border-radius: 0;
  padding: var(--spacing-md) var(--spacing-lg);
  box-shadow: none;
  border-bottom: 1px solid var(--color-border);
}

.row:last-of-type {
  border-bottom: none;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-primary);
  margin-top: 6px;
  flex-shrink: 0;
}

.dot.is-read {
  background: var(--color-border);
}

.meta {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.title {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.desc {
  font-size: 13px;
  color: var(--color-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  line-clamp: 2;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.sub {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.more {
  text-align: center;
  padding: 12px 0;
  color: var(--color-text-tertiary);
  font-size: 12px;
}

.empty {
  background: var(--color-surface);
  border-top: 1px solid var(--color-border);
  padding: 40px var(--spacing-lg);
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

.primary {
  margin-top: 16px;
  background: var(--color-primary);
  color: var(--color-text-inverse);
  border-radius: var(--border-radius-full);
}
</style>
