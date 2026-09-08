<template>
  <view class="notifications-page consumer-layout">
    <!-- 顶部操作栏 -->
    <view class="header-bar">
      <!-- Tab 切换 -->
      <view class="tabs">
        <view
          v-for="(tab, idx) in tabs"
          :key="tab.key"
          class="tab-item"
          :class="{ active: activeIndex === idx }"
          @tap="handleTabTap(idx)"
        >
          <text class="tab-text">{{ tab.label }}</text>
          <!-- 未读徽章 -->
          <view v-if="tab.badge > 0" class="tab-badge">
            {{ tab.badge > 99 ? '99+' : tab.badge }}
          </view>
        </view>
      </view>

      <!-- 全部已读按钮 -->
      <view v-if="unreadCount > 0" class="mark-all-btn" @click="handleMarkAllRead">
        <text class="btn-text">全部已读</text>
      </view>
    </view>

    <!-- 内容区：Tab 内容切换（点击 Tab 切换） -->
    <view
      v-for="(tab, idx) in tabs"
      :key="tab.key"
      class="notification-panel"
      v-show="activeIndex === idx"
    >
        <!-- 空状态 -->
        <view v-if="!loading && currentListByTab(tab.key).length === 0" class="empty-state">
          <view class="empty-icon"><uni-icons type="notification" size="60" color="#c0c4cc" /></view>
          <view class="empty-text">{{ getEmptyTextByTab(tab.key) }}</view>
          <view class="empty-hint">暂无新通知</view>
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
          <!-- 通知项 -->
          <view
            v-for="item in currentListByTab(tab.key)"
            :key="item.id"
            class="notification-item"
            :class="{ unread: !item.is_read }"
            @click="handleNotificationClick(item)"
          >
            <!-- 未读标记 -->
            <view v-if="!item.is_read" class="unread-dot"></view>

            <!-- 通知图标 -->
            <view class="notification-icon" :class="`icon-${item.type}`">
              <text class="icon-text iconfont" :class="getNotificationIcon(item.type)"></text>
            </view>

            <!-- 通知内容 -->
            <view class="notification-content">
              <!-- 标题 -->
              <view class="notification-title">{{ item.title }}</view>

              <!-- 内容 -->
              <view class="notification-text">{{ item.content }}</view>

              <!-- 时间 -->
              <view class="notification-time">{{ formatTime(item.created_at) }}</view>
            </view>

            <!-- 操作按钮 -->
            <view class="notification-actions">
              <view v-if="!item.is_read" class="action-btn" @click.stop="handleMarkRead(item.id)">
                <text class="action-text">标为已读</text>
              </view>
            </view>
          </view>

          <!-- 加载更多提示 -->
          <view v-if="loading" class="loading-more">
            <text class="loading-text">加载中...</text>
          </view>

          <view v-else-if="!pagination.hasMore && currentListByTab(tab.key).length > 0" class="no-more">
            <text class="no-more-text">没有更多了</text>
          </view>
        </scroll-view>
    </view>

    <!-- 通知详情弹层 -->
    <view v-if="detailVisible" class="detail-mask" @click="closeDetail">
      <view class="detail-panel" @click.stop>
        <view class="detail-head">
          <text class="detail-title">{{ detailItem?.title || '通知详情' }}</text>
          <text class="detail-close" @click="closeDetail">✕</text>
        </view>
        <view v-if="detailLoading" class="detail-loading">
          <text class="detail-loading-text">加载中...</text>
        </view>
        <template v-else>
          <view class="detail-body">
            <view class="detail-meta">
              <text class="detail-type">{{ getNotificationTypeLabel(detailItem?.type) }}</text>
              <text class="detail-time">{{ detailItem ? formatTime(detailItem.created_at) : '' }}</text>
            </view>
            <text class="detail-content">{{ detailItem?.content || '暂无内容' }}</text>
          </view>
          <view v-if="detailItem?.extra?.session_id || detailItem?.extra?.room_id" class="detail-footer">
            <view class="detail-action" @click="goDetailTarget(detailItem!)">
              <text>去观看</text>
            </view>
          </view>
        </template>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { storeToRefs } from 'pinia'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'
