<template>
  <el-container class="live-view-container">
    <el-main class="main-content">
      <!-- 加载与错误态 -->
      <el-card v-if="loading" shadow="never" style="margin-top:12px;">
        <div class="loading-container"><div class="spinner"></div><span>正在进入直播间...</span></div>
      </el-card>
      <el-card v-else-if="error" shadow="never" style="margin-top:12px;">
        <div class="status-container">
          <span class="status-text">进入失败：{{ error.message }}</span>
          <el-button type="primary" size="small" @click="goBack">返回</el-button>
        </div>
      </el-card>

      <!-- 主内容区 -->
      <el-row v-else-if="currentSession" :gutter="12" style="margin-top:12px;">
        <el-col :xs="24" :md="16">
          <!-- 顶部信息条（标题/状态/时间） -->
          <el-card shadow="never" class="top-info-bar">
            <el-row justify="space-between" align="middle">
              <el-col :span="16">
                <el-space>
                  <el-text class="live-title">{{ roomDetail?.title || '' }}</el-text>
                  <el-tag class="status-tag" :type="currentSession?.status === 'live' ? 'success' : (currentSession?.status === 'scheduled' ? 'primary' : 'info')">
                    {{ getStatusText(currentSession?.status || 'scheduled') }}
                  </el-tag>
                  <span class="live-time">{{ formatTime(currentSession?.start_time || '') }}</span>
                </el-space>
              </el-col>
              <el-col :span="8" style="text-align:right;">
                <!-- 目标UI上的三个操作入口占位 -->
                <el-space>
                  <el-button link>语言切换</el-button>
                  <el-button link>投诉</el-button>
                  <el-button link>分享</el-button>
                </el-space>
              </el-col>
            </el-row>
          </el-card>
          <!-- 视频播放器区域 -->
          <el-card class="video-player-area" shadow="never">
            <template #default>
              <div class="video-area-wrap">
                
                <!-- 使用 VideoPlayer 组件播放 -->
                <div v-if="isH5 && playerSourceUrl" style="position: relative;">
                  <VideoPlayer :src="playerSourceUrl" />
                  <!-- 播放控制按钮 -->
                  <div style="position: absolute; top: 10px; right: 10px; z-index: 10; display: flex; gap: 5px;">
                    <el-button size="small" type="primary" @click="reloadVideoPlayer">
                      重新加载
                    </el-button>
                    <el-button size="small" type="success" @click="testProxyConnection">
                      测试连接
                    </el-button>
                  </div>
                </div>
                
                <!-- 非 H5 环境的备用播放器 -->
                <div v-else-if="!isH5 && playerSourceUrl" class="fallback-player">
                  <video 
                    :src="playerSourceUrl" 
                    controls 
                    autoplay 
                    muted 
                    playsinline 
                    style="width: 100%; max-width: 800px; height: auto; background: #000;"
                    @loadstart="() => console.log('🎬 备用播放器开始加载')"
                    @canplay="() => console.log('✅ 备用播放器可以播放')"
                    @error="(e) => console.error('❌ 备用播放器错误:', e)"
                  >
                    您的浏览器不支持视频播放
                  </video>
                </div>
                
                <!-- 无播放源时显示占位符 -->
                <div v-else class="status-container placeholder-video">
                  <span class="status-text">{{ emptySourceHint }}</span>
                </div>
              </div>
            </template>
          </el-card>

          <!-- 分会场卡片轮播区域 -->
          <el-card shadow="never" style="margin-top:12px;" v-if="subVenueCards.length > 0">
            <template #header>
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-weight: 600; color: #303133;">分会场</span>
                <el-button type="primary" link @click="goToVenuePage">查看全部</el-button>
              </div>
            </template>
            <div class="sub-venue-carousel">
              <!-- 左侧控制按钮 -->
              <el-button 
                v-if="subVenueCards.length > visibleCards"
                :disabled="currentIndex === 0" 
                @click="prevSlide" 
                size="small" 
                circle
                class="control-btn control-btn-left"
              >
                <el-icon><ArrowLeft /></el-icon>
              </el-button>
              
              <div class="carousel-container" ref="carouselContainer">
                <div class="carousel-track" :style="{ transform: `translateX(-${currentIndex * cardWidth}px)` }">
                  <div 
                    v-for="venue in subVenueCards" 
                    :key="venue.id" 
                    class="venue-card"
                    @click="goToSubVenue(venue.id)"
                  >
                    <div class="venue-card-inner">
                      <el-image class="venue-cover" :src="getCoverSrc(venue.cover_url)" fit="cover" @error="() => (venue.cover_url = '')">
                        <template #error>
                          <div class="img-error">No Image</div>
                        </template>
                      </el-image>
                      <div class="venue-info">
                        <div class="venue-title" :title="venue.title">{{ venue.title }}</div>
                        <div class="venue-meta">
                          <span>开始时间：{{ formatTime(venue._latestStartTime) }}</span>
                        </div>
                      </div>
                      <el-tag class="status-badge" size="small" :type="statusType(venue._latestStatus)">
                        {{ statusText(venue._latestStatus) }}
                      </el-tag>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- 右侧控制按钮 -->
              <el-button 
                v-if="subVenueCards.length > visibleCards"
                :disabled="currentIndex >= maxIndex" 
                @click="nextSlide" 
                size="small" 
                circle
                class="control-btn control-btn-right"
              >
                <el-icon><ArrowRight /></el-icon>
              </el-button>
            </div>
          </el-card>

          <!-- 功能页签区域 -->
          <el-card shadow="never" style="margin-top:12px;">
            <el-tabs>
              <el-tab-pane label="直播介绍">
                <div class="room-description-card">
                  <div class="description-header">
                  </div>
                  <div class="description-content">{{ roomDetail?.description || '暂无简介' }}</div>
                </div>
              </el-tab-pane>
              <el-tab-pane label="病例介绍">
                <div style="color:#909399;">内容待补充</div>
              </el-tab-pane>
              <el-tab-pane label="返回主会场">
                <el-button type="primary" link @click="goToVenuePage">返回主会场</el-button>
              </el-tab-pane>
              <el-tab-pane label="返回营销专题">
                <el-button type="success" link @click="goToTopicDisplay">返回营销专题</el-button>
              </el-tab-pane>
            </el-tabs>
          </el-card>
        </el-col>

        <!-- 右侧聊天互动区域（评论区复刻） -->
        <el-col :xs="24" :md="8">
          <el-aside class="chat-sidebar" width="360px">
            <div class="chat-header">聊天互动</div>
            
            <!-- 管理员消息（占位） -->
            <div class="admin-messages">
              <div style="display:flex;align-items:center;">
                <el-avatar class="admin-avatar" size="small">管</el-avatar>
                <span class="admin-name">管理员</span>
              </div>
              <div class="message-content">欢迎来到直播间，文明发言，理性讨论～</div>
              <div class="message-time">{{ formatTime(currentSession?.start_time || '') }}</div>
            </div>

            <!-- 用户消息列表（复用 mockComments） -->
            <div class="user-messages">
              <div v-for="(comment, idx) in mockComments" :key="idx" class="message-item" style="display:flex;">
                <el-avatar class="user-avatar" size="small">{{ comment.user.slice(0,1) }}</el-avatar>
                <div style="flex:1;">
                  <div class="user-name">{{ comment.user }}</div>
                  <div class="message-text">{{ comment.content }}</div>
                </div>
              </div>
            </div>

            <!-- 输入区域 -->
            <div class="chat-input-area">
              <div class="input-with-icons">
                <div class="input-icons">
                  <el-button link size="small">🙂</el-button>
                  <el-button link size="small">⭐</el-button>
                </div>
                <el-input placeholder="说点什么~" />
              </div>
              <el-button type="primary" size="small">发送</el-button>
            </div>
          </el-aside>
        </el-col>
      </el-row>
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, onBeforeUnmount } from 'vue';
import { onLoad } from '@dcloudio/uni-app';
import { storeToRefs } from 'pinia';
import { useSessionStore } from '../../../store/session';
import UserInfoHeader from '@/components/shared/UserInfoHeader.vue';
import { useRoomStore } from '../../../store/room';
import { getRoomDetail } from '../../../api/room';
import type { SessionStatus } from '../../../types/session';
import AppButton from '@/components/shared/AppButton.vue';
// #ifdef H5
import VideoPlayer from '@/components/h5/VideoPlayerH5.vue';
import { useAuthStore } from '@/store/auth';
// #endif
// 引入 Element Plus 组件与图标（仅用于模板换肤，逻辑不变）
// 由于基于按需自动引入/全量引入策略不同，这里不强制显式注册组件
import { ElContainer, ElMain, ElAside, ElCard, ElRow, ElCol, ElText, ElTag, ElSpace, ElButton, ElTabs, ElTabPane, ElImage, ElIcon, ElMessageBox } from 'element-plus';
import { VideoPlay, ArrowLeft, ArrowRight } from '@element-plus/icons-vue';

