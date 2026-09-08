/**
 * 科室分类管理 API 封装
 * 严格遵循《01-科室分类管理-前端实现.md》文档规范
 */

import { request } from '@/utils/request'
import { API_PATHS } from '@/config/api'
import { logger } from '@/logs/logger'
import type {
  Category,
  CategoryCreate,
  CategoryUpdate,
  CategoryPageResult,
  CategoryDeleteOptions,
  CategoryMigrateScope,
  CategoryMigrateStats,
  CategoryMergeResult,
  LiveRoomCategoriesSetRequest
} from '@/types/category'

function summarizeCategory(category: Partial<Category> | null | undefined) {
  if (!category) return null
  return {
    id: category.id,
    name: category.name,
    slug: category.slug,
    is_active: category.is_active,
    sort_order: category.sort_order,
    icon: category.icon
  }
}

function summarizeCategoryList(items: Category[] | undefined | null) {
  return {
    count: Array.isArray(items) ? items.length : 0,
    sample: Array.isArray(items)
      ? items.slice(0, 5).map(item => summarizeCategory(item))
      : []
  }
}

function summarizeError(error: any) {
  return {
    message: error?.message || String(error),
    status: error?.status || error?.statusCode || error?.code,
    url: error?.url
  }
}

/**
 * 从 request 统一响应中取出列表：
 * - ApiResponse: { code, data }
 * - data 可能是数组，或 { items: [] }
 */
function unwrapCategoryList(payload: any): any[] {
  const raw = payload?.data !== undefined ? payload.data : payload
  if (Array.isArray(raw)) return raw
  if (Array.isArray(raw?.items)) return raw.items
  if (Array.isArray(raw?.data)) return raw.data
  return []
}

/** 房间关联项可能是 Category，也可能是 { category_id, category_name, ... } */
function normalizeCategoryRow(row: any): Category | null {
  if (!row || typeof row !== 'object') return null
  const id = String(row.id || row.category_id || '').trim()
  if (!id) return null
  return {
    id,
    name: String(row.name || row.category_name || ''),
    slug: String(row.slug || row.category_slug || ''),
    icon: row.icon,
    description: row.description,
    sort_order: Number(row.sort_order ?? 0),
    is_active: row.is_active !== false,
    parent_id: row.parent_id ?? null,
    is_primary: row.is_primary === true,
    created_at: String(row.created_at || ''),
    updated_at: String(row.updated_at || '')
  }
}

function logCategoryRequest(action: string, payload?: any) {
  logger.info('network', `[category] ${action}`, payload)
}

function logCategoryResponse(action: string, payload?: any) {
  logger.info('network', `[category] ${action} 成功`, payload)
}

function logCategoryError(action: string, error: any, payload?: any) {
  logger.error('network', `[category] ${action} 失败`, {
    error: summarizeError(error),
    payload
  })
}

// ============ 公开接口 ============

/**
 * 获取所有分类（用户端，按 sort_order 排序，仅 is_active=true）
 * 使用 async function，避免小程序对「箭头+IIFE」命名导出互操作异常
 */
export async function getAllCategories(): Promise<Category[]> {
  const action = '获取全部分类'
  const payload = { url: API_PATHS.CATEGORY.LIST, auth: false }
  logCategoryRequest(action, payload)
  try {
    const response = await request.get(API_PATHS.CATEGORY.LIST, { auth: false })
    const list = unwrapCategoryList(response)
      .map(normalizeCategoryRow)
      .filter((c): c is Category => !!c)
    logCategoryResponse(action, summarizeCategoryList(list))
    return list
  } catch (error) {
    logCategoryError(action, error, payload)
    throw error
  }
}

/**
 * 获取分类列表（兼容旧接口）
 * @param limit 限制返回数量（可选）
 */
export async function getCategoryList(limit?: number): Promise<Category[]> {
  const action = '获取分类列表（旧接口）'
  const payload = { url: API_PATHS.CATEGORY.LIST, limit, auth: false }
  logCategoryRequest(action, payload)
  try {
    const response = await request.get(API_PATHS.CATEGORY.LIST, {
      data: limit ? { limit } : undefined,
      auth: false
    })
    const list = unwrapCategoryList(response)
      .map(normalizeCategoryRow)
      .filter((c): c is Category => !!c)
    logCategoryResponse(action, summarizeCategoryList(list))
    return list
  } catch (error) {
    logCategoryError(action, error, payload)
    throw error
  }
}

