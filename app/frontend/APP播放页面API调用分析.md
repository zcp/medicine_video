# 🎬 LiveView 播放页面 API 调用分析

## 📋 文档概要
本文档详细分析 [LiveView.vue](src/pages/app/live/LiveView.vue) 页面的 API 调用情况，包括调用的 API、获取数据、数据使用流程。

**分析时间**：2025年12月30日  
**应用模式**：混合API模式（真实API + Mock数据）

---

## 1️⃣ API 调用概览

### 1.1 混合API模式配置

页面采用**混合API策略**，区分核心播放功能和互动功能：

```typescript
const LIVEVIEW_API_MODE = {
  // ✅ 播放核心功能：使用真实API
  useRealAPI: {
    room: true,           // 房间信息
    session: true,        // 场次信息
    playback: true,       // 播放地址
  },
  // 🔄 互动功能：暂时使用Mock
  useMockData: {
    chat: true,           // 聊天消息
    qa: true,             // 问答
    recommend: true,      // 推荐列表
    materials: true,      // 资料下载
    viewerCount: true,    // 观看人数（后端统计未完善）
  }
};
```

### 1.2 API 调用工具库

所有 API 调用均使用统一的请求工具：
- 路径：[src/utils/request.ts](src/utils/request.ts)
- 返回格式：`ApiResponse<T>` = `{ code, message, data }`

---

## 2️⃣ 真实API调用详情

### 2.1 核心API 1️⃣：房间信息 API

**模块**：[src/api/room.ts](src/api/room.ts)

#### 调用函数
```typescript
import { getRoomDetail } from '@/api/room';

// 函数签名
const getRoomDetail = (roomId: string): Promise<ApiResponse<Room>> => {
  return get<ApiResponse<Room>>(`/rooms/${roomId}`);
};
```

