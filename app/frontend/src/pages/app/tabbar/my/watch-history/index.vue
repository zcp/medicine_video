<template>
  <view class="watch-history-page consumer-layout">
    <!-- 空状态 -->
    <view v-if="!loading && historyCount === 0" class="empty-state">
      <view class="empty-icon"><text class="iconfont icon-video"></text></view>
      <view class="empty-text">暂无观看历史</view>
      <view class="empty-hint">观看过的直播会显示在这里</view>
    </view>

    <!-- 历史记录列表 -->
    <scroll-view
      v-else
      class="history-list"
      scroll-y
      :refresher-enabled="true"
      :refresher-triggered="refreshing"
      @refresherrefresh="onRefresh"
      @scrolltolower="onLoadMore"
    >
      <!-- 整页骨架屏：初次加载时显示 -->
      <view v-if="loading && historyCount === 0" class="history-group">
        <HistoryCardSkeleton v-for="i in 8" :key="i" />
      </view>

      <!-- 观看历史列表（B站风格） -->
      <view 
        v-for="group in groupedHistory" 
        :key="group.date"
        class="history-group"
      >
        <!-- 日期分组标题 -->
        <view class="group-header">
          <text class="group-date">{{ group.dateLabel }}</text>
        </view>
        
        <!-- 该日期的观看记录 -->
        <LiveCardRow
          v-for="item in group.items"
          :key="item.id"
          :cover-url="item.room_cover_url || item.cover_url || ''"
          :title="item.session_title || item.title || ''"
          :status="item.status || ''"
          :expert-name="item.expert_name"
          :expert-title="item.expert_title"
          :expert-hospital="item.expert_hospital"
          :expert-avatar="item.expert_avatar"
          @click="handleItemClick(item)"
          @more="handleMoreAction(item)"
        />
      </view>

      <!-- 加载更多提示 -->
      <view v-if="loading && historyCount > 0" class="loading-more">
        <text class="loading-text">加载中...</text>
      </view>

      <view v-else-if="!pagination.hasMore && historyCount > 0" class="no-more">
        <text class="no-more-text">没有更多了</text>
      </view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { storeToRefs } from 'pinia'
import { useWatchHistoryStore } from '@/store/watchHistory'
import { requireAuth } from '@/utils/auth'
import type { WatchHistoryItem } from '@/types/watchHistory'
import HistoryCardSkeleton from '@/components/HistoryCardSkeleton.vue'
import LiveCardRow from '@/components/shared/LiveCardRow.vue'

// Store
const watchHistoryStore = useWatchHistoryStore()
const { groupedHistory, loading, pagination, historyCount } = storeToRefs(watchHistoryStore)

// 下拉刷新状态
const refreshing = ref(false)
// 首次显示标记（避免 onShow 和 onMounted 重复加载）
const isFirstShow = ref(true)

// ========== 生命周期 ==========

onMounted(() => {
  console.log('📱 观看历史页面加载')
  
  if (!requireAuth()) {
    return
  }
  
  // ✅ 直接加载数据，Store层会处理所有增强
  watchHistoryStore.loadHistory()
})

onShow(() => {
  console.log('👀 观看历史页面显示', isFirstShow.value ? '(首次)' : '(返回)')
  
  // 首次显示时跳过（由 onMounted 处理），只在从其他页面返回时刷新
  if (isFirstShow.value) {
    isFirstShow.value = false
    return
  }
  
  if (requireAuth()) {
    watchHistoryStore.refresh()
  }
})

// ========== 方法 ==========

/**
 * 下拉刷新
 */
async function onRefresh() {
  refreshing.value = true
  await watchHistoryStore.refresh()
  refreshing.value = false
}

/**
 * 上拉加载更多
 */
async function onLoadMore() {
  if (!loading.value && pagination.value.hasMore) {
    await watchHistoryStore.loadMore()
  }
}

/**
 * 点击历史记录卡片
 * @description 跳转播放页并携带 progress 参数实现断点续播（仅功能保留，卡片不显示进度角标）
 */
function handleItemClick(item: WatchHistoryItem) {
  if (!item.session_id) return

  // 直接跳转到播放页面，传递progress参数实现断点续播
  const progressParam = item.progress ? `&progress=${item.progress}` : ''
  uni.navigateTo({
    url: `/pages/app/live/LiveView?sessionId=${item.session_id}${progressParam}`
  })
}

/**
 * 更多操作菜单
 */
function handleMoreAction(item: WatchHistoryItem) {
  uni.showActionSheet({
    itemList: ['删除记录'],
    success: (res) => {
      if (res.tapIndex === 0) {
        handleDelete(item)
      }
    }
  })
}

/**
 * 删除单条历史
 */
async function handleDelete(item: WatchHistoryItem) {
  uni.showModal({
    title: '提示',
    content: '确定要删除这条观看记录吗？',
    success: async (res) => {
      if (res.confirm) {
        try {
          await watchHistoryStore.deleteHistory(item.id)
          uni.showToast({ title: '已删除', icon: 'success' })
        } catch (error) {
          console.error('[观看历史] 删除失败:', error)
          uni.showToast({ title: '操作失败', icon: 'none' })
        }
      }
    }
  })
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

.watch-history-page.consumer-layout {
  min-height: 100vh;
  background: var(--home-bg);
}

// ========== 空状态 ==========
.empty-state {
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

// ========== 历史记录列表 ==========
.history-list {
  height: 100vh;
  padding: var(--home-spacing-page);
  box-sizing: border-box;
}

.history-group {
  margin-bottom: var(--home-spacing-module);

  .group-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12rpx 0;

    .group-date {
      font-size: var(--home-fs-card-title, 28rpx);
      font-weight: 500;
      color: var(--home-text2);
    }
  }
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