const sessionStore = useSessionStore();
const { currentSession, loading, error } = storeToRefs(sessionStore);

const roomStore = useRoomStore();
const { rooms } = storeToRefs(roomStore);

const isH5 = process.env.UNI_PLATFORM === 'h5' || (typeof window !== 'undefined' && window.location.protocol === 'http:');

// 协议切换状态
const useHttpProtocol = ref(false);

// 获取平台信息的安全方式
const platform = computed(() => {
  // #ifdef H5
  return 'h5';
  // #endif
  // #ifdef MP
  return 'mp';
  // #endif
  // #ifdef APP
  return 'app';
  // #endif
  return 'unknown';
});

// 新增：房间详情和仿真评论
const roomDetail = ref<any>(null);
const mockComments = ref([
  { user: '用户小白', content: '直播间讲解很棒，支持！' },
  { user: '路人甲', content: '视频很清晰，主播加油！' },
  { user: '路人乙', content: '有回放吗？错过了前面部分。' }
]);

// 专题相关
const currentTopicId = ref<string | null>(null);

// 轮播相关数据
const currentIndex = ref(0);
const cardWidth = ref(200); // 卡片宽度（更小）
const visibleCards = ref(4); // 可见卡片数量（更多）
const carouselContainer = ref<HTMLElement | null>(null);
const defaultCover = '/public/logo.png';
import { BASE_API_URL } from '@/constants/api';
import topicApi from '@/api/topic';

// 推荐直播间计算属性
const recommendedRooms = computed(() => {
  // 获取最新创建的5个房间，排除当前房间
  const currentRoomId = currentSession.value?.room_id;
  return rooms.value
    .filter(room => room.id !== currentRoomId)
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 5);
});

// 分会场计算属性
const subVenues = computed(() => {
  const currentRoomId = currentSession.value?.room_id;
  if (!currentRoomId) return [];
  // 获取当前房间的子房间（分会场）
  return rooms.value.filter((room: any) => room.parent_room_id === currentRoomId);
});

// 分会场卡片数据
const subVenueCards = computed(() => {
  return subVenues.value.map((room: any) => ({
    ...room,
    _latestStatus: room.status || 'scheduled',
    _latestStartTime: room.start_time || room.created_at,
  }));
});

