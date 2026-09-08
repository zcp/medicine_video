# 直播间留言（Room Messages）—— 前端可落地实现文档

> **版本**: V1.6  
> **日期**: 2026-09-04  
> **状态**: ✅ V1.6 已落地（讨论列表加载状态机 + 乐观发送；对齐后端 V3 快照）  
> **后端对齐**: 《07-直播间留言-后端设计文档.md》V1.1 + 《07-直播间留言-V3-用户昵称头像快照增量设计文档.md》V3.0  
> **技术栈**: uni-app + Vue 3 + TypeScript + Pinia  
> **平台**: 微信小程序  
> **后端表**: `room_messages`（展示字段来自 `extra` 快照，非跨库 JOIN）

---

## 一、功能概述

直播间留言是直播间详情页内的互动功能，用户可以在直播间内发送留言并查看他人留言。前端需要实现：

1. **用户端**：留言列表展示（嵌入直播间详情页 Tab）+ 发送留言 + 删除自己的留言
2. **管理端**：全局留言查询、统一搜索框（覆盖全部筛选维度）、单条/批量删除、清空指定直播间留言

后端共提供 **6 个 REST API 端点**（用户端 3 + 管理端 3），功能边界如下：

| 类别 | 支持 | 不支持（P2 或未设计） |
|------|------|----------------------|
| 用户端 | 列表查询（分页）、发送留言、删除留言（物理删除） | 编辑留言、置顶、审核、管理员回复 |
| 管理端 | 全局留言列表、统一搜索框筛选、批量删除（≤200条/次）、清空直播间 | 敏感词过滤 UI、留言举报 |
| 增强 | 后端已实现 WebSocket 推送、Redis 缓存、5秒限流 | 前端 WebSocket 订阅（可选，暂未接入） |

**权限规则**：

- 管理员（`role=admin`）可删除任意用户的留言，可访问全部管理端接口
- 普通用户只能删除自己的留言（后端返回 `403` + `code=3002`）
- 非 admin 访问管理端接口返回 `403` + `code=3003`
- 列表查询公开可访问（无需 JWT 也可查看，有 JWT 则识别用户身份）

**业务错误码**（与后端 §8 一致）：

| 错误码 | 说明 | 前端处理 |
|--------|------|----------|
| `2001` | 资源不存在 | Toast「资源不存在」 |
| `2004` | 业务逻辑错误（限流/直播间已关闭） | Toast 展示后端 message |
| `3001` | 未授权 | 引导登录 |
| `3002` | 无权删除他人留言 | Toast「只能删除自己的留言」 |
| `3003` | 非管理员访问管理端 | Toast「权限不足：仅管理员可执行此操作」 |
| `4001` | 参数校验失败 | Toast 展示校验提示 |

---

## 二、目录结构

```
src/
├── api/
│   └── roomMessage.ts              # 留言 API 封装（用户端3 + 管理端3）
├── types/
│   └── roomMessage.ts              # 留言类型定义 + 错误码映射（含 V3 user / user_display_name）
├── utils/
│   └── roomMessageNormalize.ts     # V3：发送者昵称/头像归一化
├── config/
│   └── api.ts                      # API_PATHS.MESSAGE 统一路径配置
├── pages/
│   ├── live/
│   │   └── LiveView.vue            # 用户端留言区（已集成在 Tab 中）
│   └── admin/
│       └── roomMessage/
│           └── RoomMessageList.vue  # 管理端全局留言列表
└── components/
    └── MessageItem.vue              # 单条留言组件
```

---

## 三、类型定义

### 3.1 后端 DDL 对应关系

| 列名 | 类型 | 约束 | TypeScript 类型 |
|---|---|---|---|
| `id` | UUID | PK | `string` |
| `room_id` | UUID | FK CASCADE | `string` |
| `user_id` | UUID | FK CASCADE | `string` |
| `content` | VARCHAR(500) | NOT NULL | `string` |
| `created_at` | TIMESTAMPTZ | 自动 | `string` |

**零偏差说明**：

- 后端不存在 `updated_at`、`status`、`pinned`、`reply` 等字段
- 删除策略为**物理删除**（非软删除）
- **V3 展示契约**（见《07-直播间留言-V3-用户昵称头像快照增量设计文档》）：
  - 主字段：嵌套 `user: { nickname, avatar_url }`（来自发送时写入的 `extra` 快照，**不是** JOIN `users`）
  - 兼容字段：顶层保留 `user_display_name`（与 `user.nickname` 同源，旧客户端可继续读）
  - `user` / `user_display_name` 均可为 `null`（历史留言无快照、或发帖时 JWT 无展示字段）
  - **快照语义**：展示发送当时的昵称/头像；用户改资料不影响历史留言
- 管理端额外字段：`room_title`、`user_nickname`、`user_role`、`ip_address`（可选）
- 前端**禁止**假设可跨库 JOIN 实时查用户；列表侧只消费响应里的快照字段

### 3.2 类型文件

类型已定义在 `src/types/roomMessage.ts` 中，**禁止重复定义**。

