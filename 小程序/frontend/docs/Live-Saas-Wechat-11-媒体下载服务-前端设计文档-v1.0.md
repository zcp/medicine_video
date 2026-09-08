# 媒体下载服务（Media Download Service）—— 前端可落地实现文档

> **技术栈**：uni-app + Vue 3 + TypeScript + Pinia
> **平台**：微信小程序
> **后端设计文档**：《11-媒体下载服务-后端设计文档.md》
> **零偏差**：所有类型、路径、端点严格对齐后端设计文档
> **独立微服务**：端口 8001，JWT 认证与主服务共享同一密钥

---

## 一、功能概述

媒体下载服务是一个独立微服务（端口 8001），用于管理视频资源的异步下载任务。前端需实现：

### 1.1 任务管理（管理端）
1. **下载任务列表**：分页 + 按状态筛选 + 操作（启动/重试/删除/查看详情）
2. **创建下载任务**：输入 resource_url + resource_type + 可选 video_id/liveroom_id
3. **任务详情**：进度条、分片信息、失败记录、已下载视频
4. **启动/重试下载**：触发异步下载（Celery Worker）

### 1.2 失败记录管理
5. **失败记录列表**：按任务维度查看失败分段
6. **重试/放弃单条失败**：分段级别的精细化控制

### 1.3 已下载视频库
7. **视频库列表**：全局浏览已下载视频
8. **视频详情**：查看视频元数据（格式、分辨率、大小、时长）

### 1.4 批量导入
9. **CSV 批量导入**：上传 CSV 文件批量创建任务
10. **爬取导入**：从指定 URL 爬取视频资源并导入
11. **导入状态查询**：轮询爬取导入进度

**后端数据表**：
- `download_tasks`：id(UUID PK), user_id(UUID), video_id(VARCHAR 200), liveroom_id(VARCHAR 200), resource_url(VARCHAR 2000 NOT NULL), resource_type(VARCHAR 20 CHECK m3u8/ts/mp4/image), status(VARCHAR 30 CHECK pending/processing/completed/partial_completed/failed/cancelled), progress(FLOAT 0-100), total_segments, downloaded_segments, failed_segments, storage_path, error_message, started_at, completed_at, created_at, updated_at
- `download_failures`：id(UUID PK), task_id(UUID FK CASCADE), segment_url(VARCHAR 2000), resource_type, failure_type(CHECK network_error/timeout/invalid_content/storage_error/permission_error), error_message, retry_count, status(CHECK pending/retrying/abandoned), created_at, updated_at
- `downloaded_videos`：id, video_id, liveroom_id, video_type, video_url, storage_path(NOT NULL), file_size(BIGINT), duration(INT), resolution, format, status(CHECK completed/partial_completed/corrupted), metadata(JSONB), created_at, updated_at. UNIQUE(video_id, storage_path)

**物理删除**：全部三张表均使用物理删除，无软删除

---

## 二、目录结构

```
src/
├── types/
│   └── download.ts                        # 下载服务类型定义
├── api/
│   └── download.ts                        # 下载服务 API 封装（16个端点）
├── config/
│   └── api.ts                             # API 路径配置（DOWNLOAD 段）
├── pages/
│   └── admin/
│       └── download/
│           ├── TaskList.vue               # 下载任务列表页
│           ├── TaskCreateForm.vue         # 新建任务表单页
│           ├── TaskDetail.vue             # 任务详情页（含失败记录+视频）
│           ├── VideoLibrary.vue           # 已下载视频库
│           └── BatchImport.vue            # 批量导入页（CSV+爬取）
└── composables/
    ├── useTaskPoller.ts                   # 任务进度轮询
    └── useCrawlStatus.ts                  # 爬取导入状态轮询
```

---

## 三、类型定义

> 严格对齐后端 Pydantic Schema 与 DDL，字段名、类型、必填/可选 100% 一致

```typescript
// src/types/download.ts

/**
 * 下载任务状态枚举
 * DDL: CHECK status IN ('pending', 'processing', 'completed', 'partial_completed', 'failed', 'cancelled')
 */
export type TaskStatus = 'pending' | 'processing' | 'completed' | 'partial_completed' | 'failed' | 'cancelled'

/**
 * 资源类型枚举
 * DDL: CHECK resource_type IN ('m3u8', 'ts', 'mp4', 'image')
 */
export type ResourceTypeEnum = 'm3u8' | 'ts' | 'mp4' | 'image'

/**
 * 失败类型枚举
 * DDL: CHECK failure_type IN ('network_error', 'timeout', 'invalid_content', 'storage_error', 'permission_error')
 */
export type FailureTypeEnum = 'network_error' | 'timeout' | 'invalid_content' | 'storage_error' | 'permission_error'

/**
 * 失败记录状态枚举
 * DDL: CHECK status IN ('pending', 'retrying', 'abandoned')
 */
export type FailureStatusEnum = 'pending' | 'retrying' | 'abandoned'

/**
 * 已下载视频状态枚举
 * DDL: CHECK status IN ('completed', 'partial_completed', 'corrupted')
 */
export type VideoStatusEnum = 'completed' | 'partial_completed' | 'corrupted'

/**
 * 创建下载任务请求（对应后端 DownloadTaskCreate Schema）
 * resource_url 必须以 http:// 或 https:// 开头
 */
export interface DownloadTaskCreate {
  resource_url: string         // max 2000, 必填, http/https
  resource_type: ResourceTypeEnum // 必填
  video_id?: string            // max 200, 可选
  liveroom_id?: string         // max 200, 可选
}

/**
 * 下载任务响应（对应后端 DownloadTaskItem Schema / DDL download_tasks 表）
 */
export interface DownloadTaskItem {
  id: string                   // UUID
  user_id: string              // UUID
  video_id: string | null
  liveroom_id: string | null
  resource_url: string
  resource_type: string        // 'm3u8' | 'ts' | 'mp4' | 'image'
  status: TaskStatus
  progress: number             // 0.0 - 100.0
  total_segments: number
  downloaded_segments: number
  failed_segments: number
  storage_path: string | null
  error_message: string | null
  started_at: string | null    // ISO 8601
  completed_at: string | null  // ISO 8601
  created_at: string           // ISO 8601
  updated_at: string           // ISO 8601
}

/**
 * 下载失败记录响应（对应后端 DownloadFailureItem Schema / DDL download_failures 表）
 * 注意：字段名为 segment_url（非 resource_url）
 */
export interface DownloadFailureItem {
  id: string                   // UUID
  task_id: string              // UUID
  segment_url: string | null   // 失败分段 URL（非资源 URL）
  resource_type: string
  failure_type: FailureTypeEnum
  error_message: string | null
  retry_count: number
  status: FailureStatusEnum
  created_at: string
  updated_at: string
}

/**
 * 已下载视频响应（对应后端 DownloadedVideoItem Schema / DDL downloaded_videos 表）
 */
export interface DownloadedVideoItem {
  id: string                   // UUID
  video_id: string | null
  liveroom_id: string | null
  video_type: string | null
  video_url: string | null
  storage_path: string         // NOT NULL
  file_size: number | null     // BIGINT, 字节
  duration: number | null      // 秒
  resolution: string | null
  format: string | null
  status: VideoStatusEnum
  created_at: string
  updated_at: string
}

/**
 * 爬取导入请求（对应后端 CrawlAndImportRequest Schema）
 */
export interface CrawlAndImportRequest {
  source_url: string           // max 2000, 必填
}

/**
 * 批量导入结果（对应后端 BatchImportResult Schema）
 */
export interface BatchImportResult {
  tasks_in_csv: number
  new_tasks_created: number
  tasks_skipped_duplicates: number
}

/**
 * 任务分页响应（对应后端 TaskPageResult Schema）
 */
export interface TaskPageResult {
  items: DownloadTaskItem[]
  total: number
  page: number
  page_size: number
}

/**
 * 失败记录分页响应（对应后端 FailurePageResult Schema）
 */
export interface FailurePageResult {
  items: DownloadFailureItem[]
  total: number
  page: number
  page_size: number
}

/**
 * 视频分页响应（对应后端 VideoPageResult Schema）
 */
export interface VideoPageResult {
  items: DownloadedVideoItem[]
  total: number
  page: number
  page_size: number
}

/**
 * 爬取导入状态响应
 */
export interface CrawlImportStatus {
  status: string               // 'processing' | 'completed' | 'failed'
  progress: number
  total_found: number
  imported: number
}
```

---

## 四、API 封装

> 严格对齐后端路由表（16 个端点），使用 `API_PATHS` 配置，不硬编码路径

