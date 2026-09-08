/**
 * 专家科室受控词表 Admin API（《20》九端点）
 * baseType: core；路径 /admin/expert-departments*
 */

import { request } from '@/utils/request'
import { API_PATHS } from '@/config/api'
import { logger } from '@/logs/logger'
import type {
  BatchVerifyRequest,
  ExpertDepartmentCreate,
  ExpertDepartmentItem,
  ExpertDepartmentListQuery,
  ExpertDepartmentPageResult,
  ExpertDepartmentUpdate,
  MergeDepartmentsRequest,
  UnmappedExpertItem
} from '@/types/expertDepartment'

function summarizeError(error: any) {
  return {
    message: error?.message || String(error),
    status: error?.status || error?.statusCode || error?.code,
    url: error?.url
  }
}

function cleanQuery(params: Record<string, any> = {}) {
  return Object.fromEntries(
    Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== '')
  )
}

function unwrapPage(payload: any): ExpertDepartmentPageResult {
  const raw = payload?.data !== undefined ? payload.data : payload
  if (Array.isArray(raw)) {
    return { items: raw, total: raw.length, page: 1, size: raw.length }
  }
  const data = raw?.items !== undefined ? raw : raw?.data
  const items = Array.isArray(data?.items) ? data.items : Array.isArray(data) ? data : []
  return {
    items,
    total: Number(data?.total ?? items.length) || 0,
    page: Number(data?.page ?? 1) || 1,
    size: Number(data?.size ?? items.length) || items.length
  }
}

function unwrapItem(payload: any): ExpertDepartmentItem {
  const raw = payload?.data !== undefined ? payload.data : payload
  return (raw?.data && typeof raw.data === 'object' && !Array.isArray(raw.data) ? raw.data : raw) as ExpertDepartmentItem
}

function logReq(action: string, payload?: any) {
  logger.info('network', `[expert-department] ${action}`, payload)
}

function logOk(action: string, payload?: any) {
  logger.info('network', `[expert-department] ${action} 成功`, payload)
}

function logFail(action: string, error: any, payload?: any) {
  logger.error('network', `[expert-department] ${action} 失败`, {
    error: summarizeError(error),
    payload
  })
}

/** 1. GET 列表 */
export async function listExpertDepartments(
  params: ExpertDepartmentListQuery = {}
): Promise<ExpertDepartmentPageResult> {
  const action = '词表列表'
  const query = cleanQuery({
    page: params.page ?? 1,
    size: params.size ?? 20,
    is_active: params.is_active,
    is_verified: params.is_verified,
    category_id: params.category_id,
    q: params.q
  })
  const payload = { url: API_PATHS.EXPERT_DEPARTMENT.ADMIN_LIST, params: query }
  logReq(action, payload)
  try {
    const res = await request.get(API_PATHS.EXPERT_DEPARTMENT.ADMIN_LIST, { data: query })
    if (res?.code === 3003) {
      throw Object.assign(new Error(res?.message || '无管理权限'), { code: 3003 })
    }
    const page = unwrapPage(res)
    logOk(action, { total: page.total, page: page.page, size: page.size, count: page.items.length })
    return page
  } catch (error) {
    logFail(action, error, payload)
    throw error
  }
}

/** 2. POST 创建 */
export async function createExpertDepartment(
  data: ExpertDepartmentCreate
): Promise<ExpertDepartmentItem> {
  const action = '创建词条'
  const payload = { url: API_PATHS.EXPERT_DEPARTMENT.ADMIN_CREATE, data }
  logReq(action, payload)
  try {
    const res = await request.post(API_PATHS.EXPERT_DEPARTMENT.ADMIN_CREATE, data, {
      loading: true,
      loadingText: '创建中...'
    })
    if (res?.code === 3003) {
      throw Object.assign(new Error(res?.message || '无管理权限'), { code: 3003 })
    }
    const item = unwrapItem(res)
    logOk(action, { id: item?.id, name: item?.name })
    return item
  } catch (error) {
    logFail(action, error, payload)
    throw error
  }
}

/** 9. GET 详情 */
export async function getExpertDepartmentDetail(id: string): Promise<ExpertDepartmentItem> {
  const action = '词条详情'
  const url = API_PATHS.EXPERT_DEPARTMENT.ADMIN_DETAIL(id)
  const payload = { url, id }
  logReq(action, payload)
  try {
    const res = await request.get(url)
    if (res?.code === 3003) {
      throw Object.assign(new Error(res?.message || '无管理权限'), { code: 3003 })
    }
    const item = unwrapItem(res)
    logOk(action, { id: item?.id, name: item?.name, expert_count: item?.expert_count })
    return item
  } catch (error) {
    logFail(action, error, payload)
    throw error
  }
}

/** 3. PATCH 编辑 */
export async function updateExpertDepartment(
  id: string,
  data: ExpertDepartmentUpdate
): Promise<ExpertDepartmentItem> {
  const action = '更新词条'
  const url = API_PATHS.EXPERT_DEPARTMENT.ADMIN_UPDATE(id)
  const payload = { url, id, data }
  logReq(action, payload)
  try {
    const res = await request.patch(url, data, { loading: true, loadingText: '更新中...' })
    if (res?.code === 3003) {
      throw Object.assign(new Error(res?.message || '无管理权限'), { code: 3003 })
    }
    const item = unwrapItem(res)
    logOk(action, { id: item?.id, name: item?.name })
    return item
  } catch (error) {
    logFail(action, error, payload)
    throw error
  }
}

