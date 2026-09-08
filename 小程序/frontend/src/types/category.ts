/**
 * 科室分类管理（Category）类型定义
 * 以后端设计文档为准：categories 表 DDL + Pydantic Schema
 */

/**
 * 分类信息（对应后端 CategoryItem Schema）
 * DDL: categories 表, slug VARCHAR(100) NOT NULL UNIQUE
 */
export interface Category {
  /** 分类唯一标识（UUID） */
  id: string
  /** 分类名称（1-100字符） */
  name: string
  /** C 端展示口语名（可选） */
  display_name?: string
  /** URL友好标识（必填，唯一，仅小写字母+数字+连字符） */
  slug: string
  /** 分类图标URL（可选，最大500字符） */
  icon?: string
  /** 分类描述说明 */
  description?: string
  /** 排序权重（升序，0最前） */
  sort_order: number
  /** 是否启用状态（软删除标记） */
  is_active: boolean
  /** 父分类 ID（V2 树；根节点为空） */
  parent_id?: string | null
  /** tree=true 时的子节点 */
  children?: Category[]
  /** 房间关联响应偶发：是否主分类 */
  is_primary?: boolean
  /** 创建时间（ISO 8601格式） */
  created_at: string
  /** 最后更新时间（ISO 8601格式） */
  updated_at: string
}

/**
 * 创建分类请求参数（对应后端 CategoryCreate Schema）
 * slug 为必填（后端 Field(..., min_length=1, max_length=100)）
 */
export interface CategoryCreate {
  /** 分类名称（必填，1-100字符） */
  name: string
  /** C 端展示口语名（可选） */
  display_name?: string
  /** URL友好标识（必填，唯一，仅小写字母+数字+连字符） */
  slug: string
  /** 分类图标URL（可选） */
  icon?: string
  /** 分类描述说明（可选） */
  description?: string
  /** 排序权重（可选，默认0） */
  sort_order?: number
  /** 是否启用状态（可选，默认true） */
  is_active?: boolean
}

/**
 * 更新分类请求参数（部分更新）
 */
export interface CategoryUpdate {
  /** 分类名称（可选） */
  name?: string
  /** C 端展示口语名（可选） */
  display_name?: string
  /** URL友好的标识符（可选） */
  slug?: string
  /** 分类图标URL（可选） */
  icon?: string
  /** 分类描述说明（可选） */
  description?: string
  /** 排序权重（可选） */
  sort_order?: number
  /** 是否启用状态（可选） */
  is_active?: boolean
}

/**
 * 分类分页查询结果
 */
export interface CategoryPageResult {
  /** 分类列表 */
  items: Category[]
  /** 总数 */
  total: number
  /** 当前页码 */
  page: number
  /** 每页数量 */
  page_size: number
}

/**
 * 直播间分类关联设置请求
 */
export interface LiveRoomCategoriesSetRequest {
  /** 分类ID列表 */
  category_ids: string[]
  /** 关联模式：replace（替换）或 append（追加） */
  mode: 'replace' | 'append'
  /** 主分类；不传则后端默认列表首个 */
  primary_category_id?: string | null
}

/** 删除分类遇引用时的 409 references（《20》V2.2 / main 对齐） */
export interface CategoryReferences {
  expert_all: number
  expert_active: number
  department_count: number
  room_count: number
  active_child_count: number
}

/** 迁移引用统计 */
export interface CategoryMigrateStats {
  expert_count: number
  department_count: number
  room_count: number
}

/** 合并分类结果（含 dry_run） */
export interface CategoryMergeResult {
  dry_run: boolean
  expert_count: number
  department_count: number
  room_count: number
  child_count: number
  inconsistent_expert_count: number
  message: string
}

export type CategoryMigrateScope = 'all' | 'experts' | 'departments' | 'rooms'

export interface CategoryDeleteOptions {
  force?: boolean
  target_category_id?: string
}