```typescript
// src/types/roomMessage.ts（已有，以下为最终确认版）

/** 留言用户信息（对应后端 UserInfo Schema） */
export interface MessageUserInfo {
  nickname?: string | null
  avatar_url?: string | null
}

/** 留言项（对应后端 LiveRoomMessageItem + V3 快照字段） */
export interface RoomMessageItem {
  id: string
  room_id: string
  user_id: string
  content: string
  created_at: string
  /** V3：发送时快照组装；历史无快照时可为 null */
  user?: MessageUserInfo | null
  /** V3：兼容旧字段，与 user.nickname 同源，可与 user 同时为 null */
  user_display_name?: string | null
  user_role?: string | null
}

/** 发送留言请求（对应后端 LiveRoomMessageCreate Schema） */
export interface RoomMessageCreate {
  content: string  // 1-500 字符，后端 strip 后校验非空
}

/** 用户端留言查询参数（GET /rooms/{roomId}/messages） */
export interface RoomMessageQueryParams {
  page?: number       // 默认 1
  /** 后端实际 Query 名（路由表）；封装层可兼传 page_size 兼容旧文档 */
  size?: number       // 默认 20，最大 100
  page_size?: number  // 兼容别名，与 size 同义
  // 注意：后端无 order 参数，固定 created_at DESC
}

/** 用户端留言分页结果（对应后端 MessagePageResult） */
export interface RoomMessagePageResult {
  items: RoomMessageItem[]
  total: number
  page: number
  page_size: number
}

// ─── 管理端类型 ─────────────────────────────────

/** 管理端全局留言查询参数（对应后端 AdminMessageQueryParams） */
export interface AdminMessageQueryParams {
  room_id?: string
  user_id?: string
  keyword?: string       // 内容模糊搜索，max 100 字符
  start_time?: string    // ISO 8601
  end_time?: string      // ISO 8601
  page?: number
  page_size?: number     // 默认 20，最大 100
}

/** 批量删除请求（对应后端 BatchDeleteRequest，1-200 条） */
export interface BatchDeleteRequest {
  message_ids: string[]
}

/** 管理端留言条目（对应后端 AdminMessageItem） */
export interface AdminMessageItem extends RoomMessageItem {
  room_title?: string | null
  user_nickname?: string | null
  user_role?: string | null
  ip_address?: string | null
}

/** 管理端筛选摘要 */
export interface AdminMessageFilterSummary {
  keyword?: string
  room_count?: number
  user_count?: number
}

/** 管理端留言分页结果（对应后端 AdminMessagePageResult） */
export interface AdminMessagePageResult {
  items: AdminMessageItem[]
  total: number
  page: number
  page_size: number
  filter_summary?: AdminMessageFilterSummary | null
}

/** 批量删除响应 data */
export interface BatchDeleteResult {
  deleted_count: number
  failed_count: number
}

/** 清空直播间留言响应 data */
export interface ClearRoomMessagesResult {
  deleted_count: number
}

/** 错误码常量 + getRoomMessageErrorMessage() 见 src/types/roomMessage.ts */
```

---

## 四、API 封装

### 4.1 留言 API（`src/api/roomMessage.ts`）

所有 API 路径必须使用 `API_PATHS.MESSAGE`，禁止硬编码路径。

```typescript
// src/api/roomMessage.ts（已有，以下为最终确认版）

import { request } from '@/utils/request'
import { API_PATHS } from '@/config/api'
import type { ApiResponse } from '@/types/common'
import type {
  RoomMessageItem,
  RoomMessageCreate,
  RoomMessageQueryParams,
  RoomMessagePageResult,
  AdminMessageQueryParams,
  AdminMessagePageResult,
  BatchDeleteRequest,
  BatchDeleteResult,
  ClearRoomMessagesResult
} from '@/types/roomMessage'

// ─── 用户端（3） ─────────────────────────────────

/** GET /api/v1/rooms/{roomId}/messages — 公开/可选 JWT，分页，created_at DESC */
export const getRoomMessages = (
  roomId: string,
  params?: RoomMessageQueryParams
): Promise<ApiResponse<RoomMessagePageResult>> => {
  return request.get(API_PATHS.MESSAGE.ROOM_MESSAGES(roomId), {
    data: params,
    auth: false,
    showError: false
  })
}

/** POST /api/v1/rooms/{roomId}/messages — JWT，限流 5秒/条（code=2004） */
export const sendRoomMessage = (
  roomId: string,
  data: RoomMessageCreate
): Promise<ApiResponse<RoomMessageItem>> => {
  return request.post(API_PATHS.MESSAGE.ROOM_MESSAGES(roomId), data, {
    loading: true,
    loadingText: '发送中...',
    showError: false  // 由页面层调用 getRoomMessageErrorMessage 处理
  })
}

/** DELETE /api/v1/rooms/{roomId}/messages/{messageId} — JWT，物理删除 */
export const deleteMessage = (
  roomId: string,
  messageId: string
): Promise<ApiResponse<null>> => {
  return request.delete(API_PATHS.MESSAGE.MESSAGE_DETAIL(roomId, messageId), {
    loading: true,
    loadingText: '删除中...',
    showError: false
  })
}

// ─── 管理端（3，仅 admin） ─────────────────────────

/** GET /api/v1/admin/messages — JWT + admin 角色 */
export const getAdminMessages = (
  params?: AdminMessageQueryParams
): Promise<ApiResponse<AdminMessagePageResult>> => {
  return request.get(API_PATHS.MESSAGE.ADMIN_LIST, {
    data: params,
    showError: false
  })
}

/** POST /api/v1/admin/messages/batch-delete — JWT + admin，最多 200 条/次 */
export const batchDeleteMessages = (
  data: BatchDeleteRequest
): Promise<ApiResponse<BatchDeleteResult>> => {
  return request.post(API_PATHS.MESSAGE.ADMIN_BATCH_DELETE, data, {
    loading: true,
    loadingText: '删除中...',
    showError: false
  })
}

/** DELETE /api/v1/admin/rooms/{roomId}/messages — JWT + admin，清空该直播间全部留言 */
export const clearRoomMessages = (
  roomId: string
): Promise<ApiResponse<ClearRoomMessagesResult>> => {
  return request.delete(API_PATHS.MESSAGE.ADMIN_CLEAR_ROOM(roomId), {
    loading: true,
    loadingText: '清空中...',
    showError: false
  })
}
```

