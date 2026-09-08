# 🎯 直播播放页面API调用升级方案

> **目标**：将所有页面从旧API升级到最新后端API（V6深度融合版）  
> **生成时间**：2026-01-26  
> **依据文档**：
> - 《直播核心功能设计文档_v6_深度融合最终版.md》
> - 《直播核心功能设计文档_v6_后端新增api接口和模块设计文档-v2.md》

---

## 📚 一、后端最新API概览

### 1.1 核心直播功能API（V6主文档）

#### 房间相关API
| 接口 | 方法 | 路径 | 用途 | 当前使用状态 |
|------|------|------|------|-------------|
| 获取房间列表 | GET | `/api/v1/rooms` | 首页直播卡片列表 | ✅ 已使用（`src/api/room.ts`） |
| 获取房间详情 | GET | `/api/v1/rooms/{room_id}` | 播放页房间信息 + Tab列表 | ✅ 已使用 |
| 获取分会场列表 | GET | `/api/v1/rooms/{room_id}/sub-venues` | 多会场切换 | ❌ 未使用 |

#### 场次相关API
| 接口 | 方法 | 路径 | 用途 | 当前使用状态 |
|------|------|------|------|-------------|
| 获取场次列表 | GET | `/api/v1/rooms/{room_id}/sessions` | 房间历史场次 | ✅ 已使用（`src/api/session.ts`） |
| 获取场次详情 | GET | `/api/v1/sessions/{session_id}` | **播放页核心接口** | ✅ 已使用 |
| 创建场次 | POST | `/api/v1/rooms/{room_id}/sessions` | 创建计划场次 | ✅ 已使用 |

#### Tab管理API（V6主文档）
| 接口 | 方法 | 路径 | 用途 | 当前使用状态 |
|------|------|------|------|-------------|
| 获取Tab列表 | GET | `/api/v1/admin/rooms/{room_id}/tabs` | 播放页Tab配置 | ❌ **未实现** |
| 创建Tab | POST | `/api/v1/admin/rooms/{room_id}/tabs` | 管理页创建Tab | ❌ **未实现** |
| 更新Tab | PATCH | `/api/v1/admin/rooms/{room_id}/tabs/{tab_id}` | 更新Tab顺序/内容 | ❌ **未实现** |
| 删除Tab | DELETE | `/api/v1/admin/rooms/{room_id}/tabs/{tab_id}` | 删除Tab | ❌ **未实现** |

#### 留言相关API（V6主文档）
| 接口 | 方法 | 路径 | 用途 | 当前使用状态 |
|------|------|------|------|-------------|
| 获取留言列表 | GET | `/api/v1/rooms/{room_id}/messages` | 播放页聊天Tab | ❌ **未实现** |
| 发送留言 | POST | `/api/v1/rooms/{room_id}/messages` | 聊天消息发送 | ❌ **未实现** |

### 1.2 新增API（V2.1扩展文档）

#### 首页专用API
| 接口 | 方法 | 路径 | 用途 | 当前使用状态 |
|------|------|------|------|-------------|
| 获取首页直播间列表 | GET | `/api/v1/homepage/rooms` | 首页直播卡片（含专家+标签，**不含Tab**） | ✅ 已实现但**未使用** |
| 获取轮播图 | GET | `/api/v1/homepage/banners` | 首页顶部轮播图 | ❌ **未实现** |

**⚠️ 重要说明**：
- `GET /api/v1/homepage/rooms`：**轻量级API**，用于首页快速展示
  - ✅ 包含：基础信息、专家信息、标签、实时状态、观看人数
  - ❌ 不包含：Tab配置、详细内容、播放地址
- `GET /api/v1/rooms/{id}`：**完整API**，用于播放页详细展示
  - ✅ 包含：完整房间信息、Tab配置列表、播放地址

#### 专家订阅API（V2.1新增）
| 接口 | 方法 | 路径 | 用途 | 当前使用状态 |
|------|------|------|------|-------------|
| 关注专家 | POST | `/api/v1/users/me/subscriptions/experts/{expert_id}` | 播放页"关注"按钮 | ❌ **未实现** |
| 取消关注 | DELETE | `/api/v1/users/me/subscriptions/experts/{expert_id}` | 取消关注专家 | ❌ **未实现** |
| 获取关注列表 | GET | `/api/v1/users/me/subscriptions/experts` | 我的关注页 | ❌ **未实现** |

