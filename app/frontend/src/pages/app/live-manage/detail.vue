<template>
  <view class="room-detail-page">
    <!-- 加载状态 -->
    <view v-if="isLoadingRoom" class="loading-container">
      <view class="spinner"></view>
      <text>加载中...</text>
    </view>

    <!-- 错误状态 -->
    <view v-else-if="loadError" class="error-container">
      <text class="error-text">{{ loadError }}</text>
      <AppButton type="primary" size="small" @click="retryLoad">重试</AppButton>
    </view>

    <!-- 内容渲染 -->
    <scroll-view v-else-if="currentRoom" class="content-scroll" scroll-y>
      <!-- 房间信息卡片 -->
      <view class="info-card">
        <view class="card-header">
          <text class="card-title">房间信息</text>
          <view class="edit-entry" @tap="goToEditPage">编辑 ›</view>
        </view>
        
        <!-- 封面图片 -->
        <view v-if="currentRoom.cover_url" class="cover-container">
          <image 
            class="room-cover" 
            :src="currentRoom.cover_url" 
            mode="aspectFill"
            lazy-load
          />
        </view>
        
        <view class="info-grid">
          <view class="info-item">
            <text class="info-label">房间名称</text>
            <text class="info-value">{{ getSafeTitle(currentRoom.title) }}</text>
          </view>
          <view class="info-item">
            <text class="info-label">简介</text>
            <text class="info-value">{{ getSafeDescription(currentRoom.description) }}</text>
          </view>
          <view class="info-item">
            <text class="info-label">房间ID</text>
            <text class="info-value id-text" @tap="copyRoomId">{{ currentRoom.id }}</text>
          </view>
          <view class="info-item" v-if="currentRoom.user_name">
            <text class="info-label">房主</text>
            <view class="info-value owner-value">
              <ProxyImage
                v-if="currentRoom.user_avatar_url"
                :src="currentRoom.user_avatar_url"
                :fallback="'/static/default-avatar.png'"
                mode="aspectFill"
                class="owner-avatar"
              />
              <image
                v-else
                class="owner-avatar"
                src="/static/default-avatar.png"
                mode="aspectFill"
                lazy-load
              />
              <text class="owner-name">{{ currentRoom.user_name }}</text>
            </view>
          </view>
          <view class="info-item">
            <text class="info-label">直播链接</text>
            <text class="info-value link-text" @tap="copyLiveLink">
              {{ getLiveLink() }}
            </text>
          </view>
          <view class="info-item">
            <text class="info-label">房间状态</text>
            <text class="info-value">
              <uni-icons v-if="currentRoom.is_private" type="locked" size="13" class="status-icon" />
              {{ currentRoom.is_private ? '私密房间' : '公开房间' }}
            </text>
          </view>
          <view class="info-item" v-if="currentRoom.is_private" @tap="copyInviteLink">
            <text class="info-label">邀请</text>
            <text class="info-value link-text">复制邀请链接，分享给他人观看 ›</text>
          </view>
          <view class="info-item">
            <text class="info-label">直播状态</text>
            <view class="info-value">
              <text :class="['status-badge', `status-${currentRoom.live_status || 'offline'}`]">
                {{ getLiveStatusText(currentRoom.live_status) }}
              </text>
            </view>
          </view>
          <view class="info-item" v-if="roomCategories.length > 0">
            <text class="info-label">分类</text>
            <view class="info-value">
              <text 
                v-for="cat in roomCategories" 
                :key="cat.id" 
                class="category-tag"
              >{{ cat.display_name || cat.name }}</text>
            </view>
          </view>
          <view class="info-item" v-if="currentRoom.created_at">
            <text class="info-label">创建时间</text>
            <text class="info-value">{{ formatDateTime(currentRoom.created_at) }}</text>
          </view>
        </view>
      </view>

      <!-- 专家/品牌信息卡片 -->
      <view class="info-card" v-if="expertInfo">
        <view class="card-header">
          <text class="card-title">专家信息</text>
        </view>
        <view class="expert-info">
          <ProxyImage 
            class="expert-avatar" 
            :src="expertInfo.avatar_url || ''" 
            :fallback="'/static/default-avatar.png'"
            mode="aspectFill"
          />
          <view class="expert-details">
            <text class="expert-name">{{ expertInfo.name }}</text>
            <text class="expert-title" v-if="expertInfo.title">{{ expertInfo.title }}</text>
            <text class="expert-hospital" v-if="expertInfo.hospital">
              {{ expertInfo.hospital }}
              <text v-if="expertInfo.department_name ?? expertInfo.department"> {{ expertInfo.department_name ?? expertInfo.department }}</text>
            </text>
            <text class="expert-bio" v-if="expertInfo.bio">{{ expertInfo.bio }}</text>
          </view>
        </view>
      </view>

      <!-- 品牌信息卡片 -->
      <view class="info-card" v-if="brandInfo">
        <view class="card-header">
          <text class="card-title">品牌信息</text>
        </view>
        <view class="brand-info">
          <image 
            class="brand-logo" 
            :src="brandInfo.logo_url || '/static/品牌占位图.png'" 
            mode="aspectFit"
            lazy-load
          />
          <view class="brand-details">
            <text class="brand-name">{{ brandInfo.name }}</text>
            <text class="brand-desc" v-if="brandInfo.description">{{ brandInfo.description }}</text>
            <text class="brand-website" v-if="brandInfo.website_url" @tap="openWebsite(brandInfo.website_url)">
              <uni-icons type="link" size="13" /> {{ brandInfo.website_url }}
            </text>
          </view>
        </view>
      </view>

      <!-- Tab 列表卡片（只读列表展示） -->
      <view class="info-card">
        <view class="card-header">
          <text class="card-title">Tab 栏目</text>
        </view>

        <view v-if="roomTabs.length === 0" class="tabs-empty">
          <text class="tabs-empty__text">暂无 Tab 栏目</text>
        </view>
        <view v-else class="tabs-list">
          <view v-for="tab in roomTabs" :key="tab.id" class="tab-item">
            <view class="tab-item-info">
              <text class="tab-item-title">{{ tab.title }}</text>
              <view :class="['tab-item-status', tab.is_active ? 'status-active' : 'status-inactive']">
                <text class="tab-item-status-text">{{ tab.is_active ? '启用' : '禁用' }}</text>
              </view>
            </view>
            <text v-if="tab.text_content" class="tab-item-content">{{ tab.text_content }}</text>
            <ProxyImage
              v-if="tab.image_url"
              :src="tab.image_url"
              :fallback="'/static/default-avatar.png'"
              mode="aspectFill"
              class="tab-item-image"
            />
          </view>
        </view>
      </view>

      <!-- 场次列表卡片 -->
      <view class="sessions-card">
        <view class="card-header">
          <text class="card-title">直播场次</text>
        </view>
        
        <!-- 场次加载状态 -->
        <view v-if="isLoadingSessions" class="loading-container">
          <view class="spinner"></view>
          <text>加载场次...</text>
        </view>
        
        <!-- 场次列表 -->
        <view v-else-if="sessions.length > 0" class="sessions-list">
          <view 
            v-for="session in sessions" 
            :key="session.id" 
            class="session-item"
            @tap="goToLiveView(session.id)"
          >
            <!-- 场次封面 -->
            <view class="session-cover">
              <image 
                :src="getSessionCover(session)"
                mode="aspectFill"
                class="cover-image"
                lazy-load
              />
              <view class="status-badge" :class="`status-${session.status}`">
                {{ getSessionStatusText(session.status) }}
              </view>
            </view>

            <!-- 场次信息 -->
            <view class="session-info">
              <text class="session-title">{{ session.title || currentRoom.title }}</text>
              <view class="session-meta">
                <text class="meta-item"><uni-icons type="calendar" size="13" /> {{ formatDateTime(session.start_time) }}</text>
                <text v-if="session.video_id" class="meta-item"><text class="iconfont icon-video"></text> {{ session.video_id }}</text>
              </view>
            </view>
          </view>
        </view>
        
        <!-- 空状态 -->
        <view v-else class="empty-state">
          <text class="empty-text">暂无场次</text>
        </view>
      </view>
    </scroll-view>

    <!-- 创建场次弹窗 -->
    <ModalDialog
      :visible="isCreateSessionModalVisible"
      title="创建场次"
      confirmText="创建"
      :confirmLoading="isSubmitting"
      @update:visible="isCreateSessionModalVisible = $event"
      @confirm="handleCreateSession"
      @cancel="closeCreateSessionModal"
    >
      <view class="form">
        <view class="form-group">
          <text class="form-label">场次标题</text>
          <input 
            class="form-input" 
            v-model="sessionForm.title" 
            placeholder="请输入场次标题（选填）" 
          />
        </view>
        <view class="form-group">
          <text class="form-label">开始时间</text>
          <input 
            class="form-input" 
            v-model="sessionForm.start_time" 
            placeholder="如：2025-07-23 10:00" 
          />
        </view>
        <view class="form-group">
          <text class="form-label">播放地址</text>
          <input 
            class="form-input" 
            v-model="sessionForm.playback_url" 
            placeholder="预告=直播流地址；回放=已录制视频地址（必填）" 
          />
        </view>
      </view>
    </ModalDialog>

    <!-- 编辑场次弹窗 -->
    <ModalDialog
      :visible="isEditSessionModalVisible"
      title="编辑场次"
      confirmText="保存"
      :confirmLoading="isSubmitting"
      @update:visible="isEditSessionModalVisible = $event"
      @confirm="handleUpdateSession"
      @cancel="closeEditSessionModal"
    >
      <view class="form">
        <view class="form-group">
          <text class="form-label">场次标题</text>
          <input 
            class="form-input" 
            v-model="sessionForm.title" 
            placeholder="请输入场次标题" 
          />
        </view>
        <view class="form-group">
          <text class="form-label">开始时间</text>
          <input 
            class="form-input" 
            v-model="sessionForm.start_time" 
            placeholder="如：2025-07-23 10:00" 
          />
        </view>
      </view>
    </ModalDialog>

    <!-- 创建分会场弹窗 -->
    <ModalDialog
      :visible="isCreateSubVenueModalVisible"
      title="创建分会场"
      confirmText="创建"
      :confirmLoading="isSubmitting"
      @update:visible="isCreateSubVenueModalVisible = $event"
      @confirm="handleCreateSubVenue"
      @cancel="closeCreateSubVenueModal"
    >
      <view class="form">
        <view class="form-group">
          <text class="form-label">分会场名称</text>
          <input 
            class="form-input" 
            v-model="subVenueForm.title" 
            placeholder="请输入分会场名称" 
          />
        </view>
        <view class="form-group">
          <text class="form-label">描述</text>
          <textarea 
            class="form-textarea" 
            v-model="subVenueForm.description" 
            placeholder="请输入描述（选填）" 
          />
        </view>
      </view>
    </ModalDialog>

    <!-- 编辑分会场弹窗 -->
    <ModalDialog
      :visible="isEditSubVenueModalVisible"
      title="编辑分会场"
      confirmText="保存"
      :confirmLoading="isSubmitting"
      @update:visible="isEditSubVenueModalVisible = $event"
      @confirm="handleUpdateSubVenue"
      @cancel="closeEditSubVenueModal"
    >
      <view class="form">
        <view class="form-group">
          <text class="form-label">分会场名称</text>
          <input 
            class="form-input" 
            v-model="subVenueForm.title" 
            placeholder="请输入分会场名称" 
          />
        </view>
        <view class="form-group">
          <text class="form-label">描述</text>
          <textarea 
            class="form-textarea" 
            v-model="subVenueForm.description" 
            placeholder="请输入描述（选填）" 
          />
        </view>
      </view>
    </ModalDialog>

    <!-- 编辑房间弹窗 -->
    <ModalDialog
      :visible="isEditRoomModalVisible"
      title="编辑房间"
      confirmText="保存"
      :confirmLoading="isSubmitting"
      @update:visible="isEditRoomModalVisible = $event"
      @confirm="handleUpdateRoom"
      @cancel="closeEditRoomModal"
    >
      <view class="form">
        <view class="form-group">
          <text class="form-label">房间名称</text>
          <input 
            class="form-input" 
            v-model="roomForm.title" 
            placeholder="请输入房间名称" 
          />
        </view>
        <view class="form-group">
          <text class="form-label">简介</text>
          <textarea 
            class="form-textarea" 
            v-model="roomForm.description" 
            placeholder="请输入简介（选填）" 
          />
        </view>
      </view>
    </ModalDialog>
  </view>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue';
