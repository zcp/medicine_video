/**
 * 内容安全管理端 API
 * 对齐后端 /admin/content-safety 端点（live_core）
 */

import { get, post, patch } from '@/utils/request';
import type { ApiResponse } from '@/types/common';
import type {
  ContentSafetyRule,
  ContentSafetyRuleCreate,
  ContentSafetyRuleUpdate,
  ContentSafetyRuleListParams,
  ContentSafetyLogQueryParams,
  PaginatedContentSafetyRules,
  PaginatedContentSafetyLogs,
} from '@/types/contentSafety';

/** GET /admin/content-safety/rules */
export const getContentSafetyRules = (
  params?: ContentSafetyRuleListParams
): Promise<ApiResponse<PaginatedContentSafetyRules>> => {
  return get<ApiResponse<PaginatedContentSafetyRules>>('/admin/content-safety/rules', params, { auth: true });
};

/** POST /admin/content-safety/rules */
export const createContentSafetyRule = (
  data: ContentSafetyRuleCreate
): Promise<ApiResponse<ContentSafetyRule>> => {
  return post<ApiResponse<ContentSafetyRule>>('/admin/content-safety/rules', data, { auth: true });
};

/** PATCH /admin/content-safety/rules/{ruleId} */
export const updateContentSafetyRule = (
  ruleId: string,
  data: ContentSafetyRuleUpdate
): Promise<ApiResponse<ContentSafetyRule>> => {
  return patch<ApiResponse<ContentSafetyRule>>(`/admin/content-safety/rules/${ruleId}`, data, { auth: true });
};

/** GET /admin/content-safety/logs */
export const getContentSafetyLogs = (
  params?: ContentSafetyLogQueryParams
): Promise<ApiResponse<PaginatedContentSafetyLogs>> => {
  return get<ApiResponse<PaginatedContentSafetyLogs>>('/admin/content-safety/logs', params, { auth: true });
};
