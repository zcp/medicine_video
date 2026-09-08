# 🎥 真实API播放功能接入方案

## 🎯 方案概述

**目标**：在后端 API 未完全实现的情况下，优先让播放功能使用真实 API，其他功能暂时使用 Mock 数据。

**核心策略**：混合 API 模式（Hybrid API Mode）
- ✅ **播放核心功能**：使用真实 API（房间、场次、播放地址）
- 🔄 **互动功能**：暂时使用 Mock 数据（聊天、问答、推荐）
- 📊 **统计功能**：暂时使用 Mock 数据（观看人数、点赞数）

---

## 📋 当前可用的真实 API 资源

根据测试结果，后端已提供以下数据：

### ✅ 已验证可用的 API

| API 接口 | 返回数据 | 可用字段 | 状态 |
|---------|---------|---------|------|
| `GET /rooms` | 房间列表 | `id`, `title`, `cover_url`, `description`, `stream_key` | ✅ 完整可用 |
| `GET /rooms/{id}` | 房间详情 | `id`, `title`, `cover_url`, `description`, `current_session_id` | ✅ 完整可用 |
| `GET /rooms/{id}/sessions` | 场次列表 | `id`, `status`, `start_time`, `end_time` | ✅ 完整可用 |
| `GET /sessions/{id}` | 场次详情 | `id`, `status`, `playback_url`, `statistics` | ✅ 完整可用 |

### 📊 可用的数据字段详情

**房间（Room）字段**：
```typescript
{
  id: string;              // 房间ID ✅
  title: string;           // 房间标题 ✅ 可用于显示
  cover_url: string;       // 封面图片 ✅ 可用于海报/缩略图
  description: string;     // 房间描述 ✅ 可用于详情介绍
  stream_key: string;      // 推流密钥
  current_session_id: string | null; // 当前场次ID
  created_at: string;      // 创建时间
}
```

**场次（Session）字段**：
```typescript
{
  id: string;              // 场次ID ✅
  room_id: string;         // 所属房间ID ✅
  status: string;          // 状态（scheduled/live/finished） ✅
  start_time: string;      // 开始时间 ✅
  end_time: string | null; // 结束时间
  playback_url: string | null; // 播放地址 ✅ 核心字段
  statistics: {            // 统计数据 ✅
    peak_viewer_count: number;
    total_viewer_count: number;
    total_like_count: number;
    // ...
  }
}
```

---

## 📋 问题诊断总结

### 你遇到的问题分析

1. **✅ 关注/收藏显示提示** - 正常（本地状态切换，未连接后端）
2. **❌ 分享功能无反应** - 已修复（改用 `uni.share` API）
3. **✅ 资料下载显示"开发中"** - 正常（功能未实现）
4. **✅ 获取 sessionId 成功** - 可以获取到真实播放地址

---

---

## 🚀 混合 API 模式实现方案

### 核心策略：多页面混合API模式

**全局原则**：
- 📊 **房间基础数据**：使用真实API（标题、封面、描述）→ 首页卡片、播放页面都使用
- 🎬 **播放核心数据**：使用真实API（场次、播放地址）→ 仅播放页面使用
- 🏷️ **分类筛选数据**：使用Mock数据（后端未实现）→ 首页筛选功能
- 💬 **互动数据**：使用Mock数据（聊天、问答、推荐）→ 播放页面互动功能

---

### 方案一：LiveView 页面级别控制（推荐 ⭐）

**原理**：在 LiveView 页面中单独控制是否使用真实 API，不影响其他页面。

**优点**：
- ✅ 不需要修改全局配置
- ✅ 其他页面继续使用 Mock 数据
- ✅ 可以随时切换测试
- ✅ 不影响团队其他成员开发
- ✅ 首页和播放页都能使用真实封面

**实现步骤**：

#### 0. 首页混合模式配置（新增）⭐

**首页需要的真实数据**：房间列表的标题和封面  
**首页继续Mock的数据**：分类筛选

在 `src/pages/app/tabbar/home/index.vue` 中添加混合模式：

