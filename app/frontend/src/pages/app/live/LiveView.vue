<template>
  <!-- ConsumerLayout：单背景、去卡片、留白分组 -->
  <view class="live-view-page consumer-layout">

    <!-- Header 四层：TitleRow / MetaRow / ExpertRow / ActionRow，同一 header-inner 共享 padding -->
    <view class="info-section">
      <view class="info-header header-inner">
        <!-- TitleRow：标题 + 展开（弱权重） -->
        <view class="title-row">
          <text class="live-title" :class="{ 'expanded': titleExpanded }">
            {{ sessionInfo?.title || pageTitle || '直播标题' }}
          </text>
          <view v-if="!titleExpanded && isTitleLong" class="expand-btn" @tap="toggleTitle">
            <text>展开</text>
            <text class="iconfont icon-arrow-down expand-icon"></text>
          </view>
          <view v-if="titleExpanded" class="expand-btn collapse" @tap="toggleTitle">
            <text>收起</text>
            <text class="iconfont icon-arrow-up expand-icon"></text>
          </view>
        </view>
        <!-- MetaRow：回放 · 观看数 · 时间（secondary，分隔符 ·） -->
        <view class="meta-row">
          <text class="meta-row-text">{{ metaRowText }}</text>
        </view>
        <!-- TagRow：场次标签（内容类型标记） -->
        <view v-if="sessionTags.length > 0" class="tag-row">
          <text
            v-for="tag in sessionTags"
            :key="tag.id"
            class="tag-chip"
          >#{{ tag.name }}</text>
        </view>
        <!-- ExpertRow：档案化层级 姓名(强) | 职称(中) / 医院|科室(弱) -->
        <!-- 只有当专家信息存在时才显示专家区域 -->
        <view v-if="sessionInfo?.expert" class="expert-row">
          <ProxyImage
            class="host-avatar"
            :src="resolveExpertAvatar(sessionInfo?.expert)"
            :fallback="DEFAULT_AVATAR_PATH"
            mode="aspectFill"
          />
          <view class="host-info">
            <view class="host-main-line">
              <text class="host-name">{{ formatExpertName(sessionInfo?.expert) }}</text><template v-if="formatExpertTitle(sessionInfo?.expert)"><text class="host-title-sep"> | </text><text class="host-title">{{ formatExpertTitle(sessionInfo?.expert) }}</text></template>
            </view>
            <text class="host-hospital">{{ formatExpertLine2(sessionInfo?.expert) }}</text>
          </view>
        </view>
        <!-- ActionRow：医疗系统工具栏，三等分平铺、icon+轻标签、无平台化（PlaybackActionBar 规范） -->
        <view class="action-row playback-actionbar">
          <!-- 预告状态显示订阅按钮，直播/回放显示收藏按钮 -->
          <view v-if="sessionInfo?.status === 'scheduled'" class="action-item" :class="{ 'is-active': isSubscribed }" role="button" aria-label="订阅" @tap="toggleSubscription">
            <view class="action-icon-wrap">
              <text class="iconfont icon-sub-outline"></text>
            </view>
            <text class="action-label">{{ isSubscribed ? '已订阅' : '订阅' }}</text>
          </view>
          <view v-else class="action-item" :class="{ 'is-active': isFavorited }" role="button" aria-label="收藏" @tap="toggleFavorite">
            <view class="action-icon-wrap">
              <text class="iconfont" :class="isFavorited ? 'icon-star-filled' : 'icon-star-outline'"></text>
            </view>
            <text class="action-label">收藏</text>
          </view>
          <view class="action-item" role="button" aria-label="分享" @tap="shareContent">
            <view class="action-icon-wrap">
              <text class="iconfont icon-share"></text>
            </view>
            <text class="action-label">分享</text>
          </view>
          <view class="action-item" :class="{ 'is-active': isLiked }" role="button" aria-label="点赞" @tap="toggleLike">
            <view class="action-icon-wrap">
              <text class="iconfont" :class="isLiked ? 'icon-like-filled' : 'icon-like-outline'"></text>
            </view>
            <text class="action-label">点赞</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 播放器区域 -->
    <view class="player-section">
      <!-- 预告遮罩 -->
      <view v-if="sessionInfo?.status === 'scheduled'" class="scheduled-overlay">
        <image v-if="coverUrlForPlayer" class="scheduled-bg" :src="coverUrlForPlayer" mode="aspectFill" />
        <view class="scheduled-gradient" />
        <view class="scheduled-content">
          <text class="scheduled-badge">预告</text>
          <text class="scheduled-countdown">{{ countdownText || '即将开播' }}</text>
          <text class="scheduled-time">开播时间 {{ formattedStartTime }}</text>
        </view>
      </view>
      <!-- V15：播放器统一使用 VideoPlayerApp（uni video）。
           live-player 原为 external 直播流的优先方案，但标准基座/模拟器渲染不稳定
           （insertBefore 崩溃），降级为 video 兜底；后续自定义基座验证后再启用 live-player -->
      <VideoPlayerApp
        v-else
        ref="playerRef"
        :src="playerSourceUrl"
        :poster="resolveMediaUrl(sessionInfo?.cover_url) || '/static/default-cover.png'"
        :autoplay="true"
        @segmentchange="handleSegmentChange"
        @play="handlePlay"
        @pause="handlePause"
        @error="handlePlaybackError"
      />

      <!-- 流量提醒弹窗 -->
      <view v-if="showTrafficWarning" class="traffic-warning-modal">
        <view class="modal-content">
          <text class="warning-icon iconfont icon-error"></text>
          <text class="warning-title">流量提醒</text>
          <text class="warning-message">
            您当前使用的是{{ networkType }}网络，
            观看直播可能消耗较多流量（约500MB/小时）
          </text>
          <view class="modal-actions">
            <button @tap="cancelPlayback">取消</button>
            <button @tap="continuePlayback">继续观看</button>
          </view>
        </view>
      </view>
    </view>

    <!-- Sticky Tabs -->
    <view class="sticky-tabs" :class="{ 'stuck': tabsStuck }">
      <scroll-view scroll-x class="tabs-container">
        <view
          v-for="(tab, idx) in tabs"
          :key="tab.key"
          class="tab-item"
          :class="{ active: activeIndex === idx }"
          @tap="handleTabTap(idx)"
        >
          <text>{{ tab.label }}</text>
        </view>
      </scroll-view>
    </view>

    <!-- Tab内容区域：swiper 承载各 Tab，左右滑动切换 -->
    <view class="content-section">
      <swiper
        class="content-swiper"
        :style="chatSwiperHeightPx ? { height: chatSwiperHeightPx + 'px' } : undefined"
        :current="activeIndex"
        @change="handleSwiperChange"
      >
        <swiper-item v-for="(tab, idx) in tabs" :key="tab.key" class="content-swiper-item">
          <scroll-view class="content-scroll" scroll-y>
            <!-- 动态渲染Tab内容：仅渲染当前激活 Tab 对应的组件 -->
            <!-- 注意：ChatTab 含 fixed 底部输入框，必须仅激活时渲染，否则非活动 swiper-item 会一直显示输入框遮挡页面 -->
            <template v-if="activeIndex === idx">
              <!-- 正常模式：使用动态 Tab 组件（fallback 时走下方硬编码降级） -->
              <!-- 条件含 currentTab：确保 currentTab 为 undefined 时不渲染 ContentTab（如 activeTab 被设为非 tabs 内的 key） -->
              <template v-if="!isUsingFallback && currentTab">
                <!-- 专家介绍Tab -->
                <ExpertsTab
                  v-if="tab.key === 'experts'"
                  :experts="experts"
                />

                <!-- 品牌介绍Tab -->
                <BrandsTab
                  v-else-if="tab.key === 'brands'"
                  :room-id="roomId"
                />

                <!-- 聊天Tab -->
                <ChatTab
                  v-else-if="tab.key === 'chat'"
                  :room-id="roomId"
                />

                <!-- 内容型Tab（intro、自定义Tab等） -->
                <ContentTab
                  v-else
                  :tab="currentTab!"
                />
              </template>

              <!-- 降级模式：使用旧的硬编码内容（fallback 时，按 tab.key 判断类型） -->
              <template v-else>
                <!-- 直播介绍Tab -->
                <view v-if="tab.key === 'intro'" class="introduction-content">
                  <view class="content-block">
                    <text class="block-title">直播介绍</text>
                    <text class="block-content">
                      {{ sessionInfo?.summary || sessionInfo?.description || '暂无介绍' }}
                    </text>
                  </view>

                  <view v-if="sessionInfo?.tags && sessionInfo.tags.length > 0" class="content-block">
                    <text class="block-title">标签</text>
                    <view class="tags-list">
                      <text
                        v-for="tag in sessionInfo.tags"
                        :key="tag.id"
                        class="tag-item"
                      >
                        #{{ tag.name }}
                      </text>
                    </view>
                  </view>
                </view>

                <!-- 聊天Tab（降级） -->
                <view v-if="tab.key === 'chat'" class="chat-content">
                <view class="chat-messages-container">
                  <view class="chat-messages">
                    <!-- 降级聊天：与 ChatTab 微信式气泡同规格；本地演示消息(current-user)视为自己靠右 -->
                    <view
                      v-for="message in chatMessages"
                      :key="message.id"
                      class="message-item"
                      :class="{ self: message.user.id === 'current-user' }"
                    >
                      <ProxyImage
                        class="message-avatar"
                        :src="resolveMediaUrl(message.user.avatar)"
                        :fallback="DEFAULT_AVATAR_PATH"
                        mode="aspectFill"
                      />
                      <view class="message-body">
                        <view class="message-meta">
                          <text v-if="message.user.id !== 'current-user'" class="message-user">{{ message.user.name }}</text>
                          <text class="message-time">{{ formatTime(message.timestamp) }}</text>
                        </view>
                        <view class="message-bubble">
                          <text class="message-text">{{ message.content }}</text>
                        </view>
                      </view>
                    </view>
                  </view>

                  <!-- 演示模式提示 -->
                  <view class="demo-notice">
                    <text>演示模式：消息仅本地显示，不会发送到服务器</text>
                  </view>
                </view>

                <!-- 固定在底部的聊天输入框（可见性修复 + 发送主色） -->
                <view class="chat-input-fixed">
                  <view class="chat-input">
                    <input
                      v-model="chatInput"
                      class="chat-input-field"
                      placeholder="请输入消息..."
                      placeholder-class="chat-input-placeholder"
                      :cursor-spacing="20"
                      :adjust-position="true"
                      confirm-type="send"
                      :hold-keyboard="false"
                      :show-confirm-bar="true"
                      :enable-native-ime="true"
                      @focus="onInputFocus"
                      @confirm="sendMessage"
                    />
                    <button class="chat-send-btn" :disabled="!chatInput.trim()" @tap="sendMessage">发送</button>
                  </view>
                </view>
              </view>
            </template>
          </template>
          </scroll-view>
        </swiper-item>
      </swiper>
    </view>

  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue';
