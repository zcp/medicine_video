# 创建直播间（Room + Session）—— 前端可落地实现文档

> **版本**：v2.3（2026-09-04）
> **技术栈**：uni-app + Vue 3 + TypeScript + Pinia
> **平台**：微信小程序（多端兼容）
> **零偏差**：所有类型、路径、端点严格对齐后端设计文档与实际代码
> **说明**：§6.1.1 已拍板 **B 细化**（对齐后端：外链可直存、本地走上传）

---

## 一、功能概述

直播间创建是平台核心业务流程，涉及 **Room（容器）** 和 **Session（场次）** 两个实体的联合创建。前端需实现：

### 1.1 用户端
1. **创建直播间**：一次操作同时创建 Room + Session，支持三种模式（预告/直播/回放）
2. **编辑直播间**：修改已有 Room 和 Session 信息
3. **我的直播列表**：查看自己创建的所有直播间，支持编辑/删除
4. **直播间详情/播放**：视频播放（live-player/video）、Tab展示、留言互动

### 1.2 管理端
5. **Tab 管理**：为直播间配置自定义内容板块（详见《Live-Saas-Wechat-06-直播间Tab管理-前端设计文档-v1.0》）
6. **标签管理**：为场次设置标签（详见《Live-Saas-Wechat-02-标签管理-前端设计文档-v1.0》）
7. **专家/品牌关联**：为直播间绑定专家和品牌

**后端数据表**：

| 表名 | 说明 | 主键 | 关键字段 |
|------|------|------|----------|
| `live_rooms` | 直播间（容器） | `id` UUID | `title`, `description`, `summary`, `category_id`, `cover_url`, `record_by_default` |
| `live_sessions` | 直播场次 | `id` UUID | `room_id` FK, `summary`, `featured_expert_id`, `start_time`, `status`, `playback_url`, `stream_url` |
| `session_tags` | 场次-标签关联 | 复合主键 | `session_id` FK, `tag_id` FK |
| `live_room_tabs` | 直播间Tab | `id` UUID | `room_id` FK, `tab_key`, `title`, `content_type`, `text_content`, `image_url`, `sort_order`, `is_active` |

**软删除策略**：`live_rooms`、`live_sessions` 使用状态字段（非物理删除）；`session_tags` 使用物理删除；`live_room_tabs` 使用 `is_active` 软删除。

### 1.3 核心概念

- **Room = 容器**：承载标题/简介/封面/分类/Tab/品牌等持久信息
- **Session = 场次**：承载开播时间、回放地址、标签、专家等场次级信息
- 每次"创建直播间"必须 **同时创建 Room + 至少一条 Session**
- 成功后跳转播放页携带 `roomId + sessionId`

### 1.4 API 端点清单

#### Room 管理（8个端点）

| # | 方法 | 路径 | 权限 | 说明 |
|---|------|------|------|------|
| 1 | GET | `/rooms` | 公开 | 房间列表（分页+分类+排序） |
| 2 | GET | `/rooms/{roomId}` | 公开 | 房间详情（含tabs） |
| 3 | POST | `/rooms` | JWT | 创建房间 |
| 4 | PATCH | `/rooms/{roomId}` | JWT | 更新房间 |
| 5 | DELETE | `/rooms/{roomId}` | JWT | 删除房间 |
| 6 | POST | `/rooms/{roomId}/cover` | JWT | 上传封面 |
| 7 | GET | `/homepage/rooms` | 公开 | 首页房间列表 |
| 8 | GET | `/users/me/rooms` | JWT | 我的房间列表 |

#### Session 管理（8个端点）

| # | 方法 | 路径 | 权限 | 说明 |
|---|------|------|------|------|
| 1 | GET | `/sessions` | 公开 | 场次列表（分页+筛选） |
| 2 | GET | `/sessions/{sessionId}` | 公开 | 场次详情 |
| 3 | POST | `/rooms/{roomId}/sessions` | JWT | 创建场次 |
| 4 | PATCH | `/sessions/{sessionId}` | JWT | 更新场次 |
| 5 | DELETE | `/sessions/{sessionId}` | JWT | 删除场次 |
| 6 | POST | `/rooms/{roomId}/sessions/import` | JWT | 导入回放场次 |
| 7 | POST | `/sessions/{sessionId}/start` | JWT | 开播（状态→live） |
| 8 | GET | `/sessions/{sessionId}/statistics` | JWT | 场次统计 |

#### 关联管理（6个端点）

| # | 方法 | 路径 | 权限 | 说明 |
|---|------|------|------|------|
| 1 | GET | `/rooms/{roomId}/tabs` | 公开 | 房间Tab列表 |
| 2 | GET | `/rooms/{roomId}/brands` | 公开 | 房间品牌列表 |
| 3 | GET | `/rooms/{roomId}/experts` | 公开 | 房间专家列表 |
| 4 | POST | `/admin/rooms/{roomId}/brands` | JWT+Admin | 设置房间品牌 |
| 5 | GET | `/content/sessions/{sessionId}/tags` | 公开 | 场次标签列表 |
| 6 | POST | `/content/sessions/{sessionId}/tags` | JWT+Admin | 设置场次标签 |

---

## 二、目录结构

```
src/
├── types/
│   ├── room.ts                    # 房间类型定义（Room, LiveRoomDetail, CreateRoomRequest, Tab 等）
│   ├── session.ts                 # 场次类型定义（SessionDetail, CreateSessionRequest 等）
│   └── common.ts                  # 通用类型（ApiResponse, PaginatedResponse, BaseEntity 等）
├── api/
│   ├── room.ts                    # 房间 API 封装（22个函数）
│   ├── session.ts                 # 场次 API 封装（12个函数）
│   ├── tabs.ts                    # Tab 管理端 API 封装（7个函数）
│   ├── room-tabs.ts               # Tab 公开 API 封装
│   └── tags.ts                    # 标签 API 封装（含场次标签关联）
├── config/
│   └── api.ts                     # API_PATHS 统一路径配置（ROOM/SESSION/ADMIN/TAGS 模块）
├── store/
│   ├── room.ts                    # 房间 Pinia 状态管理（LRU 缓存 50 条）
│   └── session.ts                 # 场次 Pinia 状态管理（LRU 缓存 30 条）
├── pages/
│   ├── live/
│   │   ├── CreateLive.vue         # 创建/编辑直播间页（三种模式：预告/直播/回放）
│   │   └── LiveView.vue           # 直播间详情/播放页（视频播放+Tab+留言）
│   ├── my-live/
│   │   └── MyLive.vue             # 我的直播列表页
│   └── admin/
│       └── roomTab/
│           ├── RoomTabManager.vue  # 管理端Tab管理组件
│           └── TabEditDialog.vue   # Tab新增/编辑弹窗
├── components/
│   └── common/
│       └── LiveCard.vue            # 首页直播卡片组件
└── composables/
    └── useCategory.ts              # 分类组合函数
```

