/**
 * 内容安全管理端 API（live_core 网关）
 * 对齐《Live-Saas-Wechat-12-全局内容安全与审核-前端设计文档-v1.0》§5
 */

import { request } from '@/utils/request'
import { API_PATHS } from '@/config/api'
import type { ApiResponse } from '@/types/common'
import type {
  ContentSafetyRule,
  ContentSafetyRuleCreate,
  ContentSafetyRuleUpdate,
  ContentSafetyLogQueryParams,
  ContentSafetyRuleListParams,
  PaginatedContentSafetyRules,
  PaginatedContentSafetyLogs
} from '@/types/contentSafety'

/** GET /admin/content-safety/rules */
export const getContentSafetyRules = (
  params?: ContentSafetyRuleListParams
): Promise<ApiResponse<PaginatedContentSafetyRules>> => {
  return request.get(API_PATHS.CONTENT_SAFETY.RULES, {
    data: params,
    showError: false
  })
}

/** POST /admin/content-safety/rules */
export const createContentSafetyRule = (
  data: ContentSafetyRuleCreate,
  options?: { silent?: boolean }
): Promise<ApiResponse<ContentSafetyRule>> => {
  return request.post(API_PATHS.CONTENT_SAFETY.RULES, data, {
    loading: !options?.silent,
    loadingText: '创建中...',
    showError: false
  })
}

/** PATCH /admin/content-safety/rules/{ruleId} */
export const updateContentSafetyRule = (
  ruleId: string,
  data: ContentSafetyRuleUpdate,
  options?: { silent?: boolean }
): Promise<ApiResponse<ContentSafetyRule>> => {
  return request.patch(API_PATHS.CONTENT_SAFETY.RULE(ruleId), data, {
    loading: !options?.silent,
    loadingText: '保存中...',
    showError: false
  })
}

/** GET /admin/content-safety/logs */
export const getContentSafetyLogs = (
  params?: ContentSafetyLogQueryParams
): Promise<ApiResponse<PaginatedContentSafetyLogs>> => {
  return request.get(API_PATHS.CONTENT_SAFETY.LOGS, {
    data: params,
    showError: false
  })
}

export default {
  getContentSafetyRules,
  createContentSafetyRule,
  updateContentSafetyRule,
  getContentSafetyLogs
}