```typescript
// src/api/download.ts

import { request } from '@/utils/request'
import { API_PATHS } from '@/config/api'
import type { ApiResponse } from '@/types/common'
import type {
  DownloadTaskCreate,
  DownloadTaskItem,
  DownloadFailureItem,
  DownloadedVideoItem,
  CrawlAndImportRequest,
  BatchImportResult,
  TaskPageResult,
  FailurePageResult,
  VideoPageResult,
  CrawlImportStatus
} from '@/types/download'

// ============ 任务管理 ============

/**
 * 创建下载任务
 * POST /download/tasks
 * JWT 认证，body: resource_url, resource_type, video_id?, liveroom_id?
 */
export const createTask = (
  data: DownloadTaskCreate
): Promise<ApiResponse<DownloadTaskItem>> => {
  return request.post(API_PATHS.DOWNLOAD.TASKS, data, { loading: true, loadingText: '创建中...' })
}

/**
 * 获取任务列表（分页+状态筛选）
 * GET /download/tasks
 * JWT 认证，Query: page?, page_size?, status?
 */
export const getTasks = (params?: {
  page?: number
  page_size?: number
  status?: string
}): Promise<ApiResponse<TaskPageResult>> => {
  return request.get(API_PATHS.DOWNLOAD.TASKS, { data: params })
}

/**
 * 获取任务详情
 * GET /download/tasks/{taskId}
 * JWT 认证
 */
export const getTask = (taskId: string): Promise<ApiResponse<DownloadTaskItem>> => {
  return request.get(API_PATHS.DOWNLOAD.TASK_DETAIL(taskId))
}

/**
 * 更新任务
 * PUT /download/tasks/{taskId}
 * JWT 认证，body: video_id?, liveroom_id?
 */
export const updateTask = (
  taskId: string,
  data: Partial<DownloadTaskCreate>
): Promise<ApiResponse<DownloadTaskItem>> => {
  return request.put(API_PATHS.DOWNLOAD.TASK_DETAIL(taskId), data)
}

/**
 * 删除任务（物理删除，级联删除关联失败记录）
 * DELETE /download/tasks/{taskId}
 * JWT 认证
 */
export const deleteTask = (taskId: string): Promise<ApiResponse<null>> => {
  return request.delete(API_PATHS.DOWNLOAD.TASK_DETAIL(taskId), { loading: true, loadingText: '删除中...' })
}

/**
 * 启动下载
 * POST /download/tasks/{taskId}/start
 * JWT 认证，异步执行（Celery Worker）
 */
export const startTask = (taskId: string): Promise<ApiResponse<null>> => {
  return request.post(API_PATHS.DOWNLOAD.TASK_START(taskId), undefined, { loading: true, loadingText: '启动中...' })
}

/**
 * 重试下载
 * POST /download/tasks/{taskId}/retry
 * JWT 认证
 */
export const retryTask = (taskId: string): Promise<ApiResponse<null>> => {
  return request.post(API_PATHS.DOWNLOAD.TASK_RETRY(taskId), undefined, { loading: true, loadingText: '重试中...' })
}

// ============ 失败记录 ============

/**
 * 获取任务失败记录（分页）
 * GET /download/tasks/{taskId}/failures
 * JWT 认证，Query: page?, page_size?, status?
 */
export const getTaskFailures = (
  taskId: string,
  params?: { page?: number; page_size?: number; status?: string }
): Promise<ApiResponse<FailurePageResult>> => {
  return request.get(API_PATHS.DOWNLOAD.TASK_FAILURES(taskId), { data: params })
}

/**
 * 重试单条失败记录
 * POST /download/tasks/{taskId}/failures/{failureId}/retry
 * JWT 认证
 */
export const retryFailure = (
  taskId: string,
  failureId: string
): Promise<ApiResponse<null>> => {
  return request.post(API_PATHS.DOWNLOAD.FAILURE_RETRY(taskId, failureId))
}

/**
 * 放弃单条失败记录
 * POST /download/tasks/{taskId}/failures/{failureId}/abandon
 * JWT 认证
 */
export const abandonFailure = (
  taskId: string,
  failureId: string
): Promise<ApiResponse<null>> => {
  return request.post(API_PATHS.DOWNLOAD.FAILURE_ABANDON(taskId, failureId))
}

// ============ 视频记录 ============

/**
 * 获取任务已下载视频
 * GET /download/tasks/{taskId}/videos
 * JWT 认证
 */
export const getTaskVideos = (
  taskId: string
): Promise<ApiResponse<{ items: DownloadedVideoItem[] }>> => {
  return request.get(API_PATHS.DOWNLOAD.TASK_VIDEOS(taskId))
}

/**
 * 获取全局已下载视频列表（分页）
 * GET /download/videos
 * JWT 认证，Query: page?, page_size?
 */
export const getVideos = (params?: {
  page?: number
  page_size?: number
}): Promise<ApiResponse<VideoPageResult>> => {
  return request.get(API_PATHS.DOWNLOAD.VIDEOS, { data: params })
}

/**
 * 获取视频详情
 * GET /download/videos/{videoId}
 * JWT 认证
 */
export const getVideo = (videoId: string): Promise<ApiResponse<DownloadedVideoItem>> => {
  return request.get(API_PATHS.DOWNLOAD.VIDEO_DETAIL(videoId))
}

// ============ 批量导入 ============

/**
 * CSV 批量导入
 * POST /download/tasks/batch-import
 * JWT 认证，multipart/form-data
 * @param filePath uni.chooseFile 返回的临时文件路径
 */
export const batchImport = (filePath: string): Promise<ApiResponse<BatchImportResult>> => {
  return request.upload({
    url: API_PATHS.DOWNLOAD.BATCH_IMPORT,
    filePath,
    name: 'file',
    loading: true,
    loadingText: '导入中...'
  })
}

/**
 * 爬取并导入
 * POST /download/tasks/crawl-and-import
 * JWT 认证，body: source_url
 */
export const crawlAndImport = (
  data: CrawlAndImportRequest
): Promise<ApiResponse<null>> => {
  return request.post(API_PATHS.DOWNLOAD.CRAWL_IMPORT, data, { loading: true, loadingText: '提交中...' })
}

/**
 * 查询爬取导入状态
 * GET /download/tasks/crawl-import-status
 * JWT 认证
 */
export const getCrawlImportStatus = (): Promise<ApiResponse<CrawlImportStatus>> => {
  return request.get(API_PATHS.DOWNLOAD.CRAWL_STATUS, { showError: false })
}
```

---

## 五、config/api.ts 路径配置

> 以下为 DOWNLOAD 模块在 `src/config/api.ts` 中的配置，已存在于当前代码中

```typescript
// src/config/api.ts 中 DOWNLOAD 模块

DOWNLOAD: {
  // 任务管理
  TASKS: '/download/tasks',
  TASK_DETAIL: (taskId: string) => `/download/tasks/${taskId}`,
  TASK_START: (taskId: string) => `/download/tasks/${taskId}/start`,
  TASK_RETRY: (taskId: string) => `/download/tasks/${taskId}/retry`,
  TASK_FAILURES: (taskId: string) => `/download/tasks/${taskId}/failures`,
  TASK_VIDEOS: (taskId: string) => `/download/tasks/${taskId}/videos`,
  FAILURE_RETRY: (taskId: string, failureId: string) => `/download/tasks/${taskId}/failures/${failureId}/retry`,
  FAILURE_ABANDON: (taskId: string, failureId: string) => `/download/tasks/${taskId}/failures/${failureId}/abandon`,
  // 视频库
  VIDEOS: '/download/videos',
  VIDEO_DETAIL: (videoId: string) => `/download/videos/${videoId}`,
  // 批量导入
  BATCH_IMPORT: '/download/tasks/batch-import',
  CRAWL_IMPORT: '/download/tasks/crawl-and-import',
  CRAWL_STATUS: '/download/tasks/crawl-import-status'
}
```

> **说明**：当前 `API_BASE_MAP` 中 DOWNLOAD 映射到 `core` 服务。由于下载服务是独立微服务（端口 8001），需在环境变量中配置 `VITE_DOWNLOAD_API_URL`，并在 `API_BASE_MAP` 中独立映射：

```typescript
// src/config/api.ts 中需追加的配置

const DOWNLOAD_API_BASE_URL = resolveGatewayBaseURL(
  import.meta.env?.VITE_DOWNLOAD_API_URL,
  'http://localhost:8080/api/core' // 默认走网关
)

// API_BASE_MAP 中修改：
// DOWNLOAD: { baseType: 'core', baseURL: DOWNLOAD_API_BASE_URL }
```

---

## 六、管理端页面

### 6.1 下载任务列表页 TaskList.vue

