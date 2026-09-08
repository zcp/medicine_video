/**
 * 用户收藏状态管理
 * 管理收藏列表、收藏状态、分页加载、实时同步收藏状态、本地缓存和数据持久化
 */

import { defineStore } from 'pinia'
import type { 
  Favorite,
  FavoriteDetail,
  FavoriteListQuery,
  CreateFavoriteRequest,
  FavoriteStatistics,
  FavoriteFolder
} from '@/types/favorites'
import type { PaginatedResponse } from '@/types/common'
import { request } from '@/utils/request'
import { API_PATHS } from '@/config/api'

/** 内联收藏 API，避免小程序 require('api/favorites') 模块未注册 */
const addFavorite = (roomId: string) =>
  request.post(API_PATHS.FAVORITE.ADD, { room_id: roomId }, { loading: true, loadingText: '收藏中...' })

const getFavoriteList = (params?: { page?: number; size?: number }) =>
  request.get(API_PATHS.FAVORITE.LIST, { data: params })

const removeFavorite = (roomId: string) =>
  request.delete(API_PATHS.FAVORITE.REMOVE(roomId), { loading: true, loadingText: '取消收藏中...' })

interface FavoritesState {
  // 收藏列表
  favoriteList: Favorite[]
  
  // 分页信息
  currentPage: number
  pageSize: number
  total: number
  hasMore: boolean
  
  // 收藏夹
  folders: FavoriteFolder[]
  
  // 当前收藏详情
  currentFavorite: FavoriteDetail | null
  
  // 收藏状态缓存
  favoriteStatus: Map<string, boolean>
  
  // 统计数据
  statistics: FavoriteStatistics | null
  
  // 加载状态
  loading: boolean
  refreshing: boolean
  loadingMore: boolean
  detailLoading: boolean
  statusLoading: Set<string>
  
  // 错误状态
  error: Error | null
  
  // 筛选条件
  filters: FavoriteListQuery
}