import { onLoad } from '@dcloudio/uni-app';
import { storeToRefs } from 'pinia';
import { useRoomStore } from '@/store/room';
import { useSessionStore } from '@/store/session';
import { useAuthStore } from '@/store/auth';
import AppButton from '@/components/shared/AppButton.vue';
import ModalDialog from '@/components/shared/ModalDialog.vue';
import ProxyImage from '@/components/common/ProxyImage.vue';
import { BASE_API_URL } from '@/constants/api';
import { escapeHtml } from '@/utils/xss';
import { buildInviteText } from '@/utils/clipboardShare';
import { getSessionExperts } from '@/api/expert';
import { getRoomCategories } from '@/api/roomCategories';
import { getPublicRoomTabList } from '@/api/tab';
import type { Expert } from '@/types/expert';
import type { Brand } from '@/types/brand';
import type { Category } from '@/types/category';

// Store
const roomStore = useRoomStore();
const sessionStore = useSessionStore();
const authStore = useAuthStore();
const { currentRoom } = storeToRefs(roomStore);
const { sessions } = storeToRefs(sessionStore);
const { subVenues } = storeToRefs(roomStore);

// 房间ID
const roomId = ref<string | null>(null);

// 专家信息
const expertInfo = ref<Expert | null>(null);

// 品牌信息
const brandInfo = ref<Brand | null>(null);

