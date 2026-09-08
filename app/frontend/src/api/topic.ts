import { get, post, put, del, patch } from '@/utils/request'
import type {
  Topic,
  TopicCategory,
  RoomInCategory,
  TopicCreate,
  TopicUpdate,
  CategoryCreate,
  CategoryUpdate,
  AddRoomsRequest,
  UpdateRoomSortRequest,
  RemoveRoomsRequest,
  BatchStatusRequest,
  RoomStatusInfo,
  RoomTopicInfo,
  PaginatedResponse,
  ApiResponse,
  TopicDetailResponse,
  TopicListParams
} from '@/types/topic'

/**
 * 过滤掉对象中值为 undefined 的字段
 * @param obj 原始对象
 * @returns 过滤后的对象
 */
const filterUndefined = <T extends Record<string, any>>(obj: T): Partial<T> => {
  const result: any = {};
  Object.keys(obj).forEach(key => {
    if (obj[key] !== undefined) {
      result[key] = obj[key];
    }
  });
  return result;
};

/**
 * 专题相关 API（对齐 room.ts 的风格，聚焦核心 CRUD 与关联操作）
 */
export const topicApi = {
  // 专题 CRUD
  getTopics: (params?: TopicListParams): Promise<PaginatedResponse<Topic>> =>
    get('/topics', params ? filterUndefined(params) : undefined),

  getTopicById: (topicId: string): Promise<ApiResponse<TopicDetailResponse>> =>
    get(`/topics/${topicId}`),

  createTopic: (payload: Pick<TopicCreate, 'title' | 'description' | 'banner_url' | 'status'>): Promise<ApiResponse<Topic>> =>
    post('/topics', payload, { auth: true }),

  updateTopic: (topicId: string, data: TopicUpdate): Promise<ApiResponse<Topic>> =>
    // 使用 PATCH 方法更新专题（后端要求）
    patch(`/topics/${topicId}`, data, { auth: true }),

  deleteTopic: (topicId: string): Promise<ApiResponse<void>> =>
    del(`/topics/${topicId}`, undefined, { auth: true }),

  // 分类管理
  getCategories: (topicId: string): Promise<PaginatedResponse<TopicCategory>> =>
    get(`/topics/${topicId}/categories`),

  createCategory: (topicId: string, data: CategoryCreate): Promise<ApiResponse<TopicCategory>> =>
    post(`/topics/${topicId}/categories`, data, { auth: true }),

  updateCategory: (categoryId: string, data: CategoryUpdate): Promise<ApiResponse<TopicCategory>> =>
    // 使用 PATCH 方法更新分类（后端要求）
    patch(`/topic-categories/${categoryId}`, data, { auth: true }),

  deleteCategory: (categoryId: string): Promise<ApiResponse<void>> =>
    del(`/topic-categories/${categoryId}`, undefined, { auth: true }),

  // 分类下直播间关联
  getCategoryRooms: (categoryId: string): Promise<PaginatedResponse<RoomInCategory>> =>
    get(`/topic-categories/${categoryId}/rooms`),

  addRoomsToCategory: (categoryId: string, data: AddRoomsRequest): Promise<ApiResponse<void>> =>
    post(`/topic-categories/${categoryId}/rooms`, data, { auth: true }),

  updateRoomSortOrder: (categoryId: string, data: UpdateRoomSortRequest): Promise<ApiResponse<void>> =>
    put(`/topic-categories/${categoryId}/rooms/sort-order`, data, { auth: true }),

  removeRoomsFromCategory: (categoryId: string, data: RemoveRoomsRequest): Promise<ApiResponse<void>> =>
    del(`/topic-categories/${categoryId}/rooms`, data, { auth: true }),

  // 辅助查询（供前端校验/展示使用）
  getRoomTopics: (roomId: string): Promise<ApiResponse<RoomTopicInfo[]>> =>
    get(`/rooms/${roomId}/topics`),

  getBatchRoomStatus: (data: BatchStatusRequest): Promise<ApiResponse<RoomStatusInfo[]>> =>
    post('/rooms/batch-status', data),

  // 横幅上传（使用uni.uploadFile，这里仅作类型定义）
  uploadBanner: (topicId: string, filePath: string): Promise<{ banner_url: string }> => {
    // 注意：实际实现使用 uni.uploadFile，这里仅作类型定义
    throw new Error('请使用 uni.uploadFile 直接调用 /topics/{topicId}/banner')
  },
}

export default topicApi
