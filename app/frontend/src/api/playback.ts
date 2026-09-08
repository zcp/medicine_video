/**
 * 播放相关API（V15）
 * 播放失败上报：线上兜底"哪些机型播不了"的可观测手段
 */

import { request } from '@/utils/request';
import type { ApiResponse } from '@/types/common';

/**
 * 上报播放失败信息
 * @param data 失败信息（场次ID/播放源hash/错误码/设备信息）
 */
export const reportPlaybackFail = (data: {
  session_id?: string;
  url_hash?: string;
  error_code?: string;
  device_info?: string;
}): Promise<ApiResponse<void>> => {
  return request<ApiResponse<void>>({
    url: '/playback/fail',
    method: 'POST',
    data,
  });
};