/**
 * 获取单个分类详情
 */
export async function getCategory(categoryId: string): Promise<Category> {
  const action = '获取分类详情'
  const url = API_PATHS.CONTENT.CATEGORY_DETAIL(categoryId)
  const payload = { url, categoryId, auth: false }
  logCategoryRequest(action, payload)
  try {
    const response = await request.get(url, { auth: false })
    const raw = (response as any)?.data ?? response
    const category = normalizeCategoryRow(raw)
    if (!category) throw new Error('分类不存在')
    logCategoryResponse(action, summarizeCategory(category))
    return category
  } catch (error) {
    logCategoryError(action, error, payload)
    throw error
  }
}

/**
 * 获取直播间关联的分类
 * GET /api/v1/rooms/{roomId}/categories（公开）
 * 兼容 items 为 Category 或 { category_id, category_name } 两种形态
 */
export async function getRoomCategories(roomId: string): Promise<Category[]> {
  const action = '获取直播间关联分类'
  const url = API_PATHS.CATEGORY.ROOM_CATEGORIES(roomId)
  const payload = { url, roomId, auth: false }
  logCategoryRequest(action, payload)
  try {
    const response = await request.get(url, { auth: false })
    const list = unwrapCategoryList(response)
      .map(normalizeCategoryRow)
      .filter((c): c is Category => !!c)
    logCategoryResponse(action, summarizeCategoryList(list))
    return list
  } catch (error) {
    logCategoryError(action, error, payload)
    throw error
  }
}

// ============ 管理端接口 ============

/**
 * 管理端分类列表（分页+搜索）
 * include_inactive=true 确保管理端能看到所有分类（含禁用）
 */
export const getAdminCategories = (params: {
  page?: number
  page_size?: number
  q?: string
  include_inactive?: boolean
}): Promise<CategoryPageResult> =>
  (() => {
    const action = '获取管理端分类列表'
    // 🚨 过滤掉 undefined/null/空字符串 值，避免序列化为 "undefined" 字符串
    const cleanParams = Object.fromEntries(
      Object.entries(params).filter(([_, v]) => v !== undefined && v !== null && v !== '')
    )
    const { page_size, ...rest } = cleanParams
    const queryParams = {
      ...rest,
      include_inactive: params.include_inactive ?? true,
      size: rest.size ?? page_size
    }
    const payload = { url: API_PATHS.CATEGORY.ADMIN_LIST, params: queryParams }
    logCategoryRequest(action, payload)
    return request.get(API_PATHS.CATEGORY.ADMIN_LIST, { data: queryParams })
      .then((response) => {
        // request.get 返回 normalizeApiResponse 包装，需解包 .data
        const raw = response?.data ?? response
        // 兼容多种后端返回格式：
        // 1. { items: [...], total: N }  — 标准分页
        // 2. [...]                       — 直接数组
        // 3. { data: { items, total } }  — 双层包装
        const data = Array.isArray(raw)
          ? { items: raw, total: raw.length }
          : (raw?.items !== undefined ? raw
            : (raw?.data ? (Array.isArray(raw.data) ? { items: raw.data, total: raw.data.length } : raw.data)
              : { items: [], total: 0 }))
        logCategoryResponse(action, {
          total: data?.total,
          page: data?.page,
          page_size: data?.page_size,
          items: summarizeCategoryList(data?.items)
        })
        return data
      })
      .catch((error) => {
        logCategoryError(action, error, payload)
        throw error
      })
  })()

/**
 * 获取管理端分类详情
 */
export const getAdminCategoryDetail = (id: string): Promise<Category> =>
  (() => {
    const action = '获取管理端分类详情'
    const url = API_PATHS.CATEGORY.ADMIN_DETAIL(id)
    const payload = { url, id }
    logCategoryRequest(action, payload)
    return request.get(url)
      .then((data) => {
        logCategoryResponse(action, summarizeCategory(data))
        return data
      })
      .catch((error) => {
        logCategoryError(action, error, payload)
        throw error
      })
  })()