// 直播间分类（动态获取，替代硬编码）
const roomCategories = ref<Category[]>([]);

// 直播间 Tab 列表（公开端点获取）
const roomTabs = ref<any[]>([]);

// 加载状态
const isLoadingRoom = ref(false);
const isLoadingSessions = ref(false);
const isLoadingSubVenues = ref(false);
const loadError = ref<string | null>(null);
const isSubmitting = ref(false);

// 弹窗状态
const isCreateSessionModalVisible = ref(false);
const isEditSessionModalVisible = ref(false);
const isCreateSubVenueModalVisible = ref(false);
const isEditSubVenueModalVisible = ref(false);
const isEditRoomModalVisible = ref(false);

// 表单数据
const sessionForm = reactive({
  id: null as string | null,
  title: '',
  start_time: '',
  playback_url: ''
});

const subVenueForm = reactive({
  id: null as string | null,
  title: '',
  description: ''
});

const roomForm = reactive({
  title: '',
  description: ''
});

// 请求重试配置
const MAX_RETRY_COUNT = 3;
const RETRY_DELAY = 1000;

// 统一错误处理
const handleError = (error: any, context: string) => {
  console.error(`❌ ${context}失败:`, error);
  
  // 生产环境过滤敏感错误信息
  let message: string;
  if (process.env.NODE_ENV === 'production') {
    message = `${context}失败，请稍后重试`;
  } else {
    message = error?.message || error?.data?.message || `${context}失败`;
  }
  
  loadError.value = message;
  
  uni.showToast({
    title: message,
    icon: 'none',
    duration: 2000
  });
};