---

## 五、config/api.ts 路径配置

路径已定义在 `src/config/api.ts` 的 `MESSAGE` 模块中，**禁止重复定义**。

```typescript
// src/config/api.ts 中的 MESSAGE 模块（已有）

MESSAGE: {
  // 用户端
  ROOM_MESSAGES: (roomId: string) => `/rooms/${roomId}/messages`,
  MESSAGE_DETAIL: (roomId: string, messageId: string) =>
    `/rooms/${roomId}/messages/${messageId}`,
  // 管理端（§3.2）
  ADMIN_LIST: '/admin/messages',
  ADMIN_BATCH_DELETE: '/admin/messages/batch-delete',
  ADMIN_CLEAR_ROOM: (roomId: string) => `/admin/rooms/${roomId}/messages`
}
```

| 端点 | HTTP 方法 | API_PATHS 调用 | 权限 |
|---|---|---|---|
| 留言列表 | GET | `MESSAGE.ROOM_MESSAGES(roomId)` | 公开/JWT |
| 发送留言 | POST | `MESSAGE.ROOM_MESSAGES(roomId)` | JWT |
| 删除留言 | DELETE | `MESSAGE.MESSAGE_DETAIL(roomId, messageId)` | JWT（admin 可删任意，普通用户仅自己） |
| 管理端全局列表 | GET | `MESSAGE.ADMIN_LIST` | JWT + admin |
| 管理端批量删除 | POST | `MESSAGE.ADMIN_BATCH_DELETE` | JWT + admin |
| 管理端清空直播间 | DELETE | `MESSAGE.ADMIN_CLEAR_ROOM(roomId)` | JWT + admin |

---

## 六、管理端页面

### 6.1 RoomMessageList.vue — 管理端全局留言列表

管理端留言页面位于 `src/pages/admin/roomMessage/RoomMessageList.vue`，对齐后端 §3.2。

**核心功能**：

- 调用 `GET /api/v1/admin/messages` 全局查询（无需强制输入 roomId）
- **统一搜索框**：一个输入框覆盖当前全部筛选能力（留言内容、直播间 ID、用户 ID、时间范围）
- 展示 `filter_summary`（关键词、涉及直播间数、涉及用户数）
- 分页浏览（`page` / `page_size`）
- 单条删除（调用用户端 DELETE 接口）
- 多选 + 批量删除（`POST /admin/messages/batch-delete`，单次 ≤200 条）
- 清空指定直播间留言（搜索框解析出 `room_id` 后显示「清空该直播间」按钮）

**不支持的功能**（P2 或未设计）：

- 状态筛选（无 status 字段）
- 置顶/取消置顶（无 pin 端点）
- 审核操作（无 moderate 端点）
- 管理员回复（无 reply 端点）

#### 6.1.1 统一搜索框 UI

管理端顶部**只保留一个搜索框**（对齐 `TagList.vue` / `CategoryList.vue` 的 `search-box` 样式），不再拆成多个独立筛选输入框。

```vue
<view class="header-actions">
  <view class="search-box">
    <input
      v-model="searchKeyword"
      class="search-input"
      placeholder="搜索留言内容、直播间ID、用户ID、时间范围"
      @confirm="handleSearch"
    />
    <view v-if="searchKeyword" class="search-clear" @click="clearSearch">✕</view>
  </view>
</view>
```

**搜索框 placeholder 文案**（固定）：

```
搜索留言内容、直播间ID、用户ID、时间范围
```

placeholder 须写清当前可搜索的四个方面，与后端 `AdminMessageQueryParams` 一一对应：

| placeholder 描述项 | 后端参数 | 说明 |
|-------------------|----------|------|
| 留言内容 | `keyword` | 模糊匹配 `content`（ILIKE，max 100 字符） |
| 直播间ID | `room_id` | 精确匹配 UUID |
| 用户ID | `user_id` | 精确匹配 UUID |
| 时间范围 | `start_time` + `end_time` | ISO 8601 起止时间 |

**交互规则**：

- 用户按回车或点击「查询」触发搜索，页码重置为 1
- 点击清除按钮（✕）或「重置」清空搜索词并重新加载全量列表
- 空搜索词时加载全部留言（分页）
- 搜索无结果时展示「未找到匹配的留言」

#### 6.1.2 搜索词解析规则

前端通过 `parseSearchKeyword()` 将单一搜索框输入映射为后端查询参数：