import { onLoad, onShow } from '@dcloudio/uni-app';
import { useSwiperTabs } from '@/composables/useSwiperTabs';
import VideoPlayerApp from '@/components/app/VideoPlayerApp.vue';
import { getProxyM3u8Url } from '@/api/session';
import { reportPlaybackFail } from '@/api/playback';
import ProxyImage from '@/components/common/ProxyImage.vue';
import ContentTab from '@/components/ContentTab.vue';
import ExpertsTab from '@/components/ExpertsTab.vue';
import BrandsTab from '@/components/BrandsTab.vue';
import ChatTab from '@/components/ChatTab.vue';
import { useAuthStore } from '@/store/auth';
import { usePlayerStore } from '@/store/player';
import { useFavoriteStore } from '@/store/favorite';
import { useFollowStore } from '@/store/follow';
import { useSubscriptionStore } from '@/store/subscription';
import { getSessionDetail, getSessionList } from '@/api/session';
import { getRoomDetail, getRoomList } from '@/api/room';
import { getSessionExperts } from '@/api/expert';
import { getRoomBrands } from '@/api/brand';
import { recordWatch } from '@/api/watchHistory';
import { getPublicRoomTabList } from '@/api/tab';
import { getSessionTags } from '@/api/sessionTags';
import { resolveMediaUrl } from '@/utils/url';
import type { Tab } from '@/types/tab';
import { mockSessionData, mockChatMessages, mockQuestions, mockRelatedSessions, mockMaterials, mockCaseData } from './mock-data';

// 常量
const DEFAULT_AVATAR_PATH = '/static/default-avatar.png';

// 路由参数
const sessionId = ref('');
const roomId = ref('');
const pageTitle = ref('');

// Store
const authStore = useAuthStore();
const playerStore = usePlayerStore();
const favoriteStore = useFavoriteStore();
const followStore = useFollowStore();
const subscriptionStore = useSubscriptionStore();

// 系统信息
const statusBarHeight = ref(0);

// 响应式数据
const sessionInfo = ref<any>(null);
const isLoading = ref(true);
const error = ref('');

// 播放器相关
const playerRef = ref<any>(null);
const playerSourceUrl = ref('');
const initialProgress = ref(0); // 初始播放进度（用于断点续播）

// UI状态
const titleExpanded = ref(false);
const tabsStuck = ref(false);
const activeTab = ref('introduction');
const expertId = ref(''); // 专家ID
const isLiked = ref(false);

// 互动讨论输入框首屏可见（纯几何修复，逻辑零改动）：
// 聊天面板内底部输入条依赖 fixed，但在 swiper/scroll-view 嵌套内容器 fixed 会退化定位，
// 其落点为"面板底部"，而面板底(CSS calc 定高)超出首屏视口 → 需下滑才见输入框。
// 修复：chat 激活时把内容面板(swiper)高度 px 适配为视口剩余（底部=视口底），
// 输入条随面板底部落在首屏视口底部 → 点击互动讨论第一眼即见；离开 chat 恢复 CSS 默认高。
const chatSwiperHeightPx = ref<number | null>(null);
let chatGeometryTimer: ReturnType<typeof setTimeout> | null = null;

// 测量时机：切到 chat 后 scrollToPlayerArea 页面滚动动画(duration 100~150ms)结束再测，
// 避免测到滚动中间态；测高失败静默兜底（维持 CSS calc，行为与修复前一致）
function applyChatPanelHeight() {
  if (chatGeometryTimer) clearTimeout(chatGeometryTimer);
  chatGeometryTimer = setTimeout(() => {
    if (activeTab.value !== 'chat') return; // 测高窗口内已切走：放弃（兜底）
    const query = uni.createSelectorQuery();
    query.select('.content-swiper').boundingClientRect();
    query.exec((rects: any) => {
      const rect = Array.isArray(rects) ? rects[0] : null;
      const top = rect && typeof rect.top === 'number' ? rect.top : 0;
      if (!top) return; // 测高失败：不覆盖，维持 CSS calc
      const windowHeight = uni.getSystemInfoSync().windowHeight || 0;
      if (!windowHeight) return;
      chatSwiperHeightPx.value = Math.max(120, Math.round(windowHeight - top));
    });
  }, 350);
}

// chat 激活/失活联动：激活 → 面板底对齐视口底（输入条首屏可见）；失活 → 恢复 CSS 默认高
watch(activeTab, (key) => {
  if (key === 'chat') {
    applyChatPanelHeight();
  } else {
    if (chatGeometryTimer) {
      clearTimeout(chatGeometryTimer);
      chatGeometryTimer = null;
    }
    chatSwiperHeightPx.value = null;
  }
});

// 从Store读取关注和收藏状态
const isFollowed = computed(() => {
  if (!expertId.value) return false;
  return followStore.isFollowed(expertId.value);
});

const isFavorited = computed(() => {
  if (!roomId.value) return false;
  return favoriteStore.isFavorited(roomId.value);
});

// 订阅状态
const isSubscribed = ref(false);

// 预告倒计时
const countdownText = ref('');

// 网络状态
const networkType = ref('wifi');
const showTrafficWarning = ref(false);

// Tab数据
const chatMessages = ref<any[]>([]);
const questions = ref<any[]>([]);
const relatedSessions = ref<any[]>([]);
const materials = ref<any[]>([]);
const chatInput = ref('');

// 病例数据
const caseInfo = ref('');
const patientInfo = ref<{
  age?: string;
  gender?: string;
  diagnosis?: string;
} | null>(null);

// 专家和品牌数据（用于动态生成Tab）
const experts = ref<any[]>([]);
const brands = ref<any[]>([]);

// 场次标签数据
const sessionTags = ref<any[]>([]);

// 自定义问答输入组件
const showQuestionInput = ref(false);
const questionInput = ref('');

// 处理输入框获取焦点时切换中文输入法
function onInputFocus() {
  // #ifdef APP-PLUS
  try {
    // 方法1: 设置当前窗口的输入法
    const webview = plus.webview.currentWebview();
    if (webview && webview.setStyle) {
      // @ts-ignore - 忽略类型检查，因为plus API类型定义不完整
      webview.setStyle({
        softinputMode: 'adjustResize',
        softinputNavBar: 'none',
        // 使用any类型避免TypeScript错误
        'inputMethodType': 'zh_CN' // 设置默认为中文输入法
      } as any);
    }
    
    // 方法2: 设置输入法辅助类型
    // 根据文档，setAssistantType只支持特定的值
    // @ts-ignore
    if (plus.key && plus.key.setAssistantType) {
      // 使用'none'参数，表示不显示辅助文字
      plus.key.setAssistantType('none');
    }
    
    // 移除导致错误的Android原生API调用
  } catch (e) {
    console.error('设置输入法失败:', e);
  }
  // #endif
}

// 定时器
let countdownTimer: number | null = null;

// 计算属性
const isAuthenticated = computed(() => authStore.isAuthenticated);
const isTitleLong = computed(() => {
  // 获取当前显示的标题
  const title = sessionInfo.value?.title || pageTitle.value || '';
  // 判断标题是否过长（超过一定字符数或包含换行符）
  // 字体28rpx，约19字/行，2行约38字；仅当标题真正超出2行时才显示展开按钮
  return title.length > 38 || title.includes('\n');
});

/** MetaRow 短状态文案（无 emoji，用于 · 分隔行） */
const metaStatusShort = computed(() => {
  const status = sessionInfo.value?.status;
  switch (status) {
    case 'live': return '直播中';
    case 'scheduled': return '预告';
    case 'finished':
    case 'ended':
    case 'archived': return '回放';
    default: return '回放';
  }
});

/** MetaRow 整行文案：回放 · 12/15 14:30（仅状态 + 开播时间，不显示观看数） */
const metaRowText = computed(() => {
  const parts: string[] = [metaStatusShort.value];
  const timeStr = formatTime(sessionInfo.value?.start_time);
  if (timeStr) parts.push(timeStr);
  return parts.join(' · ');
});

/** 预告遮罩封面图：场次封面 → 房间封面（sessionInfo 已自动兜底）→ 直播介绍图 → 静态兜底封面图 */
const coverUrlForPlayer = computed(() => {
  if (sessionInfo.value?.cover_url) return resolveMediaUrl(sessionInfo.value.cover_url) || '/static/default-cover.png';
  const introTab = allTabs.value.find(t => t.tab_key === 'intro');
  if (introTab?.image_url) return resolveMediaUrl(introTab.image_url) || '/static/default-cover.png';
  return '/static/default-cover.png';
});

/** 格式化开播时间 */
const formattedStartTime = computed(() => {
  return formatTime(sessionInfo.value?.start_time || '');
});

// Tab数据（动态获取）
const allTabs = ref<Tab[]>([]);
const isUsingFallback = ref(false);

/**
 * 专家信息第一行：姓名 职称 | 教授（字段用 | 分隔，禁止逗号、顿号）
 */
function formatExpertLine1(expert: { name?: string; title?: string } | null | undefined): string {
  if (!expert) return '主讲专家';
  const name = expert.name || '主讲专家';
  const title = (expert.title || '')
    .replace(/[,，、]\s*/g, ' | ')
    .replace(/\s*\|\s*\|\s*/g, ' | ')
    .trim();
  return title ? `${name} ${title}` : name;
}

/** 专家姓名（ExpertRow 第一行强权重） */
function formatExpertName(expert: { name?: string } | null | undefined): string {
  return expert?.name || '主讲专家';
}

/** 专家职称（ExpertRow 第一行中权重，与姓名用 | 分隔） */
function formatExpertTitle(expert: { title?: string } | null | undefined): string {
  if (!expert?.title) return '';
  return (expert.title || '')
    .replace(/[,，、]\s*/g, ' | ')
    .replace(/\s*\|\s*\|\s*/g, ' | ')
    .trim();
}

function resolveExpertAvatar(expert: { avatar?: string; avatar_url?: string } | null | undefined): string {
  const raw = expert?.avatar || expert?.avatar_url || '';
  return resolveMediaUrl(raw) || raw;
}

/**
 * 专家信息第二行：医院 | 科室（字段用 | 分隔）
 */
function formatExpertLine2(expert: { hospital?: string; department?: string } | null | undefined): string {
  if (!expert) return '';
  const parts = [expert.hospital, expert.department].filter(Boolean) as string[];
  return parts.join(' | ');
}

function buildCreatorFallbackExpert(roomData: any): any {
  return {
    id: '',
    name: roomData?.user_name || '用户',
    title: '',
    hospital: '',
    department: '',
    avatar_url: roomData?.user_avatar_url || '',
    avatar: roomData?.user_avatar_url || ''
  };
}