// 规范化封面
function getCoverSrc(url?: string | null) {
  const u = (url || '').toString();
  if (!u) return defaultCover;
  if (/^https?:\/\//.test(u)) return u;
  const base = BASE_API_URL.replace(/\/+$/, '');
  const origin = base.replace(/\/api\/.*/, '');
  return origin + (u.startsWith('/') ? u : '/' + u);
}

// UUID 校验
function isValidUuid(v?: string) {
  const s = (v || '').toString().trim();
  return /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$/.test(s);
}

// 轮播最大索引
const maxIndex = computed(() => {
  return Math.max(0, subVenueCards.value.length - visibleCards.value);
});

// 计算属性：判断是否显示返回按钮 
const showBackButtons = computed(() => {
  // #ifndef MP
  return true;
  // #endif
  // #ifdef MP
  return false;
  // #endif
});

// 直播流URL（根据房间 stream_key）
const liveUrl = computed(() => {
  const keyFromRoom = (roomDetail.value as any)?.stream_key;
  const streamKey = (keyFromRoom || '').trim();
  if (!streamKey) return null;
  const url = `/hls-proxy/${streamKey}.m3u8`;
  return url;
});

// 是否直播中
const isLive = computed(() => currentSession.value?.status === 'live');

// 播放器实际使用的URL：直播时用 liveUrl；非直播时用后端返回的 playback_url
const playerSourceUrl = computed(() => {
  if (isLive.value) return liveUrl.value;
  const playback = (currentSession.value as any)?.playback_url as string | null | undefined;
  return playback || null;
});

const emptySourceHint = computed(() => {
  return isLive.value ? '暂无有效的播放地址' : '回放未就绪，请稍候...';
});

// 回放轮询：在 ended/archived 后轮询会话详情，直到 playback_url 出现
let playbackPollTimer: number | null = null;
function startPlaybackPolling() {
  stopPlaybackPolling();
  const tryFetch = async () => {
    const s = currentSession.value as any;
    if (!s?.id) return;
    try {
      await sessionStore.fetchSessionById(s.id);
      const updated = sessionStore.currentSession as any;
      if (updated?.playback_url) {
        stopPlaybackPolling();
      }
    } catch {}
  };
  // 立即尝试一次
  tryFetch();
  // 指数退避轮询：2s -> 4s -> ... 最长30s
  let interval = 2000;
  playbackPollTimer = window.setInterval(async () => {
    await tryFetch();
    interval = Math.min(interval * 2, 30000);
  }, interval) as unknown as number;
}

function stopPlaybackPolling() {
  if (playbackPollTimer) {
    clearInterval(playbackPollTimer as unknown as number);
    playbackPollTimer = null;
  }
}

// 监听 session 状态，在结束后开始轮询回放
watch(() => currentSession.value?.status, (next) => {
  if (!next) return;
  if (next === 'ended' || next === 'archived') {
    startPlaybackPolling();
  } else if (next === 'live') {
    stopPlaybackPolling();
  }
}, { immediate: true });

// 跳转到房间详情页
const goToRoomDetail = (roomId: string) => {
  uni.navigateTo({ url: `/pages/room/RoomDetail?id=${roomId}` });
};

// 获取房间状态样式类
const getStatusClass = (status: string) => {
  const statusMap: Record<string, string> = {
    'live': 'status-live',
    'scheduled': 'status-scheduled',
    'ended': 'status-ended',
    'archived': 'status-archived'
  };
  return statusMap[status] || 'status-default';
};

// 获取房间状态文本
const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    'live': '直播中',
    'scheduled': '计划中',
    'ended': '已结束',
    'archived': '已归档'
  };
  return statusMap[status] || '未知';
};

// 格式化时间
const formatTime = (timeStr: string) => {
  if (!timeStr) return '';
  // 预清理：移除微秒和时区，统一形态
  let s = String(timeStr).trim();
  s = s.replace(/\s+/g, 'T'); // 空格转T
  s = s.replace(/\.(\d{1,6})/, ''); // 去掉小数秒
  s = s.replace(/Z$/i, ''); // 去掉Z
  if (s.includes('+')) s = s.split('+')[0]; // 去掉+时区
  if (s.includes('-')) {
    // 有些浏览器更易解析 2025/08/02 形式
    s = s.replace('T', ' ');
  }

  const candidates = [
    s,
    s.replace(/-/g, '/'), // 兜底
  ];

  for (const v of candidates) {
    const d = new Date(v);
    if (!isNaN(d.getTime())) {
      const y = d.getFullYear();
      const m = String(d.getMonth() + 1).padStart(2, '0');
      const day = String(d.getDate()).padStart(2, '0');
      const hh = String(d.getHours()).padStart(2, '0');
      const mm = String(d.getMinutes()).padStart(2, '0');
      const ss = String(d.getSeconds()).padStart(2, '0');
      return `${y}-${m}-${day} ${hh}:${mm}:${ss}`;
    }
  }
  // 解析失败则输出去噪后的日期部分
  const dateOnly = s.split('T')[0] || s.split(' ')[0] || s;
  return dateOnly;
};

// 修改 onLoad，获取房间详情
onLoad(async (options) => {
  const authStore = useAuthStore();
  
  console.log('🚀 LiveView页面加载');
  console.log('🧭 onLoad options:', options);
  console.log('🔍 当前认证状态:', {
    isAuthenticated: authStore.isAuthenticated,
    token: authStore.token,
    user: authStore.user
  });
  
  // 认证检查
  if (!authStore.isAuthenticated) {
    console.log('❌ 用户未认证');
    uni.showToast({ title: '请先登录', icon: 'none' });
    uni.navigateBack({
      fail: () => { uni.switchTab({ url: '/pages/app/tabbar/home/index' }); }
    });
    return;
  }
  
  console.log('✅ 用户已认证，加载直播详情');
  
  // H5 兜底：若未拿到参数，尝试从 URL 中解析
  if ((!options || (!options.id && !(options as any).room_id)) && typeof window !== 'undefined') {
    try {
      const hash = window.location.hash || '';
      const queryStr = hash.includes('?') ? hash.split('?')[1] : '';
      const searchParams = new URLSearchParams(queryStr);
      const idFromUrl = searchParams.get('id') || '';
      const roomIdFromUrl = searchParams.get('room_id') || searchParams.get('roomId') || '';
      (options as any) = {
        ...(options || {}),
        id: idFromUrl || (options as any)?.id,
        room_id: roomIdFromUrl || (options as any)?.room_id,
      } as any;
      console.log('🔎 H5 解析到参数:', { idFromUrl, roomIdFromUrl, merged: options });
    } catch (e) {
      console.warn('解析URL参数失败:', e);
    }
  }

  if (options && typeof options.id === 'string' && options.id) {
    // 场次ID直达
    await sessionStore.fetchSessionById(options.id);
  } else if (options && typeof (options as any).room_id === 'string' && (options as any).room_id) {
    // 仅传了房间ID：拉取该房间的场次列表，选最近的一场
    const roomId = (options as any).room_id as string;
    try {
      await sessionStore.fetchSessionsByRoomId(roomId, { refresh: true });
      const sessions = sessionStore.sessions || [];
      console.log('📦 获取到的场次数量:', sessions.length, sessions);
      if (sessions.length === 0) {
        throw new Error('该房间暂无场次');
      }
      // 优先选择直播中的一场；否则选择开始时间/创建时间最近的一场
      const liveSession = sessions.find((s: any) => s.status === 'live');
      let picked = liveSession;
      if (!picked) {
        picked = [...sessions].sort((a: any, b: any) => {
          const at = new Date(a.start_time || a.created_at || 0).getTime();
          const bt = new Date(b.start_time || b.created_at || 0).getTime();
          return bt - at; // 最近优先
        })[0];
      }
      if (!picked) {
        throw new Error('未能选出可用的场次');
      }
      sessionStore.setCurrentSession(picked);
    } catch (e: any) {
      console.error('根据room_id选择场次失败:', e);
      error.value = new Error(e.message || '无法获取该房间的场次');
      return;
    }
  } else {
    error.value = new Error('无效的场次ID');
    return;
  }

  // 获取房间详情（基于已确定的currentSession）
  const { currentSession } = storeToRefs(sessionStore);
  const session = currentSession.value;
  if (session && session.room_id) {
    try {
      console.log('正在获取房间详情，room_id:', session.room_id);
      const detailResp = await getRoomDetail(session.room_id);
      roomDetail.value = detailResp.data; // 只存 data 字段
      console.log('直播简介:', roomDetail.value.description);
      
      // 获取该直播间关联的专题信息
      await fetchRoomTopics(session.room_id);
    } catch (e) {
      console.error('获取房间详情失败:', e);
      roomDetail.value = null;
    }
  }
});

