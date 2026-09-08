/**
 * 认证模块API接口
 * 包含登录、验证码、SSO、Token刷新等功能
 */

import { post, get, put, del, patch } from '@/utils/request';
import type { UploadFile } from 'uni-app';
import { AUTH_API_URL, BASE_API_URL } from '@/constants/api';
import type { ApiResponse } from '@/types/common';
import type {
  CaptchaResponse,
  LoginRequest,
  LoginResponse,
  SSOLoginRequest,
  RefreshTokenRequest,
  RefreshTokenResponse,
  UserInfo,
  PasswordResetRequest,
  PasswordResetExecute,
  RegisterRequest,
  RegisterResponse,
  ChangePasswordRequest,
  SendOtpRequest,
  BindPhoneRequest,
  BindPhoneResponse,
  VerifyCodeRequest,
  VerifyCodeResponse,
  PhoneRegisterRequest,
  PhoneRegisterResponse,
  OneTapLoginRequest,
  OneTapLoginResponse,
  LoginByPhoneRequest,
  LoginByPhoneResponse
} from '@/types/auth';

/**
 * 获取图形验证码
 * @returns 验证码ID和Base64图片
 * @example
 * const response = await getCaptcha();
 * const { captcha_id, image_base64 } = response.data;
 */
const authUrl = (path: string) => `${AUTH_API_URL.replace(/\/+$/, '')}/${path.replace(/^\/+/, '')}`;

export const getCaptcha = (): Promise<ApiResponse<CaptchaResponse>> => {
  return get<ApiResponse<CaptchaResponse>>(authUrl('/auth/captcha'));
};

/**
 * 用户登录
 * @param data 登录信息（用户名/密码/验证码）
 * @returns Access Token和Refresh Token
 * @example
 * const response = await login({ username: 'testuser', password: 'Test@123', captcha_id: 'xxx', captcha_solution: '1234' });
 * const { access_token, refresh_token } = response.data;
 */
export const login = (data: LoginRequest): Promise<ApiResponse<LoginResponse>> => {
  return post<ApiResponse<LoginResponse>>(authUrl('/auth/login'), data);
};

/**
 * 用户注册
 * @param data 注册信息（用户名/邮箱/密码/昵称/验证码）
 * @returns 注册成功的用户信息
 * @example
 * const response = await registerUser({
 *   username: 'newuser',
 *   email: 'user@example.com',
 *   password: 'Test@123',
 *   nickname: '新用户',
 *   captcha_id: 'xxx',
 *   captcha_solution: '1234'
 * });
 * const user = response.data;
 */
export const registerUser = (data: RegisterRequest): Promise<ApiResponse<RegisterResponse>> => {
  return post<ApiResponse<RegisterResponse>>(authUrl('/register'), data);
};

/**
 * 刷新Access Token
 * @param data Refresh Token
 * @returns 新的Access Token
 * @example
 * const response = await refreshToken({ refresh_token: 'xxx' });
 * const newToken = response.data.access_token;
 */
export const refreshToken = (data: RefreshTokenRequest): Promise<ApiResponse<RefreshTokenResponse>> => {
  return post<ApiResponse<RefreshTokenResponse>>(authUrl('/auth/refresh'), data);
};

/**
 * 获取当前用户信息
 * @returns 用户详细信息
 * @example
 * const response = await getCurrentUser();
 * const user = response.data;
 */
export const getCurrentUser = (): Promise<ApiResponse<UserInfo>> => {
  return get<ApiResponse<UserInfo>>(authUrl('/me'), undefined, { auth: true });
};

/**
 * 用户登出
 * @example
 * await logout();
 */
export const logout = (): Promise<ApiResponse<void>> => {
  return post<ApiResponse<void>>(authUrl('/auth/logout'), undefined, { auth: true });
};

/**
 * SSO第三方登录（微信/Apple）
 * @param data Authing返回的id_token
 * @returns Access Token和Refresh Token
 * @example
 * const response = await ssoLogin({ id_token: 'xxx' });
 * const { access_token, refresh_token } = response.data;
 */
export const ssoLogin = (data: SSOLoginRequest): Promise<ApiResponse<LoginResponse>> => {
  return post<ApiResponse<LoginResponse>>(authUrl('/auth/sso-login'), data);
};

/**
 * 请求密码重置
 * @param data 邮箱和验证码信息
 * @example
 * await requestPasswordReset({ email: 'user@example.com', captcha_id: 'xxx', captcha_solution: '1234' });
 */
