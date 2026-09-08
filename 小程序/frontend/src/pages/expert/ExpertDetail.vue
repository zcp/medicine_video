<template>
  <view class="expert-detail">
    <LoadingIndicator v-if="loadingDetail && !dataLoaded" />
    <ErrorBanner v-if="error" :message="error.message" @close="error = null as any" />

    <view v-if="dataLoaded && detail">
      <ExpertProfile
        :avatar="detail.avatar"
        :name="detail.name"
        :title="detail.title"
        :department="detail.department"
        :stats="detail.stats"
        :isFollowing="isFollowing"
        :pending="isFollowPending"
        @toggle-follow="onToggleFollow"
      />

      <!-- 专家介绍（严格对齐后端字段：bio + expertise_areas） -->
      <view class="section">
        <text class="section-title">专家介绍</text>
        <view class="bio">
          <text class="bio-text" v-if="detail.bio">{{ detail.bio }}</text>
          <view class="bio-block" v-if="specialties.length">
            <text class="block-title">擅长领域</text>
            <view class="tags">
              <text v-for="tag in specialties" :key="tag" class="tag">{{ tag }}</text>
            </view>
          </view>
        </view>
      </view>

      <!-- 正在直播 -->
      <view class="section" v-if="liveSessions.length">
        <text class="section-title">正在直播</text>
        <view class="session-list">
          <view class="session-item clickable" v-for="s in liveSessions" :key="s.id" @tap="goLiveSession(s.id)">
            <image class="cover" :src="sessionCoverSrc(s)" mode="aspectFill" @error="onSessionCoverError(s.id, s.cover)" />
            <view class="right">
              <text class="session-title">{{ s.title }}</text>
              <text class="session-meta">直播中</text>
            </view>
            <text v-if="s.roomId" class="iconfont fav" :class="isFav(s.roomId) ? 'icon-shoucang1 active' : 'icon-shoucang'" @tap.stop="toggleFav(s.roomId)"></text>
          </view>
        </view>
      </view>

      <!-- 即将开始 -->
      <view class="section" v-if="upcomingSorted.length">
        <text class="section-title">即将开始</text>
        <view class="session-list">
          <view class="session-item" v-for="s in upcomingSorted" :key="s.id">
            <image class="cover" :src="sessionCoverSrc(s)" mode="aspectFill" @tap="goLiveSession(s.id)" @error="onSessionCoverError(s.id, s.cover)" />
            <view class="right" @tap="goLiveSession(s.id)">
              <text class="session-title">{{ s.title }}</text>
              <text class="session-meta">{{ s.scheduledAt || '—' }}</text>
            </view>
          </view>
        </view>
      </view>

      <!-- 历史直播（时间倒序） -->
      <view class="section">
        <text class="section-title">历史直播</text>
        <view class="session-list">
          <view class="session-item" v-for="s in historySorted" :key="s.id">
            <image class="cover" :src="sessionCoverSrc(s)" mode="aspectFill" @tap="goLiveSession(s.id)" @error="onSessionCoverError(s.id, s.cover)" />
            <view class="right" @tap="goLiveSession(s.id)">
              <text class="session-title">{{ s.title }}</text>
              <text class="session-meta">{{ s.scheduledAt || '—' }}</text>
            </view>
            <text v-if="s.roomId" class="iconfont fav" :class="isFav(s.roomId) ? 'icon-shoucang1 active' : 'icon-shoucang'" @tap.stop="toggleFav(s.roomId)"></text>
          </view>
          <EmptyState v-if="!historySorted.length" title="暂无历史直播" description="稍后再来看看吧" />
        </view>
      </view>
    </view>

    <EmptyState
      v-if="!loadingDetail && !detail"
      :title="error?.message === '专家已下架' ? '专家已下架' : '无法加载专家信息'"
      :description="error?.message === '专家已下架' ? '该专家暂不可访问，直播间内容仍可正常观看' : '请稍后重试'"
    />
  </view>
  
</template>

<script setup lang="ts">
import ExpertProfile from '@/components/expert/ExpertProfile.vue'
import LoadingIndicator from '@/components/common/LoadingIndicator.vue'
import ErrorBanner from '@/components/common/ErrorBanner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { useExpertStore } from '@/store/expert'
import { useAuthStore } from '@/store/auth'
import { useUserFavoritesStore } from '@/store/userFavorites'
import { storeToRefs } from 'pinia'
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { log } from '@/logs/logger'
import { resolveCoverUrl, shouldMarkCoverBroken } from '@/utils/url'

