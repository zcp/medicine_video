<template>
  <view class="room-list-page">
    <!-- 搜索栏（管理员全站 + 我的直播共用） -->
    <view v-if="pageMode === 'admin' || pageMode === 'manage'" class="admin-search-section">
      <view class="admin-search-row">
        <view class="app-search-field admin-search-field">
          <text class="admin-search-icon iconfont icon-search"></text>
          <input
            class="admin-search-input"
            v-model="adminSearchQuery"
            placeholder="搜索房间标题..."
            placeholder-class="admin-search-placeholder"
            confirm-type="search"
            @confirm="handleSearch"
          />
          <!-- 清除按钮（悬浮槽：absolute 不占布局 → 显隐零变化；v1.14 最终结构） -->
          <view class="search-clear-slot">
            <ClearButton v-if="adminSearchQuery" @clear="handleAdminClearSearch" />
          </view>
        </view>
        <view class="admin-search-btn" @tap="handleSearch">搜索</view>
      </view>
    </view>
    <!-- 可见性 Tab 栏（全部 / 公开 / 私密；管理员全站 + 我的直播共用） -->
    <view v-if="pageMode === 'admin' || pageMode === 'manage'" class="admin-tabs">
      <view
        class="admin-tab"
        :class="{ 'admin-tab--active': activeFilterPrivate === undefined }"
        @tap="onVisibilityTabChange(undefined)">全部</view>
      <view
        class="admin-tab"
        :class="{ 'admin-tab--active': activeFilterPrivate === false }"
        @tap="onVisibilityTabChange(false)">公开</view>
      <view
        class="admin-tab"
        :class="{ 'admin-tab--active': activeFilterPrivate === true }"
        @tap="onVisibilityTabChange(true)">私密</view>
    </view>
    <!-- 列表区域 -->
    <scroll-view 
      class="rooms-scroll" 
      scroll-y
      @scrolltolower="loadMore"
      :refresher-enabled="true"
      :refresher-triggered="isPullRefreshing"
      @refresherrefresh="onPullDownRefresh"
    >
      <!-- 直播卡片列表 -->
      <view 
        v-for="item in displayItems" 
        :key="item.id"
        class="live-card"
        @tap="handleCardClick(item)"
        @touchstart="handleTouchStart($event, item)"
        @touchmove="handleTouchMove"
        @touchend="handleTouchEnd(item)"
      >
        <!-- 左侧封面 -->
        <view class="card-cover">
          <image
            class="cover-image"
            :src="getCoverUrl(item)"
            mode="aspectFill"
            lazy-load
          />
          <!-- 状态标签（封面左上角）：today/live 用场次 status，manage/admin 用后端返回的 room_live_status -->
          <text v-if="getLiveStatus(item)" class="status-badge" :class="`status-${getLiveStatus(item)}`">{{ getLiveStatusText(item) }}</text>
        </view>
        
        <!-- 右侧信息 -->
        <view class="card-info">
          <!-- 标题（最多2行） -->
          <text class="card-title">{{ getSafeTitle(item) }}</text>
          
          <!-- 专家信息 -->
          <view v-if="item.isTodaySession" class="card-author">
            <image class="author-avatar" src="/static/default-avatar.png" mode="aspectFill" lazy-load />
            <view class="author-info">
              <text class="author-name">{{ item.expertName || '' }}</text>
            </view>
          </view>
          <view v-else-if="getExpertName(item)" class="card-author">
            <ProxyImage
              class="author-avatar"
              :src="getExpertAvatar(item) || ''"
              :fallback="'/static/default-avatar.png'"
              mode="aspectFill"
            />
            <view class="author-info">
              <text class="author-name">{{ getExpertName(item) }}<text v-if="getExpertTitle(item)"> | {{ getExpertTitle(item) }}</text></text>
              <text class="author-hospital">{{ getExpertHospital(item) }}</text>
            </view>
          </view>
          <!-- 无专家时：创建者兜底（后端聚合返回 user_name/user_avatar） -->
          <view v-else-if="getOwnerInfo(item)" class="card-author">
            <ProxyImage
              class="author-avatar"
              :src="getOwnerInfo(item)?.avatar || ''"
              :fallback="'/static/default-avatar.png'"
              mode="aspectFill"
            />
            <view class="author-info">
              <text class="author-name">{{ getOwnerInfo(item)?.name }}</text>
            </view>
          </view>
        </view>
        
        <!-- 房主信息（仅管理员全站模式；我的直播即本人，不显示） -->
        <view v-if="pageMode === 'admin'" class="card-admin-info">
          <view class="admin-owner-wrap">
            <ProxyImage
              v-if="item.user_avatar"
              :src="item.user_avatar"
              :fallback="'/static/default-avatar.png'"
              mode="aspectFill"
              class="admin-owner-avatar"
            />
            <image
              v-else
              class="admin-owner-avatar"
              src="/static/default-avatar.png"
              mode="aspectFill"
              lazy-load
            />
            <text class="admin-owner">{{ item.user_name || '未知' }}</text>
          </view>
        </view>
        <!-- 行内操作（管理员全站 + 我的直播共用；留言管理仅管理员） -->
        <view v-if="pageMode === 'admin' || pageMode === 'manage'" class="admin-card-actions">
          <view class="admin-action-btn" @tap.stop="handleAdminViewDetail(item)">
            <text class="admin-action-text">查看详情</text>
          </view>
          <view class="admin-action-btn" @tap.stop="handleAdminEdit(item)">
            <text class="admin-action-text">编辑</text>
          </view>
          <view class="admin-action-btn" @tap.stop="handleAdminManageTabs(item)">
            <text class="admin-action-text">Tab 管理</text>
          </view>
          <view v-if="pageMode === 'admin'" class="admin-action-btn" @tap.stop="handleAdminMessages(item)">
            <text class="admin-action-text">留言管理</text>
          </view>
          <view class="admin-action-btn admin-action-btn--danger" @tap.stop="handleAdminDelete(item)">
            <text class="admin-action-text">删除</text>
          </view>
        </view>
      </view>
      
      <!-- 加载更多状态 -->
      <view v-if="showLoadMoreIndicator" class="loading-more">
        <text>加载中...</text>
      </view>
      
      <!-- 没有更多 -->
      <view v-if="!hasMoreItems && displayItems.length > 0" class="no-more">
        <text>没有更多了</text>
      </view>
      
      <!-- 空状态 -->
      <view v-if="showEmptyState" class="empty-state">
        <text class="empty-icon iconfont" :class="emptyIcon"></text>
        <text class="empty-title">{{ emptyTitle }}</text>
        <text class="empty-desc">{{ emptyDesc }}</text>
      </view>
    </scroll-view>
    
    <!-- 编辑弹窗 -->
    <ModalDialog
      :visible="isEditModalVisible"
      title="编辑直播"
      confirmText="保存"
      :confirmLoading="isSubmitting"
      @update:visible="isEditModalVisible = $event"
      @confirm="handleConfirm"
      @cancel="closeModal"
    >
      <view class="form">
        <view class="form-group">
          <text class="form-label">标题</text>
          <input 
            class="form-input" 
            v-model="formModel.title" 
            placeholder="请输入直播标题" 
            placeholder-class="placeholder"
          />
        </view>
        <view class="form-group">
          <text class="form-label">简介</text>
          <textarea 
            class="form-textarea" 
            v-model="formModel.description" 
            placeholder="请输入直播简介（选填）" 
            placeholder-class="placeholder"
          />
        </view>
        <view class="form-group">
          <text class="form-label">开播时间</text>
          <input
            class="form-input"
            v-model="formModel.scheduled_start_time"
            placeholder="请输入开播时间，如 2025-07-23 10:00"
            placeholder-class="placeholder"
          />
        </view>
      </view>
    </ModalDialog>

    <!-- 管理员模式：编辑直播间内容弹窗（标题/简介/私密/封面 + 清空留言/删除） -->
    <ModalDialog
      v-if="isAdminEditModalVisible"
      :visible="isAdminEditModalVisible"
      title="编辑直播间内容"
      confirmText="保存"
      :confirmLoading="isAdminSubmitting"
      @update:visible="closeAdminEditModal"
      @confirm="handleAdminSave"
      @cancel="closeAdminEditModal"
    >
      <view class="form">
        <view class="form-group">
          <text class="form-label">标题 <text class="form-required">*</text></text>
          <input
            class="form-input"
            v-model="adminForm.title"
            placeholder="请输入直播间标题"
            placeholder-class="placeholder"
            maxlength="100"
          />
          <text v-if="adminFormErrors.title" class="form-error">{{ adminFormErrors.title }}</text>
        </view>
        <view class="form-group">
          <text class="form-label">简介</text>
          <textarea
            class="form-textarea"
            v-model="adminForm.description"
            placeholder="直播间简介（可选）"
            placeholder-class="placeholder"
            maxlength="500"
          />
        </view>
        <view class="form-group form-group--row">
          <text class="form-label">私密直播间</text>
          <switch :checked="adminForm.is_private" color="#0f766e" @change="onAdminPrivateChange" />
        </view>
        <text class="field-hint">私密房间仅授权用户可见；管理员列表仍可找到</text>

        <view class="form-group">
          <text class="form-label">封面</text>
          <view class="cover-row">
            <ProxyImage
              v-if="adminForm.cover_url"
              :src="adminForm.cover_url"
              :fallback="DEFAULT_AVATAR"
              mode="aspectFill"
              class="cover-preview-img"
            />
            <view v-else class="cover-placeholder">
              <text class="cover-placeholder-text">无封面</text>
            </view>
            <view class="cover-actions">
              <view class="action-chip" :class="{ disabled: isAdminUploadingCover }" @tap="handleAdminPickCover">
                <text class="chip-text">{{ isAdminUploadingCover ? '上传中...' : '换封面' }}</text>
              </view>
            </view>
          </view>
          <input
            class="form-input form-input--url"
            v-model="adminForm.cover_url"
            placeholder="或输入封面图片 URL"
            placeholder-class="placeholder"
          />
        </view>
      </view>
    </ModalDialog>
  </view>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue';