export const requestPasswordReset = (data: PasswordResetRequest): Promise<ApiResponse<void>> => {
  return post<ApiResponse<void>>(authUrl('/auth/password-reset-request'), data);
};

/**
 * 执行密码重置
 * @param data 重置令牌和新密码
 * @example
 * await resetPassword({ reset_token: 'xxx', new_password: 'NewPass@123' });
 */
export const resetPassword = (data: PasswordResetExecute): Promise<ApiResponse<void>> => {
  return post<ApiResponse<void>>(authUrl('/auth/password-reset'), data);
};

/**
 * 发送OTP验证码（邮件或短信）
 * @see POST /auth/verification-codes
 */
export const sendVerificationCode = (data: SendOtpRequest): Promise<ApiResponse<void>> => {
  return post<ApiResponse<void>>(authUrl('/auth/verification-codes'), data);
};

/**
 * 校验 OTP 验证码并换取短期 ticket
 * @see POST /auth/verification-codes/verify
 * @description Phase 2 新增。校验成功后返回 ticket，用于后续重置密码、注册等。
 */
export const verifyCode = (
  data: VerifyCodeRequest
): Promise<ApiResponse<VerifyCodeResponse>> => {
  return post<ApiResponse<VerifyCodeResponse>>(
    authUrl('/auth/verification-codes/verify'),
    data
  );
};

/**
 * 手机号注册（基于 register_ticket）
 * @see POST /users/register/phone
 * @description Phase 3 新增。不接收明文 OTP，只信任后端签发的 register_ticket。
 * 注册成功直接返回 JWT，用户无需再次登录。
 */
export const registerByPhone = (
  data: PhoneRegisterRequest
): Promise<ApiResponse<PhoneRegisterResponse>> => {
  return post<ApiResponse<PhoneRegisterResponse>>(
    authUrl('/register/phone'),
    data
  );
};

/**
 * 绑定或更换手机号（需登录，需先通过 sendVerificationCode 获取OTP）
 * @see POST /users/me/phone
 */
export const bindPhone = (data: BindPhoneRequest): Promise<ApiResponse<BindPhoneResponse>> => {
  return post<ApiResponse<BindPhoneResponse>>(authUrl('/me/phone'), data, { auth: true });
};

/**
 * 注销当前账号（需登录 + 图形验证码防误删）
 * @param data 注销请求（图形验证码）
 */
export const deleteUserAccount = (
  data: { captcha_id: string; captcha_solution: string }
): Promise<ApiResponse<void>> => {
  return del<ApiResponse<void>>(authUrl('/me'), data, { auth: true });
};

/**
 * 一键登录
 * @see POST /auth/one-tap-login
 * @description Phase 4 新增。Mock 模式（开发）：carrier_token = "mock:+8613800138000"
 */
export const oneTapLogin = (
  data: OneTapLoginRequest
): Promise<ApiResponse<OneTapLoginResponse>> => {
  return post<ApiResponse<OneTapLoginResponse>>(
    authUrl('/auth/one-tap-login'),
    data
  );
};

/**
 * 云函数一键登录（HMAC 签名版 — v2 安全路径）
 * 云函数解密手机号 + HMAC 签名 → 前端转发 → 后端验证签名
 * @see POST /auth/one-tap-login/cloud-function
 */
export const cloudFunctionLogin = (
  data: CloudFunctionLoginRequest
): Promise<ApiResponse<OneTapLoginResponse>> => {
  return post<ApiResponse<OneTapLoginResponse>>(
    authUrl('/auth/one-tap-login/cloud-function'),
    data
  );
};

/**
 * 手机号验证码登录
 * @see POST /auth/login/phone
 * @description 先通过 verifyCode 获取 login_ticket，再用此接口登录
 */
export const loginByPhone = (
  data: LoginByPhoneRequest
): Promise<ApiResponse<LoginByPhoneResponse>> => {
  return post<ApiResponse<LoginByPhoneResponse>>(
    authUrl('/auth/login/phone'),
    data
  );
};

/**
 * 已登录用户修改密码（需提供当前密码）
 * @see POST /users/me/password
 */
export const changePassword = (data: ChangePasswordRequest): Promise<ApiResponse<void>> => {
  return post<ApiResponse<void>>(authUrl('/me/password'), data, { auth: true, showLoading: false });
};

/**
 * 更新当前用户个人资料（昵称、简介、头像）
 * @see PATCH /users/me
 */
