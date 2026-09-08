/**
 * 全局搜索API
 * @description 对应后端 Search 模块
 * 支持跨直播间、专家、专题、品牌的全局搜索
 */

import { get, del } from '@/utils/request';
import type { ApiResponse, PaginatedResponse } from '@/types/common';

/**
 * 搜索结果项类型
 */
export type SearchResultType = 'room' | 'expert' | 'topic' | 'brand';

/**
 * 搜索结果项
 */
export interface SearchResultItem {
  /** 资源ID */
  id: string;
  /** 资源类型 */
  type: SearchResultType;
  /** 标题 */
  title: string;
  /** 副标题/描述 */
  subtitle?: string;
  /** 后端摘要/描述 (room=简介, expert=bio, brand=description) */
  summary?: string;
  /** 封面图 */
  cover_url?: string;
  /** 匹配分数 (0-100) */
  match_score: number;
  /** 高亮的标题（包含<em>标签） */
  highlighted_title?: string;
  /** 元数据（类型特定的额外信息） */
  metadata?: {
    /** 直播间状态 (仅room类型) */
    status?: 'scheduled' | 'live' | 'finished' | 'ended';
    /** 开始时间 (仅room类型) */
    start_time?: string;
    /** 主讲专家姓名 (仅room类型) */
    expert_name?: string;
    /** 主讲专家头像 (仅room类型) */
    expert_avatar?: string;
    /** 主讲专家职称 (仅room类型，扩展字段) */
    expert_title?: string;
    /** 主讲专家医院 (仅room类型，扩展字段) */
    expert_hospital?: string;
    /** 专家职称 (仅expert类型) */
    title?: string;
    /** 专家医院 (仅expert类型) */
    hospital?: string;
    /** 专家擅长领域 (仅expert类型，逗号分隔字符串) */
    expertise_areas?: string;
    /** 专题直播间数量 (仅topic类型) */
    room_count?: number;
  };
}

/**
 * 搜索查询参数
 */
export interface SearchParams {
  /** 搜索关键词（至少2个字符） */
  q: string;
  /** 页码 (默认1) */
  page?: number;
  /** 每页数量 (默认10, 最大50) */
  size?: number;
  /** 资源类型筛选（逗号分隔，如 'room,expert'） */
  type?: string;
  /** 分类ID筛选（仅对room有效） */
  category_id?: string;
}

/**
 * 搜索响应数据
 */
export interface SearchResponse {
  total: number;
  page: number;
  size: number;
  items: SearchResultItem[];
}

/**
 * 过滤掉对象中值为 undefined 的字段
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
 * 全局搜索
 * @description GET /api/v1/search - 公开访问，无需JWT Token
 * 
 * 支持跨直播间、专家、专题、品牌的模糊搜索，返回匹配分数和高亮文本
 * 
 * @param params 搜索参数
 * @returns 分页的搜索结果列表
 * 
 * @example
 * // 基础搜索
 * const res = await searchResources({ q: '骨科', page: 1, size: 10 });
 * const results = res.data.items;
 * 
 * @example
 * // 按类型筛选（只搜索直播间和专家）
 * const res = await searchResources({ 
 *   q: '心脏病', 
 *   type: 'room,expert',
 *   page: 1 
 * });
 * 
 * @example
 * // 按分类筛选（仅对直播间有效）
 * const res = await searchResources({ 
 *   q: '手术', 
 *   type: 'room',
 *   category_id: '550e8400-e29b-41d4-a716-446655440001' 
 * });
 */
export const searchResources = (
  params: SearchParams
): Promise<ApiResponse<SearchResponse>> => {
  // 过滤掉undefined参数，避免uni.request序列化为"undefined"字符串
  const cleanParams = filterUndefined(params);
  return get<ApiResponse<SearchResponse>>('/search', cleanParams);
};

// ==================== 搜索扩展 API ====================

/** 热门搜索项（后端返回） */
export interface HotKeywordItem {
  keyword: string;
  search_count: number;
  last_searched_at: string;
}

/** 搜索推荐项（后端返回） */
export interface RecommendationItem {
  keyword: string;
  score: number;
}

/**
 * 获取热门搜索词
 * @description GET /api/v1/search/hot-keywords - 公开接口
 * @param limit 返回条数 (默认10, 最大50)
 * @param days 统计天数窗口 (默认7, 最大30)
 */
export const getHotKeywords = (
  limit?: number,
  days?: number
): Promise<ApiResponse<HotKeywordItem[]>> => {
  const params: Record<string, any> = {};
  if (limit !== undefined) params.limit = limit;
  if (days !== undefined) params.days = days;
  return get<ApiResponse<HotKeywordItem[]>>('/search/hot-keywords', params);
};

/**
 * 获取搜索建议（前缀匹配）
 * @description GET /api/v1/search/suggestions - 公开接口
 * @param keyword 输入关键词
 * @param limit 返回条数 (默认10, 最大20)
 */
export const getSuggestions = (
  keyword: string,
  limit?: number
): Promise<ApiResponse<{ keyword: string }[]>> => {
  const params: Record<string, any> = { keyword };
  if (limit !== undefined) params.limit = limit;
  return get<ApiResponse<{ keyword: string }[]>>('/search/suggestions', params);
};

/**
 * 获取搜索推荐
 * @description GET /api/v1/search/recommendations - 公开接口（可选认证）
 * @param keyword 搜索关键词（可选，为空时返回全局热词）
 * @param limit 返回条数 (默认8, 最大20)
 */
export const getRecommendations = (
  keyword?: string,
  limit?: number
): Promise<ApiResponse<RecommendationItem[]>> => {
  const params: Record<string, any> = {};
  if (keyword !== undefined && keyword !== '') params.keyword = keyword;
  if (limit !== undefined) params.limit = limit;
  return get<ApiResponse<RecommendationItem[]>>('/search/recommendations', params);
};

// ==================== 搜索历史 API（需登录） ====================

/** 服务端搜索历史项 */
export interface ServerSearchHistoryItem {
  id: string;
  keyword: string;
  search_count: number;
  last_searched_at: string;
}

/**
 * 获取服务端搜索历史
 * @description GET /api/v1/users/me/search-history - 需 JWT Token
 */
export const getServerSearchHistory = (
  limit?: number
): Promise<ApiResponse<ServerSearchHistoryItem[]>> => {
  const url = `/users/me/search-history${limit ? `?limit=${limit}` : ''}`;
  return get<ApiResponse<ServerSearchHistoryItem[]>>(url, undefined, { auth: true });
};

/**
 * 删除单条搜索历史
 * @description DELETE /api/v1/users/me/search-history/{id} - 需 JWT Token
 */
export const deleteServerSearchHistory = (
  historyId: string
): Promise<ApiResponse<null>> => {
  return del<ApiResponse<null>>(`/users/me/search-history/${historyId}`, { auth: true });
};

/**
 * 清空全部搜索历史
 * @description DELETE /api/v1/users/me/search-history - 需 JWT Token
 */
export const clearServerSearchHistory = (): Promise<ApiResponse<null>> => {
  return del<ApiResponse<null>>('/users/me/search-history', { auth: true });
};