// 页面加载时获取房间列表
onMounted(async () => {
  console.log('🚀 LiveView onMounted 开始');
  console.log('🔍 当前状态:', {
    isH5,
    currentSession: currentSession.value,
    playerSourceUrl: playerSourceUrl.value,
    rooms: rooms.value.length
  });
  
  await roomStore.fetchRooms();
  
  console.log('✅ 房间列表加载完成:', {
    roomsCount: rooms.value.length,
    currentSession: currentSession.value,
    playerSourceUrl: playerSourceUrl.value
  });
});

// 测试视频播放
const testVideoPlayback = async () => {
  console.log('🧪 开始测试视频播放...');
  
  if (!playerSourceUrl.value) {
    console.error('❌ 没有播放地址');
    return;
  }
  
  // 测试网络连接
  try {
    console.log('🌐 测试 HLS 流网络连接...');
    const response = await fetch(playerSourceUrl.value, { 
      method: 'HEAD',
      mode: 'cors'
    });
    
    console.log('🌐 网络测试结果:', {
      status: response.status,
      statusText: response.statusText,
      headers: Object.fromEntries(response.headers.entries()),
      url: playerSourceUrl.value
    });
    
    if (response.ok) {
      console.log('✅ 网络连接正常');
      
      // 尝试直接播放
      const video = document.querySelector('video');
      if (video) {
        console.log('🎬 尝试直接播放视频...');
        video.src = playerSourceUrl.value;
        await video.play();
        console.log('✅ 视频播放成功');
      } else {
        console.log('❌ 找不到 video 元素');
      }
    } else {
      console.error('❌ 网络连接失败:', response.status, response.statusText);
    }
  } catch (error) {
    console.error('❌ 网络测试失败:', error);
    
    // 检查是否是 CORS 错误
    if (error.message.includes('CORS')) {
      console.error('🌐 CORS 错误：视频服务器不允许跨域访问');
    }
  }
};

// 协议切换函数
const switchToHttp = () => {
  console.log('🔄 切换到HTTP协议');
  useHttpProtocol.value = true;
  console.log('✅ 已切换到HTTP，播放地址已更新');
};

const switchToHttps = () => {
  console.log('🔄 切换到HTTPS协议');
  useHttpProtocol.value = false;
  console.log('✅ 已切换到HTTPS，播放地址已更新');
};

// 测试视频片段下载
const testVideoSegments = async () => {
  console.log('🧪 开始测试视频片段下载...');
  
  if (!playerSourceUrl.value) {
    console.error('❌ 没有播放地址');
    return;
  }
  
  // 从播放地址中提取基础URL
  const baseUrl = playerSourceUrl.value.replace(/\/[^\/]+\.m3u8$/, '');
  console.log('🔗 基础URL:', baseUrl);
  
  // 测试几个视频片段
  const testSegments = [
    'streamkey_3d69fdd073e0b43e78c90fad758cc447-0.ts',
    'streamkey_3d69fdd073e0b43e78c90fad758cc447-1.ts',
    'streamkey_3d69fdd073e0b43e78c90fad758cc447-2.ts'
  ];
  
  for (const segment of testSegments) {
    const segmentUrl = `${baseUrl}/${segment}`;
    console.log(`🔍 测试片段: ${segment}`);
    
    try {
      const response = await fetch(segmentUrl, { 
        method: 'HEAD',
        mode: 'cors'
      });
      
      console.log(`✅ 片段 ${segment} 测试结果:`, {
        status: response.status,
        statusText: response.statusText,
        contentType: response.headers.get('content-type'),
        contentLength: response.headers.get('content-length'),
        url: segmentUrl
      });
      
    } catch (error) {
      console.error(`❌ 片段 ${segment} 测试失败:`, {
        error: error.message,
        url: segmentUrl,
        isCorsError: error.message.includes('CORS'),
        isNetworkError: error.message.includes('Failed to fetch')
      });
      
      if (error.message.includes('CORS')) {
        console.error('🌐 CORS错误：服务器没有设置正确的跨域头');
      } else if (error.message.includes('Failed to fetch')) {
        console.error('🌐 网络错误：可能是SSL证书或防火墙问题');
      }
    }
  }
  
  console.log('✅ 视频片段测试完成');
};

// 重新加载视频播放器
const reloadVideoPlayer = () => {
  console.log('🔄 重新加载视频播放器...');
  
  // 查找video元素
  const video = document.querySelector('video');
  if (video) {
    console.log('🎬 找到video元素，重新设置源');
    video.src = '';
    video.load();
    
    // 延迟重新设置源，让播放器完全重置
    setTimeout(() => {
      video.src = playerSourceUrl.value || '';
      console.log('✅ 视频源已重新设置:', playerSourceUrl.value);
      
      // 尝试播放
      video.play().catch(e => {
        console.log('⚠️ 自动播放被阻止:', e);
      });
    }, 1000);
  } else {
    console.error('❌ 找不到video元素');
  }
};

