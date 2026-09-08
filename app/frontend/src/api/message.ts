/**
 * 留言API
 * 用于直播间聊天/留言功能的API请求
 */

import { get, post, del } from '@/utils/request';
import type { Message, MessageCreatePayload, MessageListResponse, MessageQueryParams } from '@/types/message';
import type { ApiResponse } from '@/types/common';

/**
 * 发送留言
 * @param roomId 房间ID
 * @param data 留言内容
 * @returns Promise<ApiResponse<Message>>
 */
export const sendRoomMessage = (roomId: string, data: MessageCreatePayload): Promise<ApiResponse<Message>> => {
  return post<ApiResponse<Message>>(`/rooms/${roomId}/messages`, data, { auth: true });
};

/**
 * 获取留言列表
 * @param roomId 房间ID
 * @param params 查询参数
 * @returns Promise<ApiResponse<MessageListResponse>>
 */
export const getRoomMessages = (
  roomId: string,
  params: MessageQueryParams = {}
): Promise<ApiResponse<MessageListResponse>> => {
  return get<ApiResponse<MessageListResponse>>(`/rooms/${roomId}/messages`, params);
};

/**
 * 删除留言（本人或管理员）
 * @param roomId 房间ID
 * @param messageId 留言ID
 * @description DELETE /rooms/{room_id}/messages/{message_id} — 管理员可删任意；普通用户仅本人
 * @returns 403/3002 无权限；404/2001 留言或房间不存在
 */
export const deleteRoomMessage = (roomId: string, messageId: string): Promise<ApiResponse<void>> => {
  return del<ApiResponse<void>>(`/rooms/${roomId}/messages/${messageId}`, undefined, { auth: true });
};

/**
 * 清空指定直播间的全部留言（管理员接口）
 * @param roomId 房间ID
 * @returns Promise<ApiResponse<{ deleted_count: number }>>
 */
export const clearRoomMessages = (roomId: string): Promise<ApiResponse<{ deleted_count: number }>> => {
  return del<ApiResponse<{ deleted_count: number }>>(`/admin/rooms/${roomId}/messages`, undefined, { auth: true });
};

/**
 * 管理端留言查询参数（对齐后端 AdminMessageQueryParams，使用 page_size）
 */
export interface AdminMessageQueryParams {
  room_id?: string;
  user_id?: string;
  keyword?: string;
  start_time?: string;
  end_time?: string;
  page?: number;
  page_size?: number;
}

/**
 * 管理端留言列表单项
 */
export interface AdminMessageItem {
  id: string;
  room_id: string;
  user_id: string;
  user_role: string;
  content: string;
  created_at: string;
  user_display_name?: string | null;
  avatar_url?: string | null;
  room_title?: string | null;
  extra?: {
    user_display_name?: string;
    [key: string]: any;
  } | null;
}

/**
 * 管理端留言分页结果
 */
export interface AdminMessagePageResult {
  items: AdminMessageItem[];
  total: number;
  page: number;
  page_size: number;
  filter_summary?: Record<string, any>;
}

/**
 * 管理端留言列表（仅管理员）
 * @param params 筛选参数（page_size 对齐后端契约）
 */
export const getAdminMessages = (
  params: AdminMessageQueryParams = {}
): Promise<ApiResponse<AdminMessagePageResult>> => {
  return get<ApiResponse<AdminMessagePageResult>>('/admin/messages', params, { auth: true });
};

/**
 * 管理端批量删除留言（仅管理员，最多 200 条/次）
 * @param messageIds 留言ID列表
 */
export const batchDeleteMessages = (
  messageIds: string[]
): Promise<ApiResponse<{ deleted_count: number; failed_count: number }>> => {
  return post<ApiResponse<{ deleted_count: number; failed_count: number }>>(
    '/admin/messages/batch-delete',
    { message_ids: messageIds },
    { auth: true }
  );
};
