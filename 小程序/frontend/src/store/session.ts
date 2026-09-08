/**
 * 场次状态管理
 * 管理直播场次信息、场次状态、观看记录等
 */

import { defineStore } from 'pinia'
import type { 
  Session,
  SessionDetail,
  SessionListQuery,
  CreateSessionRequest,
  UpdateSessionRequest,
  SessionStatistics
} from '@/types/session'
import type { PaginatedResponse } from '@/types/common'
import { 
  getSessionList,
  getSessionDetail,
  createSession,
  updateSession,
  deleteSession,
  getSessionStatistics
} from '@/api/session'

interface SessionState {
  // 场次列表
  sessionList: Session[]
  
  // 分页信息
  currentPage: number
  pageSize: number
  total: number
  hasMore: boolean
  
  // 当前场次详情
  currentSession: SessionDetail | null
  
  // 场次统计
  statistics: SessionStatistics | null
  
  // 加载状态
  loading: boolean
  refreshing: boolean
  loadingMore: boolean
  detailLoading: boolean
  
  // 错误状态
  error: Error | null
  
  // 筛选条件
  filters: SessionListQuery
  
  // 观看状态
  isWatching: boolean
  watchStartTime: number | null
  
  // 缓存
  sessionCache: Map<string, SessionDetail>
}

