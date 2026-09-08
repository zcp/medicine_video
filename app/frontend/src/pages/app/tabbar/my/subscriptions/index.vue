<template>
  <view class="subscriptions-page consumer-layout">
    <!-- Tab 栏：我的订阅 | 回放 -->
    <view class="subscription-tabs">
      <view
        v-for="(tab, idx) in tabs"
        :key="tab.key"
        class="subscription-tab"
        :class="{ active: activeIndex === idx }"
        @tap="handleTabTap(idx)"
      >
        <text class="subscription-tab-label">{{ tab.label }}</text>
        <view v-if="tabCounts[tab.key]" class="subscription-tab-count">{{ tabCounts[tab.key] }}</view>
        <view class="subscription-tab-line"></view>
      </view>
    </view>

    <!-- 内容区：Tab 内容切换（点击 Tab 切换） -->
    <view
      v-for="(tab, idx) in tabs"
      :key="tab.key"
      class="subscription-panel"
      v-show="activeIndex === idx"
    >
        <!-- 空状态 -->
        <view v-if="!loading && currentListByTab(tab.key).length === 0" class="empty-state">
          <view class="empty-icon"><uni-icons type="notification" size="60" color="#c0c4cc" /></view>
          <view class="empty-text">{{ tab.key === 'pending' ? '暂无订阅记录' : '暂无回放' }}</view>
          <view class="empty-hint">{{ tab.key === 'pending' ? '订阅直播后，将在此处显示' : '订阅的直播结束后，将在此处显示回放' }}</view>
        </view>

        <!-- 订阅列表 -->
        <scroll-view
          v-else
          class="subscription-list"
          scroll-y
          :refresher-enabled="true"
          :refresher-triggered="refreshing"
          @refresherrefresh="onRefresh"
          @scrolltolower="onLoadMore"
        >
          <!-- 整页骨架屏：初次加载时显示 -->
          <view v-if="loading && currentListByTab(tab.key).length === 0" class="skeleton-group">
            <HistoryCardSkeleton v-for="i in 8" :key="i" />
          </view>

          <!-- 订阅卡片列表（统一横条卡片） -->
          <LiveCardRow
            v-for="item in currentListByTab(tab.key)"
            :key="item.id"
            :cover-url="item.cover_url || ''"
            :title="item.title || ''"
            :status="item.status || ''"
            :expert-name="item.expert_name"
            :expert-title="item.expert_title"
            :expert-hospital="item.expert_hospital"
            :expert-avatar="item.expert_avatar"
            @click="handleCardClick(item)"
            @more="handleMoreAction(item)"
          />

          <!-- 加载更多提示 -->
          <view v-if="loading && currentListByTab(tab.key).length > 0" class="loading-more">
            <text class="loading-text">加载中...</text>
          </view>

          <view v-else-if="!pagination.hasMore && currentListByTab(tab.key).length > 0" class="no-more">
            <text class="no-more-text">没有更多了</text>
          </view>
        </scroll-view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { storeToRefs } from 'pinia'
import { useSubscriptionStore } from '@/store/subscription'
import { requireAuth } from '@/utils/auth'
import { useSwiperTabs } from '@/composables/useSwiperTabs'
import type { SubscriptionWithTarget } from '@/types/subscription'
import HistoryCardSkeleton from '@/components/HistoryCardSkeleton.vue'
import LiveCardRow from '@/components/shared/LiveCardRow.vue'

// Store
const subscriptionStore = useSubscriptionStore()
const { pendingList, replayList, loading, pagination, tabCounts } = storeToRefs(subscriptionStore)

// 下拉刷新状态
const refreshing = ref(false)
// 首次显示标记（避免 onShow 和 onMounted 重复加载）
const isFirstShow = ref(true)

// Tab 配置：我的订阅（预告+直播中） | 回放（已结束/回放就绪）
const tabs = computed(() => [
  { key: 'pending', label: '我的订阅' },
  { key: 'replay', label: '回放' }
] as const)

/**
 * 获取指定 Tab 的订阅列表（各 Tab 独立取 store 的分类列表）
 * @param tabKey pending=我的订阅 / replay=回放
 */
function currentListByTab(tabKey: 'pending' | 'replay'): SubscriptionWithTarget[] {
  return tabKey === 'pending' ? pendingList.value : replayList.value
}

/**
 * Tab 索引 ↔ store 联动：切换 store 的 activeTab（过滤本地列表，不重新请求）
 */
function onTabActivated(idx: number): void {
  const tab = tabs.value[idx]
  if (!tab) return
  subscriptionStore.switchTab(tab.key)
}

/** 使用滑动 Tab（点击 ↔ swiper 双向联动） */
const { activeIndex, handleTabTap } = useSwiperTabs(
  tabs.value.length,
  onTabActivated,
  // 初始索引与 store 当前 activeTab 对齐（store 默认 pending）
  Math.max(0, tabs.value.findIndex(t => t.key === subscriptionStore.activeTab))
)

// ========== 生命周期 ==========