---

## 三、类型定义

### 3.1 通用类型（`src/types/common.ts`）

```typescript
/**
 * 统一API响应结构
 */
export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T | null
  timestamp: string
}

/**
 * 分页响应格式
 */
export interface PaginatedResponse<T = any> {
  total: number
  page: number
  size: number
  items: T[]
}

/**
 * 基础实体接口
 */
export interface BaseEntity {
  id: string
  createdAt: string
  updatedAt: string
}

/**
 * 统计数据基础
 */
export interface StatsData {
  views: number
  likes: number
  shares: number
  comments: number
  collections: number
  duration?: number
}
```

### 3.2 房间类型（`src/types/room.ts`）

```typescript
import { BaseEntity, StatsData } from './common'

/**
 * 房间状态
 */
export type RoomStatus = 'scheduled' | 'live' | 'ended' | 'cancelled'

/**
 * 房间类型
 */
export type RoomType = 'public' | 'private' | 'premium' | 'vip'

/**
 * 分类简要信息
 */
export interface CategoryBrief {
  id: string
  name: string
  icon?: string
  slug?: string
}

/**
 * 直播房间信息（主接口返回结构）
 * 对应后端 DDL: live_rooms 表
 */
export interface Room extends BaseEntity {
  title: string
  description: string
  summary?: string
  category?: CategoryBrief
  category_id?: string
  coverImage: string
  status: RoomStatus
  type: RoomType
  expertId: string
  expertInfo: {
    id: string
    name: string
    avatar: string
    title: string
    hospital: string
    department: string
    isVerified: boolean
  }
  departmentId: string
  departmentName: string
  tags: string[]
  scheduledStartAt: string
  scheduledEndAt: string
  actualStartAt?: string
  actualEndAt?: string
  password?: string
  maxViewers: number
  currentViewers: number
  allowComments: boolean
  allowInteraction: boolean
  isRecorded: boolean
  recordUrl?: string
  streamUrl?: string
  playUrl?: string
  stats: RoomStats
}

/**
 * 房间统计数据
 */
export interface RoomStats extends StatsData {
  totalViewers: number
  peakViewers: number
  avgWatchTime: number
  interactionCount: number
  danmuCount: number
}

/**
 * 创建房间请求（对应后端 CreateRoomRequest Schema）
 */
export interface CreateRoomRequest {
  /** 房间标题（必填） */
  title: string
  /** 房间描述（必填） */
  description: string
  /** 直播间简介摘要（可选，用于卡片展示） */
  summary?: string
  /** 分类ID（可选） */
  category_id?: string
  /** 是否默认录制（可选） */
  record_by_default?: boolean
}

/**
 * 更新房间请求（全部可选）
 */
export type UpdateRoomRequest = Partial<CreateRoomRequest>

/**
 * Tab数据结构（对应后端 LiveRoomTabItem Schema）
 * DDL: live_room_tabs 表
 */
export interface Tab {
  id: string
  room_id: string
  tab_key: string
  title: string
  content_type: 'text' | 'image' | 'mixed'
  text_content?: string | null
  image_url?: string | null
  sort_order: number
  is_active: boolean
  created_at: string
  updated_at: string
}

/** 兼容别名 */
export type RoomTab = Tab

/**
 * 直播房间详情（扩展信息）
 * GET /api/v1/rooms/{roomId} 返回
 */
export interface LiveRoomDetail extends Room {
  tabs: Tab[]
  hostDetail: {
    id: string
    name: string
    avatar: string
    title: string
    hospital: string
    department: string
    isVerified: boolean
    followerCount: number
    experience: string
    rating: number
  }
  realTimeData: {
    currentViewers: number
    totalMessages: number
    likes: number
    duration: number
    quality: StreamQuality
  }
  relatedRooms: Array<{
    id: string
    title: string
    thumbnail: string
    hostName: string
    viewerCount: number
    status: RoomStatus
  }>
  previousSessions: Array<{
    id: string
    title: string
    startTime: string
    endTime: string
    viewerCount: number
    duration: number
  }>
}

/** 直播房间（别名） */
export interface LiveRoom extends Room {}

/** 直播质量 */
export type StreamQuality = 'auto' | 'low' | 'medium' | 'high' | 'ultra'

/**
 * 房间列表查询参数
 */
export interface RoomListQuery {
  page?: number
  pageSize?: number
  status?: RoomStatus
  type?: RoomType
  departmentId?: string
  expertId?: string
  keyword?: string
  tags?: string[]
  sortBy?: 'createdAt' | 'scheduledStartAt' | 'currentViewers' | 'totalViewers'
  sortOrder?: 'asc' | 'desc'
}
```

### 3.3 场次类型（`src/types/session.ts`）

```typescript
/**
 * 场次状态枚举
 */
export type SessionStatus = 'scheduled' | 'live' | 'ended' | 'cancelled'

/**
 * 标签信息
 */
export interface TagItem {
  id: string
  name: string
}

/**
 * 专家简要信息
 */
export interface ExpertBrief {
  id: string
  name: string
  title?: string
  hospital?: string
  avatar_url?: string
}

/**
 * 场次详情（主接口返回结构）
 * 对应后端 DDL: live_sessions 表
 */
export interface SessionDetail {
  /** 场次ID */
  id: string
  /** 房间ID */
  room_id: string
  /** 场次摘要 */
  summary?: string
  /** 特邀专家 */
  featured_expert?: ExpertBrief
  /** 标签列表 */
  tags: TagItem[]
  /** 场次状态 */
  status: SessionStatus
  /** 开始时间（ISO 8601） */
  start_time: string
  /** 回放/播放地址（回放模式） */
  playback_url?: string
  /** 直播地址（直播模式：后端拉流） */
  stream_url?: string
}

/** 兼容别名 */
export type Session = SessionDetail

/**
 * 创建场次请求
 */
export interface CreateSessionRequest {
  /** 场次摘要（可选） */
  summary?: string
  /** 特邀专家ID（可选） */
  featured_expert_id?: string
  /** 开始时间（必填，ISO 8601） */
  start_time: string
  /** 房间ID（必填） */
  room_id: string
  /** 标签ID列表（可选） */
  tags?: string[]
}

/**
 * 更新场次请求（全部可选）
 */
export interface UpdateSessionRequest {
  summary?: string
  featured_expert_id?: string
  start_time?: string
  room_id?: string
  tags?: string[]
  /** 回放/播放地址（回放模式需要） */
  playback_url?: string
  /** 直播地址（直播模式：后端拉流） */
  stream_url?: string
}

/**
 * 场次列表查询参数
 */
export interface SessionListQuery {
  page?: number
  size?: number
  q?: string
  status?: SessionStatus
  room_id?: string
  expert_id?: string
  tag_ids?: string[]
  start_time_from?: string
  start_time_to?: string
  free_only?: boolean
  sort_by?: 'start_time' | 'view_count' | 'like_count' | 'created_at'
  sort_order?: 'asc' | 'desc'
}

/**
 * 场次统计数据
 */
export interface SessionStatistics {
  totalCount: number
  liveCount: number
  scheduledCount: number
  endedCount: number
  totalViewCount: number
  totalLikeCount: number
  averageWatchDuration: number
  dailyStats: Array<{
    date: string
    sessionCount: number
    viewCount: number
    likeCount: number
  }>
}
```

