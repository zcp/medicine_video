<template>
  <view class="notifications-page consumer-layout">
    <!-- 顶部分类导航 -->
    <view class="header-tabs">
      <view class="tab-categories">
        <view
          v-for="category in categories"
          :key="category.key"
          class="category-item"
          :class="{ active: activeCategory === category.key }"
          @click="switchCategory(category.key)"
        >
          <view class="category-icon">
            <text class="category-emoji iconfont" :class="category.icon"></text>
          </view>
          <text class="category-label">{{ category.label }}</text>
          <view v-if="category.badge > 0" class="category-badge">
            {{ category.badge > 99 ? '99+' : category.badge }}
          </view>
        </view>
      </view>
    </view>

    <!-- 空状态 -->
    <view v-if="!loading && currentList.length === 0" class="empty-state">
      <view class="empty-icon"><uni-icons type="notification" size="60" color="#c0c4cc" /></view>
      <view class="empty-text">暂无通知</view>
      <view class="empty-hint">有新通知时会显示在这里</view>
    </view>

    <!-- 通知列表 -->
    <scroll-view
      v-else
      class="notification-list"
      scroll-y
      :refresher-enabled="true"
      :refresher-triggered="refreshing"
      @refresherrefresh="onRefresh"
      @scrolltolower="onLoadMore"
    >
      <!-- 通知卡片列表 -->
      <view 
        v-for="item in currentList" 
        :key="item.id"
        class="notification-card"
        :class="{ unread: !item.is_read }"
        @tap="handleNotificationClick(item)"
      >
        <!-- 未读标记 -->
        <view v-if="!item.is_read" class="unread-dot"></view>
        
        <!-- 通知头像/图标 -->
        <view class="notification-avatar" :class="getAvatarClass(item.notification_type)">
          <uni-icons :type="getAvatarIcon(item.notification_type)" size="22" color="#ffffff" />
        </view>
        
        <!-- 通知内容 -->
        <view class="notification-content">
          <view class="content-header">
            <text class="notification-title">{{ item.title }}</text>
            <text class="notification-time">{{ formatTime(item.created_at) }}</text>
          </view>
          <text v-if="item.content" class="notification-desc">{{ item.content }}</text>
        </view>
        
        <!-- 更多操作 -->
        <view class="more-btn" @tap.stop="handleMoreAction(item)">
          <text class="iconfont icon-more"></text>
        </view>
      </view>

      <!-- 加载更多提示 -->
      <view v-if="loading" class="loading-more">
        <text class="loading-text">加载中...</text>
      </view>

      <view v-else-if="!pagination.hasMore && currentList.length > 0" class="no-more">
        <text class="no-more-text">没有更多了</text>
      </view>
    </scroll-view>

    <!-- 底部操作栏 -->
    <view v-if="unreadCount > 0" class="bottom-bar">
      <view class="bar-content">
        <view class="unread-count">{{ unreadCount }} 条未读</view>
        <view class="mark-all-btn" @click="handleMarkAllRead">
          <text class="mark-all-text">全部已读</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { onShow, onHide } from '@dcloudio/uni-app'
import { storeToRefs } from 'pinia'
import dayjs from 'dayjs'
import { useNotificationStore } from '@/store/notification'
import type { NotificationItem } from '@/types/notification'

// Store
const notificationStore = useNotificationStore()
const { currentList, loading, pagination, activeTab, unreadCount, unreadCounts } = storeToRefs(notificationStore)

// 下拉刷新状态
const refreshing = ref(false)

// 分类配置（参考B站设计）
const categories = computed(() => [
  { key: 'all', label: '回复与@', icon: 'icon-message', badge: unreadCounts.value.interaction || 0 },
  { key: 'system', label: '收到喜欢', icon: 'icon-like-filled', badge: unreadCounts.value.system || 0 },
  { key: 'subscription', label: '新增关注', icon: 'icon-my', badge: unreadCounts.value.subscription || 0 }
])

// 当前激活的分类
const activeCategory = ref('all')

// ========== 生命周期 ==========

onMounted(() => {
  loadData()
})

onShow(() => {
  // 页面显示时开始轮询
  notificationStore.startPolling()
})

onHide(() => {
  // 页面隐藏时停止轮询
  notificationStore.stopPolling()
})

// ========== 方法 ==========

/**
 * 加载数据
 */
