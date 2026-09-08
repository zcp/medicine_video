// 专题相关类型定义（对齐后端 Pydantic Schema，参考 room.ts 的风格）

// 专题状态枚举（与后端 TopicStatus 枚举一致）
export type TopicStatus = 'draft' | 'published' | 'archived'

// ===== 基础实体 =====
// 专题（数据库/接口返回的主体）
export interface Topic {
  id: string
  user_id: string
  title: string
  description?: string
  banner_url?: string
  status: TopicStatus
  created_at: string
  updated_at: string
}

// 专题分类
export interface TopicCategory {
  id: string
  topic_id: string
  name: string
  sort_order: number
  created_at: string
  updated_at: string
  rooms?: RoomInCategory[]
}

// 分类中的直播间信息
export interface RoomInCategory {
  id: string
  title: string
  cover_url?: string
  live_status: string
  start_time?: string
  heat: number
  // 关联排序可由后端拼装返回，非必填
  sort_order?: number
}

// 带直播间的分类（用于专题详情）
export interface CategoryWithRooms extends TopicCategory {
  rooms: RoomInCategory[]
}

// 专题聚合详情（Topic + categories）
export interface TopicDetail extends Topic {
  categories: CategoryWithRooms[]
}

// 专题创建请求
export interface TopicCreate {
  title: string
  description?: string
  banner_url?: string
  status: TopicStatus
  categories?: CategoryCreate[]
}

// 专题更新请求
export interface TopicUpdate {
  title?: string
  description?: string
  banner_url?: string
  status?: TopicStatus
}

// 分类创建请求
export interface CategoryCreate {
  name: string
  sort_order?: number
}

// 分类更新请求
export interface CategoryUpdate {
  name?: string
  sort_order?: number
}

// 直播间关联信息
export interface RoomAssociation {
  room_id: string
  sort_order: number
}

// 专题列表查询参数
export interface TopicListParams {
  page?: number
  page_size?: number
  status?: TopicStatus
  search?: string
  sort_by?: 'created_at' | 'updated_at' | 'title'
  sort_order?: 'asc' | 'desc'
}

// 专题列表响应
export interface TopicListResponse {
  items: Topic[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

// 分类列表响应
export interface CategoryListResponse {
  items: TopicCategory[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

// 直播间列表响应
export interface RoomListResponse {
  items: RoomInCategory[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

// 添加直播间到分类请求
export interface AddRoomsRequest {
  rooms: RoomAssociation[]
}

// 更新直播间排序请求
export interface UpdateRoomSortRequest {
  rooms: RoomAssociation[]
}

// 从分类中移除直播间请求
export interface RemoveRoomsRequest {
  room_ids: string[]
}

// 批量获取直播间状态请求
export interface BatchStatusRequest {
  room_ids: string[]
}

// 直播间状态信息
export interface RoomStatusInfo {
  room_id: string
  live_status: string
  start_time?: string
  end_time?: string
  viewer_count?: number
  heat: number
}

// 专题创建表单数据
export interface TopicCreateForm {
  title: string
  description: string
  banner_url: string
  status: TopicStatus
  categories: CategoryForm[]
}

// 分类表单数据
export interface CategoryForm {
  name: string
  rooms: RoomInCategory[]
}

// API 响应基础结构
export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
  timestamp: string
}

// 分页响应基础结构
export interface PaginatedResponse<T = any> {
  code: number
  message: string
  data: {
    items: T[]
    total: number
    page: number
    page_size: number
    total_pages: number
  }
  timestamp: string
}

// 专题详情响应（包含层级化数据）
export type TopicDetailResponse = TopicDetail

// 直播间关联专题信息（用于辅助查询展示，不对应独立表）
export interface RoomTopicInfo {
  topic_id: string
  topic_title: string
  topic_status: TopicStatus
  category_id: string
  category_name: string
  sort_order: number
}
