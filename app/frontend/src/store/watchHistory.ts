/**
 * 观看历史 Store
 * 管理用户的观看历史记录
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import dayjs from 'dayjs'
import {
  getWatchHistory,
  deleteWatchHistory
} from '@/api/watchHistory'
import type { WatchHistoryItem, GroupedHistory } from '@/types/watchHistory'
import { handleApiError } from '@/utils/errorHandler'

export const useWatchHistoryStore = defineStore('watchHistory', () => {
  // ========== 状态 ==========
  
  /** 观看历史列表 */
  const historyList = ref<WatchHistoryItem[]>([])
  
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
  
  /** 左滑删除状态（记录正在删除的项ID） */
  const deletingIds = ref<Set<string>>(new Set())
  
  // ========== 计算属性 ==========
  
  /**
   * 分组的观看历史（今天/昨天/更早）
   * 使用 computed 缓存，性能优化
   */
  const groupedHistory = computed(() => {
    return groupHistoryByDate(historyList.value)
  })
  
  /** 观看历史总数 */
  const historyCount = computed(() => historyList.value.length)
  
  // ========== 方法 ==========
  
  /**
   * 分组算法：按日期分组观看历史
   */
  function groupHistoryByDate(items: WatchHistoryItem[]): GroupedHistory[] {
    const today = dayjs().startOf('day')
    const yesterday = dayjs().subtract(1, 'day').startOf('day')
    
    const groups = {
      today: [] as WatchHistoryItem[],
      yesterday: [] as WatchHistoryItem[],
      earlier: [] as WatchHistoryItem[]
    }
    
    items.forEach(item => {
      const watchedAt = dayjs(item.watched_at)
      if (watchedAt.isSame(today, 'day')) {
        groups.today.push(item)
      } else if (watchedAt.isSame(yesterday, 'day')) {
        groups.yesterday.push(item)
      } else {
        groups.earlier.push(item)
      }
    })
    
    return [
      { date: '今天', dateLabel: '今天', items: groups.today },
      { date: '昨天', dateLabel: '昨天', items: groups.yesterday },
      { date: '更早', dateLabel: '更早', items: groups.earlier }
    ].filter(group => group.items.length > 0)
  }
  
  /**
   * 加载观看历史（方案1：Store层完成数据增强后再返回）
   * @param force 是否强制刷新
   */
  async function loadHistory(force: boolean = false) {
    // 如果已加载且不强制刷新，则跳过
    if (loaded.value && !force) {
      return
    }
    
    if (loading.value) {
      return
    }
    
    loading.value = true
    
    try {
      const res = await getWatchHistory({
        page: pagination.value.page,
        size: pagination.value.size
      })
      
      if (res.data) {
        const historyItems = res.data.items || []
        
        console.log('[WatchHistoryStore] 后端返回的观看历史数据:', historyItems.length, '项')
        
        // 卡片字段（title/cover_url/status/expert_* 等）由后端聚合返回，前端直接使用
        const normalizedList = historyItems.map(item => ({
          ...item,
          session_title: item.session_title || item.title,
          title: item.session_title || item.title,
          room_cover_url: item.room_cover_url || item.cover_url,
          cover_url: item.room_cover_url || item.cover_url
        }))
        
        // 一次性设置完整数据
        historyList.value = normalizedList as WatchHistoryItem[]
        pagination.value.total = res.data.total || 0
        pagination.value.hasMore = historyList.value.length < pagination.value.total
        loaded.value = true
        
        console.log('[WatchHistoryStore] 数据加载完成')
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
      const res = await getWatchHistory({
        page: pagination.value.page,
        size: pagination.value.size
      })
      
      if (res.data) {
        const historyItems = res.data.items || []
        
        console.log('[WatchHistoryStore] 加载更多，返回', historyItems.length, '项')
        
        // 卡片字段（title/cover_url/status/expert_* 等）由后端聚合返回，前端直接使用
        const normalizedList = historyItems.map(item => ({
          ...item,
          session_title: item.session_title || item.title,
          title: item.session_title || item.title,
          room_cover_url: item.room_cover_url || item.cover_url,
          cover_url: item.room_cover_url || item.cover_url
        }))
        
        // 一次性添加完整数据
        historyList.value.push(...normalizedList as WatchHistoryItem[])
        pagination.value.total = res.data.total || 0
        pagination.value.hasMore = historyList.value.length < pagination.value.total
        
        console.log('[WatchHistoryStore] 加载更多完成')
      }
    } catch (error) {
      handleApiError(error)
      pagination.value.page-- // 回滚页码
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 删除单条观看历史
   * @param historyId 历史记录ID
   */
  async function deleteHistory(historyId: string) {
    deletingIds.value.add(historyId)
    
    try {
      console.log('[WatchHistoryStore] 删除观看历史:', historyId)
      await deleteWatchHistory(historyId)
      
      // 从列表中移除
      const index = historyList.value.findIndex(item => item.id === historyId)
      if (index > -1) {
        historyList.value.splice(index, 1)
        pagination.value.total--
      }
      
      uni.showToast({
        title: '删除成功',
        icon: 'success'
      })
    } catch (error: any) {
      console.error('[WatchHistoryStore] 删除失败:', error)
      
      // 如果是404错误，说明记录不存在或已被删除，直接从本地列表移除
      if (error.statusCode === 404 || error.code === 404) {
        console.log('[WatchHistoryStore] 记录不存在，从本地列表移除')
        const index = historyList.value.findIndex(item => item.id === historyId)
        if (index > -1) {
          historyList.value.splice(index, 1)
          pagination.value.total--
        }
        uni.showToast({
          title: '已删除',
          icon: 'success'
        })
      } else {
        handleApiError(error)
      }
    } finally {
      deletingIds.value.delete(historyId)
    }
  }
  
  /**
   * 清空所有观看历史（后端无 clear 端点，已移除；保留注释说明）
   */

  /**
   * 刷新列表（下拉刷新）
   */
  async function refresh() {
    pagination.value.page = 1
    pagination.value.hasMore = true
    loaded.value = false
    await loadHistory(true)
  }
  
  /**
   * 重置状态
   */
  function reset() {
    historyList.value = []
    loading.value = false
    loaded.value = false
    pagination.value = {
      page: 1,
      size: 20,
      total: 0,
      hasMore: true
    }
    deletingIds.value.clear()
  }
  
  return {
    // 状态
    historyList,
    loading,
    loaded,
    pagination,
    deletingIds,
    
    // 计算属性
    groupedHistory,
    historyCount,
    
    // 方法
    loadHistory,
    loadMore,
    deleteHistory,
    refresh,
    reset
  }
})