/**
 * 创建分类
 */
export const createCategory = (data: CategoryCreate): Promise<Category> =>
  (() => {
    const action = '创建分类'
    const payload = { url: API_PATHS.CATEGORY.ADMIN_LIST, data }
    logCategoryRequest(action, payload)
    return request.post(API_PATHS.CATEGORY.ADMIN_LIST, data, { loading: true, loadingText: '创建中...' })
      .then((result) => {
        logCategoryResponse(action, summarizeCategory(result))
        return result
      })
      .catch((error) => {
        logCategoryError(action, error, payload)
        throw error
      })
  })()

/**
 * 更新分类
 */
export const updateCategory = (categoryId: string, data: CategoryUpdate): Promise<Category> =>
  (() => {
    const action = '更新分类'
    const url = API_PATHS.CATEGORY.ADMIN_DETAIL(categoryId)
    const payload = { url, categoryId, data }
    logCategoryRequest(action, payload)
    return request.patch(url, data, { loading: true, loadingText: '更新中...' })
      .then((result) => {
        logCategoryResponse(action, summarizeCategory(result))
        return result
      })
      .catch((error) => {
        logCategoryError(action, error, payload)
        throw error
      })
  })()

/**
 * 删除 / 级联停用分类
 * Query：force、target_category_id（对齐 main；非 force 遇引用 → 409）
 */
export const deleteCategory = (
  categoryId: string,
  options: CategoryDeleteOptions = {},
  requestOpts?: { showError?: boolean; loading?: boolean; loadingText?: string }
): Promise<void> =>
  (() => {
    const action = options.force ? '级联停用分类' : '删除分类'
    const query: string[] = []
    if (options.force !== undefined) query.push(`force=${options.force}`)
    if (options.target_category_id) {
      query.push(`target_category_id=${encodeURIComponent(options.target_category_id)}`)
    }
    const base = API_PATHS.CATEGORY.ADMIN_DETAIL(categoryId)
    const url = query.length ? `${base}?${query.join('&')}` : base
    const payload = { url, categoryId, options }
    logCategoryRequest(action, payload)
    return request
      .delete(url, {
        loading: requestOpts?.loading !== false,
        loadingText: requestOpts?.loadingText || (options.force ? '级联停用中...' : '删除中...'),
        showError: requestOpts?.showError
      })
      .then((result) => {
        logCategoryResponse(action, { categoryId, result })
        return result
      })
      .catch((error) => {
        logCategoryError(action, error, payload)
        throw error
      })
  })()

/**
 * 迁移分类引用
 * POST /admin/categories/{id}/migrate
 */
export async function migrateCategoryReferences(
  categoryId: string,
  data: { target_category_id: string; scope: CategoryMigrateScope }
): Promise<{ migrated: CategoryMigrateStats }> {
  const action = '迁移分类引用'
  const url = API_PATHS.CATEGORY.ADMIN_MIGRATE(categoryId)
  const payload = { url, categoryId, data }
  logCategoryRequest(action, payload)
  try {
    const result: any = await request.post(url, data, {
      loading: true,
      loadingText: '迁移中...'
    })
    const raw = result?.data !== undefined ? result.data : result
    const migrated = (raw?.migrated || raw) as CategoryMigrateStats
    logCategoryResponse(action, { categoryId, migrated })
    return { migrated }
  } catch (error) {
    logCategoryError(action, error, payload)
    throw error
  }
}

/**
 * 合并分类（支持 dry_run 预览）
 * POST /admin/categories/merge
 */