// 分析M3U8内容
const analyzeM3U8Content = async () => {
  console.log('🧪 开始分析M3U8内容...');
  
  if (!playerSourceUrl.value) {
    console.error('❌ 没有播放地址');
    return;
  }
  
  try {
    console.log('🔍 获取M3U8文件内容...');
    const response = await fetch(playerSourceUrl.value as string);
    const m3u8Content = await response.text();
    
    console.log('📄 M3U8文件内容:', m3u8Content);
    
    // 分析M3U8内容
    const lines = m3u8Content.split('\n').filter(line => line.trim());
    console.log('📋 M3U8内容分析:');
    
    let isMasterPlaylist = false;
    let isMediaPlaylist = false;
    let targetDuration = null;
    let mediaSequence = null;
    let segmentCount = 0;
    let segmentUrls = [];
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      
      if (line.startsWith('#EXTM3U')) {
        console.log('✅ 有效的M3U8文件');
      } else if (line.startsWith('#EXT-X-VERSION:')) {
        const version = line.split(':')[1];
        console.log(`📌 HLS版本: ${version}`);
      } else if (line.startsWith('#EXT-X-STREAM-INF:')) {
        isMasterPlaylist = true;
        console.log('📌 主播放列表 (Master Playlist)');
        console.log(`📌 流信息: ${line}`);
      } else if (line.startsWith('#EXT-X-TARGETDURATION:')) {
        targetDuration = line.split(':')[1];
        console.log(`📌 目标持续时间: ${targetDuration}秒`);
        isMediaPlaylist = true;
      } else if (line.startsWith('#EXT-X-MEDIA-SEQUENCE:')) {
        mediaSequence = line.split(':')[1];
        console.log(`📌 媒体序列号: ${mediaSequence}`);
      } else if (line.startsWith('#EXTINF:')) {
        const duration = line.split(':')[1].split(',')[0];
        console.log(`📌 片段持续时间: ${duration}秒`);
      } else if (line.endsWith('.ts') || line.endsWith('.m4s')) {
        segmentCount++;
        segmentUrls.push(line);
        if (segmentCount <= 3) {
          console.log(`📌 视频片段 ${segmentCount}: ${line}`);
        }
      }
    }
    
    console.log('📊 M3U8分析总结:');
    console.log(`   - 播放列表类型: ${isMasterPlaylist ? '主播放列表' : (isMediaPlaylist ? '媒体播放列表' : '未知')}`);
    console.log(`   - 目标持续时间: ${targetDuration || '未设置'}`);
    console.log(`   - 媒体序列号: ${mediaSequence || '未设置'}`);
    console.log(`   - 视频片段数量: ${segmentCount}`);
    console.log(`   - 前3个片段: ${segmentUrls.slice(0, 3).join(', ')}`);
    
    // 检查是否有问题
    if (isMasterPlaylist && !isMediaPlaylist) {
      console.warn('⚠️ 这是主播放列表，需要解析具体的媒体播放列表');
    }
    
    if (segmentCount === 0) {
      console.error('❌ 没有找到视频片段，这可能是问题所在');
    }
    
    // 测试第一个片段的URL
    if (segmentUrls.length > 0) {
      const firstSegment = segmentUrls[0];
      const baseUrl = (playerSourceUrl.value as string).replace(/\/[^\/]+\.m3u8$/, '');
      const fullSegmentUrl = firstSegment.startsWith('http') ? firstSegment : `${baseUrl}/${firstSegment}`;
      
      console.log('🔍 测试第一个片段URL:', fullSegmentUrl);
      
      try {
        const segmentResponse = await fetch(fullSegmentUrl, { method: 'HEAD' });
        console.log('✅ 第一个片段测试结果:', {
          status: segmentResponse.status,
          contentType: segmentResponse.headers.get('content-type'),
          contentLength: segmentResponse.headers.get('content-length')
        });
      } catch (error) {
        console.error('❌ 第一个片段测试失败:', error);
      }
    }
    
  } catch (error) {
    console.error('❌ M3U8内容分析失败:', error);
  }
};

// 强制使用HLS.js播放
const forceHlsJsPlayback = async () => {
  console.log('🚀 强制使用HLS.js播放...');
  
  if (!playerSourceUrl.value) {
    console.error('❌ 没有播放地址');
    return;
  }
  
  // 查找video元素
  const video = document.querySelector('video');
  if (!video) {
    console.error('❌ 找不到video元素');
    return;
  }
  
  try {
    // 清除当前源
    video.src = '';
    video.load();
    
    // 动态加载HLS.js
    if (!(window as any).Hls) {
      console.log('📦 加载HLS.js库...');
      const script = document.createElement('script');
      script.src = 'https://cdn.jsdelivr.net/npm/hls.js@latest';
      
      await new Promise((resolve, reject) => {
        script.onload = resolve;
        script.onerror = reject;
        document.head.appendChild(script);
      });
    }
    
    console.log('✅ HLS.js库已加载');
    
    if ((window as any).Hls && (window as any).Hls.isSupported()) {
      console.log('✅ HLS.js支持检测通过');
      
      // 创建HLS实例，使用更宽松的配置
      const hls = new (window as any).Hls({
        debug: true,
        enableWorker: true,
        lowLatencyMode: false, // 关闭低延迟模式
        backBufferLength: 30, // 减少后缓冲
        maxBufferLength: 10, // 减少最大缓冲
        maxMaxBufferLength: 30, // 减少最大最大缓冲
        liveSyncDurationCount: 1, // 减少同步计数
        liveMaxLatencyDurationCount: 2, // 减少最大延迟计数
        // 添加错误容忍配置
        fragLoadingTimeOut: 20000, // 增加片段加载超时
        manifestLoadingTimeOut: 10000, // 增加清单加载超时
        levelLoadingTimeOut: 10000, // 增加级别加载超时
        // 忽略异常片段
        ignoreDevicePixelRatio: true,
        // 添加CORS配置
        xhrSetup: function(xhr: XMLHttpRequest, url: string) {
          console.log('🌐 HLS.js XHR请求:', url);
          xhr.setRequestHeader('Access-Control-Allow-Origin', '*');
        }
      });
      
      // 附加媒体
      hls.attachMedia(video);
      
      // 事件监听
      hls.on((window as any).Hls.Events.MEDIA_ATTACHED, () => {
        console.log('✅ 媒体已附加，开始加载源:', playerSourceUrl.value);
        hls.loadSource(playerSourceUrl.value);
      });
      
      hls.on((window as any).Hls.Events.MANIFEST_PARSED, (event: any, data: any) => {
        console.log('✅ 播放列表解析成功:', data);
        console.log('📊 播放列表信息:', {
          levels: data.levels?.length || 0,
          audioTracks: data.audioTracks?.length || 0,
          subtitles: data.subtitles?.length || 0
        });
        
        // 尝试播放
        video.play().catch((e: any) => {
          console.log('⚠️ 自动播放被阻止:', e);
        });
      });
      
      hls.on((window as any).Hls.Events.FRAG_LOADED, (event: any, data: any) => {
        console.log('✅ 片段加载成功:', {
          frag: data.frag,
          url: data.frag.url,
          duration: data.frag.duration
        });
      });
      
      hls.on((window as any).Hls.Events.ERROR, (event: any, data: any) => {
        console.error('❌ HLS.js错误:', {
          type: data.type,
          details: data.details,
          fatal: data.fatal,
          url: data.url
        });
        
        if (data.fatal) {
          switch (data.type) {
            case (window as any).Hls.ErrorTypes.NETWORK_ERROR:
              console.log('🔄 网络错误，尝试恢复...');
              hls.startLoad();
              break;
            case (window as any).Hls.ErrorTypes.MEDIA_ERROR:
              console.log('🔄 媒体错误，尝试恢复...');
              hls.recoverMediaError();
              break;
            default:
              console.log('🔄 其他错误，尝试重新加载...');
              hls.destroy();
              // 重新创建HLS实例
              setTimeout(() => {
                forceHlsJsPlayback();
              }, 1000);
              break;
          }
        }
      });
      
      console.log('🎬 HLS.js播放器已启动');
      
    } else {
      console.error('❌ HLS.js不支持或未加载');
    }
    
  } catch (error) {
    console.error('❌ 强制HLS.js播放失败:', error);
  }
};