onMounted(() => {
  console.log('📱 订阅页面加载')

  if (!requireAuth()) {
    return
  }

  // ✅ 直接加载数据，Store层会处理所有增强
  subscriptionStore.loadSubscriptions()
})

onShow(() => {
  console.log('👀 订阅页面显示', isFirstShow.value ? '(首次)' : '(返回)')

  // 首次显示时跳过（由 onMounted 处理），只在从其他页面返回时刷新
  if (isFirstShow.value) {
    isFirstShow.value = false
    return
  }

  if (requireAuth()) {
    subscriptionStore.refresh()
  }
})

// ========== 方法 ==========

/**
 * 下拉刷新
 */
async function onRefresh() {
  refreshing.value = true
  await subscriptionStore.refresh()
  refreshing.value = false
}

/**
 * 上拉加载更多
 */
async function onLoadMore() {
  if (!loading.value && pagination.value.hasMore) {
    await subscriptionStore.loadMore()
  }
}

/**
 * 跳转到详情页
 */
function handleCardClick(item: SubscriptionWithTarget) {
  if (!item.target_id) return
  
  // 根据订阅类型跳转，直接跳转到播放页面
  if (item.target_type === 'room') {
    // 跳转到直播间播放页面
    uni.navigateTo({
      url: `/pages/app/live/LiveView?roomId=${item.target_id}`
    })
  } else if (item.target_type === 'session') {
    // 跳转到场次播放页面
    uni.navigateTo({
      url: `/pages/app/live/LiveView?sessionId=${item.target_id}`
    })
  }
}

/**
 * 更多操作菜单
 */
function handleMoreAction(item: SubscriptionWithTarget) {
  uni.showActionSheet({
    itemList: ['取消订阅', '分享'],
    success: (res) => {
      if (res.tapIndex === 0) {
        handleUnsubscribe(item)
      } else if (res.tapIndex === 1) {
        handleShare()
      }
    }
  })
}

/**
 * 取消订阅
 */
async function handleUnsubscribe(item: SubscriptionWithTarget) {
  uni.showModal({
    title: '提示',
    content: '确定要取消订阅吗？',
    success: async (res) => {
      if (res.confirm) {
        try {
          await subscriptionStore.unsubscribe(item.target_type, item.target_id)
          uni.showToast({ title: '已取消订阅', icon: 'success' })
        } catch (error) {
          console.error('取消订阅失败:', error)
          uni.showToast({ title: '操作失败', icon: 'none' })
        }
      }
    }
  })
}

/**
 * 分享
 */
function handleShare() {
  uni.showToast({ title: '分享功能开发中', icon: 'none' })
}
</script>

<style lang="scss" scoped>
// ===== 淡入动画关键帧（参考收藏页面） =====
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20rpx);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.subscriptions-page.consumer-layout {
  height: 100vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: var(--home-bg);
}

// ========== Tab 栏 ==========
.subscription-tabs {
  display: flex;
  background: var(--home-card, #fff);
  border-bottom: 1rpx solid rgba(0, 0, 0, 0.06);
  position: sticky;
  top: 0;
  z-index: 10;

  .subscription-tab {
    position: relative;
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 28rpx 0;
    gap: 8rpx;

    .subscription-tab-label {
      font-size: var(--home-fs-card-title, 28rpx);
      color: var(--home-text2);
    }

    .subscription-tab-count {
      min-width: 32rpx;
      padding: 0 8rpx;
      height: 32rpx;
      line-height: 32rpx;
      text-align: center;
      font-size: 20rpx;
      color: #fff;
      background: var(--color-danger, #fa5151);
      border-radius: 16rpx;
    }

    .subscription-tab-line {
      position: absolute;
      bottom: 0;
      left: 50%;
      transform: translateX(-50%);
      width: 48rpx;
      height: 6rpx;
      border-radius: 3rpx;
      background: transparent;
    }

    &.active {
      .subscription-tab-label {
        color: var(--home-text1);
        font-weight: 600;
      }

      .subscription-tab-line {
        background: var(--home-primary);
      }
    }
  }
}

// ========== 空状态 ==========
.empty-state {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 200rpx var(--home-spacing-page);

  .empty-icon {
    font-size: 120rpx;
    margin-bottom: 24rpx;
    opacity: 0.9;
  }

  .empty-text {
    font-size: var(--home-fs-section, 32rpx);
    color: var(--home-text1);
    margin-bottom: 12rpx;
    font-weight: 500;
  }

  .empty-hint {
    font-size: var(--home-fs-meta, 28rpx);
    color: var(--home-text2);
  }
}

// ========== 内容区 Tab 面板 ==========
.subscription-panel {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

// ========== 订阅列表（每个 swiper-item 内独立滚动） ==========
.subscription-list {
  height: 100%;
  padding: var(--home-spacing-page);
  padding-bottom: 32rpx;
  box-sizing: border-box;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}

// ========== 加载状态 ==========
.loading-more,
.no-more {
  padding: 32rpx 0;
  text-align: center;

  .loading-text,
  .no-more-text {
    font-size: var(--home-fs-meta, 24rpx);
    color: var(--home-text2);
  }
}
</style>