import { onLoad, onShow } from '@dcloudio/uni-app';
import { storeToRefs } from 'pinia';
import { useRoomStore } from '@/store/room';
import { useSessionStore } from '@/store/session';
import { useAuthStore } from '@/store/auth';
import { getSessionExperts } from '@/api/expert';
import { getSessionList } from '@/api/session';
import { getAdminRooms } from '@/api/room';
import { updateRoom, deleteRoom, uploadRoomCover, getRoomDetail } from '@/api/room';
import { clearRoomMessages } from '@/api/message';
import ModalDialog from '@/components/shared/ModalDialog.vue';
import ProxyImage from '@/components/common/ProxyImage.vue';
import ClearButton from '@/components/app/ClearButton.vue';
import type { Room } from '@/types/room';
import { BASE_API_URL } from '@/constants/api';
import { escapeHtml } from '@/utils/xss';
import { DEFAULT_AVATAR } from '@/constants/assets';

// Store 和数据
const roomStore = useRoomStore();
const sessionStore = useSessionStore();
const { rooms, loading, error, pagination } = storeToRefs(roomStore);

// ========== 页面模式（manage / admin） ==========
const pageMode = ref<'manage' | 'admin'>('manage');

/** 全站房间数据（admin 模式） */
const adminRooms = ref<any[]>([]);
const adminPagination = ref({ total: 0, page: 1, size: 20, hasMore: false });
const adminLoading = ref(false);
/** admin 加载期间到达的刷新请求标记（本轮结束后自动补跑） */
let pendingAdminRefresh = false;
/** manage 模式：加载中到达的刷新请求标记（本轮结束后自动补跑，替代静默丢弃） */
let pendingManageRefresh = false;

/** 管理员搜索与筛选 */
const adminSearchQuery = ref('');
const adminFilterPrivate = ref<boolean | undefined>(undefined);
/** 我的直播可见性筛选（前端过滤，数据源已含私密房；融合方案 F2） */
const manageFilterPrivate = ref<boolean | undefined>(undefined);

/** 当前模式生效的可见性筛选（pageMode 互斥，Tab 高亮共用） */
const activeFilterPrivate = computed(() =>
  pageMode.value === 'admin' ? adminFilterPrivate.value : manageFilterPrivate.value
);

/** 统一展示列表：管理模式取主房间（按可见性前端过滤），admin 模式取全站房间 */
const displayItems = computed(() => {
  if (pageMode.value === 'manage') {
    let list = mainRooms.value;
    if (manageFilterPrivate.value !== undefined) {
      list = list.filter(r => r.is_private === manageFilterPrivate.value);
    }
    return list;
  }
  return adminRooms.value;
});

/**
 * 可见性 Tab 点击（两种模式分发）
 * - admin：后端 is_private 参数筛选
 * - manage：前端过滤（数据已含私密房）
 */
function onVisibilityTabChange(v: boolean | undefined) {
  if (pageMode.value === 'admin') {
    adminFilterPrivate.value = v;
    handleAdminSearch();
  } else {
    manageFilterPrivate.value = v;
    loadRoomList(true);
  }
}

/** 搜索（两种模式分发） */
function handleSearch() {
  if (pageMode.value === 'admin') {
    handleAdminSearch();
  } else {
    loadRoomList(true);
  }
}

/**
 * 清除搜索关键词（接线：清空后复用 handleSearch 分发重新加载——admin 走 handleAdminSearch，manage 走 loadRoomList(true)）
 */
function handleAdminClearSearch() {
  adminSearchQuery.value = '';
  handleSearch();
}

// 计算主房间列表（排除分会场）
const mainRooms = computed(() => {
  return rooms.value.filter(room => !room.parent_room_id);
});

