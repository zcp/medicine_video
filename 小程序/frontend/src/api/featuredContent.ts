/**
 * 首页焦点图管理 API
 * 以后端设计文档为准：《03-首页焦点图管理-后端设计文档.md》
 *
 * 端点清单（7个）:
 *   GET /featured-content              公开列表（最多10条，is_active=true）
 *   GET /admin/featured-content         管理端分页列表（JWT+Admin）
 *   GET /admin/featured-content/{id}    管理端详情（JWT+Admin）
 *   POST /admin/featured-content        创建（JWT+Admin）
 *   PATCH /admin/featured-content/{id}  部分更新（JWT+Admin）
 *   DELETE /admin/featured-content/{id} 软删除（JWT+Admin）
 *   POST /admin/featured-content/{id}/image  上传图片（JWT+Admin）
 */

import { request } from '@/utils/request'
import { API_PATHS } from '@/config/api'
import type { ApiResponse } from '@/types/common'
import type {
  FeaturedContent,
  FeaturedContentCreate,
  FeaturedContentUpdate
} from '@/types/featuredContent'

// ============ 公开接口 ============

/**
 * 获取首页焦点图列表（公开，最多10条active数据）
 * GET /api/v1/featured-content
 */
export const getFeaturedContent = (params?: {
  limit?: number
}): Promise<ApiResponse<{ items: FeaturedContent[] }>> => {
  return request.get(API_PATHS.CONTENT.FEATURED_CONTENT, { data: params, auth: false })
}

// ============ 管理端接口 ============

/**
 * 管理端焦点图分页列表（含已禁用）
 * GET /api/v1/admin/featured-content
 */
export const getAdminFeaturedContent = (params?: {
  page?: number
  size?: number
  page_size?: number
  q?: string
  search_type?: string
  /** 过滤启用状态；省略则返回全部 */
  is_active?: boolean
}): Promise<ApiResponse<{ total: number; page: number; size: number; items: FeaturedContent[] }>> => {
  const { page_size, ...rest } = params || {}
  const queryParams = {
    ...rest,
    size: rest.size ?? page_size
  }
  return request.get(API_PATHS.ADMIN.FEATURED_CONTENT, { data: queryParams })
}

/**
 * 获取单个焦点图详情
 * GET /api/v1/admin/featured-content/{contentId}
 */
export const getFeaturedContentDetail = (contentId: string): Promise<ApiResponse<FeaturedContent>> => {
  return request.get(API_PATHS.ADMIN.UPDATE_FEATURED(contentId))
}

/**
 * 创建焦点图
 * POST /api/v1/admin/featured-content
 */
export const createFeaturedContent = (data: FeaturedContentCreate): Promise<ApiResponse<FeaturedContent>> => {
  return request.post(API_PATHS.ADMIN.CREATE_FEATURED, data, {
    loading: true,
    loadingText: '创建中...'
  })
}

/**
 * 更新焦点图（部分更新）
 * PATCH /api/v1/admin/featured-content/{contentId}
 */
export const updateFeaturedContent = (
  contentId: string,
  data: FeaturedContentUpdate
): Promise<ApiResponse<FeaturedContent>> => {
  return request.patch(API_PATHS.ADMIN.UPDATE_FEATURED(contentId), data, {
    loading: true,
    loadingText: '更新中...'
  })
}

/**
 * 删除焦点图（软删除）
 * DELETE /api/v1/admin/featured-content/{contentId}
 */
export const deleteFeaturedContent = (contentId: string): Promise<ApiResponse<null>> => {
  return request.delete(API_PATHS.ADMIN.DELETE_FEATURED(contentId), {
    loading: true,
    loadingText: '删除中...'
  })
}

/**
 * 上传焦点图图片
 * POST /api/v1/admin/featured-content/{contentId}/image
 *
 * 注意：小程序环境使用 uni.uploadFile，不支持 FormData
 * 后端期望字段名为 image
 */
export const uploadFeaturedContentImage = (
  contentId: string,
  filePath: string
): Promise<ApiResponse<{ image_url: string }>> => {
  return request.upload({
    url: API_PATHS.ADMIN.UPLOAD_FEATURED_IMAGE(contentId),
    filePath,
    name: 'image',
    loading: true,
    loadingText: '上传中...'
  })
}

export default {
  getFeaturedContent,
  getAdminFeaturedContent,
  getFeaturedContentDetail,
  createFeaturedContent,
  updateFeaturedContent,
  deleteFeaturedContent,
  uploadFeaturedContentImage
}
