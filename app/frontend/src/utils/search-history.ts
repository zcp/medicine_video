/**
 * 搜索历史管理工具
 * @description 本地存储搜索历史记录，支持添加、删除、清空操作
 */
import { getStorage, setStorage } from '@/utils/storage';
import type { SearchHistoryItem } from '@/types/search';
import { logger } from '@/utils/logger';

/** 搜索历史存储key */
const STORAGE_KEY = 'search_history';

/** 最大历史记录数 */
export const SEARCH_HISTORY_MAX_COUNT = 10;

/**
 * 解析当前登录用户ID（仅用于前端本地分桶）
 */
const getCurrentUserId = (): string | null => {
  try {
    const token = uni.getStorageSync('jwt_token');
    if (!token || typeof token !== 'string') {
      return null;
    }

    const parts = token.split('.');
    if (parts.length !== 3) {
      return null;
    }

    const payload = JSON.parse(atob(parts[1].replace(/-/g, '+').replace(/_/g, '/')));
    return payload.user_id || payload.sub || null;
  } catch {
    return null;
  }
};

/**
 * 获取当前用户的搜索历史存储key
 */
const getUserScopedStorageKey = (): string => {
  const userId = getCurrentUserId();
  return userId ? `${STORAGE_KEY}:${userId}` : `${STORAGE_KEY}:guest`;
};

/**
 * 兼容迁移：将旧全局key的数据迁移到当前用户分桶key（仅迁移一次）
 */
const migrateLegacyHistoryIfNeeded = async (): Promise<void> => {
  try {
    // 仅在未登录（guest）场景迁移旧全局key，避免把历史串到新登录账号
    if (getCurrentUserId()) {
      return;
    }

    const scopedKey = getUserScopedStorageKey();
    const scopedHistory = await getStorage<SearchHistoryItem[]>(scopedKey);
    if (Array.isArray(scopedHistory) && scopedHistory.length > 0) {
      return;
    }

    const legacyHistory = await getStorage<SearchHistoryItem[]>(STORAGE_KEY);
    if (!Array.isArray(legacyHistory) || legacyHistory.length === 0) {
      return;
    }

    await setStorage(scopedKey, legacyHistory);
    await setStorage(STORAGE_KEY, []);
    logger.info(`[search-history] 已将旧全局历史迁移到用户分桶: ${scopedKey}`);
  } catch (error) {
    logger.warn('[search-history] 旧历史迁移失败，忽略并继续:', error);
  }
};

/**
 * 获取搜索历史记录
 * @returns 历史记录数组（按时间倒序）
 */
export const getSearchHistory = async (): Promise<SearchHistoryItem[]> => {
  try {
    await migrateLegacyHistoryIfNeeded();

    const history = await getStorage<SearchHistoryItem[]>(getUserScopedStorageKey());
    if (!history || !Array.isArray(history)) {
      return [];
    }
    // 按时间倒序排序
    return history.sort((a, b) => b.timestamp - a.timestamp);
  } catch (error) {
    logger.error('[getSearchHistory] 获取搜索历史失败:', error);
    return [];
  }
};

/**
 * 添加搜索历史记录
 * @param keyword 搜索关键词
 * @description 自动去重，最多保留10条记录
 */
export const addSearchHistory = async (keyword: string): Promise<void> => {
  try {
    // 去除首尾空格
    const trimmedKeyword = keyword.trim();
    if (!trimmedKeyword) {
      return;
    }

    // 获取当前历史记录
    const history = await getSearchHistory();

    // 去重：删除已存在的相同关键词
    const filteredHistory = history.filter(item => item.keyword !== trimmedKeyword);

    // 添加新记录到数组开头
    const newHistory: SearchHistoryItem[] = [
      {
        keyword: trimmedKeyword,
        timestamp: Date.now()
      },
      ...filteredHistory
    ];

    // 限制最大数量
    const limitedHistory = newHistory.slice(0, SEARCH_HISTORY_MAX_COUNT);

    // 保存到本地存储
    await setStorage(getUserScopedStorageKey(), limitedHistory);
    
    logger.info(`[addSearchHistory] 添加搜索记录: "${trimmedKeyword}"`);
  } catch (error) {
    logger.error('[addSearchHistory] 添加搜索历史失败:', error);
  }
};

/**
 * 删除单条搜索历史记录
 * @param keyword 要删除的关键词
 */
export const deleteSearchHistory = async (keyword: string): Promise<void> => {
  try {
    const history = await getSearchHistory();
    const filteredHistory = history.filter(item => item.keyword !== keyword);
    await setStorage(getUserScopedStorageKey(), filteredHistory);
    
    logger.info(`[deleteSearchHistory] 删除搜索记录: "${keyword}"`);
  } catch (error) {
    logger.error('[deleteSearchHistory] 删除搜索历史失败:', error);
  }
};

/**
 * 清空所有搜索历史记录
 */
export const clearSearchHistory = async (): Promise<void> => {
  try {
    await setStorage(getUserScopedStorageKey(), []);
    logger.info('[clearSearchHistory] 已清空搜索历史');
  } catch (error) {
    logger.error('[clearSearchHistory] 清空搜索历史失败:', error);
  }
};
