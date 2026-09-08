/**
 * 媒体下载服务 API
 * 以后端设计文档为准：《11-媒体下载服务-后端设计文档.md》
 * 独立微服务（端口8001），所有接口需 JWT 认证
 *
 * 端点清单（16个）:
 *   任务管理(7): POST创建, GET列表, GET详情, PUT更新, DELETE删除, POST开始, POST重试
 *   失败记录(3): GET任务失败列表, POST重试单个, POST放弃单个
 *   视频记录(3): GET全局视频列表, GET视频详情, GET任务视频列表
 *   批量导入(3): POST CSV导入, POST爬取导入, GET爬取状态
 */

import { request } from '@/utils/request'
import { API_PATHS } from '@/config/api'
import type { ApiResponse } from '@/types/common'
import type {
  DownloadTask,
  DownloadTaskCreate,
  DownloadFailure,
  DownloadedVideo,
  CrawlAndImportRequest,
  BatchImportResult
} from '@/types/download'

// ============ 任务管理 ============

/**
 * 创建下载任务
 * POST /api/v1/download/tasks
 */
export const createDownloadTask = (
  data: DownloadTaskCreate
): Promise<ApiResponse<DownloadTask>> => {
  return request.post(API_PATHS.DOWNLOAD.TASKS, data, {
    loading: true,
    loadingText: '创建任务中...'
  })
}

/**
 * 获取下载任务列表（分页，可按状态筛选）
 * GET /api/v1/download/tasks
 */
export const getDownloadTasks = (params?: {
  page?: number
  page_size?: number
  status?: string
}): Promise<ApiResponse<{ total: number; page: number; size: number; items: DownloadTask[] }>> => {
  return request.get(API_PATHS.DOWNLOAD.TASKS, { data: params, showError: false })
}

/**
 * 获取下载任务详情
 * GET /api/v1/download/tasks/{taskId}
 */
export const getDownloadTask = (
  taskId: string
): Promise<ApiResponse<DownloadTask>> => {
  return request.get(API_PATHS.DOWNLOAD.TASK_DETAIL(taskId), { showError: false })
}

/**
 * 更新下载任务
 * PUT /api/v1/download/tasks/{taskId}
 */
export const updateDownloadTask = (
  taskId: string,
  data: Partial<DownloadTaskCreate>
): Promise<ApiResponse<DownloadTask>> => {
  return request.put(API_PATHS.DOWNLOAD.TASK_DETAIL(taskId), data, {
    loading: true,
    loadingText: '更新中...'
  })
}

/**
 * 删除下载任务（级联删除关联的失败记录和视频）
 * DELETE /api/v1/download/tasks/{taskId}
 */
export const deleteDownloadTask = (
  taskId: string
): Promise<ApiResponse<null>> => {
  return request.delete(API_PATHS.DOWNLOAD.TASK_DETAIL(taskId), {
    loading: true,
    loadingText: '删除中...'
  })
}

/**
 * 开始下载任务
 * POST /api/v1/download/tasks/{taskId}/start
 */
export const startDownloadTask = (
  taskId: string
): Promise<ApiResponse<DownloadTask>> => {
  return request.post(API_PATHS.DOWNLOAD.TASK_START(taskId), {}, {
    loading: true,
    loadingText: '启动中...'
  })
}

/**
 * 重试失败的下载任务
 * POST /api/v1/download/tasks/{taskId}/retry
 */
export const retryDownloadTask = (
  taskId: string
): Promise<ApiResponse<DownloadTask>> => {
  return request.post(API_PATHS.DOWNLOAD.TASK_RETRY(taskId), {}, {
    loading: true,
    loadingText: '重试中...'
  })
}

// ============ 失败记录 ============

/**
 * 获取任务的失败记录列表
 * GET /api/v1/download/tasks/{taskId}/failures
 */
export const getTaskFailures = (
  taskId: string
): Promise<ApiResponse<{ items: DownloadFailure[] }>> => {
  return request.get(API_PATHS.DOWNLOAD.TASK_FAILURES(taskId), { showError: false })
}

/**
 * 重试单个失败记录
 * POST /api/v1/download/tasks/{taskId}/failures/{failureId}/retry
 */
export const retryFailure = (
  taskId: string,
  failureId: string
): Promise<ApiResponse<null>> => {
  return request.post(API_PATHS.DOWNLOAD.FAILURE_RETRY(taskId, failureId), {}, {
    loading: true,
    loadingText: '重试中...'
  })
}

/**
 * 放弃单个失败记录
 * POST /api/v1/download/tasks/{taskId}/failures/{failureId}/abandon
 */
export const abandonFailure = (
  taskId: string,
  failureId: string
): Promise<ApiResponse<null>> => {
  return request.post(API_PATHS.DOWNLOAD.FAILURE_ABANDON(taskId, failureId), {}, {
    loading: true,
    loadingText: '处理中...'
  })
}

// ============ 视频记录 ============

/**
 * 获取全局已下载视频列表
 * GET /api/v1/download/videos
 */
export const getDownloadedVideos = (params?: {
  page?: number
  page_size?: number
}): Promise<ApiResponse<{ total: number; page: number; size: number; items: DownloadedVideo[] }>> => {
  return request.get(API_PATHS.DOWNLOAD.VIDEOS, { data: params, showError: false })
}

/**
 * 获取视频详情
 * GET /api/v1/download/videos/{videoId}
 */
export const getDownloadedVideo = (
  videoId: string
): Promise<ApiResponse<DownloadedVideo>> => {
  return request.get(API_PATHS.DOWNLOAD.VIDEO_DETAIL(videoId), { showError: false })
}

/**
 * 获取任务关联的已下载视频
 * GET /api/v1/download/tasks/{taskId}/videos
 */
export const getTaskVideos = (
  taskId: string
): Promise<ApiResponse<{ items: DownloadedVideo[] }>> => {
  return request.get(API_PATHS.DOWNLOAD.TASK_VIDEOS(taskId), { showError: false })
}

// ============ 批量导入 ============

/**
 * CSV批量导入下载任务
 * POST /api/v1/download/tasks/batch-import
 * 注意：小程序环境使用 uni.uploadFile，不支持 FormData
 */
export const batchImportTasks = (
  filePath: string
): Promise<ApiResponse<BatchImportResult>> => {
  return request.upload({
    url: API_PATHS.DOWNLOAD.BATCH_IMPORT,
    filePath,
    name: 'file',
    loading: true,
    loadingText: '导入中...'
  })
}

/**
 * 爬取并导入下载任务
 * POST /api/v1/download/tasks/crawl-and-import
 */
export const crawlAndImport = (
  data: CrawlAndImportRequest
): Promise<ApiResponse<{ task_id: string }>> => {
  return request.post(API_PATHS.DOWNLOAD.CRAWL_IMPORT, data, {
    loading: true,
    loadingText: '爬取中...'
  })
}

/**
 * 获取爬取导入状态
 * GET /api/v1/download/tasks/crawl-import-status
 */
export const getCrawlImportStatus = (): Promise<ApiResponse<{
  status: string
  progress: number
  message?: string
}>> => {
  return request.get(API_PATHS.DOWNLOAD.CRAWL_STATUS, { showError: false })
}

export default {
  createDownloadTask,
  getDownloadTasks,
  getDownloadTask,
  updateDownloadTask,
  deleteDownloadTask,
  startDownloadTask,
  retryDownloadTask,
  getTaskFailures,
  retryFailure,
  abandonFailure,
  getDownloadedVideos,
  getDownloadedVideo,
  getTaskVideos,
  batchImportTasks,
  crawlAndImport,
  getCrawlImportStatus
}