```typescript
const UUID_RE =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i

const TIME_RANGE_RE =
  /^(\d{4}-\d{2}-\d{2}(?:[T\s]\d{2}:\d{2}(?::\d{2})?)?)\s*[~～至]\s*(\d{4}-\d{2}-\d{2}(?:[T\s]\d{2}:\d{2}(?::\d{2})?)?)$/i

interface ParsedSearchFilters {
  room_id?: string
  user_id?: string
  keyword?: string
  start_time?: string
  end_time?: string
}

/** 将统一搜索框输入解析为后端 AdminMessageQueryParams 筛选字段 */
function parseSearchKeyword(raw: string): ParsedSearchFilters {
  const input = raw.trim()
  if (!input) return {}

  // 1) 前缀语法（显式指定维度，优先级最高）
  const roomPrefix = input.match(/^(?:直播间|房间|room)[:：]\s*(\S+)/i)
  if (roomPrefix) return { room_id: roomPrefix[1].trim() }

  const userPrefix = input.match(/^(?:用户|user)[:：]\s*(\S+)/i)
  if (userPrefix) return { user_id: userPrefix[1].trim() }

  const timePrefix = input.match(/^(?:时间|time)[:：]\s*(.+)$/i)
  if (timePrefix) return parseTimeRange(timePrefix[1].trim())

  // 2) 时间范围：2026-01-01~2026-07-09 或 2026-01-01 至 2026-07-09
  const timeMatch = input.match(TIME_RANGE_RE)
  if (timeMatch) {
    return {
      start_time: normalizeIso(timeMatch[1]),
      end_time: normalizeIso(timeMatch[2])
    }
  }

  // 3) 纯 UUID：默认按直播间 ID 精确筛选（清空直播间等操作依赖 room_id）
  if (UUID_RE.test(input)) return { room_id: input }

  // 4) 其余文本：留言内容关键词模糊搜索
  return { keyword: input.slice(0, 100) }
}

function parseTimeRange(value: string): ParsedSearchFilters {
  const match = value.match(TIME_RANGE_RE)
  if (!match) return {}
  return {
    start_time: normalizeIso(match[1]),
    end_time: normalizeIso(match[2])
  }
}

/** 日期补全为 ISO 8601；仅日期时起始取 00:00:00，结束取 23:59:59 */
function normalizeIso(value: string): string {
  const trimmed = value.trim()
  if (/^\d{4}-\d{2}-\d{2}$/.test(trimmed)) {
    return new Date(`${trimmed}T00:00:00`).toISOString()
  }
  return new Date(trimmed).toISOString()
}
```

**解析优先级**（从高到低）：

1. 前缀语法：`直播间:uuid`、`用户:uuid`、`时间:2026-01-01~2026-07-09`
2. 裸时间范围：`2026-01-01~2026-07-09`
3. 裸 UUID：映射为 `room_id`（便于「清空该直播间」联动）
4. 普通文本：映射为 `keyword`（留言内容模糊搜索）

**搜索示例**：

| 用户输入 | 映射结果 |
|---------|---------|
| `广告` | `keyword=广告` |
| `550e8400-e29b-41d4-a716-446655440000` | `room_id=550e8400-...` |
| `用户:550e8400-e29b-41d4-a716-446655440000` | `user_id=550e8400-...` |
| `直播间:550e8400-e29b-41d4-a716-446655440000` | `room_id=550e8400-...` |
| `2026-01-01~2026-07-09` | `start_time` + `end_time` |
| `时间:2026-06-01 至 2026-06-30` | `start_time` + `end_time` |

> **说明**：裸 UUID 默认当作直播间 ID，是因为管理端「清空该直播间」操作需要 `room_id`。若需按用户 ID 精确筛选，请使用 `用户:` 前缀。

#### 6.1.3 关键逻辑片段

```typescript
import {
  getAdminMessages,
  deleteMessage,
  batchDeleteMessages,
  clearRoomMessages
} from '@/api/roomMessage'
import { getRoomMessageErrorMessage } from '@/types/roomMessage'

const searchKeyword = ref('')
const parsedFilters = ref<ParsedSearchFilters>({})

async function fetchData() {
  const params: AdminMessageQueryParams = {
    page: currentPage.value,
    page_size: pageSize.value,
    ...parsedFilters.value
  }

  const res = await getAdminMessages(params)
  tableData.value = res.data?.items || []
  total.value = res.data?.total || 0
  filterSummary.value = res.data?.filter_summary || null
}

function handleSearch() {
  parsedFilters.value = parseSearchKeyword(searchKeyword.value)
  currentPage.value = 1
  fetchData()
}

function clearSearch() {
  searchKeyword.value = ''
  parsedFilters.value = {}
  currentPage.value = 1
  filterSummary.value = null
  fetchData()
}

async function handleBatchDelete() {
  if (selectedIds.value.length === 0) return
  if (selectedIds.value.length > 200) {
    uni.showToast({ title: '单次最多删除200条', icon: 'none' })
    return
  }
  const res = await batchDeleteMessages({ message_ids: selectedIds.value })
  uni.showToast({
    title: `已删除 ${res.data?.deleted_count ?? 0} 条`,
    icon: 'success'
  })
  selectedIds.value = []
  fetchData()
}

async function handleClearRoom() {
  const roomId = parsedFilters.value.room_id?.trim()
  if (!roomId) return
  const res = await clearRoomMessages(roomId)
  uni.showToast({
    title: `已清空 ${res.data?.deleted_count ?? 0} 条留言`,
    icon: 'success'
  })
  fetchData()
}

/** 仅当搜索解析出 room_id 时显示「清空该直播间」 */
const canClearRoom = computed(() => Boolean(parsedFilters.value.room_id?.trim()))
```

**操作按钮区**（搜索框下方）：

| 按钮 | 显示条件 | 说明 |
|------|----------|------|
| 查询 | 始终 | 解析搜索词并刷新列表 |
| 重置 | 始终 | 等同 `clearSearch()` |
| 全选本页 / 取消全选 | 列表非空 | 批量删除前置 |
| 批量删除 (N) | 已勾选 ≥1 条 | 单次 ≤200 条 |
| 清空该直播间 | `canClearRoom === true` | 需搜索框解析出 `room_id` |

**操作说明文案**（`guide-panel`）：