// 测试代理连接
const testProxyConnection = async () => {
  console.log('🧪 测试代理连接...');
  
  const proxyUrl = '/hls-proxy/streamkey_3d69fdd073e0b43e78c90fad758cc447.m3u8';
  console.log('🔗 代理URL:', proxyUrl);
  
  try {
    // 测试代理是否工作
    const response = await fetch(proxyUrl, {
      method: 'HEAD',
      mode: 'cors'
    });
    
    console.log('✅ 代理测试成功:', {
      status: response.status,
      statusText: response.statusText,
      contentType: response.headers.get('content-type'),
      contentLength: response.headers.get('content-length'),
      corsHeaders: {
        'access-control-allow-origin': response.headers.get('access-control-allow-origin'),
        'access-control-allow-methods': response.headers.get('access-control-allow-methods'),
        'access-control-allow-headers': response.headers.get('access-control-allow-headers')
      }
    });
    
    if (response.status === 200) {
      console.log('🎉 代理工作正常，可以尝试播放');
      // 自动尝试播放
      setTimeout(() => {
        forceHlsJsPlayback();
      }, 1000);
    }
    
  } catch (error) {
    console.error('❌ 代理测试失败:', error);
    console.log('💡 请确保开发服务器已重启以应用新的代理配置');
  }
};

const goBack = () => {
  uni.navigateBack();
};

// 返回直播列表
const goBackToList = () => {
  uni.navigateTo({ url: '/pages/room/new/RoomList' });
};

// 返回房间详情页
const goBackToRoom = () => {
  if (currentSession.value?.room_id) {
    uni.navigateTo({ url: `/pages/room/RoomDetail?id=${currentSession.value.room_id}` });
  } else {
    uni.showToast({
      title: '无法获取房间信息',
      icon: 'none'
    });
  }
};

// 跳转到主分会场展示页
const goToVenuePage = () => {
  const venueId = currentSession.value?.room_id;
  if (venueId) {
    uni.navigateTo({ url: `/pages/venue/VenueDisplayPage?venue_id=${venueId}` });
  } else {
    uni.showToast({ title: '无法获取主会场ID', icon: 'none' });
  }
};

// 跳转到分会场
const goToSubVenue = (roomId: string) => {
  uni.navigateTo({ url: `/pages/live/new/LiveView?room_id=${roomId}` });
};

// 跳转到专题展示页面
const goToTopicDisplay = async () => {
  if (currentTopicId.value) {
    uni.navigateTo({ url: `/pages/topic/TopicDisplay?topic_id=${currentTopicId.value}` });
    return;
  }
  try {
    const { value } = await ElMessageBox.prompt('请输入有效的专题ID (UUID)', '返回营销专题', {
      confirmButtonText: '前往',
      cancelButtonText: '取消',
      inputPattern: /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$/,
      inputErrorMessage: '专题ID格式无效，请粘贴完整 UUID'
    }) as unknown as { value: string };
    if (value) {
      uni.navigateTo({ url: `/pages/topic/TopicDisplay?topic_id=${value}` });
    }
  } catch {
    // 取消或关闭
  }
};

// 获取直播间关联的专题信息
const fetchRoomTopics = async (roomId: string) => {
  try {
    // 这里需要调用专题API，暂时使用模拟数据
    // 实际实现时应该调用: GET /api/v1/rooms/{room_id}/topics
    console.log('正在获取直播间关联的专题信息，room_id:', roomId);
    
  // 调用真实接口：获取房间关联的专题
  const resp = await topicApi.getRoomTopics(roomId);
  const list = resp?.data || [];
  console.log('房间关联专题列表:', list);
  const published = list.find((t: any) => (t.topic_status || t.status) === 'published' || t.is_published);
  const tid = published?.topic_id || published?.id;
  if (tid && isValidUuid(tid)) {
    currentTopicId.value = tid;
    console.log('找到已发布专题，topic_id:', tid);
  } else {
    currentTopicId.value = null;
    console.log('未找到已发布专题或ID无效，不展示返回专题入口');
  }
  } catch (error) {
    console.error('获取专题信息失败:', error);
    currentTopicId.value = null;
  }
};

// 轮播控制方法
const prevSlide = () => {
  if (currentIndex.value > 0) {
    currentIndex.value--;
  }
};

const nextSlide = () => {
  if (currentIndex.value < maxIndex.value) {
    currentIndex.value++;
  }
};