#### 收藏功能API（V2.1新增）
| 接口 | 方法 | 路径 | 用途 | 当前使用状态 |
|------|------|------|------|-------------|
| 添加收藏 | POST | `/api/v1/users/me/favorites` | 播放页"收藏"按钮 | ❌ **未实现** |
| 取消收藏 | DELETE | `/api/v1/users/me/favorites/{room_id}` | 取消收藏 | ❌ **未实现** |
| 获取收藏列表 | GET | `/api/v1/users/me/favorites` | 我的收藏页 | ❌ **未实现** |

---

## 🔍 二、当前API调用现状分析

### 2.1 首页（Home）- 直播卡片列表

**当前实现**：[src/pages/app/tabbar/home/index.vue](src/pages/app/tabbar/home/index.vue#L226)

```typescript
// ✅ 当前使用：GET /api/v1/rooms（旧API）
const res = await getRoomList({
  page: params.page,
  size: params.size,
});
```

**存在问题**：
1. ❌ 使用的是通用房间列表API，不包含实时直播状态
2. ❌ 缺少专家信息（名称、头像、医院、科室）
3. ❌ 缺少观看人数、热度等首页所需字段
4. ❌ 轮播图功能使用Mock数据（`useMockData.banners: true`）

**升级方案**：
```typescript
// ✅ 升级后：GET /api/v1/homepage/rooms（新API）
import { getHomepageRooms } from '@/api/homepage';

const res = await getHomepageRooms({
  page: params.page,
  size: params.size,
  sort: 'heat:desc',  // 按热度排序
  category_id: selectedCategoryId.value,  // 分类筛选
});

// 返回数据结构（轻量级，适合首页快速加载）
interface HomepageRoomItem {
  id: string;
  title: string;
  cover_url: string | null;
  summary: string | null;
  live_status: 'scheduled' | 'live' | 'finished' | 'ready';
  is_private: boolean;
  category: { id: string; name: string; } | null;
  
  // ✅ 首页特有字段
  expert: {  // 主讲专家信息（从场次聚合）
    expert_id: string;
    name: string;
    title: string;
    hospital: string;
    department: string;
    avatar: string | null;
  } | null;
  
  tags: Array<{ id: string; name: string; }>;  // 标签列表
  viewer_count: number | null;  // 正在直播的观看人数
  start_time: string | null;  // 计划开始时间
  duration_seconds: number | null;  // 回放时长
  play_count: number | null;  // 回放播放次数
  
  // ❌ 注意：不包含以下字段（需要调用房间详情API获取）
  // tabs: Array<LiveRoomTab>  // Tab配置
  // live_stream_url: string    // 直播流地址
  // playback_url: string       // 回放地址
}
```

**升级步骤**：
1. ✅ **API已实现**：[src/api/homepage.ts](src/api/homepage.ts) 已有 `getHomepageRooms()` 函数
2. ✅ **类型已定义**：[src/types/homepage.ts](src/types/homepage.ts) 已有 `HomepageRoomItem` 类型
3. ✅ **Store已准备**：当前Store使用的 `getRoomList()` 需要替换
4. ⏳ **待修改**：[src/pages/app/tabbar/home/index.vue](src/pages/app/tabbar/home/index.vue#L226) 的 `loadRooms()` 函数

### 2.2 首页 - 轮播图

**当前实现**：使用Mock数据

```typescript
// 🔄 当前使用Mock数据
useMockData: {
  banners: true,  // 轮播图（可选）
}
```

**升级方案**：
```typescript
// ✅ 升级后：GET /api/v1/homepage/banners
import { getHomepageBanners } from '@/api/homepage';

const bannersRes = await getHomepageBanners({
  type: 'homepage',  // 'homepage' | 'topic' | 'category'
  category_id: selectedCategoryId.value,  // 可选，分类筛选
});

// 返回数据结构
interface Banner {
  id: string;
  title: string;
  image_url: string;
  link_type: 'room' | 'topic' | 'external' | 'none';
  link_target: string | null;
  sort_order: number;
  is_active: boolean;
}
```

**升级步骤**：
1. ❌ **API未实现**：需要在 `src/api/homepage.ts` 中添加 `getHomepageBanners()` 函数
2. ❌ **类型未定义**：需要在 `src/types/homepage.ts` 中添加 `Banner` 类型
3. ⏳ **待实现**：实现API调用 → 替换Mock数据

---

### 2.3 播放页（LiveView）- 核心数据

**当前实现**：[src/pages/app/live/LiveView.vue](src/pages/app/live/LiveView.vue#L453)

```typescript
// ✅ 已使用真实API
const LIVEVIEW_API_MODE = {
  useRealAPI: {
    room: true,      // ✅ GET /api/v1/rooms/{room_id}
    session: true,   // ✅ GET /api/v1/sessions/{session_id}
    playback: true,  // ✅ playback_url字段
  },
  useMockData: {
    chat: true,      // 🔄 聊天消息（未实现API）
    qa: true,        // 🔄 问答（未实现API）
    recommend: false,// ✅ 推荐列表（已改为真实API）
    materials: true, // 🔄 资料下载（未实现API）
    viewerCount: true,// 🔄 观看人数（后端统计未完善）
  }
};
```

**存在问题**：
1. ❌ **Tab数据使用硬编码**：`tabs` 数组写死在代码中，不从API获取
2. ❌ **聊天功能使用Mock**：`chat: true`
3. ❌ **问答功能未实现**：`qa: true`
4. ❌ **资料下载未实现**：`materials: true`
5. ⚠️ **专家信息降级处理**：后端未返回完整专家信息时使用Mock

**升级方案**：

#### 2.3.1 Tab数据（核心升级点）

**当前实现**：硬编码Tab列表

```typescript
// ❌ 当前：硬编码
const tabs = [
  { key: 'introduction', label: '直播介绍' },
  { key: 'case', label: '病例介绍' },
  { key: 'chat', label: '聊天' },
  { key: 'materials', label: '资料' },
  { key: 'related', label: '推荐' }
];
```

**升级方案**：从房间详情API获取Tab配置

```typescript
// ✅ 升级后：从API获取
// 1. 调用房间详情API（已经在调用，但未使用tabs字段）
const roomResponse = await getRoomDetail(roomId.value);
const room = (roomResponse as any).data || roomResponse;

// 2. 提取tabs字段（后端返回格式）
const tabs = ref<Array<{
  id: string;
  key: string;
  label: string;
  content_type: 'text' | 'html' | 'mixed';
  content: string | null;
  icon: string | null;
  sort_order: number;
  is_visible: boolean;
}>>(room.tabs || []);

// 3. 过滤并排序
const visibleTabs = computed(() => 
  tabs.value
    .filter(tab => tab.is_visible)
    .sort((a, b) => a.sort_order - b.sort_order)
);
```

**Tab数据结构**（来自V6主文档）：

```typescript
// live_room_tabs表结构
interface LiveRoomTab {
  id: string;
  room_id: string;
  key: string;  // 'introduction' | 'case' | 'qa' | 'materials' | 'chat' | 'custom'
  label: string;  // 显示标题
  content_type: 'text' | 'html' | 'mixed';
  content: string | null;  // Tab内容（直播介绍、病例等）
  icon: string | null;
  sort_order: number;  // 排序
  is_visible: boolean;  // 是否显示
  config: any | null;  // 扩展配置（JSON）
  created_at: string;
  updated_at: string;
}
```

**升级步骤**：
1. ✅ **API已支持**：`GET /api/v1/rooms/{room_id}` 已包含 `tabs` 字段（V6主文档 Section 1）
2. ⏳ **待修改**：
   - [LiveView.vue#L413](src/pages/app/live/LiveView.vue#L413) 的硬编码tabs数组
   - 从 `room.tabs` 提取并动态渲染Tab列表
   - Tab内容渲染逻辑（`content_type`决定渲染方式）

#### 2.3.2 聊天留言（优先级高）

**当前实现**：使用Mock数据

```typescript
// 🔄 当前使用Mock
const chatMessages = ref(mockChatMessages);
```

**升级方案**：

```typescript
// ✅ 升级后：调用留言API
import { getRoomMessages, sendRoomMessage } from '@/api/messages';

// 1. 获取留言列表
const loadChatMessages = async () => {
  const res = await getRoomMessages(roomId.value, {
    page: 1,
    size: 50,
    sort: 'created_at:desc',
  });
  chatMessages.value = res.data.items;
};

// 2. 发送留言
const sendMessage = async (content: string) => {
  const res = await sendRoomMessage(roomId.value, {
    content,
    session_id: sessionId.value,  // 可选，关联到当前场次
  });
  chatMessages.value.unshift(res.data);  // 新消息插入顶部
};

// 留言数据结构
interface LiveRoomMessage {
  id: string;
  room_id: string;
  session_id: string | null;
  user_id: string;
  user_name: string;
  user_role: 'REGULAR' | 'MODERATOR' | 'ADMIN' | 'SUPERADMIN';
  content: string;
  reply_to: string | null;  // 回复的留言ID
  is_pinned: boolean;  // 是否置顶
  created_at: string;
  extra: any | null;  // 扩展信息（头像、IP等）
}
```

**升级步骤**：
1. ❌ **API未实现**：需要创建 `src/api/messages.ts`
2. ❌ **类型未定义**：需要在 `src/types/` 中添加 `LiveRoomMessage` 类型
3. ⏳ **待实现**：
   - 实现 `getRoomMessages()` 和 `sendRoomMessage()` API调用
   - 替换Mock数据
   - 实现实时消息刷新（轮询或WebSocket）

#### 2.3.3 专家信息（优化点）

**当前实现**：降级使用Mock数据

```typescript
// ⚠️ 当前：后端未返回专家信息时使用Mock
if (!sessionInfo.value.expert || !sessionInfo.value.expert.name) {
  sessionInfo.value.expert = mockExpertData;
}
```

**升级方案**：
```typescript
// ✅ 升级后：优先使用API专家信息
// 场次详情API已支持expert字段（V2.1文档 Section 4.13）
const sessionResponse = await getSessionDetail(sessionId.value);
const session = sessionResponse.data.data;

// expert字段结构
session.expert = {
  expert_id: string;
  user_id: string | null;
  name: string;
  title: string;
  hospital: string;
  department: string;
  avatar: string | null;
  bio: string | null;
  specialties: string[] | null;
};
```

**升级步骤**：
1. ✅ **后端已支持**：`GET /api/v1/sessions/{session_id}` 返回 `expert` 字段
2. ⏳ **待优化**：移除Mock降级逻辑，改为错误提示（如果expert为空）

---

## 🔄 三、API调用层次关系

### 3.1 数据流向图

```
┌─────────────┐
│  首页卡片    │
└──────┬──────┘
       │ GET /api/v1/homepage/rooms（轻量级API）
       ↓
┌──────────────────────────────────────────────────┐
│  HomepageRoomItem（首页快速展示）                  │
│  ✅ 包含：基础信息 + 专家信息 + 标签 + 实时状态      │
│  ❌ 不含：Tab配置、播放地址、详细内容               │
└──────┬───────────────────────────────────────────┘
       │ 点击卡片（传递：expert, title, cover等基础数据）
       ↓
┌─────────────────────┐
│  播放页 (LiveView)  │
└──────┬──────────────┘
       │
       │ ✅ 复用首页数据：expert, title, cover（立即显示，减少等待）
       │
       ├─→ GET /api/v1/rooms/{room_id}  ← ⚠️ 必须调用（获取Tab配置）
       │   └─ tabs: Array<LiveRoomTab>  ← 首页API没有此字段
       │
       ├─→ GET /api/v1/sessions/{session_id}  ← ⚠️ 必须调用（获取播放地址）
       │   ├─ playback_url, live_stream_url  ← 首页API没有此字段
       │   ├─ expert (如果首页未传递，降级使用此数据)
       │   ├─ status (live/scheduled/finished)
       │   └─ summary, case_description
       │
       ├─→ GET /api/v1/rooms/{room_id}/messages  ← 聊天留言
       │   └─ messages: Array<LiveRoomMessage>
       │
       └─→ GET /api/v1/homepage/rooms  ← 推荐列表（相关直播）
           └─ 复用首页API，筛选条件不同
```

**🔑 关键理解**：

| API类型 | 用途 | 包含字段 | 不包含字段 |
|--------|------|---------|-----------|
| **首页API** (`/homepage/rooms`) | 快速展示列表 | 专家、标签、实时状态 | ❌ Tab配置、播放地址 |
| **房间API** (`/rooms/{id}`) | 完整房间信息 | **Tab配置列表** | - |
| **场次API** (`/sessions/{id}`) | 播放详情 | **播放地址**、专家、内容 | - |

**📌 结论**：
- 首页→播放页：可以传递专家、标题、封面（**减少等待时间**）
- 播放页：**必须调用房间API**（获取Tab配置），**必须调用场次API**（获取播放地址）
- 优化效果：用户点击卡片后立即看到标题/专家，Tab和播放器稍后加载
```typescript
// 首页：存储卡片数据到缓存
const homeStore = useHomeStore();
homeStore.setRoomCache(room.id, room);  // 缓存HomepageRoomItem

// 播放页：优先读取缓存，快速显示基础信息
onLoad((options) => {
  const cachedRoom = homeStore.getRoomCache(options.roomId);
  if (cachedRoom) {
    // ✅ 立即显示标题、封面、专家（来自首页缓存）
    pageTitle.value = cachedRoom.title;
    coverUrl.value = cachedRoom.cover_url;
    expertInfo.value = cachedRoom.expert;  // 复用专家信息
    console.log('[LiveView] ✅ 使用首页缓存数据预填充');
  }
  
  // ⚠️ 但Tab配置必须调用房间详情API获取
  await loadRoomDetail();  // 获取tabs、播放地址等完整信息
});
```

**⚠️ 注意**：首页API **不包含Tab配置**，播放页必须调用以下API：

| 数据类型 | 来源API | 是否可复用首页数据 |
|---------|---------|------------------|
| 标题、封面 | 首页API | ✅ 可复用 |
| 专家信息 | 首页API | ✅ 可复用 |
| 标签列表 | 首页API | ✅ 可复用 |
| **Tab配置** | **房间详情API** | ❌ 必须重新获取 |
| **播放地址** | **场次详情API** | ❌ 必须重新获取 |

**✅ 优化点2：播放页API调用最小化**

```typescript
// 播放页必须调用的API（无法省略）
async function loadPlaybackData() {
  // 1. 调用房间详情API - 获取Tab配置
  const roomRes = await getRoomDetail(roomId.value);
  tabs.value = roomRes.data.tabs;  // ⚠️ 首页API没有此字段
  
  // 2. 调用场次详情API - 获取播放地址
  const sessionRes = await getSessionDetail(sessionId.value);
  playbackUrl.value = sessionRes.data.playback_url;  // ⚠️ 首页API没有此字段
  
  // 3. 专家信息优先使用首页缓存
  if (!expertInfo.value && sessionRes.data.expert) {
    expertInfo.value = sessionRes.data.expert;  // 降级方案
  }
}   cover_url: cachedRoom.cover_url,
    };
  }
  // 然后再调用详细API刷新
  await loadSessionData();
});
```

---

## 📋 四、分步实施计划

### 阶段一：首页卡片升级（1-2天）

**目标**：升级首页直播卡片列表API，显示实时状态和专家信息

**步骤**：
1. ✅ **验证API可用性**：
   - 测试 `GET /api/v1/homepage/rooms` 返回格式
   - 确认 `expert`、`tags`、`viewer_count` 等字段是否正常返回
   
2. **修改首页组件**：
   - 文件：[src/pages/app/tabbar/home/index.vue](src/pages/app/tabbar/home/index.vue)
   - 位置：`loadRooms()` 函数（Line 226）
   - 替换：`getRoomList()` → `getHomepageRooms()`
   
3. **更新RoomCard组件**：
   - 文件：[src/components/shared/RoomCard.vue](src/components/shared/RoomCard.vue)
   - 新增：显示专家信息（头像、姓名、医院、科室）
   - 新增：显示标签列表
   - 新增：显示观看人数（直播中）/播放次数（回放）
   
4. **测试验证**：
   - 真实数据能否正常显示
   - 封面图片是否加载正常
   - 点击跳转到播放页是否正常

**代码示例**：

```typescript
// src/pages/app/tabbar/home/index.vue

// ❌ 旧代码
const res = await getRoomList({
  page: params.page,
  size: params.size,
});

// ✅ 新代码
import { getHomepageRooms } from '@/api/homepage';

const res = await getHomepageRooms({
  page: params.page,
  size: params.size,
  sort: 'heat:desc',  // 按热度排序
  category_id: selectedCategoryId.value,  // 可选：分类筛选
});

// 数据结构已包含专家信息，直接使用
const rooms = res.data.items;  // Array<HomepageRoomItem>
```

---

### 阶段二：播放页Tab升级（2-3天）

**目标**：播放页Tab从硬编码改为从API动态获取

**步骤**：
1. **创建Tab API调用函数**：
   - 文件：新建 `src/api/tabs.ts`
   - 实现：`getRoomTabs(roomId: string)`
   - 返回类型：`Array<LiveRoomTab>`

2. **修改LiveView组件**：
   - 文件：[src/pages/app/live/LiveView.vue](src/pages/app/live/LiveView.vue)
   - 删除：硬编码的 `tabs` 数组（Line 413）
   - 新增：从 `room.tabs` 字段提取Tab配置
   - 排序：按 `sort_order` 排序
   - 过滤：仅显示 `is_visible: true` 的Tab

3. **实现Tab内容渲染**：
   - 根据 `content_type` 决定渲染方式：
     * `text`：纯文本，换行符转`<br>`
     * `html`：富文本，使用 `<rich-text>`
     * `mixed`：混合模式，解析JSON
   - 直播介绍Tab：使用 `session.summary` 或 `tab.content`
   - 病例介绍Tab：使用 `session.case_description` 或 `tab.content`

4. **测试验证**：
   - Tab顺序是否正确
   - Tab内容是否正常显示
   - 切换Tab是否流畅

**代码示例**：

```typescript
// src/api/tabs.ts
import { get } from '@/utils/request';
import type { ApiResponse } from '@/types/common';

export interface LiveRoomTab {
  id: string;
  room_id: string;
  key: string;
  label: string;
  content_type: 'text' | 'html' | 'mixed';
  content: string | null;
  icon: string | null;
  sort_order: number;
  is_visible: boolean;
  config: any | null;
}

export const getRoomTabs = (roomId: string): Promise<ApiResponse<LiveRoomTab[]>> => {
  return get<ApiResponse<LiveRoomTab[]>>(`/admin/rooms/${roomId}/tabs`);
};
```

```typescript
// src/pages/app/live/LiveView.vue

// ✅ 从房间详情获取Tab配置
const tabs = ref<LiveRoomTab[]>([]);

async function loadRoomTabs() {
  const roomResponse = await getRoomDetail(roomId.value);
  const room = (roomResponse as any).data || roomResponse;
  
  // 提取tabs字段
  const rawTabs = room.tabs || [];
  
  // 过滤并排序
  tabs.value = rawTabs
    .filter((tab: LiveRoomTab) => tab.is_visible)
    .sort((a: LiveRoomTab, b: LiveRoomTab) => a.sort_order - b.sort_order);
  
  console.log('[LiveView] ✅ 加载Tab配置:', tabs.value.length, '个Tab');
}
```

---

### 阶段三：聊天留言功能（3-4天）

**目标**：实现聊天Tab的真实留言功能

**步骤**：
1. **创建Messages API模块**：
   - 文件：新建 `src/api/messages.ts`
   - 实现：`getRoomMessages()`, `sendRoomMessage()`
   - 类型：定义 `LiveRoomMessage` 类型

2. **修改LiveView聊天Tab**：
   - 删除：Mock数据 `mockChatMessages`
   - 新增：调用 `getRoomMessages()` 加载真实留言
   - 新增：调用 `sendRoomMessage()` 发送留言
   - 新增：实时刷新机制（轮询或WebSocket）

3. **实现留言发送UI**：
   - 输入框：支持表情、@用户
   - 发送按钮：防抖、loading状态
   - 错误处理：网络失败重试

4. **测试验证**：
   - 留言列表能否正常显示
   - 发送留言能否成功
   - 实时刷新是否正常

**代码示例**：

```typescript
// src/api/messages.ts
import { get, post } from '@/utils/request';
import type { ApiResponse, PaginatedResponse } from '@/types/common';

export interface LiveRoomMessage {
  id: string;
  room_id: string;
  session_id: string | null;
  user_id: string;
  user_name: string;
  user_role: 'REGULAR' | 'MODERATOR' | 'ADMIN' | 'SUPERADMIN';
  content: string;
  reply_to: string | null;
  is_pinned: boolean;
  created_at: string;
  extra: any | null;
}

export interface SendMessagePayload {
  content: string;
  session_id?: string;
  reply_to?: string;
}

export const getRoomMessages = (
  roomId: string,
  params: { page?: number; size?: number; sort?: string } = {}
): Promise<ApiResponse<PaginatedResponse<LiveRoomMessage>>> => {
  return get(`/rooms/${roomId}/messages`, params);
};

export const sendRoomMessage = (
  roomId: string,
  data: SendMessagePayload
): Promise<ApiResponse<LiveRoomMessage>> => {
  return post(`/rooms/${roomId}/messages`, data);
};
```

---

### 阶段四：轮播图功能（可选，1-2天）

**目标**：实现首页顶部轮播图

**步骤**：
1. **创建Banners API**：
   - 文件：`src/api/homepage.ts`（已存在）
   - 新增：`getHomepageBanners()` 函数

2. **修改首页组件**：
   - 删除：Mock轮播图数据
   - 新增：调用 `getHomepageBanners()` 获取真实数据
   - 新增：点击跳转逻辑（根据 `link_type` 处理）

3. **测试验证**：
   - 轮播图能否正常显示
   - 点击跳转是否正确

---

### 阶段五：专家关注&收藏功能（可选，2-3天）

**目标**：实现播放页的关注专家和收藏直播功能

**步骤**：
1. **创建API模块**：
   - 文件：新建 `src/api/subscriptions.ts`
   - 实现：关注/取消关注专家
   
   - 文件：新建 `src/api/favorites.ts`
   - 实现：添加/取消收藏

2. **修改LiveView按钮**：
   - 关注按钮：调用API，显示loading状态
   - 收藏按钮：调用API，显示loading状态
   - 点赞按钮：（后端未实现，暂时保持Mock）

3. **测试验证**：
   - 关注/取消关注是否成功
   - 收藏/取消收藏是否成功

---

## ⚠️ 五、注意事项

### 5.1 API路径差异

**V6主文档 vs V2.1扩展文档**：

| 功能 | V6主文档路径 | V2.1扩展文档路径 | 使用建议 |
|------|-------------|-----------------|---------|
| 房间列表 | `/api/v1/rooms` | `/api/v1/homepage/rooms` | 首页用V2.1，管理页用V6 |
| Tab管理 | `/api/v1/admin/rooms/{id}/tabs` | 同左 | 使用V6路径 |
| 留言功能 | `/api/v1/rooms/{id}/messages` | 同左 | 使用V6路径 |

### 5.2 JWT认证字段

**重要**：V2.1文档修改了JWT字段名称

```typescript
// ❌ 旧代码（JWT标准）
const userId = payload.get("sub");

// ✅ 新代码（V2.1约定）
const userId = payload.get("user_id");
```

**原因**：保持代码语义清晰，与用户服务的 `public_id` 字段对应

### 5.3 数据库字段类型

**user_id 字段类型**：
- 不是 `BIGINT`（自增ID）
- 是 `UUID`（公开ID）
- 对应 `users.public_id` 字段

### 5.4 响应格式兼容性

**后端可能返回的格式**：

```typescript
// 格式1：标准格式
{
  "code": 200,
  "message": "success",
  "data": { ... }
}

// 格式2：嵌套格式
{
  "code": 200,
  "message": "success",
  "data": {
    "data": { ... }  // 注意：data嵌套
  }
}

// 兼容性代码
const session = 
  (response as any).data?.data ||  // 嵌套格式
  (response as any).data ||        // 标准格式
  response;                        // 直接返回
```

---

## 📊 六、优先级总结

| 优先级 | 功能模块 | 工作量 | 影响范围 | 建议时间 |
|-------|---------|-------|---------|---------|
| 🔴 P0 | 首页卡片升级 | 1-2天 | 首页体验 | 立即开始 |
| 🔴 P0 | 播放页Tab升级 | 2-3天 | 播放页体验 | 第2周 |
| 🟡 P1 | 聊天留言功能 | 3-4天 | 互动体验 | 第2-3周 |
| 🟡 P1 | 专家信息优化 | 0.5天 | 信息完整性 | 随时 |
| 🟢 P2 | 轮播图功能 | 1-2天 | 首页美观度 | 第4周（可选） |
| 🟢 P2 | 关注&收藏功能 | 2-3天 | 用户粘性 | 第4周（可选） |

**总计**：核心功能（P0+P1）约 **7-10天** 工作量

---

## 🎯 七、快速开始建议

### 第一步：验证后端API可用性（0.5天）

```bash
# 测试首页直播列表API
curl -X GET "http://124.220.235.226:8000/api/v1/homepage/rooms?page=1&size=10"

# 测试房间详情API（验证tabs字段）
curl -X GET "http://124.220.235.226:8000/api/v1/rooms/{真实的room_id}"

# 测试场次详情API（验证expert字段）
curl -X GET "http://124.220.235.226:8000/api/v1/sessions/{真实的session_id}"
```

### 第二步：升级首页卡片（1天）

**单文件修改**：
```typescript
// src/pages/app/tabbar/home/index.vue

// 修改import
- import { getRoomList } from '@/api/room';
+ import { getHomepageRooms } from '@/api/homepage';

// 修改loadRooms函数
async function loadRooms(params: { page: number; size: number }): Promise<{ items: HomepageRoomItem[]; total: number }> {
  try {
-   const res = await getRoomList({ page: params.page, size: params.size });
+   const res = await getHomepageRooms({ 
+     page: params.page, 
+     size: params.size,
+     sort: 'heat:desc'
+   });
    
    const items = res.data?.items || [];
    console.log('[Home] ✅ 使用首页专用API，数量:', items.length);
    
-   // 转换 Room → HomepageRoomItem（不需要了，API直接返回）
-   return { ... };
+   return {
+     items: items,
+     total: res.data?.total || 0
+   };
  } catch (error) {
    console.error('[Home] ❌ 加载房间列表失败:', error);
    return { items: [], total: 0 };
  }
}
```

### 第三步：升级播放页Tab（2天）

**创建API文件** → **修改LiveView组件** → **测试验证**

具体步骤见"阶段二：播放页Tab升级"

---

## 📞 总结

### 核心要点
1. **首页卡片**：使用 `GET /api/v1/homepage/rooms`（包含实时状态+专家信息）
2. **播放页Tab**：从 `GET /api/v1/rooms/{id}` 的 `tabs` 字段动态加载
3. **聊天留言**：使用 `GET /api/v1/rooms/{id}/messages` 和 `POST /api/v1/rooms/{id}/messages`
4. **轮播图**：使用 `GET /api/v1/homepage/banners`（需要先实现API）
5. **关注&收藏**：使用V2.1扩展文档的用户偏好API（可选）

### API文档位置
- **V6主文档**：`docs/直播核心功能设计文档_v6_深度融合最终版.md`
  - Section 8：API接口规范
  - Section 1：最终路由表
- **V2.1扩展文档**：`docs/直播核心功能设计文档_v6_后端新增api接口和模块设计文档-v2.md`
  - Section 4.13：Homepage模块API
  - Section 4.7：User Subscriptions API
  - Section 4.6：User Favorites API

### 建议顺序
1. ✅ **首页卡片**（最快见效）
2. ✅ **播放页Tab**（核心体验）
3. ✅ **聊天留言**（互动功能）
4. ⏳ 轮播图、关注、收藏（锦上添花）

**预计总工作量**：核心功能 7-10 天，完整功能 10-15 天
