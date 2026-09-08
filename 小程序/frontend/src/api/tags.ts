/**
 * 标签管理 API
 * 依据：《02-标签管理-后端设计文档》+《02-V2》+《Live-Saas-Wechat-02-标签管理-前端设计文档-v2.0》
 *
 * 端点：
 *   Tags CRUD: GET列表, GET详情, POST创建, PATCH更新, DELETE删除
 *   【新增】POST /content/tags/resolve（用户侧解析或创建；禁止用 admin CREATE 代替）
 *   Session Tags: GET场次标签, POST设置场次标签, DELETE移除场次标签（房主或 Admin）
 *   搜索: GET按标签搜索场次
 */

import { request } from '@/utils/request'
import { API_PATHS } from '@/config/api'
import type { ApiResponse } from '@/types/common'
import type {
  Tag,
  TagCreate,
  TagUpdate,
  TagListParams,
  TagResolveRequest,
  TagResolveData,
  SessionTagsSetRequest,
  SessionTagItem,
  TagSearchParams,
  SearchResultItem
} from '@/types/tags'

// ============ Tags CRUD（公开+管理员） ============

/**
 * 获取标签列表（公开读；include_inactive=true 时须带 Admin JWT）
 * GET /api/v1/content/tags
 * Query（02 / v6）：q?, search_type?, include_inactive?
 * 说明：契约无 GET /admin/tags；写操作用 CREATE/UPDATE/DELETE。
 * include_inactive 仅 Admin（v6 §4.1.1）；须允许带 Token，禁止 auth:false。
 * data 可能为 { items } / { total, page, size, items } / TagItem[]
 */
export const getTags = (params?: TagListParams): Promise<ApiResponse<{ items: Tag[] } | Tag[]>> => {
  return request.get(API_PATHS.TAGS.LIST, {
    data: params,
    showError: false
  })
}

/**
 * 获取单个标签详情（公开）
 * GET /api/v1/content/tags/{tagId}
 */
export const getTag = (tagId: string): Promise<ApiResponse<Tag>> => {
  return request.get(API_PATHS.TAGS.DETAIL(tagId), { showError: false })
}

/**
 * 创建标签（管理员）
 * POST /api/v1/admin/tags
 * 说明：开播自建须走 resolveTag，禁止普通用户调本接口。
 */
export const createTag = (data: TagCreate): Promise<ApiResponse<Tag>> => {
  return request.post(API_PATHS.TAGS.CREATE, data, {
    loading: true,
    loadingText: '创建中...'
  })
}

/**
 * 解析或创建标签（用户侧；《02-V2》§3.4）
 * POST /api/v1/content/tags/resolve
 * Body: { name }；成功 data: { id, name, created, source? }
 */
export const resolveTag = (
  data: TagResolveRequest
): Promise<ApiResponse<TagResolveData>> => {
  return request.post(API_PATHS.TAGS.RESOLVE, data, {
    loading: true,
    loadingText: '处理中...',
    showError: false // 由页面接内容安全人话
  })
}

/**
 * 更新标签（管理员）
 * PATCH /api/v1/admin/tags/{tagId}
 */
export const updateTag = (tagId: string, data: TagUpdate): Promise<ApiResponse<Tag>> => {
  return request.patch(API_PATHS.TAGS.UPDATE(tagId), data, {
    loading: true,
    loadingText: '保存中...'
  })
}

/**
 * 删除标签（管理员，软删除）
 * DELETE /api/v1/admin/tags/{tagId}
 */
export const deleteTag = (tagId: string): Promise<ApiResponse<null>> => {
  return request.delete(API_PATHS.TAGS.DELETE(tagId), {
    loading: true,
    loadingText: '删除中...'
  })
}

// ============ Session Tags（场次-标签关联） ============

/**
 * 获取场次的标签列表（公开）
 * GET /api/v1/content/sessions/{sessionId}/tags
 */
export const getSessionTags = (sessionId: string): Promise<ApiResponse<{ items: SessionTagItem[] }>> => {
  return request.get(API_PATHS.SESSION.TAGS(sessionId), { showError: false })
}

/**
 * 设置场次标签关联（房主或 Admin；replace 幂等）
 * POST /api/v1/content/sessions/{sessionId}/tags
 * Body: tag_ids 0～5；mode 开播主路径固定 replace；[] + replace = 清空
 */
export const setSessionTags = (
  sessionId: string,
  data: SessionTagsSetRequest
): Promise<ApiResponse<{ session_id: string; tags: Array<{ tag_id: string; tag_name: string; tag_slug: string }> }>> => {
  return request.post(API_PATHS.SESSION.TAGS(sessionId), data, {
    loading: true,
    loadingText: '保存中...'
  })
}

/**
 * 移除场次标签关联（房主或 Admin；《02-V2》§3.2）
 * DELETE /api/v1/content/sessions/{sessionId}/tags/{tagId}
 */
export const removeSessionTag = (sessionId: string, tagId: string): Promise<ApiResponse<null>> => {
  return request.delete(`${API_PATHS.SESSION.TAGS(sessionId)}/${tagId}`, {
    loading: true,
    loadingText: '移除中...'
  })
}

// ============ 搜索（按标签搜索场次） ============

/**
 * 按标签搜索场次（公开）
 * GET /api/v1/content/tags/search/sessions
 */
export const searchSessionsByTag = (
  params: TagSearchParams
): Promise<ApiResponse<{ total: number; page: number; size: number; items: SearchResultItem[] }>> => {
  return request.get(API_PATHS.TAGS.SEARCH_SESSIONS, {
    data: {
      tag_ids: params.tag_ids,
      match_all: params.match_all ?? false,
      page: params.page || 1,
      page_size: params.page_size || 20
    },
    showError: false
  })
}

export default {
  getTags,
  getTag,
  createTag,
  updateTag,
  deleteTag,
  getSessionTags,
  setSessionTags,
  removeSessionTag,
  searchSessionsByTag
}