```vue
<!-- src/pages/admin/download/TaskList.vue -->
<template>
  <view class="task-list-page">
    <!-- 顶部操作栏 -->
    <view class="page-header">
      <text class="header-title">下载任务管理</text>
      <view class="header-actions">
        <view class="action-btn action-btn--secondary" @click="goBatchImport">
          <text class="action-text">批量导入</text>
        </view>
        <view class="action-btn action-btn--primary" @click="goCreate">
          <text class="action-text">+ 新建任务</text>
        </view>
      </view>
    </view>

    <!-- 状态筛选 -->
    <scroll-view class="filter-scroll" scroll-x>
      <view class="filter-tabs">
        <view
          v-for="tab in statusTabs"
          :key="tab.value"
          :class="['filter-tab', { active: statusFilter === tab.value }]"
          @click="handleFilterChange(tab.value)"
        >
          <text class="tab-text">{{ tab.label }}</text>
        </view>
      </view>
    </scroll-view>

    <!-- 加载态 -->
    <view v-if="loading" class="loading-state">
      <text class="loading-text">加载中...</text>
    </view>

    <!-- 错误态 -->
    <view v-else-if="errorMsg" class="error-state">
      <text class="error-text">{{ errorMsg }}</text>
      <view class="retry-btn" @click="fetchData">
        <text class="retry-text">重试</text>
      </view>
    </view>

    <!-- 空态 -->
    <view v-else-if="tasks.length === 0" class="empty-state">
      <text class="empty-text">暂无下载任务</text>
    </view>

    <!-- 任务列表 -->
    <view v-else class="task-list">
      <view
        v-for="task in tasks"
        :key="task.id"
        class="task-item"
        @click="goDetail(task.id)"
      >
        <view class="task-header">
          <view :class="['status-tag', `status-${task.status}`]">
            <text class="status-text">{{ statusLabelMap[task.status] }}</text>
          </view>
          <text class="task-type">{{ task.resource_type.toUpperCase() }}</text>
        </view>

        <text class="task-url">{{ truncateUrl(task.resource_url) }}</text>

        <!-- 进度条 -->
        <view v-if="task.status === 'processing' || task.status === 'completed'" class="progress-bar-wrap">
          <view class="progress-bar">
            <view class="progress-fill" :style="{ width: task.progress + '%' }" />
          </view>
          <text class="progress-text">{{ task.progress.toFixed(1) }}%</text>
        </view>

        <!-- 分片信息 -->
        <view v-if="task.total_segments > 0" class="segment-info">
          <text class="segment-text">
            {{ task.downloaded_segments }}/{{ task.total_segments }}
          </text>
          <text v-if="task.failed_segments > 0" class="segment-failed">
            失败 {{ task.failed_segments }}
          </text>
        </view>

        <view class="task-footer">
          <text class="task-time">{{ formatTime(task.created_at) }}</text>
          <view class="task-actions" @click.stop>
            <view
              v-if="task.status === 'pending'"
              class="mini-btn mini-btn--success"
              @click="handleStart(task.id)"
            >
              <text class="mini-text">启动</text>
            </view>
            <view
              v-if="task.status === 'failed' || task.status === 'partial_completed'"
              class="mini-btn mini-btn--warning"
              @click="handleRetry(task.id)"
            >
              <text class="mini-text">重试</text>
            </view>
            <view
              class="mini-btn mini-btn--danger"
              @click="handleDelete(task)"
            >
              <text class="mini-text">删除</text>
            </view>
          </view>
        </view>
      </view>
    </view>

    <!-- 分页 -->
    <view v-if="total > pageSize" class="pagination">
      <view
        class="page-btn"
        :class="{ disabled: currentPage <= 1 }"
        @click="changePage(currentPage - 1)"
      >
        <text>上一页</text>
      </view>
      <text class="page-info">{{ currentPage }} / {{ totalPages }}</text>
      <view
        class="page-btn"
        :class="{ disabled: currentPage >= totalPages }"
        @click="changePage(currentPage + 1)"
      >
        <text>下一页</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { getTasks, startTask, retryTask, deleteTask } from '@/api/download'
import type { DownloadTaskItem, TaskStatus } from '@/types/download'

const tasks = ref<DownloadTaskItem[]>([])
const loading = ref(false)
const errorMsg = ref<string | null>(null)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const statusFilter = ref('')

const totalPages = computed(() => Math.ceil(total.value / pageSize.value))

const statusTabs = [
  { label: '全部', value: '' },
  { label: '待处理', value: 'pending' },
  { label: '下载中', value: 'processing' },
  { label: '已完成', value: 'completed' },
  { label: '部分完成', value: 'partial_completed' },
  { label: '失败', value: 'failed' },
  { label: '已取消', value: 'cancelled' }
]

const statusLabelMap: Record<string, string> = {
  pending: '待处理',
  processing: '下载中',
  completed: '已完成',
  partial_completed: '部分完成',
  failed: '失败',
  cancelled: '已取消'
}

/** 处理中的任务自动轮询刷新 */
let pollTimer: ReturnType<typeof setInterval> | null = null

function startPolling() {
  stopPolling()
  pollTimer = setInterval(() => {
    const hasProcessing = tasks.value.some(t => t.status === 'processing')
    if (hasProcessing) {
      fetchData()
    }
  }, 5000)
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

function truncateUrl(url: string): string {
  return url.length > 60 ? url.slice(0, 60) + '...' : url
}

function formatTime(isoStr: string): string {
  try {
    const d = new Date(isoStr)
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
  } catch {
    return isoStr
  }
}

async function fetchData() {
  loading.value = tasks.value.length === 0 // 非首次不显示全屏 loading
  errorMsg.value = null
  try {
    const res = await getTasks({
      page: currentPage.value,
      page_size: pageSize.value,
      status: statusFilter.value || undefined
    })
    if (res.code === 200 && res.data) {
      tasks.value = res.data.items
      total.value = res.data.total
      // 如果有处理中的任务，启动轮询
      if (tasks.value.some(t => t.status === 'processing')) {
        startPolling()
      } else {
        stopPolling()
      }
    }
  } catch (err: any) {
    errorMsg.value = err.message || '加载任务列表失败'
  } finally {
    loading.value = false
  }
}

function handleFilterChange(value: string) {
  statusFilter.value = value
  currentPage.value = 1
  fetchData()
}

function changePage(page: number) {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  fetchData()
}

function goCreate() {
  uni.navigateTo({ url: '/pages/admin/download/TaskCreateForm' })
}

function goBatchImport() {
  uni.navigateTo({ url: '/pages/admin/download/BatchImport' })
}

function goDetail(taskId: string) {
  uni.navigateTo({ url: `/pages/admin/download/TaskDetail?taskId=${taskId}` })
}

async function handleStart(taskId: string) {
  try {
    await startTask(taskId)
    uni.showToast({ title: '任务已启动', icon: 'success' })
    fetchData()
  } catch (err: any) {
    uni.showToast({ title: err.message || '启动失败', icon: 'none' })
  }
}

async function handleRetry(taskId: string) {
  try {
    await retryTask(taskId)
    uni.showToast({ title: '重试已启动', icon: 'success' })
    fetchData()
  } catch (err: any) {
    uni.showToast({ title: err.message || '重试失败', icon: 'none' })
  }
}

async function handleDelete(task: DownloadTaskItem) {
  uni.showModal({
    title: '确认删除',
    content: '确定删除此下载任务吗？关联的失败记录将一并删除。',
    success: async (res) => {
      if (res.confirm) {
        try {
          await deleteTask(task.id)
          uni.showToast({ title: '删除成功', icon: 'success' })
          fetchData()
        } catch (err: any) {
          uni.showToast({ title: err.message || '删除失败', icon: 'none' })
        }
      }
    }
  })
}

onMounted(() => fetchData())
onUnmounted(() => stopPolling())
</script>

<style lang="scss" scoped>
.task-list-page {
  min-height: 100vh;
  background: var(--color-background);
  padding: var(--spacing-md);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-md);
}

.header-title {
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--color-text-primary);
}

.header-actions {
  display: flex;
  gap: var(--spacing-sm);
}

.action-btn {
  padding: var(--spacing-xs) var(--spacing-md);
  border-radius: var(--border-radius-base);
}

.action-btn--primary { background: var(--color-primary); }
.action-btn--secondary { background: var(--color-bg-secondary); border: 1px solid var(--color-border); }

.action-text {
  font-size: var(--font-size-sm);
  color: #fff;
}

.action-btn--secondary .action-text { color: var(--color-text-primary); }

.filter-scroll {
  white-space: nowrap;
  margin-bottom: var(--spacing-md);
}

.filter-tabs {
  display: inline-flex;
  gap: var(--spacing-xs);
}

.filter-tab {
  padding: var(--spacing-xs) var(--spacing-md);
  background: var(--color-card);
  border-radius: var(--border-radius-base);
  display: inline-block;
}

.filter-tab.active {
  background: var(--color-primary);
}

.filter-tab.active .tab-text { color: #fff; }

.tab-text {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  white-space: nowrap;
}

.task-item {
  padding: var(--spacing-md);
  background: var(--color-card);
  border-radius: var(--border-radius-base);
  margin-bottom: var(--spacing-sm);
}

.task-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-xs);
}

.status-tag {
  padding: 2px 8px;
  border-radius: var(--border-radius-sm);
}

.status-pending { background: #e6f7ff; }
.status-processing { background: #fff7e6; }
.status-completed { background: #f6ffed; }
.status-partial_completed { background: #fff7e6; }
.status-failed { background: #fff2f0; }
.status-cancelled { background: #f5f5f5; }

.status-text { font-size: var(--font-size-xs); }

.task-type {
  font-size: var(--font-size-xs);
  color: var(--color-text-hint);
  font-family: monospace;
}

.task-url {
  font-size: var(--font-size-xs);
  color: var(--color-primary);
  font-family: monospace;
  word-break: break-all;
  margin-bottom: var(--spacing-sm);
}

.progress-bar-wrap {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-xs);
}

.progress-bar {
  flex: 1;
  height: 8px;
  background: var(--color-bg-secondary);
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--color-primary);
  border-radius: 4px;
  transition: width 0.3s;
}

.progress-text {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  min-width: 60px;
  text-align: right;
}

.segment-info {
  display: flex;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-xs);
}

.segment-text {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

.segment-failed {
  font-size: var(--font-size-xs);
  color: var(--color-danger);
}

.task-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: var(--spacing-sm);
}

.task-time {
  font-size: var(--font-size-xs);
  color: var(--color-text-hint);
}

.task-actions {
  display: flex;
  gap: var(--spacing-xs);
}

.mini-btn {
  padding: 2px 8px;
  border-radius: var(--border-radius-sm);
}

.mini-btn--success { background: #f6ffed; border: 1px solid #b7eb8f; }
.mini-btn--warning { background: #fff7e6; border: 1px solid #ffd591; }
.mini-btn--danger { background: #fff2f0; border: 1px solid #ffa39e; }

.mini-text { font-size: var(--font-size-xs); }

.mini-btn--success .mini-text { color: #52c41a; }
.mini-btn--warning .mini-text { color: #fa8c16; }
.mini-btn--danger .mini-text { color: #f5222d; }

.empty-state, .loading-state, .error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60px 0;
}

.empty-text, .loading-text, .error-text {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.retry-btn {
  margin-top: var(--spacing-md);
  padding: var(--spacing-sm) var(--spacing-lg);
  background: var(--color-primary);
  border-radius: var(--border-radius-base);
}

.retry-text { color: #fff; font-size: var(--font-size-sm); }

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-md);
  margin-top: var(--spacing-lg);
}

.page-btn {
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-card);
  border-radius: var(--border-radius-base);
}

.page-btn.disabled { opacity: 0.5; }

.page-info {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}
</style>
```