// 空状态/加载辅助 computed
const showEmptyState = computed(() => {
  const loading = pageMode.value === 'manage' ? isLoading.value : adminLoading.value;
  return displayItems.value.length === 0 && !loading;
});
const showLoadMoreIndicator = computed(() => {
  if (pageMode.value === 'manage') return isLoadingMore.value;
  return adminLoading.value && adminRooms.value.length > 0;
});
const hasMoreItems = computed(() => {
  if (pageMode.value === 'manage') return pagination.value.hasMore;
  return adminPagination.value.hasMore;
});
const emptyIcon = computed(() => {
  if (pageMode.value === 'manage') return 'icon-video';
  return 'icon-home';
});
const emptyTitle = computed(() => {
  if (pageMode.value === 'admin') return '暂无全站房间';
  return '暂无直播';
});
const emptyDesc = computed(() => {
  if (pageMode.value === 'admin') return '当前没有直播间数据';
  return '快去创建你的第一个直播吧';
});

// 优化：统一加载状态管理
const isLoading = ref(false);
const isLoadingMore = ref(false);
const loadError = ref<string | null>(null);

// 优化：请求重试配置
const MAX_RETRY_COUNT = 3;
const RETRY_DELAY = 1000; // 1秒

// 存储每个房间的专家信息
const roomExperts = ref<Record<string, any[]>>({});

// 长按检测相关状态
const longPressTimer = ref<number | null>(null);
const touchStartPos = ref({ x: 0, y: 0 });
const isTouchMoved = ref(false);
const LONG_PRESS_DURATION = 500; // 长按触发时间（毫秒）
const MOVE_THRESHOLD = 10; // 移动阈值（像素）

// 获取封面URL（简化版，不使用H5特定的fetch和blob）
// XSS防护：安全渲染标题
const getSafeTitle = (room: Room): string => {
  return escapeHtml(room.title || '直播标题');
};