```vue
<script setup lang="ts">
import { getRoomList } from '@/api/room';
import { mockCategories } from './mock-data'; // 分类数据继续用Mock

// 🎯 首页混合API模式配置
const HOME_API_MODE = {
  useRealAPI: {
    roomList: true,        // ✅ 房间列表（标题、封面）
  },
  useMockData: {
    categories: true,      // 🔄 分类筛选（后端未实现）
    banners: true,         // 🔄 轮播图（可选）
  }
};

// 房间列表数据
const rooms = ref<Room[]>([]);
const categories = ref<Category[]>([]);

// 加载房间列表
async function loadRooms() {
  try {
    if (HOME_API_MODE.useRealAPI.roomList) {
      // ✅ 使用真实API获取房间列表
      const response = await getRoomList({ page: 1, size: 20 });
      const roomData = (response as any).data?.items || (response as any).items || [];
      
      // 🆕 直接使用真实的房间数据（包含真实封面）
      rooms.value = roomData.map((room: any) => ({
        id: room.id,
        title: room.title,                    // ✅ 真实标题
        cover_url: room.cover_url,            // ✅ 真实封面（重点！）
        description: room.description,        // ✅ 真实描述
        current_session_id: room.current_session_id,
        live_status: room.live_status || 'offline',
        // 其他字段可以补充默认值
        viewer_count: 0,
        like_count: 0,
      }));

      console.log('[Home] ✅ 使用真实房间数据，封面地址:', rooms.value[0]?.cover_url);
    } else {
      // 使用Mock数据
      rooms.value = mockRooms;
    }
  } catch (error) {
    console.error('[Home] 获取房间列表失败:', error);
    // 降级使用Mock
    rooms.value = mockRooms;
  }
}

// 加载分类数据
async function loadCategories() {
  // 🔄 分类数据继续使用Mock（后端未实现）
  if (HOME_API_MODE.useMockData.categories) {
    categories.value = mockCategories;
    console.log('[Home] 🔄 使用Mock分类数据');
  }
}

onMounted(() => {
  loadRooms();
  loadCategories();
});
</script>

<template>
  <view class="home-page">
    <!-- 分类筛选：使用Mock数据 -->
    <scroll-view scroll-x class="category-tabs">
      <view
        v-for="cat in categories"
        :key="cat.id"
        class="category-item"
        :class="{ active: selectedCategory === cat.id }"
        @tap="selectCategory(cat.id)"
      >
        <text>{{ cat.name }}</text>
      </view>
    </scroll-view>

    <!-- 房间列表：使用真实数据（包括真实封面） -->
    <scroll-view scroll-y class="room-list">
      <view
        v-for="room in rooms"
        :key="room.id"
        class="room-card"
        @tap="handleRoomClick(room)"
      >
        <!-- ✅ 使用真实封面图片 -->
        <image
          class="room-cover"
          :src="room.cover_url || '/static/default-cover.png'"
          mode="aspectFill"
        />
        
        <view class="room-info">
          <!-- ✅ 使用真实标题 -->
          <text class="room-title">{{ room.title }}</text>
          
          <!-- 状态标签 -->
          <view class="room-status">
            <text class="status-badge" :class="room.live_status">
              {{ getStatusText(room.live_status) }}
            </text>
          </view>
        </view>
      </view>
    </scroll-view>
  </view>
</template>
```

---

#### 1. 修改 LiveView.vue 的数据加载逻辑

在 `src/pages/app/live/LiveView.vue` 中添加混合模式开关：

