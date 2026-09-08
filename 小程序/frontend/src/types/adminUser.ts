/**
 * 管理端用户管理类型
 * 对齐 docs/Live-Saas-Wechat-14-管理端用户管理-账号能力模型与权限修订-设计文档-v2.0.md
 * V1 基线见 docs/Live-Saas-Wechat-14-管理端用户管理-后端设计文档-v1.1.md
 * 前端约定见 docs/Live-Saas-Wechat-14-管理端用户管理-账号能力模型与权限修订-前端设计文档-v2.0.md
 */

/** 用户角色 — 对齐后端 user_role 枚举 */
export type AdminUserRole = 'REGULAR' | 'MODERATOR' | 'ADMIN' | 'SUPERADMIN'

/** 用户状态 — 对齐后端 entity_status 枚举 */
export type AdminEntityStatus =
  | 'NORMAL'
  | 'BANNED'
  | 'DELETED'
  | 'PENDING_REVIEW'
  | 'REJECTED'

/** 管理端用户响应（对应后端 UserResponse + V2 can_stream） */
export interface AdminUserResponse {
  id: number
  public_id: string
  username: string
  nickname: string
  email: string | null
  phone_number: string | null
  avatar_url: string | null
  bio: string | null
  role: AdminUserRole
  status: AdminEntityStatus
  /** 【V2.1】是否可开播；缺省 true；false=禁止开播 */
  can_stream: boolean
  is_email_verified: boolean
  is_phone_verified: boolean
  last_login_at: string | null
  last_login_ip: string | null
  social_provider: string | null
  social_id: string | null
  created_at: string
  updated_at: string
}

/** 管理端 PATCH 更新（对应后端 UserUpdate — V2） */
export interface AdminUserUpdatePayload {
  role?: AdminUserRole
  status?: AdminEntityStatus
  can_stream?: boolean
  nickname?: string
}

/** 管理端列表 Query（V2：phone_number / nickname / can_stream） */
export interface AdminUserListQuery {
  page?: number
  size?: number
  sort?: string
  username?: string
  email?: string
  phone_number?: string
  nickname?: string
  role?: AdminUserRole
  status?: AdminEntityStatus
  can_stream?: boolean
}

/** 管理端分页结果 */
export interface AdminUserPageResult {
  total: number
  page: number
  size: number
  items: AdminUserResponse[]
}

export const ADMIN_USER_ROLE_LABEL: Record<AdminUserRole, string> = {
  REGULAR: '普通用户',
  MODERATOR: '版主',
  ADMIN: '管理员',
  SUPERADMIN: '超级管理员'
}

/** 日常角色筛选可选（隐藏 MODERATOR） */
export const ADMIN_USER_ROLE_DAILY_OPTIONS: AdminUserRole[] = ['REGULAR', 'ADMIN', 'SUPERADMIN']

/** 日常状态主路径（运营主按钮） */
export const ADMIN_USER_STATUS_DAILY_OPTIONS: AdminEntityStatus[] = ['NORMAL', 'BANNED']

const LEGACY_ROLE_MAP: Record<string, AdminUserRole> = {
  USER: 'REGULAR',
  REGULAR: 'REGULAR',
  MODERATOR: 'MODERATOR',
  ADMIN: 'ADMIN',
  SUPERADMIN: 'SUPERADMIN',
  EXPERT: 'REGULAR'
}

const LEGACY_STATUS_MAP: Record<string, AdminEntityStatus> = {
  ACTIVE: 'NORMAL',
  NORMAL: 'NORMAL',
  DISABLED: 'BANNED',
  BANNED: 'BANNED',
  DELETED: 'DELETED',
  PENDING_REVIEW: 'PENDING_REVIEW',
  REJECTED: 'REJECTED'
}

/** 兼容后端大写枚举与旧版小写 role（admin/user/expert） */
export function normalizeAdminUserRole(role?: string | null): AdminUserRole {
  const key = (role || '').trim().toUpperCase()
  return LEGACY_ROLE_MAP[key] || 'REGULAR'
}

/** 兼容旧版 active/disabled/deleted 状态值 */
export function normalizeAdminEntityStatus(status?: string | null): AdminEntityStatus {
  const key = (status || '').trim().toUpperCase()
  return LEGACY_STATUS_MAP[key] || 'NORMAL'
}

/** V2.1：缺省 / null → true（默认可播）；仅显式 false 为禁止开播 */
export function normalizeCanStream(value?: boolean | null): boolean {
  return value !== false
}

export function getAdminUserRoleLabel(role?: string | null): string {
  return ADMIN_USER_ROLE_LABEL[normalizeAdminUserRole(role)]
}

export function getAdminUserStatusLabel(status?: string | null): string {
  return ADMIN_USER_STATUS_LABEL[normalizeAdminEntityStatus(status)]
}

export function normalizeAdminUserResponse(
  user: AdminUserResponse | (Omit<AdminUserResponse, 'can_stream'> & { can_stream?: boolean })
): AdminUserResponse {
  return {
    ...user,
    role: normalizeAdminUserRole(user.role),
    status: normalizeAdminEntityStatus(user.status),
    can_stream: normalizeCanStream(user.can_stream)
  }
}

export const ADMIN_USER_STATUS_LABEL: Record<AdminEntityStatus, string> = {
  NORMAL: '正常',
  BANNED: '已禁用',
  DELETED: '已注销',
  PENDING_REVIEW: '待审核',
  REJECTED: '已拒绝'
}

export function isSuperAdminRole(role?: string | null): boolean {
  return (role || '').toUpperCase() === 'SUPERADMIN'
}

export function isAdminRole(role?: string | null): boolean {
  const normalized = (role || '').toUpperCase()
  return normalized === 'ADMIN' || normalized === 'SUPERADMIN'
}

/** 仅 SUPERADMIN 可修改他人 role（V2） */
export function canChangeUserRole(operatorRole?: string | null): boolean {
  return isSuperAdminRole(operatorRole)
}

/**
 * 是否允许打开编辑弹窗（V2）
 * - 不可编辑自己
 * - ADMIN 不可编辑 SUPERADMIN
 */
export function canEditAdminUser(
  targetRole: AdminUserRole,
  operatorRole?: string | null,
  options?: { targetPublicId?: string | null; operatorPublicId?: string | null }
): boolean {
  const targetId = (options?.targetPublicId || '').trim()
  const operatorId = (options?.operatorPublicId || '').trim()
  if (targetId && operatorId && targetId === operatorId) return false
  if (isSuperAdminRole(operatorRole)) return true
  return targetRole !== 'SUPERADMIN'
}

/**
 * 超管可设角色（不含 MODERATOR）；ADMIN 不可改 role → 空数组
 */
export function getEditableRoleOptions(operatorRole?: string | null): AdminUserRole[] {
  if (!isSuperAdminRole(operatorRole)) return []
  return ['REGULAR', 'ADMIN', 'SUPERADMIN']
}

/** 日常状态选项：NORMAL / BANNED */
export function getDailyStatusOptions(): AdminEntityStatus[] {
  return [...ADMIN_USER_STATUS_DAILY_OPTIONS]
}

/** 日常角色筛选：REGULAR / ADMIN；超管另加 SUPERADMIN；不含 MODERATOR */
export function getDailyRoleFilterOptions(operatorRole?: string | null): AdminUserRole[] {
  const base: AdminUserRole[] = ['REGULAR', 'ADMIN']
  if (isSuperAdminRole(operatorRole)) return [...base, 'SUPERADMIN']
  return base
}
