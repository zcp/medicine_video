<template>
  <view class="favorites-page consumer-layout">
    <!-- 骨架屏占位（首次加载时显示） -->
    <view v-if="initialLoading" class="skeleton-list">
      <view v-for="i in 6" :key="i" class="skeleton-card">
        <view class="skeleton-cover"></view>
        <view class="skeleton-info">
          <view class="skeleton-title"></view>
          <view class="skeleton-line"></view>
          <view class="skeleton-author">
            <view class="skeleton-avatar"></view>
            <view class="skeleton-text"></view>
          </view>
        </view>
      </view>
    </view>

    <!-- 列表区域（数据加载后显示） -->
    <scroll-view 
      v-else
      class="favorites-list" 
      scroll-y
      @scrolltolower="loadMore"
      :refresher-enabled="true"
      :refresher-triggered="refreshing"
      @refresherrefresh="onRefresh"
    >
      <!-- 收藏卡片列表（统一横条卡片） -->
      <LiveCardRow
        v-for="item in displayList"
        :key="item.id"
        :cover-url="item.room_cover_url || ''"
        :title="item.room_title || ''"
        :status="item.room_live_status || ''"
        :expert-name="item.expert_name"
        :expert-title="item.expert_title"
        :expert-hospital="item.expert_hospital"
        :expert-avatar="item.expert_avatar"
        @click="handleCardClick(item)"
        @more="handleMoreAction(item)"
      />
      
      <!-- 加载状态 -->
      <view v-if="loading" class="loading-more">
        <text>加载中...</text>
      </view>
      
      <!-- 没有更多 -->
      <view v-if="!hasMore && displayList.length > 0" class="no-more">
        <text>没有更多了</text>
      </view>
      
      <!-- 空状态 -->
      <view v-if="!loading && displayList.length === 0" class="empty-state">
        <text class="iconfont icon-shoucang1 empty-icon"></text>
        <text class="empty-title">暂无收藏</text>
        <text class="empty-desc">快去收藏你喜欢的直播吧</text>
      </view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import { requireAuth } from '@/utils/auth';
import { useFavoriteStore } from '@/store/favorite';
import type { FavoriteWithRoom } from '@/types/favorite';
import LiveCardRow from '@/components/shared/LiveCardRow.vue';

// Store
const favoriteStore = useFavoriteStore();

// 响应式数据
const loading = ref(false);
// 首次加载标记（用于显示骨架屏）- 基于Store的loading和loaded状态
const initialLoading = computed(() => favoriteStore.loading && !favoriteStore.loaded);
const refreshing = ref(false);
// 首次显示标记（避免 onShow 和 onMounted 重复加载）
const isFirstShow = ref(true);
const hasMore = ref(true);
const currentPage = ref(1);
const pageSize = 10;

// 从Store获取完整列表，然后分页显示
const displayList = computed(() => {
  const allItems = favoriteStore.favoriteList;
  const endIndex = currentPage.value * pageSize;
  return allItems.slice(0, endIndex);
});

// 生命周期
onMounted(() => {
  console.log('📱 收藏页面加载');
  
  if (!requireAuth()) {
    return;
  }
  
  loadFavorites();
});

onShow(() => {
  console.log('👀 收藏页面显示', isFirstShow.value ? '(首次)' : '(返回)');
  
  // 首次显示时跳过（由 onMounted 处理），只在从其他页面返回时刷新
  if (isFirstShow.value) {
    isFirstShow.value = false;
    return;
  }
  
  if (requireAuth()) {
    refreshData();
  }
});

// 数据加载
async function loadFavorites() {
  if (loading.value) return;
  
  loading.value = true;
  
  try {
    await favoriteStore.loadFavorites(false);
    
    // 判断是否还有更多
    const allItems = favoriteStore.favoriteList;
    hasMore.value = displayList.value.length < allItems.length;
    
    console.log('✅ 收藏列表加载成功:', allItems.length, '条');
  } catch (error) {
    console.error('❌ 加载收藏列表失败:', error);
    uni.showToast({ title: '加载失败', icon: 'none' });
  } finally {
    loading.value = false;
    refreshing.value = false;
  }
}

async function refreshData() {
  currentPage.value = 1;
  hasMore.value = true;
  await favoriteStore.loadFavorites(true);
}

function onRefresh() {
  refreshing.value = true;
  refreshData();
}

