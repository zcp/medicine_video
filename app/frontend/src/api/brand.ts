/**
 * 鍝佺墝鐩稿叧API
 * 2025
 * 灏佽鍝佺墝/鍚堜綔浼欎即鐩稿叧鐨凙PI璇锋眰
 */

import { get, post, patch, del } from '@/utils/request';
import type { Brand, BrandCreatePayload, BrandUpdatePayload } from '@/types/brand';
import type { ApiResponse, PaginatedResponse, QueryParams } from '@/types/common';
import { getToken } from '@/store/auth';
import { ENV_CONFIG } from '@/config/env';

/**
 * 获取品牌列表（公开接口）
 * @param params 查询参数
 * @returns Promise<ApiResponse<PaginatedResponse<Brand>>>
 * @example
 * const response = await getBrands({ page: 1, size: 10 });
 */
export const getBrands = (params: QueryParams = {}): Promise<ApiResponse<PaginatedResponse<Brand>>> => {
  return get<ApiResponse<PaginatedResponse<Brand>>>('/brands', params);
};

/**
 * 获取单个品牌详情（公开接口）
 * @param brandId 品牌ID
 * @returns Promise<ApiResponse<Brand>>
 * @example
 * const response = await getBrandById('550e8400-e29b-41d4-a716-446655440001');
 */
export const getBrandById = (brandId: string): Promise<ApiResponse<Brand>> => {
  return get<ApiResponse<Brand>>(`/brands/${brandId}`);
};

/**
 * 鑾峰彇鍝佺墝璇︽儏鍙婂叧鑱斾笓棰橈紙鍏紑鎺ュ彛锛? * @param brandId 鍝佺墝ID
 * @returns Promise<ApiResponse<any>>
 * @example
 * const response = await getBrandContent('550e8400-e29b-41d4-a716-446655440001');
 */
export const getBrandContent = (brandId: string): Promise<ApiResponse<any>> => {
  return get<ApiResponse<any>>(`/brands/${brandId}/content`);
};

/**
 * 获取品牌关联直播间（公开接口）
 * @description GET /brands/{brand_id}/rooms，字段由后端聚合（状态/专家/创建者）
 * @param brandId 品牌ID
 * @param params 分页参数
 */
export const getBrandRooms = (
  brandId: string,
  params: { page?: number; size?: number } = {}
): Promise<ApiResponse<PaginatedResponse<BrandRoomCardItem>>> => {
  return get<ApiResponse<PaginatedResponse<BrandRoomCardItem>>>(`/brands/${brandId}/rooms`, params);
};

/**
 * 品牌关联直播间卡片项（与专家详情卡片字段对齐）
 */
export interface BrandRoomCardItem {
  room_id: string;
  title: string;
  description?: string;
  cover_url?: string;
  is_private?: boolean;
  live_status?: string;
  expert_name?: string;
  expert_title?: string;
  expert_hospital?: string;
  expert_avatar?: string;
}

/**
 * 鍒涘缓鍝佺墝锛堢鐞嗗憳鎺ュ彛锛? * @param data 鍝佺墝鍒涘缓鏁版嵁
 * @returns Promise<ApiResponse<Brand>>
 * @example
 * const response = await createBrand({
 *   name: '杩堢憺鍖荤枟',
 *   logo_url: 'https://example.com/logo.png'
 * });
 */
export const createBrand = (data: BrandCreatePayload): Promise<ApiResponse<Brand>> => {
  return post<ApiResponse<Brand>>('/admin/brands', data, { auth: true });
};

/**
 * 鏇存柊鍝佺墝锛堢鐞嗗憳鎺ュ彛锛? * @param brandId 鍝佺墝ID
 * @param data 鍝佺墝鏇存柊鏁版嵁
 * @returns Promise<ApiResponse<Brand>>
 * @example
 * const response = await updateBrand('550e8400-e29b-41d4-a716-446655440001', {
 *   name: '杩堢憺鍖荤枟锛堟洿鏂帮級'
 * });
 */
export const updateBrand = (brandId: string, data: BrandUpdatePayload): Promise<ApiResponse<Brand>> => {
  return patch<ApiResponse<Brand>>(`/admin/brands/${brandId}`, data, { auth: true });
};

/**
 * 鍒犻櫎鍝佺墝锛堢鐞嗗憳鎺ュ彛锛岃蒋鍒犻櫎锛? * @param brandId 鍝佺墝ID
 * @returns Promise<ApiResponse<void>>
 * @example
 * await deleteBrand('550e8400-e29b-41d4-a716-446655440001');
 */
export const deleteBrand = (brandId: string): Promise<ApiResponse<void>> => {
  return del<ApiResponse<void>>(`/admin/brands/${brandId}`, undefined, { auth: true });
};

/**
 * 鑾峰彇鍝佺墝鍒楄〃锛堢鐞嗗憳鎺ュ彛锛屽寘鍚凡绂佺敤锛? * @param params 鏌ヨ鍙傛暟
 * @returns Promise<ApiResponse<PaginatedResponse<Brand>>>
 */
export const getAdminBrands = (params: QueryParams & { is_active?: boolean; name?: string } = {}): Promise<ApiResponse<PaginatedResponse<Brand>>> => {
  return get<ApiResponse<PaginatedResponse<Brand>>>('/admin/brands', params, { auth: true });
};

/**
 * 缁戝畾鐩存挱闂村搧鐗岋紙绠＄悊鍛樻帴鍙ｏ級
 * @param roomId 鐩存挱闂碔D
 * @param brandIds 鍝佺墝ID鏁扮粍
 * @returns Promise<ApiResponse<{ room_id: string; brand_ids: string[]; updated_at: string }>>
 * @example
 * const response = await bindRoomBrands('room-uuid', ['brand-uuid-1', 'brand-uuid-2']);
 */
export const bindRoomBrands = (
  roomId: string, 
  brandIds: string[]
): Promise<ApiResponse<{ room_id: string; brand_ids: string[]; updated_at: string }>> => {
  return post<ApiResponse<{ room_id: string; brand_ids: string[]; updated_at: string }>>(
    `/admin/rooms/${roomId}/brands`, 
    { brand_ids: brandIds }, 
    { auth: true }
  );
};

/**
 * 获取房间品牌列表（公开接口）
 * @param roomId 房间ID
 * @returns Promise<ApiResponse<Brand[]>>
 * @example
 * const response = await getRoomBrands('room-uuid');
 */
export const getRoomBrands = (roomId: string): Promise<ApiResponse<Brand[]>> => {
  return get<ApiResponse<Brand[]>>(`/rooms/${roomId}/brands`);
};

/**
 * 上传品牌Logo（管理员接口）
 * 后端自动更新 brand.logo_url 并返回 { brand_id, logo_url }
 * @param brandId 品牌ID（必须已存在）
 * @param filePath 本地临时文件路径
 * @returns Promise<ApiResponse<{ brand_id: string; logo_url: string }>>
 */
export const uploadBrandLogo = (
  brandId: string,
  filePath: string
): Promise<ApiResponse<{ brand_id: string; logo_url: string }>> => {
  const token = getToken();
  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url: `${ENV_CONFIG.VITE_BASE_API_URL}/admin/brands/${brandId}/logo`,
      filePath,
      name: 'file',
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
