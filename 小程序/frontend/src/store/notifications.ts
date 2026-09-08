/**
 * 通知状态管理
 * 管理通知列表、未读数量、单条标记已读
 * 说明：仅实现后端文档《后端新增api接口和模块设计文档-v2.md》§4.12 已定义端点
 */

import { defineStore } from 'pinia'
import type { NotificationListQuery } from '@/types/notifications'
import { getNotificationList, markNotificationAsRead, getUnreadNotificationCount } from '@/api/notifications'


interface NotificationItem {
  id: string
  title: string
  content: string
  notification_type: string
  related_id: string | null
  related_type: string | null
  is_read: boolean
  created_at: string
}


interface NotificationsState {
  // 通知列表
  notificationList: NotificationItem[]
  
  // 分页信息
  currentPage: number
  pageSize: number
  total: number
  hasMore: boolean
  
  // 未读数量
  unreadCount: number
  
  // 当前通知详情
  currentNotification: NotificationItem | null
  
  // 统计数据（后端文档未定义对应 API，暂不提供）
  statistics: any | null
  
  // 通知设置（后端文档未定义对应 API，暂不提供）
  settings: any | null
  
  // 加载状态
  loading: boolean
  refreshing: boolean
  loadingMore: boolean
  detailLoading: boolean
  
  // 错误状态
  error: Error | null
  
  // 筛选条件
  filters: NotificationListQuery
  
  // 批量操作选中的通知ID
  selectedIds: Set<string>
}

export const useNotificationsStore = defineStore('notifications', {
  state: (): NotificationsState => ({
    notificationList: [],
    currentPage: 1,
    pageSize: 20,
    total: 0,
    hasMore: true,
    unreadCount: 0,
    currentNotification: null,
    statistics: null,
    settings: null,
    loading: false,
    refreshing: false,
    loadingMore: false,
    detailLoading: false,
    error: null,
    filters: {},
    selectedIds: new Set()
  }),

  getters: {
    /**
     * 未读通知列表
     */
    unreadNotifications: (state) => state.notificationList.filter(item => !item.is_read),
    
    /**
     * 已读通知列表
     */
    readNotifications: (state) => state.notificationList.filter(item => item.is_read),
    
    /**
     * 按类型分组的通知
     */
    notificationsByType: (state) => {
      const groups: Record<string, NotificationItem[]> = {}
      state.notificationList.forEach(notification => {
        const type = notification.notification_type
        if (!groups[type]) {
          groups[type] = []
        }
        groups[type].push(notification)
      })
      return groups
    },
    
    /**
     * 系统通知
     */
    systemNotifications: (state) => state.notificationList.filter(item => item.notification_type === 'system'),
    
    /**
     * 订阅通知
     */
    subscriptionNotifications: (state) => state.notificationList.filter(item => item.notification_type === 'subscription'),
    
    /**
     * 互动通知
     */
    interactionNotifications: (state) => state.notificationList.filter(item => item.notification_type === 'interaction'),
    
    /**
     * 是否有未读通知
     */
    hasUnread: (state) => state.unreadCount > 0,
    
    /**
     * 选中的通知数量
     */
    selectedCount: (state) => state.selectedIds.size,
    
    /**
     * 是否为空列表
     */
    isEmpty: (state) => state.notificationList.length === 0 && !state.loading
  },

  actions: {
    /**
     * 获取通知列表
     */
    async fetchNotificationList(params?: NotificationListQuery, append: boolean = false): Promise<void> {
      if (append) {
        this.loadingMore = true
      } else {
        this.loading = true
        this.currentPage = 1
      }
      
      this.error = null
      
      try {
        const query: NotificationListQuery = {
          page: append ? this.currentPage + 1 : 1,
          pageSize: this.pageSize,
          ...this.filters,
          ...params
        }

        const response = await getNotificationList({
          page: query.page,
          size: query.pageSize,
          sort: 'created_at:desc',
          is_read: query.isRead
        })
        
        if (response.code === 200) {
          const { items, total, page, size } = response.data
          const hasMore = page * size < total
          
          if (append) {
            this.notificationList.push(...items)
            this.currentPage = page
          } else {
            this.notificationList = items
            this.currentPage = page
          }
          
          this.total = total
          this.hasMore = hasMore
          this.pageSize = size
          this.filters = query
        } else {
          throw new Error(response.message || '获取通知列表失败')
        }
      } catch (error) {
        this.error = error as Error
        throw error
      } finally {
        this.loading = false
        this.loadingMore = false
        this.refreshing = false
      }
    },

    /**
     * 刷新通知列表
     */
    async refreshNotificationList(params?: NotificationListQuery): Promise<void> {
      this.refreshing = true
      await this.fetchNotificationList(params, false)
      // 同时更新未读数量
      await this.fetchUnreadCount()
    },

    /**
     * 加载更多通知
     */
    async loadMoreNotifications(): Promise<void> {
      if (this.hasMore && !this.loadingMore) {
        await this.fetchNotificationList(this.filters, true)
      }
    },

    /**
     * 获取未读通知数量
     * 使用独立端点 GET /users/me/notifications/unread-count
     */
    async fetchUnreadCount(): Promise<void> {
      try {
        const response = await getUnreadNotificationCount()
        if (response.code === 200) {
          const unread = Number((response.data as any)?.unread_count)
          if (Number.isFinite(unread)) this.unreadCount = unread
        }
      } catch (error) {
        console.error('获取未读数量失败:', error)
      }
    },

    /**
     * 标记通知为已读
     */
    async markNotificationAsRead(notificationId: string): Promise<void> {
      try {
        const response = await markNotificationAsRead(notificationId)
        
        if (response.code === 200) {
          // 更新本地状态
          const notification = this.notificationList.find(item => item.id === notificationId)
          if (notification && !notification.is_read) {
            notification.is_read = true
            this.unreadCount = Math.max(0, this.unreadCount - 1)
          }
        } else {
          throw new Error(response.message || '标记已读失败')
        }
      } catch (error) {
        console.error('标记已读失败:', error)
        throw error
      }
    },

    /**
     * 设置筛选条件
     */
    setFilters(filters: NotificationListQuery): void {
      this.filters = { ...this.filters, ...filters }
    },

    /**
     * 清除筛选条件
     */
    clearFilters(): void {
      this.filters = {}
    },

    /**
     * 增加未读数量
     */
    incrementUnreadCount(): void {
      this.unreadCount += 1
    },

    /**
     * 减少未读数量
     */
    decrementUnreadCount(): void {
      this.unreadCount = Math.max(0, this.unreadCount - 1)
    },

    /**
     * 清除通知数据
     */
    clearNotificationsData(): void {
      this.notificationList = []
      this.currentNotification = null
      this.statistics = null
      this.currentPage = 1
      this.total = 0
      this.hasMore = true
      this.unreadCount = 0
      this.error = null
      this.selectedIds.clear()
    }
  },

  // persist: {
  //   key: 'notifications-store',
  //   paths: ['unreadCount', 'settings', 'filters']
  // }
})