### 3.4 类型系统说明

**⚠️ 双类型命名约定**：
- `Room`/`LiveRoom`/`LiveRoomDetail` 使用 **camelCase**（`coverImage`、`scheduledStartAt`）
- `SessionDetail` 使用 **snake_case**（`room_id`、`start_time`、`playback_url`）
- 原因：Room 类型早期按前端惯例定义，Session 类型后期严格对齐后端 Pydantic Schema
- 后续计划：统一为 snake_case，需同步修改 Room 类型和所有消费方

---

## 四、API 封装

### 4.1 Room API（`src/api/room.ts`）

> 使用 `request.get/post/patch/delete` from `@/utils/request`
> 响应类型统一为 `ApiResponse<T>` from `@/types/common`
> 路径统一使用 `API_PATHS` from `@/config/api`

```typescript
// src/api/room.ts

import { request, upload } from '@/utils/request'
import { API_PATHS } from '@/config/api'
import type { ApiResponse, PaginatedResponse } from '@/types/common'
import type {
  LiveRoom,
  LiveRoomDetail,
  CreateRoomRequest,
  UpdateRoomRequest,
  RoomStatistics
} from '@/types/room'

// ===== 房间基本管理 =====

/**
 * 获取房间列表（公开，分页+分类+排序）
 * GET /api/v1/rooms
 */
export const getRooms = (params?: {
  page?: number
  size?: number
  category_id?: string
  sort?: string
}): Promise<ApiResponse<PaginatedResponse<LiveRoom>>> => {
  const cleanParams: Record<string, string | number> = {}
  if (params?.page !== undefined) cleanParams.page = params.page
  if (params?.size !== undefined) cleanParams.size = params.size
  if (params?.sort !== undefined) cleanParams.sort = params.sort
  if (params?.category_id !== undefined) cleanParams.category_id = params.category_id
  return request.get(API_PATHS.ROOM.LIST, { data: cleanParams })
}

/**
 * 获取首页房间列表（公开，分页+分类+排序）
 * GET /api/v1/homepage/rooms
 */
export const getHomepageRooms = (params?: {
  page?: number
  size?: number
  category_id?: string
  sort?: string
}): Promise<ApiResponse<PaginatedResponse<any>>> => {
  const cleanParams: Record<string, string | number> = {}
  if (params?.page !== undefined) cleanParams.page = params.page
  if (params?.size !== undefined) cleanParams.size = params.size
  if (params?.sort !== undefined) cleanParams.sort = params.sort
  if (params?.category_id !== undefined) cleanParams.category_id = params.category_id
  return request.get(API_PATHS.OTHER.HOMEPAGE_ROOMS, { data: cleanParams, showError: false })
}

/**
 * 获取房间详情（公开，含tabs）
 * GET /api/v1/rooms/{roomId}
 */
export const getRoomById = (roomId: string): Promise<ApiResponse<LiveRoomDetail>> => {
  return request.get(API_PATHS.ROOM.DETAIL(roomId), { showError: false })
}

/**
 * 创建房间（JWT）
 * POST /api/v1/rooms
 */
export const createRoom = (data: CreateRoomRequest): Promise<ApiResponse<any>> => {
  return request.post(API_PATHS.ROOM.CREATE, data, { loading: true, loadingText: '创建中...' })
}

/**
 * 更新房间（JWT，部分更新）
 * PATCH /api/v1/rooms/{roomId}
 */
export const updateRoom = (roomId: string, data: UpdateRoomRequest): Promise<ApiResponse<any>> => {
  return request.patch(API_PATHS.ROOM.UPDATE(roomId), data, { loading: true, loadingText: '保存中...' })
}

/**
 * 删除房间（JWT）
 * DELETE /api/v1/rooms/{roomId}
 */
export const deleteRoom = (roomId: string): Promise<ApiResponse<{ deleted: boolean }>> => {
  return request.delete(API_PATHS.ROOM.DELETE(roomId), { loading: true, loadingText: '删除中...' })
}

/**
 * 静默删除房间（不显示loading/error）
 * DELETE /api/v1/rooms/{roomId}
 */
export const deleteRoomSilent = (roomId: string): Promise<ApiResponse<{ deleted: boolean }>> => {
  return request.delete(API_PATHS.ROOM.DELETE(roomId), { loading: false, showError: false })
}

/**
 * 上传房间封面（JWT，multipart/form-data）
 * POST /api/v1/rooms/{roomId}/cover
 */
export const uploadRoomCover = (roomId: string, filePath: string): Promise<ApiResponse<{ cover_url: string }>> => {
  return upload({
    url: API_PATHS.ROOM.COVER(roomId),
    filePath,
    name: 'file',
    loading: true,
    loadingText: '上传封面中...'
  })
}

/**
 * 获取我的房间列表（JWT）
 * GET /api/v1/users/me/rooms
 */
export const getMyRooms = (
  params?: Record<string, any>,
  page?: number,
  size?: number
): Promise<ApiResponse<PaginatedResponse<any>>> => {
  const cleanParams = {
    ...(params || {}),
    ...(page ? { page } : {}),
    ...(size ? { size } : {})
  }
  const filteredParams = Object.fromEntries(
    Object.entries(cleanParams).filter(([_, value]) => value !== undefined)
  )
  return request.get(API_PATHS.USER_BEHAVIOR.MY_ROOMS, { data: filteredParams, showError: false })
}

// ===== 房间扩展功能 =====

/**
 * 获取房间的场次列表（公开）
 * GET /api/v1/rooms/{roomId}/sessions
 */
export const getRoomSessions = (roomId: string): Promise<ApiResponse<any[]>> => {
  return request.get(API_PATHS.ROOM.SESSIONS(roomId), { showError: false })
}

/**
 * 获取房间关联品牌（公开）
 * GET /api/v1/rooms/{roomId}/brands
 */
export const getRoomBrands = (roomId: string, params?: Record<string, any>): Promise<ApiResponse<any[]>> => {
  return request.get(API_PATHS.ROOM.BRANDS(roomId), { data: params, showError: false })
}

/**
 * 获取房间关联专家（公开）
 * GET /api/v1/rooms/{roomId}/experts
 */
export const getRoomExperts = (roomId: string): Promise<ApiResponse<any[]>> => {
  return request.get(API_PATHS.ROOM.EXPERTS(roomId), { showError: false })
}

/**
 * 获取房间Tab列表（公开）
 * GET /api/v1/rooms/{roomId}/tabs
 */
export const getRoomTabs = (roomId: string): Promise<ApiResponse<any[]>> => {
  return request.get(API_PATHS.ROOM.TABS(roomId), { showError: false })
}

/**
 * 检查房间是否已收藏（JWT）
 * GET /api/v1/rooms/{roomId}/is-favorited
 */
export const checkRoomFavorited = (roomId: string): Promise<ApiResponse<{ is_favorited: boolean }>> => {
  return request.get(API_PATHS.ROOM.IS_FAVORITED(roomId), { showError: false })
}

/**
 * 获取房间统计（JWT）
 * GET /api/v1/rooms/{roomId}/statistics
 */
export const getRoomStatistics = (roomId: string): Promise<ApiResponse<RoomStatistics>> => {
  return request.get(`/rooms/${roomId}/statistics`, { showError: false })
}

// ===== 管理员操作 =====

/**
 * 设置房间关联品牌（JWT+Admin）
 * POST /api/v1/admin/rooms/{roomId}/brands
 */
export const setAdminRoomBrands = (roomId: string, brandIds: string[]): Promise<ApiResponse<any>> => {
  return request.post(API_PATHS.ADMIN.BIND_ROOM_BRAND(roomId), { brand_ids: brandIds }, {
    loading: true, loadingText: '保存中...'
  })
}

/**
 * 批量获取房间状态（公开）
 * POST /api/v1/rooms/batch-status
 */
export const batchGetRoomStatus = (roomIds: string[]): Promise<ApiResponse<any[]>> => {
  return request.post(API_PATHS.ROOM.BATCH_STATUS, { room_ids: roomIds }, { showError: false })
}
```

