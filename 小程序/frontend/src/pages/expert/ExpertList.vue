<template>
  <view class="expert-page theme-soft">
    <view class="page-shell panel main-panel">
      <view class="hero">
        <view class="hero-actions">
          <ExpertSearch class="search-box" @search="handleSearch" />
        </view>
        <CategoryTabs
          :categories="categories"
          :active-id="activeCategory"
          :pinned-ids="preferencesStore.pinnedCategoryIds"
          @select="handleCategorySelect"
          @open-all="handleOpenAllCategories"
        />
      </view>

      <LoadingIndicator v-if="loadingList && !dataLoaded" />
      <ErrorBanner v-if="error" :message="error.message" @close="error = null as any" />

      <EmptyState
        v-if="!loadingList && dataLoaded && list.length === 0"
        title="暂无专家"
        description="稍后再试或更换筛选条件"
      />

      <scroll-view
        v-else
        scroll-y
        class="list-shell"
        @scrolltolower="onScrollToLower"
        :lower-threshold="120"
      >
        <view class="card-stack">
          <view v-for="(e, i) in list" :key="e.id || i" class="card-wrapper ui-trans">
            <ExpertCard
              :avatar="e.avatar"
              :name="e.name"
              :title="e.title"
              :department="e.department"
              :specialization="e.specialization"
              :isFollowing="!!followingMap[e.id]"
              :pending="followPendingId === e.id"
              @click="goDetail(e.id)"
              @toggle-follow="onToggleFollow(e.id)"
            />
          </view>
        </view>
        <view class="list-foot" v-if="pagination.hasMore && !loadingList">上拉加载更多</view>
        <view class="list-foot muted" v-else-if="!pagination.hasMore">已经到底啦~</view>
      </scroll-view>
    </view>
  </view>
</template>

<script setup lang="ts">
import ExpertSearch from '@/components/expert/ExpertSearch.vue'
import ExpertCard from '@/components/expert/ExpertCard.vue'
import CategoryTabs from '@/components/home/CategoryTabs.vue'
import LoadingIndicator from '@/components/common/LoadingIndicator.vue'
import ErrorBanner from '@/components/common/ErrorBanner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { useExpertStore } from '@/store/expert'
import { useAuthStore } from '@/store/auth'
import { usePreferencesStore } from '@/store/preferences'
import { getCategoryList } from '@/api/categories'
import { storeToRefs } from 'pinia'
import { computed, ref, watch } from 'vue'
import { onLoad, onPullDownRefresh, onReachBottom, onShow } from '@dcloudio/uni-app'
import { setCustomTabBarSelected } from '@/utils/tabbar'
import { log, logger } from '@/logs/logger'
import type { Category } from '@/types/category'

const authStore = useAuthStore()
const preferencesStore = usePreferencesStore()
const expertStore = useExpertStore()
const { list, loadingList, error, pagination, followingMap, followPendingId } = storeToRefs(expertStore)
const dataLoaded = ref(false)
const categories = ref<Category[]>([])
const activeCategory = ref<string>('recommend')

onShow(() => {
  setCustomTabBarSelected(2)
})

const isLoggedIn = computed(() => authStore.isAuthenticated)

watch(list, (newList) => {
  log.info('page', '[ExpertList] list 变化', {
    length: newList.length,
    firstId: newList[0]?.id,
    firstItemSample: newList[0] ? JSON.stringify(newList[0]).slice(0, 200) : 'null',
    allIds: newList.slice(0, 10).map(e => e.id)
  })
}, { deep: false })

watch(error, (newErr) => {
  if (newErr) {
    log.error('page', '[ExpertList] error 变化', { message: newErr.message })
  }
})

watch(loadingList, (val) => {
  log.info('page', '[ExpertList] loadingList 变化', { loadingList: val, dataLoaded: dataLoaded.value })
})

function redirectToLogin() {
  const redirectUrl = '/pages/expert/ExpertList'
  uni.navigateTo({ url: `/pages/auth/OneTapLogin?redirect=${encodeURIComponent(redirectUrl)}` })
}

function ensureAuthed(): boolean {
  if (authStore.isAuthenticated) return true
  uni.showToast({ title: '请先登录', icon: 'none' })
  setTimeout(() => redirectToLogin(), 250)
  return false
}

function goDetail(id: string) {
  uni.navigateTo({ url: `/pages/expert/ExpertDetail?id=${id}` })
}

async function loadCategories() {
  try {
    const list = await getCategoryList()
    categories.value = (list || []).filter((c) => c?.id && c?.name && c?.is_active !== false)
  } catch (e) {
    logger.error('system', '专家页科室分类加载失败', { error: e })
    categories.value = []
  }
}

