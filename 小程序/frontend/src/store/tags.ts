/**
 * 标签状态管理
 * 以后端设计文档为准：tags 表仅有 id, name, slug, description, is_active, created_at, updated_at
 * 零偏差：删除所有后端不存在的字段引用（status, category, usageCount, color, type 等）
 */

import { defineStore } from 'pinia'
import type { Tag, TagCreate, TagUpdate, TagListParams } from '@/types/tags'
import {
  getTags,
  getTag,
  createTag,
  updateTag,
  deleteTag
} from '@/api/tags'

interface TagsState {
  /** 标签列表 */
  tagList: Tag[]
  /** 当前标签详情 */
  currentTag: Tag | null
  /** 加载状态 */
  loading: boolean
  /** 错误状态 */
  error: Error | null
  /** 筛选条件 */
  filters: TagListParams
}

export const useTagsStore = defineStore('tags', {
  state: (): TagsState => ({
    tagList: [],
    currentTag: null,
    loading: false,
    error: null,
    filters: {}
  }),

  getters: {
    /**
     * 活跃标签（is_active=true）
     */
    activeTags: (state) => state.tagList.filter(tag => tag.is_active),

    /**
     * 标签总数
     */
    totalCount: (state) => state.tagList.length
  },

  actions: {
    /**
     * 获取标签列表
     */
    async fetchTagList(params?: TagListParams): Promise<void> {
      this.loading = true
      this.error = null

      try {
        const query = { ...this.filters, ...params }
        const response = await getTags(query)

        if (response.code === 200) {
          // 兼容后端返回格式：可能是 { items: [...] } 或直接是 [...]
          const data = response.data
          this.tagList = Array.isArray(data) ? data : (Array.isArray(data?.items) ? data.items : [])
          this.filters = query
        } else {
          throw new Error(response.message || '获取标签列表失败')
        }
      } catch (error) {
        this.error = error as Error
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * 获取单个标签详情
     */
    async fetchTagDetail(tagId: string): Promise<void> {
      this.loading = true
      this.error = null

      try {
        const response = await getTag(tagId)

        if (response.code === 200) {
          this.currentTag = response.data
        } else {
          throw new Error(response.message || '获取标签详情失败')
        }
      } catch (error) {
        this.error = error as Error
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * 创建标签（Admin功能）
     */
    async createTag(tagData: TagCreate): Promise<string> {
      this.loading = true
      this.error = null

      try {
        const response = await createTag(tagData)

        if (response.code === 200) {
          await this.fetchTagList()
          return response.data?.id || ''
        } else {
          throw new Error(response.message || '创建标签失败')
        }
      } catch (error) {
        this.error = error as Error
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * 更新标签（Admin功能）
     */
    async updateTag(tagId: string, updateData: TagUpdate): Promise<void> {
      this.loading = true
      this.error = null

      try {
        const response = await updateTag(tagId, updateData)

        if (response.code === 200) {
          const index = this.tagList.findIndex(tag => tag.id === tagId)
          if (index !== -1 && response.data) {
            this.tagList[index] = response.data
          }
          if (this.currentTag?.id === tagId && response.data) {
            this.currentTag = response.data
          }
        } else {
          throw new Error(response.message || '更新标签失败')
        }
      } catch (error) {
        this.error = error as Error
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * 删除标签（Admin功能，软删除）
     */
    async deleteTag(tagId: string): Promise<void> {
      this.loading = true
      this.error = null

      try {
        const response = await deleteTag(tagId)

        if (response.code === 200) {
          this.tagList = this.tagList.filter(tag => tag.id !== tagId)
          if (this.currentTag?.id === tagId) {
            this.currentTag = null
          }
        } else {
          throw new Error(response.message || '删除标签失败')
        }
      } catch (error) {
        this.error = error as Error
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * 设置筛选条件
     */
    setFilters(filters: TagListParams): void {
      this.filters = { ...this.filters, ...filters }
    },

    /**
     * 清除筛选条件
     */
    clearFilters(): void {
      this.filters = {}
    },

    /**
     * 清除标签数据
     */
    clearTagsData(): void {
      this.tagList = []
      this.currentTag = null
      this.error = null
      this.filters = {}
    }
  }
})