```
操作说明：在搜索框输入留言内容、直播间ID、用户ID或时间范围后查询；勾选左侧复选框可批量删除；搜索直播间ID后可「清空该直播间」全部留言
```

**展示字段**：

| 字段 | 来源 | 展示方式 |
|------|------|----------|
| 用户昵称 | `user_nickname` 或 `user.nickname` | 主标题 |
| 用户角色 | `user_role` | 标签 |
| 留言内容 | `content` | 正文 |
| 直播间 | `room_title` 或 `room_id` | 元信息 |
| 用户 ID | `user_id` | 元信息 |
| 时间 | `created_at` | 相对时间 |

---

## 七、用户端页面/组件

用户端留言功能已集成在 `src/pages/live/LiveView.vue` 的留言 Tab 中。

### 7.0 发送者昵称/头像展示（V1.5，对齐后端 V3 快照）

> **后端依据**：《07-直播间留言-V3-用户昵称头像快照增量设计文档.md》V3.0  
> **背景**：users / live_core 分库，无法 JOIN；后端在发留言时把昵称+头像写入 `extra` 快照，响应组装嵌套 `user`，并保留 `user_display_name`。

#### 问题现象

直播间留言 Tab 能看到正文，但看不到具体人的昵称/头像（旧实现只写了 `extra.user_display_name`，无嵌套 `user`、无头像）。

#### 后端 V3 已落地（前端只消费，不改表）

```
登录/刷新 → JWT 含 nickname + avatar_url（可选）
     ↓
POST 留言 → extra = { user_display_name, avatar_url }
     ↓
GET / WS / Admin → 从 extra 组装 user: { nickname, avatar_url }
```

#### 响应契约（与 V3 §响应契约一致）

```json
{
  "id": "...",
  "content": "...",
  "created_at": "...",
  "user_role": "REGULAR",
  "user_display_name": "张医生",
  "user": {
    "nickname": "张医生",
    "avatar_url": "/uploads/avatars/xxx.jpg"
  }
}
```

| 字段 | 说明 | 前端处理 |
|------|------|----------|
| `user.nickname` | 主展示昵称（快照） | **优先** |
| `user.avatar_url` | 主展示头像（快照，可空） | **优先**；空则默认头像 |
| `user_display_name` | 兼容旧字段，与 nickname 同源 | `user` 缺失时回退 |
| `user` / `user_display_name` 为 null | 历史无快照或 JWT 当时无展示字段 | 昵称「匿名用户」；头像用默认图 |

**禁止**：前端列表批量调 users 接口补资料；禁止假设实时 JOIN；禁止因 `user===null` 隐藏整行头像/昵称区域。

#### 前端展示取值优先级（`normalizeRoomMessageItem`）

| 展示 | 优先级（非空优先） |
|------|-------------------|
| 昵称 | `user.nickname` → `user_display_name` →（可选，仅本人刚发且响应缺快照）`authStore.userInfo.nickname` → `"匿名用户"` |
| 头像 URL | `user.avatar_url` →（可选，仅本人刚发且响应缺快照）`authStore.userInfo.avatar_url` → **默认头像** `DEFAULT_CONFIG.DEFAULT_AVATAR` |

头像展示前统一：`normalizeImageUrl(resolveMediaUrl(url))`（相对路径 / http 兼容小程序）。

> V3 明确：头像为空时前端使用**默认头像**（非仅字母占位）。字母占位仅作为默认图加载失败时的二次回退。

#### MessageItem 展示规则

| 元素 | 规则 |
|------|------|
| 昵称 | 归一化后的昵称；本人额外「我」标签 |
| 头像 | 优先快照/默认图 `<image>`；`@error` 后再回退蓝底首字 |
| 快照语义 | 只展示发送当时信息，不因用户改资料刷新历史留言 |

#### 涉及文件（前端对接清单）

| # | 文件 | 变更 | 状态 |
|---|------|------|------|
| 1 | `src/types/roomMessage.ts` | 类型补 `user_display_name` / `user_role`（可选） | ✅ |
| 2 | `src/utils/roomMessageNormalize.ts` | 优先 `user.*`，回退 `user_display_name`；头像空→默认头像 | ✅ |
| 3 | `src/components/MessageItem.vue` | 消费归一化结果；媒体 URL；默认头像 | ✅ |
| 4 | `src/pages/live/LiveView.vue` | 列表/发送入库前归一化 | ✅ |
| 5 | `src/mock/modules/messages.ts` | Mock 对齐 V3：`user` + `user_display_name` | ✅ |
| 6 | `src/pages/admin/roomMessage/RoomMessageList.vue` | 昵称优先级与用户端一致 | ✅ |

#### 自测清单（对齐后端 V3 §自测 + 前端展示）

| # | 场景 | 期望 |
|---|---|---|
| 1 | GET 列表项含 `user.nickname` + `user.avatar_url` | 显示真实昵称与头像图 |
| 2 | 仅有 `user_display_name`、无嵌套 `user`（旧数据/旧响应） | 回退显示该昵称，非一律「匿名用户」 |
| 3 | `user` 与 `user_display_name` 均为 null（历史无 extra） | 昵称「匿名用户」+ **默认头像**，页面不报错 |
| 4 | `avatar_url` 为空但有昵称 | 显示昵称 + 默认头像 |
| 5 | `avatar_url` 为相对路径 `/uploads/...` | 经 `resolveMediaUrl` 后可显示或失败回退默认图 |
| 6 | 本人刚发送、响应已含 V3 `user` | 直接展示快照，无需再查 users |
| 7 | 管理端列表 | 昵称优先级与用户端一致 |