```vue
<script setup lang="ts">
// ... 其他导入

// 🎯 LiveView 混合API模式配置
const LIVEVIEW_API_MODE = {
  // 播放核心功能：使用真实API
  useRealAPI: {
    room: true,           // 房间信息（标题、封面）
    session: true,        // 场次信息（播放地址）
    playback: true,       // 播放地址
  },
  // 互动功能：暂时使用Mock
  useMockData: {
    chat: true,           // 聊天消息
    qa: true,             // 问答
    recommend: true,      // 推荐列表
    materials: true,      // 资料下载
    viewerCount: true,    // 观看人数（后端统计未完善）
  }
};

async function loadSessionData() {
  try {
    isLoading.value = true;
    
    // ===== 🎯 播放核心数据：使用真实API =====
    if (LIVEVIEW_API_MODE.useRealAPI.session) {
      // 1. 通过 roomId 或 sessionId 获取场次信息
      if (!sessionId.value && roomId.value) {
        // 先获取房间详情
        const roomResponse = await getRoomDetail(roomId.value);
        const room = (roomResponse as any).data || roomResponse;
        
        // 🆕 使用真实房间数据
        if (LIVEVIEW_API_MODE.useRealAPI.room) {
          sessionInfo.value = {
            ...sessionInfo.value,
            title: room.title,              // ✅ 使用真实标题
            cover_url: room.cover_url,      // ✅ 使用真实封面
            description: room.description,  // ✅ 使用真实描述
          };
        }
        
        // 查找场次ID
        if (room.current_session_id) {
          sessionId.value = room.current_session_id;
        } else {
          const sessionsResponse = await getSessionList(roomId.value, { page: 1, size: 1 });
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

      // 2. 获取场次详情（包含播放地址）
      if (sessionId.value) {
        const sessionResponse = await getSessionDetail(sessionId.value);
        const sessionData = (sessionResponse as any).data || sessionResponse;
        
        // 🆕 合并真实场次数据到 sessionInfo
        sessionInfo.value = {
          ...sessionInfo.value,          // 保留 Mock 的其他字段
          id: sessionData.id,
          room_id: sessionData.room_id,
          status: sessionData.status,    // ✅ 真实状态
          start_time: sessionData.start_time,
          end_time: sessionData.end_time,
          playback_url: sessionData.playback_url,  // ✅ 真实播放地址
          statistics: sessionData.statistics,      // ✅ 真实统计数据
        };
        
        console.log('[LiveView] ✅ 使用真实API数据:', {
          sessionId: sessionData.id,
          hasPlaybackUrl: !!sessionData.playback_url,
          status: sessionData.status,
        });
      }
    } else {
      // 完全使用 Mock 数据
      sessionInfo.value = mockSessionData;
    }

    // ===== 🔄 互动数据：使用Mock =====
    if (LIVEVIEW_API_MODE.useMockData.chat) {
      chatMessages.value = mockChatMessages;
    }
    if (LIVEVIEW_API_MODE.useMockData.qa) {
      questions.value = mockQuestions;
    }
    if (LIVEVIEW_API_MODE.useMockData.recommend) {
      relatedSessions.value = mockRelatedSessions;
    }
    if (LIVEVIEW_API_MODE.useMockData.materials) {
      materials.value = mockMaterials;
    }

    // 设置播放地址
    setupPlayerSource();
    
    // 加载观看人数
    if (LIVEVIEW_API_MODE.useMockData.viewerCount) {
      viewerCount.value = mockViewerCount.count;
    } else {
      await loadViewerCount();
    }

    isLoading.value = false;
  } catch (err) {
    console.error('[LiveView] 数据加载失败:', err);
    error.value = '加载失败，请重试';
    isLoading.value = false;
  }
}
</script>
```

---

#### 2. 优化播放地址设置逻辑

确保播放器能正确使用真实 API 返回的播放地址：

```vue
<script setup lang="ts">
function setupPlayerSource() {
  if (!sessionInfo.value) {
    error.value = '场次信息不存在';
    return;
  }

  const session = sessionInfo.value;

  // 🎯 播放地址获取策略（优先使用真实API数据）
  if (session.status === 'live') {
    // 直播中：优先 live_url，降级 playback_url
    playerSourceUrl.value = session.live_url || session.playback_url || '';
  } else if (session.status === 'finished' || session.status === 'ended') {
    // 已结束：使用 playback_url（回放地址）
    playerSourceUrl.value = session.playback_url || '';
  } else {
    // 计划中或其他状态：尝试使用可用地址
    playerSourceUrl.value = session.playback_url || session.live_url || '';
  }

  console.log('[LiveView] 播放地址已设置:', {
    status: session.status,
    url: playerSourceUrl.value,
    hasPlaybackUrl: !!session.playback_url,
    hasLiveUrl: !!session.live_url,
  });

  if (!playerSourceUrl.value) {
    console.error('[LiveView] ⚠️ 播放地址为空！');
    error.value = '暂无可播放内容';
  }
}
</script>
```

---

#### 3. 优化 UI 显示（使用真实数据）

确保页面正确显示真实的标题、封面、统计数据：