#### 使用场景
- **何时调用**：当通过 `roomId` 进入直播间时，需要先获取房间详情找到当前场次 ID
- **调用代码位置**：[LiveView.vue #503](src/pages/app/live/LiveView.vue#L503)

#### 获取的数据结构
```typescript
interface Room {
  id: string;                    // 房间ID
  title: string;                 // 房间标题
  description?: string;          // 房间描述
  cover_url?: string;            // 房间封面
  is_private: boolean;           // 是否私有
  record_by_default: boolean;    // 是否默认录制
  stream_key: string;            // 流密钥
  created_at: string;            // 创建时间
  updated_at: string;            // 更新时间
  live_status?: SessionStatus;   // 直播状态
  current_session_id?: string;   // ⭐ 当前场次ID
  parent_room_id?: string;       // 父房间ID
  user_id: string | null;        // 用户ID
  category_id: string | null;    // 分类ID
  category_name?: string;        // 分类名称
  user_name?: string;            // 用户名
}
```

#### 数据使用方式
```typescript
async function loadSessionData() {
  if (!sessionId.value && roomId.value) {
    // 获取房间详情
    const roomResponse = await getRoomDetail(roomId.value);
    const room = (roomResponse as any).data?.data || (roomResponse as any).data || roomResponse;
    
    // ⭐ 关键：从房间获取当前场次ID
    if (room.current_session_id) {
      sessionId.value = room.current_session_id;
    }
  }
}
```

#### 数据最终用途
- 提取 `current_session_id` 用于后续获取场次详情
- 若无 `current_session_id`，则降级调用 `getSessionList()` 获取场次列表

---

### 2.2 核心API 2️⃣：场次列表 API

**模块**：[src/api/session.ts](src/api/session.ts)

#### 调用函数
```typescript
import { getSessionList } from '@/api/session';

// 函数签名
const getSessionList = (roomId: string, params: { page?: number, size?: number }) => {
  return request<PaginatedSessions>({
    url: `/rooms/${roomId}/sessions`,
    method: 'GET',
    data: params,
  });
};
```

#### 使用场景
- **何时调用**：当房间没有 `current_session_id` 时，获取最新的场次列表
- **调用代码位置**：[LiveView.vue #511](src/pages/app/live/LiveView.vue#L511)

#### 获取的数据结构
```typescript
// 返回分页结构
interface PaginatedResponse<Session> {
  items: Session[];    // 场次数组
  total: number;       // 总数
  page: number;        // 当前页
  size: number;        // 每页大小
  totalPages: number;  // 总页数
}

// 单个Session
interface Session {
  id: string;                      // 场次ID ⭐
  room_id: string;                 // 房间ID
  status: 'scheduled' | 'live' | 'ended' | 'archived';  // 状态
  start_time: string;              // 开始时间
  end_time: string | null;         // 结束时间
  video_id: string | null;         // 视频ID
  playback_url?: string | null;    // ⭐ 回放地址
  summary: string | null;          // 场次总结
  featured_expert_id: string | null;  // 特邀专家ID
  created_at: string;              // 创建时间
  updated_at: string;              // 更新时间
}
```

#### 数据使用方式
```typescript
const sessionsResponse = await getSessionList(roomId.value, { page: 1, size: 1 });
const sessions = (sessionsResponse as any).data?.items || (sessionsResponse as any).items || [];

if (sessions.length > 0) {
  sessionId.value = sessions[0].id;  // 取第一条场次
}
```

---

### 2.3 核心API 3️⃣：场次详情 API

**模块**：[src/api/session.ts](src/api/session.ts)

#### 调用函数
```typescript
import { getSessionDetail } from '@/api/session';

// 函数签名
const getSessionDetail = (sessionId: string) => {
  return request<Session>({
    url: `/sessions/${sessionId}`,
    method: 'GET',
  });
};
```

#### 使用场景
- **何时调用**：获取到 `sessionId` 后，立即调用获取完整场次详情
- **调用频率**：页面加载时调用一次；页面显示时（onShow）再调用一次刷新
- **调用代码位置**：[LiveView.vue #520](src/pages/app/live/LiveView.vue#L520)

#### 获取的数据结构
```typescript
interface Session {
  // 基础标识
  id: string;                      // 场次ID
  room_id: string;                 // 房间ID
  
  // 场次状态和时间
  status: SessionStatus;           // 直播状态
  start_time: string;              // 直播开始时间
  end_time: string | null;         // 直播结束时间
  
  // ⭐ 播放地址（最核心数据）
  playback_url?: string | null;    // 回放地址 (m3u8格式)
  live_url?: string | null;        // 直播地址 (如果直播中)
  video_id: string | null;         // 视频ID
  
  // 场次信息
  summary: string | null;          // 场次总结
  title?: string;                  // 场次标题
  cover_url?: string;              // 场次封面
  
  // 专家信息
  expert?: {
    id: string;
    name: string;
    title: string;
    avatar: string;
    hospital: string;
    department: string;
  };
  featured_expert_id: string | null;
  
  // 统计数据
  statistics?: {
    peak_viewer_count: number;     // 峰值观看人数
    total_viewer_count: number;    // 总观看人数
    total_like_count: number;      // 总点赞数
    total_share_count: number;     // 总分享数
  };
  
  // 时间戳
  created_at: string;
  updated_at: string;
}
```

#### 数据使用方式
```typescript
// 1. 获取场次详情
const sessionResponse = await getSessionDetail(sessionId.value);
sessionInfo.value = (sessionResponse as any).data?.data || (sessionResponse as any).data || sessionResponse;

// 2. 提取关键播放信息
console.log('播放标题:', sessionInfo.value?.title);
console.log('播放地址:', sessionInfo.value?.playback_url);
console.log('专家信息:', sessionInfo.value?.expert);

// 3. 设置播放源
setupPlayerSource();
```

#### 数据最终用途

**UI 展示数据**：
- `title` → 直播标题（页面顶部）
- `status` → 状态徽章（直播中/回放/预告）
- `start_time` → 直播时间
- `expert` → 专家头像、名字、职称
- `cover_url` → 视频封面

**播放器数据**：
```typescript
function setupPlayerSource() {
  const session = sessionInfo.value;
  
  if (session.status === 'live') {
    // 直播：优先使用live_url
    playerSourceUrl.value = session.live_url || session.playback_url || '';
  } else if (session.status === 'finished' || session.status === 'ended' || session.status === 'archived') {
    // 回放：使用playback_url
    playerSourceUrl.value = session.playback_url || '';
  }
}
```

**统计数据**：
- 用于显示观看人数统计
- 用于UI呈现（虽然当前Mock）

---

### 2.4 核心API 4️⃣：实时观看人数 API

**模块**：[src/api/playback.ts](src/api/playback.ts)

#### 调用函数
```typescript
import { getRealtimeViewers } from '@/api/playback';

// 函数签名
export const getRealtimeViewers = (sessionId: string): Promise<ApiResponse<RealtimeViewers>> => {
  return request<ApiResponse<RealtimeViewers>>({
    url: `/sessions/${sessionId}/viewers`,
    method: 'GET'
  });
};
```

#### 使用场景
- **何时调用**：页面加载时立即调用，然后每30秒定时刷新一次
- **调用代码位置**：[LiveView.vue #653](src/pages/app/live/LiveView.vue#L653)

#### 获取的数据结构
```typescript
interface RealtimeViewers {
  count: number;        // 当前观看人数
  timestamp: string;    // 时间戳
}
```

#### 数据使用方式
```typescript
// 启动定时器
function startViewerCountTimer() {
  loadViewerCount();  // 立即加载一次
  viewerCountTimer = setInterval(loadViewerCount, 30000);  // 每30秒更新一次
}

// 加载观看人数
async function loadViewerCount() {
  if (!sessionId.value) return;

  try {
    if (ENV_CONFIG.VITE_USE_MOCK) {
      viewerCount.value = mockViewerCount.count;
    } else {
      const res = await getRealtimeViewers(sessionId.value);
      viewerCount.value = res.data?.count || 0;
    }
  } catch (err) {
    console.error('获取观看人数失败:', err);
  }
}
```

#### 数据最终用途
```vue
<!-- 显示在直播标题下方 -->
<text class="viewer-count" v-if="viewerCount > 0">
  👁️ {{ formatViewerCount(viewerCount) }}人在看
</text>

<!-- 传递给播放器组件 -->
<VideoPlayerApp
  :show-viewer-count="true"
  :viewer-count="viewerCount"
/>
```

---

### 2.5 补充API：观看历史记录 API

**模块**：[src/api/watchHistory.ts](src/api/watchHistory.ts)

#### 调用函数
```typescript
import { recordWatch } from '@/api/watchHistory';

// 函数签名
export const recordWatch = (sessionId: string, data: WatchHistoryCreatePayload): Promise<ApiResponse<WatchHistory>> => {
  return post<ApiResponse<WatchHistory>>(`/sessions/${sessionId}/watch`, data, { auth: true });
};

// 数据结构
interface WatchHistoryCreatePayload {
  progress: number;     // 播放进度（秒）
  extra?: {
    ts_filename: string;      // TS文件名
    segment_index: number;    // 分片索引
    is_seek: boolean;         // 是否快进
    device: string;           // 设备型号
    platform: 'app' | 'h5';  // 平台
  };
}
```

#### 使用场景
- **何时调用**：播放器切换 TS 分片时触发（实时上报）
- **调用代码位置**：[LiveView.vue #704](src/pages/app/live/LiveView.vue#L704)
- **权限要求**：需要用户认证（auth: true）

#### 数据使用方式
```typescript
function handleSegmentChange(data: any) {
  // 上报观看历史
  if (isAuthenticated.value && sessionId.value) {
    recordWatch(sessionId.value, {
      progress: Math.floor(data.currentTime),
      extra: {
        ts_filename: data.tsFilename,
        segment_index: data.segmentIndex,
        is_seek: data.isSeek || false,
        device: uni.getSystemInfoSync().model,
        platform: 'app'
      }
    }).catch(err => {
      console.error('上报观看历史失败:', err);
    });
  }
}
```

#### 数据最终用途
- 后端存储用户观看记录
- 用于用户观看历史查询
- 用于推荐算法训练数据

---

## 3️⃣ Mock 数据调用

### 3.1 Mock 数据模块

**模块**：[src/pages/app/live/mock-data.ts](src/pages/app/live/mock-data.ts)

### 3.2 Mock 数据类型

#### 聊天消息
```typescript
export const mockChatMessages = [
  {
    id: string;           // 消息ID
    user: {
      id: string;
      name: string;       // 用户名
      avatar: string;     // 头像URL
    };
    content: string;      // 消息内容
    timestamp: string;    // 时间戳
  }
];
```

**数据使用**：
- 显示在"聊天"Tab中
- 列表滚动显示最新消息

#### 问答
```typescript
export const mockQuestions = [
  {
    id: string;
    user: { id: string; name: string };
    content: string;           // 问题内容
    timestamp: string;
    answer?: {                 // 可选的答案
      expert: { id: string; name: string };
      content: string;         // 回答内容
      timestamp: string;
    };
  }
];
```

**数据使用**：
- 显示在"问答"Tab中
- 支持提问和回答展示

#### 推荐列表
```typescript
export const mockRelatedSessions = [
  {
    id: string;
    title: string;              // 推荐场次标题
    expert: { name: string };
    start_time: string;
    cover_url: string;          // 封面
    playback_url: string;       // 播放地址
  }
];
```

**数据使用**：
- 显示在"推荐"Tab中
- 点击可跳转到其他直播间

#### 资料
```typescript
export const mockMaterials = [
  {
    id: string;
    name: string;               // 资料名称
    url: string;                // 下载链接
    size: number;               // 文件大小
    uploaded_at: string;
  }
];
```

**数据使用**：
- 显示资料下载列表
- 提供文件下载功能

---

## 4️⃣ 数据流向图

```
┌─────────────────────────────────────────────────────────┐
│         页面加载入口 (onLoad)                            │
│   roomId or sessionId → onMounted → loadSessionData()   │
└──────────────────┬──────────────────────────────────────┘
                   │
        ┌──────────▼──────────┐
        │  判断ID来源          │
        └──────────┬──────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
   有sessionId          只有roomId
        │                     │
        │          ┌──────────▼─────────────┐
        │          │ getRoomDetail()        │
        │          │ 获取 current_session_id│
        │          └──────────┬─────────────┘
        │                     │
        │          ┌──────────▼────────────────┐
        │          │ sessionId还是为空?        │
        │          └──────┬───────────────┬────┘
        │                 │ YES           │ NO
        │                 │               │
        │          ┌──────▼────────────────┐
        │          │ getSessionList()      │
        │          │ 获取第一条场次ID       │
        │          └──────┬────────────────┘
        │                 │
        ▼                 ▼
   ┌────────────────────────────┐
   │  getSessionDetail(id)      │
   │  ⭐ 获取完整场次数据         │
   └────────────┬───────────────┘
                │
        ┌───────▼──────────┬───────────────┬────────────┐
        │                  │               │            │
        ▼                  ▼               ▼            ▼
   ┌─────────┐      ┌──────────┐    ┌────────────┐ ┌───────────┐
   │UI 展示   │      │播放器数据 │    │Mock 数据    │ │统计定时器  │
   │         │      │         │    │         │ │         │
   │标题     │      │source   │    │聊天     │ │获取    │
   │专家     │      │url      │    │问答     │ │观看    │
   │封面     │      │poster   │    │推荐     │ │人数    │
   │时间     │      │         │    │资料     │ │        │
   │观看数   │      │         │    │         │ │(30s)   │
   └─────────┘      └──────────┘    └────────────┘ │        │
                            │                      └───────────┘
                            │
                    ┌───────▼────────────┐
                    │  setupPlayerSource │
                    │  确定播放地址       │
                    │  live_url 或       │
                    │  playback_url      │
                    └───────┬────────────┘
                            │
                    ┌───────▼────────────────────┐
                    │  VideoPlayerApp 组件       │
                    │  ⭐ 播放视频               │
                    │  监听段分片变化             │
                    │  → recordWatch()记录历史   │
                    └────────────────────────────┘
```

---

## 5️⃣ 完整 API 调用时序表

| 序号 | API 名称 | 调用时机 | 权限 | 数据用途 | 状态 |
|------|---------|---------|------|---------|------|
| 1 | `getRoomDetail()` | 页面加载时 | 无 | 获取 sessionId | ✅ 真实API |
| 2 | `getSessionList()` | 房间无当前场次时 | 无 | 获取场次列表 | ✅ 真实API |
| 3 | `getSessionDetail()` | 获取到sessionId后 | 无 | 获取完整场次数据 | ✅ 真实API |
| 4 | `getRealtimeViewers()` | 加载后 + 每30秒 | 无 | 获取观看人数 | ✅ 真实API (Mock中) |
| 5 | `recordWatch()` | 播放时段分片变化 | 需认证 | 记录观看历史 | ✅ 真实API |
| - | Mock 聊天 | 页面加载时 | 无 | 聊天内容显示 | 🔄 Mock |
| - | Mock 问答 | 页面加载时 | 无 | 问答内容显示 | 🔄 Mock |
| - | Mock 推荐 | 页面加载时 | 无 | 推荐列表显示 | 🔄 Mock |
| - | Mock 资料 | 页面加载时 | 无 | 资料列表显示 | 🔄 Mock |

---

## 6️⃣ 数据字段映射表

### 页面显示 ← 数据来源

| 页面元素 | 数据字段 | 来源API | 类型 |
|---------|---------|--------|------|
| **标题区** | | | |
| 直播标题 | `sessionInfo.title` | getSessionDetail | String |
| 状态徽章 | `sessionInfo.status` | getSessionDetail | Enum |
| 开始时间 | `sessionInfo.start_time` | getSessionDetail | ISO8601 |
| 观看人数 | `viewerCount` | getRealtimeViewers | Number |
| **专家区** | | | |
| 专家头像 | `sessionInfo.expert.avatar` | getSessionDetail | URL |
| 专家名字 | `sessionInfo.expert.name` | getSessionDetail | String |
| 专家职称 | `sessionInfo.expert.title` | getSessionDetail | String |
| 医院科室 | `sessionInfo.expert.hospital` + `.department` | getSessionDetail | String |
| **操作按钮** | | | |
| 关注状态 | `isFollowed` | 本地状态 | Boolean |
| 收藏状态 | `isFavorited` | 本地状态 | Boolean |
| **播放器** | | | |
| 播放源 | `playerSourceUrl` | getSessionDetail | URL (m3u8) |
| 封面 | `sessionInfo.cover_url` | getSessionDetail | URL |
| **交互内容** | | | |
| 聊天消息 | `chatMessages` | mockChatMessages | Array |
| 问答列表 | `questions` | mockQuestions | Array |
| 推荐列表 | `relatedSessions` | mockRelatedSessions | Array |
| 资料列表 | `materials` | mockMaterials | Array |

---

## 7️⃣ 关键业务逻辑

### 7.1 播放地址选择策略

```typescript
function setupPlayerSource() {
  const session = sessionInfo.value;
  
  // 🎬 策略：根据直播状态选择播放源
  if (session.status === 'live') {
    // 直播中：优先使用live_url（直播流），失败降级到playback_url
    playerSourceUrl.value = session.live_url || session.playback_url || '';
    console.log('🔴 直播模式');
  } else if (['finished', 'ended', 'archived'].includes(session.status)) {
    // 已结束/存档：使用playback_url（录制文件）
    playerSourceUrl.value = session.playback_url || '';
    console.log('📺 回放模式');
  } else {
    // 预告/其他状态：暂无播放地址
    playerSourceUrl.value = '';
    console.log('⏰ 预告状态，暂无播放地址');
  }
}
```

**逻辑说明**：
- **直播中**：优先使用实时流，如果失败则回退到回放地址
- **已结束**：直接使用回放地址（m3u8格式）
- **预告**：不提供播放地址

---

### 7.2 导航栏标题更新策略

```typescript
function updateNavigationTitle() {
  const statusMap = {
    'live': '直播间',
    'finished': '回放',
    'ended': '回放',
    'archived': '回放',
    'scheduled': '预告'
  };
  
  const title = statusMap[sessionInfo.value?.status] || '直播间';
  uni.setNavigationBarTitle({ title });
}
```

---

### 7.3 网络状态监听

```typescript
function initNetworkListener() {
  uni.onNetworkStatusChange((res) => {
    networkType.value = res.networkType;
    
    // 流量提醒逻辑
    if (res.networkType !== 'wifi' && res.isConnected) {
      const noPrompt = uni.getStorageSync('settings_traffic_reminder');
      if (noPrompt !== false) {
        showTrafficWarning.value = true;  // 显示流量警告
      }
    }
  });
}
```

---

### 7.4 观看历史上报机制

```typescript
function handleSegmentChange(data: any) {
  // ⭐ 每次分片变化都上报一次
  if (isAuthenticated.value && sessionId.value) {
    recordWatch(sessionId.value, {
      progress: Math.floor(data.currentTime),      // 当前播放时间
      extra: {
        ts_filename: data.tsFilename,              // TS文件名
        segment_index: data.segmentIndex,          // 分片索引
        is_seek: data.isSeek || false,             // 是否用户主动快进
        device: uni.getSystemInfoSync().model,     // 设备型号
        platform: 'app'                            // 平台标识
      }
    }).catch(err => {
      console.error('上报观看历史失败:', err);
      // 失败时不中断播放
    });
  }
}
```

**特点**：
- 实时上报（每段分片变化时）
- 包含详细的观看上下文信息
- 失败不影响播放

---

## 8️⃣ 数据缓存和刷新机制

### 8.1 页面生命周期中的数据刷新

```typescript
onMounted(async () => {
  // 页面挂载时加载一次
  await loadSessionData();
  initNetworkListener();
  startViewerCountTimer();  // 启动30秒定时器
});

onShow(async () => {
  // 页面每次显示时重新刷新数据
  // 场景：从其他页面返回时
  await loadSessionData();
});

onBeforeUnmount(() => {
  // 页面卸载前清理定时器
  clearViewerCountTimer();
});
```

### 8.2 定时更新策略

| 数据 | 刷新频率 | 触发方式 | 用途 |
|------|---------|--------|------|
| 观看人数 | 每30秒 | setInterval | 实时显示观众数 |
| 场次信息 | 一次 | 页面加载时 | 标题、专家等静态数据 |
| 观看历史 | 实时 | 分片变化时 | 记录播放进度 |

---

## 9️⃣ 错误处理机制

### 9.1 API 调用错误处理

```typescript
async function loadSessionData() {
  try {
    isLoading.value = true;
    
    // API 调用
    if (!sessionId.value && roomId.value) {
      const roomResponse = await getRoomDetail(roomId.value);
      // ...
    }
    
    isLoading.value = false;
  } catch (err) {
    // ❌ 错误处理
    console.error('[LiveView] 加载数据失败:', err);
    error.value = '加载失败，请重试';
    isLoading.value = false;
  }
}
```

### 9.2 播放器错误处理

```typescript
function handlePlaybackError(errorMsg: string) {
  // ❌ 播放错误显示提示
  uni.showToast({
    title: '播放失败：' + errorMsg,
    icon: 'none',
    duration: 3000
  });
}
```

---

## 🔟 总结

### 核心 API 5 个

| API | 功能 | 状态 |
|-----|------|------|
| `getRoomDetail()` | 获取房间信息及当前场次ID | ✅ |
| `getSessionList()` | 获取房间场次列表 | ✅ |
| `getSessionDetail()` | **获取完整场次数据（最核心）** | ✅ |
| `getRealtimeViewers()` | 获取实时观看人数 | ✅ (Mock中) |
| `recordWatch()` | 上报观看历史 | ✅ |

### 关键数据流

```
roomId/sessionId → 获取场次ID → 获取场次详情 → 提取播放地址 → 启动播放 → 实时上报历史
```

### 混合策略优势

- ✅ **播放体验**：使用真实API，保证功能可用
- 🔄 **开发效率**：互动功能用Mock，不阻塞开发
- 📊 **易于测试**：Mock数据稳定可控

---

## 📚 相关文件清单

| 文件 | 说明 |
|-----|------|
| [src/pages/app/live/LiveView.vue](src/pages/app/live/LiveView.vue) | 播放页面主组件 |
| [src/api/session.ts](src/api/session.ts) | 场次相关API |
| [src/api/room.ts](src/api/room.ts) | 房间相关API |
| [src/api/playback.ts](src/api/playback.ts) | 播放相关API |
| [src/api/watchHistory.ts](src/api/watchHistory.ts) | 观看历史API |
| [src/pages/app/live/mock-data.ts](src/pages/app/live/mock-data.ts) | Mock数据定义 |
| [src/types/session.ts](src/types/session.ts) | 场次数据类型 |
| [src/types/room.ts](src/types/room.ts) | 房间数据类型 |
| [src/types/playback.ts](src/types/playback.ts) | 播放数据类型 |

---

**文档生成日期**：2025-12-30