// 带重试的请求包装
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

// 获取专家信息
const fetchExpertInfo = async () => {
  if (!roomId.value) return;
  
  try {
    // 先获取场次
    await sessionStore.fetchSessionsByRoomId(roomId.value);
    const sessions = sessionStore.sessions;
    
    if (sessions && sessions.length > 0) {
      // 获取第一个场次的专家信息
      const response = await getSessionExperts(sessions[0].id);
      if (response.code === 200 && response.data && response.data.length > 0) {
        expertInfo.value = response.data[0];
        console.log('✅ 获取到真实专家信息:', expertInfo.value);
      } else {
        // 无关联专家：不展示专家卡片（模板 v-if="expertInfo" 控制）
        expertInfo.value = null;
        console.log('ℹ️ 该场次无关联专家');
      }
    } else {
      // 没有场次：不展示专家卡片
      expertInfo.value = null;
      console.log('ℹ️ 无场次，不展示专家信息');
    }
  } catch (error) {
    console.error('获取专家信息失败:', error);
    // 获取失败：不展示专家卡片（不造假数据）
    expertInfo.value = null;
  }
};

// 获取品牌信息
const fetchBrandInfo = async () => {
  if (!roomId.value) return;
  
  try {
    // TODO: 实现品牌信息获取API
    // const response = await getRoomBrand(roomId.value);
    // if (response.code === 200 && response.data) {
    //   brandInfo.value = response.data;
    //   console.log('✅ 获取到真实品牌信息:', brandInfo.value);
    //   return;
    // }
    
    // 使用mock数据作为占位
    brandInfo.value = {
      id: 'mock-brand',
      name: '医疗品牌合作伙伴',
      slug: 'medical-partner',
      logo_url: '/static/品牌占位图.png',
      description: '专业医疗服务提供商，致力于为您提供优质的医疗体验',
      website_url: 'https://www.example.com',
      sort_order: 0,
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
    console.log('ℹ️ 使用mock品牌信息');
  } catch (error) {
    console.error('获取品牌信息失败:', error);
    // 出错时也使用mock数据
    brandInfo.value = {
      id: 'mock-brand',
      name: '医疗品牌合作伙伴',
      slug: 'medical-partner',
      logo_url: '/static/品牌占位图.png',
      description: '专业医疗服务提供商',
      website_url: null,
      sort_order: 0,
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
  }
};

// 打开品牌官网
const openWebsite = (url: string) => {
  if (!url) return;
  // 安全检查：只允许http/https协议
  if (!/^https?:\/\//i.test(url)) {
    uni.showToast({ title: '无效的链接', icon: 'none' });
    return;
  }
  uni.navigateTo({
    url: `/pages/shared/webview/index?url=${encodeURIComponent(url)}`
  });
};

// 加载房间信息
const fetchRoom = async () => {
  if (!roomId.value) return;
  
  isLoadingRoom.value = true;
  loadError.value = null;
  
  try {
    await withRetry(
      () => roomStore.fetchRoomById(roomId.value!),
      '加载房间信息'
    );
  } finally {
    isLoadingRoom.value = false;
  }
};

// 加载场次列表
const fetchSessions = async () => {
  if (!roomId.value) return;
  
  isLoadingSessions.value = true;
  
  try {
    await withRetry(
      () => sessionStore.fetchSessionsByRoomId(roomId.value!, { refresh: true }),
      '加载场次列表'
    );
  } finally {
    isLoadingSessions.value = false;
  }
};

// 加载分会场列表
const fetchSubVenues = async () => {
  if (!roomId.value) return;
  
  isLoadingSubVenues.value = true;
  
  try {
    await withRetry(
      () => roomStore.fetchSubVenues(roomId.value!),
      '加载分会场列表'
    );
  } finally {
    isLoadingSubVenues.value = false;
  }
};

// 重试加载
const retryLoad = async () => {
  await fetchRoom();
  await fetchSessions();
  await fetchSubVenues();
};

// 获取直播链接（APP环境使用固定域名）
const getLiveLink = () => {
  if (!currentRoom.value?.id) return '';
  return `https://mp.dayilive.com/pages/app/live/index?roomId=${currentRoom.value.id}`;
};

// 获取直播状态文本
const getLiveStatusText = (status: string | undefined) => {
  if (!status) return '未开播';
  const statusMap: Record<string, string> = {
    'scheduled': '预告',
    'live': '直播中',
    'finished': '已结束',
    'processing': '回放生成中',
    'ready': '回放',
    'error': '异常',
    'offline': '未开播'
  };
  return statusMap[status] || status;
};

// 获取场次状态文本
const getSessionStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    'scheduled': '预告',
    'live': '直播中',
    'finished': '已结束',
    'processing': '回放生成中',
    'ready': '回放',
    'error': '异常'
  };
  return statusMap[status] || status;
};

// 跳转编辑页（场次状态管理入口归位编辑页；房间信息 + 最新场次一并编辑）
const goToEditPage = () => {
  if (!roomId.value) return;
  uni.navigateTo({
    url: `/pages/app/live-manage/edit?roomId=${encodeURIComponent(roomId.value)}`
  });
};