```vue
<template>
  <view class="live-view-page">
    <!-- 标题：使用真实数据 -->
    <text class="live-title">
      {{ sessionInfo?.title || '直播标题' }}
    </text>

    <!-- 播放器：使用真实封面 -->
    <VideoPlayerApp
      :src="playerSourceUrl"
      :poster="sessionInfo?.cover_url || '/static/default-cover.png'"
      :autoplay="true"
    />

    <!-- 状态：使用真实状态 -->
    <view class="status-badge" :class="getStatusClass(sessionInfo?.status)">
      <text>{{ getStatusText(sessionInfo?.status) }}</text>
    </view>

    <!-- 统计：优先使用真实统计，降级使用Mock -->
    <text class="viewer-count">
      👁️ {{ formatViewerCount(sessionInfo?.statistics?.total_viewer_count || viewerCount) }}人在看
    </text>

    <!-- 详情：使用真实描述 -->
    <text class="block-content">
      {{ sessionInfo?.description || sessionInfo?.summary || '暂无介绍' }}
    </text>
  </view>
</template>

<script setup lang="ts">
// 状态映射
function getStatusClass(status: string) {
  const statusMap: Record<string, string> = {
    'live': 'live',
    'scheduled': 'scheduled',
    'finished': 'ended',
    'ended': 'ended',
  };
  return statusMap[status] || 'scheduled';
}

function getStatusText(status: string) {
  const textMap: Record<string, string> = {
    'live': '直播中',
    'scheduled': '即将开始',
    'finished': '已结束',
    'ended': '已结束',
  };
  return textMap[status] || '未知';
}
</script>
```

---

### 方案二：API 级别拦截（高级方案）

**原理**：在 `request.ts` 中根据接口路径决定是否使用真实 API。

**优点**：
- ✅ 更精细的控制
- ✅ 可以按接口类型分组

**缺点**：
- ⚠️ 配置较复杂
- ⚠️ 需要维护路径映射表

**实现示例**：

```typescript
// src/utils/request.ts

// 真实API白名单（这些接口使用真实后端）
const REAL_API_WHITELIST = [
  /^\/rooms/,              // 所有房间相关接口
  /^\/sessions/,           // 所有场次相关接口
  /^\/playback/,           // 播放相关接口
];

export const request = <T = any>(options: RequestOptions): Promise<T> => {
  // 检查是否在白名单中
  const useRealAPI = REAL_API_WHITELIST.some(pattern => pattern.test(options.url));
  
  if (ENV_CONFIG.VITE_USE_MOCK && !useRealAPI) {
    // 使用 Mock 数据
    return Promise.resolve(getMockData(options.url) as T);
  }
  
  // 使用真实 API
  return uni.request({
    // ... 正常请求逻辑
  });
};
```

---

## 📊 真实数据字段映射表

### 可以立即使用的真实数据

| UI 元素 | Mock 字段 | 真实 API 字段 | 数据来源 | 状态 |
|---------|-----------|--------------|---------|------|
| 直播标题 | `title` | `room.title` 或 `session.title` | `GET /rooms/{id}` | ✅ 立即可用 |
| 封面图片 | `cover_url` | `room.cover_url` | `GET /rooms/{id}` | ✅ 立即可用 |
| 播放地址 | `playback_url` | `session.playback_url` | `GET /sessions/{id}` | ✅ 立即可用 |
| 直播状态 | `status` | `session.status` | `GET /sessions/{id}` | ✅ 立即可用 |
| 开始时间 | `start_time` | `session.start_time` | `GET /sessions/{id}` | ✅ 立即可用 |
| 房间描述 | `description` | `room.description` | `GET /rooms/{id}` | ✅ 立即可用 |

### 暂时使用 Mock 的数据

| UI 元素 | Mock 字段 | 真实 API 字段 | 状态 | 原因 |
|---------|-----------|--------------|------|------|
| 专家信息 | `expert.*` | `session.featured_expert_id` | 🔄 待对接 | 需要关联查询专家表 |
| 聊天消息 | `chatMessages` | 待定 | 🔄 待实现 | WebSocket 或轮询接口 |
| 问答列表 | `questions` | 待定 | 🔄 待实现 | 后端接口未开放 |
| 推荐列表 | `relatedSessions` | 待定 | 🔄 待实现 | 推荐算法未实现 |
| 观看人数 | `viewerCount` | `session.statistics.total_viewer_count` | ⚠️ 可选 | 统计可能不准确 |

---

---

## 🔍 完整的 API 调用链路图

