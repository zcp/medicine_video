/**
 * 直播间留言（Room Message）类型定义
 * 对齐《07-直播间留言-后端设计文档.md》V1.1
 * + 《07-直播间留言-V3-用户昵称头像快照增量设计文档.md》V3.0
 *
 * 用户端 3 个 API + 管理端 3 个 API，共 6 个端点
 * DDL: room_messages (id, room_id, user_id, content, created_at)
 * 展示：extra 快照 → user / user_display_name（非跨库 JOIN）
 * 删除策略：物理删除
 */

/**
 * 留言用户信息（V3：从 extra 快照组装）
 */
export interface MessageUserInfo {
  nickname?: string | null
  avatar_url?: string | null
}

/**
 * 留言项（LiveRoomMessageItem + V3 快照字段）
 */
export interface RoomMessageItem {
  id: string
  room_id: string
  user_id: string
  content: string
  created_at: string
  /** V3：发送时快照；历史无快照时可为 null */
  user?: MessageUserInfo | null
  /** V3：兼容旧字段，与 user.nickname 同源 */
  user_display_name?: string | null
  user_role?: string | null
}

/** @deprecated 使用 RoomMessageItem */
export type LiveRoomMessage = RoomMessageItem

/**
 * 发送留言请求（对应后端 LiveRoomMessageCreate Schema）
 */
export interface RoomMessageCreate {
  content: string
}

/**
 * 用户端留言查询参数（GET /rooms/{roomId}/messages）
 * 后端 Query 名为 size（兼容文档里的 page_size）
 */
export interface RoomMessageQueryParams {
  page?: number
  /** 后端实际参数名 */
  size?: number
  /** 兼容旧调用 */
  page_size?: number
}

/**
 * 用户端留言分页结果（对应后端 MessagePageResult Schema）
 */
export interface RoomMessagePageResult {
  items: RoomMessageItem[]
  total: number
  page: number
  page_size: number
}

/**
 * 管理端全局留言查询参数（对应后端 AdminMessageQueryParams）
 */
export interface AdminMessageQueryParams {
  room_id?: string
  user_id?: string
  keyword?: string
  start_time?: string
  end_time?: string
  page?: number
  page_size?: number
}

/**
 * 批量删除请求（对应后端 BatchDeleteRequest，最多 200 条）
 */
export interface BatchDeleteRequest {
  message_ids: string[]
}

/**
 * 管理端留言条目（对应后端 AdminMessageItem）
 */
export interface AdminMessageItem extends RoomMessageItem {
  room_title?: string | null
  user_nickname?: string | null
  user_role?: string | null
  ip_address?: string | null
}

/**
 * 管理端筛选摘要
 */
export interface AdminMessageFilterSummary {
  keyword?: string
  room_count?: number
  user_count?: number
  [key: string]: unknown
}

/**
 * 管理端留言分页结果（对应后端 AdminMessagePageResult）
 */
export interface AdminMessagePageResult {
  items: AdminMessageItem[]
  total: number
  page: number
  page_size: number
  filter_summary?: AdminMessageFilterSummary | null
}

/**
 * 批量删除响应 data
 */
export interface BatchDeleteResult {
  deleted_count: number
  failed_count: number
}

/**
 * 清空直播间留言响应 data
 */
export interface ClearRoomMessagesResult {
  deleted_count: number
}

/** 后端业务错误码（§8 错误码对照表） */
export const ROOM_MESSAGE_ERROR_CODES = {
  SUCCESS: 200,
  DB_ERROR: 1002,
  NOT_FOUND: 2001,
  BUSINESS_ERROR: 2004,
  UNAUTHORIZED: 3001,
  FORBIDDEN: 3002,
  ADMIN_FORBIDDEN: 3003,
  VALIDATION: 4001
} as const

import { pickUserFacingMessage } from '@/utils/contentSafety'

/** 根据后端错误码返回用户可读提示 */
export function getRoomMessageErrorMessage(code?: number, fallback?: string): string {
  switch (code) {
    case ROOM_MESSAGE_ERROR_CODES.NOT_FOUND:
      return '资源不存在'
    case ROOM_MESSAGE_ERROR_CODES.BUSINESS_ERROR:
      return pickUserFacingMessage(fallback, '暂时无法发送讨论，请稍后再试')
    case ROOM_MESSAGE_ERROR_CODES.UNAUTHORIZED:
      return '请先登录'
    case ROOM_MESSAGE_ERROR_CODES.FORBIDDEN:
      return '只能删除自己的讨论'
    case ROOM_MESSAGE_ERROR_CODES.ADMIN_FORBIDDEN:
      return '权限不足：仅管理员可执行此操作'
    case ROOM_MESSAGE_ERROR_CODES.VALIDATION:
      return pickUserFacingMessage(fallback, '讨论内容为空或超出长度限制')
    case ROOM_MESSAGE_ERROR_CODES.DB_ERROR:
      return '服务器繁忙，请稍后重试'
    default:
      return pickUserFacingMessage(fallback, '操作失败，请稍后再试')
  }
}
