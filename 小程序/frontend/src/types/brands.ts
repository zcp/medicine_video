/**
 * 品牌模块类型定义（严格对齐后端字段）
 */

/**
 * 公开品牌项（GET /api/v1/brands）
 */
export interface BrandItem {
  id: string
  name: string
  slug?: string | null
  logo_url?: string | null
  description?: string | null
  website_url?: string | null
  sort_order: number
  is_active: boolean
  created_at: string
  updated_at: string
}

/**
 * 专题简要信息
 */
export interface TopicBriefItem {
  id: string
  title: string
  banner_url?: string | null
  status?: string | null
  created_at?: string | null
}

/**
 * 品牌内容数据（详情+关联专题）
 */
export interface BrandContentData {
  brand_info: BrandItem
  associated_topics: TopicBriefItem[]
}

/**
 * 创建品牌请求（Admin）
 */
export interface CreateBrandRequest {
  name: string
  slug?: string | null
  logo_url?: string | null
  description?: string | null
  website_url?: string | null
  sort_order?: number
  is_active?: boolean
}

/**
 * 更新品牌请求（Admin，部分字段）
 */
export interface UpdateBrandRequest {
  name?: string
  slug?: string | null
  logo_url?: string | null
  description?: string | null
  website_url?: string | null
  sort_order?: number
  is_active?: boolean
}

/**
 * 品牌列表查询（公开接口）
 */
export interface BrandListQuery {
  q?: string
  limit?: number
}

/**
 * 直播间品牌 Tab 展示项（GET /api/v1/rooms/{room_id}/brands）
 * 严格对齐《品牌管理·品牌专题关联·品牌直播间关联》文档 4.3.3
 */
export interface RoomBrandItem {
  id: string
  name: string
  slug?: string | null
  logo_url?: string | null
  website_url?: string | null
  sort_order: number
  /** 可选；C 端兜底过滤用，显式 false 不展示（16-D5） */
  is_active?: boolean
}

/**
 * 直播间品牌 Tab 数据（支持默认数组/增强结构化分组）
 */
export type RoomBrandsTabData =
  | RoomBrandItem[]
  | {
      room_brands: RoomBrandItem[]
      topic_brands: RoomBrandItem[]
    }

/**
 * 品牌关联直播间项（GET /api/v1/admin/brands/{brand_id}/rooms）
 * 严格对齐《品牌管理·品牌专题关联·品牌直播间关联》文档 4.3.4
 */
export interface BrandRoomItem {
  room_id: string
  room_title: string
  description?: string | null
  is_private?: boolean
  cover_url?: string | null
  associated_at: string
}