export const useFavoritesStore = defineStore('favorites', {
  state: (): FavoritesState => ({
    favoriteList: [],
    currentPage: 1,
    pageSize: 20,
    total: 0,
    hasMore: true,
    folders: [],
    currentFavorite: null,
    favoriteStatus: new Map(),
    statistics: null,
    loading: false,
    refreshing: false,
    loadingMore: false,
    detailLoading: false,
    statusLoading: new Set(),
    error: null,
    filters: {}
  }),

  getters: {
    /**
     * 按类型分组的收藏
     */
    favoritesByType: (state) => {
      const groups: Record<string, Favorite[]> = {}
      state.favoriteList.forEach(favorite => {
        const type = favorite.contentType
        if (!groups[type]) {
          groups[type] = []
        }
        groups[type].push(favorite)
      })
      return groups
    },
    
    /**
     * 按收藏夹分组
     */
    favoritesByFolder: (state) => {
      const groups: Record<string, Favorite[]> = {}
      state.favoriteList.forEach(favorite => {
        const folderId = favorite.folderId || 'default'
        if (!groups[folderId]) {
          groups[folderId] = []
        }
        groups[folderId].push(favorite)
      })
      return groups
    },
    
    /**
     * 是否为空列表
     */
    isEmpty: (state) => state.favoriteList.length === 0 && !state.loading,
    
    /**
     * 收藏总数
     */
    totalCount: (state) => state.total,
    
    /**
     * 默认收藏夹
     */
    defaultFolder: (state) => state.folders.find(folder => folder.isDefault),
    
    /**
     * 自定义收藏夹
     */
    customFolders: (state) => state.folders.filter(folder => !folder.isDefault)
  },

  actions: {
    /**
     * 获取收藏列表
     */
    async fetchFavoriteList(params?: FavoriteListQuery, append: boolean = false): Promise<void> {
      if (append) {
        this.loadingMore = true
      } else {
        this.loading = true
        this.currentPage = 1
      }
      
      this.error = null
      
      try {
        const query: FavoriteListQuery = {
          page: append ? this.currentPage + 1 : 1,
          pageSize: this.pageSize,
          ...this.filters,
          ...params
        }
        
        const response = await getFavoriteList(query)
        
        if (response.code === 200) {
          const { items, total, page, pageSize, hasMore } = response.data
          
          if (append) {
            this.favoriteList.push(...items)
            this.currentPage = page
          } else {
            this.favoriteList = items
            this.currentPage = page
          }
          
          this.total = total
          this.hasMore = hasMore
          this.filters = query
          
          // 更新收藏状态缓存
          items.forEach((favorite: Favorite) => {
            this.favoriteStatus.set(favorite.targetId, true)
          })
        } else {
          throw new Error(response.message || '获取收藏列表失败')
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
     * 刷新收藏列表
     */
    async refreshFavoriteList(params?: FavoriteListQuery): Promise<void> {
      this.refreshing = true
      await this.fetchFavoriteList(params, false)
    },

    /**
     * 加载更多收藏
     */
    async loadMoreFavorites(): Promise<void> {
      if (this.hasMore && !this.loadingMore) {
        await this.fetchFavoriteList(this.filters, true)
      }
    },

    /**
     * 获取收藏夹列表
     */
    async fetchFolderList(): Promise<void> {
      try {
        const response = await getFavoriteFolders()
        
        if (response.code === 200) {
          this.folders = response.data
        } else {
          throw new Error(response.message || '获取收藏夹列表失败')
        }
      } catch (error) {
        console.error('获取收藏夹列表失败:', error)
      }
    },

    /**
     * 创建收藏夹
     */
    async createFolder(name: string, description?: string): Promise<string> {
      this.loading = true
      this.error = null
      
      try {
        const response = await createFavoriteFolder({ name, description })
        
        if (response.code === 200) {
          // 刷新收藏夹列表
          await this.fetchFolderList()
          return response.data.folderId
        } else {
          throw new Error(response.message || '创建收藏夹失败')
        }
      } catch (error) {
        this.error = error as Error
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * 添加收藏
     */
    async addFavorite(data: CreateFavoriteRequest): Promise<void> {
      this.error = null
      
      try {
        // TODO: API参数格式需要调整
        const response = await addFavorite(data.contentId)
        
        if (response.code === 200) {
          // 更新收藏状态
          this.favoriteStatus.set(data.targetId, true)
          
          // 更新统计数据
          if (this.statistics) {
            this.statistics.totalCount += 1
          }
          
          // 如果是当前列表的内容类型，刷新列表
          if (!this.filters.contentType || this.filters.contentType === data.type) {
            await this.refreshFavoriteList()
          }
        } else {
          throw new Error(response.message || '添加收藏失败')
        }
      } catch (error) {
        this.error = error as Error
        throw error
      }
    },

    /**
     * 取消收藏
     */
    async removeFavorite(contentId: string, contentType: string): Promise<void> {
      this.error = null
      
      try {
        // TODO: API参数格式需要调整(原需contentType)
        const response = await removeFavorite(contentId)
        
        if (response.code === 200) {
          // 更新收藏状态
          this.favoriteStatus.set(contentId, false)
          
          // 从列表中移除
          const index = this.favoriteList.findIndex(
            item => item.targetId === contentId && item.type === contentType
          )
          if (index !== -1) {
            this.favoriteList.splice(index, 1)
            this.total = Math.max(0, this.total - 1)
          }
          
          // 更新统计数据
          if (this.statistics) {
            this.statistics.totalCount = Math.max(0, this.statistics.totalCount - 1)
          }
        } else {
          throw new Error(response.message || '取消收藏失败')
        }
      } catch (error) {
        this.error = error as Error
        throw error
      }
    },

    /**
     * 切换收藏状态
     */
    async toggleFavorite(data: CreateFavoriteRequest): Promise<boolean> {
      const isFavorited = await this.checkFavoriteStatus(data.contentId, data.contentType)
      
      if (isFavorited) {
        await this.removeFavorite(data.contentId, data.contentType)
        return false
      } else {
        await this.addFavorite(data)
        return true
      }
    },

    /**
     * 检查收藏状态
     */
    async checkFavoriteStatus(contentId: string, contentType: string): Promise<boolean> {
      // 先检查缓存
      const cacheKey = contentId
      if (this.favoriteStatus.has(cacheKey)) {
        return this.favoriteStatus.get(cacheKey)!
      }
      
      // 避免重复请求
      if (this.statusLoading.has(cacheKey)) {
        return false
      }
      
      this.statusLoading.add(cacheKey)
      
      try {
        // 后端无独立检查接口，从已加载的收藏列表中推断状态
        const isFavorited = this.favoriteList.some(
          (item: any) => item.room_id === contentId || item.id === contentId
        )
        this.favoriteStatus.set(cacheKey, isFavorited)
        return isFavorited
      } catch (error) {
        console.error('检查收藏状态失败:', error)
        return false
      } finally {
        this.statusLoading.delete(cacheKey)
      }
    },

    /**
     * 批量添加收藏
     */
    async batchAddFavorites(items: CreateFavoriteRequest[]): Promise<void> {
      this.loading = true
      this.error = null
      
      try {
        // 映射字段名：type -> contentType, targetId -> contentId
        const mappedItems = items.map(item => ({
          contentType: item.type,
          contentId: item.targetId
        }))
        const response = await batchAddToFavorites(mappedItems)
        
        if (response.code === 200) {
          // 更新收藏状态
          items.forEach(item => {
            this.favoriteStatus.set(item.targetId, true)
          })
          
          // 刷新列表
          await this.refreshFavoriteList()
        } else {
          throw new Error(response.message || '批量添加收藏失败')
        }
      } catch (error) {
        this.error = error as Error
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * 批量取消收藏
     */
    async batchRemoveFavorites(favoriteIds: string[]): Promise<void> {
      this.loading = true
      this.error = null
      
      try {
        const response = await batchRemoveFromFavorites(favoriteIds)
        
        if (response.code === 200) {
          // 从列表中移除
          favoriteIds.forEach(id => {
            const index = this.favoriteList.findIndex(item => item.id === id)
            if (index !== -1) {
              const favorite = this.favoriteList[index]
              this.favoriteStatus.set(favorite.contentId, false)
              this.favoriteList.splice(index, 1)
            }
          })
          
          this.total = Math.max(0, this.total - favoriteIds.length)
        } else {
          throw new Error(response.message || '批量取消收藏失败')
        }
      } catch (error) {
        this.error = error as Error
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * 获取收藏统计
     */
    async fetchFavoriteStatistics(): Promise<void> {
      try {
        const response = await getFavoriteStatistics()
        
        if (response.code === 200) {
          this.statistics = response.data
        } else {
          throw new Error(response.message || '获取收藏统计失败')
        }
      } catch (error) {
        console.error('获取收藏统计失败:', error)
      }
    },

    /**
     * 按类型筛选收藏
     */
    filterByType(type: string): void {
      this.setFilters({ contentType: type })
      this.fetchFavoriteList(this.filters)
    },

    /**
     * 按收藏夹筛选
     */
    filterByFolder(folderId: string): void {
      this.setFilters({ folderId })
      this.fetchFavoriteList(this.filters)
    },

    /**
     * 设置筛选条件
     */
    setFilters(filters: FavoriteListQuery): void {
      this.filters = { ...this.filters, ...filters }
    },

    /**
     * 清除筛选条件
     */
    clearFilters(): void {
      this.filters = {}
    },

    /**
     * 获取本地收藏状态（同步）
     */
    getFavoriteStatus(contentId: string): boolean {
      return this.favoriteStatus.get(contentId) || false
    },

    /**
     * 设置收藏状态（本地）
     */
    setFavoriteStatus(contentId: string, isFavorited: boolean): void {
      this.favoriteStatus.set(contentId, isFavorited)
    },

    /**
     * 清除收藏数据
     */
    clearFavoritesData(): void {
      this.favoriteList = []
      this.folders = []
      this.currentFavorite = null
      this.favoriteStatus.clear()
      this.statistics = null
      this.currentPage = 1
      this.total = 0
      this.hasMore = true
      this.error = null
      this.statusLoading.clear()
    },

    /**
     * 清除状态缓存
     */
    clearStatusCache(): void {
      this.favoriteStatus.clear()
    }
  },

  // persist: {
  //   key: 'favorites-store',
  //   paths: ['favoriteStatus', 'filters', 'statistics']
  // }
})