---

### 7.1 MessageItem.vue — 单条留言组件

```vue
<!--
 * MessageItem - 单条留言组件
 * @description 直播间留言列表中的单条消息展示
 * V1.5：对齐后端 V3 快照；优先 user.*，回退 user_display_name；头像空用默认图
 -->
<template>
  <view
    class="msg-item"
    :class="{ 'msg-item--own': isOwnMessage }"
    @longpress="handleLongPress"
  >
    <view class="msg-avatar">
      <image
        v-if="avatarSrc && !avatarBroken"
        class="msg-avatar__img"
        :src="avatarSrc"
        mode="aspectFill"
        @error="avatarBroken = true"
      />
      <text v-else class="msg-avatar__text">{{ avatarLetter }}</text>
    </view>

    <view class="msg-body">
      <view class="msg-header">
        <text class="msg-name">{{ displayName }}</text>
        <text v-if="isOwnMessage" class="msg-own-tag">我</text>
        <text class="msg-time">{{ formatTime(message.created_at) }}</text>
      </view>
      <text class="msg-content">{{ message.content }}</text>
    </view>
  </view>
</template>

<script setup lang="ts">
// displayName：user.nickname → user_display_name → 匿名用户
// avatarSrc：user.avatar_url → DEFAULT_AVATAR，再经 resolveMediaUrl / normalizeImageUrl
// ... 逻辑见 src/components/MessageItem.vue
</script>

<style lang="scss" scoped>
/* 留言区嵌入 LiveView Tab，背景为浅色 var(--color-surface)，禁止写白色正文 */
.msg-item {
  border-bottom: 1rpx solid var(--color-border);
}

.msg-name {
  color: var(--color-text-secondary);
}

.msg-time {
  color: var(--color-text-tertiary);
}

.msg-content {
  color: var(--color-text-primary);
}

/* 头像占位字母在蓝色渐变背景上，保留 #ffffff */
.msg-avatar__text {
  color: #ffffff;
}
</style>
```

**样式要点**：

- 留言区位于 `LiveView.vue` 的 `.tab-content` 内，背景为 `var(--color-surface)`（白色），**必须使用设计令牌深色文字**，不得使用 `rgba(255,255,255,*)` 作为正文/昵称/时间颜色
- 头像占位字母（`.msg-avatar__text`）位于蓝色渐变背景上，可保留 `#ffffff`
- 删除按钮使用危险色 `#ff4d4f`，与全局一致

### 7.2 LiveView.vue 中的留言集成逻辑

#### 体验钉（讨论 Tab）

| 项 | 口径 |
|----|------|
| 受众 | 直播间观众（含未登录只读） |
| 闭环 | 进「讨论」→ 看到历史 → 登录后发一条立刻上屏 → 可长按删自己的 |
| 首屏 | 讨论 Tab 激活且 `roomId` 就绪后加载最近一页；展示为聊天式 ASC（旧上新下） |
| 关键态 | 加载中文案；空列表引导；拉数失败 Toast；未登录底部提示去登录 |
| 非目标 | 本版不做 WebSocket；不做编辑/置顶/审核 |

留言区作为特殊 Tab（`tab_key = 'message'`，标题「讨论」）注入到直播间详情页功能性 Tab 列表末尾。

**加载触发（V1.6，必须同时满足）**：

1. 当前功能性 Tab 为讨论（`tab_key === 'message'`）
2. `roomId` 已就绪

实现要点：

- `watch(isMessageTabActive)`：进入讨论 Tab 时拉第一页（已有列表则 silent 刷新）
- `watch(roomId)`：换房或 `onLoad` 用场次详情覆盖标准 `room_id` 时先清空本地列表；**若仍在讨论 Tab 则立即补拉**（禁止只清空不拉）
- `messagesFetchSeq`：丢弃过期响应，避免快切 Tab / 换房串数据
- 禁止仅依赖 StickyTabPager 的 change 事件拉数（易漏）

**发送（乐观更新）**：先清空输入并插入 `local_*` 气泡 → POST → 用服务端项替换；失败回滚并恢复输入。全屏 `showLoading` 禁止用于发送。

```typescript
import { getRoomMessages, sendRoomMessage, deleteMessage } from '@/api/roomMessage'
import { getRoomMessageErrorMessage } from '@/types/roomMessage'

const messages = ref<RoomMessageItem[]>([])
const messagesPage = ref(1)
const messagesPageSize = ref(20)
const messageInputContent = ref('')
let messagesFetchSeq = 0

/** API 仍 DESC 分页；展示 ASC（聊天式旧上新下） */
const messagesSorted = computed(() =>
  [...messages.value]
    .filter((m) => !!m?.id)
    .sort(
      (a, b) =>
        new Date(a.created_at || 0).getTime() - new Date(b.created_at || 0).getTime()
    )
)

function pullMessagesWhenDiscussionReady(opts?: { silent?: boolean }) {
  if (!isMessageTabActive.value || !roomId.value) return
  messagesPage.value = 1
  fetchMessages(false, opts)
}

async function fetchMessages(append = false, opts?: { silent?: boolean }) {
  if (!roomId.value) return
  const seq = ++messagesFetchSeq
  const requestRoomId = roomId.value
  const res = await getRoomMessages(requestRoomId, {
    page: messagesPage.value,
    size: messagesPageSize.value
  })
  if (seq !== messagesFetchSeq || roomId.value !== requestRoomId) return
  const data = res.data
  const fetchedItems = normalizeRoomMessageItems(data?.items ?? [], messageAuthFallback())
  if (append) {
    // 去重 append
  } else {
    const pendingLocals = messages.value.filter((m) => String(m.id).startsWith('local_'))
    messages.value = [...fetchedItems, ...pendingLocals]
  }
  messagesTotal.value = data?.total ?? 0
}

// 发送：乐观 local_* → POST → splice 替换；失败回滚（详见 LiveView.vue）
```

