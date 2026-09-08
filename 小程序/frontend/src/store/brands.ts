/**
 * 品牌状态管理
 * 管理品牌列表、品牌详情、CRUD操作（Admin用户）、品牌与专题的关联关系
 */

import { defineStore } from 'pinia'
import type { 
  BrandItem,
  BrandListQuery,
  CreateBrandRequest,
  UpdateBrandRequest
} from '@/types/brands'
import type { PaginatedResponse } from '@/types/common'
import { getBrandList, createBrand, updateBrand, deleteBrand } from '@/api/brands'
// TODO: 待后端API实现后启用
// import { getBrandById, getBrandStatistics, getPopularBrands } from '@/api/brands'

interface BrandsState {
  // 品牌列表
  brandList: BrandItem[]
  
  // 热门品牌
  popularBrands: Brand[]
  
  // 分页信息
  currentPage: number
  pageSize: number
  total: number
  hasMore: boolean
  
  // 当前品牌详情
  currentBrand: BrandItem | null
  
  // 统计数据
  statistics: null
  
  // 加载状态
  loading: boolean
  refreshing: boolean
  loadingMore: boolean
  detailLoading: boolean
  popularLoading: boolean
  
  // 错误状态
  error: Error | null
  
  // 筛选条件
  filters: BrandListQuery
  
  // 缓存
  brandCache: Map<string, BrandDetail>
}