const authStore = useAuthStore()
const expertStore = useExpertStore()
const { detail, sessions, loadingDetail, error, followingMap, followPendingId } = storeToRefs(expertStore)
const dataLoaded = ref(false)
const favStore = useUserFavoritesStore()
const favSet = ref<Set<string>>(new Set())
const favPendingRoomIds = new Set<string>()
const brokenSessionCoverIds = ref<Record<string, true>>({})

function sessionCoverSrc(s: { id: string; cover: string }) {
  return resolveCoverUrl(s.cover, !!brokenSessionCoverIds.value[s.id])
}

function onSessionCoverError(sessionId: string, cover: string) {
  const id = String(sessionId || '').trim()
  if (!id || brokenSessionCoverIds.value[id]) return
  if (!shouldMarkCoverBroken(cover, !!brokenSessionCoverIds.value[id])) return
  brokenSessionCoverIds.value = { ...brokenSessionCoverIds.value, [id]: true }
}

const isFollowing = computed(() => {
  const id = detail.value?.id
  if (!id) return false
  return !!followingMap.value[id]
})

const isFollowPending = computed(() => {
  const id = detail.value?.id
  if (!id) return false
  return followPendingId.value === id
})

function redirectToLogin(expertId?: string) {
  const redirectUrl = expertId
    ? `/pages/expert/ExpertDetail?id=${encodeURIComponent(expertId)}`
    : '/pages/expert/ExpertDetail'
  uni.navigateTo({ url: `/pages/auth/OneTapLogin?redirect=${encodeURIComponent(redirectUrl)}` })
}

function ensureAuthed(expertId?: string): boolean {
  if (authStore.isAuthenticated) return true
  uni.showToast({ title: '请先登录', icon: 'none' })
  setTimeout(() => redirectToLogin(expertId), 250)
  return false
}

// 基础展示派生（严格按后端：expertise_areas -> specialization）
const specialties = computed(() => (detail.value?.specialization ?? []) as string[])

// 分组与排序
const liveSessions = computed(() => (sessions.value || []).filter(s => s.status === 'live'))
const upcomingSorted = computed(() => {
  const scheduled = (sessions.value || []).filter(s => s.status === 'scheduled')
  return scheduled.sort((a, b) => {
    const ta = a.scheduledAt ? Date.parse(a.scheduledAt) : 0
    const tb = b.scheduledAt ? Date.parse(b.scheduledAt) : 0
    return ta - tb
  })
})
const historySorted = computed(() => {
  const ended = (sessions.value || []).filter(s => s.status === 'ended')
  return ended.sort((a, b) => {
    const ta = a.scheduledAt ? Date.parse(a.scheduledAt) : 0
    const tb = b.scheduledAt ? Date.parse(b.scheduledAt) : 0
    return tb - ta
  })
})

function isFav(roomId: string) {
  return favSet.value.has(roomId)
}
async function toggleFav(roomId: string) {
  const expertId = detail.value?.id
  if (!ensureAuthed(expertId)) return

  const rid = String(roomId || '').trim()
  if (!rid) return
  if (favPendingRoomIds.has(rid)) return

  favPendingRoomIds.add(rid)
  try {
    if (favSet.value.has(rid)) {
      await favStore.remove(rid)
      favSet.value.delete(rid)
      uni.showToast({ title: '已取消收藏', icon: 'none' })
      log.userAction({ action: 'unfavorite_room', pagePath: '/pages/expert/ExpertDetail', params: { roomId: rid }, result: 'success' })
    } else {
      await favStore.add(rid)
      favSet.value.add(rid)
      uni.showToast({ title: '已收藏', icon: 'success' })
      log.userAction({ action: 'favorite_room', pagePath: '/pages/expert/ExpertDetail', params: { roomId: rid }, result: 'success' })
    }
  } catch (e: any) {
    uni.showToast({ title: e?.message || '操作失败', icon: 'none' })
    log.userAction({ action: 'favorite_toggle_failed', pagePath: '/pages/expert/ExpertDetail', params: { roomId: rid }, result: 'failure' })
  } finally {
    favPendingRoomIds.delete(rid)
  }
}

function goLiveSession(sessionId: string) {
  const sid = String(sessionId || '')
  if (!sid) return
  uni.navigateTo({ url: `/pages/live/LiveView?id=${encodeURIComponent(sid)}` })
  log.userAction({ action: 'goto_live_session', pagePath: '/pages/expert/ExpertDetail', params: { sessionId: sid }, result: 'success' })
}

