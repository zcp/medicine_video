/**
 * 直播场次-标签关联API
 * 阶段一新建：2025
 * 封装直播场次与标签关联相关的API请求
 */

import { get, post, del } from '@/utils/request';
import type { Tag, SessionTagsPayload } from '@/types/tag';
import type { ApiResponse } from '@/types/common';

/**
 * 为直播场次批量设置标签（登录用户；房主或 Admin）
 * @param sessionId 直播场次ID
 * @param data 标签设置数据（tag_ids 0~5 + mode: replace|append）
 * @returns Promise<ApiResponse<void>>
 * @example
 * await setSessionTags('session_uuid_123', {
 *   tag_ids: ['tag_uuid_1', 'tag_uuid_2'],
 *   mode: 'replace'
 * });
 */
export const setSessionTags = (sessionId: string, data: SessionTagsPayload): Promise<ApiResponse<void>> => {
  return post<ApiResponse<void>>(`/sessions/${sessionId}/tags`, data, { auth: true });
};

/**
 * 删除直播场次的单个标签（登录用户）
 * @param sessionId 直播场次ID
 * @param tagId 标签ID
 * @returns Promise<ApiResponse<void>>
 * @example
 * await removeSessionTag('session_uuid_123', 'tag_uuid_1');
 */
export const removeSessionTag = (sessionId: string, tagId: string): Promise<ApiResponse<void>> => {
  return del<ApiResponse<void>>(`/sessions/${sessionId}/tags/${tagId}`, undefined, { auth: true });
};

/**
 * 获取直播场次的标签列表（公开）
 * @param sessionId 直播场次ID
 * @returns Promise<ApiResponse<Tag[]>>
 * @example
 * const response = await getSessionTags('session_uuid_123');
 */
export const getSessionTags = (sessionId: string): Promise<ApiResponse<Tag[]>> => {
  return get<ApiResponse<Tag[]>>(`/sessions/${sessionId}/tags`);
};