// 状态相关方法
const statusText = (status?: string) => {
  const map: Record<string, string> = {
    live: '直播中',
    scheduled: '未开始',
    ended: '已结束',
    archived: '回放中',
  };
  return map[status || 'scheduled'] || '未开始';
};

const statusType = (status?: string) => {
  const map: Record<string, string> = {
    live: 'success',
    scheduled: 'info',
    ended: 'warning',
    archived: 'primary',
  };
  return map[status || 'scheduled'] || 'info';
};

const sessionStatusText = (status: SessionStatus) => {
  const map: Record<SessionStatus, string> = {
    scheduled: '计划中',
    live: '直播中',
    ended: '已结束',
    archived: '已归档',
  };
  return map[status] || '未知状态';
};

</script>

<style lang="scss" scoped>
.live-view-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #f7f8fa; /* 改为浅灰色背景 */
  color: #333; /* 改为深色文字 */
  padding-top: 120px; /* 为顶部用户信息区域和固定标题留出空间 */
}

.fixed-header {
  position: fixed;
  top: 60px; /* 调整位置，避免与用户信息区域重叠 */
  left: 0;
  right: 0;
  height: 60px;
  background-color: #ffffff;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  align-items: center;
  z-index: 1000;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  padding: 0 20px;
}

.page-title {
  font-size: 18px;
  font-weight: bold;
  color: #333;
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  z-index: 1;
}

.header-left {
  display: flex;
  gap: 30px;
  align-items: center;
  position: relative;
  z-index: 2;
}

.header-right {
  display: flex;
  align-items: center;
  position: relative;
  z-index: 2;
}

.loading-container,
.status-container {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  flex-grow: 1;
  padding: var(--spacing-large);
  text-align: center;
}

.status-text {
  margin-bottom: var(--spacing-medium);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: var(--spacing-medium);
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.content-container {
  display: flex;
  flex-direction: row;
  flex-grow: 1;
  height: calc(100vh - 60px); /* 减去固定标题的高度 */
  background-color:#ffffff;
}

/* 左侧区域：视频 + 评论区 */
.left-section {
  flex: 2;
  display: flex;
  flex-direction: column;
  margin: 10px;
  border-radius: 8px;
}

/* 视频容器 */
.video-container {
  flex: 2; /* 增加视频区域的比例 */
  margin: 10px;
  border-radius: 8px;
  overflow: hidden;
  min-height: 500px; /* 设置最小高度 */
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15); /* 添加阴影 */
}

.placeholder-video {
  height: 225px;
  background-color: #ffffff; /* 白色背景 */
}

/* VideoPlayer 组件样式优化 */
.fallback-player {
  display: flex;
  justify-content: center;
  align-items: center;
  background: #000;
  border-radius: 8px;
  overflow: hidden;
}

.video-player-container {
  width: 100%;
  height: 500px;
  background: #000;
  border-radius: 8px;
  overflow: hidden;
}

/* 评论区 */
.comments-section {
  flex: 1; /* 保持评论区比例较小 */
  margin: 10px;
  border-radius: 8px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  min-height: 200px; /* 设置评论区最小高度 */
}

/* 手机端响应式布局 */
@media (max-width: 767px) {
  .content-container {
    flex-direction: column; /* 改为垂直布局 */
    height: auto; /* 高度自适应 */
    padding: 10px;
  }
  
  .left-section {
    flex: none; /* 移除flex属性 */
    margin: 0 0 20px 0; /* 调整边距 */
  }
  
  .video-container {
    flex: none; /* 移除flex属性 */
    margin: 0 0 20px 0; /* 调整边距 */
    min-height: 300px; /* 手机端视频高度适中 */
  }
  
  .comments-section {
    flex: none; /* 移除flex属性 */
    margin: 0 0 20px 0; /* 调整边距 */
    min-height: auto; /* 高度自适应 */
    padding: 16px; /* 减少内边距 */
  }
}
.room-description-card {
  background-color: #ffffff;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15); /* 更新阴影 */
  border: 1px solid #e0e0e0;
}

/* 手机端房间简介卡片样式 */
@media (max-width: 767px) {
  .room-description-card {
    padding: 12px; /* 减少内边距 */
    margin-bottom: 16px; /* 保持底部边距 */
  }
}

.description-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.description-icon {
  font-size: 16px;
  margin-right: 8px;
}

.description-label {
  font-size: 14px;
  font-weight: bold;
  color: #333;
}

.description-content {
  font-size: 14px;
  color: #444;
  line-height: 1.5;
}

.no-description {
  color: #aaa;
  font-style: italic;
}
.mock-comments {
  margin-top: 16px;
}

.comment-card {
  background-color: #ffffff;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 5px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
  border-left: 5px solid rgb(109, 184, 246);
  border: 1px solid #e0e0e0;
  border-left: 5px solid rgb(109, 184, 246);
}

.comment-user {
  font-size: 14px;
  font-weight: bold;
  color: rgb(24, 132, 221);
  margin-right: 4px;
}

.comment-content {
  font-size: 14px;
  color: #333;
  line-height: 1.4;
}

/* 右侧推荐区域 */
.recommendations-section {
  flex: 1;
  margin: 10px;
  border-radius: 8px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  height: 100%; /* 确保高度填满父容器 */
  min-height: 0; /* 允许flex子元素收缩 */
}

/* 手机端推荐区域样式 */
@media (max-width: 767px) {
  .recommendations-section {
    flex: none; /* 移除flex属性 */
    margin: 0 0 20px 0; /* 调整边距 */
    padding: 16px; /* 减少内边距 */
    height: auto; /* 高度自适应 */
  }
}

/* 区域标题 */
.section-title {
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 16px;
  color: #333;
}

.placeholder-text {
  color: #666;
  font-size: 14px;
}

/* 房间卡片容器 */
.room-cards-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
  flex: 1;
}

/* 手机端房间卡片横向滑动 */
@media (max-width: 767px) {
  .room-cards-container {
    flex-direction: row; /* 改为横向排列 */
    gap: 16px; /* 增加卡片间距 */
    overflow-x: auto; /* 允许横向滚动 */
    overflow-y: hidden; /* 禁止纵向滚动 */
    padding-bottom: 8px; /* 为滚动条留出空间 */
    -webkit-overflow-scrolling: touch; /* iOS平滑滚动 */
    scrollbar-width: none; /* Firefox隐藏滚动条 */
    -ms-overflow-style: none; /* IE隐藏滚动条 */
  }
  
  .room-cards-container::-webkit-scrollbar {
    display: none; /* Chrome隐藏滚动条 */
  }
}