const getCoverUrl = (room: Room) => {
  if (!room) return '/logo.png';
  const url = room.cover_url || '';
  if (!url) return '/logo.png';

  // 如果是完整URL，直接返回
  if (/^https?:\/\//.test(url)) return url;

  // 如果是相对路径，拼接BASE_API_URL
  const base = BASE_API_URL.replace(/\/+$/, '');
  const origin = base.replace(/\/api\/.*/, '');
  return origin + (url.startsWith('/') ? url : '/' + url);
};

/**
 * 获取直播间状态（用于状态标签）
 * @description 数据来源分两类：
 * - today/live 模式：场次数据自带 status
 * - manage/admin 模式：后端房间接口聚合返回的 room_live_status（代表场次状态）
 */
const getLiveStatus = (item: any): string => {
  if (item.isTodaySession) return item.status || '';
  return item.room_live_status || item.live_status || '';
};

/**
 * 状态标签文本（三态收敛，与全局卡片一致）
 */
const getLiveStatusText = (item: any): string => {
  const status = getLiveStatus(item);
  const map: Record<string, string> = {
    'live': '直播中',
    'scheduled': '预告',
    'ready': '回放',
    'error': '异常',
    'finished': '已结束',
    'processing': '回放生成中',
  };
  return map[status] || '未开播';
};

// 优化：统一错误处理函数（带安全过滤）
const handleError = (error: any, context: string) => {
  console.error(`❌ ${context}失败:`, error);
  
  // 生产环境过滤敏感错误信息
  let message: string;
  if (process.env.NODE_ENV === 'production') {
    message = `${context}失败，请稍后重试`;
  } else {
    message = error?.message || error?.data?.message || `${context}失败，请重试`;
  }
  
  loadError.value = message;
  
  uni.showToast({
    title: message,
    icon: 'none',
    duration: 2000
  });
};

// 优化：带重试的请求包装函数
const withRetry = async <T>(
  fn: () => Promise<T>,
  context: string,
  retryCount = 0
): Promise<T | null> => {
  try {
    return await fn();
  } catch (error: any) {
    if (retryCount < MAX_RETRY_COUNT) {
      console.log(`⚠️ ${context}失败，${RETRY_DELAY}ms后重试 (${retryCount + 1}/${MAX_RETRY_COUNT})`);
      await new Promise(resolve => setTimeout(resolve, RETRY_DELAY));
      return withRetry(fn, context, retryCount + 1);
    }
    handleError(error, context);
    return null;
  }
};

// 优化：加载房间列表（带加载状态和错误处理）
const loadRoomList = async (refresh = false) => {
  if (pageMode.value === 'admin') {
    await loadAdminRooms(refresh);
    return;
  }
  // 加载中到达的刷新请求：标记补跑，本轮结束后自动执行（不再静默丢弃——下拉/搜索/切可见性不被吞）
  if (isLoading.value || isLoadingMore.value) {
    if (refresh) pendingManageRefresh = true;
    return;
  }
  
  isLoading.value = true;
  loadError.value = null;
  
  try {
    await withRetry(
      () => roomStore.fetchRooms({ refresh, ownerOnly: true, q: adminSearchQuery.value || undefined }),
      '加载房间列表'
    );
    
    // 加载成功后获取专家信息
    await fetchAllRoomExperts();
  } finally {
    isLoading.value = false;
    // 加载期间到达的刷新请求：补跑一次（合并连续触发）
    if (pendingManageRefresh) {
      pendingManageRefresh = false;
      await loadRoomList(true);
    }
  }
};

/** 加载全站房间列表（admin 模式） */
const loadAdminRooms = async (refresh = false) => {
  if (adminLoading.value) {
    // 加载中到达的刷新请求：标记补跑，本轮结束后自动执行（避免吞掉 Tab/搜索刷新）
    if (refresh) pendingAdminRefresh = true;
    return;
  }
  adminLoading.value = true;
  try {
    const page = refresh ? 1 : adminPagination.value.page;
    const params: Record<string, any> = { page, size: adminPagination.value.size };
    if (adminSearchQuery.value) params.q = adminSearchQuery.value;
    if (adminFilterPrivate.value !== undefined) params.is_private = adminFilterPrivate.value;
    const res = await getAdminRooms(params);
    if (res.code === 200) {
      const items = res.data.items || [];
      const serverSize = res.data.size || adminPagination.value.size;
      let total = res.data.total || 0;

      if (refresh) {
        adminRooms.value = items;
        // 空结果但 total>0（服务端口径不一致）→ 截断，避免空列表循环加载
        if (items.length === 0 && total > 0) total = 0;
      } else {
        // 去重追加：防止后端分页不稳导致重复数据无限增长
        const existingIds = new Set(adminRooms.value.map((r: any) => r.id));
        const newItems = items.filter((r: any) => !existingIds.has(r.id));
        adminRooms.value = [...adminRooms.value, ...newItems];
        // 本页全重复或为空 → 以实际列表长度为准，终止继续加载
        if (newItems.length < items.length || items.length === 0) {
          total = adminRooms.value.length;
        }
      }

      // 成功后才推进页码（失败保持原页码，滚动重试不跳页）；hasMore 按已加载页判断
      adminPagination.value = {
        total,
        page: page + 1,
        size: serverSize,
        hasMore: page * serverSize < total,
      };

      // 异步加载专家信息（分批并发，控制请求量）
      if (items.length > 0) {
        void fetchRoomExpertsBatch(items);
      }
    }
  } catch (error) {
    console.error('加载全站房间失败:', error);
  } finally {
    adminLoading.value = false;
    // 加载期间到达的刷新请求：补跑一次（合并连续触发）
    if (pendingAdminRefresh) {
      pendingAdminRefresh = false;
      await loadAdminRooms(true);
    }
  }
};

/** 管理员搜索/筛选后刷新 */
const handleAdminSearch = () => {
  adminPagination.value.page = 1;
  loadAdminRooms(true);
};

// 优化：加载更多（分页）
const loadMore = async () => {
  if (pageMode.value === 'admin') {
    if (!adminPagination.value.hasMore || adminLoading.value) return;
    await loadAdminRooms(false);
    return;
  }
  if (pageMode.value !== 'manage') return;
  if (isLoadingMore.value || !pagination.value.hasMore || isLoading.value || displayItems.value.length === 0) {
    return;
  }
  
  isLoadingMore.value = true;
  
  try {
    await withRetry(
      () => roomStore.fetchRooms({ refresh: false, ownerOnly: true }),
      '加载更多'
    );
    
    // 加载新房间的专家信息
    await fetchAllRoomExperts();
  } finally {
    isLoadingMore.value = false;
  }
};

/**
 * 页面生命周期
 */
onLoad((options?: any) => {
  const authStore = useAuthStore();
  const mode = options?.mode;
  
  // 管理员全站房间模式：mode=admin 显式直达；管理员裸链/无栈 fallback（detail 无栈返回、遗留分享路径等）
  // 也强制转全站房间（Phase3 兜底），避免落入"我的直播"owner 空态引导创建
  if (mode === 'admin' || authStore.isAdmin) {
    if (!authStore.isAdmin) {
      uni.showToast({ title: '权限不足', icon: 'none' });
      uni.navigateBack();
      return;
    }
    pageMode.value = 'admin';
    uni.setNavigationBarTitle({ title: '全站房间' });
    loadAdminRooms(true);
    return;
  }
  
  console.log('🚀 RoomList页面加载');
  
  if (authStore.isAuthenticated) {
    console.log('✅ 用户已认证，加载房间列表');
    loadRoomList(true);
  } else {
    console.log('❌ 用户未认证');
    uni.showToast({ title: '请先登录', icon: 'none' });
    uni.navigateBack({
      fail: () => { uni.switchTab({ url: '/pages/app/tabbar/home/index' }); }
    });
  }
});

// 页面显示时刷新（从编辑页/详情页返回后同步数据；onLoad 已加载过，此处静默刷新）
onShow(() => {
  const authStore = useAuthStore();
  if (!authStore.isAuthenticated) return;
  if (pageMode.value === 'manage') {
    loadRoomList(true);
  }
});

/** 下拉刷新最小展示时长（ms）：请求过快时保证指示器可感知 */
const PULL_REFRESH_MIN_MS = 400;
const isPullRefreshing = ref(false);
let pullRefreshStartTime = 0;

// 优化：下拉刷新（使用scroll-view的refresher）
const onPullDownRefresh = async () => {
  if (isPullRefreshing.value) return;
  isPullRefreshing.value = true;
  pullRefreshStartTime = Date.now();
  try {
    if (pageMode.value === 'admin') {
      await loadAdminRooms(true);
    } else {
      await loadRoomList(true);
    }
  } finally {
    // 最短展示时长：请求过快时补足，保证"正在刷新"可感知
    const elapsed = Date.now() - pullRefreshStartTime;
    if (elapsed < PULL_REFRESH_MIN_MS) {
      await new Promise(resolve => setTimeout(resolve, PULL_REFRESH_MIN_MS - elapsed));
    }
    isPullRefreshing.value = false;
  }
};

// 优化：触底加载更多（防抖）


// 跳转到房间详情页
const goToRoomDetail = (roomId: string) => {
  uni.navigateTo({ url: `/pages/app/live-manage/detail?id=${roomId}` });
};

/**
 * 点击卡片跳转到播放页面（带安全检查和加载状态）
 */
const handleCardClick = async (item: any) => {
  // 今日场次模式：已有 sessionId，直接跳转
  if (item.isTodaySession) {
    const sessionId = item.id;
    if (!sessionId) {
      uni.showToast({ title: '无效的场次信息', icon: 'none' });
      return;
    }
    uni.navigateTo({
      url: `/pages/app/live/LiveView?sessionId=${encodeURIComponent(sessionId)}`,
    });
    return;
  }
  
  const room = item;
  // 安全检查：验证room对象和ID
  if (!room || !room.id || typeof room.id !== 'string') {
    console.error('无效的房间数据:', room);
    uni.showToast({ title: '无效的直播信息', icon: 'none' });
    return;
  }
  
  // 显示加载状态
  uni.showLoading({ title: '加载中...', mask: true });
  
  try {
    // 获取房间的场次列表
    await sessionStore.fetchSessionsByRoomId(room.id, { refresh: true });
    
    // 立即读取 store 中的数据（在被其他请求覆盖之前）
    const sessions = [...sessionStore.sessions]; // 创建副本，避免引用被修改
    
    console.log('🔍 获取到的场次数据:', {
      roomId: room.id,
      roomTitle: room.title,
      sessionsCount: sessions.length,
      firstSessionId: sessions[0]?.id,
      allSessionIds: sessions.map(s => s.id)
    });
    
    // 检查场次是否存在
    if (!sessions || sessions.length === 0) {
      uni.hideLoading();
      uni.showToast({ 
        title: '该直播暂无场次，请先创建场次', 
        icon: 'none',
        duration: 2000
      });
      return;
    }
    
    // 获取第一个场次
    const firstSession = sessions[0];
    
    // 安全检查：验证场次ID
    if (!firstSession.id || typeof firstSession.id !== 'string') {
      uni.hideLoading();
      console.error('无效的场次数据:', firstSession);
      uni.showToast({ title: '无效的场次信息', icon: 'none' });
      return;
    }
    
    // 验证场次是否属于当前房间
    if (firstSession.room_id !== room.id) {
      uni.hideLoading();
      console.error('场次房间ID不匹配:', {
        expectedRoomId: room.id,
        actualRoomId: firstSession.room_id,
        sessionId: firstSession.id
      });
      uni.showToast({ title: '数据异常，请重试', icon: 'none' });
      return;
    }
    
    // XSS防护：转义sessionId
    const safeSessionId = encodeURIComponent(firstSession.id);
    
    uni.hideLoading();
    
    // 跳转到播放页面
    console.log('✅ 准备跳转到播放页面:', {
      roomId: room.id,
      roomTitle: room.title,
      sessionId: firstSession.id,
      sessionRoomId: firstSession.room_id,
      sessionTitle: firstSession.title || '未知标题'
    });
    
    uni.navigateTo({
      url: `/pages/app/live/LiveView?sessionId=${safeSessionId}`,
      success: () => {
        console.log('✅ 跳转成功，直接进入播放页面');
      },
      fail: (err) => {
        console.error('❌ 跳转失败:', err);
        uni.showToast({ title: '跳转失败，请重试', icon: 'none' });
      }
    });
  } catch (error) {
    uni.hideLoading();
    console.error('❌ 加载场次失败:', error);
    uni.showToast({ 
      title: '加载失败，请稍后重试', 
      icon: 'none',
      duration: 2000
    });
  }
};

/**
 * 触摸开始 - 记录初始位置并启动长按计时器
 */
const handleTouchStart = (event: any, room: any) => {
  // 记录触摸起始位置
  const touch = event.touches[0];
  touchStartPos.value = { x: touch.clientX, y: touch.clientY };
  isTouchMoved.value = false;
  
  // 清除之前的计时器
  if (longPressTimer.value) {
    clearTimeout(longPressTimer.value);
  }
  
  // 启动长按计时器
  longPressTimer.value = setTimeout(() => {
    // 只有在没有移动的情况下才触发长按
    if (!isTouchMoved.value) {
      console.log('长按房间:', room.title);
      uni.vibrateShort({ type: 'medium' });
      handleMoreAction(room);
    }
  }, LONG_PRESS_DURATION) as unknown as number;
};

/**
 * 触摸移动 - 检测是否移动超过阈值
 */
const handleTouchMove = (event: any) => {
  const touch = event.touches[0];
  const deltaX = Math.abs(touch.clientX - touchStartPos.value.x);
  const deltaY = Math.abs(touch.clientY - touchStartPos.value.y);
  
  // 如果移动距离超过阈值，标记为已移动并取消长按
  if (deltaX > MOVE_THRESHOLD || deltaY > MOVE_THRESHOLD) {
    isTouchMoved.value = true;
    if (longPressTimer.value) {
      clearTimeout(longPressTimer.value);
      longPressTimer.value = null;
    }
  }
};

/**
 * 触摸结束 - 清理计时器
 */
const handleTouchEnd = (room: any) => {
  // 清除长按计时器
  if (longPressTimer.value) {
    clearTimeout(longPressTimer.value);
    longPressTimer.value = null;
  }
};

/**
 * 更多操作菜单
 */
const handleMoreAction = (room: any) => {
  if (pageMode.value !== 'manage') return;
  uni.showActionSheet({
    itemList: ['编辑', '删除', '查看详情'],
    success: (res) => {
      if (res.tapIndex === 0) {
        handleEdit(room);
      } else if (res.tapIndex === 1) {
        handleDelete(room);
      } else if (res.tapIndex === 2) {
        handleDetail(room);
      }
    }
  });
};

/**
 * 打开编辑弹窗
 */
const isEditModalVisible = ref(false);
const isSubmitting = ref(false);
const formModel = reactive({
  id: null as string | null,
  title: '',
  description: '',
  scheduled_start_time: ''
});

const handleEdit = (room: any) => {
  // 跳转到编辑页面
  uni.navigateTo({
    url: `/pages/app/live-manage/edit?roomId=${room.id}`
  });
};

/**
 * 处理删除
 */
const handleDelete = (room: any) => {
  uni.showModal({
    title: '确认删除',
    content: `确定要删除直播间"${room.title}"吗？此操作不可恢复。`,
    success: async (res) => {
      if (res.confirm) {
        uni.showLoading({ title: '删除中...', mask: true });
        try {
          await withRetry(
            () => roomStore.deleteRoom(room.id),
            '删除房间'
          );
          uni.hideLoading();
          uni.showToast({
            title: '删除成功',
            icon: 'success'
          });
          await loadRoomList(true);
        } catch (error) {
          uni.hideLoading();
        }
      }
    }
  });
};

/**
 * 处理查看详情
 */
const handleDetail = (room: any) => {
  goToRoomDetail(room.id);
};

/**
 * 获取专家头像（有真实数据显示真实数据，没有则返回空）
 */
const getExpertAvatar = (room: any): string => {
  const experts = roomExperts.value[room.id];
  if (experts && experts.length > 0 && experts[0].avatar_url) {
    return experts[0].avatar_url;
  }
  return '';
};

/**
 * 获取专家显示名称（后端真实数据，无专家返回空）
 */
const getExpertName = (room: any): string => {
  const experts = roomExperts.value[room.id];
  if (experts && experts.length > 0 && experts[0].name) {
    return experts[0].name;
  }
  return '';
};

/**
 * 获取专家职称（后端真实数据，无职称返回空）
 */
const getExpertTitle = (room: any): string => {
  const experts = roomExperts.value[room.id];
  if (experts && experts.length > 0 && experts[0].title) {
    return experts[0].title;
  }
  return '';
};

/**
 * 获取专家医院信息（后端真实数据，无医院返回空）
 */
const getExpertHospital = (room: any): string => {
  const experts = roomExperts.value[room.id];
  if (experts && experts.length > 0 && experts[0].hospital) {
    return experts[0].hospital;
  }
  return '';
};

/**
 * 获取创建者兜底信息（无专家时显示）
 * @description 数据来自后端房间接口聚合返回的 user_name/user_avatar（include_owner=True）
 * 无专家且无创建者信息时返回 null，模板不渲染
 */
const getOwnerInfo = (room: any): { name: string; avatar: string } | null => {
  const name = room?.user_name || '';
  if (!name) return null;
  return {
    name,
    avatar: room?.user_avatar || ''
  };
};

/**
 * 获取房间的专家信息
 * 修复：直接使用 API 返回值，避免全局 store 数据混乱
 */
const fetchRoomExperts = async (roomId: string) => {
  try {
    // 直接调用 API 获取场次列表，不依赖全局 store
    const sessionsResponse: any = await getSessionList(roomId, { page: 1, size: 1 }, { showLoading: false });
    
    // 处理不同的响应格式
    const sessions = sessionsResponse.data?.items || 
                    sessionsResponse.items || 
                    sessionsResponse.data || 
                    [];
    
    if (sessions && sessions.length > 0) {
      const sessionId = sessions[0].id;
      const response = await getSessionExperts(sessionId, undefined, { showLoading: false });
      
      // 处理不同的响应格式
      const expertsData = response.data || response;
      
      if (expertsData && Array.isArray(expertsData) && expertsData.length > 0) {
        roomExperts.value[roomId] = expertsData;
        console.log(`✅ 房间 ${roomId} 的专家信息:`, expertsData[0].name);
      } else {
        console.log(`⚠️ 房间 ${roomId} 没有专家信息，将使用Mock数据`);
      }
    } else {
      console.log(`⚠️ 房间 ${roomId} 没有场次，将使用Mock数据`);
    }
  } catch (error) {
    console.warn(`⚠️ 获取房间 ${roomId} 的专家信息失败，将使用Mock数据:`, error);
  }
};

/**
 * 批量获取房间的专家信息（分批并发，控制请求量，避免 N×2 请求风暴）
 * @param items 房间列表
 * @param batchSize 每批并发数，默认 5
 */
const fetchRoomExpertsBatch = async (items: any[], batchSize = 5) => {
  for (let i = 0; i < items.length; i += batchSize) {
    const batch = items.slice(i, i + batchSize);
    await Promise.allSettled(batch.map((r: any) => fetchRoomExperts(r.id)));
  }
};

/**
 * 批量获取所有房间的专家信息
 */
const fetchAllRoomExperts = async () => {
  await fetchRoomExpertsBatch(mainRooms.value);
};

/**
 * 关闭编辑弹窗
 */
const closeModal = () => {
  isEditModalVisible.value = false;
  formModel.id = null;
  formModel.title = '';
  formModel.description = '';
  formModel.scheduled_start_time = '';
};

/**
 * 表单验证
 */
const validateForm = (): boolean => {
  if (!formModel.title || !formModel.title.trim()) {
    uni.showToast({ title: '请输入直播标题', icon: 'none' });
    return false;
  }
  return true;
};

/**
 * 提交编辑表单
 */
const handleConfirm = async () => {
  if (!validateForm()) {
    return;
  }
  
  isSubmitting.value = true;
  
  try {
    // 更新房间信息
    const payload = {
      title: formModel.title,
      description: formModel.description || undefined,
    };

    if (formModel.id) {
      await withRetry(
        () => roomStore.updateRoom(formModel.id!, payload),
        '更新房间信息'
      );
      
      // 如果有开播时间，更新场次信息
      if (formModel.scheduled_start_time) {
        try {
          await sessionStore.fetchSessionsByRoomId(formModel.id);
          const sessions = sessionStore.sessions;
          if (sessions && sessions.length > 0) {
            await sessionStore.updateSession(sessions[0].id, {
              scheduled_start_time: new Date(formModel.scheduled_start_time).toISOString()
            });
          }
        } catch (error) {
          console.warn('更新场次时间失败:', error);
        }
      }
      
      uni.showToast({ title: '更新成功', icon: 'success' });
    }

    closeModal();
    await loadRoomList(true);
  } finally {
    isSubmitting.value = false;
  }
};

// ================= 管理员模式：编辑直播间内容 =================
const isAdminEditModalVisible = ref(false);
const isAdminSubmitting = ref(false);
const isAdminUploadingCover = ref(false);
const adminEditingRoom = ref<any>(null);
const adminForm = reactive({
  title: '',
  description: '',
  is_private: false,
  cover_url: '',
});
const adminFormErrors = reactive<{ title: string }>({ title: '' });

function openAdminEditModal(room: any) {
  adminEditingRoom.value = room;
  adminFormErrors.title = '';
  isAdminEditModalVisible.value = true;
  void loadAdminRoomDetail(room.id);
}

function closeAdminEditModal() {
  if (isAdminSubmitting.value || isAdminUploadingCover.value) return;
  isAdminEditModalVisible.value = false;
  adminEditingRoom.value = null;
}

/** 打开弹窗时拉取详情回填（列表字段可能截断/缺失） */
async function loadAdminRoomDetail(roomId: string) {
  try {
    const res = await getRoomDetail(roomId);
    if (res.code === 200 && res.data) {
      const r: any = res.data;
      adminForm.title = String(r.title || '');
      adminForm.description = String(r.description || '');
      adminForm.is_private = Boolean(r.is_private);
      adminForm.cover_url = String(r.cover_url || '');
    } else {
      // 详情失败时用列表项兜底
      const item = adminEditingRoom.value;
      if (item) {
        adminForm.title = String(item.title || '');
        adminForm.description = String(item.description || '');
        adminForm.is_private = Boolean(item.is_private);
        adminForm.cover_url = String(item.cover_url || '');
      }
    }
  } catch (e) {
    const item = adminEditingRoom.value;
    if (item) {
      adminForm.title = String(item.title || '');
      adminForm.description = String(item.description || '');
      adminForm.is_private = Boolean(item.is_private);
      adminForm.cover_url = String(item.cover_url || '');
    }
  }
}

function onAdminPrivateChange(e: any) {
  adminForm.is_private = Boolean(e?.detail?.value);
}

/** 换封面（上传即更新后端 cover_url，表单回填） */
async function handleAdminPickCover() {
  if (isAdminUploadingCover.value || !adminEditingRoom.value?.id) return;
  const roomId = adminEditingRoom.value.id;
  const res = await new Promise<{ path: string }>((resolve) => {
    uni.chooseImage({
      count: 1,
      sizeType: ['compressed'],
      sourceType: ['album', 'camera'],
      success: (r) => resolve({ path: r.tempFilePaths?.[0] || '' }),
      fail: () => resolve({ path: '' }),
    });
  });
  if (!res.path) return;
  isAdminUploadingCover.value = true;
  try {
    const resp = await uploadRoomCover(roomId, res.path);
    if (resp.code === 200) {
      const url = String((resp.data as any)?.cover_url || '');
      if (url) adminForm.cover_url = url;
      uni.showToast({ title: '封面已更新', icon: 'success' });
    } else {
      uni.showToast({ title: resp.message || '封面上传失败', icon: 'none' });
    }
  } catch (e: any) {
    uni.showToast({ title: e?.data?.message || '封面上传失败', icon: 'none' });
  } finally {
    isAdminUploadingCover.value = false;
  }
}

function validateAdminForm(): boolean {
  adminFormErrors.title = '';
  const title = adminForm.title.trim();
  if (!title) {
    adminFormErrors.title = '请输入直播间标题';
    return false;
  }
  if (title.length > 100) {
    adminFormErrors.title = '标题不超过 100 个字符';
    return false;
  }
  return true;
}

/** 保存（标题/简介/私密） */
async function handleAdminSave() {
  if (isAdminSubmitting.value) return;
  if (!validateAdminForm()) return;
  const roomId = adminEditingRoom.value?.id;
  if (!roomId) return;
  isAdminSubmitting.value = true;
  try {
    const res = await updateRoom(roomId, {
      title: adminForm.title.trim(),
      description: adminForm.description.trim(),
      is_private: adminForm.is_private,
      cover_url: adminForm.cover_url || undefined,
    });
    if (res.code === 200) {
      uni.showToast({ title: '已保存', icon: 'success' });
      isAdminEditModalVisible.value = false;
      adminEditingRoom.value = null;
      await loadAdminRooms(true);
    } else if (res.code === 2005) {
      uni.showToast({ title: '内容违规，请修改后重试', icon: 'none' });
    } else {
      uni.showToast({ title: res.message || '保存失败', icon: 'none' });
    }
  } catch (e: any) {
    const code = e?.data?.code;
    if (code === 2005) {
      uni.showToast({ title: '内容违规，请修改后重试', icon: 'none' });
    } else {
      uni.showToast({ title: e?.data?.message || '保存失败，请稍后再试', icon: 'none' });
    }
  } finally {
    isAdminSubmitting.value = false;
  }
}

/** 清空留言（二次确认） */
function handleAdminClearMessages(room: any) {
  if (!room?.id) return;
  uni.showModal({
    title: '清空留言',
    content: `确定清空「${room.title || '该直播间'}」全部留言？此操作不可恢复。`,
    confirmText: '清空',
    confirmColor: '#dc2626',
    success: async (r) => {
      if (!r.confirm) return;
      try {
        const res = await clearRoomMessages(room.id);
        if (res.code === 200) {
          uni.showToast({ title: '已清空留言', icon: 'success' });
        } else {
          uni.showToast({ title: res.message || '清空失败', icon: 'none' });
        }
      } catch (e: any) {
        uni.showToast({ title: e?.data?.message || '清空失败', icon: 'none' });
      }
    },
  });
}

/** 删除直播间（二次确认，处理 409/403） */
function handleAdminDelete(room: any) {
  if (!room?.id) return;
  uni.showModal({
    title: '删除直播间',
    content: `将删除「${room.title || '该直播间'}」及相关内容，不可恢复。确定继续？`,
    confirmText: '删除',
    confirmColor: '#dc2626',
    success: async (r) => {
      if (!r.confirm) return;
      try {
        const res = await deleteRoom(room.id);
        if (res.code === 200) {
          uni.showToast({ title: '已删除', icon: 'success' });
          isAdminEditModalVisible.value = false;
          adminEditingRoom.value = null;
          await loadAdminRooms(true);
        } else {
          uni.showToast({ title: res.message || '删除失败', icon: 'none' });
        }
      } catch (e: any) {
        uni.showToast({ title: e?.data?.message || '删除失败', icon: 'none' });
      }
    },
  });
}

/** 卡片行内编辑入口：manage/admin 均跳转完整编辑页（方案 A'：标签/分类/时间/回放等全字段） */
function handleAdminEdit(room: any) {
  if (!room?.id) return;
  handleEdit(room);
}

/** 管理员模式：查看详情入口（跳转详情页，阶段 B 改造详情页内容） */
function handleAdminViewDetail(room: any) {
  if (!room?.id) return;
  uni.navigateTo({
    url: `/pages/app/live-manage/detail?id=${encodeURIComponent(room.id)}`,
  });
}

/** 管理员模式：留言管理入口（跳转该房间留言管理页，页内有清空/批删） */
function handleAdminMessages(room: any) {
  if (!room?.id) return;
  uni.navigateTo({
    url: `/pages/app/admin/messages/index?roomId=${encodeURIComponent(room.id)}`,
  });
}

/** 管理员模式：Tab 管理入口（跳转独立 Tab 管理页，复用 TabManager 组件） */
function handleAdminManageTabs(room: any) {
  if (!room?.id) return;
  isAdminEditModalVisible.value = false;
  adminEditingRoom.value = null;
  uni.navigateTo({
    url: `/pages/app/admin/room-tabs/index?roomId=${encodeURIComponent(room.id)}`,
  });
}
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

/* ========== PAGE ========== */
.room-list-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background-color: $color-surface-page;
}

