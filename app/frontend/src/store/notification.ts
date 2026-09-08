/**
 * 通知 Store
 * 管理用户的通知消息
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  getNotifications,
  markNotificationRead,
  markAllNotificationsRead
} from '@/api/notification'
import type { NotificationItem, NotificationType } from '@/types/notification'
import { handleApiError } from '@/utils/errorHandler'
import { PollingManager } from '@/utils/polling'
import { mockNotifications } from '@/mock/notification'

export const useNotificationStore = defineStore('notification', () => {
  // ========== 状态 ==========
  
  /** 通知列表 */
  const notifications = ref<NotificationItem[]>([])
  
  /** 是否正在加载 */
  const loading = ref(false)
  
  /** 是否已加载过 */
  const loaded = ref(false)
  
  /** 分页信息 */
  const pagination = ref({
    page: 1,
    size: 20,
    total: 0,
    hasMore: true
  })
  
  /** 当前选中的标签 */
  const activeTab = ref<'all' | 'system' | 'subscription' | 'interaction'>('all')
  
  /** 是否使用mock数据 */
  const useMock = ref(true) // 开发阶段使用mock数据
  
  /** 轮询管理器实例（30秒轮询） */
  const pollingManager = new PollingManager(30000)
  
  // ========== 计算属性 ==========
  
  /**
   * 系统通知列表
   */
  const systemNotifications = computed(() => {
    return notifications.value.filter(item => item.notification_type === 'system')
  })
  
  /**
   * 订阅通知列表
   */
  const subscriptionNotifications = computed(() => {
    return notifications.value.filter(item => item.notification_type === 'subscription')
  })
  
  /**
   * 互动通知列表
   */
  const interactionNotifications = computed(() => {
    return notifications.value.filter(item => item.notification_type === 'interaction')
  })
  
  /**
   * 当前标签的列表
   */
  const currentList = computed(() => {
    switch (activeTab.value) {
      case 'all':
        return notifications.value
      case 'system':
        return systemNotifications.value
      case 'subscription':
        return subscriptionNotifications.value
      case 'interaction':
        return interactionNotifications.value
      default:
        return []
    }
  })
  
  /**
   * 未读通知总数
   */
  const unreadCount = computed(() => {
    return notifications.value.filter(item => !item.is_read).length
  })
  
  /**
   * 各类型未读数量
   */
  const unreadCounts = computed(() => ({
    all: unreadCount.value,
    system: systemNotifications.value.filter(item => !item.is_read).length,
    subscription: subscriptionNotifications.value.filter(item => !item.is_read).length,
    interaction: interactionNotifications.value.filter(item => !item.is_read).length
  }))
  
  /**
   * 各标签的数量
   */
  const tabCounts = computed(() => ({
    all: notifications.value.length,
    system: systemNotifications.value.length,
    subscription: subscriptionNotifications.value.length
  }))
  
  // ========== 方法 ==========
  
  /**
   * 加载通知列表
   * @param force 是否强制刷新
   */
  async function loadNotifications(force: boolean = false) {
    // 如果已加载且不强制刷新，则跳过
    if (loaded.value && !force) {
      return
    }
    
    if (loading.value) {
      return
    }
    
    loading.value = true
    
    try {
      if (useMock.value) {
        // 使用mock数据
        await new Promise(resolve => setTimeout(resolve, 500)) // 模拟网络延迟
        const mockData = mockNotifications()
        notifications.value = mockData.items
        pagination.value.total = mockData.total
        pagination.value.hasMore = false
        loaded.value = true
      } else {
        // 使用真实API
        const params: any = {
          page: pagination.value.page,
          size: pagination.value.size
        }
        
        // 如果选中了特定类型，添加类型过滤
        if (activeTab.value !== 'all') {
          params.notification_type = activeTab.value
        }
        
        const res = await getNotifications(params)
        
        if (res.data) {
          notifications.value = res.data.items || []
          pagination.value.total = res.data.total || 0
          pagination.value.hasMore = notifications.value.length < pagination.value.total
          loaded.value = true
        }
      }
    } catch (error) {
      console.warn('加载通知失败，使用mock数据:', error)
      // API失败时回退到mock数据
      const mockData = mockNotifications()
      notifications.value = mockData.items
      pagination.value.total = mockData.total
      pagination.value.hasMore = false
      loaded.value = true
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 加载更多（上拉加载）
   */
  async function loadMore() {
    if (loading.value || !pagination.value.hasMore) {
      return
    }
    
    loading.value = true
    pagination.value.page++
    
    try {
      const params: any = {
        page: pagination.value.page,
        size: pagination.value.size
      }
      
      if (activeTab.value !== 'all') {
        params.type = activeTab.value
      }
      
      const res = await getNotifications(params)
      
      if (res.data) {
        const newItems = res.data.items || []
        notifications.value.push(...newItems)
        pagination.value.total = res.data.total || 0
        pagination.value.hasMore = notifications.value.length < pagination.value.total
      }
    } catch (error) {
      handleApiError(error)
      pagination.value.page-- // 回滚页码
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 标记单条通知为已读
   * @param notificationId 通知ID
   */
  async function markAsRead(notificationId: string) {
    try {
      await markNotificationRead(notificationId)
      
      // 更新本地状态
      const notification = notifications.value.find(item => item.id === notificationId)
      if (notification) {
        notification.is_read = true
      }
    } catch (error) {
      handleApiError(error)
    }
  }
  
  /**
   * 标记全部通知为已读
   */
  async function markAllAsRead() {
    try {
      await markAllNotificationsRead()
      
      // 更新本地状态
      notifications.value.forEach(item => {
        item.is_read = true
      })
      
      uni.showToast({
        title: '已全部标记为已读',
        icon: 'success'
      })
    } catch (error) {
      handleApiError(error)
    }
  }
  
  /**
   * 切换标签
   * @param tab 标签名称
   */
  function switchTab(tab: 'all' | 'system' | 'subscription' | 'interaction') {
    activeTab.value = tab
    // 切换标签时重新加载
    pagination.value.page = 1
    loaded.value = false
    loadNotifications(true)
  }
  
  /**
   * 切换数据源（开发用）
   * @param mock 是否使用mock数据
   */
  function toggleMock(mock: boolean) {
    useMock.value = mock
    reset()
    loadNotifications(true)
  }
  
  /**
   * 开始轮询（页面显示时调用）
   */
  function startPolling() {
    pollingManager.start(async () => {
      await loadNotifications(true)
    })
  }
  
  /**
   * 停止轮询（页面隐藏时调用）
   */
  function stopPolling() {
    pollingManager.stop()
  }
  
  /**
   * 刷新列表（下拉刷新）
   */
  async function refresh() {
    pagination.value.page = 1
    pagination.value.hasMore = true
    loaded.value = false
    await loadNotifications(true)
  }
  
  /**
   * 重置状态
   */
  function reset() {
    notifications.value = []
    loading.value = false
    loaded.value = false
    pagination.value = {
      page: 1,
      size: 20,
      total: 0,
      hasMore: true
    }
    activeTab.value = 'all'
    stopPolling()
  }
  
  return {
    // 状态
    notifications,
    loading,
    loaded,
    pagination,
    activeTab,
    
    // 计算属性
    systemNotifications,
    subscriptionNotifications,
    interactionNotifications,
    currentList,
    unreadCount,
    unreadCounts,
    tabCounts,
    
    // 方法
    loadNotifications,
    loadMore,
    markAsRead,
    markAllAsRead,
    switchTab,
    startPolling,
    stopPolling,
    refresh,
    reset
  }
})
