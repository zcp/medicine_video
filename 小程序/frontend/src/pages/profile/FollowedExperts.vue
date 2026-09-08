<template>
  <view class="page">
    <ErrorBanner v-if="error" :message="error" @close="error = null" />

    <LoadingIndicator v-if="loading && !loaded" fullscreen text="加载关注中..." />

    <view v-else class="content">
      <EmptyState
        v-if="!loading && items.length === 0"
        title="暂无关注"
        description="你还没有关注任何专家"
      />

      <view v-else class="list">
        <view v-for="it in items" :key="it.expert_id" class="row" @tap="openExpert(it)">
          <image
            class="avatar"
            :src="avatarSrc(it)"
            mode="aspectFill"
            @error="onAvatarError(it.expert_id, it.avatar_url)"
          />
          <view class="meta">
            <view class="title-row">
              <text class="title">{{ it.name || '未命名专家' }}</text>
              <text v-if="isLive(it)" class="badge">直播中</text>
            </view>
            <text class="sub">{{ [it.title, it.hospital].filter(Boolean).join('｜') || '—' }}</text>
            <text class="sub">关注时间：{{ format(it.subscribed_at) }}</text>
          </view>
          <button class="follow-btn" size="mini" :disabled="unfollowingId === it.expert_id" @tap.stop="onUnfollow(it.expert_id)">
            {{ unfollowingId === it.expert_id ? '取消中...' : '已关注' }}
          </button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { onLoad, onPullDownRefresh, onShow } from '@dcloudio/uni-app'
import { ref } from 'vue'
import { useAuthStore } from '@/store/auth'
import { getMyFollowedExperts, unfollowExpert, type FollowedExpertItem } from '@/api/expert'
import { formatDateTime } from '@/utils/time'
import { resolveAvatarUrl, shouldMarkAvatarBroken } from '@/utils/url'
import LoadingIndicator from '@/components/common/LoadingIndicator.vue'
import ErrorBanner from '@/components/common/ErrorBanner.vue'
import EmptyState from '@/components/common/EmptyState.vue'

const authStore = useAuthStore()

const loading = ref(false)
const loaded = ref(false)
const error = ref<string | null>(null)
const items = ref<FollowedExpertItem[]>([])
const brokenAvatarIds = ref<Record<string, true>>({})
const unfollowingId = ref<string>('')

function avatarSrc(it: FollowedExpertItem): string {
  const id = String(it?.expert_id || '').trim()
  return resolveAvatarUrl(it.avatar_url, id ? !!brokenAvatarIds.value[id] : false)
}

function onAvatarError(expertId: string, raw?: string | null) {
  const id = String(expertId || '').trim()
  if (!id || brokenAvatarIds.value[id]) return
  if (!shouldMarkAvatarBroken(raw, !!brokenAvatarIds.value[id])) return
  brokenAvatarIds.value = { ...brokenAvatarIds.value, [id]: true }
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

function isLive(it: FollowedExpertItem) {
  const s: any = (it as any)?.live_status
  return !!s?.is_live && !!s?.session_id
}

function openExpert(it: FollowedExpertItem) {
  const s: any = (it as any)?.live_status
  if (s?.is_live && s?.session_id) {
    uni.navigateTo({ url: `/pages/live/LiveView?sessionId=${encodeURIComponent(String(s.session_id))}` })
    return
  }
  uni.navigateTo({ url: `/pages/expert/ExpertDetail?id=${encodeURIComponent(String(it.expert_id))}` })
}

async function onUnfollow(expertId: string) {
  if (!expertId || unfollowingId.value) return

  uni.showModal({
    title: '取消关注？',
    content: '取消后将不再接收该专家的相关动态',
    confirmText: '取消关注',
    success: async (res) => {
      if (!res.confirm) return
      unfollowingId.value = expertId
      try {
        const resp: any = await unfollowExpert(expertId)
        if (resp?.code !== 200) throw new Error(resp?.message || '取消关注失败')
        items.value = items.value.filter((x) => x.expert_id !== expertId)
        uni.showToast({ title: '已取消关注', icon: 'success' })
      } catch (e: any) {
        uni.showToast({ title: e?.message || '取消关注失败', icon: 'none' })
      } finally {
        unfollowingId.value = ''
      }
    }
  })
}

async function load() {
  if (loading.value) return
  loading.value = true
  try {
    error.value = null
    const res = await getMyFollowedExperts({ include_live_status: true })
    if (res.code !== 200) throw new Error(res.message || '加载关注失败')
    items.value = Array.isArray(res.data) ? res.data : []
    loaded.value = true
  } catch (e: any) {
    error.value = e?.message || '加载关注失败'
  } finally {
    loading.value = false
  }
}

/** 首次由 onLoad 拉数；再次进入页面由 onShow 刷新（N1） */
const initialLoadDone = ref(false)

onLoad(async () => {
  if (!ensureLoginOrBack()) return
  await load()
  initialLoadDone.value = true
})

onShow(async () => {
  if (!initialLoadDone.value) return
  if (!authStore.isAuthenticated) return
  await load()
})

onPullDownRefresh(async () => {
  await load()
  uni.stopPullDownRefresh()
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
  align-items: center;
  gap: 12px;
  padding: var(--spacing-md) var(--spacing-lg);
  border-bottom: 1px solid var(--color-border);
}

.row:last-child {
  border-bottom: none;
}

.avatar {
  width: 44px;
  height: 44px;
  border-radius: 22px;
  background: var(--color-bg-tertiary);
}

.meta {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 200px;
}

.badge {
  font-size: 11px;
  color: var(--color-text-inverse);
  background: var(--color-primary);
  padding: 2px 6px;
  border-radius: var(--border-radius-full);
}

.sub {
  font-size: 12px;
  color: var(--color-text-tertiary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.value {
  color: var(--color-text-tertiary);
}

.follow-btn {
  height: 28px;
  line-height: 28px;
  font-size: 12px;
  padding: 0 10px;
  border-radius: var(--border-radius-full);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text-secondary);
}

.follow-btn:active {
  opacity: 0.85;
}
</style>