### 6.2 新建任务页 TaskCreateForm.vue

```vue
<!-- src/pages/admin/download/TaskCreateForm.vue -->
<template>
  <view class="create-task-page">
    <view class="form-card">
      <text class="form-title">新建下载任务</text>

      <!-- 资源 URL -->
      <view class="form-item">
        <text class="form-label">资源 URL <text class="required">*</text></text>
        <input
          v-model="formData.resource_url"
          class="form-input"
          placeholder="https://example.com/video.m3u8"
          maxlength="2000"
        />
        <text v-if="errors.resource_url" class="form-error">{{ errors.resource_url }}</text>
      </view>

      <!-- 资源类型 -->
      <view class="form-item">
        <text class="form-label">资源类型 <text class="required">*</text></text>
        <picker
          :range="resourceTypeOptions"
          range-key="label"
          :value="resourceTypeIndex"
          @change="handleTypeChange"
        >
          <view class="picker-btn">
            <text>{{ resourceTypeOptions[resourceTypeIndex].label }}</text>
          </view>
        </picker>
      </view>

      <!-- 关联视频 ID -->
      <view class="form-item">
        <text class="form-label">关联视频 ID（可选）</text>
        <input
          v-model="formData.video_id"
          class="form-input"
          placeholder="视频 ID"
          maxlength="200"
        />
      </view>

      <!-- 关联直播间 ID -->
      <view class="form-item">
        <text class="form-label">关联直播间 ID（可选）</text>
        <input
          v-model="formData.liveroom_id"
          class="form-input"
          placeholder="直播间 ID"
          maxlength="200"
        />
      </view>

      <!-- 提交按钮 -->
      <view
        class="submit-btn"
        :class="{ disabled: submitting }"
        @click="handleSubmit"
      >
        <text class="submit-text">{{ submitting ? '创建中...' : '创建任务' }}</text>
      </view>

      <!-- 错误提示 -->
      <view v-if="errorMsg" class="error-banner">
        <text class="error-text">{{ errorMsg }}</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { createTask } from '@/api/download'
import type { ResourceTypeEnum } from '@/types/download'

const submitting = ref(false)
const errorMsg = ref<string | null>(null)

const resourceTypeOptions = [
  { label: 'M3U8 (HLS)', value: 'm3u8' },
  { label: 'MP4', value: 'mp4' },
  { label: 'Image', value: 'image' }
]
const resourceTypeIndex = ref(0)

const formData = reactive({
  resource_url: '',
  resource_type: 'm3u8' as ResourceTypeEnum,
  video_id: '',
  liveroom_id: ''
})

const errors = reactive({
  resource_url: ''
})

function handleTypeChange(e: any) {
  resourceTypeIndex.value = e.detail.value
  formData.resource_type = resourceTypeOptions[e.detail.value].value as ResourceTypeEnum
}

function validate(): boolean {
  errors.resource_url = ''

  if (!formData.resource_url) {
    errors.resource_url = '请输入资源 URL'
    return false
  }
  if (!formData.resource_url.startsWith('http://') && !formData.resource_url.startsWith('https://')) {
    errors.resource_url = 'URL 必须以 http:// 或 https:// 开头'
    return false
  }
  return true
}

async function handleSubmit() {
  errorMsg.value = null
  if (!validate()) return

  submitting.value = true
  try {
    await createTask({
      resource_url: formData.resource_url,
      resource_type: formData.resource_type,
      video_id: formData.video_id || undefined,
      liveroom_id: formData.liveroom_id || undefined
    })
    uni.showToast({ title: '任务创建成功', icon: 'success' })
    setTimeout(() => {
      uni.navigateBack({ delta: 1 })
    }, 500)
  } catch (err: any) {
    errorMsg.value = err.message || '创建失败'
  } finally {
    submitting.value = false
  }
}
</script>

<style lang="scss" scoped>
.create-task-page {
  min-height: 100vh;
  background: var(--color-background);
  padding: var(--spacing-lg);
}

.form-card {
  padding: var(--spacing-lg);
  background: var(--color-card);
  border-radius: var(--border-radius-lg);
}

.form-title {
  display: block;
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-xl);
}

.form-item {
  margin-bottom: var(--spacing-lg);
}

.form-label {
  display: block;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-xs);
}

.required { color: var(--color-danger); }

.form-input {
  width: 100%;
  padding: var(--spacing-md);
  background: var(--color-bg-secondary);
  border-radius: var(--border-radius-base);
  font-size: var(--font-size-base);
}

.form-error {
  font-size: var(--font-size-xs);
  color: var(--color-danger);
  margin-top: var(--spacing-xs);
  display: block;
}

.picker-btn {
  padding: var(--spacing-md);
  background: var(--color-bg-secondary);
  border-radius: var(--border-radius-base);
  font-size: var(--font-size-base);
}

.submit-btn {
  margin-top: var(--spacing-xl);
  padding: var(--spacing-md);
  background: var(--color-primary);
  border-radius: var(--border-radius-base);
  text-align: center;
}

.submit-btn.disabled { opacity: 0.6; }

.submit-text { color: #fff; font-size: var(--font-size-base); font-weight: 500; }

.error-banner {
  margin-top: var(--spacing-md);
  padding: var(--spacing-sm) var(--spacing-md);
  background: #fff2f0;
  border-radius: var(--border-radius-sm);
}

.error-text { font-size: var(--font-size-sm); color: var(--color-danger); }
</style>
```

### 6.3 任务详情页 TaskDetail.vue