.rooms-scroll {
  flex: 1;
  min-height: 0;
  padding: $spacing-md;
}

/* ========== CARD ========== */
.live-card {
  display: flex;
  flex-wrap: wrap;
  background-color: $color-surface-card;
  border-radius: var(--home-r-lg);
  margin-bottom: var(--home-spacing-card);
  overflow: hidden;
  position: relative;
  padding: var(--home-spacing-card) $spacing-lg;
  box-shadow: var(--home-shadow-card);
  transition: box-shadow $motion-fast, transform $motion-fast;

  &:active {
    transform: scale(0.985);
    box-shadow: none;
  }
}

.card-cover {
  position: relative;
  width: 240rpx;
  height: 150rpx;
  flex-shrink: 0;
  background-color: $color-surface-input;
  border-radius: $radius-sm;
  overflow: hidden;

  .cover-image {
    width: 100%;
    height: 100%;
  }
}

/* 状态标签（封面左上角）：直播中/预告/回放三态 + 异常 */
.status-badge {
  position: absolute;
  top: 8rpx;
  left: 8rpx;
  padding: 2rpx 12rpx;
  border-radius: $radius-full;
  font-size: 20rpx;
  line-height: 1.5;
  color: $color-text-white;
  z-index: 2;

  &.status-live {
    background-color: rgba(220, 38, 38, 0.9);
  }

  &.status-scheduled {
    background-color: var(--home-primary);
  }

  // 回放及其余状态：半透明黑
  &.status-replay,
  &.status-finished,
  &.status-ended,
  &.status-processing,
  &.status-ready {
    background-color: rgba(0, 0, 0, 0.6);
  }

  &.status-error {
    background-color: rgba(0, 0, 0, 0.45);
  }
}

