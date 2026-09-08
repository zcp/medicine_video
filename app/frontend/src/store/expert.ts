/**
 * 专家Store
 * @description 管理专家列表、详情、场次数据
 */

import { defineStore } from 'pinia';
import { getFeaturedExperts, getExpertById, getExpertFollowerCount, getExpertSessions, getExperts } from '@/api/expert';
import { resolveMediaUrl } from '@/utils/url';

/**
 * 专家信息
 */
export interface Expert {
  id: string;
  name: string;
  avatar: string;
  title: string;
  hospital?: string;
  department_name?: string;
  department_id?: string;
  category_name?: string;
  bio?: string;
  specialization?: string[];
  stats: {
    followers: number;
    sessions: number;
  };
}

/**
 * 专家场次
 */
export interface ExpertSession {
  id: string;
  roomId?: string;
  title: string;
  cover: string;
  status: 'scheduled' | 'live' | 'ended';
  scheduledAt?: string;
  viewers?: number;
  role?: string; // 专家角色：host(主持人)、speaker(演讲嘉宾)、guest(特邀嘉宾)
}

/**
 * 分页信息
 */
interface Pagination {
  page: number;
  pageSize: number;
  total: number;
  hasMore: boolean;
}

export const useExpertStore = defineStore('expert', {
  state: () => ({
    /** 专家列表 */
    list: [] as Expert[],
    /** 当前专家详情 */
    detail: null as Expert | null,
    /** 专家场次列表 */
    sessions: [] as ExpertSession[],
    /** 专家总场次数（从分页响应 total 获取） */
    sessionCount: 0,
    /** 列表加载状态 */
    loadingList: false,
    /** 详情加载状态 */
    loadingDetail: false,
    /** 场次加载状态 */
    loadingSessions: false,
    /** 错误信息 */
    error: null as null | { message: string },
    /** 分页信息 */
    pagination: {
      page: 1,
      pageSize: 20,
      total: 0,
      hasMore: true
    } as Pagination,
    /** 搜索关键词 */
    keyword: '',
    /** 科室筛选（前端按名称过滤，当无 categoryId 时生效） */
    specialty: '',
    /** 当前分类ID（来自真实分类API，有值时后端筛选优先） */
    currentCategoryId: null as string | null,
    /** 关注状态映射 */
    followingMap: {} as Record<string, boolean>,
    /** 关注操作中 */
    followPending: false
  }),

  actions: {
    /**
     * 获取专家列表
     */
    async fetchExperts(params?: {
      page?: number;
      pageSize?: number;
      keyword?: string;
      specialty?: string;
      hospital?: string;
    }) {
      this.loadingList = true;
      this.error = null;

      try {
        console.log('[ExpertStore] 开始获取专家列表:', params);
        
        const page = params?.page ?? 1;
        const pageSize = params?.pageSize ?? this.pagination.pageSize;
        const isFirstPage = page === 1;
        const finalKeyword = (params?.keyword ?? this.keyword).trim();
        const finalSpecialty = (params?.specialty ?? this.specialty).trim();

        // 直接调用公开专家列表 API，所有筛选交给后端
        const queryParams: Record<string, any> = { page, size: pageSize };
        if (this.currentCategoryId) queryParams.category_id = this.currentCategoryId;
        if (finalKeyword) queryParams.keyword = finalKeyword;
        if (params?.hospital) queryParams.hospital = params.hospital;

        const newRes = await getExperts(queryParams as any);
        if (newRes.code === 200 && newRes.data?.items) {
          const newItems = newRes.data.items.map(mapExpertFromApi);
          const existingIds = isFirstPage ? new Set<string>() : new Set(this.list.map(e => e.id));
          const deduped = isFirstPage ? newItems : newItems.filter(e => !existingIds.has(e.id));
          this.list = isFirstPage ? deduped : [...this.list, ...deduped];
          this.pagination = {
            page: newRes.data.page,
            pageSize: newRes.data.size,
            total: newRes.data.total,
            hasMore: this.list.length < newRes.data.total
          };
          console.log('[ExpertStore] 专家列表加载成功:', this.list.length, '/', this.pagination.total);
          return;
        }

        throw new Error(newRes.message || '获取专家失败');
      } catch (error: any) {
        console.error('[ExpertStore] 获取专家列表失败:', error);
        // 阶段5语义：按停用/不存在分类筛选 → 后端 400/4001，明确提示而非误判"加载失败"
        if (error?.data?.code === 4001 || error?.code === 4001) {
          this.error = { message: '该分类已停用或不存在，请更换筛选条件' };
        } else {
          this.error = { message: error?.message || '获取专家失败' };
        }
        this.list = isFirstPage ? [] : this.list;  // 仅首屏清空
      } finally {
        this.loadingList = false;
      }
    },

    /**
     * 获取专家详情
     */
    async fetchExpertById(id: string) {
      this.loadingDetail = true;
      this.error = null;

      try {
        console.log('[ExpertStore] 获取专家详情:', id);
        
        // 调用API获取专家详情
        const res = await getExpertById(id);
        
        if (res.code !== 200 || !res.data) {
          throw new Error(res.message || '获取专家详情失败');
        }

        const x = res.data;
        
        // 映射数据
        this.detail = {
          id: x.id,
          name: x.name,
          avatar: resolveMediaUrl(x.avatar_url) || '/static/default-avatar.png',
          title: x.title || '',
          hospital: x.hospital || undefined,
          department_name: x.department_name || undefined,
          department_id: x.department_id || undefined,
          category_name: x.category_name || undefined,
          bio: x.bio,
          specialization: (x.expertise_areas || '')
            .split(',')
            .map((s: string) => s.trim())
            .filter((s: string) => !!s),
          stats: {
            followers: 0,
            sessions: 0
          }
        };

        // 非阻塞获取粉丝数
        getExpertFollowerCount(id).then(r => {
          if (r.code === 200 && this.detail) {
            this.detail.stats.followers = r.data.follower_count;
          }
        }).catch(() => {});

        // 如果场次已提前加载，同步场次数
        if (this.sessionCount > 0 && this.detail) {
          this.detail.stats.sessions = this.sessionCount;
        }
        
        console.log('[ExpertStore] 专家详情加载成功');
      } catch (e: any) {
        this.error = { message: e?.message || '加载专家详情失败' };
        this.detail = null;
        console.error('[ExpertStore] 加载详情失败:', e);
      } finally {
        this.loadingDetail = false;
      }
    },

    /**
     * 获取专家的直播场次列表
     */
    async fetchExpertSessions(expertId: string) {
      this.loadingSessions = true;
      
      try {
        console.log('[ExpertStore] 获取专家场次列表:', expertId);
        
        // 调用API获取专家场次
        const res = await getExpertSessions(expertId, { page: 1, size: 50 });
        
        if (res.code !== 200 || !res.data) {
          throw new Error(res.message || '获取专家场次失败');
        }

        const sessionsData = res.data.sessions || {};
        const items = sessionsData.items || [];
        
        // 映射场次数据
        this.sessions = items.map((item: any) => {
          // 映射状态：scheduled(未开始) -> scheduled, live(直播中) -> live, ended(已结束) -> ended
          let status: 'scheduled' | 'live' | 'ended' = 'ended';
          if (item.status === 'scheduled' || item.status === 'upcoming') {
            status = 'scheduled';
          } else if (item.status === 'live' || item.status === 'streaming') {
            status = 'live';
          } else {
            status = 'ended';
          }
          
          return {
            id: item.id,
            roomId: item.room_id,
            title: item.room_title || '未命名直播',
            cover: resolveMediaUrl(item.cover_url) || '/static/默认封面.jpg',
            status,
            scheduledAt: item.start_time ? new Date(item.start_time).toLocaleString('zh-CN') : undefined,
            viewers: item.viewer_count || 0,
            role: item.role // 专家在该场次中的角色：host(主持人)、speaker(演讲嘉宾)、guest(特邀嘉宾)
          };
        });
        
        this.sessionCount = sessionsData.total || items.length;
        if (this.detail) {
          this.detail.stats.sessions = this.sessionCount;
        }

        console.log('[ExpertStore] 场次列表加载完成，共', this.sessions.length, '条');
      } catch (e: any) {
        console.error('[ExpertStore] 加载场次失败:', e);
        this.sessions = [];
      } finally {
        this.loadingSessions = false;
      }
    },

    /**
     * 重置Store
     */
    reset() {
      this.list = [];
      this.detail = null;
      this.sessions = [];
      this.sessionCount = 0;
      this.pagination = {
        page: 1,
        pageSize: 20,
        total: 0,
        hasMore: true
      };
      this.error = null;
      this.keyword = '';
      this.specialty = '';
      this.currentCategoryId = null;
      this.followingMap = {};
      this.followPending = false;
    }
  }
});

/**
 * 将后端专家对象映射为前端 Expert 接口（复用逻辑，避免 fetchExperts 中重复代码）
 */
function mapExpertFromApi(x: any): Expert {
  return {
    id: x.id,
    name: x.name,
    avatar: resolveMediaUrl(x.avatar_url) || '/static/default-avatar.png',
    title: x.title || '',
    hospital: x.hospital || undefined,
    department_name: x.department_name || undefined,
    department_id: x.department_id || undefined,
    category_name: x.category_name || undefined,
    bio: x.bio,
    specialization: (x.expertise_areas || '').split(',').map((s: string) => s.trim()).filter((s: string) => !!s),
    stats: { followers: 0, sessions: 0 }
  };
}
