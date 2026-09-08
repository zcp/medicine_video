/**
 * 房间状态管理
 * 管理直播房间列表、房间详情、房间状态等（支持分页加载）
 */

import { defineStore } from 'pinia'
import type { 
  LiveRoom,
  LiveRoomDetail,
  RoomListQuery,
  CreateRoomRequest,
  UpdateRoomRequest,
  RoomStatistics
} from '@/types/room'
import type { PaginatedResponse } from '@/types/common'
import { 
  getRooms,
  getRoomById,
  createRoom,
  updateRoom,
  deleteRoom,
  getRoomStatistics
} from '@/api/room'

interface RoomState {
  // 房间列表
  roomList: LiveRoom[]
  
  // 分页信息
  currentPage: number
  pageSize: number
  total: number
  hasMore: boolean
  
  // 当前房间详情
  currentRoom: LiveRoomDetail | null
  
  // 房间统计
  statistics: RoomStatistics | null
  
  // 加载状态
  loading: boolean
  refreshing: boolean
  loadingMore: boolean
  detailLoading: boolean
  
  // 错误状态
  error: Error | null
  
  // 筛选条件
  filters: RoomListQuery
  
  // 缓存
  roomCache: Map<string, LiveRoomDetail>
  
  // 从首页传递过来的房间数据（临时存储，用于跨页面传递）
  selectedRoomFromHome: any | null
}