```vue
<!-- src/pages/admin/download/TaskDetail.vue -->
<template>
  <view class="task-detail-page">
    <!-- 加载态 -->
    <view v-if="loading" class="loading-state">
      <text class="loading-text">加载中...</text>
    </view>

    <!-- 错误态 -->
    <view v-else-if="errorMsg" class="error-state">
      <text class="error-text">{{ errorMsg }}</text>
      <view class="retry-btn" @click="loadDetail">
        <text class="retry-text">重试</text>
      </view>
    </view>

    <!-- 任务详情 -->
    <view v-else-if="task" class="detail-content">
      <!-- 基本信息 -->
      <view class="section-card">
        <text class="section-title">基本信息</text>
        <view class="info-row">
          <text class="info-label">任务 ID</text>
          <text class="info-value mono">{{ task.id }}</text>
        </view>
        <view class="info-row">
          <text class="info-label">资源 URL</text>
          <text class="info-value mono url-text">{{ task.resource_url }}</text>
        </view>
        <view class="info-row">
          <text class="info-label">资源类型</text>
          <text class="info-value">{{ task.resource_type.toUpperCase() }}</text>
        </view>
        <view class="info-row">
          <text class="info-label">状态</text>
          <view :class="['status-tag', `status-${task.status}`]">
            <text class="status-text">{{ statusLabelMap[task.status] }}</text>
          </view>
        </view>
        <view class="info-row">
          <text class="info-label">进度</text>
          <view class="progress-inline">
            <view class="progress-bar">
              <view class="progress-fill" :style="{ width: task.progress + '%' }" />
            </view>
            <text class="progress-num">{{ task.progress.toFixed(1) }}%</text>
          </view>
        </view>
        <view v-if="task.total_segments > 0" class="info-row">
          <text class="info-label">分片信息</text>
          <text class="info-value">
            总计 {{ task.total_segments }} / 已下载 {{ task.downloaded_segments }} / 失败 {{ task.failed_segments }}
          </text>
        </view>
        <view v-if="task.storage_path" class="info-row">
          <text class="info-label">存储路径</text>
          <text class="info-value mono">{{ task.storage_path }}</text>
        </view>
        <view v-if="task.error_message" class="info-row">
          <text class="info-label">错误信息</text>
          <text class="info-value error-msg">{{ task.error_message }}</text>
        </view>
        <view class="info-row">
          <text class="info-label">创建时间</text>
          <text class="info-value">{{ formatTime(task.created_at) }}</text>
        </view>
        <view v-if="task.video_id" class="info-row">
          <text class="info-label">关联视频</text>
          <text class="info-value">{{ task.video_id }}</text>
        </view>
        <view v-if="task.liveroom_id" class="info-row">
          <text class="info-label">关联直播间</text>
          <text class="info-value">{{ task.liveroom_id }}</text>
        </view>
      </view>

      <!-- 操作按钮 -->
      <view class="action-bar">
        <view
          v-if="task.status === 'pending'"
          class="action-btn action-btn--primary"
          @click="handleStart"
        >
          <text class="action-text">启动下载</text>
        </view>
        <view
          v-if="task.status === 'failed' || task.status === 'partial_completed'"
          class="action-btn action-btn--warning"
          @click="handleRetry"
        >
          <text class="action-text">重试下载</text>
        </view>
      </view>

      <!-- 处理中轮询提示 -->
      <view v-if="task.status === 'processing'" class="polling-banner">
        <text class="polling-text">正在下载中，自动刷新进度...</text>
      </view>

      <!-- 失败记录 -->
      <view class="section-card">
        <text class="section-title">失败记录 ({{ failures.length }})</text>

        <view v-if="failures.length === 0" class="section-empty">
          <text class="section-empty-text">暂无失败记录</text>
        </view>

        <view v-else class="failure-list">
          <view
            v-for="failure in failures"
            :key="failure.id"
            class="failure-item"
          >
            <view class="failure-header">
              <view :class="['failure-type-tag', `ft-${failure.failure_type}`]">
                <text class="failure-type-text">{{ failureTypeLabelMap[failure.failure_type] }}</text>
              </view>
              <view :class="['failure-status-tag', `fs-${failure.status}`]">
                <text class="failure-status-text">{{ failureStatusLabelMap[failure.status] }}</text>
              </view>
            </view>
            <text v-if="failure.segment_url" class="failure-url mono">{{ truncateUrl(failure.segment_url) }}</text>
            <text v-if="failure.error_message" class="failure-error">{{ failure.error_message }}</text>
            <text class="failure-retry">重试次数: {{ failure.retry_count }}</text>

            <view class="failure-actions">
              <view
                v-if="failure.status !== 'abandoned'"
                class="mini-btn mini-btn--warning"
                @click="handleRetryFailure(failure.id)"
              >
                <text class="mini-text">重试</text>
              </view>
              <view
                v-if="failure.status !== 'abandoned'"
                class="mini-btn mini-btn--danger"
                @click="handleAbandonFailure(failure.id)"
              >
                <text class="mini-text">放弃</text>
              </view>
            </view>
          </view>
        </view>
      </view>

      <!-- 已下载视频 -->
      <view class="section-card">
        <text class="section-title">已下载视频 ({{ videos.length }})</text>

        <view v-if="videos.length === 0" class="section-empty">
          <text class="section-empty-text">暂无已下载视频</text>
        </view>

        <view v-else class="video-list">
          <view
            v-for="video in videos"
            :key="video.id"
            class="video-item"
          >
            <text class="video-url mono">{{ video.video_url || '-' }}</text>
            <view class="video-meta">
              <text v-if="video.format" class="meta-tag">{{ video.format }}</text>
              <text v-if="video.resolution" class="meta-tag">{{ video.resolution }}</text>
              <text v-if="video.file_size" class="meta-tag">{{ formatFileSize(video.file_size) }}</text>
              <text v-if="video.duration" class="meta-tag">{{ formatDuration(video.duration) }}</text>
            </view>
            <text class="video-path mono">{{ video.storage_path }}</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import {
  getTask,
  getTaskFailures,
  getTaskVideos,
  startTask,
  retryTask,
  retryFailure,
  abandonFailure
} from '@/api/download'
import type { DownloadTaskItem, DownloadFailureItem, DownloadedVideoItem } from '@/types/download'

const loading = ref(false)
const errorMsg = ref<string | null>(null)
const task = ref<DownloadTaskItem | null>(null)
const failures = ref<DownloadFailureItem[]>([])
const videos = ref<DownloadedVideoItem[]>([])

let taskId = ''
let pollTimer: ReturnType<typeof setInterval> | null = null

const statusLabelMap: Record<string, string> = {
  pending: '待处理',
  processing: '下载中',
  completed: '已完成',
  partial_completed: '部分完成',
  failed: '失败',
  cancelled: '已取消'
}

const failureTypeLabelMap: Record<string, string> = {
  network_error: '网络错误',
  timeout: '超时',
  invalid_content: '无效内容',
  storage_error: '存储错误',
  permission_error: '权限错误'
}

const failureStatusLabelMap: Record<string, string> = {
  pending: '待重试',
  retrying: '重试中',
  abandoned: '已放弃'
}

function truncateUrl(url: string): string {
  return url.length > 80 ? url.slice(0, 80) + '...' : url
}

function formatTime(isoStr: string): string {
  try {
    const d = new Date(isoStr)
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
  } catch {
    return isoStr
  }
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  if (bytes < 1024 * 1024 * 1024) return (bytes / 1024 / 1024).toFixed(1) + ' MB'
  return (bytes / 1024 / 1024 / 1024).toFixed(2) + ' GB'
}

function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  return `${m}:${String(s).padStart(2, '0')}`
}

async function loadDetail() {
  if (!taskId) return
  loading.value = !task.value // 非首次不显示全屏 loading
  errorMsg.value = null
  try {
    const [taskRes, failuresRes, videosRes] = await Promise.all([
      getTask(taskId),
      getTaskFailures(taskId),
      getTaskVideos(taskId)
    ])
    if (taskRes.code === 200 && taskRes.data) {
      task.value = taskRes.data
      // 如果正在处理中，启动轮询
      if (task.value.status === 'processing') {
        startPolling()
      } else {
        stopPolling()
      }
    }
    if (failuresRes.code === 200 && failuresRes.data) {
      failures.value = failuresRes.data.items
    }
    if (videosRes.code === 200 && videosRes.data) {
      videos.value = videosRes.data.items
    }
  } catch (err: any) {
    errorMsg.value = err.message || '加载详情失败'
  } finally {
    loading.value = false
  }
}

function startPolling() {
  stopPolling()
  pollTimer = setInterval(async () => {
    try {
      const res = await getTask(taskId)
      if (res.code === 200 && res.data) {
        task.value = res.data
        if (['completed', 'failed', 'cancelled', 'partial_completed'].includes(res.data.status)) {
          stopPolling()
          loadDetail() // 刷新失败记录和视频列表
        }
      }
    } catch {
      stopPolling()
    }
  }, 3000)
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

async function handleStart() {
  try {
    await startTask(taskId)
    uni.showToast({ title: '任务已启动', icon: 'success' })
    loadDetail()
  } catch (err: any) {
    uni.showToast({ title: err.message || '启动失败', icon: 'none' })
  }
}

async function handleRetry() {
  try {
    await retryTask(taskId)
    uni.showToast({ title: '重试已启动', icon: 'success' })
    loadDetail()
  } catch (err: any) {
    uni.showToast({ title: err.message || '重试失败', icon: 'none' })
  }
}

async function handleRetryFailure(failureId: string) {
  try {
    await retryFailure(taskId, failureId)
    uni.showToast({ title: '重试已启动', icon: 'success' })
    loadDetail()
  } catch (err: any) {
    uni.showToast({ title: err.message || '重试失败', icon: 'none' })
  }
}

async function handleAbandonFailure(failureId: string) {
  uni.showModal({
    title: '确认放弃',
    content: '确定放弃该失败分段吗？',
    success: async (res) => {
      if (res.confirm) {
        try {
          await abandonFailure(taskId, failureId)
          uni.showToast({ title: '已放弃', icon: 'success' })
          loadDetail()
        } catch (err: any) {
          uni.showToast({ title: err.message || '操作失败', icon: 'none' })
        }
      }
    }
  })
}

onMounted(() => {
  // 从页面参数获取 taskId
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1]
  const options = (currentPage as any)?.$page?.options || (currentPage as any)?.options || {}
  taskId = options.taskId || ''
  if (taskId) {
    loadDetail()
  } else {
    errorMsg.value = '缺少任务 ID'
  }
})

onUnmounted(() => stopPolling())
</script>

<style lang="scss" scoped>
.task-detail-page {
  min-height: 100vh;
  background: var(--color-background);
  padding: var(--spacing-md);
}

.section-card {
  padding: var(--spacing-md);
  background: var(--color-card);
  border-radius: var(--border-radius-base);
  margin-bottom: var(--spacing-md);
}

.section-title {
  display: block;
  font-size: var(--font-size-base);
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-md);
}

.info-row {
  display: flex;
  align-items: flex-start;
  margin-bottom: var(--spacing-sm);
}

.info-label {
  width: 160rpx;
  flex-shrink: 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.info-value {
  flex: 1;
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
  word-break: break-all;
}

.mono { font-family: monospace; font-size: var(--font-size-xs); }
.url-text { color: var(--color-primary); }
.error-msg { color: var(--color-danger); }

.status-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: var(--border-radius-sm);
}

.status-pending { background: #e6f7ff; }
.status-processing { background: #fff7e6; }
.status-completed { background: #f6ffed; }
.status-partial_completed { background: #fff7e6; }
.status-failed { background: #fff2f0; }
.status-cancelled { background: #f5f5f5; }

.status-text { font-size: var(--font-size-xs); }

.progress-inline {
  flex: 1;
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.progress-bar {
  flex: 1;
  height: 8px;
  background: var(--color-bg-secondary);
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--color-primary);
  border-radius: 4px;
}

.progress-num {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  min-width: 80rpx;
  text-align: right;
}

.action-bar {
  display: flex;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-md);
}

.action-btn {
  flex: 1;
  padding: var(--spacing-md);
  border-radius: var(--border-radius-base);
  text-align: center;
}

.action-btn--primary { background: var(--color-primary); }
.action-btn--warning { background: #fa8c16; }
.action-text { color: #fff; font-size: var(--font-size-base); }

.polling-banner {
  padding: var(--spacing-sm) var(--spacing-md);
  background: #fff7e6;
  border-radius: var(--border-radius-sm);
  margin-bottom: var(--spacing-md);
  text-align: center;
}

.polling-text { font-size: var(--font-size-sm); color: #fa8c16; }

.section-empty {
  padding: var(--spacing-lg) 0;
  text-align: center;
}

.section-empty-text { font-size: var(--font-size-sm); color: var(--color-text-hint); }

.failure-item {
  padding: var(--spacing-md);
  background: var(--color-bg-secondary);
  border-radius: var(--border-radius-sm);
  margin-bottom: var(--spacing-sm);
}

.failure-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-xs);
}

.failure-type-tag, .failure-status-tag {
  padding: 2px 8px;
  border-radius: var(--border-radius-sm);
}

.ft-network_error { background: #fff2f0; }
.ft-timeout { background: #fff7e6; }
.ft-invalid_content { background: #f5f5f5; }
.ft-storage_error { background: #fff2f0; }
.ft-permission_error { background: #fff2f0; }

.failure-type-text { font-size: var(--font-size-xs); color: var(--color-danger); }

.fs-pending { background: #e6f7ff; }
.fs-retrying { background: #fff7e6; }
.fs-abandoned { background: #f5f5f5; }

.failure-status-text { font-size: var(--font-size-xs); color: var(--color-text-secondary); }

.failure-url {
  font-size: var(--font-size-xs);
  color: var(--color-primary);
  word-break: break-all;
  margin-bottom: var(--spacing-xs);
  display: block;
}

.failure-error {
  font-size: var(--font-size-xs);
  color: var(--color-danger);
  margin-bottom: var(--spacing-xs);
  display: block;
}

.failure-retry {
  font-size: var(--font-size-xs);
  color: var(--color-text-hint);
  display: block;
  margin-bottom: var(--spacing-sm);
}

.failure-actions {
  display: flex;
  gap: var(--spacing-xs);
}

.mini-btn {
  padding: 2px 8px;
  border-radius: var(--border-radius-sm);
}

.mini-btn--warning { background: #fff7e6; border: 1px solid #ffd591; }
.mini-btn--danger { background: #fff2f0; border: 1px solid #ffa39e; }

.mini-text { font-size: var(--font-size-xs); }
.mini-btn--warning .mini-text { color: #fa8c16; }
.mini-btn--danger .mini-text { color: #f5222d; }

.video-item {
  padding: var(--spacing-md);
  background: var(--color-bg-secondary);
  border-radius: var(--border-radius-sm);
  margin-bottom: var(--spacing-sm);
}

.video-url {
  font-size: var(--font-size-xs);
  color: var(--color-primary);
  word-break: break-all;
  margin-bottom: var(--spacing-xs);
  display: block;
}

.video-meta {
  display: flex;
  gap: var(--spacing-xs);
  flex-wrap: wrap;
  margin-bottom: var(--spacing-xs);
}

.meta-tag {
  padding: 2px 6px;
  background: var(--color-card);
  border-radius: var(--border-radius-sm);
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

.video-path {
  font-size: var(--font-size-xs);
  color: var(--color-text-hint);
  word-break: break-all;
  display: block;
}

.empty-state, .loading-state, .error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60px 0;
}

.empty-text, .loading-text, .error-text {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.retry-btn {
  margin-top: var(--spacing-md);
  padding: var(--spacing-sm) var(--spacing-lg);
  background: var(--color-primary);
  border-radius: var(--border-radius-base);
}

.retry-text { color: #fff; font-size: var(--font-size-sm); }
</style>
```

