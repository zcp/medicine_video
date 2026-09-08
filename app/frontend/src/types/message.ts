/**
 * 留言相关类型定义
 * 用于直播间聊天/留言功能
 */

import type { PaginatedResponse } from './common';

/**
 * 留言信息
 */
export interface Message {
  /** 留言ID */
  id: string;
  /** 房间ID */
  room_id: string;
  /** 用户ID */
  user_id: string;
  /** 留言内容 */
  content: string;
  /** 留言状态 */
  status: 'pending' | 'approved' | 'rejected';
  /** 用户展示昵称（后端读时回填：profile → extra 快照 → 注销占位） */
  user_display_name?: string | null;
  /** 用户展示信息（后端三段式管线：profile 回填 / 注销占位） */
  user?: {
    nickname?: string | null;
    avatar_url?: string | null;
  } | null;
  /** 扩展信息（写时快照：user_display_name/avatar_url） */
  extra?: {
    user_avatar?: string;
    user_display_name?: string;
    avatar_url?: string;
    [key: string]: any;
  };
  /** 创建时间 */
  created_at: string;
  /** 更新时间 */
  updated_at: string;
}

/**
 * 创建留言请求体
 */
export interface MessageCreatePayload {
  /** 留言内容 */
  content: string;
}

/**
 * 留言列表响应
 */
export interface MessageListResponse {
  /** 留言列表 */
  items: Message[];
  /** 总数 */
  total: number;
  /** 当前页码 */
  page: number;
  /** 每页数量 */
  size: number;
  /** 分页信息（可选，用于兼容不同后端格式） */
  pagination?: {
    page: number;
    page_size: number;
    total_pages: number;
    total_items: number;
  };
}

/**
 * 留言查询参数
 */
export interface MessageQueryParams {
  /** 页码 */
  page?: number;
  /** 每页数量（对齐后端 size 参数） */
  size?: number;
  /** 留言状态 */
  status?: 'pending' | 'approved' | 'rejected';
}