export const useRoomStore = defineStore('room', {
  state: (): RoomState => ({
    roomList: [],
    currentPage: 1,
    pageSize: 20,
    total: 0,
    hasMore: true,
    currentRoom: null,
    statistics: null,
    loading: false,
    refreshing: false,
    loadingMore: false,
    detailLoading: false,
    error: null,
    filters: {},
    roomCache: new Map(),
    selectedRoomFromHome: null
  }),

  getters: {
    /**
     * 直播中的房间
     */
    liveRooms: (state) => state.roomList.filter(room => room.status === 'live'),
    
    /**
     * 预告房间
     */
    upcomingRooms: (state) => state.roomList.filter(room => room.status === 'upcoming'),
    
    /**
     * 回放房间
     */
    replayRooms: (state) => state.roomList.filter(room => room.status === 'replay'),
    
    /**
     * 是否为空列表
     */
    isEmpty: (state) => state.roomList.length === 0 && !state.loading,
    
    /**
     * 当前房间是否为直播状态
     */
    isCurrentRoomLive: (state) => state.currentRoom?.status === 'live'
  },

  actions: {
    /**
     * 获取房间列表（支持分页和筛选）
     */
    async fetchRoomList(params?: RoomListQuery, append: boolean = false): Promise<void> {
      if (append) {
        this.loadingMore = true
      } else {
        this.loading = true
        this.currentPage = 1
      }
      
      this.error = null
      
      try {
        const query: RoomListQuery = {
          page: append ? this.currentPage + 1 : 1,
          pageSize: this.pageSize,
          ...this.filters,
          ...params
        }

        // 映射到后端 getRooms 支持的参数
        const apiParams: {
          page?: number
          size?: number
          category_id?: string
          sort?: string
        } = {
          page: query.page,
          size: query.pageSize
        }

        // 暂无 category_id，保留占位（若 filters 中未来有）
        if ((query as any).category_id) {
          apiParams.category_id = (query as any).category_id
        }

        if (query.sortBy) {
          const sortOrder = query.sortOrder === 'desc' ? 'desc' : 'asc'
          const backendSortField = query.sortBy === 'createdAt' ? 'created_at' : query.sortBy
          apiParams.sort = `${backendSortField}:${sortOrder}`
        }
        
        const response = await getRooms(apiParams)
        
        if (response.code === 200) {
          const { items, total, page, pageSize, hasMore } = response.data
          
          if (append) {
            // 追加数据
            this.roomList.push(...items)
            this.currentPage = page
          } else {
            // 覆盖数据
            this.roomList = items
            this.currentPage = page
          }
          
          this.total = total
          this.hasMore = hasMore
          this.filters = query
        } else {
          throw new Error(response.message || '获取房间列表失败')
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
     * 刷新房间列表
     */
    async refreshRoomList(params?: RoomListQuery): Promise<void> {
      this.refreshing = true
      await this.fetchRoomList(params, false)
    },

    /**
     * 加载更多房间
     */
    async loadMoreRooms(): Promise<void> {
      if (this.hasMore && !this.loadingMore) {
        await this.fetchRoomList(this.filters, true)
      }
    },

    /**
     * 获取房间详情
     */
    async fetchRoomDetail(roomId: string, useCache: boolean = true): Promise<void> {
      // 检查缓存
      if (useCache && this.roomCache.has(roomId)) {
        this.currentRoom = this.roomCache.get(roomId)!
        return
      }
      
      this.detailLoading = true
      this.error = null
      
      try {
        const response = await getRoomById(roomId)
        
        if (response.code === 200) {
          this.currentRoom = response.data
          
          // 更新缓存
          this.roomCache.set(roomId, response.data)
          
          // 限制缓存大小
          if (this.roomCache.size > 50) {
            const firstKey = this.roomCache.keys().next().value
            this.roomCache.delete(firstKey)
          }
        } else {
          throw new Error(response.message || '获取房间详情失败')
        }
      } catch (error) {
        this.error = error as Error
        throw error
      } finally {
        this.detailLoading = false
      }
    },

    /**
     * 创建房间
     */
    async createRoom(roomData: CreateRoomRequest): Promise<string> {
      this.loading = true
      this.error = null
      
      try {
        const response = await createRoom(roomData)

        if (response.code === 200) {
          const roomId = String((response.data as any)?.roomId || (response.data as any)?.id || '')
          if (!roomId) {
            throw new Error('创建房间失败：缺少 roomId')
          }

          // 刷新房间列表
          await this.refreshRoomList()
          return roomId
        }

        throw new Error(response.message || '创建房间失败')
      } catch (error) {
        this.error = error as Error
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * 更新房间信息
     */
    async updateRoom(roomId: string, updateData: UpdateRoomRequest): Promise<void> {
      this.loading = true
      this.error = null
      
      try {
        const response = await updateRoom(roomId, updateData)
        
        if (response.code === 200) {
          // 更新本地数据
          const index = this.roomList.findIndex(room => room.id === roomId)
          if (index !== -1) {
            Object.assign(this.roomList[index], response.data)
          }
          
          // 更新当前房间
          if (this.currentRoom?.id === roomId) {
            Object.assign(this.currentRoom, response.data)
          }
          
          // 更新缓存
          if (this.roomCache.has(roomId)) {
            const cachedRoom = this.roomCache.get(roomId)!
            Object.assign(cachedRoom, response.data)
          }
        } else {
          throw new Error(response.message || '更新房间失败')
        }
      } catch (error) {
        this.error = error as Error
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * 删除房间
     */
    async deleteRoom(roomId: string): Promise<void> {
      this.loading = true
      this.error = null
      
      try {
        const response = await deleteRoom(roomId)
        
        if (response.code === 200) {
          // 从列表中移除
          const index = this.roomList.findIndex(room => room.id === roomId)
          if (index !== -1) {
            this.roomList.splice(index, 1)
            this.total -= 1
          }
          
          // 清除当前房间
          if (this.currentRoom?.id === roomId) {
            this.currentRoom = null
          }
          
          // 清除缓存
          this.roomCache.delete(roomId)
        } else {
          throw new Error(response.message || '删除房间失败')
        }
      } catch (error) {
        this.error = error as Error
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * 获取房间统计数据
     */
    async fetchRoomStatistics(roomId?: string): Promise<void> {
      try {
        const response = await getRoomStatistics(roomId)
        
        if (response.code === 200) {
          this.statistics = response.data
        } else {
          throw new Error(response.message || '获取统计数据失败')
        }
      } catch (error) {
        console.error('获取房间统计失败:', error)
      }
    },

    /**
     * 设置筛选条件
     */
    setFilters(filters: RoomListQuery): void {
      this.filters = { ...this.filters, ...filters }
    },

    /**
     * 清除筛选条件
     */
    clearFilters(): void {
      this.filters = {}
    },

    /**
     * 更新房间状态
     */
    updateRoomStatus(roomId: string, status: LiveRoom['status']): void {
      const room = this.roomList.find(r => r.id === roomId)
      if (room) {
        room.status = status
      }
      
      if (this.currentRoom?.id === roomId) {
        this.currentRoom.status = status
      }
      
      // 更新缓存
      const cachedRoom = this.roomCache.get(roomId)
      if (cachedRoom) {
        cachedRoom.status = status
      }
    },

    /**
     * 增加房间观看数
     */
    incrementViewCount(roomId: string): void {
      const room = this.roomList.find(r => r.id === roomId)
      if (room) {
        room.viewerCount += 1
      }
      
      if (this.currentRoom?.id === roomId) {
        this.currentRoom.viewerCount += 1
      }
      
      // 更新缓存
      const cachedRoom = this.roomCache.get(roomId)
      if (cachedRoom) {
        cachedRoom.viewerCount += 1
      }
    },

    /**
     * 清除房间数据
     */
    clearRoomData(): void {
      this.roomList = []
      this.currentRoom = null
      this.statistics = null
      this.currentPage = 1
      this.total = 0
      this.hasMore = true
      this.error = null
      this.roomCache.clear()
    },

    /**
     * 清除缓存
     */
    clearCache(): void {
      this.roomCache.clear()
    },

    /**
     * 设置从首页选中的房间（用于跨页面传递数据）
     */
    setSelectedRoomFromHome(room: any): void {
      this.selectedRoomFromHome = room
    },

    /**
     * 获取从首页选中的房间
     */
    getSelectedRoomFromHome(): any | null {
      return this.selectedRoomFromHome
    },

    /**
     * 清除从首页选中的房间
     */
    clearSelectedRoomFromHome(): void {
      this.selectedRoomFromHome = null
    }
  }
})
