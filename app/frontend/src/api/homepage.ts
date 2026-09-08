/**
 * 首页专用API
 * @description 对应后端 Homepage 模块 (Section 4.13)
 * 获取首页展示的直播间列表，包含实时状态、主讲专家、热度等信息
 */
import { get } from '@/utils/request';
import type { ApiResponse, PaginatedResponse } from '@/types/common';
import type { HomepageRoomItem } from '@/types/homepage';

/**
 * 首页直播间列表查询参数
 */
export interface HomepageRoomsParams {
  /** 页码 (默认1) */
  page?: number;
  /** 每页数量 (默认10, 最大100) */
  size?: number;
  /** 排序规则: heat:desc, start_time:asc, created_at:desc (默认 heat:desc) */
  sort?: 'heat:desc' | 'start_time:asc' | 'created_at:desc';
  /** 按分类筛选 */
  category_id?: string;
}

/**
 * 首页直播间列表响应数据
 */
export interface HomepageRoomsResponse {
  total: number;
  page: number;
  size: number;
  items: HomepageRoomItem[];
}

/**
 * 过滤掉对象中值为 undefined 的字段
 * @param obj 原始对象
 * @returns 过滤后的对象
 */
const filterUndefined = <T extends Record<string, any>>(obj: T): Partial<T> => {
  const result: any = {};
  Object.keys(obj).forEach(key => {
    if (obj[key] !== undefined) {
      result[key] = obj[key];
    }
  });
  return result;
};

/**
 * 获取首页直播间列表
 * @description GET /api/v1/homepage/rooms - 公开访问，无需JWT Token
 * 
 * 获取首页展示的直播间列表，包含实时状态、主讲专家、热度等信息（分页）
 * 
 * @param params 查询参数
 * @returns 分页的首页直播间列表
 * 
 * @example
 * // 获取第一页，按热度排序
 * const res = await getHomepageRooms({ page: 1, size: 10, sort: 'heat:desc' });
 * const rooms = res.data.items;
 * 
 * @example
 * // 按分类筛选
 * const res = await getHomepageRooms({ 
 *   page: 1, 
 *   size: 10, 
 *   category_id: '550e8400-e29b-41d4-a716-446655440001' 
 * });
 */
export const getHomepageRooms = (
  params: HomepageRoomsParams = {}
): Promise<ApiResponse<HomepageRoomsResponse>> => {
  // 🔧 过滤掉undefined参数，避免uni.request序列化为"undefined"字符串
  const cleanParams = filterUndefined(params);
  return get<ApiResponse<HomepageRoomsResponse>>('/homepage/rooms', cleanParams);
};
