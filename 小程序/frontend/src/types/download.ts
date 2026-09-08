/**
 * 媒体下载服务（Media Download）类型定义
 * 以后端设计文档为准：《11-媒体下载服务-后端设计文档.md》
 * 独立微服务，端口8001
 *
 * DDL: download_tasks, download_failures, downloaded_videos
 */

/**
 * 下载任务状态
 * 后端 CHECK: pending/processing/completed/partial_completed/failed/cancelled
 */
export type TaskStatus = 'pending' | 'processing' | 'completed' | 'partial_completed' | 'failed' | 'cancelled'

/**
 * 资源类型
 * 后端 CHECK: m3u8/ts/mp4/image
 */
export type ResourceType = 'm3u8' | 'ts' | 'mp4' | 'image'

/**
 * 失败类型
 * 后端 CHECK: network_error/timeout/invalid_content/storage_error/permission_error
 */
export type FailureType = 'network_error' | 'timeout' | 'invalid_content' | 'storage_error' | 'permission_error'

/**
 * 失败记录状态
 * 后端 CHECK: pending/retrying/abandoned
 */
export type FailureStatus = 'pending' | 'retrying' | 'abandoned'

/**
 * 下载任务（对应后端 DownloadTaskItem Schema）
 * DDL: download_tasks 表
 */
export interface DownloadTask {
  id: string
  user_id: string
  video_id?: string | null
  liveroom_id?: string | null
  resource_url: string
  resource_type: ResourceType
  status: TaskStatus
  progress: number
  total_segments: number
  downloaded_segments: number
  failed_segments: number
  storage_path?: string | null
  error_message?: string | null
  started_at?: string | null
  completed_at?: string | null
  created_at: string
  updated_at: string
}

/**
 * 创建下载任务请求（对应后端 DownloadTaskCreate Schema）
 * URL 必须以 http:// 或 https:// 开头
 */
export interface DownloadTaskCreate {
  resource_url: string
  resource_type: ResourceType
  video_id?: string
  liveroom_id?: string
}

/**
 * 下载失败记录（对应后端 DownloadFailureItem Schema）
 * DDL: download_failures 表
 * 注意：字段名是 segment_url（非 resource_url）
 */
export interface DownloadFailure {
  id: string
  task_id: string
  segment_url?: string | null
  resource_type: ResourceType
  failure_type: FailureType
  error_message?: string | null
  retry_count: number
  status: FailureStatus
  created_at: string
  updated_at: string
}

/**
 * 已下载视频（对应后端 DownloadedVideoItem Schema）
 * DDL: downloaded_videos 表
 */
export interface DownloadedVideo {
  id: string
  video_id: string
  liveroom_id?: string | null
  video_type?: string | null
  video_url?: string | null
  storage_path: string
  file_size?: number | null
  duration?: number | null
  resolution?: string | null
  format?: string | null
  status: 'completed' | 'partial_completed' | 'corrupted'
  metadata?: Record<string, any> | null
  created_at: string
  updated_at: string
}

/**
 * 爬取导入请求
 */
export interface CrawlAndImportRequest {
  url: string
  room_id?: string
  auto_download?: boolean
}

/**
 * 批量导入结果（对应后端 BatchImportResult Schema）
 */
export interface BatchImportResult {
  tasks_in_csv: number
  new_tasks_created: number
  tasks_skipped_duplicates: number
}