### 4.2 Session API（`src/api/session.ts`）

```typescript
// src/api/session.ts

import { request } from '@/utils/request'
import { API_PATHS } from '@/config/api'
import type { ApiResponse, PaginatedResponse } from '@/types/common'
import type {
  Session,
  SessionDetail,
  SessionListQuery,
  CreateSessionRequest,
  UpdateSessionRequest,
  SessionStatistics
} from '@/types/session'

/**
 * 获取场次列表（公开，分页+筛选）
 * GET /api/v1/sessions
 */
export const getSessionList = (params?: SessionListQuery): Promise<ApiResponse<PaginatedResponse<Session>>> => {
  const data: any = { ...(params || {}) }
  if (data.pageSize !== undefined && data.size === undefined) data.size = data.pageSize
  return request.get(API_PATHS.SESSION.LIST, { data })
}

/**
 * 获取场次详情（公开）
 * GET /api/v1/sessions/{sessionId}
 */
export const getSessionDetail = (sessionId: string): Promise<ApiResponse<SessionDetail>> => {
  return request.get(API_PATHS.SESSION.DETAIL(sessionId), { showError: false })
}

/**
 * 创建场次（JWT）
 * POST /api/v1/rooms/{roomId}/sessions
 * @param data - 必须包含 room_id
 */
export const createSession = (data: CreateSessionRequest & { room_id?: string }): Promise<ApiResponse<{ sessionId: string } & any>> => {
  const roomId: string = (data as any).room_id
  if (!roomId) return Promise.reject(new Error('createSession: room_id is required'))
  return request.post(API_PATHS.SESSION.CREATE(roomId), data, { loading: true, loadingText: '创建中...' })
}

/**
 * 为房间创建场次（JWT，直接指定roomId）
 * POST /api/v1/rooms/{roomId}/sessions
 */
export const createRoomSession = (roomId: string, data: any): Promise<ApiResponse<any>> => {
  return request.post(API_PATHS.ROOM.SESSIONS(roomId), data, { loading: true, loadingText: '创建中...' })
}

/**
 * 导入回放场次（JWT）
 * POST /api/v1/rooms/{roomId}/sessions/import
 */
export const importSession = (roomId: string, data: any): Promise<ApiResponse<any>> => {
  return request.post(API_PATHS.SESSION.IMPORT(roomId), data, { loading: true, loadingText: '导入中...' })
}

/**
 * 更新场次（JWT，部分更新）
 * PATCH /api/v1/sessions/{sessionId}
 */
export const updateSession = (sessionId: string, data: UpdateSessionRequest): Promise<ApiResponse<any>> => {
  return request.patch(API_PATHS.SESSION.DETAIL(sessionId), data, { loading: true, loadingText: '保存中...' })
}

/**
 * 删除场次（JWT）
 * DELETE /api/v1/sessions/{sessionId}
 */
export const deleteSession = (sessionId: string): Promise<ApiResponse<{ deleted: boolean }>> => {
  return request.delete(API_PATHS.SESSION.DETAIL(sessionId), { loading: true, loadingText: '删除中...' })
}

/**
 * 开播（JWT，状态→live）
 * POST /api/v1/sessions/{sessionId}/start
 */
export const startSession = (sessionId: string): Promise<ApiResponse<any>> => {
  return request.post(API_PATHS.SESSION.START(sessionId), {}, {
    loading: true, loadingText: '开播中...', showError: false
  })
}

/**
 * 获取场次统计（JWT）
 * GET /api/v1/sessions/{sessionId}/statistics
 */
export const getSessionStatistics = (sessionId: string): Promise<ApiResponse<SessionStatistics>> => {
  return request.get(API_PATHS.SESSION.STATISTICS(sessionId), { showError: false })
}

/**
 * 获取房间的场次列表（公开，分页）
 * GET /api/v1/rooms/{roomId}/sessions
 */
export const getRoomSessions = (
  roomId: string,
  params?: { page?: number; size?: number; sort_by?: string; sort_order?: 'asc' | 'desc' }
): Promise<ApiResponse<PaginatedResponse<any>>> => {
  return request.get(API_PATHS.ROOM.SESSIONS(roomId), { data: params, showError: false })
}

/**
 * 记录观看（JWT）
 * POST /api/v1/sessions/{sessionId}/watch
 */
export const recordWatchSession = (sessionId: string, data: any): Promise<ApiResponse<any>> => {
  return request.post(API_PATHS.HISTORY.RECORD_WATCH(sessionId), data, { loading: false, showError: false })
}

/**
 * 分享统计
 * POST /api/v1/playback/stats
 */
export const shareSession = (sessionId: string, platform: string): Promise<ApiResponse<any>> => {
  return request.post(API_PATHS.SESSION.SHARE, { session_id: sessionId, platform }, { loading: false, showError: false })
}
```