async function loadData() {
  await notificationStore.loadNotifications()
}

/**
 * 切换分类
 */
function switchCategory(category: string) {
  activeCategory.value = category
  notificationStore.switchTab(category as 'all' | 'system' | 'subscription')
}

/**
 * 下拉刷新
 */
async function onRefresh() {
  refreshing.value = true
  await notificationStore.refresh()
  refreshing.value = false
}

/**
 * 上拉加载更多
 */
async function onLoadMore() {
  if (!loading.value && pagination.value.hasMore) {
    await notificationStore.loadMore()
  }
}

/**
 * 点击通知
 */
async function handleNotificationClick(item: NotificationItem) {
  // 标记为已读
  if (!item.is_read) {
    await notificationStore.markAsRead(item.id)
  }
  
  // 根据通知类型跳转
  if (item.related_type === 'session' && item.related_id) {
    uni.navigateTo({
      url: `/pages/app/live/LiveView?id=${item.related_id}`
    })
  } else if (item.related_type === 'room' && item.related_id) {
    uni.navigateTo({
      url: `/pages/app/live/LiveView?roomId=${item.related_id}`
    })
  }
}

/**
 * 更多操作菜单
 */
function handleMoreAction(item: NotificationItem) {
  const itemList = item.is_read ? ['删除'] : ['标记已读', '删除']
  
  uni.showActionSheet({
    itemList,
    success: (res) => {
      if (res.tapIndex === 0 && !item.is_read) {
        // 标记已读
        notificationStore.markAsRead(item.id)
      } else if ((res.tapIndex === 1 && !item.is_read) || (res.tapIndex === 0 && item.is_read)) {
        // 删除
        handleDelete(item)
      }
    }
  })
}

/**
 * 删除通知
 */
function handleDelete(item: NotificationItem) {
  uni.showModal({
    title: '提示',
    content: '确定要删除这条通知吗？',
    success: (res) => {
      if (res.confirm) {
        uni.showToast({ title: '删除成功', icon: 'success' })
        // TODO: 调用删除API
      }
    }
  })
}

/**
 * 全部已读
 */
function handleMarkAllRead() {
  uni.showModal({
    title: '提示',
    content: '确定要将所有通知标记为已读吗？',
    success: async (res) => {
      if (res.confirm) {
        await notificationStore.markAllAsRead()
      }
    }
  })
}

/**
 * 获取头像类名
 */
function getAvatarClass(type: string): string {
  const classMap: Record<string, string> = {
    system: 'avatar-system',
    subscription: 'avatar-subscription', 
    interaction: 'avatar-interaction'
  }
  return classMap[type] || 'avatar-system'
}

/**
 * 获取头像图标
 */
function getAvatarIcon(type: string): string {
  const iconMap: Record<string, string> = {
    system: 'sound',
    subscription: 'notification',
    interaction: 'chatbubble'
  }
  return iconMap[type] || 'sound'
}

/**
 * 格式化时间
 */
function formatTime(time: string): string {
  const now = dayjs()
  const target = dayjs(time)
  const diffMinutes = now.diff(target, 'minute')
  const diffHours = now.diff(target, 'hour')
  const diffDays = now.diff(target, 'day')
  
  if (diffMinutes < 1) {
    return '刚刚'
  } else if (diffMinutes < 60) {
    return `${diffMinutes}分钟前`
  } else if (diffHours < 24) {
    return `${diffHours}小时前`
  } else if (diffDays < 7) {
    return `${diffDays}天前`
  } else {
    return target.format('YYYY-MM-DD')
  }
}
</script>

<style lang="scss" scoped>
.notifications-page.consumer-layout {
  min-height: 100vh;
  background: var(--home-bg);
  padding-bottom: 120rpx;
}

// ========== 顶部分类导航：品牌主色 ==========
.header-tabs {
  position: sticky;
  top: 0;
  z-index: 10;
  background: var(--home-card);
  border-bottom: 1rpx solid rgba(0, 0, 0, 0.06);
  padding: 24rpx var(--home-spacing-page) 16rpx;
}

.tab-categories {
  display: flex;
  justify-content: space-around;
}

