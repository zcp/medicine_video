/**
 * 关注Store
 * 管理用户的关注状态，减少API请求
 */

import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { 
  getFollowedExperts, 
  followExpert as followExpertApi, 
  unfollowExpert as unfollowExpertApi,
  checkIsFollowed as checkIsFollowedApi
} from '@/api/expertFollow';
import { resolveMediaUrl } from '@/utils/url';
import { loadImagesWithProxy } from '@/utils/imageProxy';
import { DEFAULT_AVATAR } from '@/constants/assets';
import type { FollowedExpertItem } from '@/types/expertFollow';

export const useFollowStore = defineStore('follow', () => {
  // ========== 状态 ==========
  
  /** 关注的专家ID集合（用于快速查询） */
  const followedExpertIds = ref<Set<string>>(new Set());
  
  /** 完整的关注列表（用于关注列表页显示） */
  const followedList = ref<FollowedExpertItem[]>([]);
  
  /** 是否正在加载 */
  const loading = ref(false);
  
  /** 是否已加载过（避免重复加载） */
  const loaded = ref(false);
  
  // ========== 计算属性 ==========
  
  /** 关注数量 */
  const followCount = computed(() => followedExpertIds.value.size);
  
  // ========== 方法 ==========
  
  /**
   * 加载关注列表
   * @param force 是否强制刷新（忽略缓存）
   */
  async function loadFollowedExperts(force: boolean = false) {
    // 如果已加载且不强制刷新，则跳过
    if (loaded.value && !force) {
      console.log('[FollowStore] 使用缓存数据');
      return;
    }
    
    if (loading.value) {
      console.log('[FollowStore] 正在加载中，跳过');
      return;
    }
    
    loading.value = true;
    
    try {
      console.log('[FollowStore] 开始加载关注列表');
      
      // 获取所有关注（包含直播状态）
      const res = await getFollowedExperts(true);
      const items = res.data || [];
      
      // 处理头像URL：先标准化，再走代理（外链在APP端更稳定）
      const normalizedAvatarUrls = items.map((item) => {
        return resolveMediaUrl(item.avatar_url) || item.avatar_url || '';
      });
      const proxiedAvatarUrls = await loadImagesWithProxy(normalizedAvatarUrls, 3);

      const processedItems = items.map((item, index) => ({
        ...item,
        avatar_url: proxiedAvatarUrls[index] || normalizedAvatarUrls[index] || DEFAULT_AVATAR
      }));
      
      // 更新关注列表
      followedList.value = processedItems;
      
      // 更新ID集合（用于快速查询）
      followedExpertIds.value = new Set(items.map(item => item.expert_id));
      
      // 标记已加载
      loaded.value = true;
      
      console.log('[FollowStore] 关注列表加载完成:', items.length, '个');
    } catch (error) {
      console.error('[FollowStore] 加载关注列表失败:', error);
      throw error;
    } finally {
      loading.value = false;
    }
  }
  
  /**
   * 检查是否已关注某个专家
   * @param expertId 专家ID
   * @returns 是否已关注
   */
  function isFollowed(expertId: string): boolean {
    return followedExpertIds.value.has(expertId);
  }
  
  /**
   * 从API检查是否已关注指定专家（单次查询，不依赖列表加载）
   * @param expertId 专家ID
   * @returns Promise<boolean>
   * @description 调用 GET /api/v1/experts/{expert_id}/is-followed
   */
  async function checkIsFollowedFromApi(expertId: string): Promise<boolean> {
    try {
      console.log('[FollowStore] 检查专家关注状态:', expertId.substring(0, 8));
      const res = await checkIsFollowedApi(expertId);
      
      if (res.code === 200 && res.data) {
        const isFollowedStatus = res.data.is_followed;
        
        // 同步到本地状态
        if (isFollowedStatus) {
          followedExpertIds.value.add(expertId);
        } else {
          followedExpertIds.value.delete(expertId);
        }
        
        console.log('[FollowStore] 专家关注状态:', isFollowedStatus ? '已关注' : '未关注');
        return isFollowedStatus;
      }
      
      return false;
    } catch (error: any) {
      // 401/403 表示未登录，返回false
      if (error.statusCode === 401 || error.statusCode === 403) {
        console.log('[FollowStore] 未登录，默认未关注');
        return false;
      }
      
      console.error('[FollowStore] 检查关注状态失败:', error);
      // 出错时使用本地缓存状态
      return followedExpertIds.value.has(expertId);
    }
  }
  
  /**
   * 关注专家
   * @param expertId 专家ID
   */
  async function followExpert(expertId: string) {
    try {
      console.log('[FollowStore] 关注专家:', expertId);
      
      // 调用API
      await followExpertApi({ expert_id: expertId });
      
      // 更新Store
      followedExpertIds.value.add(expertId);
      
      console.log('[FollowStore] 关注成功');
    } catch (error: any) {
      console.error('[FollowStore] 关注失败:', error);
      
      // 如果是已关注错误，也更新Store
      if (error.code === 2002) {
        followedExpertIds.value.add(expertId);
      }
      
      throw error;
    }
  }
  
  /**
   * 取消关注专家
   * @param expertId 专家ID
   */
  async function unfollowExpert(expertId: string) {
    try {
      console.log('[FollowStore] 取消关注:', expertId);
      
      // 调用API
      await unfollowExpertApi(expertId);
      
      // 更新Store
      followedExpertIds.value.delete(expertId);
      
      // 从列表中移除
      followedList.value = followedList.value.filter(item => item.expert_id !== expertId);
      
      console.log('[FollowStore] 取消关注成功');
    } catch (error) {
      console.error('[FollowStore] 取消关注失败:', error);
      throw error;
    }
  }
  
  /**
   * 清空Store（用户登出时调用）
   */
  function clear() {
    followedExpertIds.value.clear();
    followedList.value = [];
    loaded.value = false;
    console.log('[FollowStore] Store已清空');
  }
  
  // ========== 返回 ==========
  
  return {
    // 状态
    followedExpertIds,
    followedList,
    loading,
    loaded,
    
    // 计算属性
    followCount,
    
    // 方法
    loadFollowedExperts,
    isFollowed,
    checkIsFollowedFromApi,
    followExpert,
    unfollowExpert,
    clear
  };
});
