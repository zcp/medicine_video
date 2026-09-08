/**
 * 管理端全站房间列表类型
 * 对齐《17-管理端管播MVP-后端设计文档》AdminRoomQueryParams / AdminRoomListItem
 */

/**
 * 管理端全站房间列表 Query（对应后端 AdminRoomQueryParams）
 */
export interface AdminRoomQueryParams {
  /** 标题模糊搜索，最大 100 字符；空/null 勿传 */
  q?: string
  /** 房主 public_id（UUID）；空/null 勿传 */
  owner_user_id?: string
  /** 私密筛选；省略 = 全部（含私密） */
  is_private?: boolean
  page?: number
  /** 后端字段名为 size，非 page_size；1–100 */
  size?: number
}

/**
 * 管理端房间列表项（对应后端 AdminRoomListItem）
 * ⚠️ 不含 stream_key
 */
export interface AdminRoomListItem {
  id: string
  title: string
  description?: string | null
  cover_url?: string | null
  /** 房主 public_id — 运营定位主播的关键字段 */
  owner_user_id: string
  is_private: boolean
  parent_room_id?: string | null
  created_at: string
  updated_at: string
}

/**
 * 管理端房间分页结果（统一分页）
 */
export interface AdminRoomPageResult {
  items: AdminRoomListItem[]
  total: number
  page: number
  size: number
}

/**
 * 运营编辑弹窗本地表单（提交时映射到既有 UpdateRoomRequest）
 */
export interface AdminRoomEditForm {
  title: string
  description: string
  is_private: boolean
  cover_url?: string | null
}