.category-item {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16rpx 24rpx;
  border-radius: var(--home-r-lg);
  transition: all 0.2s ease;
  
  .category-icon {
    width: 80rpx;
    height: 80rpx;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--home-bg);
    border-radius: 50%;
    margin-bottom: 12rpx;
    transition: all 0.2s ease;
    
    .category-emoji {
      font-size: 36rpx;
    }
  }
  
  .category-label {
    font-size: var(--home-fs-tab, 24rpx);
    color: var(--home-text2);
    font-weight: 400;
    transition: all 0.2s ease;
  }
  
  .category-badge {
    position: absolute;
    top: 8rpx;
    right: 16rpx;
    min-width: 32rpx;
    height: 32rpx;
    line-height: 32rpx;
    padding: 0 8rpx;
    background: var(--home-primary);
    color: #fff;
    font-size: 20rpx;
    text-align: center;
    border-radius: 16rpx;
    font-weight: 500;
  }
  
  &.active {
    background: rgba(15, 118, 110, 0.08);
    
    .category-icon {
      background: var(--home-primary);
      transform: scale(1.05);
      
      .category-emoji {
        filter: brightness(0) invert(1);
      }
    }
    
    .category-label {
      color: var(--home-primary);
      font-weight: 500;
    }
  }
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

// ========== 通知列表 ==========
.notification-list {
  height: calc(100vh - 120rpx);
  padding: var(--home-spacing-page);
  box-sizing: border-box;
}

.notification-card {
  position: relative;
  display: flex;
  align-items: flex-start;
  background: var(--home-card);
  border-radius: var(--home-r-lg);
  padding: 24rpx;
  margin-bottom: 16rpx;
  box-shadow: var(--home-shadow-card);
  
  &.unread {
    background: rgba(15, 118, 110, 0.04);
  }
  
  .unread-dot {
    position: absolute;
    top: 28rpx;
    left: 12rpx;
    width: 12rpx;
    height: 12rpx;
    background: var(--home-primary);
    border-radius: 50%;
  }
}

.notification-avatar {
  width: 88rpx;
  height: 88rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  flex-shrink: 0;
  margin-right: 24rpx;
  position: relative;

  &.avatar-system {
    background: linear-gradient(135deg, var(--home-primary) 0%, rgba(15, 118, 110, 0.85) 100%);
  }

  &.avatar-subscription {
    background: linear-gradient(135deg, rgba(15, 118, 110, 0.9) 0%, rgba(15, 118, 110, 0.7) 100%);
  }

  &.avatar-interaction {
    background: linear-gradient(135deg, rgba(15, 118, 110, 0.75) 0%, rgba(15, 118, 110, 0.55) 100%);
  }
}

.notification-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
  
  .content-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 4rpx;
    
    .notification-title {
      flex: 1;
      font-size: var(--home-fs-card-title, 30rpx);
      font-weight: 500;
      color: var(--home-text1);
      line-height: 1.4;
      margin-right: 16rpx;
    }
    
    .notification-time {
      font-size: var(--home-fs-meta, 24rpx);
      color: var(--home-text2);
      flex-shrink: 0;
      line-height: 1.4;
    }
  }
  
  .notification-desc {
    font-size: 26rpx;
    color: var(--home-text2);
    line-height: 1.5;
    overflow: hidden;
    text-overflow: ellipsis;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
  }
}

.more-btn {
  width: 48rpx;
  height: 48rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-left: 16rpx;
  
  .iconfont {
    font-size: 32rpx;
    color: var(--home-text2);
  }
}

// ========== 加载状态 ==========
.loading-more, .no-more {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32rpx 0;
  
  .loading-text, .no-more-text {
    font-size: var(--home-fs-meta, 24rpx);
    color: var(--home-text2);
  }
}

// ========== 底部操作栏：品牌主色 Pill ==========
.bottom-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: var(--home-card);
  border-top: 1rpx solid rgba(0, 0, 0, 0.06);
  padding: 24rpx var(--home-spacing-page);
  padding-bottom: calc(24rpx + env(safe-area-inset-bottom));
  z-index: 10;
}

.bar-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.unread-count {
  font-size: var(--home-fs-card-title, 28rpx);
  color: var(--home-text2);
}

.mark-all-btn {
  padding: 12rpx 32rpx;
  background: var(--home-primary);
  border-radius: var(--home-r-pill);
  
  .mark-all-text {
    font-size: var(--home-fs-card-title, 28rpx);
    color: #ffffff;
  }
}
</style>
