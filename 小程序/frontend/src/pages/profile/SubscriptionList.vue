<template>
  <view class="page">
    <ErrorBanner v-if="error" :message="error" @close="error = null" />

    <LoadingIndicator v-if="loading && !loaded" fullscreen text="加载订阅中..." />

    <view v-else class="content">
      <view v-if="!loading && items.length === 0" class="empty">
        <text class="empty-title">暂无订阅</text>
        <text class="empty-desc">订阅直播间后可收到开播提醒</text>
      </view>

      <view v-else class="list">
        <view v-for="it in items" :key="it.id" class="row" @tap="openRoom(it.room_id)">
          <image class="cover" :src="getCoverSrc(it.room_id, it.room_cover_url)" mode="aspectFill" @error="handleCoverError(it.room_id, it.room_cover_url)" />
          <view class="meta">
            <text class="title">{{ it.room_title || '未命名直播间' }}</text>
            <text class="sub">订阅时间：{{ format(it.created_at) }}</text>
          </view>
          <button class="danger" size="mini" @tap.stop="onRemove(it.room_id)">取消</button>
        </view>

        <view v-if="loadingMore" class="more">加载更多...</view>
      </view>

      <view v-if="!loadingMore && !hasMore && items.length > 0" class="no-more-plain">没有更多了</view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { onLoad, onShow, onPullDownRefresh, onReachBottom } from '@dcloudio/uni-app'
import { storeToRefs } from 'pinia'
import { logger } from '@/logs/logger'
import { useAuthStore } from '@/store/auth'
import { useUserSubscriptionsStore } from '@/store/userSubscriptions'
import { formatDateTime } from '@/utils/time'
import { resolveCoverUrl, shouldMarkCoverBroken } from '@/utils/url'
import LoadingIndicator from '@/components/common/LoadingIndicator.vue'
import ErrorBanner from '@/components/common/ErrorBanner.vue'

const authStore = useAuthStore()
const subscriptionsStore = useUserSubscriptionsStore()

const { items, loading, loadingMore } = storeToRefs(subscriptionsStore)
const hasMore = computed(() => subscriptionsStore.hasMore)

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
    page: 'subscriptions',
    itemId: id,
    rawCoverUrl: url || null,
    reason: String(url || '').trim() ? 'cover_url_unreachable' : 'missing_cover_field'
  })
  brokenCoverIds.value = {
    ...brokenCoverIds.value,
    [id]: true
  }
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

async function load(refresh = false) {
  try {
    error.value = null
    if (refresh) await subscriptionsStore.refresh()
    else await subscriptionsStore.fetch()
    // 参考收藏/历史：若列表接口缺字段，按 room_id 拉详情补齐，避免封面/标题兜底
    await subscriptionsStore.hydrateMissingRoomInfo()
    loaded.value = true
  } catch (e: any) {
    error.value = e?.message || '加载订阅失败'
  }
}

async function onRemove(roomId: string) {
  try {
    await subscriptionsStore.remove(roomId)
    uni.showToast({ title: '已取消订阅', icon: 'success' })
  } catch (e: any) {
    uni.showToast({ title: e?.message || '取消失败', icon: 'none' })
  }
}

function openRoom(roomId: string) {
  const id = String(roomId || '').trim()
  if (!id) {
    uni.showToast({ title: '房间信息缺失', icon: 'none' })
    return
  }
  uni.navigateTo({ url: `/pages/live/LiveView?roomId=${encodeURIComponent(id)}` })
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
    await subscriptionsStore.refresh()
    await subscriptionsStore.hydrateMissingRoomInfo()
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
    await subscriptionsStore.loadMore()
    // 分页追加后也补齐封面/标题
    void subscriptionsStore.hydrateMissingRoomInfo()
  } catch {
    // ignore
  }
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

.sub {
  font-size: 12px;
  color: var(--color-text-secondary);
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
