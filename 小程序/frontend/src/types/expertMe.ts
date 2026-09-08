/**
 * 专家认领 /experts/me（P1）
 * @deprecated 《14-V2》V2.2 已裁剪：后端接口已删除，类型仅保留兼容旧引用
 */

/** GET /api/core/experts/me 响应（核心字段；未绑定时 data 为 null） */
export interface MyExpertResponse {
  id: string
  name: string
  avatar_url?: string | null
  title?: string | null
  hospital?: string | null
  department?: string | null
  bio?: string | null
  expertise_areas?: string | string[] | null
  user_id?: string | null
  is_active?: boolean
  created_at?: string
  updated_at?: string
}

/** PATCH /api/core/experts/me — 仅提交变更字段 */
export interface MyExpertUpdatePayload {
  name?: string
  title?: string
  hospital?: string
  department?: string
  bio?: string
  expertise_areas?: string
}

export function normalizeExpertiseAreas(value?: string | string[] | null): string {
  if (Array.isArray(value)) return value.filter(Boolean).join('、')
  return String(value || '').trim()
}