---

## 五、config/api.ts 路径配置

> 路径已定义在 `src/config/api.ts` 中，**禁止重复定义**。以下为 Room+Session 相关的完整映射。

### 5.1 ROOM 模块

```typescript
ROOM: {
  LIST: '/rooms',                                                    // GET 公开
  DETAIL: (roomId: string) => `/rooms/${roomId}`,                    // GET 公开
  CREATE: '/rooms',                                                  // POST JWT
  UPDATE: (roomId: string) => `/rooms/${roomId}`,                    // PATCH JWT
  DELETE: (roomId: string) => `/rooms/${roomId}`,                    // DELETE JWT
  SESSIONS: (roomId: string) => `/rooms/${roomId}/sessions`,         // GET 公开 / POST JWT
  COVER: (roomId: string) => `/rooms/${roomId}/cover`,               // POST JWT
  BRANDS: (roomId: string) => `/rooms/${roomId}/brands`,             // GET 公开
  EXPERTS: (roomId: string) => `/rooms/${roomId}/experts`,           // GET 公开
  TOPICS: (roomId: string) => `/rooms/${roomId}/topics`,             // GET 公开
  TABS: (roomId: string) => `/rooms/${roomId}/tabs`,                 // GET 公开
  IS_FAVORITED: (roomId: string) => `/rooms/${roomId}/is-favorited`, // GET JWT
  MESSAGES: (roomId: string) => `/rooms/${roomId}/messages`,         // GET 公开 / POST JWT
  BATCH_STATUS: '/rooms/batch-status',                               // POST 公开
  SUB_VENUES: (roomId: string) => `/rooms/${roomId}/sub-venues`      // GET 公开
}
```

### 5.2 SESSION 模块

```typescript
SESSION: {
  LIST: '/sessions',                                                   // GET 公开
  DETAIL: (sessionId: string) => `/sessions/${sessionId}`,             // GET/PATCH/DELETE
  CREATE: (roomId: string) => `/rooms/${roomId}/sessions`,             // POST JWT
  IMPORT: (roomId: string) => `/rooms/${roomId}/sessions/import`,      // POST JWT
  STATISTICS: (sessionId: string) => `/sessions/${sessionId}/statistics`, // GET JWT
  START: (sessionId: string) => `/sessions/${sessionId}/start`,        // POST JWT
  END: (sessionId: string) => `/sessions/${sessionId}/end`,            // POST JWT
  TAGS: (sessionId: string) => `/content/sessions/${sessionId}/tags`,  // GET/POST
  VIEWERS: (sessionId: string) => `/sessions/${sessionId}/viewers`,    // GET
  STREAM_URL: (sessionId: string) => `/sessions/${sessionId}/stream-url`, // GET
  SEARCH: '/sessions/search',                                          // GET
  SHARE: '/playback/stats',                                            // POST
  WATCH: (sessionId: string) => `/sessions/${sessionId}/watch`         // POST
}
```

### 5.3 ADMIN 模块（Room/Session 相关）

```typescript
ADMIN: {
  // 品牌关联
  BIND_ROOM_BRAND: (roomId: string) => `/admin/rooms/${roomId}/brands`, // POST JWT+Admin

  // Tab管理（详见06-直播间Tab管理文档）
  ROOM_TABS: (roomId: string) => `/admin/rooms/${roomId}/tabs`,
  CREATE_TAB: (roomId: string) => `/admin/rooms/${roomId}/tabs`,
  UPDATE_TAB: (tabId: string) => `/admin/tabs/${tabId}`,
  DELETE_TAB: (tabId: string) => `/admin/tabs/${tabId}`,
  UPLOAD_TAB_IMAGE: (roomId: string) => `/admin/rooms/${roomId}/tabs/image`,
  SORT_TABS: (roomId: string) => `/admin/rooms/${roomId}/tabs/sort`,

  // 场次标签关联（详见02-标签管理文档）
  SESSION_TAGS: (sessionId: string) => `/content/sessions/${sessionId}/tags`,
  DELETE_SESSION_TAG: (sessionId: string, tagId: string) =>
    `/content/sessions/${sessionId}/tags/${tagId}`
}
```

### 5.4 其他相关模块

```typescript
// 首页
OTHER: {
  HOMEPAGE_ROOMS: '/homepage/rooms'  // GET 公开
}

// 用户行为
USER_BEHAVIOR: {
  MY_ROOMS: '/users/me/rooms'  // GET JWT
}

// 观看历史
HISTORY: {
  RECORD_WATCH: (sessionId: string) => `/sessions/${sessionId}/watch`  // POST JWT
}
```

### 5.5 双网关路由说明

```
┌─────────────────────────────────────────────────────────┐
│  users 服务（认证）    │  core 服务（业务）              │
│  /auth/*              │  /rooms/*, /sessions/*          │
│  /me/*, /register     │  /content/*, /admin/*           │
│                       │  /homepage/*, /experts/*        │
└─────────────────────────────────────────────────────────┘

默认地址：
  core:  http://localhost:8080/api/core
  users: http://localhost:8080/api/users/api/v1

环境变量：
  VITE_BASE_API_URL  → core 服务地址
  VITE_AUTH_API_URL  → users 服务地址
```

---

## 六、管理端页面实现

