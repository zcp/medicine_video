/**
 * 认证模块类型定义
 * 包含登录、注册、SSO、密码重置等相关类型
 */

/**
 * 验证码响应
 */
export interface CaptchaResponse {
  /** 验证码ID，用于后续验证 */
  captcha_id: string;
  /** Base64编码的验证码图片，格式：data:image/png;base64,xxx */
  image_base64: string;
}

/**
 * 登录请求
 */
export interface LoginRequest {
  /** 登录标识：用户名或邮箱，后端字段名为 username */
  username: string;
  /** 密码 */
  password: string;
  /** 验证码ID */
  captcha_id: string;
  /** 验证码答案 */
  captcha_solution: string;
}

/**
 * 登录响应
 */
export interface LoginResponse {
  /** 访问令牌（15分钟有效期） */
  access_token: string;
  /** 刷新令牌（7天有效期） */
  refresh_token: string;
  /** 令牌类型 */
  token_type: 'bearer';
}

/**
 * SSO登录请求
 */
export interface SSOLoginRequest {
  /** Authing返回的id_token */
  id_token: string;
}

/**
 * 刷新Token请求
 */
export interface RefreshTokenRequest {
  /** 刷新令牌 */
  refresh_token: string;
}

/**
 * 刷新Token响应
 */
export interface RefreshTokenResponse {
  /** 新的访问令牌 */
  access_token: string;
  /** 令牌类型 */
  token_type: 'bearer';
}

/**
 * 用户信息
 */
export interface UserInfo {
  /** 用户UUID */
  uuid: string;
  /** 用户名 */
  username: string;
  /** 邮箱 */
  email: string;
  /** 手机号（可选） */
  phone_number?: string;
  /** 昵称 */
  nickname: string;
  /** 头像URL（可选） */
  avatar_url?: string;
  /** 个人简介（可选） */
  bio?: string;
  /** 用户角色 */
  role: 'REGULAR' | 'MODERATOR' | 'ADMIN' | 'SUPERADMIN';
  /** 用户状态 */
  status: 'NORMAL' | 'BANNED' | 'DELETED' | 'PENDING_REVIEW' | 'REJECTED';
  /** 邮箱是否已验证 */
  is_email_verified: boolean;
  /** 手机号是否已验证（可选） */
  is_phone_verified?: boolean;
  /** Whether a login password has been set */
  has_password?: boolean;
  /** 是否拥有开播资格 */
  can_stream?: boolean;
}

/**
 * 密码重置请求
 */
export interface PasswordResetRequest {
  /** 邮箱地址 */
  email: string;
  /** 验证码ID */
  captcha_id: string;
  /** 验证码答案 */
  captcha_solution: string;
}

/**
 * 密码重置执行
 */
export interface PasswordResetExecute {
  /** 重置令牌（邮箱方式，旧路径保留兼容） */
  reset_token?: string;
  /** 重置票据（OTP 验证方式，Phase 2 新增） */
  reset_ticket?: string;
  /** 新密码 */
  new_password: string;
}

/**
 * 发送OTP验证码请求（邮件或短信）
 */
export interface SendOtpRequest {
  /** 发送渠道：EMAIL 或 SMS */
  channel: 'EMAIL' | 'SMS';
  /** 接收方：邮箱地址或手机号 */
  recipient: string;
  /** 业务场景 */
  scenario: 'REGISTER' | 'RESET_PASSWORD' | 'BIND_PHONE' | 'LOGIN';
  /** 图形验证码ID（LOGIN 场景可选） */
  captcha_id?: string;
  /** 图形验证码答案（LOGIN 场景可选） */
  captcha_solution?: string;
}

/**
 * 绑定手机号请求（POST /users/me/phone）
 */
export interface BindPhoneRequest {
  /** 手机号码 */
  phone_number: string;
  /** 短信OTP验证码 */
  bind_ticket: string;
}

/**
 * 绑定手机号响应
 */
export interface BindPhoneResponse {
  /** 脱敏手机号 */
  phone_number: string;
  /** 是否已验证 */
  is_phone_verified: boolean;
}

/**
 * 校验 OTP 验证码请求（Phase 2 新增端点 POST /auth/verification-codes/verify）
 */
