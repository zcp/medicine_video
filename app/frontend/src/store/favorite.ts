/**
 * 收藏Store
 * 管理用户的收藏状态，减少API请求
 */

import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { getFavorites, addFavorite as addFavoriteApi, removeFavorite as removeFavoriteApi, checkIsFavorited as checkIsFavoritedApi } from '@/api/favorite';
import type { FavoriteWithRoom } from '@/types/favorite';
import { RequestLock } from '@/utils/debounce';

export const useFavoriteStore = defineStore('favorite', () => {
  // ========== 状态 ==========
  
  /** 收藏的直播间ID集合（用于快速查询） */
  const favoriteRoomIds = ref<Set<string>>(new Set());
  
  /** 完整的收藏列表（用于收藏列表页显示） */
  const favoriteList = ref<FavoriteWithRoom[]>([]);
  
  /** 是否正在加载 */
  const loading = ref(false);
  
  /** 是否已加载过（避免重复加载） */
  const loaded = ref(false);
  
  /** 请求锁（防止重复收藏/取消收藏） */
  const favoriteRequestLock = new RequestLock();
  const unfavoriteRequestLock = new RequestLock();
  
  // ========== 计算属性 ==========
  
  /** 收藏数量 */
  const favoriteCount = computed(() => favoriteRoomIds.value.size);
  
  // ========== 方法 ==========
  
  /**
   * 加载收藏列表
   * @param force 是否强制刷新（忽略缓存）
   */
  async function loadFavorites(force: boolean = false) {
    // 如果已加载且不强制刷新，则跳过
    if (loaded.value && !force) {
      console.log('[FavoriteStore] 使用缓存数据');
      return;
    }
    
    if (loading.value) {
      console.log('[FavoriteStore] 正在加载中，跳过');
      return;
    }
    
    loading.value = true;
    
    try {
      console.log('[FavoriteStore] 开始加载收藏列表');
      
      // 分页获取所有收藏（避免数量超过100的问题）
      let page = 1;
      const allItems: FavoriteWithRoom[] = [];
      
      while (true) {
        const res = await getFavorites({ page, size: 100 });
        const items = res.data?.items || [];
        allItems.push(...items);
        
        // 如果返回的数据少于100条，说明已经是最后一页
        if (items.length < 100) break;
        
        page++;
        
        // 安全限制：最多获取500个收藏
        if (page > 5) {
          console.warn('[FavoriteStore] 收藏数量超过500，只加载前500个');
          break;
        }
      }
      
      console.log('[FavoriteStore] 基础收藏列表加载完成:', allItems.length, '个');
      
      // ===== 关键修复：立即更新favoriteRoomIds，确保收藏状态检测可用 =====
      favoriteRoomIds.value = new Set(allItems.map(item => item.room_id));
      loaded.value = true;
      console.log('[FavoriteStore] ✅ favoriteRoomIds已更新:', favoriteRoomIds.value.size, '个');
      
      // 直接设置列表（卡片字段由后端批量聚合返回，无需前端补充）
      favoriteList.value = allItems;
    } catch (error) {
      console.error('[FavoriteStore] 加载收藏列表失败:', error);
      throw error;
    } finally {
      loading.value = false;
    }
  }
  
  /**
   * 检查是否已收藏某个直播间
   * @param roomId 直播间ID
   * @returns 是否已收藏
   */
  function isFavorited(roomId: string): boolean {
    return favoriteRoomIds.value.has(roomId);
  }
  
  /**
   * 从API检查是否已收藏指定直播间（单次查询，不依赖列表加载）
   * @param roomId 直播间ID
   * @returns Promise<boolean>
   * @description 调用 GET /api/v1/rooms/{room_id}/is-favorited
   */
  async function checkIsFavoritedFromApi(roomId: string): Promise<boolean> {
    try {
      console.log('[FavoriteStore] 检查直播间收藏状态:', roomId.substring(0, 8));
      const res = await checkIsFavoritedApi(roomId);
      
      if (res.code === 200 && res.data) {
        const isFavoritedStatus = res.data.is_favorited;
        
        // 同步到本地状态
        if (isFavoritedStatus) {
          favoriteRoomIds.value.add(roomId);
        } else {
          favoriteRoomIds.value.delete(roomId);
        }
        
        console.log('[FavoriteStore] 直播间收藏状态:', isFavoritedStatus ? '已收藏' : '未收藏');
        return isFavoritedStatus;
      }
      
      return false;
    } catch (error: any) {
      // 401/403 表示未登录，返回false
      if (error.statusCode === 401 || error.statusCode === 403) {
        console.log('[FavoriteStore] 未登录，默认未收藏');
        return false;
      }
      
      console.error('[FavoriteStore] 检查收藏状态失败:', error);
      // 出错时使用本地缓存状态
      return favoriteRoomIds.value.has(roomId);
    }
  }
  
  /**
   * 添加收藏（带请求锁保护，防止重复收藏）
   * @param roomId 直播间ID
   */
  async function addFavorite(roomId: string) {
    // 检查是否有正在进行的收藏请求
    if (favoriteRequestLock.isLocked()) {
      console.warn('⚠️ 收藏请求进行中，请稍候...');
      uni.showToast({
        title: '请求进行中，请稍候',
        icon: 'none',
        duration: 1500
      });
      return;
    }
    
    return await favoriteRequestLock.execute(async () => {
      try {
        console.log('[FavoriteStore] 添加收藏:', roomId);
      
      // 调用API
      const res = await addFavoriteApi({ room_id: roomId });
      
      // 更新Store
      favoriteRoomIds.value.add(roomId);
      
      // 如果有完整数据，也添加到列表中
      if (res.data) {
        favoriteList.value.unshift(res.data as any);
      }
      
      console.log('[FavoriteStore] 收藏成功');
    } catch (error: any) {
      console.error('[FavoriteStore] 收藏失败:', error);
      
      // ===== 关键修复：正确处理错误码 =====
      // 4001: 已收藏该直播间（后端返回的实际错误码）
      if (error.code === 4001 || error.message?.includes('已收藏')) {
        // 已收藏，同步本地状态
        favoriteRoomIds.value.add(roomId);
        console.log('[FavoriteStore] 检测到已收藏，同步状态');
        // 不抛出错误，让调用方显示成功提示
        return;
      }
      
      // ===== 500错误特殊处理：可能实际收藏成功了 =====
      if (error.statusCode === 500 || error.code === 1002) {
        console.warn('[FavoriteStore] 500错误，延迟后重新加载收藏列表验证');
        // 乐观更新：先添加到本地状态
        favoriteRoomIds.value.add(roomId);
        
        // 延迟1秒后重新加载收藏列表，验证是否真的收藏成功
        setTimeout(async () => {
          try {
            await loadFavorites(true); // 强制刷新
            console.log('[FavoriteStore] 收藏状态已验证');
          } catch (e) {
            console.error('[FavoriteStore] 验证收藏状态失败:', e);
          }
        }, 1000);
        
        // 不抛出错误，让用户体验更好
        return;
      }
      
      throw error;
    }
    });
  }
  
  /**
   * 取消收藏（带请求锁保护，防止重复取消）
   * @param roomId 直播间ID
   */
  async function removeFavorite(roomId: string) {
    // 检查是否有正在进行的取消收藏请求
    if (unfavoriteRequestLock.isLocked()) {
      console.warn('⚠️ 取消收藏请求进行中，请稍候...');
      uni.showToast({
        title: '请求进行中，请稍候',
        icon: 'none',
        duration: 1500
      });
      return;
    }
    
    return await unfavoriteRequestLock.execute(async () => {
      try {
        console.log('[FavoriteStore] 取消收藏:', roomId);
      
      // 调用API
      await removeFavoriteApi(roomId);
      
      // 更新Store
      favoriteRoomIds.value.delete(roomId);
      
      // 从列表中移除
      favoriteList.value = favoriteList.value.filter(item => item.room_id !== roomId);
      
      console.log('[FavoriteStore] 取消收藏成功');
    } catch (error) {
      console.error('[FavoriteStore] 取消收藏失败:', error);
      throw error;
    }
    });
  }
  
  /**
   * 清空Store（用户登出时调用）
   */
  function clear() {
    favoriteRoomIds.value.clear();
    favoriteList.value = [];
    loaded.value = false;
    console.log('[FavoriteStore] Store已清空');
  }
  
  // ========== 返回 ==========
  
  return {
    // 状态
    favoriteRoomIds,
    favoriteList,
    loading,
    loaded,
    
    // 计算属性
    favoriteCount,
    
    // 方法
    loadFavorites,
    isFavorited,
    checkIsFavoritedFromApi,
    addFavorite,
    removeFavorite,
    clear,
  };
});