export async function mergeCategories(data: {
  source_id: string
  target_id: string
  attach_children?: boolean
  dry_run?: boolean
}): Promise<CategoryMergeResult> {
  const action = data.dry_run ? '合并分类预览' : '合并分类'
  const url = API_PATHS.CATEGORY.ADMIN_MERGE
  const payload = { url, data }
  logCategoryRequest(action, payload)
  try {
    const result: any = await request.post(url, data, {
      loading: true,
      loadingText: data.dry_run ? '预览中...' : '合并中...'
    })
    const raw = result?.data !== undefined ? result.data : result
    const body = (raw?.data && typeof raw.data === 'object' ? raw.data : raw) as CategoryMergeResult
    logCategoryResponse(action, body)
    return {
      dry_run: body?.dry_run !== undefined ? Boolean(body.dry_run) : Boolean(data.dry_run),
      expert_count: Number(body?.expert_count ?? 0),
      department_count: Number(body?.department_count ?? 0),
      room_count: Number(body?.room_count ?? 0),
      child_count: Number(body?.child_count ?? 0),
      inconsistent_expert_count: Number(body?.inconsistent_expert_count ?? 0),
      message: String(body?.message || '')
    }
  } catch (error) {
    logCategoryError(action, error, payload)
    throw error
  }
}

/**
 * 上传分类图标
 * 注意：小程序环境使用 uni.uploadFile，不支持 FormData
 */
export const uploadCategoryIcon = (categoryId: string, filePath: string): Promise<{ icon_url: string }> => {
  const action = '上传分类图标'
  const url = API_PATHS.CATEGORY.ICON(categoryId)
  const payload = { url, categoryId, filePath }
  logCategoryRequest(action, payload)
  return request.upload({
    url,
    filePath,
    name: 'file',
    loading: true,
    loadingText: '上传中...'
  })
    .then((result) => {
      logCategoryResponse(action, { categoryId, icon_url: result?.icon_url })
      return result
    })
    .catch((error) => {
      logCategoryError(action, error, payload)
      throw error
    })
}

/**
 * 删除分类图标
 */
export const deleteCategoryIcon = (categoryId: string): Promise<void> =>
  (() => {
    const action = '删除分类图标'
    const url = API_PATHS.CATEGORY.ICON(categoryId)
    const payload = { url, categoryId }
    logCategoryRequest(action, payload)
    return request.delete(url, { loading: true, loadingText: '删除中...' })
      .then((result) => {
        logCategoryResponse(action, { categoryId, result })
        return result
      })
      .catch((error) => {
        logCategoryError(action, error, payload)
        throw error
      })
  })()

/**
 * 设置直播间分类关联
 * POST /api/v1/admin/rooms/{roomId}/categories（管理员）
 */
export async function setRoomCategories(
  roomId: string,
  data: LiveRoomCategoriesSetRequest
): Promise<void> {
  const action = '设置直播间分类关联'
  const url = API_PATHS.CATEGORY.ADMIN_SET_ROOM_CATEGORIES(roomId)
  const payload = { url, roomId, data }
  logCategoryRequest(action, payload)
  try {
    const result = await request.post(url, data, { loading: true, loadingText: '更新中...' })
    logCategoryResponse(action, {
      roomId,
      category_ids: data?.category_ids,
      mode: data?.mode,
      primary_category_id: data?.primary_category_id,
      result
    })
  } catch (error) {
    logCategoryError(action, error, payload)
    throw error
  }
}

/**
 * 解除直播间分类关联
 * DELETE /api/v1/admin/rooms/{roomId}/categories/{categoryId}（管理员）
 */
export async function removeRoomCategory(roomId: string, categoryId: string): Promise<void> {
  const action = '解除直播间分类关联'
  const url = API_PATHS.CATEGORY.ADMIN_REMOVE_ROOM_CATEGORY(roomId, categoryId)
  const payload = { url, roomId, categoryId }
  logCategoryRequest(action, payload)
  try {
    const result = await request.delete(url, { loading: true, loadingText: '解除中...' })
    logCategoryResponse(action, { roomId, categoryId, result })
  } catch (error) {
    logCategoryError(action, error, payload)
    throw error
  }
}

export default {
  getAllCategories,
  getCategory,
  getCategoryList,
  getRoomCategories,
  getAdminCategories,
  getAdminCategoryDetail,
  createCategory,
  updateCategory,
  deleteCategory,
  migrateCategoryReferences,
  mergeCategories,
  uploadCategoryIcon,
  deleteCategoryIcon,
  setRoomCategories,
  removeRoomCategory
}
