/**
 * 标签相关API
 * 阶段一新建：2025
 * 封装内容标签相关的API请求
 */

import { get, post, patch, del } from '@/utils/request';
import type { Tag, TagCreatePayload, TagUpdatePayload, TagResolveResult } from '@/types/tag';
import type { ApiResponse, PaginatedResponse, QueryParams } from '@/types/common';

/**
 * 获取标签列表（公开接口）
 * @param params 查询参数
 * @returns Promise<ApiResponse<Tag[]>>
 * @example
 * const response = await getTags();
 */
export const getTags = (params: QueryParams = {}): Promise<ApiResponse<Tag[]>> => {
  return get<ApiResponse<Tag[]>>('/content/tags', params);
};

/**
 * 解析或创建标签（需登录；resolve 幂等：命中复用、未中自建 source=user，公共词表立即可联想）
 * @param name 标签名（1~80，后端 strip；违禁词 422/2005 不落库；软删同名 400/4001「标签不可用」不复活）
 * @returns Promise<ApiResponse<TagResolveResult>>
 * @example
 * const response = await resolveTag('手术直播');
 * // response.data: { id: '...', name: '手术直播', created: true, source: 'user' }
 */
export const resolveTag = (name: string): Promise<ApiResponse<TagResolveResult>> => {
  return post<ApiResponse<TagResolveResult>>('/content/tags/resolve', { name }, { auth: true });
};

/**
 * 创建标签（管理员接口）
 * @param data 标签创建数据
 * @returns Promise<ApiResponse<Tag>>
 * @example
 * const response = await createTag({
 *   name: '手术直播',
 *   slug: 'surgery-live'
 * });
 */
export const createTag = (data: TagCreatePayload): Promise<ApiResponse<Tag>> => {
  return post<ApiResponse<Tag>>('/admin/tags', data, { auth: true });
};

/**
 * 更新标签（管理员接口）
 * @param tagId 标签ID
 * @param data 标签更新数据
 * @returns Promise<ApiResponse<Tag>>
 * @example
 * const response = await updateTag('550e8400-e29b-41d4-a716-446655440001', {
 *   name: '手术直播（更新）'
 * });
 */
export const updateTag = (tagId: string, data: TagUpdatePayload): Promise<ApiResponse<Tag>> => {
  return patch<ApiResponse<Tag>>(`/admin/tags/${tagId}`, data, { auth: true });
};

/**
 * 删除标签（管理员接口，软删除）
 * @param tagId 标签ID
 * @returns Promise<ApiResponse<void>>
 * @example
 * await deleteTag('550e8400-e29b-41d4-a716-446655440001');
 */
export const deleteTag = (tagId: string): Promise<ApiResponse<void>> => {
  return del<ApiResponse<void>>(`/admin/tags/${tagId}`, undefined, { auth: true });
};

/**
 * 获取标签列表（管理员接口，包含已禁用）
 * @param params 查询参数
 * @returns Promise<ApiResponse<PaginatedResponse<Tag>>>
 */
export const getAdminTags = (params: QueryParams & { is_active?: boolean } = {}): Promise<ApiResponse<PaginatedResponse<Tag>>> => {
  return get<ApiResponse<PaginatedResponse<Tag>>>('/admin/tags', params, { auth: true });
};