import { useNotificationStore } from '@/store/notification'
import { getNotificationDetail } from '@/api/notification'
import { navigateTo } from '@/utils/router'
import { useSwiperTabs } from '@/composables/useSwiperTabs'
import type { NotificationItem } from '@/types/notification'

// 配置 dayjs
dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

// Store
const notificationStore = useNotificationStore()
const { notifications, systemNotifications, subscriptionNotifications, loading, pagination, unreadCounts } = storeToRefs(notificationStore)

// 下拉刷新状态
const refreshing = ref(false)

// Tab 配置
const tabs = computed(() => [
  { key: 'all', label: '全部', badge: unreadCounts.value.all },
  { key: 'system', label: '系统', badge: unreadCounts.value.system },
  { key: 'subscription', label: '直播', badge: unreadCounts.value.subscription }
] as const)

// 未读总数
const unreadCount = computed(() => unreadCounts.value.all)

/**
 * 获取指定 Tab 的通知列表（各 Tab 独立取 store 的分类列表）
 * @param tabKey all / system / subscription
 */
function currentListByTab(tabKey: 'all' | 'system' | 'subscription'): NotificationItem[] {
  if (tabKey === 'system') return systemNotifications.value
  if (tabKey === 'subscription') return subscriptionNotifications.value
  // all：直接读 store 的完整列表，避免依赖 store 当前 activeTab（防止与 swiper 索引短暂失步时显示错误）
  return notifications.value
}

/**
 * 获取指定 Tab 的空状态文案
 * @param tabKey all / system / subscription
 */
function getEmptyTextByTab(tabKey: 'all' | 'system' | 'subscription'): string {
  const textMap: Record<string, string> = {
    all: '暂无通知',
    system: '暂无系统通知',
    subscription: '暂无直播通知'
  }
  return textMap[tabKey] || '暂无通知'
}

/**
 * Tab 索引 ↔ store 联动：切换 store 的 activeTab（会重置分页并重新加载）
 */
function onTabActivated(idx: number): void {
  const tab = tabs.value[idx]
  if (!tab) return
  notificationStore.switchTab(tab.key as 'all' | 'system' | 'subscription')
}

/** 使用滑动 Tab（点击 ↔ swiper 双向联动） */
const { activeIndex, handleTabTap } = useSwiperTabs(
  tabs.value.length,
  onTabActivated,
  // 初始索引与 store 当前 activeTab 对齐
  Math.max(0, tabs.value.findIndex(t => t.key === notificationStore.activeTab))
)

// ========== 生命周期 ==========

onMounted(() => {
  loadData()
  // 启动轮询
  notificationStore.startPolling()
})

