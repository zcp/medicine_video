/**
 * 内容安全类型定义
 * 对齐后端 content_safety 表与 /admin/content-safety 端点契约
 */

/** live_core 管理端可维护的场景（不含 nickname） */
export type AdminContentScene =
  | 'message'
  | 'room_title'
  | 'room_description'
  | 'room_tab'
  | 'search_query'

/** 全量 scene 枚举（日志筛选/展示用） */
export type ContentScene = AdminContentScene | 'nickname'

export type ContentSafetyAction = 'block' | 'warn' | 'allow'
export type BindingLevel = 'statutory' | 'platform'

export interface ContentSafetyRule {
  id: string
  rule_name: string
  scene: ContentScene
  target_field: string
  match_type: string
  pattern: string
  action: ContentSafetyAction
  severity: 'low' | 'medium' | 'high' | 'critical'
  priority: number
  enabled: boolean
  remark?: string
  binding_level: BindingLevel
  rule_category: string
  regulation_ref?: string
  created_by?: string
  created_at: string
  updated_at: string
}

export interface ContentSafetyRuleCreate {
  rule_name: string
  scene: AdminContentScene
  target_field: string
  match_type: string
  pattern: string
  action?: ContentSafetyAction
  severity?: ContentSafetyRule['severity']
  priority?: number
  enabled?: boolean
  remark?: string
  binding_level?: BindingLevel
  rule_category?: string
  regulation_ref?: string
}

/** PATCH 仅允许更新以下字段 */
export interface ContentSafetyRuleUpdate {
  pattern?: string
  action?: ContentSafetyAction
  severity?: ContentSafetyRule['severity']
  priority?: number
  enabled?: boolean
  remark?: string
}

export interface ContentSafetyLogQueryParams {
  scene?: string
  resource_type?: string
  user_id?: string
  decision?: 'allow' | 'warn' | 'block'
  start_time?: string
  end_time?: string
  page?: number
  page_size?: number
}

export interface ContentSafetyLog {
  id: string
  scene: string
  resource_type: string
  resource_id?: string
  target_field: string
  user_id?: string
  user_nickname?: string | null
  username?: string | null
  user?: { nickname?: string | null; username?: string | null; avatar_url?: string | null } | null
  input_excerpt?: string
  normalized_excerpt?: string
  decision: 'allow' | 'warn' | 'block'
  matched_rule_ids?: string[] | null
  matched_rule_names?: string[]
  reason_code?: string
  reason_message?: string
  client_ip?: string
  created_at: string
}

export interface ContentSafetyRuleListParams {
  scene?: AdminContentScene
  page?: number
  page_size?: number
}

export interface PaginatedContentSafetyRules {
  total: number
  page: number
  page_size: number
  items: ContentSafetyRule[]
}

export interface PaginatedContentSafetyLogs {
  total: number
  page: number
  page_size: number
  items: ContentSafetyLog[]
}
