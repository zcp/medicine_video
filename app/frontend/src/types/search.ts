/**
 * 搜索模块类型定义
 * @description 搜索历史、热门搜索、搜索建议等类型
 */

/**
 * 搜索历史记录项
 */
export interface SearchHistoryItem {
  /** 搜索关键词 */
  keyword: string;
  /** 搜索时间戳 */
  timestamp: number;
}

/**
 * 热门搜索项
 */
export interface HotSearchItem {
  /** 热门关键词 */
  keyword: string;
  /** 热度值（用于排序） */
  heat?: number;
  /** 是否为新增热词 */
  isNew?: boolean;
}

/**
 * 搜索建议项（Mock使用）
 */
export interface SuggestionItem {
  /** 建议关键词 */
  keyword: string;
  /** 匹配数量 */
  match_count?: number;
}

/**
 * Tab类型
 */
export type SearchTabType = 'all' | 'room' | 'expert' | 'brand';

/**
 * Tab配置项
 */
export interface SearchTab {
  /** Tab标识 */
  key: SearchTabType;
  /** Tab标题 */
  label: string;
  /** API type参数值 */
  apiType?: string;
}
