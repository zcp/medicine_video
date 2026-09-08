/**
 * 品牌-专题关联API
 * 阶段一新建：2025
 * 封装品牌与专题关联相关的API请求
 */

import { get, post, del } from '@/utils/request';
import type { BrandTopicsPayload } from '@/types/brand';
import type { ApiResponse, PaginatedResponse, QueryParams } from '@/types/common';

/**
 * 批量关联专题到品牌（Admin）
 * @param brandId 品牌ID
 * @param data 专题ID列表
 * @returns Promise<ApiResponse<void>>
 * @example
 * await addBrandTopics('brand_uuid_123', {
 *   topic_ids: ['topic_uuid_1', 'topic_uuid_2']
 * });
 */
export const addBrandTopics = (brandId: string, data: BrandTopicsPayload): Promise<ApiResponse<void>> => {
  return post<ApiResponse<void>>(`/admin/brands/${brandId}/topics`, data, { auth: true });
};

/**
 * 解除单个品牌-专题关联（Admin）
 * @param brandId 品牌ID
 * @param topicId 专题ID
 * @returns Promise<ApiResponse<void>>
 * @example
 * await removeBrandTopic('brand_uuid_123', 'topic_uuid_1');
 */
export const removeBrandTopic = (brandId: string, topicId: string): Promise<ApiResponse<void>> => {
  return del<ApiResponse<void>>(`/admin/brands/${brandId}/topics/${topicId}`, undefined, { auth: true });
};

/**
 * 获取品牌的关联专题列表（Admin）
 * @param brandId 品牌ID
 * @param params 查询参数
 * @returns Promise<ApiResponse<PaginatedResponse<any>>>
 * @example
 * const response = await getBrandTopics('brand_uuid_123', { page: 1, size: 10 });
 */
export const getBrandTopics = (brandId: string, params: QueryParams = {}): Promise<ApiResponse<PaginatedResponse<any>>> => {
  return get<ApiResponse<PaginatedResponse<any>>>(`/admin/brands/${brandId}/topics`, params, { auth: true });
};
