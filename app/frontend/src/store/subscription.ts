/**
 * 订阅 Store
 * 管理用户的订阅记录
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { SubscriptionWithTarget } from '@/types/subscription'
import { 
  getSubscriptions, 
  addSubscription, 
  removeSubscription,
  checkSessionIsSubscribed
} from '@/api/subscription'
import { RequestLock } from '@/utils/debounce'
import { handleApiError } from '@/utils/errorHandler'

export const useSubscriptionStore = defineStore('subscription', () => {
  // ========== 状态 ==========
  
  /** 订阅列表 */
  const subscriptions = ref<SubscriptionWithTarget[]>([])
  
  /** 是否正在加载 */
  const loading = ref(false)
  
  /** 是否已加载过 */
  const loaded = ref(false)
  
  /** 请求锁（防止重复订阅/取消订阅） */
  const subscribeRequestLock = new RequestLock()
  const unsubscribeRequestLock = new RequestLock()
  
  /** 已订阅的场次ID集合（用于快速查询，不依赖列表加载） */
  const subscribedSessionIds = ref<Set<string>>(new Set())
  
  /** 分页信息 */
  const pagination = ref({
    page: 1,
    size: 20,
    total: 0,
    hasMore: true
  })
  
  /** 当前选中的标签：pending=我的订阅，replay=回放 */
  const activeTab = ref<'pending' | 'replay'>('pending')
  
  // ========== 计算属性 ==========
  
  /**
   * 我的订阅列表：房间订阅全部保留（直播间会持续开播），
   * 场次订阅仅保留未开播/直播中的（预告与开播中的仍在此列表）
   */
  const pendingList = computed(() => {
    return subscriptions.value.filter(sub => {
      if (sub.target_type !== 'session') return true
      return sub.status === 'scheduled' || sub.status === 'live' || !sub.status
    })
  })
  
  /**
   * 回放列表：场次订阅已结束/回放就绪的（finished/processing/ready/error 等）
   */
  const replayList = computed(() => {
    // V15：与后端六态对齐（ended/archived 已删除）
    const REPLAY_STATUSES = ['finished', 'processing', 'ready', 'error']
    return subscriptions.value.filter(sub => {
      if (sub.target_type !== 'session') return false
      return REPLAY_STATUSES.includes(sub.status || '')
    })
  })
  
  /**
   * 当前标签的列表
   */
  const currentList = computed(() => {
    switch (activeTab.value) {
      case 'pending':
        return pendingList.value
      case 'replay':
        return replayList.value
      default:
        return []
    }
  })
  
  /**
   * 未读徽章数量（我的订阅：预告 + 直播中）
   */
  const unreadCount = computed(() => {
    return pendingList.value.length
  })
  
  /**
   * 各标签的数量
   */
  const tabCounts = computed(() => ({
    pending: pendingList.value.length,
    replay: replayList.value.length
  }))
  
  // ========== 方法 ==========
  
  /**
   * 加载订阅列表
   * @param force 是否强制刷新
   */
  async function loadSubscriptions(force: boolean = false) {
    if (loaded.value && !force) {
      return
    }
    
    if (loading.value) {
      return
    }
    
    loading.value = true
    
    try {
      const res = await getSubscriptions({
        page: pagination.value.page,
        size: pagination.value.size
      })
      
      if (res.data) {
        const subscriptionList = res.data.items || []
        
        console.log('[SubscriptionStore] 后端返回的订阅数据:', subscriptionList.length, '项')
        
        // 卡片字段（title/cover_url/status/expert_* 等）由后端聚合返回，前端直接使用
        const normalizedList = subscriptionList.map(sub => ({
          ...sub,
          title: sub.room_title || sub.title,
          cover_url: sub.room_cover_url || sub.cover_url
        }))
        
        // 一次性设置完整数据
        subscriptions.value = normalizedList
        // 同步已订阅场次ID集合（仅session类型）
        subscribedSessionIds.value = new Set(
          subscriptionList
            .filter(sub => sub.target_type === 'session')
            .map(sub => sub.target_id)
        )
        pagination.value.total = res.data.total || 0
        pagination.value.hasMore = subscriptions.value.length < pagination.value.total
        loaded.value = true
        
        console.log('[SubscriptionStore] 数据加载完成, 已订阅场次:', subscribedSessionIds.value.size)
      }
    } catch (error) {
      handleApiError(error)
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
      const res = await getSubscriptions({
        page: pagination.value.page,
        size: pagination.value.size
      })
      
      if (res.data) {
        const subscriptionList = res.data.items || []
        
        console.log('[SubscriptionStore] 加载更多，返回', subscriptionList.length, '项')
        
        // 卡片字段（title/cover_url/status/expert_* 等）由后端聚合返回，前端直接使用
        const normalizedList = subscriptionList.map(sub => ({
          ...sub,
          title: sub.room_title || sub.title,
          cover_url: sub.room_cover_url || sub.cover_url
        }))
        
        // 一次性添加完整数据
        subscriptions.value.push(...normalizedList as SubscriptionWithTarget[])
        pagination.value.total = res.data.total || 0
        pagination.value.hasMore = subscriptions.value.length < pagination.value.total
        
        console.log('[SubscriptionStore] 加载更多完成')
      }
    } catch (error) {
      handleApiError(error)
      pagination.value.page-- // 回滚页码
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 添加订阅（带请求锁保护，防止重复订阅）
   * @param targetType 目标类型
   * @param targetId 目标ID
   */
  async function subscribe(targetType: 'room' | 'session', targetId: string) {
    // 检查是否有正在进行的订阅请求
    if (subscribeRequestLock.isLocked()) {
      console.warn('⚠️ 订阅请求进行中，请稍候...')
      uni.showToast({
        title: '请求进行中，请稍候',
        icon: 'none',
        duration: 1500
      })
      return
    }
    
    const result = await subscribeRequestLock.execute(async () => {
      try {
        await addSubscription({ target_type: targetType, target_id: targetId })
        
        // 同步到本地快速查询集合
        if (targetType === 'session') {
          subscribedSessionIds.value.add(targetId)
        }
        
        // 刷新列表
        await loadSubscriptions(true)
        
        uni.showToast({
          title: '订阅成功',
          icon: 'success'
        })
        
        return true
      } catch (error) {
        handleApiError(error)
        return false
      }
    })
    
    return result
  }
  
  /**
   * 取消订阅（带请求锁保护，防止重复取消）
   * @param targetType 订阅目标类型
   * @param targetId 订阅目标ID
   */
  async function unsubscribe(targetType: 'room' | 'session', targetId: string) {
    // 检查是否有正在进行的取消订阅请求
    if (unsubscribeRequestLock.isLocked()) {
      console.warn('⚠️ 取消订阅请求进行中，请稍候...')
      uni.showToast({
        title: '请求进行中，请稍候',
        icon: 'none',
        duration: 1500
      })
      return
    }
    
    const result = await unsubscribeRequestLock.execute(async () => {
      try {
        await removeSubscription(targetType, targetId)
        
        // 同步到本地快速查询集合
        if (targetType === 'session') {
          subscribedSessionIds.value.delete(targetId)
        }
        
        // 从列表中移除（按 target_type 和 target_id 查找）
        const index = subscriptions.value.findIndex(
          item => item.target_type === targetType && item.target_id === targetId
        )
        if (index > -1) {
          subscriptions.value.splice(index, 1)
          pagination.value.total--
        }
        
        uni.showToast({
          title: '取消订阅成功',
          icon: 'success'
        })
        
        return true
      } catch (error) {
        handleApiError(error)
        return false
      }
    })
    
    return result
  }
  
  /**
   * 检查是否已订阅（从本地列表查找）
   * @param targetId 目标ID
   */
  async function isSubscribed(targetId: string): Promise<boolean> {
    try {
      if (!loaded.value) {
        await loadSubscriptions()
      }
      
      const found = subscriptions.value.find(sub => 
        sub.target_id === targetId && sub.target_type === 'session'
      )
      
      return !!found
    } catch (error) {
      console.error('[SubscriptionStore] 检查订阅状态失败:', error)
      return false
    }
  }
  
  /**
   * 从API检查是否已订阅指定场次（单次查询，不依赖列表加载）
   * @param sessionId 场次ID
   * @returns Promise<boolean>
   * @description 调用 GET /api/v1/sessions/{session_id}/is-subscribed
   */
  async function checkSessionIsSubscribedFromApi(sessionId: string): Promise<boolean> {
    try {
      console.log('[SubscriptionStore] 检查场次订阅状态:', sessionId.substring(0, 8))
      const res = await checkSessionIsSubscribed(sessionId)
      
      if (res.code === 200 && res.data) {
        const isSubscribedStatus = res.data.is_subscribed
        
        // 同步到本地状态
        if (isSubscribedStatus) {
          subscribedSessionIds.value.add(sessionId)
        } else {
          subscribedSessionIds.value.delete(sessionId)
        }
        
        console.log('[SubscriptionStore] 场次订阅状态:', isSubscribedStatus ? '已订阅' : '未订阅')
        return isSubscribedStatus
      }
      
      return false
    } catch (error: any) {
      if (error.statusCode === 401 || error.statusCode === 403) {
        console.log('[SubscriptionStore] 未登录，默认未订阅')
        return false
      }
      
      console.error('[SubscriptionStore] 检查订阅状态失败:', error)
      return subscribedSessionIds.value.has(sessionId)
    }
  }
  
  /**
   * 检查场次是否已订阅（从本地集合快速查询）
   * @param sessionId 场次ID
   */
  function isSessionSubscribed(sessionId: string): boolean {
    return subscribedSessionIds.value.has(sessionId)
  }
  
  /**
   * 切换标签
   * @param tab 标签名称
   */
  function switchTab(tab: 'pending' | 'replay') {
    activeTab.value = tab
  }
  
  /**
   * 刷新列表（下拉刷新）
   */
  async function refresh() {
    pagination.value.page = 1
    pagination.value.hasMore = true
    loaded.value = false
    await loadSubscriptions(true)
  }
  
  /**
   * 重置状态
   */
  function reset() {
    subscriptions.value = []
    subscribedSessionIds.value.clear()
    loading.value = false
    loaded.value = false
    pagination.value = {
      page: 1,
      size: 20,
      total: 0,
      hasMore: true
    }
    activeTab.value = 'pending'
  }
  
  return {
    // 状态
    subscriptions,
    subscribedSessionIds,
    loading,
    loaded,
    pagination,
    activeTab,
    
    // 计算属性
    pendingList,
    replayList,
    currentList,
    unreadCount,
    tabCounts,
    
    // 方法
    loadSubscriptions,
    loadMore,
    subscribe,
    unsubscribe,
    isSubscribed,
    checkSessionIsSubscribedFromApi,
    isSessionSubscribed,
    switchTab,
    refresh,
    reset
  }
})
