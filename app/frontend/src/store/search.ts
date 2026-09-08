/**
 * 搜索状态管理
 * @description 管理搜索历史、热门搜索、搜索结果等状态
 */
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { SearchHistoryItem, HotSearchItem } from '@/types/search';
import type { SearchResultItem, SearchResponse } from '@/api/search';
import { 
  getSearchHistory, 
  addSearchHistory, 
  deleteSearchHistory, 
  clearSearchHistory 
} from '@/utils/search-history';
import { searchResources, getHotKeywords, getSuggestions, getRecommendations, getServerSearchHistory, deleteServerSearchHistory, clearServerSearchHistory } from '@/api/search';
import type { ServerSearchHistoryItem } from '@/api/search';
import { logger } from '@/utils/logger';

export const useSearchStore = defineStore('search', () => {
  /** 搜索历史记录 */
  const searchHistory = ref<SearchHistoryItem[]>([]);

  /** 热门搜索列表（从后端API获取） */
  const hotSearches = ref<HotSearchItem[]>([]);

  /** 热门搜索是否已加载 */
  const hotSearchesLoaded = ref(false);

  /** 搜索建议列表 */
  const suggestions = ref<string[]>([]);

  /** 是否正在加载建议 */
  const suggestionsLoading = ref(false);

  /** 搜索推荐列表 */
  const recommendations = ref<{ keyword: string; score: number }[]>([]);

  /** 当前搜索关键词 */
  const currentKeyword = ref<string>('');

  /** 搜索结果 */
  const searchResults = ref<SearchResultItem[]>([]);

  /** 搜索结果总数 */
  const totalResults = ref<number>(0);

  /** 当前页码 */
  const currentPage = ref<number>(1);

  /** 每页数量 */
  const pageSize = ref<number>(10);

  /** 是否正在搜索 */
  const isSearching = ref<boolean>(false);

  /** 是否有更多数据 */
  const hasMore = computed(() => {
    return searchResults.value.length < totalResults.value;
  });

  /**
   * 加载搜索历史记录（localStorage + 服务端）
   */
  const loadSearchHistory = async () => {
    try {
      // 1. 加载本地历史
      searchHistory.value = await getSearchHistory();

      // 2. 尝试加载服务端历史（登录用户）
      try {
        const token = uni.getStorageSync('jwt_token');
        if (token) {
          const res = await getServerSearchHistory(20);
          if (res.code === 200 && Array.isArray(res.data)) {
            // 合并服务端历史到本地（去重）
            const serverKeywords = new Set(res.data.map((i: ServerSearchHistoryItem) => i.keyword));
            const localOnly = searchHistory.value.filter(h => !serverKeywords.has(h.keyword));
            const serverItems = res.data.map((i: ServerSearchHistoryItem) => ({
              keyword: i.keyword,
              timestamp: new Date(i.last_searched_at).getTime(),
            }));
            searchHistory.value = [...serverItems, ...localOnly].slice(0, 20);
            logger.info('[loadSearchHistory] 合并服务端历史:', serverItems.length);
          }
        }
      } catch {
        // 服务端不可用时保持本地历史
      }
    } catch (error) {
      logger.error('[loadSearchHistory] 加载失败:', error);
    }
  };

  /**
   * 加载热门搜索词（从后端API获取）
   */
  const loadHotKeywords = async () => {
    if (hotSearchesLoaded.value) return;
    try {
      const res = await getHotKeywords(10, 7);
      if (res.code === 200 && Array.isArray(res.data)) {
        hotSearches.value = res.data.map(item => ({
          keyword: item.keyword,
          heat: item.search_count,
        }));
        hotSearchesLoaded.value = true;
        logger.info('[loadHotKeywords] 热门搜索加载成功:', hotSearches.value.length);
      }
    } catch (error) {
      logger.warn('[loadHotKeywords] 热门搜索加载失败，使用空列表:', error);
    }
  };

  /**
   * 获取搜索建议（输入时实时联想）
   */
  const fetchSuggestions = async (keyword: string) => {
    if (!keyword || keyword.trim().length < 1) {
      suggestions.value = [];
      return;
    }
    suggestionsLoading.value = true;
    try {
      const res = await getSuggestions(keyword.trim(), 10);
      if (res.code === 200 && Array.isArray(res.data)) {
        suggestions.value = res.data.map(item => item.keyword);
      }
    } catch (error) {
      logger.warn('[fetchSuggestions] 加载建议失败:', error);
      suggestions.value = [];
    } finally {
      suggestionsLoading.value = false;
    }
  };

  /**
   * 加载搜索推荐
   */
  const loadRecommendations = async (keyword?: string) => {
    try {
      const res = await getRecommendations(keyword || undefined, 8);
      if (res.code === 200 && Array.isArray(res.data)) {
        recommendations.value = res.data;
      }
    } catch (error) {
      logger.warn('[loadRecommendations] 加载失败:', error);
    }
  };

  /**
   * 添加搜索记录
   */
  const addHistory = async (keyword: string) => {
    try {
      await addSearchHistory(keyword);
      await loadSearchHistory();
    } catch (error) {
      logger.error('[addHistory] 添加搜索记录失败:', error);
    }
  };

  /**
   * 删除单条搜索记录（localStorage + 服务端同步删除）
   */
  const deleteHistory = async (keyword: string) => {
    try {
      // 1. 从本地存储删除
      await deleteSearchHistory(keyword);

      // 2. 同步删除服务端记录（需先查找 serverId）
      try {
        const token = uni.getStorageSync('jwt_token');
        if (token) {
          const res = await getServerSearchHistory(20);
          if (res.code === 200 && Array.isArray(res.data)) {
            const match = res.data.find((i: ServerSearchHistoryItem) => i.keyword === keyword);
            if (match) {
              await deleteServerSearchHistory(match.id);
              logger.info(`[deleteHistory] 已同步删除服务端记录: "${keyword}" (id: ${match.id})`);
            }
          }
        }
      } catch {
        // 服务端删除失败不阻塞本地操作
        logger.warn(`[deleteHistory] 服务端删除"${keyword}"失败，本地已删除`);
      }

      // 3. 直接从本地列表移除，而非从服务端重新加载（避免被服务端旧数据覆盖）
      searchHistory.value = searchHistory.value.filter(h => h.keyword !== keyword);
      logger.info(`[deleteHistory] 已删除搜索记录: "${keyword}"`);
    } catch (error) {
      logger.error('[deleteHistory] 删除搜索记录失败:', error);
    }
  };

  /**
   * 清空搜索历史
   */
  const clearHistory = async () => {
    try {
      await clearSearchHistory();
      // 同步清空服务端
      try { await clearServerSearchHistory(); } catch { /* ignore */ }
      searchHistory.value = [];
      logger.info('[clearHistory] 搜索历史已清空');
    } catch (error) {
      logger.error('[clearHistory] 清空搜索历史失败:', error);
    }
  };

  /**
   * 执行搜索
   * @param keyword 搜索关键词
   * @param type 资源类型筛选
   * @param page 页码
   * @param append 是否追加到现有结果（用于加载更多）
   */
  const performSearch = async (
    keyword: string,
    type?: string,
    page: number = 1,
    append: boolean = false
  ): Promise<void> => {
    try {
      isSearching.value = true;
      currentKeyword.value = keyword;
      currentPage.value = page;

      const response = await searchResources({
        q: keyword,
        page,
        size: pageSize.value,
        type
      });

      if (response.code === 200 && response.data) {
        const data = response.data as SearchResponse;
        
        if (append) {
          // 追加模式：合并结果（用于加载更多）
          searchResults.value = [...searchResults.value, ...data.items];
        } else {
          // 替换模式：重置结果（新搜索）
          searchResults.value = data.items;
        }

        totalResults.value = data.total;

        // 添加到搜索历史（仅在首次搜索时）
        if (page === 1 && !append) {
          await addHistory(keyword);
        }

        logger.info(`[performSearch] 搜索成功: "${keyword}", 结果数: ${data.total}`);
      } else {
        throw new Error(response.message || '搜索失败');
      }
    } catch (error) {
      logger.error('[performSearch] 搜索失败:', error);
      uni.showToast({
        title: '搜索失败',
        icon: 'none',
        duration: 2000
      });
      throw error;
    } finally {
      isSearching.value = false;
    }
  };

  /**
   * 加载更多搜索结果
   */
  const loadMore = async (type?: string): Promise<void> => {
    if (!hasMore.value || isSearching.value) {
      return;
    }

    const nextPage = currentPage.value + 1;
    await performSearch(currentKeyword.value, type, nextPage, true);
  };

  /**
   * 重置搜索状态
   */
  const resetSearch = () => {
    currentKeyword.value = '';
    searchResults.value = [];
    totalResults.value = 0;
    currentPage.value = 1;
    isSearching.value = false;
  };

  return {
    // 状态
    searchHistory,
    hotSearches,
    suggestions,
    suggestionsLoading,
    recommendations,
    currentKeyword,
    searchResults,
    totalResults,
    currentPage,
    pageSize,
    isSearching,
    hasMore,

    // 方法
    loadSearchHistory,
    loadHotKeywords,
    fetchSuggestions,
    loadRecommendations,
    addHistory,
    deleteHistory,
    clearHistory,
    performSearch,
    loadMore,
    resetSearch
  };
});