### 6.4 已下载视频库 VideoLibrary.vue

```vue
<!-- src/pages/admin/download/VideoLibrary.vue -->
<template>
  <view class="video-library-page">
    <view class="page-header">
      <text class="header-title">已下载视频库</text>
    </view>

    <!-- 加载态 -->
    <view v-if="loading" class="loading-state">
      <text class="loading-text">加载中...</text>
    </view>

    <!-- 错误态 -->
    <view v-else-if="errorMsg" class="error-state">
      <text class="error-text">{{ errorMsg }}</text>
      <view class="retry-btn" @click="fetchData">
        <text class="retry-text">重试</text>
      </view>
    </view>

    <!-- 空态 -->
    <view v-else-if="videos.length === 0" class="empty-state">
      <text class="empty-text">暂无已下载视频</text>
    </view>

    <!-- 视频列表 -->
    <view v-else class="video-list">
      <view
        v-for="video in videos"
        :key="video.id"
        class="video-item"
        @click="goDetail(video.id)"
      >
        <view class="video-header">
          <view :class="['status-tag', `status-${video.status}`]">
            <text class="status-text">{{ videoStatusLabelMap[video.status] }}</text>
          </view>
          <text v-if="video.format" class="format-tag">{{ video.format }}</text>
        </view>

        <text class="video-url mono">{{ video.video_url || '-' }}</text>

        <view class="video-meta">
          <text v-if="video.resolution" class="meta-item">{{ video.resolution }}</text>
          <text v-if="video.file_size" class="meta-item">{{ formatFileSize(video.file_size) }}</text>
          <text v-if="video.duration" class="meta-item">{{ formatDuration(video.duration) }}</text>
        </view>

        <text class="video-path mono">{{ video.storage_path }}</text>
        <text class="video-time">{{ formatTime(video.created_at) }}</text>
      </view>
    </view>

    <!-- 分页 -->
    <view v-if="total > pageSize" class="pagination">
      <view
        class="page-btn"
        :class="{ disabled: currentPage <= 1 }"
        @click="changePage(currentPage - 1)"
      >
        <text>上一页</text>
      </view>
      <text class="page-info">{{ currentPage }} / {{ totalPages }}</text>
      <view
        class="page-btn"
        :class="{ disabled: currentPage >= totalPages }"
        @click="changePage(currentPage + 1)"
      >
        <text>下一页</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { getVideos } from '@/api/download'
import type { DownloadedVideoItem } from '@/types/download'

const videos = ref<DownloadedVideoItem[]>([])
const loading = ref(false)
const errorMsg = ref<string | null>(null)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

const totalPages = computed(() => Math.ceil(total.value / pageSize.value))

const videoStatusLabelMap: Record<string, string> = {
  completed: '已完成',
  partial_completed: '部分完成',
  corrupted: '损坏'
}

function formatTime(isoStr: string): string {
  try {
    const d = new Date(isoStr)
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
  } catch {
    return isoStr
  }
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  if (bytes < 1024 * 1024 * 1024) return (bytes / 1024 / 1024).toFixed(1) + ' MB'
  return (bytes / 1024 / 1024 / 1024).toFixed(2) + ' GB'
}

function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  return `${m}:${String(s).padStart(2, '0')}`
}

async function fetchData() {
  loading.value = true
  errorMsg.value = null
  try {
    const res = await getVideos({
      page: currentPage.value,
      page_size: pageSize.value
    })
    if (res.code === 200 && res.data) {
      videos.value = res.data.items
      total.value = res.data.total
    }
  } catch (err: any) {
    errorMsg.value = err.message || '加载视频列表失败'
  } finally {
    loading.value = false
  }
}

function changePage(page: number) {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  fetchData()
}

function goDetail(videoId: string) {
  // 可跳转到视频详情页，或弹出详情
  uni.navigateTo({ url: `/pages/admin/download/VideoDetail?videoId=${videoId}` })
}

onMounted(() => fetchData())
</script>

<style lang="scss" scoped>
.video-library-page {
  min-height: 100vh;
  background: var(--color-background);
  padding: var(--spacing-md);
}

.page-header {
  margin-bottom: var(--spacing-lg);
}

.header-title {
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--color-text-primary);
}

.video-item {
  padding: var(--spacing-md);
  background: var(--color-card);
  border-radius: var(--border-radius-base);
  margin-bottom: var(--spacing-sm);
}

.video-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-xs);
}

.status-tag {
  padding: 2px 8px;
  border-radius: var(--border-radius-sm);
}

.status-completed { background: #f6ffed; }
.status-partial_completed { background: #fff7e6; }
.status-corrupted { background: #fff2f0; }

.status-text { font-size: var(--font-size-xs); }

.format-tag {
  font-size: var(--font-size-xs);
  color: var(--color-text-hint);
  font-family: monospace;
}

.video-url {
  font-size: var(--font-size-xs);
  color: var(--color-primary);
  word-break: break-all;
  margin-bottom: var(--spacing-xs);
  display: block;
}

.mono { font-family: monospace; }

.video-meta {
  display: flex;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
  margin-bottom: var(--spacing-xs);
}

.meta-item {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  padding: 2px 6px;
  background: var(--color-bg-secondary);
  border-radius: var(--border-radius-sm);
}

.video-path {
  font-size: var(--font-size-xs);
  color: var(--color-text-hint);
  word-break: break-all;
  display: block;
  margin-bottom: var(--spacing-xs);
}

.video-time {
  font-size: var(--font-size-xs);
  color: var(--color-text-hint);
  display: block;
}

.empty-state, .loading-state, .error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60px 0;
}

.empty-text, .loading-text, .error-text {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.retry-btn {
  margin-top: var(--spacing-md);
  padding: var(--spacing-sm) var(--spacing-lg);
  background: var(--color-primary);
  border-radius: var(--border-radius-base);
}

.retry-text { color: #fff; font-size: var(--font-size-sm); }

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-md);
  margin-top: var(--spacing-lg);
}

.page-btn {
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-card);
  border-radius: var(--border-radius-base);
}

.page-btn.disabled { opacity: 0.5; }

.page-info {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}
</style>
```