onUnmounted(() => {
  // 停止轮询
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
 * 点击通知：标已读 + 打开详情弹层（详情取后端最新，404 回退列表项）
 */
async function handleNotificationClick(item: NotificationItem) {
  // 如果未读，先标记为已读
  if (!item.is_read) {
    await notificationStore.markAsRead(item.id)
  }

  detailItem.value = item
  detailVisible.value = true
  detailLoading.value = true
  try {
    const res = await getNotificationDetail(item.id)
    if (res.code === 200 && res.data) {
      detailItem.value = res.data
    }
  } catch (e) {
    // 详情 404 等异常时回退列表项数据展示
    console.warn('[通知详情] 获取失败，使用列表数据:', e)
  } finally {
    detailLoading.value = false
  }
}

// ===== 通知详情弹层 =====
const detailVisible = ref(false)
const detailLoading = ref(false)
const detailItem = ref<NotificationItem | null>(null)

function closeDetail() {
  detailVisible.value = false
  detailItem.value = null
}

function goDetailTarget(item: NotificationItem) {
  closeDetail()
  if (item.extra?.session_id) {
    navigateTo('/live/LiveView', { sessionId: item.extra.session_id })
  } else if (item.extra?.room_id) {
    navigateTo('/live/LiveView', { roomId: item.extra.room_id })
  }
}

function getNotificationTypeLabel(type?: string): string {
  const map: Record<string, string> = {
    system: '系统通知',
    subscription: '订阅通知',
    interaction: '互动通知',
    live_start: '开播提醒',
    live_end: '直播结束',
    follow: '关注通知',
  }
  return map[type || ''] || '通知'
}

/**
 * 标记单条已读
 */
async function handleMarkRead(notificationId: string) {
  await notificationStore.markAsRead(notificationId)
}

/**
 * 标记全部已读
 */
function handleMarkAllRead() {
  uni.showModal({
    title: '确认操作',
    content: '确定要将所有通知标记为已读吗？',
    success: async (res) => {
      if (res.confirm) {
        await notificationStore.markAllAsRead()
      }
    }
  })
}

/**
 * 获取通知图标
 */
function getNotificationIcon(type?: string): string {
  const iconMap: Record<string, string> = {
    system: 'icon-setting',
    subscription: 'icon-video',
    interaction: 'icon-message'
  }
  return (type && iconMap[type]) || 'icon-video'
}

/**
 * 格式化时间
 */
function formatTime(createdAt: string): string {
  const time = dayjs(createdAt)
  const now = dayjs()
  const diffMinutes = now.diff(time, 'minute')

  if (diffMinutes < 1) {
    return '刚刚'
  } else if (diffMinutes < 60) {
    return `${diffMinutes}分钟前`
  } else if (time.isSame(now, 'day')) {
    return time.format('HH:mm')
  } else if (time.isSame(now.subtract(1, 'day'), 'day')) {
    return `昨天 ${time.format('HH:mm')}`
  } else if (time.isSame(now, 'year')) {
    return time.format('MM-DD HH:mm')
  } else {
    return time.format('YYYY-MM-DD')
  }
}
</script>

<style lang="scss" scoped>
.notifications-page.consumer-layout {
  height: 100vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: var(--home-bg);
}

// ========== 顶部操作栏 ==========
.header-bar {
  position: sticky;
  top: 0;
  z-index: 10;
  background: var(--home-card);
  // 若隐若现分割线（对比度 ~4%）
  border-bottom: 1rpx solid rgba(17, 24, 39, 0.06);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-right: var(--home-spacing-page);
}

.tabs {
  flex: 1;
  display: flex;
  padding: 0 var(--home-spacing-page);

  .tab-item {
    position: relative;
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 24rpx 0;
    min-height: 88rpx; // 热区 ≥ 44px

    .tab-text {
      font-size: var(--home-fs-card-title);
      color: var(--home-text2);
      transition: color 0.2s ease, font-size 0.2s ease;
    }

    // 未读标记（品牌红）
    .tab-badge {
      position: absolute;
      top: 14rpx;
      right: 20%;
      min-width: 32rpx;
      height: 32rpx;
      padding: 0 8rpx;
      background: var(--color-danger);
      border-radius: var(--home-r-pill);
      color: #fff;
      font-size: 20rpx;
      display: flex;
      align-items: center;
      justify-content: center;
      transform: scale(0.9);
    }

    // 激活态：品牌主色，清除遗留蓝色
    &.active {
      .tab-text {
        color: var(--home-primary);
        font-weight: 600;
        font-size: 30rpx;
      }

      &::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 40rpx;
        height: 4rpx;
        background: var(--home-primary);
        border-radius: 2rpx;
      }
    }
  }
}

// 全部已读按钮：Gaoshoutem Pill 风格，品牌主色
.mark-all-btn {
  padding: 10rpx 28rpx;
  background: var(--home-primary);
  border-radius: var(--home-r-pill);
  min-height: 64rpx;
  display: flex;
  align-items: center;

  &:active {
    opacity: 0.8;
    transition: opacity 0.15s ease;
  }

  .btn-text {
    font-size: var(--home-fs-tab);
    color: #fff;
    font-weight: 500;
  }
}

// ========== 内容区 Tab 面板 ==========
.notification-panel {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

// ========== 空状态 ==========
.empty-state {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 200rpx 0;

  .empty-icon {
    font-size: 120rpx;
    margin-bottom: 24rpx;
    opacity: 0.65;
  }

  .empty-text {
    font-size: var(--home-fs-section);
    color: var(--home-text1);
    margin-bottom: 12rpx;
    font-weight: 500;
  }

  .empty-hint {
    font-size: var(--home-fs-card-title);
    color: var(--home-text2);
  }
}

// ========== 通知列表（每个 swiper-item 内独立滚动） ==========
.notification-list {
  height: 100%;
  padding: var(--home-spacing-page);
  box-sizing: border-box;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}

.notification-item {
  position: relative;
  display: flex;
  align-items: flex-start;
  padding: 24rpx;
  background: var(--home-card);
  border-radius: var(--home-r-lg);
  margin-bottom: var(--home-spacing-inner);
  box-shadow: var(--home-shadow-card);

  // 未读：品牌色极轻底色点缀
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

  .notification-icon {
    width: 80rpx;
    height: 80rpx;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    margin-right: 24rpx;

    .icon-text {
      font-size: 40rpx;
    }

    // 图标背景统一用品牌色淡色，消除遗留色块
    &.icon-system {
      background: rgba(15, 118, 110, 0.10);
    }

    &.icon-subscription {
      background: rgba(15, 118, 110, 0.07);
    }

    &.icon-interaction {
      background: rgba(15, 118, 110, 0.05);
    }
  }

  .notification-content {
    flex: 1;
    min-width: 0;

    .notification-title {
      font-size: var(--home-fs-card-title);
      color: var(--home-text1);
      font-weight: 500;
      margin-bottom: 8rpx;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .notification-text {
      font-size: var(--home-fs-meta);
      color: var(--home-text2);
      line-height: 1.55;
      margin-bottom: 8rpx;
      overflow: hidden;
      text-overflow: ellipsis;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      line-clamp: 2;
      -webkit-box-orient: vertical;
    }

    .notification-time {
      font-size: 20rpx;
      color: var(--home-tabbar-inactive);
    }
  }

  .notification-actions {
    display: flex;
    align-items: center;
    margin-left: var(--home-spacing-inner);
    flex-shrink: 0;

    // 标为已读按钮：轻边框 + Pill，热区 ≥ 44px
    .action-btn {
      padding: 10rpx 20rpx;
      background: transparent;
      border: 1.5rpx solid var(--home-border);
      border-radius: var(--home-r-pill);
      min-height: 60rpx;
      display: flex;
      align-items: center;

      &:active {
        background: var(--home-bg);
        transition: background 0.1s;
      }

      .action-text {
        font-size: var(--home-fs-meta);
        color: var(--home-text2);
      }
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
    font-size: var(--home-fs-meta);
    color: var(--home-text2);
  }
}

// ========== 通知详情弹层 ==========
.detail-mask {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0, 0, 0, 0.45);
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48rpx;
}
.detail-panel {
  width: 100%;
  max-height: 70vh;
  background: #fff;
  border-radius: 20rpx;
  padding: 32rpx;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
}
.detail-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24rpx;
}
.detail-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #1a1a1a;
  flex: 1;
  margin-right: 24rpx;
}
.detail-close {
  font-size: 32rpx;
  color: #999;
  padding: 8rpx;
}
.detail-loading {
  padding: 60rpx 0;
  text-align: center;
}
.detail-loading-text {
  font-size: 26rpx;
  color: #999;
}
.detail-body {
  overflow-y: auto;
}
.detail-meta {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-bottom: 16rpx;
}
.detail-type {
  font-size: 22rpx;
  color: var(--home-primary);
  background: rgba(15, 118, 110, 0.08);
  padding: 4rpx 14rpx;
  border-radius: 20rpx;
}
.detail-time {
  font-size: 22rpx;
  color: #999;
}
.detail-content {
  font-size: 28rpx;
  color: #333;
  line-height: 1.6;
  word-break: break-all;
}
.detail-footer {
  margin-top: 32rpx;
  display: flex;
  justify-content: flex-end;
}
.detail-action {
  background: var(--home-primary);
  color: #fff;
  font-size: 26rpx;
  padding: 14rpx 40rpx;
  border-radius: 10rpx;
}
</style>
