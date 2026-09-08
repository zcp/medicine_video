/**
 * 焦点图相关API
 * 阶段一新建：2025
 * 封装首页焦点图轮播相关的API请求
 */

import { get, post, patch, del } from '@/utils/request';
import type { FeaturedContent, FeaturedContentCreatePayload, FeaturedContentUpdatePayload } from '../types/featured';
import type { ApiResponse, PaginatedResponse } from '@/types/common';
import { getToken } from '@/store/auth';
import { ENV_CONFIG } from '@/config/env';

/**
 * 获取焦点图列表（公开接口）
 * @returns Promise<ApiResponse<FeaturedContent[]>>
 * @example
 * const response = await getFeaturedContent();
 */
export const getFeaturedContent = (): Promise<ApiResponse<FeaturedContent[]>> => {
  return get<ApiResponse<FeaturedContent[]>>('/featured-content');
};

/**
 * 创建焦点图（管理员接口）
 * @param data 焦点图创建数据
 * @returns Promise<ApiResponse<FeaturedContent>>
 * @example
 * const response = await createFeaturedContent({
 *   title: '全国骨科学术研讨会',
 *   image_url: '/media/featured/banner1.jpg',
 *   target_type: 'session',
 *   target_id: 'session_uuid_123'
 * });
 */
export const createFeaturedContent = (data: FeaturedContentCreatePayload): Promise<ApiResponse<FeaturedContent>> => {
  return post<ApiResponse<FeaturedContent>>('/admin/featured-content', data, { auth: true });
};

/**
 * 更新焦点图（管理员接口）
 * @param contentId 焦点图ID
 * @param data 焦点图更新数据
 * @returns Promise<ApiResponse<FeaturedContent>>
 * @example
 * const response = await updateFeaturedContent('featured_uuid_1', {
 *   title: '全国骨科学术研讨会（更新）'
 * });
 */
export const updateFeaturedContent = (contentId: string, data: FeaturedContentUpdatePayload): Promise<ApiResponse<FeaturedContent>> => {
  return patch<ApiResponse<FeaturedContent>>(`/admin/featured-content/${contentId}`, data, { auth: true });
};

/**
 * 获取焦点图列表（管理端分页接口）
 * @param params 筛选+分页参数
 * @returns Promise<ApiResponse<PaginatedResponse<FeaturedContent>>>
 */
export const getAdminFeaturedContent = (
  params: { page?: number; size?: number; q?: string; is_active?: boolean; status?: string } = {}
): Promise<ApiResponse<PaginatedResponse<FeaturedContent>>> => {
  return get<ApiResponse<PaginatedResponse<FeaturedContent>>>('/admin/featured-content', params, { auth: true, showLoading: false }, { retry: 1, timeout: 8000 });
};

/**
 * 获取焦点图详情（管理员接口）
 * @param contentId 焦点图ID
 * @returns Promise<ApiResponse<FeaturedContent>>
 */
export const getFeaturedContentDetail = (contentId: string): Promise<ApiResponse<FeaturedContent>> => {
  return get<ApiResponse<FeaturedContent>>(`/admin/featured-content/${contentId}`, undefined, { auth: true });
};

/**
 * 上传焦点图图片（管理员接口）
 * @param contentId 焦点图ID
 * @param filePath 本地临时文件路径
 */
export const uploadFeaturedImage = (
  contentId: string,
  filePath: string
): Promise<ApiResponse<any>> => {
  const token = getToken();
  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url: `${ENV_CONFIG.VITE_BASE_API_URL}/admin/featured-content/${contentId}/image`,
      filePath,
      name: 'image',
      header: token ? { Authorization: `Bearer ${token}` } : {},
      success: (res) => {
        try {
          resolve(JSON.parse(res.data));
        } catch {
          reject(new Error('响应解析失败'));
        }
      },
      fail: (err) => reject(err),
    });
  });
};

/**
 * 删除焦点图（管理员接口）
 * @param contentId 焦点图ID
 * @returns Promise<ApiResponse<void>>
 * @example
 * await deleteFeaturedContent('featured_uuid_1');
 */
export const deleteFeaturedContent = (contentId: string): Promise<ApiResponse<void>> => {
  return del<ApiResponse<void>>(`/admin/featured-content/${contentId}`, undefined, { auth: true });
};