### 6.1 CreateLive.vue — 创建/编辑直播间

> 核心页面，一次操作同时创建 Room + Session
> 支持三种创建模式：预告(scheduled)、直播(live)、回放(replay)
> 支持编辑模式：`?mode=edit&roomId=...`

**表单字段**：

| 字段 | 绑定 | 必填 | 说明 |
|------|------|------|------|
| 直播标题 | `form.title` | ✅ | maxlength=60 |
| 简介 | `form.summary` | ❌ | maxlength=2000，展示为简介Tab |
| 简介图片 | `form.intro_image_url` / 本地文件 | ❌ | 相册→上传；`https?://`→直存 Tab `image_url`；见 §6.1.1 |
| 封面 | `form.cover_url` / 本地文件 | ❌ | 相册→`uploadRoomCover`；`https?://`→直存 `cover_url`；见 §6.1.1 |
| 创建类型 | `creationMode` | ✅ | `scheduled` / `live` / `replay` |
| 开始时间 | `startDate` + `startTime` | ✅ | date+time picker |
| 直播地址 | `form.stream_url` | 仅直播模式 | maxlength=500 |
| 回放地址 | `form.playback_url` | 仅回放模式 | maxlength=500 |
| 关联专家 | `selectedExpertIds` | ❌ | 多选，第一个作为主讲 |
| 关联品牌 | `selectedBrandIds` | ❌ | 多选 |
| 标签 | `selectedTagIds` | ❌ | 仅管理员可见 |

**创建流程（`handleSubmit`）**：

```
1. 校验必填字段（title, start_time, 模式特定字段）
2. POST /rooms → 获取 roomId
3. POST /rooms/{roomId}/cover（如有封面）→ 上传封面
4. 创建 Room Intro Tab（如有简介）→ POST /admin/rooms/{roomId}/tabs
5. 根据 creationMode：
   - scheduled/live: POST /rooms/{roomId}/sessions → 获取 sessionId
   - replay: POST /rooms/{roomId}/sessions/import → 获取 sessionId
6. 直播模式补充：
   PATCH /sessions/{sessionId}（写入 stream_url）
   POST /sessions/{sessionId}/start（状态→live）
7. 设置标签（仅管理员）：POST /content/sessions/{sessionId}/tags
8. 设置专家：POST /experts/sessions/{sessionId}/experts
9. 设置品牌：POST /admin/rooms/{roomId}/brands
10. 成功提示 → redirectTo(LiveView?roomId&sessionId)
```

**回滚逻辑**：
- Room 创建成功但后续步骤失败时，调用 `deleteRoomSilent(roomId)` 清理已创建的 Room
- 使用 `createdRoomId` 变量追踪已创建的 Room

**编辑模式**：
- 从 URL 参数获取 `roomId`，调用 `getRoomById(roomId)` 加载数据
- 回填表单字段：title、summary、cover_url、intro_image_url
- 回填关联数据：专家、品牌、标签
- 提交时调用 `updateRoom(roomId, data)` 更新房间信息
- 如有新封面：`uploadRoomCover(roomId, filePath)` 通过独立接口上传
- 如有新简介图片：`uploadTabImage(roomId, filePath)` 上传后更新 intro Tab 的 `image_url`
- 更新场次：`updateSession(sessionId, data)`

**简介Tab图片 / 封面（已拍板 · 对齐后端）**：

| 来源 | 封面 | 简介 Tab |
|------|------|----------|
| 相册 / 本地 temp | `POST .../cover` → 相对路径 | `POST .../tabs/image` → 相对路径 |
| 绝对 `https?://` 外链 | 写入 `cover_url`（create/PATCH），**不** downloadFile | 写入 Tab `image_url`，**不** downloadFile |
| 展示 | 统一 `resolveMediaUrl`（相对拼媒体基址；绝对原样） | 同左 |

依据：后端读房时对已是 http(s) 的 `cover_url` 原样返回；Tab `image_url` Schema 无强制 `/media` 白名单。

#### 6.1.1 现码与环境（拍板记录）

| 维度 | 说明 |
|------|------|
| **拍板** | **B 细化**（2026-09-04）：外链直存 + 本地上传；封面与简介同一规则 |
| **历史坑** | 曾对简介/封面外链强制下载再上传 → 易 `Failed to fetch`，且上传进 `/media` 后真机受局域网 HTTP 影响 |
| **环境约束 A** | 仅当落库为 `/media/...` 时，真机依赖 `VITE_MEDIA_BASE_URL`；局域网 HTTP 时模拟器可看、真机常挂 |
| **环境约束 B** | 外链直存不依赖 downloadFile 合法域名；展示依赖小程序对图片域名的策略（外网 https 通常优于局域网 HTTP） |
| **环境约束 C** | 本地简介图仍走 `uploadTabImage`（Admin 或房间 owner） |
| **曾误判** | 封面外链「能保存但不显示」≠ 合法域名失败；若已进 `/media` 再查约束 A |

**AI 口令**：改图相关逻辑以本节拍板为准；勿再改回「外链必须上传」。

### 6.2 MyLive.vue — 我的直播列表

**核心功能**：
- 调用 `getMyRooms()` 获取当前用户的房间列表
- 支持本地缓存 fallback（API 失败时从 localStorage 读取）
- 每个房间卡片显示：封面、标题、状态、创建时间
- 操作：编辑（跳转 CreateLive?mode=edit）、删除（确认后调用 deleteRoom）

**缓存策略**：
- 首次加载：API → 成功写入 localStorage
- API 失败：从 localStorage 读取缓存数据
- 缓存 key：`myLiveCache`

---

## 七、用户端页面/组件

### 7.1 Pinia Store — Room Store（`src/store/room.ts`）

**State**：
- `roomList: LiveRoom[]` — 房间列表
- `currentRoom: LiveRoomDetail | null` — 当前房间详情
- `roomCache: Map<string, LiveRoomDetail>` — LRU 缓存（最大 50 条）
- `currentPage/pageSize/total/hasMore` — 分页信息
- `loading/refreshing/loadingMore/detailLoading` — 加载状态
- `filters: RoomListQuery` — 筛选条件
- `selectedRoomFromHome` — 跨页面数据传递

**Getters**：
- `liveRooms` — 直播中的房间
- `upcomingRooms` — 预告房间
- `replayRooms` — 回放房间
- `isEmpty` — 列表是否为空
- `isCurrentRoomLive` — 当前房间是否直播中

