<template>
  <view class="page">
    <ErrorBanner v-if="error" :message="error" @close="error = null" />

    <LoadingIndicator v-if="loading && !loaded" fullscreen text="加载历史中..." />

    <view v-else class="content">
      <view class="top-actions">
          <view
            class="seg"
            :class="{ active: sessionType === 'scheduled' }"
            @tap="switchType('scheduled')"
          >
            预告
          </view>
          <view
            class="seg"
            :class="{ active: sessionType === 'live' }"
            @tap="switchType('live')"
          >
            直播中
          </view>
          <view
            class="seg"
            :class="{ active: sessionType === 'replay' }"
            @tap="switchType('replay')"
          >
            回放
          </view>
        </view>

      <view v-if="!loading && items.length === 0" class="empty">
        <text class="empty-title">暂无观看历史</text>
        <text class="empty-desc">看过的预告、直播、回放会出现在这里</text>
      </view>

      <view v-else class="list">
        <view v-for="it in items" :key="it.id" class="row" @tap="openSession(it.session_id)">
          <image class="cover" :src="getCoverSrc(it.id, it.room_cover_url)" mode="aspectFill" @error="handleCoverError(it.id, it.room_cover_url)" />
          <view class="meta">
            <view class="meta-header">
              <text class="title">{{ it.session_title || '未命名场次' }}</text>
              <view class="status-pill" :class="getStatusClass(it)">
                {{ getStatusText(it) }}
              </view>
            </view>
            <text v-if="getStatusHint(it)" class="status-hint">{{ getStatusHint(it) }}</text>
            <text class="sub">观看进度：{{ formatProgress(it.progress) }}</text>
            <text class="sub">最近观看：{{ format(it.watched_at) }}</text>
          </view>
          <button class="danger" size="mini" @tap.stop="onRemove(it.id)">删除</button>
        </view>

        <view v-if="loadingMore" class="more">加载更多...</view>
      </view>

      <view v-if="!loadingMore && !hasMore && items.length > 0" class="no-more-plain">没有更多了</view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { onLoad, onShow, onPullDownRefresh, onReachBottom } from '@dcloudio/uni-app'
import { storeToRefs } from 'pinia'
import { logger } from '@/logs/logger'
import { useAuthStore } from '@/store/auth'
import { useWatchHistoryStore } from '@/store/watchHistory'
import { formatDateTime, formatFriendlyDuration } from '@/utils/time'
import { resolveCoverUrl, shouldMarkCoverBroken } from '@/utils/url'
import LoadingIndicator from '@/components/common/LoadingIndicator.vue'
import ErrorBanner from '@/components/common/ErrorBanner.vue'

const authStore = useAuthStore()
const historyStore = useWatchHistoryStore()

const { items, loading, loadingMore, sessionType } = storeToRefs(historyStore)
const hasMore = computed(() => historyStore.hasMore)

const loaded = ref(false)
const error = ref<string | null>(null)
const brokenCoverIds = ref<Record<string, true>>({})

function getCoverSrc(id: string, url: string) {
  return resolveCoverUrl(url, !!brokenCoverIds.value[id])
}

function handleCoverError(id: string, url: string) {
  if (brokenCoverIds.value[id]) return
  if (!shouldMarkCoverBroken(url, !!brokenCoverIds.value[id])) return
  logger.warn('system', 'cover_load_failed', {
    page: 'watch_history',
    itemId: id,
    rawCoverUrl: url || null,
    reason: String(url || '').trim() ? 'cover_url_unreachable' : 'missing_cover_field'
  })
  brokenCoverIds.value = {
    ...brokenCoverIds.value,
    [id]: true
  }
}

async function switchType(type: 'scheduled' | 'live' | 'replay') {
  logger.info('system', 'watch_history_tab_switch_start', {
    from: historyStore.sessionType,
    to: type,
    currentCount: items.value.length
  })
  try {
    await historyStore.setSessionType(type)
    logger.info('system', 'watch_history_tab_switch_done', {
      to: type,
      count: items.value.length,
      rows: items.value.slice(0, 30).map(it => ({
        id: it.id,
        session_id: it.session_id,
        session_type: it.session_type || 'unknown',
        session_status: it.session_status || 'unknown',
        watched_at: it.watched_at
      }))
    })
  } catch (e: any) {
    uni.showToast({ title: e?.message || '切换失败', icon: 'none' })
  }
}

function getStatusText(it: { session_type?: string; session_status?: string }) {
  const type = String(it.session_type || '')
  const status = String(it.session_status || '').toLowerCase()

  if (type === 'scheduled') {
    if (status === 'live') return '已开播'
    if (status === 'ended' || status === 'replay' || status === 'playback') return '已结束'
    return '预告'
  }

  if (type === 'replay') return '回放'
  if (status === 'ended' || status === 'replay' || status === 'playback') return '已结束'
  return '直播中'
}

function getStatusHint(it: { session_type?: string; session_status?: string }) {
  if (String(it.session_type || '') !== 'scheduled') return ''
  if (String(it.session_status || '').toLowerCase() === 'live') return '该预告已开始直播'
  return ''
}