export interface VerifyCodeRequest {
  /** 发送渠道 */
  channel: 'EMAIL' | 'SMS';
  /** 接收方：邮箱或手机号 */
  recipient: string;
  /** 业务场景 */
  scenario: 'REGISTER' | 'RESET_PASSWORD' | 'BIND_PHONE' | 'LOGIN';
  /** 用户输入的验证码 */
  code: string;
}

/**
 * 校验 OTP 验证码响应
 */
export interface VerifyCodeResponse {
  /** 短期 ticket，用于后续业务操作 */
  ticket: string;
  /** ticket 过期时间（秒） */
  expires_in: number;
}

/**
 * 手机号注册请求（Phase 3 新增端点 POST /users/register/phone）
 */
export interface PhoneRegisterRequest {
  /** REGISTER 场景的 ticket（由 /verification-codes/verify 签发） */
  register_ticket: string;
  /** 密码 */
  password: string;
  /** 昵称 */
  nickname: string;
}

/**
 * 手机号注册响应
 */
export interface PhoneRegisterResponse {
  /** 用户公开ID */
  public_id: string;
  /** 用户名（自动生成） */
  username: string;
  /** 昵称 */
  nickname: string;
  /** 手机号 */
  phone_number: string;
  /** 手机号是否已验证 */
  is_phone_verified: boolean;
  /** 是否为新用户 */
  is_new_user: boolean;
  /** 访问令牌 */
  access_token: string;
  /** 刷新令牌 */
  refresh_token: string;
  /** 令牌类型 */
  token_type: 'bearer';
}

/** 一键登录请求（Phase 4） */
export interface OneTapLoginRequest {
  carrier_token: string;
  provider?: string;
}

/** 一键登录响应 */
export interface OneTapLoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: 'bearer';
  is_new_user: boolean;
  phone_masked: string;
}

/** 云函数一键登录请求（HMAC 签名版，v2 安全路径） */
export interface CloudFunctionLoginRequest {
  phone: string;       // 云函数解密后的真实手机号
  sign: string;        // HMAC-SHA256(phone + timestamp, PSK)
  timestamp: number;   // 签名时间戳
}

/** 手机号验证码登录请求 */
export interface LoginByPhoneRequest {
  login_ticket: string;
}

/** 手机号验证码登录响应 */
export interface LoginByPhoneResponse {
  access_token: string;
  refresh_token: string;
  token_type: 'bearer';
  is_new_user: boolean;
  phone_masked: string;
}

/**
 * 已登录用户修改密码（POST /users/me/password）
 * @see 用户模块设计文档 7.1.6 — 后端仅接收 current_password + new_password；确认新密码由前端校验
 */
export interface ChangePasswordRequest {
  /** 当前密码 */
  current_password?: string;
  /** 新密码（须符合强度策略） */
  new_password: string;
}

/**
 * 用户注册请求参数
 */
export interface RegisterRequest {
  /** 用户名（2-50字符，字母/数字/下划线） */
  username: string;
  /** 邮箱地址 */
  email: string;
  /** 密码（至少8位，包含大小写字母+数字+特殊字符） */
  password: string;
  /** 昵称（2-50字符） */
  nickname: string;
  /** 验证码ID */
  captcha_id: string;
  /** 验证码答案 */
  captcha_solution: string;
}

/**
 * 用户注册响应
 */
export interface RegisterResponse {
  /** 用户UUID */
  uuid: string;
  /** 用户名 */
  username: string;
  /** 邮箱 */
  email: string;
  /** 昵称 */
  nickname: string;
}

/**
 * 注册表单数据（前端使用）
 */
export interface RegisterForm {
  /** 用户名 */
  username: string;
  /** 邮箱 */
  email: string;
  /** 密码 */
  password: string;
  /** 昵称 */
  nickname: string;
  /** 验证码答案 */
  captcha_solution: string;
}

/**
 * 密码强度级别枚举
 */
export enum PasswordStrengthLevel {
  /** 很弱（红色） */
  VeryWeak = 1,
  /** 弱（橙色） */
  Weak = 2,
  /** 中（黄色） */
  Medium = 3,
  /** 强（浅绿） */
  Strong = 4,
  /** 很强（深绿） */
  VeryStrong = 5
}

/**
 * 密码强度对象
 */
export interface PasswordStrength {
  /** 强度级别 */
  level: PasswordStrengthLevel;
  /** 显示文本 */
  text: string;
  /** 颜色值 */
  color: string;
  /** 分数（0-5） */
  score: number;
}