/* ========== CARD INFO ========== */
.card-info {
  flex: 1;
  margin-left: $spacing-lg;
  margin-right: 48rpx;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-width: 0;
}

.card-title {
  font-size: $font-md;
  font-weight: 500;
  color: $color-text-primary;
  line-height: 42rpx;
  margin-bottom: $spacing-xs;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  word-break: break-all;
  max-width: 100%;
}

/* ========== AUTHOR / EXPERT ========== */
.card-author {
  display: flex;
  align-items: flex-start;

  .author-avatar {
    width: 44rpx;
    height: 44rpx;
    border-radius: 50%;
    margin-right: $spacing-sm;
    flex-shrink: 0;
    margin-top: 4rpx;
    border: 1rpx solid $color-border-divider;
  }

  .author-info {
    display: flex;
    flex-direction: column;
    flex: 1;
    min-width: 0;

    .author-name {
      font-size: $font-sm;
      color: $color-text-primary;
      line-height: 34rpx;
    }

    .author-hospital {
      font-size: $font-xs;
      color: $color-text-tertiary;
      line-height: 30rpx;
      margin-top: 2rpx;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
  }
}

/* ========== ADMIN INFO BAR ========== */
.card-admin-info {
  flex-basis: 100%;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: $spacing-sm;
  margin-top: $spacing-sm;
  padding-top: $spacing-sm;
  border-top: 1rpx solid $color-border-divider;

  .admin-owner-wrap {
    display: flex;
    align-items: center;
    gap: $spacing-sm;
    min-width: 0;
  }

  .admin-owner-avatar {
    width: 40rpx;
    height: 40rpx;
    border-radius: $radius-full;
    flex-shrink: 0;
    background: $color-surface-input;
  }

  .admin-owner {
    font-size: $font-xs;
    color: $color-text-secondary;
    background: var(--home-input-bg);
    padding: 4rpx 12rpx;
    border-radius: $radius-full;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    max-width: 260rpx;
  }
}

/* ========== ADMIN CARD ACTIONS ========== */
.admin-card-actions {
  flex-basis: 100%;
  width: 100%;
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  margin-top: $spacing-sm;

  .admin-action-btn {
    flex: 1;
    min-height: 72rpx;
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 10rpx 0;
    border-radius: $radius-full;
    background: var(--home-action-secondary-bg);
    border: none;
    transition: opacity $motion-fast, transform $motion-fast;

    .admin-action-text {
      font-size: $font-xs;
      color: $color-text-secondary;
    }

    &:active {
      opacity: 0.7;
      transform: scale(0.96);
    }

    &.admin-action-btn--danger {
      background: var(--home-action-danger-bg);

      .admin-action-text {
        color: var(--home-action-danger-text);
      }
    }
  }
}

/* ========== ADMIN EDIT MODAL ========== */
.form-group--row {
  display: flex;
  align-items: center;
  justify-content: space-between;

  .form-label {
    margin-bottom: 0;
  }
}

.form-required {
  color: #dc2626;
}

.form-error {
  font-size: $font-xs;
  color: var(--color-danger);
  margin-top: 8rpx;
  display: block;
}

.field-hint {
  font-size: $font-xs;
  color: $color-text-tertiary;
  display: block;
  margin: -12rpx 0 16rpx;
}

.form-group--danger {
  margin-top: 8rpx;
}

.danger-label {
  color: $color-text-secondary;
}

.danger-actions {
  display: flex;
  gap: $spacing-sm;
}

.action-chip {
  padding: 12rpx 24rpx;
  border-radius: $radius-sm;
  background: rgba(15, 118, 110, 0.08);
  font-size: $font-xs;
  color: $color-primary;

  &.disabled {
    opacity: 0.5;
  }

  &.action-chip--warn {
    background: rgba(217, 119, 6, 0.1);
    color: #b45309;
  }

  &.action-chip--danger {
    background: rgba(220, 38, 38, 0.08);
    color: #dc2626;
  }
}

.cover-row {
  display: flex;
  align-items: center;
  gap: $spacing-md;

  .cover-preview-img {
    width: 160rpx;
    height: 100rpx;
    border-radius: $radius-sm;
    background: $color-surface-input;
  }

  .cover-placeholder {
    width: 160rpx;
    height: 100rpx;
    border-radius: $radius-sm;
    background: $color-surface-input;
    display: flex;
    align-items: center;
    justify-content: center;

    .cover-placeholder-text {
      font-size: $font-xs;
      color: $color-text-tertiary;
    }
  }

  .cover-actions {
    .action-chip {
      display: inline-block;
    }
  }
}

/* ========== MORE BUTTON ========== */
.more-btn {
  position: absolute;
  top: $spacing-lg;
  right: $spacing-lg;
  width: 48rpx;
  height: 48rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
  background-color: rgba(0, 0, 0, 0.04);
  border-radius: 50%;
  transition: background-color $motion-fast;

  .more-icon {
    font-size: 32rpx;
    color: $color-text-secondary;
    font-weight: 500;
    line-height: 1;
  }

  &:active {
    background-color: rgba(0, 0, 0, 0.08);
  }
}

/* ========== LOADING / EMPTY ========== */
.loading-more,
.no-more {
  text-align: center;
  padding: $spacing-2xl;
  font-size: $font-sm;
  color: $color-text-tertiary;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 160rpx $spacing-4xl;

  .empty-icon {
    font-size: 96rpx;
    opacity: 0.5;
    margin-bottom: $spacing-lg;
  }

  .empty-title {
    font-size: $font-lg;
    color: $color-text-secondary;
    margin-bottom: $spacing-sm;
    font-weight: 500;
  }

  .empty-desc {
    font-size: $font-sm;
    color: $color-text-tertiary;
  }
}

/* ========== EDIT MODAL ========== */
.form {
  padding: $spacing-lg 0;
}

.form-group {
  margin-bottom: $spacing-2xl;
}

.form-label {
  display: block;
  font-size: $font-sm;
  color: $color-text-secondary;
  margin-bottom: $spacing-sm;
  font-weight: 500;
}

.form-input,
.form-textarea {
  width: 100%;
  padding: $spacing-md $spacing-lg;
  border: 1rpx solid $color-border-input;
  border-radius: $radius-md;
  font-size: $font-md;
  color: $color-text-primary;
  background-color: $color-surface-input;
  box-sizing: border-box;
  transition: border-color $motion-fast;

  &:focus {
    border-color: $color-primary;
    background-color: $color-surface-card;
    outline: none;
  }
}

.form-textarea {
  min-height: 160rpx;
  resize: vertical;
}

.placeholder {
  color: $color-text-tertiary;
}

/* ========== ADMIN SEARCH BAR ========== */
.admin-search-section {
  background: $color-surface-card;
  padding: $spacing-md $spacing-lg;
}

.admin-search-row {
  display: flex;
  gap: $spacing-sm;
}

/* 胶囊：叠加共享容器 .app-search-field（B站风格：白底+1rpx细边+胶囊）；
   高度保持 72rpx（D6 特例，与按钮同高对齐）；默认态即最终态（原 --home-input-bg 灰底/focus 白底切换已删） */
.admin-search-field {
  flex: 1;
  height: 72rpx;
  box-sizing: border-box;
}

.admin-search-icon {
  font-size: 26rpx;
  color: var(--search-icon);
  margin-right: 12rpx;
  flex-shrink: 0;
  line-height: 1;
}

.admin-search-input {
  flex: 1;
  min-width: 0;
  height: 100%;
  padding: 0;
  font-size: $font-sm;
  color: $color-text-primary;
  background: transparent;
  border: none;
  outline: none;
  box-sizing: border-box;
  padding-right: 56rpx; /* 恒定预留悬浮清除位（不随内容变化 → 布局恒定） */
}

.admin-search-placeholder {
  color: var(--search-placeholder);
}

/* 搜索按钮：实心主色 → 主色文字（B站风格，保留双触发语义；热区 ≥64rpx） */
.admin-search-btn {
  height: 72rpx;
  padding: 0 20rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  color: $color-primary;
  font-size: $font-sm;
  font-weight: 500;
  flex-shrink: 0;
  transition: opacity $motion-fast;

  &:active {
    opacity: 0.7;
  }
}

/* ========== ADMIN VISIBILITY TABS ========== */
.admin-tabs {
  display: flex;
  align-items: center;
  padding: 0 $spacing-lg;
  background: $color-surface-card;
  border-bottom: 1rpx solid $color-border-divider;
}

.admin-tab {
  padding: 20rpx 32rpx;
  font-size: $font-sm;
  color: $color-text-secondary;
  border-bottom: 4rpx solid transparent;
  transition: color $motion-fast, border-color $motion-fast;

  &:active {
    opacity: 0.7;
  }
}

.admin-tab--active {
  color: $color-primary;
  border-bottom-color: $color-primary;
  font-weight: 600;
}
</style>