```
用户点击直播卡片
    ↓
跳转到 LiveView 页面（传递 roomId 或 sessionId）
    ↓
loadSessionData() 函数执行
    ↓
┌─────────────────────────────────────┐
│ 步骤1: 获取房间详情                    │
│ API: GET /rooms/{roomId}             │
│ 目的: 查找 current_session_id         │
└─────────────────────────────────────┘
    ↓
    ├─ 有 current_session_id？
    │   YES → 使用该 sessionId
    │   NO  → 继续下一步
    ↓
┌─────────────────────────────────────┐
│ 步骤2: 获取场次列表                    │
│ API: GET /rooms/{roomId}/sessions    │
│ 目的: 获取第一个场次ID                 │
└─────────────────────────────────────┘
    ↓
    ├─ 场次列表为空？
    │   YES → ❌ 失败（这可能是你的问题！）
    │   NO  → 使用第一个场次ID
    ↓
┌─────────────────────────────────────┐
│ 步骤3: 获取场次详情                    │
│ API: GET /sessions/{sessionId}       │
│ 目的: 获取播放地址                     │
└─────────────────────────────────────┘
    ↓
    ├─ 有 playback_url 或 live_url？
    │   YES → ✅ 设置播放地址，开始播放
    │   NO  → ❌ 失败（无播放地址）
```

---

## 🎯 立即可行的实施步骤

### 第一阶段：最小可用版本（30分钟）⭐

**目标**：让播放功能工作起来，使用真实播放地址

**步骤**：

1. **修改 LiveView.vue 的 LIVEVIEW_API_MODE 配置**
   ```bash
   # 文件位置：src/pages/app/live/LiveView.vue
   # 找到第 442 行附近
   ```

2. **替换 loadSessionData 函数**（复制上面"方案一"中的代码）

3. **测试播放**
   ```bash
   # 使用测试工具找到的可播放场次
   # 场次ID: 0902349d-97cf-49b8-a7db-aa957bd5bb5d
   
   # H5测试
   npm run dev:h5
   # 访问: http://localhost:5173/pages/h5/live/LiveView?sessionId=0902349d-97cf-49b8-a7db-aa957bd5bb5d
   
   # App测试
   npm run dev:app
   # 在开发工具中访问: pages/app/live/LiveView?sessionId=0902349d-97cf-49b8-a7db-aa957bd5bb5d
   ```

**预期结果**：
- ✅ 视频能正常播放
- ✅ 显示真实的房间标题
- ✅ 显示真实的封面图片
- ✅ 显示真实的直播状态
- 🔄 聊天/问答等功能仍使用 Mock（正常）

---

### 第二阶段：优化用户体验（1小时）

**目标**：优化数据显示和错误处理

**步骤**：

1. **添加加载状态提示**
   ```vue
   <view v-if="isLoading" class="loading-overlay">
     <text>正在加载播放数据...</text>
   </view>
   ```

2. **优化错误提示**
   ```typescript
   if (!sessionData.playback_url) {
     uni.showToast({
       title: '该场次暂无播放地址',
       icon: 'none',
       duration: 3000
     });
   }
   ```

3. **添加数据降级逻辑**
   ```typescript
   // 如果真实API失败，降级使用Mock数据
   try {
     const sessionData = await getSessionDetail(sessionId.value);
     sessionInfo.value = sessionData;
   } catch (error) {
     console.warn('[LiveView] 真实API失败，降级使用Mock:', error);
     sessionInfo.value = mockSessionData;
   }
   ```

---

### 第三阶段：集成更多真实数据（可选）

**目标**：逐步替换更多 Mock 数据

**步骤**：

1. **使用真实统计数据**
   ```typescript
   // 使用 session.statistics 中的数据
   viewerCount.value = sessionInfo.value?.statistics?.total_viewer_count || 0;
   likeCount.value = sessionInfo.value?.statistics?.total_like_count || 0;
   ```

2. **等待后端完善后，接入更多API**
   - 专家信息 API
   - 聊天消息 WebSocket
   - 问答列表 API
   - 推荐算法 API

---

## 📝 配置文件说明

### .env.development 配置

```bash
# API基础地址
VITE_BASE_API_URL=http://124.220.235.226:8000/api/v1

# Mock模式开关（全局）
# true: 所有页面使用Mock | false: 所有页面使用真实API
VITE_USE_MOCK=true

# 注意：LiveView 页面会忽略此开关，使用自己的混合模式配置
```

### LiveView 页面配置

```typescript
// src/pages/app/live/LiveView.vue

const LIVEVIEW_API_MODE = {
  useRealAPI: {
    room: true,      // ✅ 使用真实房间信息
    session: true,   // ✅ 使用真实场次信息
    playback: true,  // ✅ 使用真实播放地址
  },
  useMockData: {
    chat: true,      // 🔄 暂时使用Mock聊天
    qa: true,        // 🔄 暂时使用Mock问答
    recommend: true, // 🔄 暂时使用Mock推荐
  }
};
```