function getStatusClass(it: { session_type?: string; session_status?: string }) {
  const type = String(it.session_type || '')
  const status = String(it.session_status || '').toLowerCase()
  if (type === 'scheduled' && status === 'live') return 'status-pill--live-now'
  if (type === 'scheduled') return 'status-pill--scheduled'
  if (type === 'replay' || status === 'ended' || status === 'replay' || status === 'playback') return 'status-pill--replay'
  return 'status-pill--live'
}

function ensureLoginOrBack(): boolean {
  if (authStore.isAuthenticated) return true
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

function formatProgress(seconds: number) {
  if (!seconds || seconds <= 0) return '0秒'
  return formatFriendlyDuration(seconds)
}

async function load(refresh = false) {
  try {
    error.value = null
    if (refresh) await historyStore.refresh()
    else await historyStore.fetch()
    loaded.value = true
  } catch (e: any) {
    error.value = e?.message || '加载历史失败'
  }
}

async function onRemove(historyId: string) {
  try {
    await historyStore.remove(historyId)
    uni.showToast({ title: '已删除', icon: 'success' })
  } catch (e: any) {
    uni.showToast({ title: e?.message || '删除失败', icon: 'none' })
  }
}

function openSession(sessionId: string) {
  uni.navigateTo({ url: `/pages/live/LiveView?sessionId=${encodeURIComponent(sessionId)}` })
}

onLoad(async () => {
  if (!ensureLoginOrBack()) return
  await load(false)
})

onShow(async () => {
  if (!authStore.isAuthenticated) return
  if (!loaded.value) return
  brokenCoverIds.value = {}
  try {
    await historyStore.refresh()
  } catch {
    // ignore
  }
})

onPullDownRefresh(async () => {
  await load(true)
  uni.stopPullDownRefresh()
})

onReachBottom(async () => {
  if (!hasMore.value) return
  try {
    await historyStore.loadMore()
  } catch {
    // ignore
  }
})

watch(
  () => items.value,
  (list) => {
    const map: Record<string, string[]> = {}
    for (const it of list) {
      const sid = String(it.session_id || '').trim()
      if (!sid) continue
      const t = String(it.session_type || 'unknown')
      if (!map[sid]) map[sid] = []
      if (!map[sid].includes(t)) map[sid].push(t)
    }

    const conflicts = Object.entries(map)
      .filter(([, types]) => types.length > 1)
      .map(([session_id, types]) => ({ session_id, types }))

    logger.info('system', 'watch_history_view_items_changed', {
      tab: sessionType.value,
      count: list.length,
      rows: list.slice(0, 30).map(it => ({
        id: it.id,
        session_id: it.session_id,
        session_type: it.session_type || 'unknown',
        session_status: it.session_status || 'unknown',
        watched_at: it.watched_at
      })),
      conflictCount: conflicts.length,
      conflicts
    })
  },
  { immediate: true }
)
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
  gap: 8px;
  padding: var(--spacing-sm) var(--spacing-lg);
  margin-bottom: 0;
}

.seg {
  flex: 1;
  text-align: center;
  padding: 8px 0;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-full);
  background: var(--color-surface);
  color: var(--color-text-secondary);
  font-size: 13px;
}

.seg.active {
  border-color: var(--color-primary);
  color: var(--color-primary);
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
  align-items: center;
  background: var(--color-surface);
  border-radius: 0;
  padding: var(--spacing-md) var(--spacing-lg);
  box-shadow: none;
  border-bottom: 1px solid var(--color-border);
}

.row:last-of-type {
  border-bottom: none;
}

.cover {
  width: 88px;
  height: 56px;
  border-radius: var(--border-radius-base);
  background: var(--color-bg-tertiary);
}

.meta {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.meta-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
}

.title {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  min-width: 0;
}

.sub {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.status-pill {
  flex: 0 0 auto;
  font-size: 11px;
  line-height: 1;
  padding: 4px 8px;
  border-radius: var(--border-radius-full);
  background: var(--color-bg-tertiary);
  color: var(--color-text-secondary);
}

.status-pill--scheduled {
  background: rgba(245, 158, 11, 0.12);
  color: #b45309;
}

.status-pill--live,
.status-pill--live-now {
  background: rgba(220, 38, 38, 0.12);
  color: #b91c1c;
}

.status-pill--replay {
  background: rgba(59, 130, 246, 0.12);
  color: #1d4ed8;
}

.status-hint {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.danger {
  background: var(--color-danger-light);
  color: var(--color-danger);
  border-radius: var(--border-radius-full);
}

.more {
  text-align: center;
  padding: 12px 0;
  color: var(--color-text-tertiary);
  font-size: $font-size-sm;
}

.no-more-plain {
  text-align: center;
  padding: $spacing-base 0 40rpx;
  color: var(--color-text-tertiary);
  font-size: $font-size-sm;
}

.empty {
  background: var(--color-surface);
  border-top: 1px solid var(--color-border);
  border-bottom: 1px solid var(--color-border);
  border-radius: 0;
  padding: 24px 16px;
  text-align: center;
  box-shadow: none;
}

.empty-title {
  display: block;
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 6px;
}

.empty-desc {
  display: block;
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-bottom: 12px;
}

.primary {
  background: var(--color-primary);
  color: var(--color-text-inverse);
  border-radius: var(--border-radius-full);
}
</style>