async function loadData(refresh = false) {
  // 根分类筛选优先；清空旧 specialty 文本筛，避免与 category_id 叠死
  expertStore.specialty = ''
  expertStore.categoryId =
    activeCategory.value && activeCategory.value !== 'recommend' ? activeCategory.value : ''
  log.info('page', '[ExpertList] loadData 开始', {
    refresh,
    currentPage: pagination.value.page,
    pageSize: pagination.value.pageSize,
    categoryId: expertStore.categoryId,
    isAdmin: authStore.isAdmin,
    isLoggedIn: authStore.isAuthenticated
  })
  const nextPage = refresh ? 1 : (pagination.value.page || 1)
  await expertStore.fetchExperts({
    page: nextPage,
    pageSize: pagination.value.pageSize,
    categoryId: expertStore.categoryId
  })
  log.info('page', '[ExpertList] fetchExperts 返回后', { listLength: list.value.length, error: error.value?.message, dataLoaded: dataLoaded.value })
  if (isLoggedIn.value) {
    await expertStore.refreshMyFollowedExperts()
  }
  dataLoaded.value = true
  log.info('page', '[ExpertList] loadData 完成', { listLength: list.value.length, dataLoaded: dataLoaded.value, error: error.value?.message })
}

function handleSearch(keyword: string) {
  expertStore.keyword = keyword
  loadData(true)
}

function handleCategorySelect(categoryId: string | null) {
  activeCategory.value = String(categoryId || 'recommend')
  loadData(true)
}

function handleOpenAllCategories() {
  uni.navigateTo({ url: '/pages/home/AllCategories' })
}

async function onToggleFollow(id: string) {
  if (!id) return
  if (!ensureAuthed()) return

  const wasFollowing = !!followingMap.value[id]
  try {
    await expertStore.toggleFollow(id)
    uni.showToast({ title: wasFollowing ? '已取消关注' : '已关注', icon: wasFollowing ? 'none' : 'success' })
  } catch (e: any) {
    uni.showToast({ title: e?.message || '操作失败', icon: 'none' })
  }
}

onLoad(() => {
  void loadCategories()
  void loadData(true)
})

onPullDownRefresh(async () => {
  await loadCategories()
  await loadData(true)
  uni.stopPullDownRefresh()
})

onReachBottom(async () => {
  await loadMore()
})

async function onScrollToLower() {
  await loadMore()
}

async function loadMore() {
  if (!loadingList.value && pagination.value.hasMore) {
    await expertStore.fetchExperts({
      page: pagination.value.page + 1,
      pageSize: pagination.value.pageSize,
      categoryId: expertStore.categoryId
    })
  }
}
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.expert-page {
  min-height: 100vh;
  background: var(--color-background);
  padding: 0;
}

.page-shell {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.panel {
  background: transparent;
  border: none;
  border-radius: 0;
  box-shadow: none;
}

.main-panel {
  padding: 0;
}

.hero {
  background: var(--color-surface);
  padding: var(--spacing-base) var(--spacing-lg) var(--spacing-sm);
  display: flex;
  flex-direction: column;
  gap: 10px;
  border-bottom: 1px solid var(--color-border);
}

.hero-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  align-items: center;
}

.search-box {
  flex: 1;
  min-width: 0;
  width: 100%;
}

.tab-bar {
  width: 100%;
}

.tab-bar-scroll {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  white-space: nowrap;
}

.list-shell {
  max-height: calc(100vh - 212px);
  padding: 0;
  padding-bottom: calc(100rpx + constant(safe-area-inset-bottom));
  padding-bottom: calc(100rpx + env(safe-area-inset-bottom));
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
}

.card-stack {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.card-wrapper {
  background: transparent;
  border-radius: 0;
  border: none;
  border-bottom: 1px solid var(--color-border);
  padding: 0;
}

.card-wrapper:last-child {
  border-bottom: none;
}

.card-wrapper:hover {
  background: var(--color-surface-light);
}

.list-foot {
  text-align: center;
  padding: 12px;
  font-size: 12px;
  color: var(--color-text-secondary);
}

.muted {
  color: var(--color-text-tertiary);
}

.ui-trans {
  transition: background-color var(--duration-fast) var(--ease-in-out), border-color var(--duration-fast) var(--ease-in-out), opacity var(--duration-fast) var(--ease-in-out), transform var(--duration-fast) var(--ease-in-out);
}

@media (max-width: 767px) {
  .expert-page { padding: 0; }
  .hero { padding: var(--spacing-base) var(--spacing-lg) var(--spacing-sm); }
  .list-shell {
    max-height: none;
    padding: 0;
    padding-bottom: calc(100rpx + constant(safe-area-inset-bottom));
    padding-bottom: calc(100rpx + env(safe-area-inset-bottom));
  }
  .hero-actions { flex-direction: column; gap: 10px; }
  .search-box { width: 100%; min-width: 0; }
}
</style>

