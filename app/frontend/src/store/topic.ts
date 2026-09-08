import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { topicApi } from '../api/topic'
import type { 
  Topic, 
  TopicCategory, 
  RoomInCategory, 
  TopicCreate, 
  TopicUpdate, 
  CategoryCreate, 
  CategoryUpdate,
  RoomAssociation,
  TopicListParams
} from '../types/topic'

interface TopicState {
  topics: Topic[]
  currentTopic: Topic | null
  categories: TopicCategory[]
  loading: boolean
  error: string | null
}

export const useTopicStore = defineStore('topic', {
  state: (): TopicState => ({
    topics: [],
    currentTopic: null,
    categories: [],
    loading: false,
    error: null
  }),

  getters: {
    // 获取已发布的专题列表
    publishedTopics: (state) => state.topics.filter((topic: Topic) => topic.status === 'published'),
    
    // 获取草稿专题列表
    draftTopics: (state) => state.topics.filter((topic: Topic) => topic.status === 'draft'),
    
    // 获取已归档专题列表
    archivedTopics: (state) => state.topics.filter((topic: Topic) => topic.status === 'archived'),
    
    // 根据ID获取专题
    getTopicById: (state) => (id: string) => state.topics.find((topic: Topic) => topic.id === id),
    
    // 获取当前专题的分类数量
    currentTopicCategoriesCount: (state) => state.categories.length,
    
    // 获取当前专题的直播间总数
    currentTopicRoomsCount: (state) => {
      return state.categories.reduce((total: number, category: TopicCategory) => {
        return total + (category.rooms?.length || 0)
      }, 0)
    }
  },

  actions: {
    // 设置加载状态
    setLoading(loading: boolean) {
      this.loading = loading
    },

    // 设置错误信息
    setError(error: string | null) {
      this.error = error
    },

    // 获取专题列表
    async fetchTopics(params?: TopicListParams) {
      try {
        this.setLoading(true)
        this.setError(null)
        
        const response = await topicApi.getTopics(params)
        if (response && response.code === 200) {
          this.topics = response.data.items || []
        } else {
          throw new Error(response?.message || '获取专题列表失败')
        }
      } catch (error: any) {
        console.error('获取专题列表失败:', error)
        this.setError(error.message || '获取专题列表失败')
        throw error
      } finally {
        this.setLoading(false)
      }
    },

    // 根据ID获取专题详情
    async fetchTopicById(topicId: string) {
      try {
        this.setLoading(true)
        this.setError(null)
        
        const response = await topicApi.getTopicById(topicId)
        if (response && response.code === 200) {
          // 兼容实际后端返回：data 直接为聚合详情对象（非 { topic, categories } 包裹）
          const detail: any = response.data || {}
          this.currentTopic = detail // 直接存放主体信息（包含 id/title/description/banner_url/status/...）
          this.categories = detail.categories || []
        } else {
          throw new Error(response?.message || '获取专题详情失败')
        }
      } catch (error: any) {
        console.error('获取专题详情失败:', error)
        this.setError(error.message || '获取专题详情失败')
        throw error
      } finally {
        this.setLoading(false)
      }
    },

    // 获取专题详情（编辑模式使用）
    async fetchTopicDetail(topicId: string) {
      try {
        this.setLoading(true)
        this.setError(null)
        
        const response = await topicApi.getTopicById(topicId)
        if (response && response.code === 200) {
          // 返回专题基本信息，不包含分类
          const detail: any = response.data || {}
          return {
            id: detail.id,
            title: detail.title,
            description: detail.description,
            banner_url: detail.banner_url,
            status: detail.status,
            created_at: detail.created_at,
            updated_at: detail.updated_at
          }
        } else {
          throw new Error(response?.message || '获取专题详情失败')
        }
      } catch (error: any) {
        console.error('获取专题详情失败:', error)
        this.setError(error.message || '获取专题详情失败')
        throw error
      } finally {
        this.setLoading(false)
      }
    },

    // 创建专题
    async createTopic(topicData: TopicCreate) {
      try {
        this.setLoading(true)
        this.setError(null)
        
        // 仅发送后端允许的字段，避免把 categories 等扩展字段一并提交导致 500
        // 仅提交有值的字段，避免把空字符串写入触发数据库约束
        const payload: Record<string, any> = { title: topicData.title }
        if (topicData.description && topicData.description.trim()) payload.description = topicData.description.trim()
        if (topicData.banner_url && topicData.banner_url.trim()) payload.banner_url = topicData.banner_url.trim()
        if (topicData.status && topicData.status.trim()) payload.status = topicData.status.trim()

        console.debug('[TopicStore] createTopic payload:', payload)

        const response = await topicApi.createTopic(payload as any)
        if (response && response.code === 200) {
          console.debug('[TopicStore] createTopic response:', response)
          this.topics.unshift(response.data)
          return response.data
        } else {
          throw new Error(response?.message || '创建专题失败')
        }
      } catch (error: any) {
        console.error('创建专题失败: ', {
          error,
          message: error?.message,
          stack: error?.stack,
        })
        this.setError(error.message || '创建专题失败')
        throw error
      } finally {
        this.setLoading(false)
      }
    },

    // 更新专题
    async updateTopic(topicId: string, topicData: TopicUpdate) {
      try {
        this.setLoading(true)
        this.setError(null)
        
        const response = await topicApi.updateTopic(topicId, topicData)
        if (response && response.code === 200) {
          const index = this.topics.findIndex((topic: Topic) => topic.id === topicId)
          if (index !== -1) {
            this.topics[index] = response.data
          }
          if (this.currentTopic?.id === topicId) {
            this.currentTopic = response.data
          }
          return response.data
        } else {
          throw new Error(response?.message || '更新专题失败')
        }
      } catch (error: any) {
        console.error('更新专题失败:', error)
        this.setError(error.message || '更新专题失败')
        throw error
      } finally {
        this.setLoading(false)
      }
    },

    // 删除专题
    async deleteTopic(topicId: string) {
      try {
        this.setLoading(true)
        this.setError(null)
        
        const response = await topicApi.deleteTopic(topicId)
        if (response && response.code === 200) {
          this.topics = this.topics.filter((topic: Topic) => topic.id !== topicId)
          if (this.currentTopic?.id === topicId) {
            this.currentTopic = null
            this.categories = []
          }
        } else {
          throw new Error(response?.message || '删除专题失败')
        }
      } catch (error: any) {
        console.error('删除专题失败:', error)
        this.setError(error.message || '删除专题失败')
        throw error
      } finally {
        this.setLoading(false)
      }
    },

    // 获取专题分类列表
    async fetchCategories(topicId: string) {
      try {
        this.setLoading(true)
        this.setError(null)
        
        console.log('[DEBUG] store.fetchCategories 被调用，topicId:', topicId)
        console.log('[DEBUG] store.fetchCategories 准备调用API')
        
        const response = await topicApi.getCategories(topicId)
        console.log('[DEBUG] store.fetchCategories API响应:', response)
        console.log('[DEBUG] store.fetchCategories 响应类型:', typeof response)
        console.log('[DEBUG] store.fetchCategories 响应结构:', {
          hasResponse: !!response,
          code: response?.code,
          data: response?.data,
          message: response?.message
        })
        
        if (response && response.code === 200) {
          this.categories = response.data.items || []
          console.log('✅ [DEBUG] store.fetchCategories 成功，分类数量:', this.categories.length)
          console.log('✅ [DEBUG] store.fetchCategories 返回数据:', this.categories)
          return this.categories // 返回分类列表
        } else {
          console.error('❌ [DEBUG] store.fetchCategories API响应错误:', response)
          throw new Error(response?.message || '获取分类列表失败')
        }
      } catch (error: any) {
        console.error('❌ [DEBUG] store.fetchCategories 失败:', error)
        console.error('❌ [DEBUG] store.fetchCategories 错误详情:', {
          message: error.message,
          stack: error.stack,
          response: error.response
        })
        this.setError(error.message || '获取分类列表失败')
        throw error
      } finally {
        this.setLoading(false)
      }
    },

    // 创建分类
    async createCategory(topicId: string, categoryData: CategoryCreate) {
      try {
        this.setLoading(true)
        this.setError(null)
        
        const response = await topicApi.createCategory(topicId, categoryData)
        if (response && response.code === 200) {
          this.categories.push(response.data)
          return response.data
        } else {
          throw new Error(response?.message || '创建分类失败')
        }
      } catch (error: any) {
        console.error('创建分类失败:', error)
        this.setError(error.message || '创建分类失败')
        throw error
      } finally {
        this.setLoading(false)
      }
    },

    // 更新分类
    async updateCategory(categoryId: string, categoryData: CategoryUpdate) {
      try {
        this.setLoading(true)
        this.setError(null)
        
        const response = await topicApi.updateCategory(categoryId, categoryData)
        if (response && response.code === 200) {
          const index = this.categories.findIndex((category: TopicCategory) => category.id === categoryId)
          if (index !== -1) {
            this.categories[index] = response.data
          }
          return response.data
        } else {
          throw new Error(response?.message || '更新分类失败')
        }
      } catch (error: any) {
        console.error('更新分类失败:', error)
        this.setError(error.message || '更新分类失败')
        throw error
      } finally {
        this.setLoading(false)
      }
    },

    // 删除分类
    async deleteCategory(categoryId: string) {
      try {
        this.setLoading(true)
        this.setError(null)
        
        const response = await topicApi.deleteCategory(categoryId)
        if (response && response.code === 200) {
          this.categories = this.categories.filter((category: TopicCategory) => category.id !== categoryId)
        } else {
          throw new Error(response?.message || '删除分类失败')
        }
      } catch (error: any) {
        console.error('删除分类失败:', error)
        this.setError(error.message || '删除分类失败')
        throw error
      } finally {
        this.setLoading(false)
      }
    },

    // 获取分类下的直播间列表
    async fetchCategoryRooms(categoryId: string) {
      try {
        this.setLoading(true)
        this.setError(null)
        
        const response = await topicApi.getCategoryRooms(categoryId)
        if (response && response.code === 200) {
          // 更新对应分类的直播间列表
          const categoryIndex = this.categories.findIndex((category: TopicCategory) => category.id === categoryId)
          if (categoryIndex !== -1) {
            this.categories[categoryIndex].rooms = response.data.items || []
          }
          return response.data.items || []
        } else {
          throw new Error(response?.message || '获取直播间列表失败')
        }
      } catch (error: any) {
        console.error('获取直播间列表失败:', error)
        this.setError(error.message || '获取直播间列表失败')
        throw error
      } finally {
        this.setLoading(false)
      }
    },

    // 添加直播间到分类
    async addRoomsToCategory(categoryId: string, rooms: RoomAssociation[]) {
      try {
        this.setLoading(true)
        this.setError(null)
        
        const response = await topicApi.addRoomsToCategory(categoryId, { rooms })
        if (response && response.code === 200) {
          // 刷新分类下的直播间列表
          await this.fetchCategoryRooms(categoryId)
        } else {
          throw new Error(response?.message || '添加直播间失败')
        }
      } catch (error: any) {
        console.error('添加直播间失败:', error)
        this.setError(error.message || '添加直播间失败')
        throw error
      } finally {
        this.setLoading(false)
      }
    },

    // 更新直播间排序
    async updateRoomSortOrder(categoryId: string, rooms: RoomAssociation[]) {
      try {
        this.setLoading(true)
        this.setError(null)
        
        const response = await topicApi.updateRoomSortOrder(categoryId, { rooms })
        if (response && response.code === 200) {
          // 刷新分类下的直播间列表
          await this.fetchCategoryRooms(categoryId)
        } else {
          throw new Error(response?.message || '更新排序失败')
        }
      } catch (error: any) {
        console.error('更新排序失败:', error)
        this.setError(error.message || '更新排序失败')
        throw error
      } finally {
        this.setLoading(false)
      }
    },

    // 从分类中移除直播间
    async removeRoomsFromCategory(categoryId: string, roomIds: string[]) {
      try {
        this.setLoading(true)
        this.setError(null)
        
        const response = await topicApi.removeRoomsFromCategory(categoryId, { room_ids: roomIds })
        if (response && response.code === 200) {
          // 刷新分类下的直播间列表
          await this.fetchCategoryRooms(categoryId)
        } else {
          throw new Error(response?.message || '移除直播间失败')
        }
      } catch (error: any) {
        console.error('移除直播间失败:', error)
        this.setError(error.message || '移除直播间失败')
        throw error
      } finally {
        this.setLoading(false)
      }
    },

    // 获取直播间关联的专题列表
    async fetchRoomTopics(roomId: string) {
      try {
        this.setLoading(true)
        this.setError(null)
        
        const response = await topicApi.getRoomTopics(roomId)
        if (response && response.code === 200) {
          return response.data || []
        } else {
          throw new Error(response?.message || '获取专题列表失败')
        }
      } catch (error: any) {
        console.error('获取专题列表失败:', error)
        this.setError(error.message || '获取专题列表失败')
        throw error
      } finally {
        this.setLoading(false)
      }
    },

    // 批量获取直播间状态
    async getBatchRoomStatus(roomIds: string[]) {
      try {
        this.setLoading(true)
        this.setError(null)
        
        const response = await topicApi.getBatchRoomStatus({ room_ids: roomIds })
        if (response && response.code === 200) {
          return response.data || []
        } else {
          throw new Error(response?.message || '获取直播间状态失败')
        }
      } catch (error: any) {
        console.error('获取直播间状态失败:', error)
        this.setError(error.message || '获取直播间状态失败')
        throw error
      } finally {
        this.setLoading(false)
      }
    },

    // 清空当前专题数据
    clearCurrentTopic() {
      this.currentTopic = null
      this.categories = []
    },

    // 重置状态
    reset() {
      this.topics = []
      this.currentTopic = null
      this.categories = []
      this.loading = false
      this.error = null
    }
  }
})