**Actions**：
- `fetchRoomList(params?, append?)` — 获取房间列表（支持分页追加）
- `refreshRoomList(params?)` — 刷新房间列表
- `loadMoreRooms()` — 加载更多
- `fetchRoomDetail(roomId, useCache?)` — 获取房间详情（LRU 缓存）
- `createRoom(roomData)` — 创建房间（返回 roomId，自动刷新列表）
- `updateRoom(roomId, data)` — 更新房间（同步更新列表/详情/缓存）
- `deleteRoom(roomId)` — 删除房间（从列表/缓存中移除）
- `fetchRoomStatistics(roomId?)` — 获取统计数据
- `setFilters/clearFilters` — 筛选条件管理
- `updateRoomStatus(roomId, status)` — 更新房间状态
- `clearRoomData/clearCache` — 清除数据

### 7.2 Pinia Store — Session Store（`src/store/session.ts`）

**State**：
- `sessionList: Session[]` — 场次列表
- `currentSession: SessionDetail | null` — 当前场次详情
- `sessionCache: Map<string, SessionDetail>` — LRU 缓存（最大 30 条）
- `isWatching/watchStartTime` — 观看状态

**Getters**：
- `liveSessions` — 进行中的场次
- `upcomingSessions` — 即将开始的场次
- `endedSessions` — 已结束的场次
- `todaySessions` — 今日场次
- `watchDuration` — 观看时长（秒）
- `isCurrentSessionLive` — 当前场次是否直播中

**Actions**：
- `fetchSessionList(params?, append?)` — 获取场次列表
- `fetchSessionDetail(sessionId, useCache?)` — 获取场次详情（LRU 缓存）
- `createSession(sessionData)` — 创建场次（返回 sessionId）
- `updateSession(sessionId, data)` — 更新场次
- `deleteSession(sessionId)` — 删除场次
- `startWatching/stopWatching/pauseWatching/resumeWatching` — 观看状态管理
- `incrementViewCount(sessionId)` — 增加观看数
- `updateSessionStatus(sessionId, status)` — 更新场次状态

### 7.3 LiveView.vue — 直播间详情/播放页

**核心功能**：
- 从 URL 参数获取 `roomId` + `sessionId`
- 调用 `fetchRoomDetail(roomId)` + `fetchSessionDetail(sessionId)` 加载数据
- 视频播放器：
  - 微信小程序：`<live-player>` 组件（直播模式）/ `<video>` 组件（回放模式）
  - 其他端：`<video>` 组件
  - 播放地址优先级：`session.stream_url` > `session.playback_url` > `room.playUrl`
- Tab 展示：从 `room.tabs` 获取，按 `sort_order` 排序，仅显示 `is_active=true`
- 留言区：作为特殊 Tab（`tab_key === 'message'`）注入列表末尾

**Tab 渲染规则**：
- `content_type === 'text'`：渲染 `text_content` 纯文本
- `content_type === 'image'`：渲染 `image_url` 纯图片
- `content_type === 'mixed'`：渲染 `text_content` + `image_url` 图文混排
- Tab 匹配使用 `tab_key` 而非 `title`

### 7.4 LiveCard.vue — 首页直播卡片

**展示字段**：
- 封面图（`room.coverImage` 或 `room.cover_url`）
- 状态徽章：直播中（红）/ 预告（蓝）/ 回放（绿）
- 分类徽章（`room.category.name`）
- 标题、简介摘要
- 主播头像+名称
- 观看人数、点赞数

**点击行为**：
- 跳转播放页：`/pages/live/LiveView?roomId=...&sessionId=...`
- 从 `room.previousSessions` 或 API 获取最新的 sessionId

---

## 八、对接清单

| # | 任务 | 文件路径 | 说明 |
|---|------|---------|------|
| 1 | 房间类型定义 | `src/types/room.ts` | Room, LiveRoomDetail, CreateRoomRequest, Tab 等 |
| 2 | 场次类型定义 | `src/types/session.ts` | SessionDetail, CreateSessionRequest, UpdateSessionRequest 等 |
| 3 | 通用类型 | `src/types/common.ts` | ApiResponse, PaginatedResponse, BaseEntity |
| 4 | 房间 API 封装 | `src/api/room.ts` | 22个函数：CRUD + 封面 + 扩展 + 管理员 |
| 5 | 场次 API 封装 | `src/api/session.ts` | 12个函数：CRUD + 导入 + 开播 + 统计 |
| 6 | API 路径配置 | `src/config/api.ts` | ROOM/SESSION/ADMIN 模块路径 |
| 7 | 房间 Store | `src/store/room.ts` | Pinia，LRU缓存50条，分页追加 |
| 8 | 场次 Store | `src/store/session.ts` | Pinia，LRU缓存30条，观看状态管理 |
| 9 | 创建直播间页 | `src/pages/live/CreateLive.vue` | 三种模式+编辑模式+回滚逻辑 |
| 10 | 直播间详情页 | `src/pages/live/LiveView.vue` | 视频播放+Tab+留言 |
| 11 | 我的直播列表 | `src/pages/my-live/MyLive.vue` | 列表+缓存fallback+编辑/删除 |
| 12 | 直播卡片组件 | `src/components/common/LiveCard.vue` | 首页卡片展示 |
| 13 | Tab 管理组件 | `src/pages/admin/roomTab/RoomTabManager.vue` | 嵌入 CreateLive |
| 14 | Tab 编辑弹窗 | `src/pages/admin/roomTab/TabEditDialog.vue` | Tab CRUD |
| 15 | 更新 pages.json | `src/pages.json` | 路由注册 |

---

## 九、API 链路总结

### 9.1 创建直播间完整链路