// 动态生成降级Tab（根据实际数据）
function generateFallbackTabs(): Tab[] {
  const tabs: Tab[] = [];
  let sortOrder = 1;

  // 1. 直播介绍Tab（使用真实的sessionInfo数据）
  tabs.push({
    id: 'fallback-intro',
    room_id: roomId.value,
    tab_key: 'intro',
    title: '直播介绍',
    content_type: 'text',
    text_content: sessionInfo.value?.summary || sessionInfo.value?.description || '暂无介绍',
    image_url: null,
    sort_order: sortOrder++,
    is_active: true,
    created_at: '',
    updated_at: ''
  });

  // 2. 专家Tab（如果有专家数据）
  if (experts.value && experts.value.length > 0) {
    tabs.push({
      id: 'fallback-experts',
      room_id: roomId.value,
      tab_key: 'experts',
      title: '专家介绍',
      content_type: 'text',
      text_content: '',
      image_url: null,
      sort_order: sortOrder++,
      is_active: true,
      created_at: '',
      updated_at: ''
    });
  }

  // 3. 品牌Tab（如果有品牌数据）
  if (brands.value && brands.value.length > 0) {
    tabs.push({
      id: 'fallback-brands',
      room_id: roomId.value,
      tab_key: 'brands',
      title: '品牌介绍',
      content_type: 'text',
      text_content: '',
      image_url: null,
      sort_order: sortOrder++,
      is_active: true,
      created_at: '',
      updated_at: ''
    });
  }

  // 4. 互动讨论Tab（医疗化命名，原聊天）
  tabs.push({
    id: 'fallback-chat',
    room_id: roomId.value,
    tab_key: 'chat',
    title: '互动讨论',
    content_type: 'text',
    text_content: '',
    image_url: null,
    sort_order: sortOrder++,
    is_active: true,
    created_at: '',
    updated_at: ''
  });

  return tabs;
}

// 当前选中的Tab
const currentTab = computed(() => {
  return allTabs.value.find(tab => tab.tab_key === activeTab.value);
});

// 兼容旧的tabs格式（用于Tab导航显示）；聊天→互动讨论 医疗化
const tabs = computed(() => {
  return allTabs.value.map(tab => ({
    key: tab.tab_key,
    label: tab.tab_key === 'chat' ? '互动讨论' : tab.title
  }));
});

/**
 * Tab 索引 ↔ 业务联动
 * @description 点击 Tab 头 / 滑动 swiper 均会触发；设置 activeTab 并执行原有的"回滚到播放器"逻辑
 */
function onTabActivated(idx: number): void {
  const tab = tabs.value[idx];
  if (!tab) return;
  activeTab.value = tab.key;
  scrollToPlayerArea();
}

/** 使用滑动 Tab（点击 ↔ swiper 双向联动）
 * 注意：tabs 为异步加载（loadRoomTabs 拉取后 allTabs 才填充），
 * 必须传 tabs 计算属性本身（响应式 total），使 total 从 0 变为 N 时 activeIndex 能正确归一化；
 * 若传 tabs.value.length（固定 0）会导致 normalizeIndex 越界返回 -1，高亮/内容全部失效。
 */
const { activeIndex, handleTabTap, handleSwiperChange } = useSwiperTabs(
  tabs,
  onTabActivated,
  0
);

/** 内容区 swiper 高度由 CSS 类 .content-swiper 控制（calc(100vh - 400rpx)，与原有布局一致） */

// 监听 allTabs 异步加载完成，同步初始索引（首屏默认选中第一个 Tab）
watch(
  () => allTabs.value.length,
  (len) => {
    if (len > 0) {
      const defaultKey = activeTab.value || allTabs.value[0].tab_key;
      const idx = tabs.value.findIndex(t => t.key === defaultKey);
      if (idx >= 0 && idx !== activeIndex.value) {
        activeIndex.value = idx;
      }
    }
  },
  { immediate: true }
);

// 监听 activeTab 程序化变化（如 scrollToMaterials 直接设置），同步 swiper 索引
watch(activeTab, (key) => {
  const idx = tabs.value.findIndex(t => t.key === key);
  if (idx >= 0 && idx !== activeIndex.value) {
    activeIndex.value = idx;
  }
});

// 页面加载
onLoad((options: any) => {
  sessionId.value = options.sessionId || '';
  roomId.value = options.roomId || '';
  
  // 接收progress参数（用于断点续播）
  const progress = Number(options.progress) || 0;
  if (progress > 0) {
    initialProgress.value = progress;
    console.log('[LiveView] 断点续播：接收到进度参数', progress, '秒');
  }
  
  // 从首页卡片传入的标题作为备用
  if (options.title) {
    try {
      pageTitle.value = decodeURIComponent(options.title);
    } catch {
      pageTitle.value = options.title;
    }
  }
  // 初始显示占位标题，数据加载完成后根据status更新（不使用"加载中..."避免与页面自绘加载层重复）
  uni.setNavigationBarTitle({ title: '直播' });
});

onMounted(async () => {
  // 获取系统信息
  const systemInfo = uni.getSystemInfoSync();
  statusBarHeight.value = systemInfo.statusBarHeight || 0;
  
  await loadSessionData();
  initNetworkListener();
});

onShow(async () => {
  // 页面显示时刷新数据
  await loadSessionData();
});

onBeforeUnmount(() => {
  stopCountdown();
  // 清理聊天面板测高定时器，防止卸载后触发 DOM 查询
  if (chatGeometryTimer) {
    clearTimeout(chatGeometryTimer);
    chatGeometryTimer = null;
  }
});

// 🎯 LiveView 混合API模式配置
const LIVEVIEW_API_MODE = {
  // 播放核心功能：使用真实API
  useRealAPI: {
    room: true,           // ✅ 房间信息（标题、封面）
    session: true,        // ✅ 场次信息（播放地址）
    playback: true,       // ✅ 播放地址
  },
  // 互动功能：暂时使用Mock
  useMockData: {
    chat: true,           // 🔄 聊天消息
    qa: true,             // 🔄 问答
    recommend: false,     // ✅ 推荐列表（已改为真实API）
    materials: true,      // 🔄 资料下载
  }
};

// 数据加载
async function loadSessionData() {
  try {
    isLoading.value = true;
    
    // ===== 🎯 播放核心数据：使用真实API =====
    if (LIVEVIEW_API_MODE.useRealAPI.session) {
      console.log('[LiveView] ✅ 混合API模式：播放核心使用真实API');

      // 1. 通过 roomId 或 sessionId 获取场次信息
      if (!sessionId.value && roomId.value) {
        // 获取房间详情，查找当前场次ID
        const roomResponse = await getRoomDetail(roomId.value, { showLoading: false });
        const room = (roomResponse as any).data || roomResponse;
        
        if (room.current_session_id) {
          sessionId.value = room.current_session_id;
        } else {
          // 获取房间的场次列表
          const sessionsResponse = await getSessionList(roomId.value, { page: 1, size: 1 }, { showLoading: false });
          const sessions = (sessionsResponse as any).data?.items || (sessionsResponse as any).items || [];
          
          if (sessions.length > 0) {
            sessionId.value = sessions[0].id;
          } else {
            error.value = '该房间暂无可用场次';
            isLoading.value = false;
            return;
          }
        }
      }

      if (!sessionId.value) {
        error.value = '缺少场次ID或房间ID';
        isLoading.value = false;
        return;
      }

      // 2. 获取场次详情（包含播放地址）
      const sessionResponse = await getSessionDetail(sessionId.value, { showLoading: false });
      
      // 正确提取：response.data.data（后端返回格式：{code, message, data}）
      sessionInfo.value = (sessionResponse as any).data?.data || (sessionResponse as any).data || sessionResponse;
      
      // ===== 重要：从场次详情同步更新roomId，确保收藏状态检测正确 =====
      if (sessionInfo.value?.room_id && !roomId.value) {
        roomId.value = sessionInfo.value.room_id;
        console.log('[LiveView] 📦 从场次同步roomId:', roomId.value);
      }
      
      console.log('[LiveView] 📦 场次详情:', sessionInfo.value?.id);
      console.log('[LiveView] ✅ 播放地址:', sessionInfo.value?.playback_url || 'undefined');
      
      // ===== 3. 从房间信息获取标题（场次API不返回title） =====
      const currentRoomId = sessionInfo.value?.room_id || roomId.value;
      let roomDetailData: any = null;
      if (currentRoomId) {
        try {
          const roomDetailRes = await getRoomDetail(currentRoomId, { showLoading: false });
          roomDetailData = (roomDetailRes as any).data?.data || (roomDetailRes as any).data || roomDetailRes;
          
          if (roomDetailData?.title && !sessionInfo.value?.title) {
            sessionInfo.value.title = roomDetailData.title;
            console.log('[LiveView] ✅ 从房间获取标题:', roomDetailData.title);
          }
          if (roomDetailData?.cover_url) {
            sessionInfo.value.cover_url = roomDetailData.cover_url;
          }
        } catch (err) {
          console.warn('[LiveView] 获取房间详情失败:', err);
        }
      }
      
      // 如果仍然没有标题，使用pageTitle或默认值
      if (!sessionInfo.value?.title) {
        sessionInfo.value.title = pageTitle.value || '精彩直播';
        console.log('[LiveView] ⚠️ 使用默认标题:', sessionInfo.value.title);
      }
      
      console.log('[LiveView] 📋 最终标题:', sessionInfo.value?.title);

      // ===== 🔄 获取场次专家信息（调用真实API） =====
      try {
        const expertsResponse = await getSessionExperts(sessionId.value, undefined, { showLoading: false });
        const expertsData = (expertsResponse as any).data?.data || (expertsResponse as any).data || [];
        
        console.log('[LiveView] 📋 专家API响应:', expertsResponse);
        console.log('[LiveView] 📋 专家列表数据:', expertsData);
        
        if (expertsData && expertsData.length > 0) {
          // 保存专家列表（用于动态生成Tab）
          experts.value = expertsData;
          
          // 获取主讲专家（role='主讲'）或第一个专家
          const mainExpert = expertsData.find((e: any) => e.role === '主讲') || expertsData[0];
          sessionInfo.value.expert = mainExpert;
          expertId.value = mainExpert.id;
          console.log('[LiveView] ✅ 已获取真实专家信息:', mainExpert.name);
          console.log('[LiveView] ✅ 专家ID:', expertId.value);
          console.log('[LiveView] ✅ 专家列表数量:', experts.value.length);
        } else {
          console.log('[LiveView] ⚠️ 该场次没有关联专家，使用房间创建者兜底');
          experts.value = [];
          sessionInfo.value.expert = buildCreatorFallbackExpert(roomDetailData);
          expertId.value = '';
        }
      } catch (error) {
        console.error('[LiveView] ❌ 获取专家信息失败，使用房间创建者兜底:', error);
        experts.value = [];
        sessionInfo.value.expert = buildCreatorFallbackExpert(roomDetailData);
        expertId.value = '';
      }

      // ===== 🔄 获取房间品牌信息（调用真实API） =====
      try {
        const brandsResponse = await getRoomBrands(roomId.value);
        const brandsData = (brandsResponse as any).data?.data || (brandsResponse as any).data || [];
        
        console.log('[LiveView] 📋 品牌API响应:', brandsResponse);
        console.log('[LiveView] 📋 品牌列表数据:', brandsData);
        
        if (brandsData && brandsData.length > 0) {
          brands.value = brandsData;
          console.log('[LiveView] ✅ 品牌列表数量:', brands.value.length);
        } else {
          console.log('[LiveView] ⚠️ 该房间没有关联品牌');
          brands.value = [];
        }
      } catch (error) {
        console.error('[LiveView] ❌ 获取品牌信息失败:', error);
        brands.value = [];
      }

      // ===== 🔄 获取场次标签（调用真实API） =====
      try {
        const tagsResponse = await getSessionTags(sessionId.value);
        const tagsData = (tagsResponse as any).data?.data || (tagsResponse as any).data || [];
        if (tagsData && tagsData.length > 0) {
          sessionTags.value = tagsData;
          console.log('[LiveView] ✅ 场次标签:', tagsData.map((t: any) => t.name));
        } else {
          sessionTags.value = [];
          console.log('[LiveView] ⚠️ 该场次没有关联标签');
        }
      } catch (error) {
        console.error('[LiveView] ❌ 获取场次标签失败:', error);
        sessionTags.value = [];
      }

      // ===== 🔄 互动数据：使用Mock =====
      if (LIVEVIEW_API_MODE.useMockData.chat) {
        chatMessages.value = mockChatMessages;
        console.log('[LiveView] 🔄 使用Mock聊天数据');
      }
      if (LIVEVIEW_API_MODE.useMockData.qa) {
        questions.value = mockQuestions;
        console.log('[LiveView] 🔄 使用Mock问答数据');
      }
      if (LIVEVIEW_API_MODE.useMockData.recommend) {
        relatedSessions.value = mockRelatedSessions;
        console.log('[LiveView] 🔄 使用Mock推荐数据');
      } else {
        // ✅ 使用真实API获取推荐列表
        await loadRelatedSessions();
      }
      if (LIVEVIEW_API_MODE.useMockData.materials) {
        materials.value = mockMaterials;
        console.log('[LiveView] 🔄 使用Mock资料数据');
      }

      // ===== 🔄 病例数据：优先使用API，否则使用Mock =====
      if (sessionInfo.value.case_description) {
        caseInfo.value = sessionInfo.value.case_description;
        console.log('[LiveView] ✅ 使用API病例数据');
      } else {
        caseInfo.value = mockCaseData.description;
        patientInfo.value = mockCaseData.patientInfo;
        console.log('[LiveView] 🔄 使用Mock病例数据');
      }

      // 设置播放地址
      setupPlayerSource();

      // 根据status设置导航栏标题
      updateNavigationTitle();

      // 预告倒计时（仅 scheduled 生效）
      startCountdown();

      // 加载Tab列表
      await loadRoomTabs();

      // ===== 🔄 检查订阅/收藏和关注状态（从服务器同步） =====
      if (authStore.isAuthenticated) {
        // 根据场次状态决定检查订阅还是收藏
        const status = sessionInfo.value?.status;
        if (status === 'scheduled') {
          // 预告场次 → 检查订阅状态
          if (sessionId.value) {
            try {
              isSubscribed.value = await subscriptionStore.checkSessionIsSubscribedFromApi(sessionId.value);
              console.log('[LiveView] ✅ 已同步订阅状态');
            } catch (error) {
              console.error('[LiveView] ❌ 检查订阅状态失败:', error);
            }
          }
        } else {
          // 直播/回放 → 检查收藏状态（原有逻辑）
          if (roomId.value) {
            try {
              await favoriteStore.checkIsFavoritedFromApi(roomId.value);
              console.log('[LiveView] ✅ 已同步收藏状态');
            } catch (error) {
              console.error('[LiveView] ❌ 检查收藏状态失败:', error);
            }
          }
        }
        
        // 检查是否关注了专家
        if (expertId.value) {
          try {
            await followStore.checkIsFollowedFromApi(expertId.value);
            console.log('[LiveView] ✅ 已同步关注状态');
          } catch (error) {
            console.error('[LiveView] ❌ 检查关注状态失败:', error);
          }
        }
      }

      isLoading.value = false;
    } else {
      // 完全使用Mock数据
      console.log('[LiveView] 🔄 完全Mock模式：使用本地数据');
      sessionInfo.value = mockSessionData;
      chatMessages.value = mockChatMessages;
      questions.value = mockQuestions;
      relatedSessions.value = mockRelatedSessions;
      materials.value = mockMaterials;
      caseInfo.value = mockCaseData.description;
      patientInfo.value = mockCaseData.patientInfo;
      setupPlayerSource();
      updateNavigationTitle();
      startCountdown();
      isLoading.value = false;
    }
  } catch (err) {
    console.error('[LiveView] 加载数据失败:', err);
    error.value = '加载失败，请重试';
    isLoading.value = false;
  }
}