### 7.3 发送限流（后端 P1）

后端已实现 Redis 限流：**每 5 秒最多 1 条**，超限返回 `code=2004`。

前端处理：

- `sendRoomMessage` 设置 `showError: false`，由 `handleSendMessage` 捕获错误
- 通过 `getRoomMessageErrorMessage(2004, err.message)` 展示后端返回的提示文案
- 可选增强：收到 2004 后禁用发送按钮 5 秒（当前未实现，依赖后端拦截）

### 7.4 WebSocket 实时推送（后端 P1，前端可选）

后端已实现 `WS /api/v1/ws/rooms/{roomId}/messages`，推送 `new_message` 事件。

**当前前端策略（V1.6）**：暂未接入 WebSocket。本人发送靠乐观更新即时上屏；历史靠进讨论 Tab / `roomId` 就绪后的 GET；其他用户新留言需重新进入讨论 Tab 或刷新页面才能看到。

**后续接入建议**：

```typescript
// 可选实现（P2 前端增强）
// 1. 进入留言 Tab 时 connectSocket
// 2. 监听 new_message 事件，去重后 append 到 messages（展示层再 ASC 排序）
// 3. 离开 Tab / 页面 onUnload 时 closeSocket
```

### 7.5 UI 样式规范（亮色 Tab 背景）

留言区作为 `LiveView.vue` 功能性 Tab 的一部分，容器背景与页面其他 Tab 一致，为**浅色**（`var(--color-surface)` / `#FFFFFF`）。样式必须引用 `src/common/uni.scss` 导出的 CSS 变量，**禁止**在留言列表区域硬编码白色文字。

| 元素 | 类名 | 颜色令牌 | 说明 |
|------|------|----------|------|
| Tab 内容区背景 | `.tab-content` | `var(--color-surface)` | 与直播间其他 Tab 一致 |
| 留言顶栏标题 | `.msg-board-title` | `var(--color-text-primary)` | 「全部留言 (N)」 |
| 顶栏/列表分隔线 | `.msg-board-header`、`.msg-item` | `var(--color-border)` | 浅色边框 |
| 留言正文 | `.msg-content` | `var(--color-text-primary)` | 主阅读内容 |
| 用户昵称 | `.msg-name` | `var(--color-text-secondary)` | 次要信息 |
| 发布时间 | `.msg-time` | `var(--color-text-tertiary)` | 辅助信息 |
| 操作提示 | `.msg-tip-text` | `var(--color-text-secondary)` | 「长按删除」等提示 |
| 字数统计 | `.msg-char-count-text` | `var(--color-text-tertiary)` | 输入框下方 0/500 |
| 输入框文字 | `.msg-input` | `var(--color-text-primary)` | 发送留言输入 |
| 空态/加载文案 | `.msg-empty-text` 等 | `var(--color-text-tertiary)` | 与页面其他空态一致 |
| 刷新/发送按钮文字 | `.msg-refresh-text`、`.msg-send-text` | `var(--color-primary)` / `#ffffff` | 主色描边按钮 / 主色实心按钮 |
| 头像占位字母 | `.msg-avatar__text` | `#ffffff` | **例外**：蓝色渐变头像背景上保留白色 |

**常见错误（已修复）**：

- ❌ `.msg-content { color: rgba(255, 255, 255, 0.9) }` — 白字叠白底，留言不可见
- ❌ `.msg-board-title { color: rgba(255, 255, 255, 0.75) }` — 顶栏标题不可见
- ✅ 统一改用 `var(--color-text-primary)` / `secondary` / `tertiary` 三级文字色

实现文件：

- `src/components/MessageItem.vue` — 单条留言颜色
- `src/pages/live/LiveView.vue` — 留言区顶栏、输入栏、提示文案颜色（`.message-board-tab` 区块）

---

## 八、对接清单

### 8.1 已与后端确认的事项

| # | 确认项 | 结论 |
|---|---|---|
| 1 | 留言发送频率限制 | 每 5 秒 1 条，超限 `code=2004`，前端 Toast 展示后端 message |
| 2 | 删除权限判断 | 前端根据 `authStore.isAdmin` 显示删除按钮；越权操作后端返回 3002/3003 |
| 3 | 分页默认值 | `page=1`，`size=20`（兼容 `page_size`），最大 100，与后端路由表一致 |

| 4 | 排序方向 | 后端固定 `created_at DESC`，**无 `order` 查询参数** |
| 5 | 嵌套 user 对象（V3 快照） | POST/GET/WS/Admin 从 `extra` 组装 `user: { nickname, avatar_url }`；保留 `user_display_name`；可为 null（历史无快照） |
| 6 | 管理端批量删除上限 | 200 条/次，超出返回 `422` + `code=4001` |
| 7 | 管理端权限 | 非 admin 访问管理端接口返回 `403` + `code=3003` |

### 8.2 前端已完成清单