// 格式化日期时间
const formatDateTime = (dateString: string) => {
  if (!dateString) return '';
  try {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch (error) {
    return dateString;
  }
};

// XSS防护：安全渲染标题和描述
const getSafeTitle = (title: string | undefined): string => {
  return escapeHtml(title || '');
};

const getSafeDescription = (description: string | undefined): string => {
  return escapeHtml(description || '暂无简介');
};

// 获取场次封面
const getSessionCover = (session: any) => {
  if (session.cover_url) return session.cover_url;
  if (currentRoom.value?.cover_url) return currentRoom.value.cover_url;
  return '/logo.png';
};

// 复制房间ID
const copyRoomId = () => {
  if (!currentRoom.value?.id) return;
  uni.setClipboardData({
    data: currentRoom.value.id,
    success: () => {
      uni.showToast({ title: '房间ID已复制', icon: 'success' });
    }
  });
};

// 复制直播链接
const copyLiveLink = () => {
  const link = getLiveLink();
  uni.setClipboardData({
    data: link,
    success: () => {
      uni.showToast({ title: '直播链接已复制', icon: 'success' });
    }
  });
};

// 复制私密房邀请链接（仅私密房间显示；对方打开 App 将自动识别进入）
const copyInviteLink = () => {
  if (!currentRoom.value?.id) return;
  uni.setClipboardData({
    data: buildInviteText(currentRoom.value.id),
    success: () => {
      uni.showToast({ title: '邀请链接已复制！请勿直接点击链接，复制后打开 App 将自动识别进入', icon: 'none' });
    }
  });
};

// 返回列表
const goBackToList = () => {
  uni.navigateBack({
    delta: 1,
    fail: () => {
      uni.redirectTo({ url: '/pages/app/live-manage/list' });
    }
  });
};

// 获取直播间分类（动态展示，替代硬编码）
const fetchRoomCategories = async () => {
  if (!roomId.value) return;
  try {
    const response = await getRoomCategories(roomId.value);
    if (response.data) {
      roomCategories.value = response.data;
    }
  } catch (error) {
    console.error('获取直播间分类失败:', error);
  }
};

/** 获取直播间 Tab 列表（公开端点，展示 Tab 栏目） */
const fetchRoomTabs = async () => {
  if (!roomId.value) return;
  try {
    const response = await getPublicRoomTabList(roomId.value);
    const data = response.data as any;
    roomTabs.value = Array.isArray(data) ? data : (data?.items || []);
  } catch (error) {
    console.error('获取直播间 Tab 失败:', error);
  }
};

// 跳转到直播页面（播放页 LiveView 读 sessionId 参数）
const goToLiveView = (sessionId: string) => {
  uni.navigateTo({
    url: `/pages/app/live/LiveView?sessionId=${encodeURIComponent(sessionId)}`
  });
};

// 跳转到分会场详情
const goToSubVenueDetail = (subVenueId: string) => {
  uni.navigateTo({
    url: `/pages/app/live-manage/detail?id=${subVenueId}`
  });
};

// 打开编辑房间弹窗
const handleEditRoom = () => {
  if (!currentRoom.value) return;
  roomForm.title = currentRoom.value.title;
  roomForm.description = currentRoom.value.description || '';
  isEditRoomModalVisible.value = true;
};

// 更新房间
const handleUpdateRoom = async () => {
  if (!roomForm.title.trim()) {
    uni.showToast({ title: '请输入房间名称', icon: 'none' });
    return;
  }
  
  isSubmitting.value = true;
  
  try {
    await withRetry(
      () => roomStore.updateRoom(roomId.value!, {
        title: roomForm.title,
        description: roomForm.description || undefined
      }),
      '更新房间信息'
    );
    
    uni.showToast({ title: '更新成功', icon: 'success' });
    closeEditRoomModal();
    await fetchRoom();
  } finally {
    isSubmitting.value = false;
  }
};

const closeEditRoomModal = () => {
  isEditRoomModalVisible.value = false;
  roomForm.title = '';
  roomForm.description = '';
};

// 打开创建场次弹窗
const openCreateSessionModal = () => {
  sessionForm.id = null;
  sessionForm.title = '';
  sessionForm.start_time = '';
  sessionForm.playback_url = '';
  isCreateSessionModalVisible.value = true;
};

// 创建场次
const handleCreateSession = async () => {
  if (!sessionForm.start_time.trim()) {
    uni.showToast({ title: '请输入开始时间', icon: 'none' });
    return;
  }
  if (!sessionForm.playback_url.trim()) {
    uni.showToast({ title: '请输入播放地址（后端必填）', icon: 'none' });
    return;
  }
  
  isSubmitting.value = true;
  
  try {
    await withRetry(
      () => sessionStore.createSession(roomId.value!, {
        title: sessionForm.title || undefined,
        start_time: new Date(sessionForm.start_time).toISOString(),
        playback_url: sessionForm.playback_url.trim()
      }),
      '创建场次'
    );
    
    uni.showToast({ title: '创建成功', icon: 'success' });
    closeCreateSessionModal();
    await fetchSessions();
  } finally {
    isSubmitting.value = false;
  }
};

const closeCreateSessionModal = () => {
  isCreateSessionModalVisible.value = false;
  sessionForm.id = null;
  sessionForm.title = '';
  sessionForm.start_time = '';
  sessionForm.playback_url = '';
};

// 打开编辑场次弹窗
const handleEditSession = (session: any) => {
  sessionForm.id = session.id;
  sessionForm.title = session.title || '';
  sessionForm.start_time = formatDateTime(session.start_time);
  isEditSessionModalVisible.value = true;
};

// 更新场次
const handleUpdateSession = async () => {
  if (!sessionForm.id) return;
  
  isSubmitting.value = true;
  
  try {
    await withRetry(
      () => sessionStore.updateSession(sessionForm.id!, {
        title: sessionForm.title || undefined,
        start_time: new Date(sessionForm.start_time).toISOString()
      }),
      '更新场次'
    );
    
    uni.showToast({ title: '更新成功', icon: 'success' });
    closeEditSessionModal();
    await fetchSessions();
  } finally {
    isSubmitting.value = false;
  }
};

const closeEditSessionModal = () => {
  isEditSessionModalVisible.value = false;
  sessionForm.id = null;
  sessionForm.title = '';
  sessionForm.start_time = '';
};

// 删除场次
const handleDeleteSession = (session: any) => {
  uni.showModal({
    title: '确认删除',
    content: '确定要删除这个场次吗？',
    success: async (res) => {
      if (res.confirm) {
        uni.showLoading({ title: '删除中...', mask: true });
        
        try {
          await withRetry(
            () => sessionStore.deleteSession(session.id, roomId.value!),
            '删除场次'
          );
          
          uni.hideLoading();
          uni.showToast({ title: '删除成功', icon: 'success' });
          await fetchSessions();
        } catch (error) {
          uni.hideLoading();
        }
      }
    }
  });
};

// 打开创建分会场弹窗
const openCreateSubVenueModal = () => {
  subVenueForm.id = null;
  subVenueForm.title = '';
  subVenueForm.description = '';
  isCreateSubVenueModalVisible.value = true;
};

// 创建分会场
const handleCreateSubVenue = async () => {
  if (!subVenueForm.title.trim()) {
    uni.showToast({ title: '请输入分会场名称', icon: 'none' });
    return;
  }
  
  isSubmitting.value = true;
  
  try {
    await withRetry(
      () => roomStore.createSubVenue({
        parent_room_id: roomId.value!,
        title: subVenueForm.title,
        description: subVenueForm.description || undefined
      }),
      '创建分会场'
    );
    
    uni.showToast({ title: '创建成功', icon: 'success' });
    closeCreateSubVenueModal();
    await fetchSubVenues();
  } finally {
    isSubmitting.value = false;
  }
};

const closeCreateSubVenueModal = () => {
  isCreateSubVenueModalVisible.value = false;
  subVenueForm.id = null;
  subVenueForm.title = '';
  subVenueForm.description = '';
};

// 打开编辑分会场弹窗
const handleEditSubVenue = (venue: any) => {
  subVenueForm.id = venue.id;
  subVenueForm.title = venue.title;
  subVenueForm.description = venue.description || '';
  isEditSubVenueModalVisible.value = true;
};

// 更新分会场
const handleUpdateSubVenue = async () => {
  if (!subVenueForm.id || !subVenueForm.title.trim()) {
    uni.showToast({ title: '请输入分会场名称', icon: 'none' });
    return;
  }
  
  isSubmitting.value = true;
  
  try {
    await withRetry(
      () => roomStore.updateRoom(subVenueForm.id!, {
        title: subVenueForm.title,
        description: subVenueForm.description || undefined
      }),
      '更新分会场'
    );
    
    uni.showToast({ title: '更新成功', icon: 'success' });
    closeEditSubVenueModal();
    await fetchSubVenues();
  } finally {
    isSubmitting.value = false;
  }
};

const closeEditSubVenueModal = () => {
  isEditSubVenueModalVisible.value = false;
  subVenueForm.id = null;
  subVenueForm.title = '';
  subVenueForm.description = '';
};

// 删除分会场
const handleDeleteSubVenue = (venue: any) => {
  uni.showModal({
    title: '确认删除',
    content: `确定要删除分会场"${venue.title}"吗？`,
    success: async (res) => {
      if (res.confirm) {
        uni.showLoading({ title: '删除中...', mask: true });
        
        try {
          await withRetry(
            () => roomStore.deleteRoom(venue.id),
            '删除分会场'
          );
          
          uni.hideLoading();
          uni.showToast({ title: '删除成功', icon: 'success' });
          await fetchSubVenues();
        } catch (error) {
          uni.hideLoading();
        }
      }
    }
  });
};

// 页面加载
onLoad((options) => {
  console.log('🚀 RoomDetail页面加载');
  
  if (!authStore.isAuthenticated) {
    console.log('❌ 用户未认证');
    uni.showToast({ title: '请先登录', icon: 'none' });
    uni.navigateBack({
      fail: () => { uni.switchTab({ url: '/pages/app/tabbar/home/index' }); }
    });
    return;
  }
  
  if (options && options.id) {
    roomId.value = options.id;
    fetchRoom();
    fetchSessions();
    fetchSubVenues();
    fetchExpertInfo();
    fetchBrandInfo();
    fetchRoomCategories();
    fetchRoomTabs();
  } else {
    loadError.value = '无效的房间ID';
  }
});
</script>

<style lang="scss" scoped>
.room-detail-page {
  min-height: 100vh;
  background-color: var(--home-bg);
  padding-bottom: 40rpx;
}


.content-scroll {
  height: 100vh;
  padding: 20rpx 24rpx;
  box-sizing: border-box;
}

.loading-container,
.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 120rpx 40rpx;
}

