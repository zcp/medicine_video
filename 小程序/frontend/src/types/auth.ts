/**
 * 认证相关类型定义
 * 对齐 docs/Live-Saas-Wechat-10-用户认证与管理-前端设计文档-v1.7.md V1.4 + V3 增量
 */

export type LoginType = 'password' | 'sms' | 'wechat' | 'phone' | 'email' | 'one_tap'

export type UserRole = 'user' | 'admin' | 'expert'

export type UserStatus = 'active' | 'disabled' | 'deleted'

export type ChannelType = 'EMAIL' | 'SMS'

export type ScenarioType =
  | 'REGISTER'
  | 'PASSWORD_RESET'
  | 'LOGIN'
  | 'BIND_PHONE'
  | 'BIND_EMAIL'

export type Permission =
  | 'user:read'
  | 'user:write'
  | 'room:read'
  | 'room:write'
  | 'room:create'
  | 'room:delete'
  | 'expert:read'
  | 'expert:write'
  | 'admin:access'
  | 'content:manage'

/**
 * 当前登录用户信息（GET /api/v1/users/me）
 * JWT payload 使用 user_id（非 sub）
 */
export interface UserInfo {
  user_id: string
  username: string
  email: string | null
  phone: string | null
  nickname: string | null
  bio?: string | null
  avatar_url: string | null
  role: UserRole
  status: UserStatus
  /** 【V2.1】是否可开播；缺省 true；false=禁止开播 */
  can_stream?: boolean
  is_email_verified?: boolean
  is_phone_verified?: boolean
  public_id?: string | null
  created_at: string
}

/** 与后端 UserProfile Schema 同构 */
export type UserProfile = UserInfo

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: 'bearer' | string
}

export interface CaptchaResponseData {
  captcha_id: string
  captcha_image?: string
  image_base64?: string
}

/** 发送 OTP；所有 scenario（含 LOGIN）发码前须传 captcha */
export interface VerificationCodesRequest {
  channel: ChannelType
  recipient: string
  scenario: ScenarioType
  captcha_id?: string
  captcha_solution?: string
}

/** @deprecated 使用 VerificationCodesRequest */
export type VerificationCodeRequest = VerificationCodesRequest

/** 校验 OTP 并签发 Ticket */
export interface VerifyCodeRequest {
  channel: ChannelType
  recipient: string
  scenario: ScenarioType
  code: string
}

export interface VerifyCodeResponse {
  ticket: string
  expires_in: number
}

export interface RegisterRequest {
  username: string
  email: string
  nickname: string
  password: string
  verification_code: string
  /** 现网后端 RegisterRequest 仍要求；发码时 captcha 已消耗，提交前须换新验证码 */
  captcha_id: string
  captcha_solution: string
  /** 须为 true，否则后端拒绝注册 */
  agreed_to_terms: boolean
}

export interface RegisterResponse {
  user_id: string
  username: string
  email: string
  nickname: string
  is_email_verified: boolean
}

/** 手机号 Ticket 注册 */
export interface PhoneRegisterRequest {
  register_ticket: string
  password: string
  nickname: string
  /** 须为 true，否则后端拒绝注册 */
  agreed_to_terms: boolean
}

export interface PhoneRegisterResponse {
  public_id: string
  username: string
  nickname: string
  phone_number: string
  is_phone_verified: boolean
  is_new_user: boolean
  access_token: string
  refresh_token: string
  token_type: 'bearer' | string
}

/** 手机号 Ticket 登录 */
export interface PhoneLoginRequest {
  login_ticket: string
  /** 须为 true，否则后端拒绝登录 */
  agreed_to_terms: boolean
}

/** 邮箱 Ticket 登录（V3.5：后端 POST /auth/login/email 已就绪） */
export interface EmailLoginRequest {
  login_ticket: string
  /** 须为 true，否则后端拒绝登录 */
  agreed_to_terms: boolean
}

/** 运营商一键登录 */
export interface OneTapLoginRequest {
  carrier_token: string
  provider?: string
  agreed_to_terms: boolean
}

/** 云函数 HMAC 一键登录 */
export interface CloudFunctionLoginRequest {
  phone: string
  sign: string
  timestamp: number
  agreed_to_terms: boolean
}

export interface OneTapLoginResponse extends LoginResponse {
  is_new_user?: boolean
  phone_masked?: string
  user_public_id?: string
  username?: string
  nickname?: string
}

export interface ChangePasswordRequest {
  /** 与后端 PasswordChangeRequest.current_password 对齐 */
  current_password: string
  new_password: string
  /** 图形验证码（前端必填；后端若未校验可忽略） */
  captcha_id?: string
  captcha_solution?: string
}

/** V3：绑定手机号使用 bind_ticket */
export interface BindPhoneRequest {
  phone_number: string
  bind_ticket: string
}

export interface BindEmailRequest {
  email: string
  verification_code: string
}

export interface DeactivateAccountRequest {
  captcha_id: string
  captcha_solution: string
}

export interface UpdateProfileRequest {
  nickname?: string
  bio?: string
}

export interface AvatarUploadResponse {
  avatar_url: string
}

export interface AdminUserUpdate {
  role?: UserRole
  status?: 'active' | 'disabled'
}

export interface RefreshTokenRequest {
  refresh_token: string
}

export interface PasswordResetRequest {
  email: string
  captcha_id: string
  captcha_solution: string
}

/** POST /auth/password-reset — 邮箱 reset_token 或 SMS reset_ticket */
export interface PasswordResetConfirmRequest {
  reset_token?: string
  reset_ticket?: string
  new_password: string
}

export interface SsoLoginRequest {
  id_token: string
}

export interface LoginRequest {
  username: string
  password: string
  captcha_id: string
  captcha_solution: string
  /** 须为 true，否则后端拒绝登录 */
  agreed_to_terms: boolean
}

export interface AuthState {
  isAuthenticated: boolean
  user: UserInfo | null
  token: string | null
  refreshToken: string | null
  permissions: Permission[]
  loading: boolean
  error: string | null
}

export interface JwtPayload {
  user_id: string
  username: string
  role: UserRole
  exp: number
  iat?: number
}