/** 4. DELETE 删除词条（默认软删；hardDelete=true 时物理删除） */
export async function deleteExpertDepartment(
  id: string,
  options?: { hardDelete?: boolean }
): Promise<void> {
  const hardDelete = options?.hardDelete ?? false
  const action = hardDelete ? '删除词条' : '停用词条'
  const url = hardDelete
    ? `${API_PATHS.EXPERT_DEPARTMENT.ADMIN_DELETE(id)}?hard_delete=true`
    : API_PATHS.EXPERT_DEPARTMENT.ADMIN_DELETE(id)
  const payload = { url, id, hardDelete }
  logReq(action, payload)
  try {
    const res = await request.delete(url, {
      loading: true,
      loadingText: hardDelete ? '删除中...' : '停用中...'
    })
    if (res?.code === 3003) {
      throw Object.assign(new Error(res?.message || '无管理权限'), { code: 3003 })
    }
    logOk(action, { id, result: res })
  } catch (error) {
    logFail(action, error, payload)
    throw error
  }
}

/** 5. GET 未映射专家 */
export async function listUnmappedExperts(params?: {
  page?: number
  size?: number
}): Promise<{ items: UnmappedExpertItem[]; total: number; page: number; size: number }> {
  const action = '未映射专家'
  const query = cleanQuery({
    page: params?.page ?? 1,
    size: params?.size ?? 20
  })
  const payload = { url: API_PATHS.EXPERT_DEPARTMENT.ADMIN_UNMAPPED, params: query }
  logReq(action, payload)
  try {
    const res = await request.get(API_PATHS.EXPERT_DEPARTMENT.ADMIN_UNMAPPED, { data: query })
    if (res?.code === 3003) {
      throw Object.assign(new Error(res?.message || '无管理权限'), { code: 3003 })
    }
    const page = unwrapPage(res)
    logOk(action, { total: page.total, count: page.items.length })
    return {
      items: page.items as unknown as UnmappedExpertItem[],
      total: page.total,
      page: page.page,
      size: page.size
    }
  } catch (error) {
    logFail(action, error, payload)
    throw error
  }
}

/** 6. POST 合并 */
export async function mergeExpertDepartments(
  data: MergeDepartmentsRequest
): Promise<{ transferred_experts?: number; target?: ExpertDepartmentItem; [key: string]: any }> {
  const action = '合并科室'
  const payload = { url: API_PATHS.EXPERT_DEPARTMENT.ADMIN_MERGE, data }
  logReq(action, payload)
  try {
    const res = await request.post(API_PATHS.EXPERT_DEPARTMENT.ADMIN_MERGE, data, {
      loading: true,
      loadingText: '合并中...'
    })
    if (res?.code === 3003) {
      throw Object.assign(new Error(res?.message || '无管理权限'), { code: 3003 })
    }
    const raw = res?.data !== undefined ? res.data : res
    logOk(action, {
      transferred_experts: raw?.transferred_experts,
      source_id: data.source_id,
      target_id: data.target_id
    })
    return raw
  } catch (error) {
    logFail(action, error, payload)
    throw error
  }
}

/** 7. PATCH 改分类（专用，返回 synced_experts） */
export async function updateExpertDepartmentCategory(
  id: string,
  category_id: string
): Promise<{ synced_experts?: number; item?: ExpertDepartmentItem; [key: string]: any }> {
  const action = '改词表分类'
  const url = API_PATHS.EXPERT_DEPARTMENT.ADMIN_CATEGORY(id)
  const payload = { url, id, category_id }
  logReq(action, payload)
  try {
    const res = await request.patch(
      url,
      { category_id },
      { loading: true, loadingText: '同步中...' }
    )
    if (res?.code === 3003) {
      throw Object.assign(new Error(res?.message || '无管理权限'), { code: 3003 })
    }
    const raw = res?.data !== undefined ? res.data : res
    logOk(action, { id, category_id, synced_experts: raw?.synced_experts })
    return raw
  } catch (error) {
    logFail(action, error, payload)
    throw error
  }
}

/** 8. POST 批量审核 */
export async function batchVerifyExpertDepartments(
  data: BatchVerifyRequest
): Promise<{ affected?: number; [key: string]: any }> {
  const action = '批量审核'
  const payload = { url: API_PATHS.EXPERT_DEPARTMENT.ADMIN_BATCH_VERIFY, data }
  logReq(action, payload)
  try {
    const res = await request.post(API_PATHS.EXPERT_DEPARTMENT.ADMIN_BATCH_VERIFY, data, {
      loading: true,
      loadingText: '审核中...'
    })
    if (res?.code === 3003) {
      throw Object.assign(new Error(res?.message || '无管理权限'), { code: 3003 })
    }
    const raw = res?.data !== undefined ? res.data : res
    logOk(action, { affected: raw?.affected, count: data.department_ids?.length })
    return raw
  } catch (error) {
    logFail(action, error, payload)
    throw error
  }
}

export default {
  listExpertDepartments,
  createExpertDepartment,
  getExpertDepartmentDetail,
  updateExpertDepartment,
  deleteExpertDepartment,
  listUnmappedExperts,
  mergeExpertDepartments,
  updateExpertDepartmentCategory,
  batchVerifyExpertDepartments
}