export interface UpdateProfileRequest {
  nickname?: string;
  bio?: string;
  avatar_url?: string;
}

export const updateProfile = (data: UpdateProfileRequest): Promise<ApiResponse<UserInfo>> => {
  return patch<ApiResponse<UserInfo>>(authUrl('/me'), data, { auth: true, showLoading: false });
};

/**
 * 上传当前用户头像
 * @description POST /users/me/avatar - 上传单张头像图片，返回稳定 avatar_url
 * @param file 需要上传的图片文件
 * @returns 包含 avatar_url 的标准响应
 * @example
 * const uploadRes = await uploadAvatar(filePath);
 * const avatarUrl = uploadRes.data.avatar_url;
 */
export const uploadAvatar = (file: string | UploadFile): Promise<ApiResponse<{ avatar_url: string }>> => {
  const uploadFilePath = typeof file === 'string' ? file : (file as any).path || (file as any).tempFilePath || '';

  if (!uploadFilePath) {
    return Promise.reject(new Error('请选择要上传的头像图片'));
  }

  const token = uni.getStorageSync('jwt_token') || '';
  // 头像上传走认证服务（8002），路径为 /users/me/avatar（与 getCurrentUser 同服务）
  const fullUploadUrl = authUrl('/me/avatar');

  // ===== 详细诊断日志 =====
  console.log('═══════════════════════════════════════════════════');
  console.log('[auth-api] 📤 头像上传 - 诊断开始');
  console.log('[auth-api] 📁 上传文件路径:', uploadFilePath);
  console.log('[auth-api] 🔗 完整上传URL:', fullUploadUrl);
  console.log('[auth-api] 🔑 Token存在:', !!token);
  console.log('[auth-api] 🔑 Token长度:', token.length);
  console.log('[auth-api] 🔑 Token预览:', token ? `${token.substring(0, 30)}...` : 'null');
  console.log('[auth-api] 📋 请求头 Authorization:', token ? `Bearer ${token.substring(0, 30)}...` : '（空）');
  console.log('[auth-api] 📋 表单字段名 name:', 'file');
  console.log('[auth-api] 🌐 AUTH_API_URL:', AUTH_API_URL);
  console.log('═══════════════════════════════════════════════════');

  return new Promise((resolve, reject) => {
    const uploadTask = uni.uploadFile({
      url: fullUploadUrl,
      filePath: uploadFilePath,
      name: 'file',
      header: {
        Authorization: token ? `Bearer ${token}` : '',
      },
      success: (res) => {
        console.log('[auth-api] ✅ 上传请求成功 - HTTP状态码:', res.statusCode);
        console.log('[auth-api] 📥 原始响应数据:', res.data);
        console.log('[auth-api] 📥 响应数据类型:', typeof res.data);
        try {
          const data = typeof res.data === 'string' ? JSON.parse(res.data) : res.data;
          console.log('[auth-api] 📦 解析后的响应数据:', JSON.stringify(data));
          console.log('[auth-api] 📦 data.code:', data?.code);
          console.log('[auth-api] 📦 data.data?.avatar_url:', data?.data?.avatar_url);
          if (data?.code === 200 && data?.data?.avatar_url) {
            console.log('[auth-api] ✅ 头像上传成功, avatar_url:', data.data.avatar_url);
            resolve(data);
            return;
          }
          console.error('[auth-api] ❌ 上传响应异常 - 状态码非200或无avatar_url');
          console.error('[auth-api] ❌ code:', data?.code, 'message:', data?.message);
          reject(new Error(data?.message || '头像上传失败'));
        } catch (error) {
          console.error('[auth-api] ❌ JSON解析失败:', error);
          console.error('[auth-api] ❌ 原始数据:', res.data);
          reject(error);
        }
      },
      fail: (err) => {
        console.error('═══════════════════════════════════════════════════');
        console.error('[auth-api] ❌ 上传请求失败 (网络层)');
        console.error('[auth-api] ❌ 错误对象:', JSON.stringify(err));
        console.error('[auth-api] ❌ err.errMsg:', err.errMsg);
        console.error('[auth-api] ❌ 目标URL:', fullUploadUrl);
        console.error('═══════════════════════════════════════════════════');
        reject(err);
      }
    });

    // 监听上传进度
    uploadTask.onProgressUpdate((res) => {
      console.log('[auth-api] 📊 上传进度:', res.progress + '%', '已上传:', res.totalBytesSent, '总大小:', res.totalBytesExpectedToSend);
    });
  });
};