### 6.5 批量导入页 BatchImport.vue

```vue
<!-- src/pages/admin/download/BatchImport.vue -->
<template>
  <view class="batch-import-page">
    <view class="form-card">
      <text class="form-title">批量导入</text>

      <!-- CSV 导入 -->
      <view class="section">
        <text class="section-title">CSV 文件导入</text>
        <text class="section-desc">CSV 格式：resource_url, resource_type, video_id (可选), liveroom_id (可选)</text>

        <view class="upload-area" @click="chooseCSVFile">
          <view v-if="selectedFile" class="file-info">
            <text class="file-name">{{ selectedFile.name }}</text>
            <text class="file-size">{{ formatFileSize(selectedFile.size) }}</text>
          </view>
          <view v-else class="upload-placeholder">
            <text class="upload-text">点击选择 CSV 文件</text>
          </view>
        </view>

        <view
          class="submit-btn"
          :class="{ disabled: !selectedFile || csvImporting }"
          @click="handleCSVImport"
        >
          <text class="submit-text">{{ csvImporting ? '导入中...' : '开始导入' }}</text>
        </view>

        <!-- 导入结果 -->
        <view v-if="importResult" class="result-card">
          <text class="result-title">导入结果</text>
          <view class="result-row">
            <text class="result-label">CSV 中任务数</text>
            <text class="result-value">{{ importResult.tasks_in_csv }}</text>
          </view>
          <view class="result-row">
            <text class="result-label">新创建任务</text>
            <text class="result-value success">{{ importResult.new_tasks_created }}</text>
          </view>
          <view class="result-row">
            <text class="result-label">跳过重复任务</text>
            <text class="result-value warning">{{ importResult.tasks_skipped_duplicates }}</text>
          </view>
        </view>
      </view>

      <!-- 爬取导入 -->
      <view class="section">
        <text class="section-title">爬取导入</text>
        <text class="section-desc">从指定页面 URL 爬取视频资源并导入下载任务</text>

        <view class="form-item">
          <input
            v-model="sourceUrl"
            class="form-input"
            placeholder="输入要爬取的页面 URL"
            maxlength="2000"
          />
        </view>

        <view
          class="submit-btn submit-btn--secondary"
          :class="{ disabled: !sourceUrl || crawlImporting }"
          @click="handleCrawlImport"
        >
          <text class="submit-text">{{ crawlImporting ? '提交中...' : '开始爬取' }}</text>
        </view>

        <!-- 爬取状态 -->
        <view v-if="crawlStatus" class="result-card">
          <text class="result-title">爬取状态</text>
          <view class="result-row">
            <text class="result-label">状态</text>
            <text class="result-value">{{ crawlStatus.status }}</text>
          </view>
          <view class="result-row">
            <text class="result-label">进度</text>
            <text class="result-value">{{ crawlStatus.progress }}%</text>
          </view>
          <view class="result-row">
            <text class="result-label">发现资源</text>
            <text class="result-value">{{ crawlStatus.total_found }}</text>
          </view>
          <view class="result-row">
            <text class="result-label">已导入</text>
            <text class="result-value success">{{ crawlStatus.imported }}</text>
          </view>
        </view>
      </view>

      <!-- 错误提示 -->
      <view v-if="errorMsg" class="error-banner">
        <text class="error-text">{{ errorMsg }}</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onUnmounted } from 'vue'
import { batchImport, crawlAndImport, getCrawlImportStatus } from '@/api/download'
import type { BatchImportResult, CrawlImportStatus } from '@/types/download'

const errorMsg = ref<string | null>(null)

// CSV 导入
const selectedFile = ref<{ name: string; size: number; path: string } | null>(null)
const csvImporting = ref(false)
const importResult = ref<BatchImportResult | null>(null)

// 爬取导入
const sourceUrl = ref('')
const crawlImporting = ref(false)
const crawlStatus = ref<CrawlImportStatus | null>(null)
let crawlPollTimer: ReturnType<typeof setInterval> | null = null

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1024 / 1024).toFixed(1) + ' MB'
}

/**
 * 选择 CSV 文件（uni.chooseFile 仅 H5 支持，小程序用 wx.chooseMessageFile）
 */
function chooseCSVFile() {
  // #ifdef MP-WEIXIN
  wx.chooseMessageFile({
    count: 1,
    type: 'file',
    extension: ['csv'],
    success: (res) => {
      const file = res.tempFiles[0]
      selectedFile.value = {
        name: file.name,
        size: file.size,
        path: file.path
      }
      importResult.value = null
    }
  })
  // #endif

  // #ifdef H5
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.csv'
  input.onchange = (e: any) => {
    const file = e.target.files[0]
    if (file) {
      selectedFile.value = {
        name: file.name,
        size: file.size,
        path: URL.createObjectURL(file) // H5 临时路径
      }
      importResult.value = null
    }
  }
  input.click()
  // #endif
}

/**
 * CSV 批量导入
 */
async function handleCSVImport() {
  if (!selectedFile.value) return
  errorMsg.value = null
  csvImporting.value = true
  try {
    const res = await batchImport(selectedFile.value.path)
    if (res.code === 200 && res.data) {
      importResult.value = res.data
      uni.showToast({ title: '导入完成', icon: 'success' })
    }
  } catch (err: any) {
    errorMsg.value = err.message || '导入失败'
  } finally {
    csvImporting.value = false
  }
}

/**
 * 爬取导入
 */
async function handleCrawlImport() {
  if (!sourceUrl.value) return
  errorMsg.value = null
  crawlImporting.value = true
  try {
    await crawlAndImport({ source_url: sourceUrl.value })
    uni.showToast({ title: '爬取任务已提交', icon: 'success' })
    // 开始轮询状态
    startCrawlPolling()
  } catch (err: any) {
    errorMsg.value = err.message || '爬取导入失败'
  } finally {
    crawlImporting.value = false
  }
}

function startCrawlPolling() {
  stopCrawlPolling()
  crawlPollTimer = setInterval(async () => {
    try {
      const res = await getCrawlImportStatus()
      if (res.code === 200 && res.data) {
        crawlStatus.value = res.data
        if (res.data.status === 'completed' || res.data.status === 'failed') {
          stopCrawlPolling()
        }
      }
    } catch {
      stopCrawlPolling()
    }
  }, 5000)
}

function stopCrawlPolling() {
  if (crawlPollTimer) {
    clearInterval(crawlPollTimer)
    crawlPollTimer = null
  }
}

onUnmounted(() => stopCrawlPolling())
</script>

<style lang="scss" scoped>
.batch-import-page {
  min-height: 100vh;
  background: var(--color-background);
  padding: var(--spacing-lg);
}

.form-card {
  padding: var(--spacing-lg);
  background: var(--color-card);
  border-radius: var(--border-radius-lg);
}

.form-title {
  display: block;
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-xl);
}

.section {
  margin-bottom: var(--spacing-xl);
  padding-bottom: var(--spacing-xl);
  border-bottom: 1px solid var(--color-border);
}

.section:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.section-title {
  display: block;
  font-size: var(--font-size-base);
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-xs);
}

.section-desc {
  display: block;
  font-size: var(--font-size-xs);
  color: var(--color-text-hint);
  margin-bottom: var(--spacing-md);
}

.upload-area {
  padding: var(--spacing-lg);
  background: var(--color-bg-secondary);
  border: 2px dashed var(--color-border);
  border-radius: var(--border-radius-base);
  text-align: center;
  margin-bottom: var(--spacing-md);
}

.upload-text {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.file-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-xs);
}

.file-name {
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
  font-weight: 500;
}

.file-size {
  font-size: var(--font-size-xs);
  color: var(--color-text-hint);
}

.form-item {
  margin-bottom: var(--spacing-md);
}

.form-input {
  width: 100%;
  padding: var(--spacing-md);
  background: var(--color-bg-secondary);
  border-radius: var(--border-radius-base);
  font-size: var(--font-size-base);
}

.submit-btn {
  padding: var(--spacing-md);
  background: var(--color-primary);
  border-radius: var(--border-radius-base);
  text-align: center;
}

.submit-btn--secondary {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
}

.submit-btn--secondary .submit-text { color: var(--color-text-primary); }

.submit-btn.disabled { opacity: 0.6; }

.submit-text { color: #fff; font-size: var(--font-size-base); font-weight: 500; }

.result-card {
  margin-top: var(--spacing-md);
  padding: var(--spacing-md);
  background: var(--color-bg-secondary);
  border-radius: var(--border-radius-base);
}

.result-title {
  display: block;
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-sm);
}

.result-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: var(--spacing-xs);
}

.result-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.result-value {
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
  font-weight: 500;
}

.result-value.success { color: #52c41a; }
.result-value.warning { color: #fa8c16; }

.error-banner {
  margin-top: var(--spacing-md);
  padding: var(--spacing-sm) var(--spacing-md);
  background: #fff2f0;
  border-radius: var(--border-radius-sm);
}

.error-text { font-size: var(--font-size-sm); color: var(--color-danger); }
</style>
```