function setupPlayerSource() {
  const session = sessionInfo.value;
  if (!session) {
    console.warn('[LiveView] sessionInfo为空，无法设置播放地址');
    playerSourceUrl.value = '';
    return;
  }

  // V15：external 场次统一走代理地址（session 关联，防 SSRF；两级重写后切片直连外部）
  if (session.source_type === 'external') {
    playerSourceUrl.value = getProxyM3u8Url(session.id);
    console.log('[LiveView] 🔗 external 场次，播放地址（代理）:', playerSourceUrl.value);
    return;
  }

  // 🎬 播放地址获取策略（push 场次，保持现状）
  if (session.status === 'live') {
    // 直播：优先使用live_url，失败时降级使用playback_url
    playerSourceUrl.value = session.live_url || session.playback_url || '';
    console.log('[LiveView] 🔴 直播模式，播放地址:', playerSourceUrl.value);
  } else if (session.status === 'finished' || session.status === 'ready') {
    // 回放：finished=直播结束后, ready=回放已就绪
    playerSourceUrl.value = session.playback_url || '';
    console.log('[LiveView] 📺 回放模式，播放地址:', playerSourceUrl.value);
  } else {
    // 预告或其他状态
    playerSourceUrl.value = '';
    console.log('[LiveView] ⏰ 预告状态（', session.status, '），暂无播放地址');
  }

  console.log('[LiveView] 播放地址已设置:', {
    status: session.status,
    url: playerSourceUrl.value,
    hasLiveUrl: !!session.live_url,
    hasPlaybackUrl: !!session.playback_url,
    sessionKeys: Object.keys(session)
  });

  if (!playerSourceUrl.value) {
    console.error('[LiveView] ⚠️ 播放地址为空！请检查session数据中的playback_url或live_url字段');
    error.value = '播放地址为空，无法播放';
  }
}