---

## 🐛 常见问题 FAQ

### Q1: 为什么设置了真实API还是看到Mock数据？

**A:** 检查以下几点：
1. 是否重启了开发服务器（`npm run dev:app` 或 `npm run dev:h5`）
2. 是否传递了正确的 `sessionId` 或 `roomId` 参数
3. 查看浏览器控制台，确认API调用成功
4. 检查 `LIVEVIEW_API_MODE.useRealAPI` 配置是否正确

---

### Q2: 播放地址获取到了但无法播放？

**A:** 可能原因：
1. **网络问题**：检查播放地址是否可访问
   ```bash
   # 测试播放地址
   curl -I https://mp2.dayilive.com/clip/2309808065.m3u8
   ```

2. **CORS问题**：播放服务器未设置跨域头
   - 临时解决：在测试工具中播放
   - 长期解决：联系后端配置CORS

3. **格式不支持**：浏览器/播放器不支持HLS格式
   - H5端：确保引入了 `hls.js`
   - App端：使用原生视频组件

---

### Q3: 如何找到更多可播放的场次？

**A:** 使用批量查询脚本：

```powershell
# PowerShell 脚本
$rooms = (Invoke-RestMethod "http://124.220.235.226:8000/api/v1/rooms?page=1&size=50").data.items

$playableSessions = @()
foreach ($room in $rooms) {
    $sessions = (Invoke-RestMethod "http://124.220.235.226:8000/api/v1/rooms/$($room.id)/sessions").data.items
    
    foreach ($s in $sessions) {
        if ($s.playback_url) {
            $playableSessions += @{
                roomTitle = $room.title
                sessionId = $s.id
                status = $s.status
                playbackUrl = $s.playback_url
            }
            Write-Host "✅ 可播放: $($room.title)" -ForegroundColor Green
            Write-Host "   SessionID: $($s.id)" -ForegroundColor Cyan
            Write-Host "   URL: $($s.playback_url)" -ForegroundColor Yellow
        }
    }
}

Write-Host "`n找到 $($playableSessions.Count) 个可播放场次" -ForegroundColor Magenta
```

---

### Q4: 真实数据中没有专家信息怎么办？

**A:** 当前方案：
1. **保留Mock数据**：专家信息继续使用Mock
2. **或者隐藏**：如果不是必须显示，可以隐藏该模块
3. **等待后端**：等后端实现专家关联查询后再接入

```vue
<!-- 条件渲染 -->
<view v-if="sessionInfo?.expert" class="host-section">
  <!-- 显示专家信息 -->
</view>
<view v-else class="host-section">
  <!-- 显示默认/占位信息 -->
  <text>主讲专家信息待补充</text>
</view>
```

---

### Q5: 混合模式会不会影响其他页面？

**A:** 不会。混合模式只在 LiveView 页面内部生效：
- ✅ 首页继续使用全局 `VITE_USE_MOCK` 配置
- ✅ 我的页面继续使用全局配置
- ✅ 只有 LiveView 使用特殊的混合模式

---

## ✅ 功能检查清单

在提交代码前，请确认：

### 播放功能
- [ ] 能获取到真实的播放地址（`playback_url`）
- [ ] 视频能正常播放
- [ ] 播放器显示正确的封面图片
- [ ] 播放进度条正常工作

### 数据显示
- [ ] 房间标题显示正确（来自真实API）
- [ ] 封面图片显示正确（来自真实API）
- [ ] 直播状态显示正确（live/scheduled/finished）
- [ ] 开始时间显示正确

### 降级策略
- [ ] API失败时有友好的错误提示
- [ ] 没有播放地址时显示"暂无播放内容"
- [ ] Mock数据的互动功能仍然正常（聊天/问答）

### 开发体验
- [ ] 控制台有清晰的日志输出
- [ ] 能快速切换真实API/Mock模式
- [ ] 代码有注释说明配置选项

---

## 📞 需要帮助？

如果实施过程中遇到问题：

1. **检查控制台日志**
   - 查看是否有API请求错误
   - 确认返回的数据结构

2. **使用测试工具验证**
   - 打开 `test-real-api.html`
   - 测试API是否正常返回数据

3. **提供以下信息**
   - 具体的错误信息/截图
   - 控制台日志
   - 使用的场次ID

---

## 🎉 预期成果

完成本方案后，你将获得：

✅ **可用的播放功能**
- 使用真实API获取播放地址
- 显示真实的房间信息
- 支持多个场次切换

✅ **灵活的开发模式**
- 核心功能用真实API测试
- 未完成功能用Mock开发
- 随时可以切换模式

✅ **良好的用户体验**
- 真实数据展示
- 流畅的播放体验
- 友好的错误提示

---

**祝开发顺利！有任何问题随时沟通。** 🚀

### 原因1: 房间没有 current_session_id 且场次列表为空

**症状：**
- `room.current_session_id` 为 `null` 或 `undefined`
- `getSessionList` 返回空数组 `[]`

**解决方案：**
```javascript
// 在后台管理系统中为该房间创建场次
// 或者使用已有场次数据的房间
```

**测试方法：**
使用我创建的测试工具 `test-real-api.html`，点击"一键测试完整流程"

---

### 原因2: API 路径不正确

**症状：**
- 返回 404 错误
- 控制台显示 "Failed to fetch" 或 CORS 错误

**可能的问题：**
```javascript
// ❌ 错误：路径缺少 /api/v1 前缀
GET /rooms/xxx/sessions