async function onToggleFollow() {
  const id = detail.value?.id
  if (!id) return
  if (!ensureAuthed(id)) return

  const wasFollowing = !!followingMap.value[id]
  try {
    await expertStore.toggleFollow(id)
    uni.showToast({ title: wasFollowing ? '已取消关注' : '已关注', icon: wasFollowing ? 'none' : 'success' })
    log.userAction({ action: wasFollowing ? 'unfollow_expert' : 'follow_expert', pagePath: '/pages/expert/ExpertDetail', params: { expertId: id }, result: 'success' })
  } catch (e: any) {
    uni.showToast({ title: e?.message || '操作失败', icon: 'none' })
    log.userAction({ action: 'follow_toggle_failed', pagePath: '/pages/expert/ExpertDetail', params: { expertId: id }, result: 'failure' })
  }
}

// 读取页面参数并加载数据
// @ts-ignore
onLoad((options: any) => {
  const id: string | undefined = options?.id
  log.userAction({ action: 'open_expert_detail', pagePath: '/pages/expert/ExpertDetail', params: { id }, result: id ? 'success' : 'failure' })
  if (id) {
    const isAuthed = authStore.isAuthenticated
    Promise.all([
      expertStore.fetchExpertById(id),
      expertStore.fetchExpertSessions(id),
      // 关注状态属用户态接口：未登录跳过，避免 401 误弹
      isAuthed ? expertStore.checkFollow(id) : Promise.resolve()
    ]).then(async () => {
      // 收藏列表同属用户态：仅登录后拉取；匿名浏览只展示公开内容
      if (isAuthed) {
        try {
          if (!favStore.items.length) {
            await favStore.fetch({ page: 1, size: 50 })
          }
        } catch {}

        const rawRoomIds = (sessions.value || []).map(s => s.roomId).filter(Boolean) as string[]
        const roomIds = Array.from(new Set(rawRoomIds.map(v => String(v || '').trim()).filter(Boolean)))

        // 逐个对齐后端收藏状态（避免仅靠分页列表导致状态错误）
        const statusList = await Promise.all(roomIds.map(rid => favStore.checkStatus(rid)))
        const set = new Set<string>()
        roomIds.forEach((rid, idx) => {
          if (statusList[idx]) set.add(rid)
        })
        favSet.value = set
      } else {
        favSet.value = new Set()
      }

      dataLoaded.value = true
      log.userAction({ action: 'expert_detail_loaded', pagePath: '/pages/expert/ExpertDetail', params: { id, sessions: sessions.value.length }, result: 'success' })
    }).catch((e: any) => {
      dataLoaded.value = true
      log.userAction({ action: 'expert_detail_loaded', pagePath: '/pages/expert/ExpertDetail', params: { id, error: e?.message }, result: 'failure' })
    })
  }
})
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.expert-detail {
  min-height: 100vh;
  background: var(--color-background);
  padding: 0;
  box-sizing: border-box;
}

.section {
  margin-top: 0;
  background: var(--color-surface);
  border-radius: 0;
  padding: var(--spacing-md) var(--spacing-lg);
  box-shadow: none;
  border-bottom: 1px solid var(--color-border);
}

.section:first-of-type {
  border-top: 1px solid var(--color-border);
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.bio {
  margin-top: var(--spacing-sm);
}

.bio-text {
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.6;
}

.bio-block {
  margin-top: var(--spacing-md);
}

.block-title {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-xs);
  display: block;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tag {
  padding: 4px 10px;
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
  border-radius: var(--border-radius-full);
  font-size: 12px;
}

.session-list {
  margin-top: var(--spacing-sm);
}

.session-item {
  padding: 10px 0;
  border-bottom: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  gap: 10px;
}

.session-item:last-child {
  border-bottom: none;
}

.session-item.clickable {
  cursor: pointer;
}

.cover {
  width: 120rpx;
  height: 90rpx;
  border-radius: var(--border-radius-sm);
  background: var(--color-bg-tertiary);
  flex-shrink: 0;
}

.right {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.session-title {
  font-size: 13px;
  color: var(--color-text-primary);
}

.session-meta {
  font-size: 12px;
  color: var(--color-text-tertiary);
  margin-top: 4px;
  display: block;
}

.fav {
  font-size: 22px;
  color: var(--color-text-tertiary);
  padding: 6px;
}

.fav.active {
  color: var(--color-warning);
}
</style>