export const useBrandsStore = defineStore('brands', {
  state: (): BrandsState => ({
    brandList: [],
    popularBrands: [],
    currentPage: 1,
    pageSize: 20,
    total: 0,
    hasMore: true,
    currentBrand: null,
    statistics: null,
    loading: false,
    refreshing: false,
    loadingMore: false,
    detailLoading: false,
    popularLoading: false,
    error: null,
    filters: {},
    brandCache: new Map()
  }),

  getters: {
    /**
     * 可用品牌（is_active=true）
     */
    activeBrands: (state) => state.brandList.filter(brand => brand.is_active === true),
    
    /**
     * 是否为空列表
     */
    isEmpty: (state) => state.brandList.length === 0 && !state.loading
  },

  actions: {
    /**
     * 获取品牌列表
     */
    async fetchBrandList(params?: BrandListQuery, append: boolean = false): Promise<void> {
      if (append) {
        this.loadingMore = true
      } else {
        this.loading = true
        this.currentPage = 1
      }
      
      this.error = null
      
      try {
        const query: BrandListQuery = { ...this.filters, ...params }

        const response = await getBrandList(query)

        if (response.code === 200) {
          const items: BrandItem[] = Array.isArray(response.data) ? response.data : []
          this.brandList = items
          this.total = items.length
          this.hasMore = false
          this.filters = query
        } else {
          throw new Error(response.message || '获取品牌列表失败')
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
     * 刷新品牌列表
     */
    async refreshBrandList(params?: BrandListQuery): Promise<void> {
      this.refreshing = true
      await this.fetchBrandList(params, false)
    },

    /**
     * 加载更多品牌
     */
    async loadMoreBrands(): Promise<void> {
      if (this.hasMore && !this.loadingMore) {
        await this.fetchBrandList(this.filters, true)
      }
    },

    // TODO: 待后端API实现后启用
    // /**
    //  * 获取热门品牌
    //  */
    // async fetchPopularBrands(limit: number = 10): Promise<void> {
    //   this.popularLoading = true
    //   
    //   try {
    //     const response = await getPopularBrands(limit)
    //     
    //     if (response.code === 200) {
    //       this.popularBrands = response.data
    //     } else {
    //       throw new Error(response.message || '获取热门品牌失败')
    //     }
    //   } catch (error) {
    //     console.error('获取热门品牌失败:', error)
    //   } finally {
    //     this.popularLoading = false
    //   }
    // },

    // TODO: 待后端API实现后启用
    // /**
    //  * 获取品牌详情
    //  */
    // async fetchBrandDetail(brandId: string, useCache: boolean = true): Promise<void> {
    //   // 检查缓存
    //   if (useCache && this.brandCache.has(brandId)) {
    //     this.currentBrand = this.brandCache.get(brandId)!
    //     return
    //   }
    //   
    //   this.detailLoading = true
    //   this.error = null
    //   
    //   try {
    //     const response = await getBrandById(brandId)
    //     
    //     if (response.code === 200) {
    //       this.currentBrand = response.data
    //       
    //       // 更新缓存
    //       this.brandCache.set(brandId, response.data)
    //       
    //       // 限制缓存大小
    //       if (this.brandCache.size > 30) {
    //         const firstKey = this.brandCache.keys().next().value
    //         this.brandCache.delete(firstKey)
    //       }
    //     } else {
    //       throw new Error(response.message || '获取品牌详情失败')
    //     }
    //   } catch (error) {
    //     this.error = error as Error
    //     throw error
    //   } finally {
    //     this.detailLoading = false
    //   }
    // },

    /**
     * 创建品牌（Admin功能）
     */
    async createBrand(brandData: CreateBrandRequest): Promise<string> {
      this.loading = true
      this.error = null
      
      try {
        const response = await createBrand(brandData)
        
        if (response.code === 200) {
          // 刷新品牌列表
          await this.refreshBrandList()
          return response.data.id
        } else {
          throw new Error(response.message || '创建品牌失败')
        }
      } catch (error) {
        this.error = error as Error
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * 更新品牌（Admin功能）
     */
    async updateBrand(brandId: string, updateData: UpdateBrandRequest): Promise<void> {
      this.loading = true
      this.error = null
      
      try {
        const response = await updateBrand(brandId, updateData)
        
        if (response.code === 200) {
          // 更新本地数据
          const index = this.brandList.findIndex(brand => brand.id === brandId)
          if (index !== -1) {
            Object.assign(this.brandList[index], response.data)
          }
          
          // 更新当前品牌
          if (this.currentBrand?.id === brandId) {
            Object.assign(this.currentBrand, response.data)
          }
          
          // 更新缓存
          if (this.brandCache.has(brandId)) {
            const cachedBrand = this.brandCache.get(brandId)!
            Object.assign(cachedBrand, response.data)
          }
        } else {
          throw new Error(response.message || '更新品牌失败')
        }
      } catch (error) {
        this.error = error as Error
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * 删除品牌（Admin功能）
     */
    async deleteBrand(brandId: string): Promise<void> {
      this.loading = true
      this.error = null
      
      try {
        const response = await deleteBrand(brandId)
        
        if (response.code === 200) {
          // 从列表中移除
          const index = this.brandList.findIndex(brand => brand.id === brandId)
          if (index !== -1) {
            this.brandList.splice(index, 1)
            this.total -= 1
          }
          
          // 清除当前品牌
          if (this.currentBrand?.id === brandId) {
            this.currentBrand = null
          }
          
          // 清除缓存
          this.brandCache.delete(brandId)
        } else {
          throw new Error(response.message || '删除品牌失败')
        }
      } catch (error) {
        this.error = error as Error
        throw error
      } finally {
        this.loading = false
      }
    },

    // TODO: 待后端API实现后启用
    // /**
    //  * 获取品牌统计数据
    //  */
    // async fetchBrandStatistics(brandId?: string): Promise<void> {
    //   try {
    //     const response = await getBrandStatistics(brandId)
    //     
    //     if (response.code === 200) {
    //       this.statistics = response.data
    //     } else {
    //       throw new Error(response.message || '获取品牌统计失败')
    //     }
    //   } catch (error) {
    //     console.error('获取品牌统计失败:', error)
    //   }
    // },

    /**
     * 搜索品牌
     */
    searchBrands(keyword: string): BrandItem[] {
      if (!keyword.trim()) {
        return this.brandList
      }
      
      const searchKeyword = keyword.toLowerCase()
      return this.brandList.filter(brand =>
        brand.name.toLowerCase().includes(searchKeyword) ||
        (brand.description && brand.description.toLowerCase().includes(searchKeyword))
      )
    },

    /**
     * 按分类筛选品牌
     */
    filterByCategory(_category: string): BrandItem[] {
      // 后端未提供分类字段，此函数保留兼容但不做筛选
      return this.brandList
    },

    /**
     * 获取品牌的专题列表
     */
    getBrandTopics(_brandId: string): any[] {
      // 关联专题通过 /brands/{id}/content 获取；此处留空
      return []
    },

    /**
     * 设置筛选条件
     */
    setFilters(filters: BrandListQuery): void {
      this.filters = { ...this.filters, ...filters }
    },

    /**
     * 清除筛选条件
     */
    clearFilters(): void {
      this.filters = {}
    },

    /**
     * 增加品牌关注数
     */
    incrementFollowerCount(_brandId: string): void {
      // 后端未定义关注数，本方法暂不实现
    },

    /**
     * 减少品牌关注数
     */
    decrementFollowerCount(_brandId: string): void {
      // 后端未定义关注数，本方法暂不实现
    },

    /**
     * 清除品牌数据
     */
    clearBrandsData(): void {
      this.brandList = []
      this.popularBrands = []
      this.currentBrand = null
      this.statistics = null
      this.currentPage = 1
      this.total = 0
      this.hasMore = true
      this.error = null
      this.brandCache.clear()
    },

    /**
     * 清除缓存
     */
    clearCache(): void {
      this.brandCache.clear()
    }
  },

  // persist: {
  //   key: 'brands-store',
  //   paths: ['filters']
  // }
})