// ✅ 正确：完整路径
GET /api/v1/rooms/xxx/sessions
```

**检查方法：**
查看 [src/api/session.ts](src/api/session.ts#L14) 中的 `getSessionList` 函数：

```typescript
export const getSessionList = (roomId: string, params: { page?: number, size?: number }) => {
  return request<PaginatedSessions>({
    url: `/rooms/${roomId}/sessions`,  // ✅ request函数会自动添加 /api/v1 前缀
    method: 'GET',
    data: params,
  });
};
```

---

### 原因3: 后端返回的数据结构不匹配

**症状：**
- API 请求成功（200），但前端解析失败
- 控制台显示 `sessionInfo.value` 为 `undefined`

**可能的数据结构差异：**

```javascript
// 后端可能返回：
{
  "data": {
    "items": [...],
    "total": 10
  }
}

// 或者直接返回：
{
  "items": [...],
  "total": 10
}
```

**前端代码处理：**
```typescript
// 当前代码已经处理了两种情况
const sessions = (sessionsResponse as any).data?.items || (sessionsResponse as any).items || [];
```

---

## 🚀 立即可行的解决步骤

### 步骤1: 测试 API 连通性（5分钟）

1. 用浏览器打开 `test-real-api.html` 文件
2. 点击 **"🚀 一键测试完整流程"** 按钮
3. 查看测试结果：

**成功的输出应该是：**
```
✅ 步骤1成功: 找到房间 "xxx" (ID: xxx)
✅ 步骤2成功: 房间有current_session_id = xxx
✅ 步骤3成功: 获取到场次 "xxx"
✅ 步骤4成功: 找到播放地址!
🎬 播放地址: https://mp2.dayilive.com/clip/xxx.m3u8
```

**如果失败，会明确指出哪一步失败了。**

---

### 步骤2: 根据测试结果决定下一步

#### 场景A: 测试成功 ✅

说明后端 API 正常，可以关闭 Mock 模式：

1. 修改 `.env.development`：
```bash
VITE_USE_MOCK=false
```

2. 重启开发服务器：
```bash
npm run dev:app
```

3. 在 App 中点击直播卡片，应该能播放真实视频

---

#### 场景B: 步骤1失败（无法获取房间列表） ❌

**问题：** 后端服务未启动或网络不通

**解决方案：**
1. 检查后端服务是否运行在 `https://124.220.235.226:8000`
2. 用浏览器直接访问：`https://124.220.235.226/api/v1/rooms?page=1&size=1`
3. 如果浏览器也无法访问，联系后端同学

---

#### 场景C: 步骤2失败（房间有，但没有场次） ⚠️

**这可能是你昨天遇到的问题！**

**问题：** 房间存在，但没有创建场次

**解决方案：**

**方法1（推荐）：找一个有场次数据的房间**
```html
<!-- 在 test-real-api.html 中 -->
1. 点击"获取房间列表"
2. 查看每个房间的 current_session_id
3. 选择一个有 current_session_id 的房间
4. 记录该 roomId
```

**方法2：在后台管理系统中创建场次**
1. 登录后台管理系统
2. 进入"房间管理"
3. 为该房间创建一个场次，并设置播放地址

---

#### 场景D: 步骤4失败（场次有，但没有播放地址） ❌

