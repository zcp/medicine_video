/**
 * 搜索 API
 * 兼容房间搜索、综合搜索，以及新增的热词/建议/历史能力。
 */

import { request } from '@/utils/request'
import { API_PATHS } from '@/config/api'
import type { ApiResponse, PaginatedResponse } from '@/types/common'

export interface HotKeywordItem {
  keyword: string
  search_count: number
  last_searched_at: string
}

export interface SearchSuggestionItem {
  keyword: string
}

export interface SearchHistoryItem {
  id: string
  keyword: string
  search_count: number
  last_searched_at: string
}

// §5.1 GET /api/v1/rooms?q=... 按关键词搜索房间
export const searchRooms = (
  q: string,
  opts?: {
    page?: number
    size?: number
    category_id?: string
  }
): Promise<ApiResponse<PaginatedResponse<any>>> => {
  return request.get(API_PATHS.OTHER.ROOMS_SEARCH, {
    data: { q, keyword: q, ...(opts || {}) },
    showError: false
  })
}

export const globalSearch = (
  q: string,
  opts?: { type?: string; page?: number; size?: number; category_id?: string }
): Promise<ApiResponse<any>> => {
  return request.get(API_PATHS.OTHER.SEARCH, {
    data: { q, keyword: q, ...(opts || {}) },
    showError: false
  })
}

export const recordSearchQuery = (
  q: string,
  opts?: { type?: string; page?: number; size?: number; category_id?: string }
): Promise<ApiResponse<any>> => {
  return globalSearch(q, opts)
}

export const getHotKeywords = (
  params?: { limit?: number; days?: number }
): Promise<ApiResponse<HotKeywordItem[]>> => {
  return request.get('/search/hot-keywords', {
    data: params,
    auth: false,
    showError: false
  })
}

export const getSearchSuggestions = (
  params: { keyword: string; limit?: number }
): Promise<ApiResponse<SearchSuggestionItem[]>> => {
  return request.get('/search/suggestions', {
    data: params,
    auth: false,
    showError: false
  })
}

export const getSearchHistory = (
  params?: { limit?: number }
): Promise<ApiResponse<SearchHistoryItem[]>> => {
  return request.get('/users/me/search-history', {
    data: params,
    showError: false
  })
}

export const deleteSearchHistoryItem = (
  historyId: string
): Promise<ApiResponse<null>> => {
  return request.delete(`/users/me/search-history/${encodeURIComponent(historyId)}`, {
    loading: true,
    loadingText: '删除中...',
    showError: false
  })
}

export const clearSearchHistory = (): Promise<ApiResponse<{ deleted_count: number }>> => {
  return request.delete('/users/me/search-history', {
    loading: true,
    loadingText: '清空中...',
    showError: false
  })
}

export default {
  searchRooms,
  globalSearch,
  recordSearchQuery,
  getHotKeywords,
  getSearchSuggestions,
  getSearchHistory,
  deleteSearchHistoryItem,
  clearSearchHistory
}