---

## 七、用户端页面/组件

### 7.1 任务进度轮询 Composable

```typescript
// src/composables/useTaskPoller.ts

import { ref, onUnmounted } from 'vue'
import { getTask } from '@/api/download'
import type { DownloadTaskItem, TaskStatus } from '@/types/download'

/**
 * 任务进度轮询
 * 用于任务详情页自动刷新进度，直到任务进入终态
 * @param taskId 任务 ID
 * @param interval 轮询间隔（毫秒），默认 3000
 */
export function useTaskPoller(taskId: string, interval = 3000) {
  const task = ref<DownloadTaskItem | null>(null)
  const isPolling = ref(false)
  let timer: ReturnType<typeof setInterval> | null = null

  /** 终态列表 */
  const terminalStatuses: TaskStatus[] = ['completed', 'failed', 'cancelled', 'partial_completed']

  async function poll() {
    try {
      const res = await getTask(taskId)
      if (res.code === 200 && res.data) {
        task.value = res.data
        if (terminalStatuses.includes(res.data.status)) {
          stop()
        }
      }
    } catch (err) {
      console.error('轮询任务状态失败', err)
    }
  }

  function start() {
    if (isPolling.value) return
    isPolling.value = true
    poll() // 立即执行一次
    timer = setInterval(poll, interval)
  }

  function stop() {
    isPolling.value = false
    if (timer) {
      clearInterval(timer)
      timer = null
    }
  }

  onUnmounted(stop)

  return { task, isPolling, start, stop }
}
```

### 7.2 爬取导入状态轮询 Composable

```typescript
// src/composables/useCrawlStatus.ts

import { ref, onUnmounted } from 'vue'
import { getCrawlImportStatus } from '@/api/download'
import type { CrawlImportStatus } from '@/types/download'

/**
 * 爬取导入状态轮询
 * 用于批量导入页自动刷新爬取进度
 * @param interval 轮询间隔（毫秒），默认 5000
 */
export function useCrawlStatus(interval = 5000) {
  const status = ref<CrawlImportStatus | null>(null)
  const isPolling = ref(false)
  let timer: ReturnType<typeof setInterval> | null = null

  async function poll() {
    try {
      const res = await getCrawlImportStatus()
      if (res.code === 200 && res.data) {
        status.value = res.data
        if (res.data.status === 'completed' || res.data.status === 'failed') {
          stop()
        }
      }
    } catch (err) {
      console.error('轮询爬取状态失败', err)
    }
  }

  function start() {
    if (isPolling.value) return
    isPolling.value = true
    poll()
    timer = setInterval(poll, interval)
  }

  function stop() {
    isPolling.value = false
    if (timer) {
      clearInterval(timer)
      timer = null
    }
  }

  onUnmounted(stop)

  return { status, isPolling, start, stop }
}
```

---

## 八、对接清单

| # | 任务 | 文件路径 | 说明 |
|---|------|---------|------|
| 1 | 创建类型定义 | `src/types/download.ts` | 按第三节，所有枚举严格对齐 DDL CHECK |
| 2 | 创建 API 封装 | `src/api/download.ts` | 按第四节，16 个端点 |
| 3 | 配置 API 路径 | `src/config/api.ts` | DOWNLOAD 段（已存在），确认独立微服务 base URL |
| 4 | 创建轮询 Composable | `src/composables/useTaskPoller.ts` | 按第七节 7.1 |
| 5 | 创建爬取状态 Composable | `src/composables/useCrawlStatus.ts` | 按第七节 7.2 |
| 6 | 实现任务列表页 | `src/pages/admin/download/TaskList.vue` | 按第六节 6.1 |
| 7 | 实现新建任务页 | `src/pages/admin/download/TaskCreateForm.vue` | 按第六节 6.2 |
| 8 | 实现任务详情页 | `src/pages/admin/download/TaskDetail.vue` | 按第六节 6.3 |
| 9 | 实现视频库页 | `src/pages/admin/download/VideoLibrary.vue` | 按第六节 6.4 |
| 10 | 实现批量导入页 | `src/pages/admin/download/BatchImport.vue` | 按第六节 6.5 |
| 11 | 更新 pages.json | `src/pages.json` | 添加 admin/download/ 路由 |
| 12 | 配置环境变量 | `.env` / `.env.development` | 追加 VITE_DOWNLOAD_API_URL（独立微服务地址） |

---

## 九、API 链路总结

### 后端路由表（16 个端点）

| # | 方法 | 后端路径 | 认证 | 前端函数 | 错误码 |
|---|------|---------|------|---------|--------|
| 1 | POST | `/download/tasks` | JWT | `createTask(data)` | 200, 2002, 3001, 4001, 1002 |
| 2 | GET | `/download/tasks` | JWT | `getTasks(params)` | 200, 3001, 1002 |
| 3 | GET | `/download/tasks/{taskId}` | JWT | `getTask(taskId)` | 200, 2001, 3001, 3002, 1002 |
| 4 | PUT | `/download/tasks/{taskId}` | JWT | `updateTask(taskId, data)` | 200, 2001, 3001, 3002, 4001, 1002 |
| 5 | DELETE | `/download/tasks/{taskId}` | JWT | `deleteTask(taskId)` | 200, 2001, 3001, 3002, 1002 |
| 6 | POST | `/download/tasks/{taskId}/start` | JWT | `startTask(taskId)` | 200, 2001, 2004, 3001, 3002, 1002 |
| 7 | POST | `/download/tasks/{taskId}/retry` | JWT | `retryTask(taskId)` | 200, 2001, 2004, 3001, 3002, 1002 |
| 8 | GET | `/download/tasks/{taskId}/failures` | JWT | `getTaskFailures(taskId, params)` | 200, 2001, 3001, 3002, 1002 |
| 9 | POST | `/download/tasks/{taskId}/failures/{failureId}/retry` | JWT | `retryFailure(taskId, failureId)` | 200, 2001, 3001, 3002, 1002 |
| 10 | POST | `/download/tasks/{taskId}/failures/{failureId}/abandon` | JWT | `abandonFailure(taskId, failureId)` | 200, 2001, 3001, 3002, 1002 |
| 11 | GET | `/download/tasks/{taskId}/videos` | JWT | `getTaskVideos(taskId)` | 200, 2001, 3001, 3002, 1002 |
| 12 | GET | `/download/videos` | JWT | `getVideos(params)` | 200, 3001, 1002 |
| 13 | GET | `/download/videos/{videoId}` | JWT | `getVideo(videoId)` | 200, 2001, 3001, 3002, 1002 |
| 14 | POST | `/download/tasks/batch-import` | JWT | `batchImport(filePath)` | 200, 3001, 4001, 1002 |
| 15 | POST | `/download/tasks/crawl-and-import` | JWT | `crawlAndImport(data)` | 200, 3001, 4001, 1002 |
| 16 | GET | `/download/tasks/crawl-import-status` | JWT | `getCrawlImportStatus()` | 200, 3001, 1002 |

### 错误码映射

| 错误码 | 说明 | 前端处理 |
|--------|------|---------|
| 200 | 成功 | 正常处理 |
| 1002 | 数据库错误 | 提示"服务器内部错误" |
| 2001 | 资源不存在 | 提示"任务/视频不存在" |
| 2002 | 资源已存在 | 提示"相同资源的任务已存在"（去重） |
| 2004 | 业务逻辑错误 | 提示"任务状态不允许此操作" |
| 3001 | 未授权 | 跳转登录页 |
| 3002 | 权限不足 | 提示"无权操作此资源" |
| 4001 | 参数校验失败 | 提示具体校验错误（如 URL 格式） |

### 状态机转换图

```
pending ──start──→ processing ──→ completed
   │                    │
   │                    ├──→ partial_completed
   │                    │
   │                    └──→ failed ──retry──→ processing
   │
   └──delete──→ (物理删除)
```

### 轮询策略

| 场景 | 轮询间隔 | 终态 | 说明 |
|------|---------|------|------|
| 任务列表（有 processing 任务） | 5s | 无 processing 任务时停止 | TaskList.vue |
| 任务详情（processing 状态） | 3s | completed/failed/cancelled/partial_completed | TaskDetail.vue / useTaskPoller |
| 爬取导入状态 | 5s | completed/failed | BatchImport.vue / useCrawlStatus |
