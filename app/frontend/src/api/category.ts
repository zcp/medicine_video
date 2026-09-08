/**
 * 分类相关API
 * 阶段一新建：2025
 * 封装医学内容分类相关的API请求
 */

import { get, post, put, del } from '@/utils/request';
import type { Category, CategoryCreatePayload, CategoryUpdatePayload } from '@/types/category';
import type { ApiResponse, PaginatedResponse, QueryParams } from '@/types/common';

/**
 * 获取分类列表（公开接口）
 * @description 后端: GET /api/v1/content/categories — 已在前端7处调用
 *   无需认证，后端自动筛选is_active=true的分类
 * @returns Promise<ApiResponse<Category[]>>
 */
export const getCategories = (options: { showLoading?: boolean } = {}): Promise<ApiResponse<Category[]>> => {
  return get<ApiResponse<Category[]>>('/content/categories', undefined, { ...options });
};

/**
 * 获取单个分类详情（公开接口）
 * @description 后端: GET /api/v1/content/categories/{id} — 当前无前端调用方
 *   如需使用，路径已对齐后端
 * @param categoryId 分类ID
 */
export const getCategoryById = (categoryId: string): Promise<ApiResponse<Category>> => {
  return get<ApiResponse<Category>>(`/content/categories/${categoryId}`);
};

/**
 * 获取分类下的内容（公开接口）
 * @description 后端无此端点，当前无前端调用方
 *   原设计意图是获取某个分类下关联的直播间/场次列表，
 *   类似 getBrandContent 的"分类详情"模式（标签侧的同类设想 getTagContent 已删除，见标签管理 V2 契约层清理）。
 *   如需启用，需后端先新增路由。
 * @deprecated 后端未实现该接口，待确认需求后再决定删除或开发
 */
export const getCategoryContent = (categoryId: string, params: QueryParams = {}): Promise<ApiResponse<any>> => {
  return get<ApiResponse<any>>(`/categories/${categoryId}/content`, params);
};

/**
 * 创建分类（管理员接口）
 * @description 后端: POST /api/v1/admin/categories — 当前无前端调用方
 *   预期与分类管理后台页面配合使用
 * @param data 分类创建数据
 */
export const createCategory = (data: CategoryCreatePayload): Promise<ApiResponse<Category>> => {
  return post<ApiResponse<Category>>('/admin/categories', data, { auth: true });
};

/**
 * 更新分类（管理员接口）
 * @description 后端: PUT /api/v1/admin/categories/{id} — 当前无前端调用方
 *   预期与分类管理后台页面配合使用
 * @param categoryId 分类ID
 * @param data 分类更新数据
 */
export const updateCategory = (categoryId: string, data: CategoryUpdatePayload): Promise<ApiResponse<Category>> => {
  return put<ApiResponse<Category>>(`/admin/categories/${categoryId}`, data, { auth: true });
};

/**
 * 删除分类（管理员接口，软删除）
 * @description 后端: DELETE /api/v1/admin/categories/{id}
 *   参数为 Query：force=false 且分类有引用 → 409 + data.references 结构化；
 *   force=true = 确认级联（安顿引用并级联停用子树，不再跳过检查）；target_category_id 指定迁移目标（缺省"其他"）
 * @param categoryId 分类ID
 * @param options 删除选项
 */
export const deleteCategory = (
  categoryId: string,
  options: { force?: boolean; target_category_id?: string } = {}
): Promise<ApiResponse<void>> => {
  const query: string[] = [];
  if (options.force !== undefined) query.push(`force=${options.force}`);
  if (options.target_category_id) query.push(`target_category_id=${options.target_category_id}`);
  const url = `/admin/categories/${categoryId}${query.length ? `?${query.join('&')}` : ''}`;
  return del<ApiResponse<void>>(url, undefined, { auth: true });
};

/**
 * 获取分类列表（管理员接口，包含已禁用）
 * @description 后端: GET /api/v1/admin/categories — 当前无前端调用方
 *   预期与分类管理后台页面配合使用，返回分页格式
 * @param params 查询参数
 */
export const getAdminCategories = (params: QueryParams & { is_active?: boolean } = {}): Promise<ApiResponse<PaginatedResponse<Category>>> => {
  return get<ApiResponse<PaginatedResponse<Category>>>('/admin/categories', params, { auth: true });
};

// ========== 分类治理工具（阶段4） ==========

/** 分类引用统计（409 响应 data.references） */
export interface CategoryReferences {
  expert_all: number;
  expert_active: number;
  department_count: number;
  room_count: number;
  active_child_count: number;
}

/** 迁移引用统计（migrate 响应 data.migrated） */
export interface CategoryMigrateStats {
  expert_count: number;
  department_count: number;
  room_count: number;
}

/** 合并分类结果（merge 响应 data） */
export interface CategoryMergeResult {
  dry_run: boolean;
  expert_count: number;
  department_count: number;
  room_count: number;
  child_count: number;
  inconsistent_expert_count: number;
  message: string;
}

/**
 * 迁移分类引用（管理员治理工具）
 * @description POST /admin/categories/{id}/migrate
 *   scope: experts=仅专家 / departments=仅科室 / rooms=仅房间关联 / all=全部
 *   校验：target ≠ source、存在且启用、∉ source 子树
 */
export const migrateCategoryReferences = (
  categoryId: string,
  data: { target_category_id: string; scope: 'experts' | 'departments' | 'rooms' | 'all' }
): Promise<ApiResponse<{ migrated: CategoryMigrateStats }>> => {
  return post<ApiResponse<{ migrated: CategoryMigrateStats }>>(`/admin/categories/${categoryId}/migrate`, data, { auth: true });
};

/**
 * 合并分类（管理员治理工具）
 * @description POST /admin/categories/merge
 *   attach_children: false=子分类挂到 target 下（默认）/ true=提升为一级
 *   dry_run: 预览模式只统计不落库
 *   校验：target ≠ source、存在且启用、非"其他"、∉ source 子树
 */
export const mergeCategories = (
  data: { source_id: string; target_id: string; attach_children?: boolean; dry_run?: boolean }
): Promise<ApiResponse<CategoryMergeResult>> => {
  return post<ApiResponse<CategoryMergeResult>>('/admin/categories/merge', data, { auth: true });
};