function loadMore() {
  if (!hasMore.value || loading.value) return;
  
  const allItems = favoriteStore.favoriteList;
  const nextEndIndex = (currentPage.value + 1) * pageSize;
  
  if (nextEndIndex < allItems.length) {
    currentPage.value++;
    hasMore.value = nextEndIndex < allItems.length;
  } else {
    hasMore.value = false;
  }
}

// 事件处理
function handleCardClick(item: FavoriteWithRoom) {
  if (!item.room_id) return;
  
  uni.navigateTo({
    url: `/pages/app/live/LiveView?roomId=${item.room_id}`
  });
}

// 更多操作菜单
function handleMoreAction(item: FavoriteWithRoom) {
  uni.showActionSheet({
    itemList: ['取消收藏', '分享'],
    success: (res) => {
      if (res.tapIndex === 0) {
        handleUnfavorite(item);
      } else if (res.tapIndex === 1) {
        handleShare();
      }
    }
  });
}

async function handleUnfavorite(item: FavoriteWithRoom) {
  uni.showModal({
    title: '提示',
    content: '确定要取消收藏吗？',
    success: async (res) => {
      if (res.confirm) {
        try {
          await favoriteStore.removeFavorite(item.room_id);
          uni.showToast({ title: '已取消收藏', icon: 'success' });
        } catch (error) {
          console.error('取消收藏失败:', error);
          uni.showToast({ title: '操作失败', icon: 'none' });
        }
      }
    }
  });
}

function handleShare() {
  uni.showToast({ title: '分享功能开发中', icon: 'none' });
}
</script>

<style lang="scss" scoped>
// ===== 动画关键帧 =====
@keyframes fadeSlideIn {
  from { opacity: 0; transform: translateY(16rpx); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes shimmer {
  0%   { background-position: 100% 50%; }
  100% { background-position: 0 50%; }
}

// ===== 页面根 =====
.favorites-page.consumer-layout {
  min-height: 100vh;
  background: var(--home-bg);
}

// ========== 骨架屏 ==========
.skeleton-list {
  padding: var(--home-spacing-page);
}

.skeleton-card {
  display: flex;
  background: var(--home-card);
  border-radius: var(--home-r-lg);
  margin-bottom: var(--home-spacing-module);
  padding: calc(var(--home-spacing-card) * 1.25);
  overflow: hidden;
  box-shadow: var(--home-shadow-card);
}

// 骨架波纹（统一中性色，消除灰色突兀感）
%shimmer-block {
  background: linear-gradient(
    90deg,
    rgba(17,24,39,0.06) 25%,
    rgba(17,24,39,0.03) 50%,
    rgba(17,24,39,0.06) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

.skeleton-cover {
  @extend %shimmer-block;
  width: 240rpx;
  height: 150rpx;
  border-radius: var(--home-r-md);
  flex-shrink: 0;
}

.skeleton-info {
  flex: 1;
  margin-left: var(--home-spacing-inner);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.skeleton-title {
  @extend %shimmer-block;
  width: 100%;
  height: 36rpx;
  border-radius: var(--home-r-md);
  margin-bottom: var(--home-spacing-inner);
}

.skeleton-line {
  @extend %shimmer-block;
  width: 70%;
  height: 28rpx;
  border-radius: var(--home-r-md);
  margin-bottom: var(--home-spacing-inner);
}

.skeleton-author {
  display: flex;
  align-items: center;
}

.skeleton-avatar {
  @extend %shimmer-block;
  width: 44rpx;
  height: 44rpx;
  border-radius: 50%;
  margin-right: var(--home-spacing-inner);
}

.skeleton-text {
  @extend %shimmer-block;
  flex: 1;
  height: 24rpx;
  border-radius: var(--home-r-md);
}

// ========== 列表容器 ==========
.favorites-list {
  height: 100vh;
  padding: var(--home-spacing-page);
  box-sizing: border-box;
}

// ========== 加载/底部 ==========
.loading-more,
.no-more {
  text-align: center;
  padding: 32rpx 0;
  font-size: var(--home-fs-meta);
  color: var(--home-text2);
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
    color: var(--home-tabbar-inactive);
    margin-bottom: 32rpx;
  }

  .empty-title {
    font-size: var(--home-fs-section);
    color: var(--home-text1);
    margin-bottom: 16rpx;
    font-weight: 500;
  }

  .empty-desc {
    font-size: var(--home-fs-card-title);
    color: var(--home-text2);
  }
}
</style>
