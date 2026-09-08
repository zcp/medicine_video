/**
 * 专家科室受控词表类型（对齐《20》后端 Pydantic Schema，snake_case）
 */

/** 对应 ExpertDepartmentItem */
export interface ExpertDepartmentItem {
  id: string
  name: string
  category_id: string
  category_name?: string | null
  synonyms: string[]
  is_active: boolean
  is_verified: boolean
  source?: string | null
  created_by?: string | null
  expert_count: number
  created_at: string
  updated_at: string
}

export interface ExpertDepartmentCreate {
  /** 1..120 */
  name: string
  category_id: string
  synonyms?: string[]
  /** 默认 false */
  is_verified?: boolean
  /** 默认 "admin_api" */
  source?: string
}

export interface ExpertDepartmentUpdate {
  name?: string
  category_id?: string
  synonyms?: string[]
  is_active?: boolean
  is_verified?: boolean
}

export interface ExpertDepartmentPageResult {
  items: ExpertDepartmentItem[]
  total: number
  page: number
  /** 禁止写成 page_size */
  size: number
}

export interface BatchVerifyRequest {
  /** 1..200 */
  department_ids: string[]
  /** 默认 true */
  verified?: boolean
}

export interface MergeDepartmentsRequest {
  source_id: string
  target_id: string
}

/** unmapped 列表单项（后端 §3.1.5） */
export interface UnmappedExpertItem {
  id: string
  name: string
  title?: string | null
  hospital?: string | null
  avatar_url?: string | null
  category_id?: string | null
  category_name?: string | null
  expertise_areas?: unknown
  is_active: boolean
  /** 过渡文本 */
  department?: string | null
}

export interface ExpertDepartmentListQuery {
  page?: number
  size?: number
  is_active?: boolean
  is_verified?: boolean
  category_id?: string
  q?: string
}