| # | 文件 | 状态 | 说明 |
|---|---|---|---|
| 1 | `src/api/roomMessage.ts` | ✅ 已完成 | 6 个 API 封装（用户端3 + 管理端3） |
| 2 | `src/types/roomMessage.ts` | ✅ V1.5 | 补齐 `user_display_name` / `user_role` |
| 3 | `src/config/api.ts` | ✅ 已完成 | MESSAGE 模块 6 条路径 |
| 4 | `src/utils/roomMessageNormalize.ts` | ✅ V1.5 | 对齐 V3：`user.*` → `user_display_name` → 默认头像 |
| 5 | `src/pages/live/LiveView.vue` | ✅ V1.6 | 讨论加载状态机 + 乐观发送 + 归一化 |

| 6 | `src/components/MessageItem.vue` | ✅ V1.5 | 昵称/头像展示 + 默认头像 |
| 7 | `src/pages/admin/roomMessage/RoomMessageList.vue` | ✅ V1.5 | 管理端昵称优先级对齐 |

### 8.3 不实现的功能清单

以下功能在后端未设计或属 P2，前端不得自行扩展：

| 功能 | 原因 |
|---|---|
| 编辑留言 | 后端无 PATCH 端点 |
| 置顶/取消置顶 | 后端无 pin 端点，DDL 无 pinned 字段 |
| 审核（隐藏/显示） | 后端无 moderate 端点，DDL 无 status 字段 |
| 管理员回复 | 后端无 reply 端点 |
| 单条留言详情 | 后端无 `GET /messages/{messageId}` 端点 |
| WebSocket 实时推送 | 后端已实现，前端暂未接入（可选 P2 增强） |
| 敏感词过滤 UI | 后端 P2 未实现 |
| 留言举报 | 后端 P2 未实现 |

---

## 九、API 链路总结

```
用户端接口（公开/JWT）:
┌──────────────────────────────────────────────────────────────────────┐
│  GET    /rooms/{roomId}/messages                获取留言列表          │
│  POST   /rooms/{roomId}/messages                发送留言（限流+WS推送）│
│  DELETE /rooms/{roomId}/messages/{messageId}    删除留言（物理删除）  │
└──────────────────────────────────────────────────────────────────────┘

管理端接口（JWT + admin）:
┌──────────────────────────────────────────────────────────────────────┐
│  GET    /admin/messages                         全局留言列表 + 筛选   │
│  POST   /admin/messages/batch-delete            批量删除（≤200条）    │
│  DELETE /admin/rooms/{roomId}/messages          清空指定直播间留言    │
└──────────────────────────────────────────────────────────────────────┘

WebSocket（后端已实现，前端可选）:
┌──────────────────────────────────────────────────────────────────────┐
│  WS     /ws/rooms/{roomId}/messages             new_message 事件推送  │
└──────────────────────────────────────────────────────────────────────┘

前端消费方:
┌──────────────────────────────────────────────────────────────────────┐
│  src/api/roomMessage.ts              → 6 个 API 封装                  │
│  src/pages/live/LiveView.vue         → 用户端留言 Tab                 │
│  src/components/MessageItem.vue      → 单条留言展示                   │
│  src/pages/admin/roomMessage/        → 管理端全局留言管理             │
│    RoomMessageList.vue                                                │
└──────────────────────────────────────────────────────────────────────┘

数据流:
  用户发送讨论 → POST /rooms/{roomId}/messages → 乐观 local_* 上屏 → 成功后替换为服务端项
  用户查看讨论 → 讨论 Tab 激活且 roomId 就绪 → GET ?page=1&size=20 → 展示 ASC；↑ 加载更早翻页
  删除讨论     → DELETE /rooms/{roomId}/messages/{messageId} → 本地 filter
  管理端查询   → GET  /admin/messages?keyword=...&room_id=... → 统一搜索框解析后分页展示
  管理端批量删 → POST /admin/messages/batch-delete → 刷新列表
  管理端清空   → DELETE /admin/rooms/{roomId}/messages → 刷新列表
```

---

## 十、文档修订历史

| 版本 | 日期 | 修订内容 | 作者 |
|------|------|----------|------|
| V1.0 | 2026-06-07 | 初始版本（用户端 3 API） | Claude |
| V1.1 | 2026-07-04 | 对齐后端 V1.1：管理端 3 API、Admin 类型、批量删除、清空直播间、错误码、限流说明；移除过时的「不支持 batch-delete / admin 列表」描述 | Agent |
| V1.2 | 2026-07-04 | 修复留言区白字叠白底不可见问题；新增 §7.5 UI 样式规范，明确亮色 Tab 背景下须使用设计令牌文字色 | Agent |
| V1.3 | 2026-07-09 | §6.1 管理端改为**统一搜索框**设计：placeholder 写明可搜「留言内容、直播间ID、用户ID、时间范围」；新增 `parseSearchKeyword()` 解析规则与示例；`RoomMessageList.vue` 标记为待改造 | Agent |
| V1.4 | 2026-07-16 | （中间稿，已由 V1.5 取代）曾按 JOIN 假设补展示；**不正确**，勿再按 V1.4 实现 | Agent |
| V1.5 | 2026-07-16 | **对齐后端 V3 快照**：§7.0 重写为 `user.*` 优先 + `user_display_name` 回退 + 默认头像；明确分库无 JOIN；类型补 `user_display_name`；对接清单与自测对齐《07-…-V3-用户昵称头像快照…》 | Agent |
| V1.6 | 2026-09-04 | **讨论加载状态机**：§7.2 重写为「讨论 Tab 激活 ∧ roomId 就绪」联合触发 + `messagesFetchSeq` 丢弃过期响应；发送改为乐观更新；Query 对齐后端 `size`；展示 ASC；体验钉五问写入 §7.2 | Agent |

---

**文档结束** ✅
