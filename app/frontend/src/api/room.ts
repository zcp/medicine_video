/**
 * 房间相关API
 * 阶段一修订：统一返回类型为 ApiResponse<T>
 * 封装所有与"房间"相关的API请求
 */
import { get, post, patch, del } from '@/utils/request';
import type { Room, RoomCreatePayload } from '@/types/room';
import type { ApiResponse, PaginatedResponse } from '@/types/common';
import { getToken } from '@/store/auth';
import { ENV_CONFIG } from '@/config/env';

/**
 * 获取房间列表
 * @param params 分页参数
 * @returns Promise<ApiResponse<PaginatedResponse<Room>>>
 * @example
 * const res = await getRoomList({ page: 1, size: 20 });
 * const rooms = res.data.items;
 */
export const getRoomList = (params: { page?: number; size?: number; q?: string; parent_room_id?: string } = {}, options: { showLoading?: boolean } = {}): Promise<ApiResponse<PaginatedResponse<Room>>> => {
  return get<ApiResponse<PaginatedResponse<Room>>>('/rooms', params, { ...options });
};

/**
 * 获取当前用户创建的房间列表（含私密房，响应透出 is_private）
 * @param params 分页/搜索/排序参数
 * @returns Promise<ApiResponse<PaginatedResponse<Room>>>
 * @example
 * const res = await getMyRooms({ page: 1, size: 20 });
 * const myRooms = res.data.items;
 */
export const getMyRooms = (params: { page?: number; size?: number; q?: string; sort?: string } = {}): Promise<ApiResponse<PaginatedResponse<Room>>> => {
  return get<ApiResponse<PaginatedResponse<Room>>>('/users/me/rooms', params, { auth: true });
};

/**
 * 获取单个房间详情
 * @param roomId 房间ID
 * @returns Promise<ApiResponse<Room>>
 * @example
 * const res = await getRoomDetail('room-uuid');
 * const room = res.data;
 */
export const getRoomDetail = (roomId: string, options: { showLoading?: boolean } = {}): Promise<ApiResponse<Room>> => {
  return get<ApiResponse<Room>>(`/rooms/${roomId}`, undefined, { ...options });
};

/**
 * 创建一个新的直播间
 * @param payload 创建房间所需的数据
 * @returns Promise<ApiResponse<Room>>
 * @example
 * const res = await createRoom({ title: '直播间标题', description: '描述' });
 * const newRoom = res.data;
 */
export const createRoom = (payload: RoomCreatePayload): Promise<ApiResponse<Room>> => {
  return post<ApiResponse<Room>>('/rooms', payload, { auth: true });
};

/**
 * 更新房间
 * @param roomId 房间ID
 * @param data 要更新的房间数据
 * @returns Promise<ApiResponse<Room>>
 */
export const updateRoom = (roomId: string, data: Partial<Room>): Promise<ApiResponse<Room>> => {
  // 后端仅暴露 PATCH /rooms/{room_id}（room.py:394），PUT 会 405
  return patch<ApiResponse<Room>>(`/rooms/${roomId}`, data, { auth: true });
};

/**
 * 删除房间
 * @param roomId 房间ID
 * @returns Promise<ApiResponse<void>>
 */
export const deleteRoom = (roomId: string): Promise<ApiResponse<void>> => {
  return del<ApiResponse<void>>(`/rooms/${roomId}`, undefined, { auth: true });
};

/**
 * 上传房间封面（管理员/房主接口）
 * 后端自动更新房间 cover_url 并返回 { cover_url }
 * @param roomId 房间ID
 * @param filePath 本地临时文件路径
 * @returns Promise<ApiResponse<{ cover_url: string }>>
 */
export const uploadRoomCover = (
  roomId: string,
  filePath: string
): Promise<ApiResponse<{ cover_url: string }>> => {
  const token = getToken();
  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url: `${ENV_CONFIG.VITE_BASE_API_URL}/rooms/${roomId}/cover`,
      filePath,
      name: 'file',
      header: token ? { Authorization: `Bearer ${token}` } : {},
      success: (res) => {
        try {
          resolve(JSON.parse(res.data));
        } catch {
          reject(new Error('响应解析失败'));
        }
      },
      fail: (err) => reject(err),
    });
  });
};

/**
 * 获取主会场下所有分会场
 * @param roomId 主会场ID
 * @param params 分页参数
 * @returns Promise<ApiResponse<PaginatedResponse<Room>>>
 */
export const getSubVenues = (roomId: string, params: { page?: number; size?: number } = {}): Promise<ApiResponse<PaginatedResponse<Room>>> => {
  return get<ApiResponse<PaginatedResponse<Room>>>(`/rooms/${roomId}/sub-venues`, params);
};

/**
 * 创建分会场
 * @param payload 创建分会场的数据，包含 parent_room_id
 * @returns Promise<ApiResponse<Room>>
 */
export const createSubVenue = (payload: RoomCreatePayload & { parent_room_id: string }): Promise<ApiResponse<Room>> => {
  return post<ApiResponse<Room>>('/rooms', payload, { auth: true });
};

/**
 * 更新分会场
 * @param roomId 分会场ID
 * @param data 要更新的数据
 * @returns Promise<ApiResponse<Room>>
 */
export const updateSubVenue = (roomId: string, data: Partial<Room>): Promise<ApiResponse<Room>> => {
  return patch<ApiResponse<Room>>(`/rooms/${roomId}`, data, { auth: true });
};

/**
 * 删除分会场
 * @param roomId 分会场ID
 * @returns Promise<ApiResponse<void>>
 */
export const deleteSubVenue = (roomId: string): Promise<ApiResponse<void>> => {
  return del<ApiResponse<void>>(`/rooms/${roomId}`, undefined, { auth: true });
};

/**
 * 获取全站房间列表（管理员接口）
 * @param params 查询参数（支持q标题搜索、owner_user_id房主筛选、is_private私密筛选、page/size分页）
 * @returns Promise<ApiResponse<PaginatedResponse<Room>>>
 */
export const getAdminRooms = (
  params: { page?: number; size?: number; q?: string; owner_user_id?: string; is_private?: boolean } = {}
): Promise<ApiResponse<PaginatedResponse<Room>>> => {
  return get<ApiResponse<PaginatedResponse<Room>>>('/admin/rooms', params, { auth: true, showLoading: false }, { retry: 1, timeout: 8000 });
}; 