/* 房间卡片样式 */
.room-card {
  background-color: #ffffff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border: 1px solid #e0e0e0;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-bottom: 12px;
}

.room-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* 手机端房间卡片样式 */
@media (max-width: 767px) {
  .room-card {
    flex-shrink: 0; /* 防止卡片被压缩 */
    width: 280px; /* 固定宽度 */
    margin-bottom: 0; /* 移除底部边距 */
    margin-right: 0; /* 移除右边距 */
  }
  
  .room-card:last-child {
    margin-right: 16px; /* 最后一个卡片右边距 */
  }
}

.room-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.room-title {
  font-size: 16px;
  font-weight: bold;
  color: #333;
  flex: 1;
  margin-right: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 手机端房间标题样式 */
@media (max-width: 767px) {
  .room-title {
    font-size: 14px; /* 手机端字体稍小 */
    line-height: 1.3; /* 调整行高 */
  }
}

.room-status {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
  white-space: nowrap;
}

.status-live {
  background-color: #ff4444;
  color: white;
}

.status-scheduled {
  background-color: #2196f3;
  color: white;
}

.status-ended {
  background-color: #666;
  color: white;
}

.status-archived {
  background-color: #9c27b0;
  color: white;
}

.status-default {
  background-color: #ccc;
  color: #333;
}

.room-card-content {
  margin-bottom: 8px;
}

.room-description {
  font-size: 14px;
  color: #666;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* 手机端房间描述样式 */
@media (max-width: 767px) {
  .room-description {
    font-size: 12px; /* 手机端字体更小 */
    line-height: 1.3; /* 调整行高 */
    -webkit-line-clamp: 1; /* 手机端只显示一行 */
  }
}

.room-card-footer {
  display: flex;
  justify-content: flex-end;
}

.room-time {
  font-size: 12px;
  color: #999;
}

.no-recommendations {
  display: flex;
  justify-content: center;
  align-items: center;
  flex: 1;
}

/* 评论区美化 */
.chat-sidebar {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: #ffffff;
}

.chat-header {
  padding: 14px 16px;
  text-align: center;
  font-weight: 600;
  color: #1e80ff;
  background: linear-gradient(180deg, #ffffff 0%, #f9fbff 100%);
  border-bottom: 1px solid #e6efff;
  position: relative;
}
.chat-header::after {
  content: '';
  position: absolute;
  left: 50%;
  bottom: 0;
  transform: translateX(-50%);
  width: 80px;
  height: 2px;
  background: #1e80ff;
  border-radius: 2px;
}

.admin-messages {
  padding: 12px 16px;
  background: #f6f9ff;
  border-bottom: 1px solid #eef1f6;
}
.admin-avatar {
  margin-right: 8px;
}
.admin-name {
  font-weight: 600;
  color: #303133;
  margin-left: 4px;
}
.message-content {
  margin: 8px 0;
  line-height: 1.5;
  color: #606266;
}
.message-time {
  color: #909399;
  font-size: 12px;
}

.user-messages {
  flex: 1;
  padding: 12px 12px 0 12px;
  overflow-y: auto;
  max-height: 420px;
}

.message-item {
  display: flex;
  background: #ffffff;
  border: 1px solid #eef1f6;
  border-radius: 10px;
  padding: 10px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.message-item + .message-item {
  margin-top: 10px;
}
.user-avatar {
  margin-right: 8px;
}
.user-name {
  font-weight: 500;
  color: #1f2d3d;
  margin-bottom: 4px;
}
.message-text {
  color: #606266;
}

.chat-input-area {
  padding: 12px 12px 14px 12px;
  border-top: 1px solid #eef1f6;
  background: #ffffff;
}
.input-with-icons {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.input-icons .el-button.is-link {
  color: #909399;
}
.chat-input-area :deep(.el-input__wrapper) {
  border-radius: 10px;
}
.chat-input-area .el-button[type="primary"] {
  border-radius: 8px;
}

/* 分会场轮播样式 */
.sub-venue-carousel {
  position: relative;
  display: flex;
  align-items: center;
  gap: 8px;
}

.carousel-container {
  flex: 1;
  overflow: hidden;
  border-radius: 8px;
}

.carousel-track {
  display: flex;
  transition: transform 0.3s ease;
  gap: 8px;
}

.venue-card {
  flex-shrink: 0;
  width: 200px;
  background: #ffffff;
  border-radius: 6px;
  padding: 8px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
  border: 1px solid #e0e0e0;
  cursor: pointer;
  transition: all 0.3s ease;
}

.venue-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.12);
}

.venue-card-inner {
  display: flex;
  flex-direction: column;
  gap: 6px;
  position: relative;
}

.venue-cover {
  width: 100%;
  height: 80px;
  border-radius: 4px;
  overflow: hidden;
  background: #fafafa;
}

.img-error {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #bbb;
  font-size: 10px;
}

.venue-info {
  flex: 1;
}

.venue-title {
  font-size: 12px;
  font-weight: 600;
  color: #303133;
  line-height: 1.3;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 3px;
}

.venue-meta {
  color: #909399;
  font-size: 10px;
}

.status-badge {
  position: absolute;
  top: 6px;
  right: 6px;
  font-size: 10px;
  padding: 2px 4px;
}

.control-btn {
  width: 28px;
  height: 28px;
  flex-shrink: 0;
  background: #ffffff;
  border: 1px solid #e0e0e0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.control-btn:hover:not(:disabled) {
  background: #f5f7fa;
  border-color: #409eff;
}

.control-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .sub-venue-carousel {
    gap: 4px;
  }
  
  .venue-card {
    width: 160px;
    padding: 6px;
  }
  
  .venue-cover {
    height: 60px;
  }
  
  .venue-title {
    font-size: 11px;
  }
  
  .venue-meta {
    font-size: 9px;
  }
  
  .control-btn {
    width: 24px;
    height: 24px;
  }
  
  .status-badge {
    font-size: 9px;
    padding: 1px 3px;
  }
}
</style>