**问题：** 场次存在，但 `playback_url` 和 `live_url` 都为空

**解决方案：**
1. 在后台管理系统中编辑该场次
2. 设置 `playback_url` 字段，例如：
   ```
   https://mp2.dayilive.com/clip/2aa5b88f3d.m3u8
   ```

---

### 步骤3: 修改首页卡片跳转逻辑（可选）

如果你发现某些房间没有场次，可以在跳转前做判断：

```vue
<!-- src/pages/app/tabbar/home/index.vue -->
<script setup>
function handleRoomClick(room: any) {
  // 检查是否有可用的场次
  if (!room.current_session_id) {
    uni.showToast({
      title: '该房间暂无可播放内容',
      icon: 'none'
    });
    return;
  }

  // 直播中或回放状态直接跳转到播放页面
  uni.navigateTo({
    url: `/pages/app/live/LiveView?roomId=${room.id}&title=${encodeURIComponent(room.title)}`,
  });
}
</script>
```

---

## 📝 关键代码位置参考

| 文件 | 行号 | 功能 |
|------|------|------|
| [LiveView.vue](src/pages/app/live/LiveView.vue#L432) | 432-529 | 数据加载逻辑 `loadSessionData()` |
| [LiveView.vue](src/pages/app/live/LiveView.vue#L531) | 531-565 | 播放地址设置 `setupPlayerSource()` |
| [session.ts](src/api/session.ts#L14) | 14-20 | 获取场次列表 API |
| [session.ts](src/api/session.ts#L23) | 23-28 | 获取场次详情 API |
| [room.ts](src/api/room.ts#L30) | 30-35 | 获取房间详情 API |

---

## 🎯 今天的目标建议

### 优先级1：诊断 API 问题（必须）

1. ✅ 用 `test-real-api.html` 测试完整流程
2. ✅ 找到至少1个可用的 sessionId
3. ✅ 确认能获取到播放地址

### 优先级2：关闭 Mock 测试真实播放（重要）

1. 修改 `.env.development` 中 `VITE_USE_MOCK=false`
2. 重启服务器
3. 在 App 中点击卡片，测试真实播放

### 优先级3：优化用户体验（可选）

1. 修复分享功能（已完成 ✅）
2. 添加加载状态提示
3. 优化错误提示信息

---

## ❓ 常见问题 FAQ

### Q1: 为什么 Mock 模式下能播放，关闭 Mock 后不行？

**A:** Mock 模式使用的是硬编码的播放地址：
```typescript
// mock-data.ts
const REAL_M3U8_URL = 'https://mp2.dayilive.com/clip/2aa5b88f3d.m3u8';
```

真实 API 模式需要从后端获取，可能后端数据中没有设置播放地址。

---

### Q2: 能不能让前端直接调用播放列表，不依赖房间？

**A:** 可以！修改跳转逻辑，直接传递 sessionId：

```typescript
// 首页获取推荐列表时，直接使用 sessionId
uni.navigateTo({
  url: `/pages/app/live/LiveView?sessionId=${session.id}`
});
```

这样可以跳过"获取房间 → 查找场次"的步骤。

---

### Q3: 后端说有几十个视频，但我获取不到？

**A:** 可能的原因：
1. 视频数据在 `sessions` 表中，而不是 `rooms` 表
2. 需要直接调用 `/sessions` 接口（而不是 `/rooms/{id}/sessions`）
3. 需要认证 token

**测试方法：**
用浏览器直接访问：
```
https://124.220.235.226/api/v1/sessions?page=1&size=20
```

如果能看到数据，说明需要修改前端获取逻辑。

---

## 📞 需要帮助？

如果测试后仍有问题，请提供以下信息：

1. `test-real-api.html` 的完整测试结果截图
2. 浏览器控制台的错误信息
3. 具体在哪一步失败了

我会根据具体情况给出针对性的解决方案！

---

## ✅ 检查清单

在开始调试前，请确认：

- [ ] 后端服务正在运行（访问 `https://124.220.235.226/api/v1/rooms` 能看到数据）
- [ ] 已用 `test-real-api.html` 测试过 API
- [ ] 已确认至少有1个房间有场次数据
- [ ] 已确认至少有1个场次有播放地址
- [ ] 开发服务器已重启（修改 `.env` 后必须重启）

---

**祝调试顺利！如果遇到问题，随时告诉我测试结果。** 🚀
