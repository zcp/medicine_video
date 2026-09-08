/**
 * 用户相关 API（users-service）
 * 严格对齐：
 * docs/Live-Saas-Wechat-10-用户认证与管理-前端设计文档-v1.7.md
 * docs/Live-Saas-Wechat-14-管理端用户管理-账号能力模型与权限修订-前端设计文档-v2.0.md
 */

import { request } from '@/utils/request'
import { API_PATHS } from '@/config/api'
import { logger } from '@/logs/logger'
import type { ApiResponse } from '@/types/common'
import type {
  UserInfo,
  UpdateProfileRequest,
  ChangePasswordRequest,
  BindPhoneRequest,
  BindEmailRequest,
  DeactivateAccountRequest,
  AvatarUploadResponse
} from '@/types/auth'
import type {
  AdminUserListQuery,
  AdminUserPageResult,
  AdminUserResponse,
  AdminUserUpdatePayload
} from '@/types/adminUser'

/** 本地规范化 /me 字段（phone_number→phone；缺省可播）——内联避免独立模块在小程序里 require 失败 */
function normalizeUserInfo(raw: any): UserInfo {
  const userId = String(raw?.user_id ?? raw?.uuid ?? raw?.public_id ?? '').trim()
  const phoneRaw = raw?.phone ?? raw?.phone_number ?? null
  const phone = phoneRaw != null && String(phoneRaw).trim() ? String(phoneRaw).trim() : null
  return {
    ...(raw && typeof raw === 'object' ? raw : {}),
    user_id: userId,
    username: String(raw?.username ?? ''),
    email: raw?.email ?? null,
    phone,
    nickname: raw?.nickname ?? null,
    bio: raw?.bio ?? null,
    avatar_url: raw?.avatar_url ?? null,
    role: (raw?.role as UserInfo['role']) || 'user',
    status: (raw?.status as UserInfo['status']) || 'active',
    can_stream: raw?.can_stream !== false,
    is_email_verified: raw?.is_email_verified,
    is_phone_verified: raw?.is_phone_verified,
    created_at: raw?.created_at || new Date().toISOString(),
    public_id: raw?.public_id ?? raw?.uuid
  }
}

// ===== 用户基本信息 (users服务) =====

/**
 * 获取当前用户信息
 * GET /users/me
 * JWT 认证
 */
export const getMyProfile = async (): Promise<ApiResponse<UserInfo>> => {
  logger.info('network', '[getMyProfile] 开始获取当前用户信息', {
    配置路径: API_PATHS.USER.ME,
    完整URL: API_PATHS.USER.ME
  })

  const res = await request.get(API_PATHS.USER.ME, { showError: false })
  if (res?.data) {
    res.data = normalizeUserInfo(res.data)
  }
  return res as ApiResponse<UserInfo>
}

// 保持向后兼容
export const getCurrentUser = getMyProfile

/**
 * 更新当前用户信息
 * PATCH /users/me — 仅 nickname / bio，禁止 avatar_url
 */
export const updateMyProfile = async (data: UpdateProfileRequest): Promise<ApiResponse<UserInfo>> => {
  const res = await request.patch(API_PATHS.USER.UPDATE, data, {
    loading: true,
    loadingText: '保存中...',
    showError: false
  })
  if (res?.data) {
    res.data = normalizeUserInfo(res.data)
  }
  return res as ApiResponse<UserInfo>
}

// 保持向后兼容
export const updateProfile = updateMyProfile

/**
 * 上传用户头像
 * POST /users/me/avatar — multipart 字段名 file
 */
export const uploadAvatar = (filePath: string): Promise<ApiResponse<AvatarUploadResponse>> => {
  return request.upload({
    url: API_PATHS.USER.AVATAR,
    filePath,
    name: 'file',
    loading: true,
    loadingText: '上传中...',
    showError: false
  })
}

/**
 * 绑定/更换手机号
 * POST /users/me/phone
 * JWT 认证，body: phone_number, bind_ticket（V3）
 */
export const bindMyPhone = (data: BindPhoneRequest): Promise<ApiResponse<void>> => {
  return request.post(API_PATHS.USER.PHONE, data, { loading: true, loadingText: '绑定中...' })
}

// 保持向后兼容
export const bindPhone = bindMyPhone

/**
 * 修改密码
 * POST /users/me/password
 * JWT 认证，body: current_password, new_password
 * 修改后撤销所有 Refresh Token，强制重新登录
 */
export const changeMyPassword = (data: ChangePasswordRequest): Promise<ApiResponse<void>> => {
  return request.post(API_PATHS.USER.PASSWORD, data, { loading: true, loadingText: '修改中...' })
}

// 保持向后兼容
export const changePassword = changeMyPassword

/**
 * 注销账号（软删除）
 * DELETE /users/me — Body: DeactivateAccountRequest
 */
export const deleteMyAccount = (data: DeactivateAccountRequest): Promise<ApiResponse<void>> => {
  return request.delete(API_PATHS.USER.DELETE, {
    data,
    loading: true,
    loadingText: '注销中...'
  })
}

// 保持向后兼容
export const deleteAccount = deleteMyAccount

/**
 * 绑定/更换邮箱
 * POST /users/me/email
 * JWT 认证，body: email, verification_code
 * 需要先发送邮箱验证码（channel=EMAIL, scenario=BIND_EMAIL）
 */
export const updateMyEmail = (data: BindEmailRequest): Promise<ApiResponse<void>> => {
  return request.post(API_PATHS.USER.EMAIL, data, { loading: true, loadingText: '绑定中...' })
}
export const bindEmail = updateMyEmail

// ============ 管理员接口 ============

/**
 * 管理端用户列表（分页+筛选）
 * 网关: GET /api/users/admin/users
 * JWT + Admin 认证
 */
export const getAdminUsers = (
  params?: AdminUserListQuery
): Promise<ApiResponse<AdminUserPageResult>> => {
  return request.get(API_PATHS.ADMIN_USER.USERS, { data: params })
}

/**
 * 管理员更新用户（角色/状态/开播开关）
 * 网关: PATCH /api/users/admin/users/{user_uuid}
 * V2.1：ADMIN 仅可写 status∈{NORMAL,BANNED} 与 can_stream（禁止/恢复开播）；改 role 仅 SUPERADMIN
 */
export const adminUpdateUser = (
  userUuid: string,
  data: AdminUserUpdatePayload
): Promise<ApiResponse<AdminUserResponse>> => {
  return request.patch(API_PATHS.ADMIN_USER.USER_DETAIL(userUuid), data, {
    loading: true,
    loadingText: '保存中...'
  })
}

export default {
  getMyProfile,
  getCurrentUser,
  updateMyProfile,
  updateProfile,
  uploadAvatar,
  bindMyPhone,
  bindPhone,
  changeMyPassword,
  changePassword,
  deleteMyAccount,
  deleteAccount,
  updateMyEmail,
  bindEmail,
  getAdminUsers,
  adminUpdateUser
}