.spinner {
  width: 60rpx;
  height: 60rpx;
  border: 4rpx solid rgba(17, 24, 39, 0.08);
  border-top-color: var(--home-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 20rpx;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-text {
  font-size: var(--home-fs-card-title);
  color: var(--color-danger);
  margin-bottom: 20rpx;
}

.info-card,
.sessions-card,
.sub-venues-card {
  background: var(--home-card);
  border-radius: var(--home-r-lg);
  margin-bottom: var(--home-spacing-card);
  overflow: visible;
  box-shadow: var(--home-shadow-card);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20rpx 24rpx;
  border-bottom: 1.5rpx solid var(--home-divider);

  .edit-icon {
    margin-right: 4rpx;
  }
}

.card-title {
  font-size: var(--home-fs-section);
  font-weight: 600;
  color: var(--home-text1);
}

// 编辑页入口（状态管理归位编辑页后的跳转）
.edit-entry {
  font-size: var(--home-fs-meta);
  color: var(--home-primary);
  display: flex;
  align-items: center;
}

// 封面容器
.cover-container {
  padding: 0 24rpx 24rpx;
}

.room-cover {
  width: 100%;
  height: 380rpx;
  border-radius: var(--home-r-md);
  background: var(--home-bg);
  display: block;
  object-fit: cover;
}

// 分类标签
.category-tag {
  display: inline-block;
  padding: 6rpx 20rpx;
  background: var(--home-primary);
  color: #ffffff;
  border-radius: var(--home-r-pill);
  font-size: var(--home-fs-meta);
  font-weight: 500;
  line-height: 1.4;
}

// 回放链接
.playback-link {
  color: var(--home-primary) !important;
  text-decoration: underline;
  cursor: pointer;
}

.info-grid {
  padding: 24rpx 24rpx;
}

.info-item {
  display: flex;
  align-items: flex-start;
  margin-bottom: 24rpx;
  
  &:last-child {
    margin-bottom: 0;
  }
}

.info-label {
  width: 140rpx;
  font-size: var(--home-fs-meta);
  color: var(--home-text2);
  flex-shrink: 0;
  line-height: 40rpx;
}

.info-value {
  flex: 1;
  font-size: var(--home-fs-meta);
  color: var(--home-text1);
  word-break: break-word;
  line-height: 40rpx;
  min-width: 0;
}

.id-text {
  font-family: 'Courier New', monospace;
  font-size: var(--home-fs-meta);
  color: var(--home-text2);
  user-select: text;
}

.owner-value {
  display: flex;
  align-items: center;
  gap: 12rpx;

  .owner-avatar {
    width: 44rpx;
    height: 44rpx;
    border-radius: 50%;
    flex-shrink: 0;
    background: var(--home-input-bg);
  }

  .owner-name {
    font-size: var(--home-fs-meta);
    color: var(--home-text1);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

/* Tab 列表卡片 */
.tabs-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32rpx 0;

  .tabs-empty__text {
    font-size: 26rpx;
    color: var(--home-tabbar-inactive);
  }
}

/* Tab 列表展示 */
.tabs-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;

  .tab-item {
    background: var(--home-input-bg);
    border-radius: var(--home-r-md);
    padding: 16rpx;

    .tab-item-info {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12rpx;

      .tab-item-title {
        font-size: var(--home-fs-title);
        color: var(--home-text1);
        font-weight: 500;
      }

      .tab-item-status {
        font-size: var(--home-fs-tag);
        padding: 2rpx 12rpx;
        border-radius: var(--home-tag-radius);
        flex-shrink: 0;

        &.status-active {
          background: rgba(15, 118, 110, 0.08);
          color: var(--home-primary);
        }

        &.status-inactive {
          background: var(--home-input-bg);
          color: var(--home-tabbar-inactive);
        }
      }
    }

    .tab-item-content {
      font-size: var(--home-fs-meta);
      color: var(--home-text2);
      margin-top: 8rpx;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }

    .tab-item-image {
      width: 100%;
      height: 160rpx;
      border-radius: 8rpx;
      margin-top: 8rpx;
      background: var(--home-input-bg);
    }
  }
}

.link-text {
  color: var(--home-primary);
  text-decoration: underline;
}

.status-icon {
  margin-right: 8rpx;
}

.status-badge {
  display: inline-block;
  padding: 4rpx 16rpx;
  border-radius: var(--home-r-pill);
  font-size: var(--home-fs-meta);
  font-weight: 500;
  color: #fff;
  
  &.status-scheduled {
    background: var(--home-primary);
  }
  
  &.status-live {
    background: var(--color-danger);
    animation: pulse 2s infinite;
  }
  
  &.status-finished {
    background: var(--home-tabbar-inactive);
  }
  
  &.status-ready {
    background: var(--home-primary);
    opacity: 0.85;
  }
  
  &.status-offline {
    background: var(--home-border);
    color: var(--home-text2);
  }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.sessions-list,
.sub-venues-list {
  padding: 16rpx;
}

.session-item {
  display: flex;
  align-items: flex-start;
  padding: var(--home-spacing-card);
  background: var(--home-bg);
  border-radius: var(--home-r-md);
  margin-bottom: var(--home-spacing-inner);
  box-sizing: border-box;
  
  &:last-child {
    margin-bottom: 0;
  }
}

.session-cover {
  position: relative;
  width: 160rpx;
  height: 100rpx;
  border-radius: var(--home-r-md);
  overflow: hidden;
  flex-shrink: 0;
  background: var(--home-border);
  
  .cover-image {
    width: 100%;
    height: 100%;
  }
  
  .status-badge {
    position: absolute;
    top: 6rpx;
    left: 6rpx;
    font-size: 20rpx;
    padding: 2rpx 8rpx;
  }
}

.session-info {
  flex: 1;
  margin-left: 16rpx;
  margin-right: 12rpx;
  min-width: 0;
  overflow: hidden;
}

.session-title {
  font-size: var(--home-fs-meta);
  font-weight: 500;
  color: var(--home-text1);
  margin-bottom: 8rpx;
  line-height: 36rpx;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  word-break: break-word;
}

.session-meta {
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}

.meta-item {
  font-size: var(--home-fs-meta);
  color: var(--home-text2);
  line-height: 32rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.session-actions {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
  flex-shrink: 0;
  min-width: 100rpx;
  align-items: stretch;
}

.sub-venue-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24rpx;
  background: var(--home-bg);
  border-radius: var(--home-r-md);
  margin-bottom: var(--home-spacing-inner);
  
  &:last-child {
    margin-bottom: 0;
  }
}

.venue-info {
  flex: 1;
  margin-right: 20rpx;
}

.venue-title {
  font-size: var(--home-fs-card-title);
  font-weight: 500;
  color: var(--home-text1);
  margin-bottom: 8rpx;
}

.venue-desc {
  font-size: var(--home-fs-meta);
  color: var(--home-text2);
}

.venue-actions {
  display: flex;
  gap: 8rpx;
  flex-shrink: 0;
}

// 专家信息样式
.expert-info {
  display: flex;
  padding: 24rpx;
  align-items: flex-start;
}

.expert-avatar {
  width: 120rpx;
  height: 120rpx;
  border-radius: 50%;
  flex-shrink: 0;
  background: var(--home-border);
}

.expert-details {
  flex: 1;
  margin-left: 24rpx;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.expert-name {
  font-size: var(--home-fs-section);
  font-weight: 600;
  color: var(--home-text1);
  line-height: 42rpx;
}

.expert-title {
  font-size: var(--home-fs-meta);
  color: var(--home-text2);
  line-height: 34rpx;
}

.expert-hospital {
  font-size: var(--home-fs-meta);
  color: var(--home-tabbar-inactive);
  line-height: 34rpx;
}

.expert-bio {
  font-size: var(--home-fs-meta);
  color: var(--home-text2);
  line-height: 36rpx;
  margin-top: 8rpx;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

// 品牌信息样式
.brand-info {
  display: flex;
  padding: 24rpx;
  align-items: flex-start;
}

.brand-logo {
  width: 120rpx;
  height: 120rpx;
  border-radius: var(--home-r-md);
  flex-shrink: 0;
  background: var(--home-border);
  border: 1.5rpx solid var(--home-border);
}

.brand-details {
  flex: 1;
  margin-left: 24rpx;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.brand-name {
  font-size: var(--home-fs-section);
  font-weight: 600;
  color: var(--home-text1);
  line-height: 42rpx;
}

.brand-desc {
  font-size: var(--home-fs-meta);
  color: var(--home-text2);
  line-height: 36rpx;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

.brand-website {
  font-size: var(--home-fs-meta);
  color: var(--home-primary);
  line-height: 32rpx;
  text-decoration: underline;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 80rpx 40rpx;
}

.empty-text {
  font-size: var(--home-fs-card-title);
  color: var(--home-tabbar-inactive);
  margin-bottom: 8rpx;
}

.empty-tip {
  font-size: var(--home-fs-meta);
  color: var(--home-border);
}

.form {
  padding: 20rpx 0;
}

.form-group {
  margin-bottom: 32rpx;
}

.form-label {
  display: block;
  font-size: var(--home-fs-card-title);
  color: var(--home-text1);
  margin-bottom: var(--home-spacing-inner);
  font-weight: 500;
}

.form-input,
.form-textarea {
  width: 100%;
  padding: 20rpx;
  border: 1.5rpx solid var(--home-border);
  border-radius: var(--home-r-md);
  font-size: var(--home-fs-card-title);
  color: var(--home-text1);
  background-color: var(--home-bg);
  box-sizing: border-box;
}

.form-textarea {
  min-height: 160rpx;
}
</style>
