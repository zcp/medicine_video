/**
 * Tab API - 直播图文混排模块
 */

import { get, post, patch, del } from '@/utils/request';
import type { Tab, TabCreatePayload, TabUpdatePayload } from '@/types/tab';
import type { ApiResponse } from '@/types/common';
import { ENV_CONFIG } from '@/config/env';
import { getToken } from '@/store/auth';

/**
 * 获取房间Tab列表
 * @param roomId 房间ID
 * @returns Promise<ApiResponse<Tab[]>>
 */
export const getRoomTabList = (roomId: string): Promise<ApiResponse<Tab[]>> => {
  return get<ApiResponse<Tab[]>>(`/rooms/${roomId}/tabs`, undefined, { auth: true });
};

/**
 * 获取房间公开Tab列表
 * @param roomId 房间ID
 */
export const getPublicRoomTabList = (roomId: string): Promise<ApiResponse<Tab[]>> => {
  return get<ApiResponse<Tab[]>>(`/rooms/${roomId}/tabs`, undefined, { auth: false });
};

/**
 * 创建房间Tab
 * @param roomId 房间ID
 * @param data Tab创建数据
 * @returns Promise<ApiResponse<Tab>>
 */
export const createRoomTab = (roomId: string, data: TabCreatePayload): Promise<ApiResponse<Tab>> => {
  return post<ApiResponse<Tab>>(`/admin/rooms/${roomId}/tabs`, data, { auth: true });
};

/**
 * 更新房间Tab
 * @param tabId Tab ID
 * @param data Tab更新数据
 * @returns Promise<ApiResponse<Tab>>
 */
export const updateRoomTab = (tabId: string, data: TabUpdatePayload): Promise<ApiResponse<Tab>> => {
  return patch<ApiResponse<Tab>>(`/admin/tabs/${tabId}`, data, { auth: true });
};

/**
 * 闂佸憡甯炴繛鈧繛鍛厹ab
 * @param tabId Tab ID
 * @returns Promise<ApiResponse<void>>
 */
export const deleteRoomTab = (tabId: string): Promise<ApiResponse<void>> => {
  return del<ApiResponse<void>>(`/admin/tabs/${tabId}`, undefined, { auth: true });
};

/**
 * 婵炴垶鎸搁敃锝囨缁傘倹b闂佹悶鍎辨晶鑺ユ櫠?
 * @param roomId 闂佽娼欏鈥澄涚缓鍑?
 * @param filePath 闂佸搫鍊稿ú锝呪枎閵忋垺宕夋い鏍ㄦ皑缁?
 * @returns Promise<string> 闁哄鏅滈弻銊ッ洪弽顓炵倞闁告挆鍐炬毈URL
 */
export const uploadTabImage = (roomId: string, filePath: string): Promise<string> => {
  return new Promise<string>((resolve, reject) => {
    const token = getToken();
    if (!token) {
      reject(new Error('未登录，请先登录'));
      return;
    }

    uni.uploadFile({
      url: `${ENV_CONFIG.VITE_BASE_API_URL}/admin/rooms/${roomId}/tabs/image`,
      filePath,
      name: 'file',
      header: {
        'Authorization': `Bearer ${token}`
      },
      success: (res) => {
        if (res.statusCode === 200) {
          try {
            const data = JSON.parse(res.data);
            resolve(data.data.image_url);
          } catch (error) {
            reject(new Error('图片上传响应解析失败'));
          }
        } else {
          reject(new Error('图片上传失败'));
        }
      },
      fail: reject
    });
  });
};