```
CreateLive.vue — handleSubmit()
  │
  ├─ 1. createRoom({ title, description, summary, category_id, record_by_default })
  │     ──→ POST /rooms
  │     ──→ ApiResponse<{ roomId: string }>
  │
  ├─ 2. uploadRoomCover(roomId, filePath)           [如有封面]
  │     ──→ POST /rooms/{roomId}/cover (multipart)
  │     ──→ ApiResponse<{ cover_url: string }>
  │
  ├─ 3. createTab(roomId, { tab_key: 'intro', ... })  [如有简介]
  │     ──→ POST /admin/rooms/{roomId}/tabs
  │     ──→ ApiResponse<LiveRoomTab>
  │
  ├─ 4a. createRoomSession(roomId, { start_time, summary, featured_expert_id })  [预告/直播]
  │      ──→ POST /rooms/{roomId}/sessions
  │      ──→ ApiResponse<{ sessionId: string }>
  │
  ├─ 4b. importSession(roomId, { start_time, playback_url, status: 'ready' })    [回放]
  │      ──→ POST /rooms/{roomId}/sessions/import
  │      ──→ ApiResponse<{ sessionId: string }>
  │
  ├─ 5. updateSession(sessionId, { stream_url })    [直播模式]
  │     ──→ PATCH /sessions/{sessionId}
  │
  ├─ 6. startSession(sessionId)                     [直播模式]
  │     ──→ POST /sessions/{sessionId}/start
  │
  ├─ 7. setSessionTags(sessionId, { tag_ids, mode: 'replace' })  [管理员]
  │     ──→ POST /content/sessions/{sessionId}/tags
  │
  ├─ 8. setSessionExperts(sessionId, expertIds)     [如有专家]
  │     ──→ POST /experts/sessions/{sessionId}/experts
  │
  ├─ 9. setAdminRoomBrands(roomId, brandIds)        [如有品牌]
  │     ──→ POST /admin/rooms/{roomId}/brands
  │
  └─ 10. redirectTo(LiveView?roomId=...&sessionId=...)
```

### 9.2 Room CRUD 链路

```
Room Store / CreateLive / MyLive
  │
  ├─ fetchRoomList()  → getRooms()          → GET  /rooms
  ├─ fetchRoomDetail() → getRoomById()      → GET  /rooms/{roomId}
  ├─ createRoom()     → createRoom()        → POST /rooms
  ├─ updateRoom()     → updateRoom()        → PATCH /rooms/{roomId}
  ├─ deleteRoom()     → deleteRoom()        → DELETE /rooms/{roomId}
  ├─ getMyRooms()     → getMyRooms()        → GET  /users/me/rooms
  └─ getHomepageRooms() → getHomepageRooms() → GET /homepage/rooms
```

### 9.3 Session CRUD 链路

```
Session Store / CreateLive / LiveView
  │
  ├─ fetchSessionList()  → getSessionList()    → GET  /sessions
  ├─ fetchSessionDetail() → getSessionDetail()  → GET  /sessions/{sessionId}
  ├─ createSession()     → createSession()      → POST /rooms/{roomId}/sessions
  ├─ updateSession()     → updateSession()      → PATCH /sessions/{sessionId}
  ├─ deleteSession()     → deleteSession()      → DELETE /sessions/{sessionId}
  ├─ importSession()     → importSession()      → POST /rooms/{roomId}/sessions/import
  └─ startSession()      → startSession()       → POST /sessions/{sessionId}/start
```

### 9.4 端点→类型→页面 对照表

| 端点 | 方法 | 请求类型 | 响应类型 | 调用页面/组件 |
|------|------|----------|----------|--------------|
| /rooms | GET | RoomListQuery | PaginatedResponse\<LiveRoom\> | Home, MyLive |
| /rooms/{roomId} | GET | - | LiveRoomDetail | LiveView, CreateLive(edit) |
| /rooms | POST | CreateRoomRequest | { roomId } | CreateLive |
| /rooms/{roomId} | PATCH | UpdateRoomRequest | any | CreateLive(edit) |
| /rooms/{roomId} | DELETE | - | { deleted } | MyLive, CreateLive(rollback) |
| /rooms/{roomId}/cover | POST | FormData(file) | { cover_url } | CreateLive |
| /homepage/rooms | GET | { page?, size? } | PaginatedResponse | Home |
| /users/me/rooms | GET | { page?, size? } | PaginatedResponse | MyLive |
| /sessions | GET | SessionListQuery | PaginatedResponse\<Session\> | SessionList |
| /sessions/{sessionId} | GET | - | SessionDetail | LiveView |
| /rooms/{roomId}/sessions | POST | CreateSessionRequest | { sessionId } | CreateLive |
| /sessions/{sessionId} | PATCH | UpdateSessionRequest | any | CreateLive(edit) |
| /sessions/{sessionId} | DELETE | - | { deleted } | CreateLive(edit) |
| /rooms/{roomId}/sessions/import | POST | { start_time, playback_url, status } | any | CreateLive(replay) |
| /sessions/{sessionId}/start | POST | - | any | CreateLive(live) |
| /rooms/{roomId}/tabs | GET | - | { items: Tab[] } | LiveView |
| /admin/rooms/{roomId}/tabs | POST | LiveRoomTabCreate | LiveRoomTab | CreateLive |
| /admin/rooms/{roomId}/brands | POST | { brand_ids } | any | CreateLive |
| /content/sessions/{sessionId}/tags | POST | { tag_ids, mode } | any | CreateLive |

### 9.5 错误码映射

| 错误码 | 说明 | 前端处理 |
|--------|------|---------|
| 200 | 成功 | 正常处理 |
| 2001 | 资源不存在 | 提示"房间/场次不存在" |
| 2002 | 资源已存在 | 提示"重复创建" |
| 2004 | 业务逻辑错误 | 提示具体业务错误 |
| 3001 | 未授权 | 跳转登录页 |
| 3002 | 权限不足 | 提示"需要管理员权限"，隐藏管理员功能 |
| 4001 | 参数校验失败 | 提示具体校验错误 |

### 9.6 Session 状态机

```
                    ┌──────────────┐
                    │  scheduled   │ ← 创建后初始状态
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │   live   │ │  ended   │ │ cancelled│
        └──────────┘ └──────────┘ └──────────┘
              │
              │ POST /sessions/{id}/start
              │ 或直播模式创建后自动调用
              ▼
        ┌──────────┐
        │   live   │ → 播放页使用 stream_url
        └──────────┘
              │
              │ POST /sessions/{id}/end
              ▼
        ┌──────────┐
        │  ended   │ → 播放页使用 playback_url
        └──────────┘
```

### 9.7 缓存策略

| Store | 缓存对象 | 最大条数 | 淘汰策略 | 更新时机 |
|-------|---------|---------|---------|---------|
| room.ts | `roomCache: Map<string, LiveRoomDetail>` | 50 | FIFO（删除最早的） | fetchRoomDetail 命中时；createRoom/updateRoom 后同步更新 |
| session.ts | `sessionCache: Map<string, SessionDetail>` | 30 | FIFO（删除最早的） | fetchSessionDetail 命中时；createSession/updateSession 后同步更新 |
| MyLive.vue | localStorage `myLiveCache` | 1份完整列表 | 覆盖写入 | API 成功时写入；API 失败时读取 |