export const useSessionStore = defineStore('session', {
  state: (): SessionState => ({
    sessionList: [],
    currentPage: 1,
    pageSize: 20,
    total: 0,
    hasMore: true,
    currentSession: null,
    statistics: null,
    loading: false,
    refreshing: false,
    loadingMore: false,
    detailLoading: false,
    error: null,
    filters: {},
    isWatching: false,
    watchStartTime: null,
    sessionCache: new Map()
  }),

  getters: {
    /**
     * 进行中的场次
     */
    liveSessions: (state) => state.sessionList.filter(session => session.status === 'live'),
    
    /**
     * 即将开始的场次
     */
    upcomingSessions: (state) => state.sessionList.filter(session => session.status === 'scheduled'),
    
    /**
     * 已结束的场次
     */
    endedSessions: (state) => state.sessionList.filter(session => session.status === 'ended'),
    
    /**
     * 今日场次
     */
    todaySessions: (state) => {
      const today = new Date().toDateString()
      return state.sessionList.filter(session => 
        new Date(session.startTime).toDateString() === today
      )
    },
    
    /**
     * 观看时长（秒）
     */
    watchDuration: (state) => {
      if (!state.watchStartTime) return 0
      return Math.floor((Date.now() - state.watchStartTime) / 1000)
    },
    
    /**
     * 当前场次是否为直播状态
     */
    isCurrentSessionLive: (state) => state.currentSession?.status === 'live'
  },

  actions: {
    /**
     * 获取场次列表
     */
    async fetchSessionList(params?: SessionListQuery, append: boolean = false): Promise<void> {
      if (append) {
        this.loadingMore = true
      } else {
        this.loading = true
        this.currentPage = 1
      }
      
      this.error = null
      
      try {
        const query: SessionListQuery = {
          page: append ? this.currentPage + 1 : 1,
          pageSize: this.pageSize,
          ...this.filters,
          ...params
        }
        
        const response = await getSessionList(query)
        
        if (response.code === 200) {
          if (!response.data) {
            throw new Error('获取场次列表失败：响应数据为空')
          }
          const { items, total, page, pageSize, hasMore } = response.data
          
          if (append) {
            this.sessionList.push(...items)
            this.currentPage = page
          } else {
            this.sessionList = items
            this.currentPage = page
          }
          
          this.total = total
          this.hasMore = hasMore
          this.filters = query
        } else {
          throw new Error(response.message || '获取场次列表失败')
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
     * 刷新场次列表
     */
    async refreshSessionList(params?: SessionListQuery): Promise<void> {
      this.refreshing = true
      await this.fetchSessionList(params, false)
    },

    /**
     * 加载更多场次
     */
    async loadMoreSessions(): Promise<void> {
      if (this.hasMore && !this.loadingMore) {
        await this.fetchSessionList(this.filters, true)
      }
    },

    /**
     * 获取场次详情
     */
    async fetchSessionDetail(sessionId: string, useCache: boolean = true): Promise<void> {
      // 检查缓存
      if (useCache && this.sessionCache.has(sessionId)) {
        this.currentSession = this.sessionCache.get(sessionId)!
        return
      }
      
      this.detailLoading = true
      this.error = null
      
      try {
        const response = await getSessionDetail(sessionId)
        
        if (response.code === 200) {
          if (!response.data) {
            throw new Error('获取场次详情失败：响应数据为空')
          }
          
          this.currentSession = response.data
          
          // 更新缓存
          this.sessionCache.set(sessionId, response.data)
          
          // 限制缓存大小
          if (this.sessionCache.size > 30) {
            const firstKey = this.sessionCache.keys().next().value
            if (firstKey) {
            this.sessionCache.delete(firstKey)
            }
          }
        } else {
          throw new Error(response.message || '获取场次详情失败')
        }
      } catch (error: any) {
        const errorMessage = error?.message || error?.errMsg || '获取场次详情失败'
        const detailedError = new Error(errorMessage)
        this.error = detailedError
        console.error('❌ fetchSessionDetail 错误:', {
          sessionId,
          error: errorMessage,
          errorType: error?.constructor?.name,
          errorStack: error?.stack
        })
        throw detailedError
      } finally {
        this.detailLoading = false
      }
    },

    /**
     * 创建场次
     */
    async createSession(sessionData: CreateSessionRequest): Promise<string> {
      this.loading = true
      this.error = null
      
      try {
        const response = await createSession(sessionData)
        
        if (response.code === 200) {
          // 刷新场次列表
          await this.refreshSessionList()
          if (!response.data) {
            throw new Error('创建场次失败：响应数据为空')
          }
          return response.data.sessionId
        } else {
          throw new Error(response.message || '创建场次失败')
        }
      } catch (error) {
        this.error = error as Error
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * 更新场次信息
     */
    async updateSession(sessionId: string, updateData: UpdateSessionRequest): Promise<void> {
      this.loading = true
      this.error = null
      
      try {
        const response = await updateSession(sessionId, updateData)
        
        if (response.code === 200) {
          // 更新本地数据
          const index = this.sessionList.findIndex(session => session.id === sessionId)
          if (index !== -1) {
            Object.assign(this.sessionList[index], response.data)
          }
          
          // 更新当前场次
          if (this.currentSession?.id === sessionId) {
            Object.assign(this.currentSession, response.data)
          }
          
          // 更新缓存
          if (this.sessionCache.has(sessionId)) {
            const cachedSession = this.sessionCache.get(sessionId)!
            Object.assign(cachedSession, response.data)
          }
        } else {
          throw new Error(response.message || '更新场次失败')
        }
      } catch (error) {
        this.error = error as Error
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * 删除场次
     */
    async deleteSession(sessionId: string): Promise<void> {
      this.loading = true
      this.error = null
      
      try {
        const response = await deleteSession(sessionId)
        
        if (response.code === 200) {
          // 从列表中移除
          const index = this.sessionList.findIndex(session => session.id === sessionId)
          if (index !== -1) {
            this.sessionList.splice(index, 1)
            this.total -= 1
          }
          
          // 清除当前场次
          if (this.currentSession?.id === sessionId) {
            this.currentSession = null
          }
          
          // 清除缓存
          this.sessionCache.delete(sessionId)
        } else {
          throw new Error(response.message || '删除场次失败')
        }
      } catch (error) {
        this.error = error as Error
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * 获取场次统计数据
     */
    async fetchSessionStatistics(sessionId?: string): Promise<void> {
      try {
        const response = await getSessionStatistics(sessionId)
        
        if (response.code === 200) {
          this.statistics = response.data
        } else {
          throw new Error(response.message || '获取统计数据失败')
        }
      } catch (error) {
        console.error('获取场次统计失败:', error)
      }
    },

    /**
     * 开始观看
     */
    startWatching(sessionId: string): void {
      this.isWatching = true
      this.watchStartTime = Date.now()
      
      // 更新观看数
      this.incrementViewCount(sessionId)
    },

    /**
     * 结束观看
     */
    stopWatching(): number {
      const duration = this.watchDuration
      this.isWatching = false
      this.watchStartTime = null
      
      return duration
    },

    /**
     * 暂停观看
     */
    pauseWatching(): void {
      this.isWatching = false
    },

    /**
     * 恢复观看
     */
    resumeWatching(): void {
      this.isWatching = true
    },

    /**
     * 增加场次观看数
     */
    incrementViewCount(sessionId: string): void {
      const session = this.sessionList.find(s => s.id === sessionId)
      if (session) {
        session.viewCount += 1
      }
      
      if (this.currentSession?.id === sessionId) {
        this.currentSession.viewCount += 1
      }
      
      // 更新缓存
      const cachedSession = this.sessionCache.get(sessionId)
      if (cachedSession) {
        cachedSession.viewCount += 1
      }
    },

    /**
     * 更新场次状态
     */
    updateSessionStatus(sessionId: string, status: Session['status']): void {
      const session = this.sessionList.find(s => s.id === sessionId)
      if (session) {
        session.status = status
      }
      
      if (this.currentSession?.id === sessionId) {
        this.currentSession.status = status
      }
      
      // 更新缓存
      const cachedSession = this.sessionCache.get(sessionId)
      if (cachedSession) {
        cachedSession.status = status
      }
    },

    /**
     * 设置筛选条件
     */
    setFilters(filters: SessionListQuery): void {
      this.filters = { ...this.filters, ...filters }
    },

    /**
     * 清除筛选条件
     */
    clearFilters(): void {
      this.filters = {}
    },

    /**
     * 清除场次数据
     */
    clearSessionData(): void {
      this.sessionList = []
      this.currentSession = null
      this.statistics = null
      this.currentPage = 1
      this.total = 0
      this.hasMore = true
      this.error = null
      this.isWatching = false
      this.watchStartTime = null
      this.sessionCache.clear()
    },

    /**
     * 清除缓存
     */
    clearCache(): void {
      this.sessionCache.clear()
    }
  }
})