/** 预告倒计时：仅 scheduled 状态生效，每秒更新 text */
function startCountdown() {
  stopCountdown();

  if (sessionInfo.value?.status !== 'scheduled') {
    countdownText.value = '';
    return;
  }

  const startTime = sessionInfo.value?.start_time;
  if (!startTime) {
    countdownText.value = '即将开播';
    return;
  }

  const startMs = new Date(startTime).getTime();
  if (isNaN(startMs)) {
    countdownText.value = '即将开播';
    return;
  }

  const tick = () => {
    const diff = startMs - Date.now();
    if (diff <= 0) {
      countdownText.value = '即将开播';
      stopCountdown();
      return;
    }
    const h = Math.floor(diff / 3600000);
    const m = Math.floor((diff % 3600000) / 60000);
    const s = Math.floor((diff % 60000) / 1000);
    countdownText.value =
      `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  };

  tick();
  countdownTimer = setInterval(tick, 1000) as unknown as number;
}

function stopCountdown() {
  if (countdownTimer !== null) {
    clearInterval(countdownTimer);
    countdownTimer = null;
  }
}

/**
 * 根据session的status更新导航栏标题
 * 后端实际返回的status: 'scheduled' | 'live' | 'finished' | 'ended' | 'archived'
 * - live: 显示"直播间"
 * - finished/ended/archived: 显示"回放"
 * - scheduled: 显示"预告"
 */
function updateNavigationTitle() {
  const status = sessionInfo.value?.status;
  let title = '直播间';
  
  switch (status) {
    case 'live':
      title = '直播间';
      break;
    case 'finished':
    case 'ended':
    case 'archived':
    case 'ready':
      title = '回放';
      break;
    case 'scheduled':
      title = '预告';
      break;
    default:
      title = '直播间';
  }
  
  console.log('[LiveView] 📍 导航栏标题设置为:', title, '(status:', status, ')');
  
  try {
    uni.setNavigationBarTitle({ title });
  } catch (e) {
    console.warn('[LiveView] 设置导航栏标题失败:', e);
  }
}

// 网络监听
function initNetworkListener() {
  uni.getNetworkType({
    success: (res) => {
      networkType.value = res.networkType;
    }
  });

  uni.onNetworkStatusChange((res) => {
    networkType.value = res.networkType;

    // 流量提醒逻辑
    if (res.networkType !== 'wifi' && res.isConnected) {
      const noPrompt = uni.getStorageSync('settings_traffic_reminder');
      if (noPrompt !== false) {
        showTrafficWarning.value = true;
      }
    }
  });
}

// 加载推荐直播列表
async function loadRelatedSessions() {
  try {
    console.log('[LiveView] 🔄 获取推荐直播列表...');
    const res = await getRoomList({ page: 1, size: 6 }, { showLoading: false });
    const rooms = res.data?.items || [];
    
    console.log('[LiveView] ✅ 获取到推荐直播:', rooms.length, '个');
    
    // 转换房间数据为推荐场次格式
    relatedSessions.value = rooms
      .filter(room => room.id !== roomId.value) // 过滤掉当前房间
      .slice(0, 5) // 只取前5个
      .map(room => ({
        id: room.id,
        title: room.title || '精彩直播',
        cover_url: room.cover_url || '/static/default-cover.png',
        start_time: room.updated_at || room.created_at || new Date().toISOString(),
        expert: {
          id: room.id,
          name: room.user_name || '专家',
          avatar: '/static/default-avatar.png',
        },
        status: room.live_status || 'scheduled',
      }));
      
    console.log('[LiveView] ✅ 推荐列表处理完成，共', relatedSessions.value.length, '个');
  } catch (err) {
    console.error('[LiveView] ❌ 获取推荐列表失败:', err);
    // 失败时使用 mock 数据
    relatedSessions.value = mockRelatedSessions;
  }
}

// 加载房间Tab列表
async function loadRoomTabs() {
  if (!roomId.value) {
    console.warn('[LiveView] roomId为空，使用备用Tab');
    allTabs.value = generateFallbackTabs();
    isUsingFallback.value = true;
    activeTab.value = 'intro';
    return;
  }

  try {
    console.log('[LiveView] 🔄 获取房间Tab列表...');
    const response = await getPublicRoomTabList(roomId.value);
    console.log('[LiveView] 📦 原始响应数据:', JSON.stringify(response.data, null, 2));
    
    // ⚠️ 关键修复：后端返回 {code, message, data: {items: []}}
    // 检查response.data是否有items属性（嵌套结构）
    let tabs: Tab[] = [];
    if (response.data && typeof response.data === 'object' && 'items' in response.data) {
      tabs = (response.data as any).items || [];
    } else if (Array.isArray(response.data)) {
      tabs = response.data;
    }
    
    if (tabs && tabs.length > 0) {
      const activeTabs = tabs.filter((tab: Tab) => tab.is_active).sort((a: Tab, b: Tab) => a.sort_order - b.sort_order);
      
      // ⚠️ 关键优化：如果后端只返回intro Tab，自动补充其他Tab
      const hasExpertsTab = activeTabs.some(tab => tab.tab_key === 'experts');
      const hasBrandsTab = activeTabs.some(tab => tab.tab_key === 'brands');
      const hasChatTab = activeTabs.some(tab => tab.tab_key === 'chat');
      
      if (!hasExpertsTab || !hasBrandsTab || !hasChatTab) {
        console.log('[LiveView] ⚠️ 检测到Tab不完整，自动补充备用Tab');
        console.log('[LiveView] 📊 Tab状态:', {
          hasExpertsTab,
          hasBrandsTab,
          hasChatTab,
          expertsDataExists: experts.value && experts.value.length > 0,
          brandsDataExists: brands.value && brands.value.length > 0
        });
        
        // 补充缺失的Tab
        let maxSortOrder = Math.max(...activeTabs.map(t => t.sort_order), 0);
        
        if (!hasExpertsTab && experts.value && experts.value.length > 0) {
          activeTabs.push({
            id: 'fallback-experts',
            room_id: roomId.value,
            tab_key: 'experts',
            title: '专家介绍',
            content_type: 'text',
            text_content: '',
            image_url: null,
            sort_order: ++maxSortOrder,
            is_active: true,
            created_at: '',
            updated_at: ''
          });
          console.log('[LiveView] ➕ 已补充专家Tab');
        }
        
        if (!hasBrandsTab && brands.value && brands.value.length > 0) {
          activeTabs.push({
            id: 'fallback-brands',
            room_id: roomId.value,
            tab_key: 'brands',
            title: '品牌介绍',
            content_type: 'text',
            text_content: '',
            image_url: null,
            sort_order: ++maxSortOrder,
            is_active: true,
            created_at: '',
            updated_at: ''
          });
          console.log('[LiveView] ➕ 已补充品牌Tab');
        }
        
        if (!hasChatTab) {
          activeTabs.push({
            id: 'fallback-chat',
            room_id: roomId.value,
            tab_key: 'chat',
            title: '互动讨论',
            content_type: 'text',
            text_content: '',
            image_url: null,
            sort_order: ++maxSortOrder,
            is_active: true,
            created_at: '',
            updated_at: ''
          });
          console.log('[LiveView] ➕ 已补充聊天Tab');
        }
        
        isUsingFallback.value = true;
      } else {
        isUsingFallback.value = false;
      }
      
      allTabs.value = activeTabs;
      console.log('[LiveView] ✅ 最终Tab列表:', allTabs.value.length, '个');
      console.log('[LiveView] 📋 Tab详细数据:', JSON.stringify(allTabs.value, null, 2));
      
      // ⚠️ 检查intro Tab的内容
      const introTab = allTabs.value.find(tab => tab.tab_key === 'intro');
      if (introTab) {
        console.log('[LiveView] 📝 直播介绍Tab数据:', {
          content_type: introTab.content_type,
          text_content: introTab.text_content,
          text_length: introTab.text_content?.length || 0,
          image_url: introTab.image_url,
          has_text: !!introTab.text_content,
          has_image: !!introTab.image_url
        });
      } else {
        console.warn('[LiveView] ⚠️ 未找到intro Tab');
      }
    } else {
      // 如果后端返回空Tab列表，动态生成备用Tab
      allTabs.value = generateFallbackTabs();
      isUsingFallback.value = true;
      console.warn('[LiveView] 后端返回空Tab列表，使用动态生成的备用Tab，包含', allTabs.value.length, '个Tab');
    }
    
    // 默认选中第一个Tab
    if (allTabs.value.length > 0) {
      activeTab.value = allTabs.value[0].tab_key;
    }
  } catch (error: any) {
    console.error('[LiveView] ❌ 获取Tab列表失败:', error);
    
    // API调用失败，动态生成备用Tab
    allTabs.value = generateFallbackTabs();
    isUsingFallback.value = true;
    activeTab.value = 'intro';
    
    uni.showToast({
      title: '加载Tab失败，使用默认Tab',
      icon: 'none',
      duration: 2000
    });
  }
}

// 事件处理
function handleSegmentChange(data: any) {
  // 分段播放处理
  console.log('分段切换:', data);
}

function handlePlay() {
  playerStore.setPlayingState(true);
  console.log('播放开始');
  
  // 记录观看历史（需要登录）
  if (isAuthenticated.value && sessionId.value) {
    recordWatch(sessionId.value, {
      progress: 0,
      extra: {
        device: 'mobile',
        quality: '1080p',
        platform: 'uni-app'
      }
    }).then(() => {
      console.log('[LiveView] 观看历史已记录');
    }).catch((error) => {
      console.error('[LiveView] 记录观看历史失败:', error);
    });
  } else if (!isAuthenticated.value && sessionId.value) {
    console.log('[LiveView] 📱 用户未登录，跳过观看历史记录');
  }
  
  // 如果有初始进度，在首次播放时跳转
  if (initialProgress.value > 0 && playerRef.value) {
    setTimeout(() => {
      try {
        playerRef.value.seek(initialProgress.value);
        console.log('[LiveView] 断点续播：已跳转到', initialProgress.value, '秒');
        
        // 显示提示
        const minutes = Math.floor(initialProgress.value / 60);
        const seconds = Math.floor(initialProgress.value % 60);
        const timeStr = `${minutes}:${String(seconds).padStart(2, '0')}`;
        uni.showToast({
          title: `已跳转到 ${timeStr}`,
          icon: 'none',
          duration: 2000
        });
        
        // 清除初始进度，避免重复跳转
        initialProgress.value = 0;
      } catch (error) {
        console.error('[LiveView] 跳转进度失败:', error);
      }
    }, 1000); // 等待视频加载完成
  }
}

function handlePause() {
  playerStore.setPlayingState(false);
  console.log('播放暂停');
}

function handlePlaybackError(errorMsg: string) {
  uni.showToast({
    title: '播放失败：' + errorMsg,
    icon: 'none',
    duration: 3000
  });

  // V15：播放失败上报（线上兜底：统计"哪些机型/流播不了"，后端记日志）
  try {
    reportPlaybackFail({
      session_id: sessionInfo.value?.id || '',
      url_hash: playerSourceUrl.value || '',
      error_code: errorMsg,
      device_info: JSON.stringify(uni.getSystemInfoSync()),
    }).catch(() => { /* 上报失败不影响播放体验 */ });
  } catch (e) {
    console.warn('[LiveView] 播放失败上报异常:', e);
  }
}

function toggleTitle() {
  titleExpanded.value = !titleExpanded.value;
}

/**
 * 点击 Tab 后回滚到播放器区域顶部（Tab 头点击/滑动共用）
 * @description 提取自原 switchTab，仅负责滚动，不负责切换（切换由 useSwiperTabs 统一处理）
 */
function scrollToPlayerArea() {
  // 点击tab后自动滚动到播放区域顶部
  nextTick(() => {
    // 优化滚动性能，确保视频播放不受影响
    const scrollOptions = {
      selector: '.player-section',
      duration: 100, // 进一步加快滚动速度
      // 使用更流畅的缓动函数
      easing: 'easeOutCubic',
      // 滚动完成后的回调
      success: () => {
        // 滚动完成后确保视频播放状态正常
        if (playerRef.value && playerStore.isPlaying) {
          // 触发视频重新渲染以防止滚动导致的播放问题
          nextTick(() => {
            console.log('滚动完成，视频播放状态正常');
          });
        }
      },
      fail: (err: any) => {
        console.warn('滚动失败，使用备用方案:', err);
        // 备用方案：直接计算位置并滚动
        uni.createSelectorQuery().select('.player-section').boundingClientRect((rect) => {
          if (rect && !Array.isArray(rect) && rect.top !== undefined) {
            // 获取当前页面滚动位置
            uni.getSystemInfo({
              success: (sysInfo) => {
                const currentScrollTop = uni.getStorageSync('currentScrollTop') || 0;
                uni.pageScrollTo({
                  scrollTop: Math.max(0, rect.top + currentScrollTop - 10), // 稍微向上偏移10px
                  duration: 150,
                  easing: 'easeOutCubic'
                });
              }
            });
          }
        }).exec();
      }
    };

    // 执行滚动
    uni.pageScrollTo(scrollOptions);
  });
}

async function toggleFollow() {
  // 🔴 P0：检查登录状态，未登录时轻量提示
  if (!isAuthenticated.value) {
    uni.showToast({ title: '请先登录', icon: 'none' });
    return;
  }

  // 检查expertId
  if (!expertId.value) {
    console.warn('[LiveView] 专家信息缺失，无法关注');
    return;
  }

  // 检查是否为Mock数据
  if (expertId.value.startsWith('expert-mock-')) {
    uni.showToast({ 
      title: '该直播间暂无专家信息', 
      icon: 'none',
      duration: 2000
    });
    return;
  }

  try {
    if (isFollowed.value) {
      await followStore.unfollowExpert(expertId.value);
      uni.showToast({ title: '已取消关注', icon: 'success' });
    } else {
      await followStore.followExpert(expertId.value);
      uni.showToast({ title: '关注成功', icon: 'success' });
    }
  } catch (error: any) {
    console.error('[LiveView] 关注操作失败:', error);
    
    if (error.code === 2002 || error.message?.includes('已关注')) {
      uni.showToast({ title: '已关注该专家', icon: 'none' });
    } else if (error.code === 2203 || error.message?.includes('未关注')) {
      uni.showToast({ title: '未关注该专家', icon: 'none' });
    } else {
      const msg = error.message || '操作失败，请重试';
      uni.showToast({ title: msg, icon: 'none' });
    }
  }
}

async function toggleFavorite() {
  // 🔴 P0：检查登录状态，未登录时轻量提示
  if (!isAuthenticated.value) {
    uni.showToast({ title: '请先登录', icon: 'none' });
    return;
  }

  // 检查roomId
  if (!roomId.value) {
    uni.showToast({ title: '直播间信息缺失', icon: 'none' });
    return;
  }

  try {
    if (isFavorited.value) {
      await favoriteStore.removeFavorite(roomId.value);
      uni.showToast({ title: '已取消收藏', icon: 'success' });
    } else {
      await favoriteStore.addFavorite(roomId.value);
      uni.showToast({ title: '收藏成功', icon: 'success' });
    }
  } catch (error: any) {
    console.error('[LiveView] 收藏操作失败:', error);
    
    // ===== 优化错误处理：大部分情况显示成功 =====
    // 4001: 已收藏 - 实际上收藏成功了
    // 4002: 未收藏 - 实际上取消成功了
    // 500: 服务器错误 - 可能实际操作成功了，Store已做乐观更新
    if (error.code === 4001 || error.message?.includes('已收藏')) {
      uni.showToast({ title: '收藏成功', icon: 'success' });
    } else if (error.code === 4002 || error.message?.includes('未收藏')) {
      uni.showToast({ title: '已取消收藏', icon: 'success' });
    } else if (error.statusCode === 500 || error.code === 1002) {
      // 500错误：Store已做乐观更新，显示成功
      uni.showToast({ title: '收藏成功', icon: 'success' });
    } else {
      // 其他错误才显示失败
      const msg = error.message || '操作失败，请重试';
      uni.showToast({ title: msg, icon: 'none' });
    }
  }
}

function toggleLike() {
  if (!isAuthenticated.value) {
    uni.showToast({ title: '请先登录', icon: 'none' });
    return;
  }

  isLiked.value = !isLiked.value;
  uni.showToast({
    title: isLiked.value ? '已点赞' : '已取消点赞',
    icon: 'none'
  });
}

/**
 * 检查订阅状态（调 API，不依赖本地列表缓存）
 */
async function checkSubscriptionStatus() {
  if (!sessionId.value) return;
  
  if (!authStore.isAuthenticated) {
    console.log('[LiveView] 📱 用户未登录，跳过订阅状态检查');
    isSubscribed.value = false;
    return;
  }
  
  try {
    isSubscribed.value = await subscriptionStore.checkSessionIsSubscribedFromApi(sessionId.value);
  } catch (error) {
    console.error('[LiveView] ❌ 检查订阅状态失败:', error);
    isSubscribed.value = false;
  }
}

/**
 * 切换订阅状态
 */
async function toggleSubscription() {
  if (!isAuthenticated.value) {
    uni.showToast({ title: '请先登录', icon: 'none' });
    return;
  }
  
  if (!sessionId.value) {
    uni.showToast({ title: '无法获取场次信息', icon: 'none' });
    return;
  }
  
  try {
    if (isSubscribed.value) {
      // 取消订阅 - 直接使用 target_type 和 target_id
      await subscriptionStore.unsubscribe('session', sessionId.value);
      isSubscribed.value = false;
      uni.showToast({ title: '已取消订阅', icon: 'success' });
    } else {
      // 添加订阅
      await subscriptionStore.subscribe('session', sessionId.value);
      isSubscribed.value = true;
      uni.showToast({ title: '订阅成功', icon: 'success' });
    }
  } catch (error: any) {
    console.error('订阅操作失败:', error);
    uni.showToast({ title: error.message || '操作失败', icon: 'none' });
  }
}

function downloadContent() {
  if (!isAuthenticated.value) {
    uni.showToast({ title: '请先登录', icon: 'none' });
    return;
  }

  uni.showToast({
    title: '下载功能开发中',
    icon: 'none'
  });
}

function shareContent() {
  // 🔧 分享功能修复：使用 uni.share API 替代 showShareMenu
  // showShareMenu 仅在某些平台（如微信小程序）有效
  
  // #ifdef APP-PLUS || H5
  uni.share({
    provider: 'weixin', // 可选：weixin、sinaweibo、qq等
    type: 0, // 0-图文，1-纯文字，2-纯图片，3-音乐，4-视频，5-小程序
    title: sessionInfo.value?.title || '精彩直播分享',
    summary: sessionInfo.value?.summary || '快来观看这场精彩直播！',
    href: window.location.href,
    imageUrl: sessionInfo.value?.cover_url || '/static/default-cover.png',
    success: (res) => {
      console.log('分享成功', res);
      uni.showToast({
        title: '分享成功',
        icon: 'success'
      });
    },
    fail: (err) => {
      console.error('分享失败', err);
      // 降级方案：使用系统分享
      // #ifdef H5
      if (navigator.share) {
        navigator.share({
          title: sessionInfo.value?.title || '精彩直播分享',
          text: sessionInfo.value?.summary || '快来观看这场精彩直播！',
          url: window.location.href
        }).then(() => {
          uni.showToast({ title: '分享成功', icon: 'success' });
        }).catch(err => {
          console.error('系统分享失败', err);
          uni.showToast({ title: '分享功能暂不可用', icon: 'none' });
        });
      } else {
        uni.showToast({ title: '当前环境不支持分享', icon: 'none' });
      }
      // #endif
      
      // #ifdef APP-PLUS
      uni.showToast({
        title: '请先配置分享参数',
        icon: 'none'
      });
      // #endif
    }
  });
  // #endif
  
  // #ifdef MP-WEIXIN
  uni.showShareMenu({
    withShareTicket: true,
    success: () => {
      uni.showToast({ title: '请点击右上角分享', icon: 'none' });
    }
  });
  // #endif
}

/** 更多操作：ActionSheet 收纳点赞/订阅|下载/分享（方案 A） */
function openMoreActionSheet() {
  const isScheduled = sessionInfo.value?.status === 'scheduled';
  const itemList = isScheduled ? ['点赞', '订阅', '分享'] : ['点赞', '下载', '分享'];
  uni.showActionSheet({
    itemList,
    success: (res) => {
      if (isScheduled) {
        if (res.tapIndex === 0) toggleLike();
        else if (res.tapIndex === 1) toggleSubscription();
        else if (res.tapIndex === 2) shareContent();
      } else {
        if (res.tapIndex === 0) toggleLike();
        else if (res.tapIndex === 1) downloadContent();
        else if (res.tapIndex === 2) shareContent();
      }
    }
  });
}

function downloadMaterials() {
  uni.showToast({
    title: '资料下载功能开发中',
    icon: 'none'
  });
}

/**
 * 滚动到资料区域
 * @description 点击资料按钮后滚动到相关资料区域
 */
function scrollToMaterials() {
  // 切换到详情Tab
  activeTab.value = 'details';
  
  // 延迟滚动到资料区域
  setTimeout(() => {
    uni.createSelectorQuery()
      .select('.materials-section')
      .boundingClientRect((rect: any) => {
        if (rect) {
          // 使用scroll-view的scrollTop
          uni.pageScrollTo({
            scrollTop: rect.top,
            duration: 300
          });
        }
      })
      .exec();
  }, 100);
}

function cancelPlayback() {
  showTrafficWarning.value = false;
  if (playerRef.value) {
    playerRef.value.pause();
  }
}

function continuePlayback() {
  showTrafficWarning.value = false;
  if (playerRef.value) {
    playerRef.value.play();
  }
}

// 切换问题输入区域显示状态
function toggleQuestionInput(show: boolean) {
  showQuestionInput.value = show;
  if (!show) {
    questionInput.value = ''; // 关闭时清空输入
  }
}

// 提交问题
function submitQuestion() {
  if (!questionInput.value.trim()) return;
  
  // 本地模拟添加问题（演示模式）
  const newQuestion = {
    id: `q-${Date.now()}`,
    user: { id: 'current-user', name: '我' },
    content: questionInput.value,
    timestamp: new Date().toISOString(),
    status: 'pending' // 待回答状态
  };

  // 添加到问题列表顶部
  questions.value.unshift(newQuestion);
  
  // 清空输入并关闭输入区
  questionInput.value = '';
  showQuestionInput.value = false;

  uni.showToast({
    title: '问题已提交，专家会尽快回答',
    icon: 'success'
  });
}

// 保留原有弹窗方式作为备用
function showAskDialog() {
  // 在Android平台上，需要先设置一个全局样式
  // #ifdef APP-PLUS
  // @ts-ignore 忽略类型检查
  plus.webview.currentWebview().setStyle({
    popupInputMethodStyle: {
      color: '#333333' // 设置输入文字为深色
    }
  } as any);
  // #endif
  
  uni.showModal({
    title: '我要提问',
    editable: true, // 允许输入
    placeholderText: '请输入您的问题...',
    success: (res) => {
      if (res.confirm && res.content?.trim()) {
        // 本地模拟添加问题（演示模式）
        const newQuestion = {
          id: `q-${Date.now()}`,
          user: { id: 'current-user', name: '我' },
          content: res.content,
          timestamp: new Date().toISOString(),
          status: 'pending' // 待回答状态
        };

        // 添加到问题列表顶部
        questions.value.unshift(newQuestion);

        uni.showToast({
          title: '问题已提交，专家会尽快回答',
          icon: 'success'
        });
      }
    }
  });
}

// 🎯 演示模式：本地模拟聊天交互
function sendMessage() {
  if (!chatInput.value.trim()) return;

  // 🔴 P0：检查登录状态，未登录时轻量提示
  if (!isAuthenticated.value) {
    uni.showToast({ title: '请先登录', icon: 'none' });
    return;
  }

  // 本地模拟发送成功（演示模式）
  const newMsg = {
    id: `msg-${Date.now()}`,
    user: {
      id: 'current-user',
      name: '我',
      avatar: '/static/default-avatar.png'
    },
    content: chatInput.value,
    timestamp: new Date().toISOString()
  };

  // 本地追加消息
  chatMessages.value.push(newMsg);
  chatInput.value = '';

  // 模拟滚动到底部（演示模式）
  nextTick(() => {
    // 这里可以添加滚动到底部的逻辑
    console.log('消息已发送（演示模式）');
  });
}

async function goToSession(session: any) {
  try {
    // 如果是推荐的房间数据，需要先获取该房间的场次列表
    if (!session.session_id && session.id) {
      console.log('[LiveView] 跳转到房间:', session.id);
      // 获取房间的场次列表
      const sessionsRes = await getSessionList(session.id, { page: 1, size: 1 }, { showLoading: false });
      const sessions = (sessionsRes as any).data?.items || sessionsRes.items || [];
      
      if (sessions.length > 0) {
        const targetSession = sessions[0];
        const title = encodeURIComponent(session.title || targetSession.title || '直播');
        uni.navigateTo({
          url: `/pages/app/live/LiveView?sessionId=${targetSession.id}&roomId=${session.id}&title=${title}`
        });
      } else {
        uni.showToast({
          title: '暂无可播放的场次',
          icon: 'none'
        });
      }
    } else {
      // 直接跳转到场次
      const title = encodeURIComponent(session.title || '直播');
      uni.navigateTo({
        url: `/pages/app/live/LiveView?sessionId=${session.id}&title=${title}`
      });
    }
  } catch (err) {
    console.error('[LiveView] 跳转失败:', err);
    uni.showToast({
      title: '跳转失败',
      icon: 'none'
    });
  }
}

function downloadMaterial(material: any) {
  uni.showToast({
    title: '下载功能开发中',
    icon: 'none'
  });
}

// 返回上一页
function handleBack() {
  uni.navigateBack({
    fail: () => {
      // 如果无法返回，则跳转到首页
      uni.switchTab({
        url: '/pages/app/tabbar/home/index'
      });
    }
  });
}

// 工具函数

function formatTime(timeStr: string): string {
  if (!timeStr) return '';

  try {
    // 清洗时间字符串
    // 1. 去除微秒部分（支持任意位数）
    // 2. 处理 +00:00Z 或 +00:00 或 Z 的情况
    let cleaned = timeStr.replace(/\.\d+/, ''); // 去除所有微秒
    
    // 移除尾部的 Z（如果存在 +00:00 后面的 Z）
    if (cleaned.endsWith('+00:00Z')) {
      cleaned = cleaned.replace('+00:00Z', 'Z');
    } else if (cleaned.endsWith('+00:00')) {
      cleaned = cleaned.replace('+00:00', 'Z');
    } else if (!cleaned.endsWith('Z') && !cleaned.includes('+')) {
      cleaned = cleaned + 'Z'; // 添加 Z 如果没有时区信息
    }
    
    const date = new Date(cleaned);
    
    // 验证日期是否有效
    if (isNaN(date.getTime())) {
      console.error('无效的日期:', timeStr, '清洗后:', cleaned);
      return '时间格式错误';
    }

    const now = new Date();
    const currentYear = now.getFullYear();
    const dateYear = date.getFullYear();
    
    // 判断是否是今年
    if (dateYear === currentYear) {
      // 今年：只显示 MM/DD HH:mm
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      const hour = String(date.getHours()).padStart(2, '0');
      const minute = String(date.getMinutes()).padStart(2, '0');
      return `${month}/${day} ${hour}:${minute}`;
    } else {
      // 往年：显示 YYYY/MM/DD HH:mm
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      const hour = String(date.getHours()).padStart(2, '0');
      const minute = String(date.getMinutes()).padStart(2, '0');
      return `${year}/${month}/${day} ${hour}:${minute}`;
    }
  } catch (err) {
    console.error('时间格式化失败:', err, 'timeStr:', timeStr);
    return '时间格式错误';
  }
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}
</script>

<style lang="scss" scoped>
.live-view-page {
  min-height: 100vh;
  background-color: #f5f5f5;
  width: 100%;
  max-width: 100vw;
  overflow-x: hidden;
  box-sizing: border-box;
}

/* ConsumerLayout：单背景、去卡片 */
.live-view-page.consumer-layout {
  background-color: var(--home-bg);
  min-height: 100vh;
}

.info-section {
  position: relative;
  z-index: 10;
  background-color: var(--home-bg);
  margin-bottom: var(--home-spacing-inner);
}

/* 四层 Header 共享同一 padding-left，ExpertRow 不独立缩进 */
.info-section .header-inner {
  padding-left: var(--home-spacing-module);
  padding-right: var(--home-spacing-module);
  padding-top: var(--home-spacing-page);
  padding-bottom: var(--home-spacing-page);
}

.info-header {
  .title-row {
    display: flex;
    align-items: flex-start;
    margin-bottom: var(--home-spacing-inner);
    gap: var(--home-spacing-inner);
  }

  .live-title {
    flex: 1;
    font-size: var(--home-fs-card-title);
    font-weight: 600;
    color: var(--home-text1);
    line-height: 1.4;
    word-break: break-all;
  }

  .live-title.expanded {
    display: block;
    white-space: normal;
  }

  .live-title:not(.expanded) {
    display: -webkit-box;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 2;
    line-clamp: 2;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .expand-btn {
    flex-shrink: 0;
    display: flex;
    align-items: center;
    min-height: 88rpx;
    min-width: 88rpx;
    padding: var(--home-spacing-inner) var(--home-spacing-module);
    background-color: rgba(15, 118, 110, 0.08);
    border-radius: var(--home-r-pill);
    font-size: var(--home-fs-meta);
    color: var(--home-primary);
    white-space: nowrap;
    transition: var(--transition-base);
  }

  .expand-btn:active {
    background-color: rgba(15, 118, 110, 0.15);
    transform: scale(0.98);
  }

  .expand-btn .expand-icon {
    margin-left: 4rpx;
    font-size: 20rpx;
  }

  .expand-btn.collapse {
    background-color: var(--home-bg);
    color: var(--home-text2);
  }

  .expand-btn.collapse:active {
    background-color: var(--home-border-light);
  }

  .meta-row {
    margin-bottom: var(--home-spacing-inner);
  }

  .meta-row .meta-row-text {
    font-size: var(--home-fs-meta);
    color: var(--home-text2);
    opacity: 0.9;
  }

  /* 场次标签行 */
  .tag-row {
    display: flex;
    flex-wrap: wrap;
    gap: 12rpx;
    margin-bottom: var(--home-spacing-inner);
  }

  .tag-chip {
    display: inline-block;
    padding: 4rpx 16rpx;
    font-size: 22rpx;
    color: var(--home-primary);
    background-color: rgba(15, 118, 110, 0.08);
    border-radius: var(--home-r-pill);
    border: 1rpx solid rgba(15, 118, 110, 0.15);
    line-height: 1.6;
  }

  .expert-row {
    display: flex;
    align-items: center;
    margin-bottom: var(--home-spacing-module);
    gap: var(--home-spacing-inner);
  }

  .expert-row .host-info {
    flex: 1;
    min-width: 0;
  }

  .expert-row .host-avatar {
    width: 56rpx;
    height: 56rpx;
    border-radius: var(--radius-circle);
    flex-shrink: 0;
  }

  .expert-row .host-main-line {
    display: flex;
    align-items: center;
    min-width: 0;
    gap: 8rpx;
  }

  .expert-row .host-name {
    font-size: var(--home-fs-meta);
    font-weight: 600;
    color: var(--home-text1);
    line-height: 1.3;
  }

  .expert-row .host-title-sep,
  .expert-row .host-title {
    font-size: var(--home-fs-meta);
    color: var(--home-text2);
    opacity: 0.85;
    line-height: 1.3;
  }

  .expert-row .host-hospital {
    display: block;
    font-size: var(--home-fs-meta);
    color: var(--home-text2);
    opacity: 0.75;
    line-height: 1.3;
    margin-top: 2rpx;
  }

  .expert-row .follow-btn {
    flex-shrink: 0;
    min-height: 88rpx;
    padding: var(--home-spacing-inner) var(--home-spacing-module);
    background-color: var(--home-bg);
    color: var(--home-text2);
    border: 1rpx solid var(--home-border);
    border-radius: var(--home-r-pill);
    font-size: var(--home-fs-meta);
    transition: var(--transition-base);
  }

  .expert-row .follow-btn::after {
    border: none;
  }

  .expert-row .follow-btn.followed {
    background-color: var(--home-primary);
    color: var(--color-text-on-primary);
    border-color: var(--home-primary);
  }

  /* 收藏/分享/点赞：医疗系统工具栏，三等分平铺、icon+轻标签、无平台化（PlaybackActionBar + UI-UX-PRO-MAX） */
  .action-row.playback-actionbar {
    width: 100%;
    display: flex;
    align-items: stretch;
    justify-content: space-between;
    margin-top: var(--home-spacing-module);
    margin-bottom: 0;
    padding-bottom: var(--home-spacing-inner);
    min-height: 120rpx;
  }

  .action-row .action-item {
    flex: 1;
    min-height: 88rpx;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    transition: opacity 0.2s ease, color 0.2s ease, transform 0.2s ease;
  }

  .action-row .action-item:active {
    opacity: 0.9;
    transform: scale(0.96);
  }

  .action-row .action-icon-wrap {
    width: 40rpx;
    height: 40rpx;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  /* iconfont图标样式 */
  .action-row .iconfont {
    font-size: 40rpx;
    line-height: 1;
    color: #999;
    transition: color 0.2s ease;
  }

  /* 保留原有样式兼容性 */
  .action-row .action-icon-inner {
    font-size: 40rpx;
    line-height: 1;
    color: #999;
    transition: color 0.2s ease;
  }

  .action-row .action-item.is-active .iconfont {
    color: #0F766E;
  }

  .action-row .action-item.is-active .action-icon-inner {
    color: #0F766E;
  }

  /* 轻标签：--home-fs-meta，--home-text2，opacity 0.75~0.85，无 bold */
  .action-row .action-label {
    margin-top: var(--home-spacing-inner);
    font-size: var(--home-fs-meta);
    color: var(--home-text2);
    opacity: 0.8;
    font-weight: normal;
    line-height: 1.2;
  }
}

/* 播放器区域：纯净，无悬浮气泡 */
.player-section {
  position: relative;
  width: 100%;
  background-color: #000;
  margin-bottom: var(--home-spacing-module);

  :deep(.video-player-app) {
    width: 100%;
    height: 56.25vw;
    max-height: 60vh;
  }
}

/* 预告遮罩：封面图 + 渐变 + 倒计时 */
.scheduled-overlay {
  position: relative;
  width: 100%;
  height: 56.25vw;
  max-height: 60vh;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  overflow: hidden;
}

.scheduled-bg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.scheduled-gradient {
  position: absolute;
  inset: 0;
  background: linear-gradient(rgba(0, 0, 0, 0.3), rgba(0, 0, 0, 0.7));
}

.scheduled-content {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #fff;
  padding: 40rpx;
}

.scheduled-badge {
  display: inline-block;
  padding: 8rpx 28rpx;
  border-radius: 20rpx;
  background: rgba(255, 255, 255, 0.2);
  font-size: 24rpx;
  color: #fff;
  margin-bottom: 28rpx;
}

.scheduled-countdown {
  font-size: 64rpx;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  letter-spacing: 6rpx;
  line-height: 1.2;
  margin-bottom: 24rpx;
}

.scheduled-time {
  font-size: 26rpx;
  opacity: 0.8;
}

/* 流量提醒弹窗（tokens） */
.traffic-warning-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;

  .modal-content {
    background-color: var(--home-card);
    border-radius: var(--home-r-lg);
    padding: var(--home-spacing-module) var(--home-spacing-page);
    margin: var(--home-spacing-module);
    max-width: 600rpx;
    text-align: center;

    .warning-icon {
      font-size: 80rpx;
      margin-bottom: var(--home-spacing-module);
    }

    .warning-title {
      display: block;
      font-size: var(--home-fs-card-title);
      font-weight: 600;
      color: var(--home-text1);
      margin-bottom: var(--home-spacing-inner);
    }

    .warning-message {
      display: block;
      font-size: var(--home-fs-meta);
      color: var(--home-text2);
      line-height: 1.5;
      margin-bottom: var(--home-spacing-module);
    }

    .modal-actions {
      display: flex;
      gap: var(--home-spacing-inner);

      button {
        flex: 1;
        min-height: 88rpx;
        padding: var(--home-spacing-inner);
        border-radius: var(--home-r-md);
        border: none;
        font-size: var(--home-fs-meta);
        transition: var(--transition-base);

        &:first-child {
          background-color: var(--home-bg);
          color: var(--home-text2);
        }

        &:last-child {
          background-color: var(--home-primary);
          color: var(--color-text-on-primary);
        }
      }
    }
  }
}

/* Tabs 轻导航：主色选中、细下划线、200ms 动效 */
.sticky-tabs {
  position: sticky;
  top: 0;
  background-color: var(--home-bg);
  z-index: 100;
  border-bottom: 1rpx solid var(--home-border);

  &.stuck {
    box-shadow: var(--home-shadow-card);
  }

  .tabs-container {
    height: 88rpx;
    white-space: nowrap;
  }

  .tab-item {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-height: 88rpx;
    padding: 0 var(--home-spacing-module);
    font-size: var(--home-fs-tab);
    color: var(--home-text2);
    opacity: 0.75;
    position: relative;
    transition: color 0.2s ease, opacity 0.2s ease;

    &::after {
      content: '';
      position: absolute;
      bottom: 0;
      left: 50%;
      transform: translateX(-50%);
      width: 0;
      height: 2rpx;
      background-color: var(--home-primary);
      border-radius: 0;
      transition: width 0.2s ease;
    }

    &.active {
      color: var(--home-primary);
      opacity: 1;
      font-weight: 600;
    }

    &.active::after {
      width: 48rpx;
    }
  }
}

/* Tab 内容区：单背景，与 Tabs 用 spacing 分隔 */
.content-section {
  background-color: var(--home-bg);
  padding-top: var(--home-spacing-inner);

  /* 内容区 swiper：定高（视口 - 头部预留），每个 swiper-item 内独立滚动 */
  .content-swiper {
    width: 100%;
    height: calc(100vh - 400rpx);
  }

  .content-swiper-item {
    height: 100%;
  }

  .content-scroll {
    height: 100%;
  }
}

/* 直播介绍 Tab（tokens） */
.introduction-content {
  padding: 0 var(--home-spacing-module) var(--home-spacing-page);
}

.introduction-content .content-block {
  padding: var(--home-spacing-module) 0;
  border-bottom: 1rpx solid var(--home-border-light);

  &:last-child {
    border-bottom: none;
  }

  .block-title {
    display: block;
    font-size: var(--home-fs-card-title);
    font-weight: 600;
    color: var(--home-text1);
    margin-bottom: var(--home-spacing-inner);
  }

  .block-content {
    font-size: var(--home-fs-meta);
    color: var(--home-text2);
    line-height: 1.6;
    white-space: pre-wrap;
  }

  .tags-list {
    display: flex;
    flex-wrap: wrap;
    gap: var(--home-spacing-inner);
  }

  .tags-list .tag-item {
    padding: var(--home-tag-padding-y) var(--home-tag-padding-x);
    min-height: var(--home-tag-height);
    background-color: var(--home-bg);
    border-radius: var(--home-tag-radius);
    font-size: var(--home-tag-font);
    color: var(--home-text2);
  }
}

/* 病例介绍Tab */
.case-content {
  .content-block {
    padding: 32rpx;
    border-bottom: 1rpx solid #f0f0f0;

    &:last-child {
      border-bottom: none;
    }

    .block-title {
      display: block;
      font-size: 32rpx;
      font-weight: 600;
      color: #333333;
      margin-bottom: 16rpx;
    }

    .block-content {
      font-size: 28rpx;
      color: #666666;
      line-height: 1.6;
      white-space: pre-wrap;
    }

    .info-list {
      .info-item {
        display: flex;
        align-items: flex-start;
        padding: 12rpx 0;
        font-size: 28rpx;

        .info-label {
          color: #999999;
          width: 120rpx;
          flex-shrink: 0;
        }

        .info-value {
          flex: 1;
          color: #333333;
          line-height: 1.5;
        }
      }
    }
  }
}

/* 旧样式兼容（可能被其他地方引用） */
.details-content {
  .content-block {
    padding: 32rpx;
    border-bottom: 1rpx solid #f0f0f0;

    &:last-child {
      border-bottom: none;
    }

    .block-title {
      display: block;
      font-size: 32rpx;
      font-weight: 600;
      color: #333333;
      margin-bottom: 16rpx;
    }

    .block-content {
      font-size: 28rpx;
      color: #666666;
      line-height: 1.6;
    }

    .tags-list {
      display: flex;
      flex-wrap: wrap;
      gap: 16rpx;

      .tag-item {
        padding: 8rpx 16rpx;
        background-color: #f0f0f0;
        border-radius: 12rpx;
        font-size: 24rpx;
        color: #666666;
      }
    }

    .materials-list {
      .material-item {
        display: flex;
        align-items: center;
        padding: 24rpx 0;
        border-bottom: 1rpx solid #f0f0f0;

        &:last-child {
          border-bottom: none;
        }

        .iconfont {
          font-size: 40rpx;
          color: #509cec;
          margin-right: 16rpx;
        }

        .material-name {
          flex: 1;
          font-size: 28rpx;
          color: #333333;
        }

        .material-size {
          font-size: 24rpx;
          color: #999999;
        }
      }
    }
  }
}

/* 聊天Tab（降级）：面板高度跟随内容容器(swiper)。
   chat 激活时 LiveView 将 swiper 高度 px 适配到视口底，此处 100% 同步伸缩，
   使底部输入条落在首屏视口内（原先硬编码 calc(100vh-400rpx) 时面板底超出首屏，输入条需下滑才见） */
.chat-content {
  position: relative;
  height: 100%;
  display: flex;
  flex-direction: column;

  .chat-messages-container {
    flex: 1;
    overflow-y: auto;
    padding-bottom: 120rpx; /* 为固定输入框留出空间 */

    .chat-messages {
      padding: 0 32rpx;

      /* 微信式消息气泡（与 ChatTab 同规格） */
      .message-item {
        display: flex;
        align-items: flex-start;
        margin-bottom: 28rpx;
        max-width: 100%;
      }

      /* 自己：整行翻转 → 头像在右、气泡在右 */
      .message-item.self {
        flex-direction: row-reverse;
      }

      .message-avatar {
        width: 64rpx;
        height: 64rpx;
        border-radius: 50%;
        margin-right: 16rpx;
        flex-shrink: 0;
      }

      .message-item.self .message-avatar {
        margin-right: 0;
        margin-left: 16rpx;
      }

      /* 气泡列：宽度自适应内容；上限 72% 面板宽 */
      .message-body {
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        max-width: 72%;
        min-width: 0;
      }

      .message-item.self .message-body {
        align-items: flex-end;
      }

      /* 气泡外 meta：他人=昵称+时间同行；自己=仅时间 */
      .message-meta {
        display: flex;
        align-items: baseline;
        gap: 12rpx;
        margin-bottom: 6rpx;
        padding: 0 8rpx;
        max-width: 100%;
        box-sizing: border-box;
      }

      .message-user {
        font-size: 22rpx;
        color: var(--home-text2);
        flex-shrink: 0;
        max-width: 320rpx;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .message-time {
        font-size: 20rpx;
        color: var(--home-text2);
        opacity: 0.65;
        flex-shrink: 0;
      }

      /* 气泡本体：仅文字，宽度随内容；他人浅色卡片、自己品牌浅底 */
      .message-bubble {
        padding: 16rpx 24rpx;
        background-color: var(--home-card);
        border: 1rpx solid var(--home-border);
        border-radius: 20rpx;
        max-width: 100%;
        min-width: 0;
        box-sizing: border-box;
      }

      .message-item.self .message-bubble {
        background-color: var(--home-tag-forecast-bg);
        border-color: transparent;
      }

      .message-text {
        display: block;
        font-size: var(--home-fs-meta);
        color: var(--home-text1);
        line-height: 1.5;
        overflow-wrap: break-word;
        word-break: break-all;
      }
    }

    .demo-notice {
      padding: 16rpx 32rpx;
      background-color: #fff7e6;
      border-left: 4rpx solid #ffa500;
      margin: 24rpx 32rpx;
      border-radius: 8rpx;

      text {
        font-size: 24rpx;
        color: #d48806;
      }
    }
  }

  .chat-input-fixed {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background-color: var(--home-bg);
    border-top: 1rpx solid var(--home-border);
    z-index: 1000;
  }

  .chat-input {
    display: flex;
    align-items: center;
    padding: var(--home-spacing-inner) var(--home-spacing-module);
    gap: var(--home-spacing-inner);
  }

  .chat-input-field {
    flex: 1;
    min-height: 88rpx;
    padding: 0 var(--home-spacing-module);
    font-size: var(--home-fs-meta);
    color: var(--home-text1);
    background-color: var(--home-card);
    border: 2rpx solid var(--home-border);
    border-radius: var(--home-r-md);
    transition: var(--transition-base);
    box-sizing: border-box;
  }

  .chat-input-field:focus {
    border-color: var(--home-primary);
  }

  .chat-input-placeholder {
    color: var(--home-text2);
    opacity: 0.85;
  }

  .chat-send-btn {
    min-width: 120rpx;
    min-height: 88rpx;
    padding: 0 var(--home-spacing-module);
    font-size: var(--home-fs-meta);
    color: var(--color-text-on-primary);
    background-color: var(--home-primary);
    border: none;
    border-radius: var(--home-r-md);
    transition: var(--transition-base);
  }

  .chat-send-btn::after {
    border: none;
  }

  .chat-send-btn:active:not([disabled]) {
    opacity: 0.9;
  }

  .chat-send-btn[disabled] {
    background-color: var(--home-border);
    color: var(--home-text2);
    opacity: 0.7;
  }
}

/* 资料Tab */
.materials-content {
  padding: 32rpx;

  .materials-list-container {
    .material-card {
      display: flex;
      align-items: center;
      padding: 32rpx;
      background-color: #ffffff;
      border-radius: 16rpx;
      box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.08);
      margin-bottom: 24rpx;
      transition: all 0.3s ease;

      &:active {
        transform: scale(0.98);
        box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.12);
      }

      .material-icon-wrapper {
        width: 96rpx;
        height: 96rpx;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 16rpx;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 24rpx;

        .material-icon {
          font-size: 48rpx;
          color: #ffffff;
        }
      }

      .material-info {
        flex: 1;
        display: flex;
        flex-direction: column;

        .material-name {
          font-size: 30rpx;
          color: #333333;
          font-weight: 600;
          margin-bottom: 8rpx;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .material-size {
          font-size: 24rpx;
          color: #999999;
        }
      }

      .download-btn {
        width: 80rpx;
        height: 80rpx;
        background-color: #509cec;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;

        .iconfont {
          font-size: 36rpx;
          color: #ffffff;
        }
      }
    }
  }

  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 120rpx 0;

    .empty-icon {
      font-size: 120rpx;
      color: #d9d9d9;
      margin-bottom: 24rpx;
    }

    .empty-text {
      font-size: 28rpx;
      color: #999999;
    }
  }
}

/* 推荐Tab */
.related-content {
  .related-sessions {
    padding: 32rpx;

    .session-card {
      display: flex;
      padding: 24rpx 0;
      border-bottom: 1rpx solid #f0f0f0;

      &:last-child {
        border-bottom: none;
      }

      .session-cover {
        width: 200rpx;
        height: 112rpx;
        border-radius: 8rpx;
        margin-right: 24rpx;
        flex-shrink: 0;
      }

      .session-info {
        flex: 1;

        .session-title {
          display: -webkit-box;
          -webkit-box-orient: vertical;
          -webkit-line-clamp: 2;
          line-clamp: 2;
          overflow: hidden;
          text-overflow: ellipsis;
          font-size: 30rpx;
          font-weight: 600;
          color: #333333;
          margin-bottom: 8rpx;
          line-height: 1.3;
        }

        .session-expert {
          display: block;
          font-size: 26rpx;
          color: #666666;
          margin-bottom: 4rpx;
        }

        .session-time {
          font-size: 24rpx;
          color: #999999;
        }
      }
    }
  }
}
</style>
