/**
 * 认证相关 API
 * 对齐 docs/Live-Saas-Wechat-10-用户认证与管理-前端设计文档-v1.7.md + V3.5 增量（含邮箱 ticket 登录）
 */

import { request } from '@/utils/request'
import { API_PATHS } from '@/config/api'
import type { ApiResponse } from '@/types/common'
import type {
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  RegisterResponse,
  VerificationCodesRequest,
  VerifyCodeRequest,
  VerifyCodeResponse,
  PhoneLoginRequest,
  EmailLoginRequest,
  PhoneRegisterRequest,
  PhoneRegisterResponse,
  OneTapLoginRequest,
  OneTapLoginResponse,
  CloudFunctionLoginRequest,
  RefreshTokenRequest,
  PasswordResetRequest,
  PasswordResetConfirmRequest,
  CaptchaResponseData,
  SsoLoginRequest
} from '@/types/auth'

export const getCaptcha = (): Promise<ApiResponse<CaptchaResponseData>> =>
  request.get(API_PATHS.AUTH.CAPTCHA, { auth: false, loading: false })

export const sendVerificationCode = (data: VerificationCodesRequest) =>
  request.post(API_PATHS.AUTH.VERIFICATION_CODES, data, {
    auth: false,
    loading: true,
    loadingText: '发送中...'
  })

/** V3：校验 OTP 并签发 ticket */
export const verifyVerificationCode = (
  data: VerifyCodeRequest
): Promise<ApiResponse<VerifyCodeResponse>> =>
  request.post(API_PATHS.AUTH.VERIFICATION_CODES_VERIFY, data, {
    auth: false,
    loading: true,
    loadingText: '验证中...'
  })

export const login = (data: LoginRequest): Promise<ApiResponse<LoginResponse>> =>
  request.post(API_PATHS.AUTH.LOGIN, data, { auth: false, loading: true, loadingText: '登录中...' })

/** V3：手机号 ticket 登录 */
export const loginByPhone = (data: PhoneLoginRequest): Promise<ApiResponse<LoginResponse>> =>
  request.post(API_PATHS.AUTH.LOGIN_PHONE, data, { auth: false, loading: true, loadingText: '登录中...' })

/** V3.5：邮箱 ticket 登录（后端 POST /auth/login/email 已就绪） */
export const loginByEmail = (data: EmailLoginRequest): Promise<ApiResponse<LoginResponse>> =>
  request.post(API_PATHS.AUTH.LOGIN_EMAIL, data, { auth: false, loading: true, loadingText: '登录中...' })

export const logout = () => request.post(API_PATHS.AUTH.LOGOUT, {}, { loading: false })

export const refreshToken = (data: RefreshTokenRequest): Promise<ApiResponse<LoginResponse>> =>
  request.post(API_PATHS.AUTH.REFRESH, data, { auth: false, loading: false, showError: false })

export const requestPasswordReset = (data: PasswordResetRequest) =>
  request.post(API_PATHS.AUTH.PASSWORD_RESET_REQUEST, data, {
    auth: false,
    loading: true,
    loadingText: '提交中...'
  })

export const resetPassword = (data: PasswordResetConfirmRequest) =>
  request.post(API_PATHS.AUTH.PASSWORD_RESET, data, {
    auth: false,
    loading: true,
    loadingText: '重置中...'
  })

/** @deprecated 使用 resetPassword */
export const confirmPasswordReset = resetPassword

export const ssoLogin = (data: SsoLoginRequest): Promise<ApiResponse<LoginResponse>> =>
  request.post(API_PATHS.AUTH.SSO_LOGIN, data, { auth: false, loading: true, loadingText: '登录中...' })

/** V3：运营商一键登录 */
export const oneTapLogin = (data: OneTapLoginRequest): Promise<ApiResponse<OneTapLoginResponse>> =>
  request.post(API_PATHS.AUTH.ONE_TAP_LOGIN, data, { auth: false, loading: true, loadingText: '登录中...' })

/** V3：云函数 HMAC 一键登录 */
export const oneTapLoginCloudFunction = (
  data: CloudFunctionLoginRequest
): Promise<ApiResponse<OneTapLoginResponse>> =>
  request.post(API_PATHS.AUTH.ONE_TAP_LOGIN_CF, data, { auth: false, loading: true, loadingText: '登录中...' })

export const register = (data: RegisterRequest): Promise<ApiResponse<RegisterResponse>> =>
  request.post(API_PATHS.USER.REGISTER, data, { auth: false, loading: true, loadingText: '注册中...' })

/** V3：手机号 ticket 注册（直接返回 JWT） */
export const registerByPhone = (
  data: PhoneRegisterRequest
): Promise<ApiResponse<PhoneRegisterResponse>> =>
  request.post(API_PATHS.USER.REGISTER_PHONE, data, { auth: false, loading: true, loadingText: '注册中...' })

export default {
  getCaptcha,
  sendVerificationCode,
  verifyVerificationCode,
  login,
  loginByPhone,
  loginByEmail,
  logout,
  refreshToken,
  requestPasswordReset,
  resetPassword,
  confirmPasswordReset,
  ssoLogin,
  oneTapLogin,
  oneTapLoginCloudFunction,
  register,
  registerByPhone
}
