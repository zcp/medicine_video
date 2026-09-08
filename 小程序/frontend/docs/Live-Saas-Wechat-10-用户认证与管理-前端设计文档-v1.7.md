# 用户认证与管理（Auth & Users）—— 前端可落地实现文档

**版本**: V1.7  
**日期**: 2026-07-13  
**状态**: ✅ 设计完成，可直接开发  
**技术栈**：uni-app + Vue 3 + TypeScript + Pinia  
**平台**：微信小程序  
**后端设计文档**：《10-用户认证与管理-后端设计文档.md》(V1.4)  
**增量文档**：
- 《Live-Saas-Wechat-10-用户认证与管理-内容安全-前端设计文档-v2.1.md》（nickname/bio 文本安全、头像上传与图片审核）
- 《Live-Saas-Wechat-10-用户认证与管理-手机号与运营商登录-前端设计文档-v3.5.md》（手机注册/登录、邮箱验证码登录、Ticket 闭环、运营商一键登录）  
**契约对齐**：类型、路径、端点、校验规则对齐后端设计文档 V1.2；手机登录/一键登录细节见 V3 增量文档

> **实现差异提示**：邮箱绑定 `POST /me/email` 后端可能尚未完全落地；手机号注册/绑定 Ticket 闭环、运营商一键登录以 V3 增量为准开发，联调时以实际后端行为校验。

---

## 一、功能概述

用户认证是整个平台的基础设施，涵盖登录、注册、Token 管理、个人中心、管理员用户管理等。前端需实现：

### 1.1 用户端
1. **登录**（v1 · 三页同构 consumer 大样式 · **三个主登录方式**）：
   - **一键登录页** `OneTapLogin.vue`（默认入口）：大 pill「一键登录」，对接 `POST /auth/one-tap-login` 或云函数 `POST /auth/one-tap-login/cloud-function`（详见 **V3 增量文档**）；原 Authing `sso-login` 降为可选扩展
   - **验证码登录页** `PhoneLogin.vue`（V3 新增）：手机/邮箱 + **图形验证码** + OTP → `login_ticket` → `POST /auth/login/phone`（SMS）或 `POST /auth/login/email`（EMAIL）；发码 `scenario=LOGIN` **须先通过图形验证码**
   - **密码登录页** `Login.vue`：手机号/邮箱/用户名 + 密码 + 图形验证码
   - 三页共用 `src/common/auth.scss`，互相跳转用全宽 pill 次按钮（`.auth-alt`），**禁止小字 tab 切换**
2. **注册**（V3 · 选择页 + 单模式页）：
   - **注册方式选择页** `RegisterChoice.vue`：「手机号注册」「邮箱注册」两个主按钮
   - **注册页** `Register.vue`：由 URL `?mode=phone|email` 决定单一表单；无 `mode` 时重定向至 `RegisterChoice`
   - **手机注册**（`mode=phone`）：手机号 + SMS OTP → `register_ticket` → `POST /users/register/phone` → 直接返回 JWT（详见 **V3 增量文档**）
   - **邮箱注册**（`mode=email`）：用户名 + 昵称 + 邮箱 + 邮箱验证码 + 密码 —— 逻辑保持 V1.4 不变
3. **忘记密码**：`ForgotPassword.vue` 双路径 —— 邮箱（`reset_token`）+ SMS（`reset_ticket`，V3）；入口在 **密码登录页** `Login.vue` 底部「忘记密码？」链接
4. **个人中心**：查看/修改个人信息（昵称/简介）、头像上传、修改密码、绑定手机号/邮箱、注销账户
5. **账号与安全**：展示个人信息概览（头像+昵称，与「我的」页面一致），分区块导航至各绑定操作详细页，不直接暴露操作表单

### 1.2 账号与安全设计原则
- **逐级下沉**：`AccountSecurity` 主页面仅展示状态摘要（已绑定/未绑定/脱敏展示），点击具体项跳转至独立详细页（`BindPhone`、`ChangePassword`）
- **信息对齐**：个人信息区域展示内容（头像 + 昵称）与 `Profile.vue` 顶部英雄区保持一致
- **API 对齐**：可绑定/修改的信息严格对齐后端可用 API 端点（手机号 → `POST /users/me/phone`（V3：`bind_ticket`），邮箱 → `POST /users/me/email`，密码 → `POST /users/me/password`，昵称/简介 → `PATCH /users/me`，头像 → `POST /users/me/avatar`）
- **不可变字段**：用户名不可修改；邮箱注册时设置，后续可通过绑定 API 更换；手机注册用户系统生成用户名

### 1.2.1 图形验证码防滥用原则（重要）

> **一句话**：凡是会**绑定账号身份信息**、**触发验证码下发**，或**持久化修改用户数据**的敏感交互，都必须经过图形验证码人机校验，防止脚本撞库、刷绑、连续恶意修改。

**三种主登录入口对照**：

| 页面 | 图形验证码 |
|------|------------|
| `OneTapLogin` | ❌ 无（信任运营商/云函数验签） |
| `Login`（密码登录） | ✅ 有（提交登录前必填） |
| `PhoneLogin`（验证码登录） | ✅ **有**（**发码前必填**；UI 与 `Login` / `Register` 同构 captcha 行） |

**设计意图**（比「仅手机号绑定要 captcha」更广）：

| 防护目标 | 说明 |
|----------|------|
| 防自动化攻击 | 阻止脚本批量登录尝试、刷短信/邮件、反复绑定/解绑 |
| 防连续恶意操作 | 同一攻击者不能在没有人工介入的情况下高频改号、改邮、改密 |
| 防公开入口滥用 | 未登录即可调用的接口（密码登录、验证码登录发码、注册、找回密码）是首要攻击面 |

**按操作类型分类**：

| 类型 | 典型操作 | 图形验证码要求 |
|------|----------|----------------|
| **A. 公开身份入口** | 密码登录、申请密码重置 | ✅ **提交前必填** captcha |
| **B. 公开发码链路** | 注册 / 找回密码 / 绑定手机 / 绑定邮箱 / **验证码登录发码** 的「发送验证码」 | ✅ **发码前必填** captcha（含 `scenario=LOGIN`） |
| **C. 已登录写库操作** | 改昵称简介、改密、换绑提交、上传头像、**注销账号** | 绑定类经 B 类发码 + verify ticket 已间接校验；**注销账号**后端要求 DELETE Body 携带图形验证码（`DeactivateAccountRequest`）；改资料/改密/上传头像当前仅 JWT + 业务校验 |
| **D. 第三方信任链** | 运营商一键登录（`carrier_token` / 云函数 HMAC） | 豁免图形验证码，信任运营商/云函数验签 |

**前端落地规则**：

1. **凡调用 `POST /auth/verification-codes`**：所有 `scenario`（含 `LOGIN`）UI 必须先展示图形验证码，发码请求携带 `captcha_id` + `captcha_solution`。
2. **凡公开表单提交**（密码登录、密码重置申请）：表单内嵌图形验证码，提交时携带 `captcha_id` + `captcha_solution`。
3. **已登录敏感页**（`BindPhone`、`BindEmail`、`ChangePassword`、`ProfileEdit` 保存、`deleteMyAccount`）：至少满足后端现有校验；若产品要求「所有写库操作都过人机」，在提交按钮前增加图形验证码（需后端配套接口，当前 V1.1 未统一要求）。

**与限流的关系**：图形验证码解决「是不是人」；60 秒发码间隔、登录 5 次锁定（HTTP 429）解决「刷得多快」。两者叠加，不互相替代。

### 1.3 管理端
5. **管理员用户管理**：用户列表（分页+筛选：用户名/邮箱/角色/状态/邮箱验证/手机验证）、角色/状态管理

### 1.4 基础设施
6. **Token 管理**：uni.request 拦截器自动附加/刷新 Token（Access 30min / Refresh 7day）
7. **路由守卫**：pages.json + 页面级 onShow 鉴权

**后端数据表**：
- `users`：id(UUID PK), username(VARCHAR 50 UNIQUE), email(VARCHAR 200 UNIQUE partial), phone(VARCHAR 20 UNIQUE partial), password_hash(VARCHAR 256), nickname(VARCHAR 100), avatar_url(VARCHAR 500), bio(TEXT), role(VARCHAR 20 CHECK user/admin/expert), status(VARCHAR 20 CHECK active/disabled/deleted), is_email_verified(BOOLEAN), is_phone_verified(BOOLEAN), public_id(VARCHAR 100 UNIQUE), created_at, updated_at
- `verification_codes`：channel(EMAIL/SMS), recipient, scenario(REGISTER/PASSWORD_RESET/LOGIN/BIND_PHONE/BIND_EMAIL), code, is_used, expires_at
- `refresh_tokens`：user_id FK, token_hash(UNIQUE), expires_at, is_revoked

**后端 API 总数**：20 个（Auth 9 + Users 9 + Admin 2）；V3 增量另含 `login/phone`、`one-tap-login` 等，详见 V3 前端增量文档

---

## 二、目录结构

```
src/
├── types/
│   └── auth.ts                          # 认证与用户类型定义
├── api/
│   ├── auth.ts                          # 认证 API 封装（8个端点，含 SSO）
│   └── user.ts                          # 用户 API 封装（8个端点，含头像/邮箱绑定）+ 管理员（2个端点）
├── config/
│   └── api.ts                           # API 路径配置（AUTH + USER 段）
├── store/
│   └── auth.ts                          # Pinia 认证状态管理
├── utils/
│   ├── token.ts                         # Token 存取工具
│   └── request.ts                       # uni.request 封装（含 Token 拦截器）
├── pages/
│   ├── auth/
│   │   ├── OneTapLogin.vue              # 一键登录（默认入口，V3：运营商/云函数）
│   │   ├── PhoneLogin.vue               # 验证码登录（V3 新增）
│   │   ├── Login.vue                    # 密码登录
│   │   ├── RegisterChoice.vue           # 注册方式选择（V3 新增）
│   │   ├── Register.vue                 # 注册页（V3：单模式，?mode=phone|email）
│   │   └── ForgotPassword.vue           # 忘记密码页（Login 页「忘记密码？」入口）
│   ├── profile/
│   │   ├── Profile.vue                  # 个人中心（已有，需改造）
│   │   ├── ProfileEdit.vue              # 编辑个人信息（已有，需改造）
│   ├── settings/
│   │   ├── AccountSecurity.vue          # 账号与安全（主页面，展示摘要，导航至详细页）
│   │   ├── BindPhone.vue                # 绑定/更换手机号（详细操作页）
│   │   ├── BindEmail.vue                # 绑定/更换邮箱（详细操作页）
│   │   └── ChangePassword.vue           # 修改密码（详细操作页）
│   └── admin/
│       └── user/
│           └── UserList.vue             # 管理员用户管理
└── composables/
    └── useAuth.ts                       # 认证组合函数（登录态检查、密码强度校验）
    └── useOtpTicket.ts                  # V3：OTP 发码 + verify → ticket 封装
```

---

## 三、类型定义

> 严格对齐后端 Pydantic Schema 与 DDL，字段名、类型、必填/可选 100% 一致

```typescript
// src/types/auth.ts

/**
 * 角色枚举（DDL: CHECK role IN ('user', 'admin', 'expert')）
 * 后端 Pydantic: str, lowercase
 */
export type UserRole = 'user' | 'admin' | 'expert'

/**
 * 用户状态枚举（DDL: CHECK status IN ('active', 'disabled', 'deleted')）
 */
export type UserStatus = 'active' | 'disabled' | 'deleted'

/**
 * 验证码渠道枚举（DDL: CHECK channel IN ('EMAIL', 'SMS')）
 * 后端 Pydantic: ChannelEnum, uppercase
 */
export type ChannelType = 'EMAIL' | 'SMS'

/**
 * 验证码场景枚举（DDL: CHECK scenario IN ('REGISTER', 'PASSWORD_RESET', 'LOGIN', 'BIND_PHONE', 'BIND_EMAIL')）
 * 后端 Pydantic: ScenarioEnum, uppercase
 */
export type ScenarioType = 'REGISTER' | 'PASSWORD_RESET' | 'LOGIN' | 'BIND_PHONE' | 'BIND_EMAIL'

/**
 * 登录请求（对应后端 LoginRequest Schema）
 * username 字段支持：用户名 / 邮箱 / 已验证手机号
 * captcha_id + captcha_solution 必填
 */
export interface LoginRequest {
  username: string       // 1-50字符，必填（用户名/邮箱/已验证手机号）
  password: string       // 必填
  captcha_id: string     // 必填
  captcha_solution: string // 必填
}

/**
 * 登录响应（对应后端 LoginResponse Schema）
 */
export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: 'bearer'
}

/**
 * 注册请求（对应后端 RegisterRequest Schema）
 * password 校验：min 8, 大写+小写+数字
 * 注册成功后 is_email_verified = true
 */
export interface RegisterRequest {
  username: string         // 3-50字符，必填
  email: string            // 必填
  nickname: string         // 1-100字符，必填
  password: string         // min 8，必含大写+小写+数字
  verification_code: string // 邮箱验证码（scenario=REGISTER），必填
}

/**
 * SSO 登录请求（对应后端 SSOLoginRequest Schema）
 */
export interface SSOLoginRequest {
  id_token: string         // Authing 等 IdP 返回的 id_token
}

/**
 * 发送验证码请求（对应后端 VerificationCodeRequest Schema）
 */
export interface VerificationCodeRequest {
  channel: ChannelType     // EMAIL | SMS
  recipient: string        // 邮箱或手机号
  scenario: ScenarioType   // REGISTER | PASSWORD_RESET | LOGIN | BIND_PHONE | BIND_EMAIL
  captcha_id?: string      // scenario=LOGIN 发码时必填（与 REGISTER 等一致）
  captcha_solution?: string
}

/**
 * 校验 OTP 并签发 Ticket（V3 新增）
 * 手机号注册/登录/绑定、SMS 重置密码等场景必须先 verify 再消费 ticket
 */
export interface VerifyCodeRequest {
  channel: ChannelType
  recipient: string
  scenario: ScenarioType
  code: string
}

export interface VerifyCodeResponse {
  ticket: string
  expires_in: number       // 默认 600
}

/**
 * 刷新 Token 请求（对应后端 RefreshTokenRequest Schema）
 */
export interface RefreshTokenRequest {
  refresh_token: string
}

/**
 * 密码重置申请请求（对应后端 PasswordResetRequest Schema）
 */
export interface PasswordResetRequest {
  email: string
  captcha_id: string
  captcha_solution: string
}

/**
 * 执行密码重置请求（对应后端 PasswordReset Schema）
 * 双路径：邮箱 reset_token 或 SMS reset_ticket（V3）
 * 注意：后端仅要求 min 8，不含大小写+数字（与注册/改密不同）
 */
export interface PasswordReset {
  reset_token?: string
  reset_ticket?: string
  new_password: string     // min 8
}

/**
 * 注册成功响应（对应后端注册接口 data 部分字段，非完整 UserProfile）
 */
export interface RegisterResponse {
  user_id: string
  username: string
  email: string
  nickname: string
  is_email_verified: boolean
}

/**
 * 用户信息响应（对应后端 UserProfile Schema / DDL users 表）
 * JWT payload 使用 user_id（非 sub）
 */
export interface UserProfile {
  user_id: string          // UUID
  username: string
  email: string | null
  nickname: string | null
  avatar_url: string | null
  bio: string | null
  role: UserRole           // 'user' | 'admin' | 'expert'（小写）
  status: UserStatus       // 'active' | 'disabled' | 'deleted'
  phone: string | null
  is_email_verified: boolean
  is_phone_verified: boolean
  public_id: string | null
  created_at: string       // ISO 8601
}

/**
 * 更新用户信息请求（对应后端 UserUpdate Schema）
 * 不含 avatar_url，头像请走 POST /users/me/avatar
 * nickname/bio 写库前需内容安全校验，详见 V2 增量文档
 */
export interface UserUpdate {
  nickname?: string        // max 100
  bio?: string
}

/**
 * 头像上传响应（对应后端 AvatarUploadResponse Schema）
 */
export interface AvatarUploadResponse {
  avatar_url: string       // 相对路径
}

/**
 * 修改密码请求（对应后端 ChangePasswordRequest Schema）
 * new_password 校验：min 8, 大写+小写+数字
 */
export interface ChangePasswordRequest {
  old_password: string
  new_password: string
}

/**
 * 绑定手机号请求（对应后端 BindPhoneRequest Schema，V3）
 * 须先 POST /auth/verification-codes/verify 获取 bind_ticket
 */
export interface BindPhoneRequest {
  phone_number: string
  bind_ticket: string      // scenario=BIND_PHONE
}

/**
 * 绑定/更换邮箱请求（对应后端 BindEmailRequest Schema）
 */
export interface BindEmailRequest {
  email: string
  verification_code: string  // scenario=BIND_EMAIL
}

/**
 * 管理员更新用户请求（对应后端 AdminUserUpdate Schema）
 */
export interface AdminUserUpdate {
  role?: UserRole          // 'user' | 'admin' | 'expert'
  status?: 'active' | 'disabled'  // 管理端不可设 deleted
}

/**
 * 图形验证码响应（对应后端 CaptchaResponse Schema）
 * 后端字段为 captcha_image；若网关/旧版返回 image_base64，前端需兼容二者
 */
export interface CaptchaResponse {
  captcha_id: string
  captcha_image: string    // Base64 图片（优先）
  image_base64?: string    // 兼容旧响应字段
}

/**
 * 注销账号请求（对应后端 DeactivateAccountRequest Schema）
 * DELETE /users/me Body 必填
 */
export interface DeactivateAccountRequest {
  captcha_id: string
  captcha_solution: string
}

/**
 * 用户列表分页响应（对应后端统一分页格式）
 * 后端 size 字段名（非 page_size）
 */
export interface UserPageResult {
  items: UserProfile[]
  total: number
  page: number
  size: number             // 后端字段名为 size
}
```

---

## 四、API 封装

> 严格对齐后端路由表（V1.2 共 20 端点 + V3 扩展），使用 `API_PATHS` 配置，不硬编码路径。V3 新增 API 函数见 V3 增量文档 §三。

### 4.1 认证 API（V1.2 基础 + V3 扩展）

```typescript
// src/api/auth.ts

import { request } from '@/utils/request'
import { API_PATHS } from '@/config/api'
import type { ApiResponse } from '@/types/common'
import type {
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  VerificationCodeRequest,
  RefreshTokenRequest,
  PasswordResetRequest,
  PasswordReset,
  CaptchaResponse,
  RegisterResponse,
  SSOLoginRequest
} from '@/types/auth'

/**
 * 获取图形验证码
 * GET /auth/captcha
 * 公开接口，无需认证
 */
export const getCaptcha = (): Promise<ApiResponse<CaptchaResponse>> => {
  return request.get(API_PATHS.AUTH.CAPTCHA, { auth: false, showError: false })
}

/**
 * 用户登录
 * POST /auth/login
 * 公开接口，body: username, password, captcha_id, captcha_solution
 * 错误码：4012(验证码错误), 4013(登录失败), 4014(账号禁用)
 */
export const login = (data: LoginRequest): Promise<ApiResponse<LoginResponse>> => {
  return request.post(API_PATHS.AUTH.LOGIN, data, { auth: false })
}

/**
 * 用户登出
 * POST /auth/logout
 * JWT 认证，撤销所有 Refresh Token
 */
export const logout = (): Promise<ApiResponse<null>> => {
  return request.post(API_PATHS.AUTH.LOGOUT)
}

/**
 * 刷新 Token
 * POST /auth/refresh
 * 公开接口，body: refresh_token
 * 错误码：4011(JWT 无效)
 */
export const refreshToken = (data: RefreshTokenRequest): Promise<ApiResponse<LoginResponse>> => {
  return request.post(API_PATHS.AUTH.REFRESH, data, { auth: false, showError: false })
}

/**
 * 发送验证码
 * POST /auth/verification-codes
 * 公开接口 + 限流（60秒/次）
 * body: channel, recipient, scenario, captcha_id, captcha_solution
 */
export const sendVerificationCode = (data: VerificationCodeRequest): Promise<ApiResponse<null>> => {
  return request.post(API_PATHS.AUTH.VERIFICATION_CODES, data, { auth: false })
}

/**
 * 申请密码重置（发送重置邮件）
 * POST /auth/password-reset-request
 * 公开接口，body: email, captcha_id, captcha_solution
 */
export const requestPasswordReset = (data: PasswordResetRequest): Promise<ApiResponse<null>> => {
  return request.post(API_PATHS.AUTH.PASSWORD_RESET_REQUEST, data, { auth: false })
}

/**
 * 执行密码重置
 * POST /auth/password-reset
 * 公开接口，body: reset_token, new_password
 */
export const resetPassword = (data: PasswordReset): Promise<ApiResponse<null>> => {
  return request.post(API_PATHS.AUTH.PASSWORD_RESET, data, { auth: false })
}

/**
 * SSO 登录（Authing 等 IdP）
 * POST /auth/sso-login
 * 公开接口，body: id_token
 * 错误码：4011(JWT 无效), 4001(参数校验失败)
 */
export const ssoLogin = (data: SSOLoginRequest): Promise<ApiResponse<LoginResponse>> => {
  return request.post(API_PATHS.AUTH.SSO_LOGIN, data, { auth: false })
}

/**
 * 用户注册
 * POST /users/register
 * 公开接口，body: username, email, nickname, password, verification_code
 * 错误码：2002(用户名/邮箱已存在), 4012(验证码错误)
 */
export const register = (data: RegisterRequest): Promise<ApiResponse<RegisterResponse>> => {
  return request.post(API_PATHS.USER.REGISTER, data, { auth: false })
}
```

> **说明**：`register()` 虽调用 Users 域路径，可放在 `src/api/auth.ts`（与现有代码一致）或 `src/api/user.ts`，以项目约定为准。

### 4.2 用户 API（V1.2 基础 + 管理员 2 个端点 + V3 扩展）

```typescript
// src/api/user.ts

import { request } from '@/utils/request'
import { API_PATHS } from '@/config/api'
import type { ApiResponse } from '@/types/common'
import type {
  UserProfile,
  UserUpdate,
  ChangePasswordRequest,
  BindPhoneRequest,
  BindEmailRequest,
  AvatarUploadResponse,
  AdminUserUpdate,
  UserPageResult
} from '@/types/auth'

// ============ 个人用户接口 ============

/**
 * 获取当前用户信息
 * GET /users/me
 * JWT 认证
 */
export const getMyProfile = (): Promise<ApiResponse<UserProfile>> => {
  return request.get(API_PATHS.USER.ME)
}

/**
 * 更新当前用户信息（仅文本字段）
 * PATCH /users/me
 * JWT 认证，body: nickname?, bio?
 * 禁止传 avatar_url，否则后端返回 4001
 */
export const updateMyProfile = (data: UserUpdate): Promise<ApiResponse<UserProfile>> => {
  return request.patch(API_PATHS.USER.UPDATE, data)
}

/**
 * 上传头像（multipart）
 * POST /users/me/avatar
 * JWT 认证，字段名 file（图片文件）
 * 错误码：2004(内容安全), 2005(图片审核不通过)
 * 详见 V2 内容安全增量文档
 */
export const uploadMyAvatar = (filePath: string): Promise<ApiResponse<AvatarUploadResponse>> => {
  return request.upload({
    url: API_PATHS.USER.AVATAR,
    filePath,
    name: 'file'
  })
}

/**
 * 修改密码
 * POST /users/me/password
 * JWT 认证，body: old_password, new_password
 * 修改后撤销所有 Refresh Token，强制重新登录
 */
export const changeMyPassword = (data: ChangePasswordRequest): Promise<ApiResponse<null>> => {
  return request.post(API_PATHS.USER.PASSWORD, data)
}

/**
 * 绑定/更换手机号
 * POST /users/me/phone
 * JWT 认证，body: phone_number, bind_ticket（V3：先 verify OTP 换取 ticket）
 * 错误码：2002(手机号已被绑定), 4011(ticket 无效)
 */
export const bindMyPhone = (data: BindPhoneRequest): Promise<ApiResponse<null>> => {
  return request.post(API_PATHS.USER.PHONE, data)
}

/**
 * 绑定/更换邮箱
 * POST /users/me/email
 * JWT 认证，body: email, verification_code（scenario=BIND_EMAIL）
 * 错误码：2002(邮箱已被绑定), 4012(验证码错误)
 */
export const bindMyEmail = (data: BindEmailRequest): Promise<ApiResponse<null>> => {
  return request.post(API_PATHS.USER.EMAIL, data)
}

/**
 * 注销账号（软删除，status -> 'deleted'）
 * DELETE /users/me
 * JWT 认证，Body: captcha_id + captcha_solution（DeactivateAccountRequest）
 * 错误码：4003(图形验证码错误), 2002(存在活跃订阅), 3001
 */
export const deleteMyAccount = (
  data: DeactivateAccountRequest
): Promise<ApiResponse<null>> => {
  return request.delete(API_PATHS.USER.DELETE, { data })
}

// ============ 管理员接口 ============

/**
 * 管理端用户列表（分页+筛选）
 * GET /admin/users
 * JWT + Admin 认证
 * Query: page, page_size, username?, email?, role?, status?, is_email_verified?, is_phone_verified?
 */
export const getAdminUsers = (params?: {
  page?: number
  page_size?: number
  username?: string
  email?: string
  role?: string
  status?: string
  is_email_verified?: boolean
  is_phone_verified?: boolean
}): Promise<ApiResponse<UserPageResult>> => {
  return request.get(API_PATHS.ADMIN.USERS, { data: params })
}

/**
 * 管理员更新用户（角色/状态）
 * PATCH /api/v1/admin/users/{userId}
 * JWT + Admin 认证，body: role?, status?
 */
export const adminUpdateUser = (
  userId: string,
  data: AdminUserUpdate
): Promise<ApiResponse<UserProfile>> => {
  return request.patch(API_PATHS.ADMIN.USER_DETAIL(userId), data)
}
```

---

## 五、config/api.ts 路径配置

> 以下为 AUTH 和 USER 模块在 `src/config/api.ts` 中的配置，已存在于当前代码中

```typescript
// src/config/api.ts 中 AUTH 和 USER 模块

AUTH: {
  CAPTCHA: '/auth/captcha',
  LOGIN: '/auth/login',
  REFRESH: '/auth/refresh',
  LOGOUT: '/auth/logout',
  SSO_LOGIN: '/auth/sso-login',
  PASSWORD_RESET_REQUEST: '/auth/password-reset-request',
  PASSWORD_RESET: '/auth/password-reset',
  VERIFICATION_CODES: '/auth/verification-codes',
  VERIFICATION_CODES_VERIFY: '/auth/verification-codes/verify',  // V3
  LOGIN_PHONE: '/auth/login/phone',                              // V3
  ONE_TAP_LOGIN: '/auth/one-tap-login',                          // V3
  ONE_TAP_LOGIN_CF: '/auth/one-tap-login/cloud-function',        // V3
  CAPTCHA_IMAGE: (id: string) => `/auth/captcha/image/${id}`     // V3 可选
},

USER: {
  REGISTER: '/register',
  REGISTER_PHONE: '/register/phone',  // V3
  ME: '/me',
  PHONE: '/me/phone',
  EMAIL: '/me/email',
  DELETE: '/me',
  PASSWORD: '/me/password',
  UPDATE: '/me',
  AVATAR: '/me/avatar'
}
```

> **说明**：通知接口 `GET /users/me/notifications` 归属通知模块，不在本模块 18 端点范围内；见 `src/config/api.ts` 的 `NOTIFICATION` 段。

> **说明**：ADMIN 段中用户管理相关的路径需追加：
```typescript
ADMIN: {
  // ... 现有内容 ...
  USERS: '/admin/users',
  USER_DETAIL: (userId: string) => `/admin/users/${userId}`
}
```

---

## 六、管理端页面

### 6.1 管理员用户管理 UserList.vue

> 筛选参数对齐后端 `AdminUserQueryParams`：`username`、`email`、`role`、`status`、`is_email_verified`、`is_phone_verified`

```vue
<!-- src/pages/admin/user/UserList.vue -->
<template>
  <view class="user-list-page">
    <!-- 顶部操作栏 -->
    <view class="page-header">
      <text class="header-title">用户管理</text>
    </view>

    <!-- 筛选栏 -->
    <view class="filter-bar">
      <view class="filter-item">
        <input
          v-model="filters.username"
          class="filter-input"
          placeholder="搜索用户名"
          @confirm="handleSearch"
        />
      </view>
      <view class="filter-item">
        <input
          v-model="filters.email"
          class="filter-input"
          placeholder="搜索邮箱"
          @confirm="handleSearch"
        />
      </view>
      <view class="filter-item">
        <picker
          :range="roleOptions"
          range-key="label"
          @change="handleRoleChange"
        >
          <view class="picker-btn">
            <text>{{ currentRoleLabel }}</text>
          </view>
        </picker>
      </view>
      <view class="filter-item">
        <picker
          :range="statusOptions"
          range-key="label"
          @change="handleStatusChange"
        >
          <view class="picker-btn">
            <text>{{ currentStatusLabel }}</text>
          </view>
        </picker>
      </view>
      <view class="filter-item">
        <picker
          :range="verifiedOptions"
          range-key="label"
          @change="handleEmailVerifiedChange"
        >
          <view class="picker-btn">
            <text>{{ currentEmailVerifiedLabel }}</text>
          </view>
        </picker>
      </view>
      <view class="filter-item">
        <picker
          :range="verifiedOptions"
          range-key="label"
          @change="handlePhoneVerifiedChange"
        >
          <view class="picker-btn">
            <text>{{ currentPhoneVerifiedLabel }}</text>
          </view>
        </picker>
      </view>
    </view>

    <!-- 加载态 -->
    <view v-if="loading" class="loading-state">
      <text class="loading-text">加载中...</text>
    </view>

    <!-- 错误态 -->
    <view v-else-if="errorMsg" class="error-state">
      <text class="error-text">{{ errorMsg }}</text>
      <view class="retry-btn" @click="fetchData">
        <text class="retry-text">重试</text>
      </view>
    </view>

    <!-- 空态 -->
    <view v-else-if="users.length === 0" class="empty-state">
      <text class="empty-text">暂无用户数据</text>
    </view>

    <!-- 用户列表 -->
    <view v-else class="user-list">
      <view
        v-for="user in users"
        :key="user.user_id"
        class="user-item"
      >
        <view class="user-info">
          <view class="user-avatar">
            <image
              v-if="user.avatar_url"
              :src="user.avatar_url"
              class="avatar-img"
              mode="aspectFill"
            />
            <view v-else class="avatar-placeholder">
              <text class="avatar-text">{{ (user.nickname || user.username).charAt(0) }}</text>
            </view>
          </view>
          <view class="user-detail">
            <view class="user-name-row">
              <text class="user-name">{{ user.nickname || user.username }}</text>
              <view :class="['role-tag', `role-${user.role}`]">
                <text class="role-text">{{ roleLabelMap[user.role] }}</text>
              </view>
            </view>
            <text class="user-email">{{ user.email || '未设置邮箱' }}</text>
            <text class="user-created">{{ formatTime(user.created_at) }}</text>
          </view>
        </view>
        <view class="user-status-action">
          <view :class="['status-tag', `status-${user.status}`]">
            <text class="status-text">{{ statusLabelMap[user.status] }}</text>
          </view>
          <view class="action-btn" @click="openEditPopup(user)">
            <text class="action-text">编辑</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 分页 -->
    <view v-if="total > pageSize" class="pagination">
      <view
        class="page-btn"
        :class="{ disabled: currentPage <= 1 }"
        @click="changePage(currentPage - 1)"
      >
        <text>上一页</text>
      </view>
      <text class="page-info">{{ currentPage }} / {{ totalPages }}</text>
      <view
        class="page-btn"
        :class="{ disabled: currentPage >= totalPages }"
        @click="changePage(currentPage + 1)"
      >
        <text>下一页</text>
      </view>
    </view>

    <!-- 编辑弹窗（uni-app popup） -->
    <view v-if="showEditPopup" class="popup-mask" @click="closeEditPopup">
      <view class="popup-content" @click.stop>
        <view class="popup-header">
          <text class="popup-title">编辑用户</text>
          <view class="popup-close" @click="closeEditPopup">
            <text>✕</text>
          </view>
        </view>
        <view class="popup-body">
          <view class="form-item">
            <text class="form-label">角色</text>
            <picker
              :range="editRoleOptions"
              range-key="label"
              :value="editRoleIndex"
              @change="handleEditRoleChange"
            >
              <view class="picker-btn">
                <text>{{ editRoleOptions[editRoleIndex]?.label }}</text>
              </view>
            </picker>
          </view>
          <view class="form-item">
            <text class="form-label">状态</text>
            <picker
              :range="editStatusOptions"
              range-key="label"
              :value="editStatusIndex"
              @change="handleEditStatusChange"
            >
              <view class="picker-btn">
                <text>{{ editStatusOptions[editStatusIndex]?.label }}</text>
              </view>
            </picker>
          </view>
        </view>
        <view class="popup-footer">
          <view class="popup-btn popup-btn--cancel" @click="closeEditPopup">
            <text>取消</text>
          </view>
          <view class="popup-btn popup-btn--confirm" @click="handleUpdateUser">
            <text>保存</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { getAdminUsers, adminUpdateUser } from '@/api/user'
import type { UserProfile, UserRole, UserStatus, AdminUserUpdate } from '@/types/auth'

const users = ref<UserProfile[]>([])
const loading = ref(false)
const errorMsg = ref<string | null>(null)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

const filters = reactive({
  username: '',
  email: '',
  role: '' as string,
  status: '' as string,
  is_email_verified: '' as string,
  is_phone_verified: '' as string
})

const totalPages = computed(() => Math.ceil(total.value / pageSize.value))

// 角色/状态选项
const roleOptions = [
  { label: '全部角色', value: '' },
  { label: '普通用户', value: 'user' },
  { label: '管理员', value: 'admin' },
  { label: '专家', value: 'expert' }
]
const statusOptions = [
  { label: '全部状态', value: '' },
  { label: '正常', value: 'active' },
  { label: '禁用', value: 'disabled' }
]
const verifiedOptions = [
  { label: '全部', value: '' },
  { label: '已验证', value: 'true' },
  { label: '未验证', value: 'false' }
]

const roleLabelMap: Record<string, string> = {
  user: '普通用户',
  admin: '管理员',
  expert: '专家'
}
const statusLabelMap: Record<string, string> = {
  active: '正常',
  disabled: '禁用',
  deleted: '已注销'
}

const currentRoleLabel = computed(() => {
  return roleOptions.find(o => o.value === filters.role)?.label || '全部角色'
})
const currentStatusLabel = computed(() => {
  return statusOptions.find(o => o.value === filters.status)?.label || '全部状态'
})
const currentEmailVerifiedLabel = computed(() => {
  return verifiedOptions.find(o => o.value === filters.is_email_verified)?.label || '邮箱验证'
})
const currentPhoneVerifiedLabel = computed(() => {
  return verifiedOptions.find(o => o.value === filters.is_phone_verified)?.label || '手机验证'
})

// 编辑弹窗
const showEditPopup = ref(false)
const editingUserId = ref('')
const editForm = reactive<AdminUserUpdate>({ role: 'user', status: 'active' })
const editRoleOptions = [
  { label: '普通用户', value: 'user' },
  { label: '管理员', value: 'admin' },
  { label: '专家', value: 'expert' }
]
const editStatusOptions = [
  { label: '正常', value: 'active' },
  { label: '禁用', value: 'disabled' }
]
const editRoleIndex = ref(0)
const editStatusIndex = ref(0)

/**
 * 格式化时间
 */
function formatTime(isoStr: string): string {
  try {
    const d = new Date(isoStr)
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
  } catch {
    return isoStr
  }
}

async function fetchData() {
  loading.value = true
  errorMsg.value = null
  try {
    const params: Record<string, any> = {
      page: currentPage.value,
      page_size: pageSize.value
    }
    if (filters.username) params.username = filters.username
    if (filters.email) params.email = filters.email
    if (filters.role) params.role = filters.role
    if (filters.status) params.status = filters.status
    if (filters.is_email_verified !== '') params.is_email_verified = filters.is_email_verified === 'true'
    if (filters.is_phone_verified !== '') params.is_phone_verified = filters.is_phone_verified === 'true'

    const res = await getAdminUsers(params)
    if (res.code === 200 && res.data) {
      users.value = res.data.items
      total.value = res.data.total
    }
  } catch (err: any) {
    errorMsg.value = err.message || '加载用户列表失败'
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  currentPage.value = 1
  fetchData()
}

function handleRoleChange(e: any) {
  filters.role = roleOptions[e.detail.value]?.value || ''
  handleSearch()
}

function handleStatusChange(e: any) {
  filters.status = statusOptions[e.detail.value]?.value || ''
  handleSearch()
}

function handleEmailVerifiedChange(e: any) {
  filters.is_email_verified = verifiedOptions[e.detail.value]?.value || ''
  handleSearch()
}

function handlePhoneVerifiedChange(e: any) {
  filters.is_phone_verified = verifiedOptions[e.detail.value]?.value || ''
  handleSearch()
}

function changePage(page: number) {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  fetchData()
}

function openEditPopup(user: UserProfile) {
  editingUserId.value = user.user_id
  editForm.role = user.role
  editForm.status = user.status
  editRoleIndex.value = editRoleOptions.findIndex(o => o.value === user.role)
  editStatusIndex.value = editStatusOptions.findIndex(o => o.value === user.status)
  showEditPopup.value = true
}

function closeEditPopup() {
  showEditPopup.value = false
}

function handleEditRoleChange(e: any) {
  editRoleIndex.value = e.detail.value
  editForm.role = editRoleOptions[e.detail.value]?.value as UserRole
}

function handleEditStatusChange(e: any) {
  editStatusIndex.value = e.detail.value
  editForm.status = editStatusOptions[e.detail.value]?.value as UserStatus
}

async function handleUpdateUser() {
  try {
    await adminUpdateUser(editingUserId.value, editForm)
    uni.showToast({ title: '更新成功', icon: 'success' })
    closeEditPopup()
    fetchData()
  } catch (err: any) {
    uni.showToast({ title: err.message || '更新失败', icon: 'none' })
  }
}

onMounted(() => fetchData())
</script>

<style lang="scss" scoped>
.user-list-page {
  min-height: 100vh;
  background: var(--color-background);
  padding: var(--spacing-md);
}

.page-header {
  margin-bottom: var(--spacing-lg);
}

.header-title {
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--color-text-primary);
}

.filter-bar {
  display: flex;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
  flex-wrap: wrap;
}

.filter-input {
  flex: 1;
  min-width: 140px;
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-card);
  border-radius: var(--border-radius-base);
  font-size: var(--font-size-sm);
}

.picker-btn {
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-card);
  border-radius: var(--border-radius-base);
  font-size: var(--font-size-sm);
}

.user-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md);
  background: var(--color-card);
  border-radius: var(--border-radius-base);
  margin-bottom: var(--spacing-sm);
}

.user-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  flex: 1;
}

.avatar-img {
  width: 48px;
  height: 48px;
  border-radius: 50%;
}

.avatar-placeholder {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary);
}

.avatar-text {
  color: #fff;
  font-size: var(--font-size-lg);
  font-weight: 600;
}

.user-name-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.user-name {
  font-size: var(--font-size-base);
  font-weight: 500;
  color: var(--color-text-primary);
}

.role-tag {
  padding: 2px 8px;
  border-radius: var(--border-radius-sm);
  font-size: var(--font-size-xs);
}

.role-user { background: #e6f7ff; }
.role-admin { background: #fff7e6; }
.role-expert { background: #f6ffed; }

.role-text {
  font-size: var(--font-size-xs);
}

.user-email {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  margin-top: 2px;
}

.user-created {
  font-size: var(--font-size-xs);
  color: var(--color-text-hint);
  margin-top: 2px;
}

.user-status-action {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: var(--spacing-xs);
}

.status-tag {
  padding: 2px 8px;
  border-radius: var(--border-radius-sm);
}

.status-active { background: #f6ffed; }
.status-disabled { background: #fff2f0; }
.status-deleted { background: #f5f5f5; }

.status-text {
  font-size: var(--font-size-xs);
}

.action-btn {
  padding: var(--spacing-xs) var(--spacing-sm);
  border: 1px solid var(--color-primary);
  border-radius: var(--border-radius-sm);
}

.action-text {
  color: var(--color-primary);
  font-size: var(--font-size-xs);
}

.empty-state, .loading-state, .error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60px 0;
}

.empty-text, .loading-text, .error-text {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.retry-btn {
  margin-top: var(--spacing-md);
  padding: var(--spacing-sm) var(--spacing-lg);
  background: var(--color-primary);
  border-radius: var(--border-radius-base);
}

.retry-text {
  color: #fff;
  font-size: var(--font-size-sm);
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-md);
  margin-top: var(--spacing-lg);
}

.page-btn {
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-card);
  border-radius: var(--border-radius-base);
}

.page-btn.disabled {
  opacity: 0.5;
}

.page-info {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

/* 弹窗样式 */
.popup-mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.popup-content {
  width: 600rpx;
  background: #fff;
  border-radius: var(--border-radius-lg);
  overflow: hidden;
}

.popup-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md) var(--spacing-lg);
  border-bottom: 1px solid var(--color-border);
}

.popup-title {
  font-size: var(--font-size-base);
  font-weight: 600;
}

.popup-close {
  padding: var(--spacing-xs);
}

.popup-body {
  padding: var(--spacing-lg);
}

.form-item {
  margin-bottom: var(--spacing-md);
}

.form-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-xs);
  display: block;
}

.popup-footer {
  display: flex;
  border-top: 1px solid var(--color-border);
}

.popup-btn {
  flex: 1;
  padding: var(--spacing-md);
  text-align: center;
}

.popup-btn--cancel {
  border-right: 1px solid var(--color-border);
}

.popup-btn--confirm {
  background: var(--color-primary);
}

.popup-btn--confirm text {
  color: #fff;
}
</style>
```

---

## 七、账号与安全（AccountSecurity）详细设计

> 设计原则：「汇总展示 → 逐项跳转」，不在主页面暴露操作表单

### 7.1 页面导航关系

```
Profile.vue（我的）
  └─ "账号与安全" → AccountSecurity.vue
       ├─ 个人信息（头像+昵称，同 Profile 英雄区）
       │    └─ 无绑定操作，点击跳转 ProfileEdit.vue
       ├─ 账号绑定
       │    ├─ 邮箱（已绑定→脱敏显示/未绑定→提示） → BindEmail.vue
       │    └─ 手机号（已绑定→脱敏显示/未绑定→提示） → BindPhone.vue
       ├─ 安全设置
       │    └─ 修改密码 → ChangePassword.vue
       └─ 危险操作
            └─ 注销账号（弹窗确认，原地执行）
```

### 7.2 AccountSecurity.vue — 主页面

**页面结构（3 个 Section + 1 个 Danger Section）**：

1. **个人信息 Section**
   - 展示当前用户头像 + 昵称 + 用户名（与 Profile 英雄区一致）
   - 数据来源：`GET /users/me`（`UserProfile`）
   - 交互：点击跳转 `ProfileEdit.vue` 编辑资料
   - 无绑定状态判断，始终显示当前值

2. **账号绑定 Section**
   - **邮箱**（可绑定+可更换）：
     - 未绑定 → 显示「未绑定」+ 右箭头 + 「绑定」标签
     - 已绑定 → 脱敏显示 `a***@domain.com`，可展示 `is_email_verified` 状态
     - 点击跳转 `BindEmail.vue`
   - **手机号**（可绑定+可更换）：
     - 未绑定 → 显示「未绑定」+ 右箭头 + 「绑定」标签
     - 已绑定 → 脱敏显示 `138****5678`
     - 点击跳转 `BindPhone.vue`

3. **安全设置 Section**
   - **修改密码**：点击跳转 `ChangePassword.vue`

4. **危险操作 Section**
   - **注销账号**（入口：`Settings.vue` → `AccountSecurity.vue` → 危险操作区）：
     1. 点击行 → `uni.showModal` 一次警示（不可逆说明）
     2. 用户确认 → 弹出**图形验证码确认层**（UI 复用 `Login.vue` 的 `.captcha-row` / `.captcha-box` 结构与 `auth.scss` tokens）
     3. 用户填写验证码并点「确认注销」→ `deleteMyAccount({ captcha_id, captcha_solution })`
     4. 成功：toast → `authStore.logout()` → `reLaunch` 首页；失败 4003 刷新验证码；失败 2002 提示「存在活跃订阅，无法注销」

**状态处理**：
- `loading`：首次加载显示骨架屏或 loading 提示
- `error`：显示错误提示 + 重试按钮
- `empty`：正常情况下不应为空（用户已登录），但若 `userInfo` 为空则提示「请先登录」

### 7.3 BindPhone.vue — 绑定/更换手机号

**功能**：绑定新手机号或更换已有手机号（V3：OTP → `bind_ticket` 闭环）

**页面结构**：
```
BindPhone.vue
├─ 页面标题: "绑定手机号" 或 "更换手机号"（根据是否已有 phone）
├─ 手机号输入框
├─ 图形验证码行（captcha_id + captcha_solution）
├─ 发送验证码按钮（cooldown 60s）
│    └─ POST /auth/verification-codes (channel=SMS, scenario=BIND_PHONE)
├─ 短信验证码输入框（6位数字）
├─ 确认按钮
│    ├─ POST /auth/verification-codes/verify (BIND_PHONE) → bind_ticket
│    └─ POST /users/me/phone { phone_number, bind_ticket }
└─ 底部提示文字
```

**校验规则**（对齐后端 V3）：
- 发码前：手机号格式合法 + 图形验证码已填写
- 提交前：先 verify 获取 `bind_ticket`；`phone_number` 须与 verify 时 `recipient` 一致

**API 依赖**：
- `GET /auth/captcha`
- `POST /auth/verification-codes`（`channel: 'SMS'`, `scenario: 'BIND_PHONE'`）
- `POST /auth/verification-codes/verify`（V3 新增）
- `POST /users/me/phone`（`{ phone_number, bind_ticket }`）

> **V3 详细流程与错误处理**见《Live-Saas-Wechat-10-用户认证与管理-手机号与运营商登录-前端设计文档-v3.5.md》§5.4

### 7.4 BindEmail.vue — 绑定/更换邮箱

**功能**：绑定新邮箱或更换已有邮箱

**页面结构**：
```
BindEmail.vue
├─ 页面标题: "绑定邮箱" 或 "更换邮箱"（根据是否已有 email）
├─ 邮箱输入框
│    └─ 若已绑定，预填当前邮箱
├─ 图形验证码行（与 BindPhone / Register 一致：输入框 + 可点击刷新图片）
├─ 发送验证码按钮（cooldown 60s）
│    └─ 调用 POST /auth/verification-codes (channel=EMAIL, scenario=BIND_EMAIL, captcha_id, captcha_solution)
├─ 邮箱验证码输入框（6位数字）
├─ 确认按钮 → 调用 POST /users/me/email
└─ 底部提示文字
```

**API 依赖**：
- `GET /auth/captcha`（页面加载时获取图形验证码）
- `POST /auth/verification-codes`（`channel: 'EMAIL'`, `scenario: 'BIND_EMAIL'`, captcha 必填）
- `POST /users/me/email`（`{ email, verification_code }`）

**注意事项**：
- 绑定成功后 `is_email_verified = true`，AccountSecurity 页需刷新用户信息

### 7.5 ChangePassword.vue — 修改密码

**功能**：修改登录密码

**页面结构**：
```
ChangePassword.vue
├─ 页面标题: "修改密码"
├─ 当前密码输入框（password 类型，含显示/隐藏切换）
├─ 新密码输入框（password 类型，含显示/隐藏切换）
│    └─ 密码强度实时提示（8位以上/大写/小写/数字）
├─ 确认新密码输入框（password 类型）
├─ 确认按钮 → 调用 POST /users/me/password
└─ 底部提示：修改成功后需重新登录
```

**校验规则**（对齐后端 `ChangePasswordRequest.validate_password`）：
- `old_password`：必填
- `new_password`：min 8，必含大写+小写+数字
- `confirm_password`：须与 `new_password` 一致

**状态处理**：
- `loading`：提交中禁用按钮
- `error`：显示错误 toast（旧密码错误、新密码强度不足等）
- `success`：toast 提示「密码修改成功，请重新登录」→ 调用 `authStore.logout()` → 跳转登录页

**API 依赖**：
- `POST /users/me/password`（`{ old_password, new_password }`）

---

## 八、忘记密码页详细设计

### 8.1 ForgotPassword.vue

**功能**：两步重置密码（申请重置邮件 → 输入 reset_token + 新密码）

**校验规则**（严格对齐后端 Schema）：

| 步骤 | 接口 | 前端校验 |
|------|------|----------|
| 步骤1 | `POST /auth/password-reset-request` | 邮箱 + 图形验证码必填 |
| 步骤2 | `POST /auth/password-reset` | `reset_token` 必填；`new_password` **仅 min 8**（后端 `PasswordReset` 无大小写+数字要求） |

> **注意**：注册（`RegisterRequest`）和修改密码（`ChangePasswordRequest`）仍要求大小写+数字；忘记密码重置按后端 `PasswordReset` 仅校验长度。

**错误处理**：
- `4011`：重置令牌无效或过期
- `4001`：参数校验失败

---

## 九、用户端页面/组件

> **说明**：以下为登录/注册/忘记密码等独立认证页面；账号与安全相关页面（AccountSecurity、BindPhone、ChangePassword）已在第七节详细设计，此处不再重复。
>
> **v1 登录 UI**：三页同构大样式（`OneTapLogin` + `Login` + `PhoneLogin`），详见 **V3 增量文档 §1.1** 与 `src/common/auth.scss`。

### 9.1 一键登录页 OneTapLogin.vue（v1 · 默认入口）

- 路由：`/pages/auth/OneTapLogin`
- **页面标题**：仅 `pages.json` 导航栏「登录」
- 内容标题：`auth-title` → H1「欢迎回来」+ 副标题「使用本机一键登录，安全快捷」
- 主区：`auth-cta`「一键登录」（88rpx 实心）→ **V3**：云函数 HMAC 或 `POST /auth/one-tap-login`（`carrier_token` + `agreed_to_terms`）
- 次区：`auth-alt`「密码登录」→ Login；`auth-alt`「验证码登录」→ PhoneLogin
- 小字：`auth-link`「注册账号」→ RegisterChoice
- 底部：`auth-agreement` 协议一行（须与 `agreed_to_terms` 联动）
- 成功：存储双 Token → `authStore.fetchUserInfo()` → 跳转 redirect 或首页

> **V3 详细实现**（Mock token、云函数验签、错误码 3002）见 V3 增量文档 §5.1

### 9.1.1 验证码登录页 PhoneLogin.vue（V3 新增）

- 路由：`/pages/auth/PhoneLogin`
- **页面标题**：导航栏「验证码登录」；内容 H1「验证码登录」
- **图形验证码**：✅ **有**（`onLoad`/`onMounted` 调用 `GET /auth/captcha`；发码前校验 captcha；UI 复用 `auth.scss` 的 `.captcha-row` / `.captcha-box`，与 `Login.vue` 一致）
- 账号输入：手机号或邮箱（`detectLoginRecipient` 自动识别 channel）
- 流程：图形验证码 → 发码（`scenario=LOGIN` + captcha）→ verify → `login/phone`（SMS）或 `login/email`（EMAIL）
- 次入口：`auth-alt` 切换一键登录 / 密码登录；`auth-link`「注册账号」→ RegisterChoice

**页面结构**：
```
PhoneLogin.vue
├─ 账号输入框（手机号 / 邮箱）
├─ 图形验证码行（captcha_id + captcha_solution，可点击刷新）
├─ OTP 验证码行 + 「获取验证码」
├─ 「登录」主按钮
└─ auth-alt / auth-link / auth-agreement
```

**发码校验**：账号格式合法 + 图形验证码已填写；发码失败（含 4003）刷新图形验证码。

> 详见 V3 增量文档 §5.2

### 9.2 密码登录页 Login.vue（v1 · consumer 大样式）

- 路由：`/pages/auth/Login`
- **页面标题**：导航栏「密码登录」；**无** `auth-top` kicker
- 内容标题：H1「密码登录」+ 副标题「可使用手机号、邮箱或用户名登录」
- 登录标识输入框 placeholder：「手机号 / 邮箱 / 用户名」（后端支持已验证手机号登录）
- **登录锁定**：连续失败 5 次锁定 300 秒，后端返回 HTTP `429`；前端需识别并提示「登录失败次数过多，请稍后再试」
- 主区：`auth-form` + `auth-cta`「登录」（88rpx 实心）
- 次区：`auth-alt`「一键登录」→ OneTapLogin；`auth-alt`「验证码登录」→ PhoneLogin
- 小字：`auth-link`「忘记密码？」→ ForgotPassword；`auth-link`「注册账号」→ RegisterChoice

#### 9.2.1 医学直播小程序按钮设计（选型说明）

采用 **主次同高（方案 A）**：当前页主操作为 88rpx 实心 `.auth-cta`；切换另一登录方式为 88rpx 线框 `.auth-alt`（同宽同高，仅填充不同）。理由：C 端一键登录 friction 最低，密码/验证码为补充路径；三页互跳保持同高避免视觉不一致。详见 V3 增量文档 §1.1。

#### 9.2.2 页面结构示意

```vue
<!-- 两页骨架：无 auth-top，标题仅 navigationBar -->
<view class="auth-page">
  <view class="auth-container">
    <view class="auth-main">
      <view class="auth-title">
        <text class="auth-title__h1">欢迎回来</text>
        <text class="auth-title__sub">…</text>
      </view>
      <view class="auth-primary"><!-- cta 或 form+cta --></view>
      <view class="auth-secondary">
        <button class="auth-alt">切换登录方式</button><!-- 88rpx 线框 -->
        <button class="auth-cancel">暂不登录</button><!-- 72rpx -->
      </view>
    </view>
  </view>
</view>
```

#### 9.2.3 未登录跳转约定

- 全项目未登录默认：`AUTH_ROUTES.ONE_TAP_LOGIN`（`buildOneTapLoginUrl(redirect)`）
- 密码登录 / 验证码登录页通过三页 `auth-alt` 互跳或显式 deep link 进入

> **旧版单页双 mode + auth-links 方案已废弃**；**Register 页内 pill 切换注册方式已废弃**，改由 `RegisterChoice` 分流。

### 9.2-legacy 登录页 Login.vue（旧版 · 已废弃，仅留档）

<details>
<summary>点击展开旧版 login-card / auth-links 参考（勿用于新开发）</summary>

      <!-- 用户名 -->
      <view class="form-item">
        <input
          v-model="formData.username"
          class="form-input"
          placeholder="用户名或邮箱"
          maxlength="50"
        />
      </view>

      <!-- 密码 -->
      <view class="form-item">
        <input
          v-model="formData.password"
          class="form-input"
          placeholder="密码"
          :password="!showPassword"
          maxlength="100"
        />
        <view class="toggle-pwd" @click="showPassword = !showPassword">
          <text class="toggle-text">{{ showPassword ? '隐藏' : '显示' }}</text>
        </view>
      </view>

      <!-- 图形验证码 -->
      <view class="form-item captcha-row">
        <input
          v-model="formData.captcha_solution"
          class="form-input captcha-input"
          placeholder="验证码"
          maxlength="10"
        />
        <view class="captcha-image" @click="refreshCaptcha">
          <image
            v-if="captchaImage"
            :src="captchaImage"
            class="captcha-img"
            mode="aspectFit"
          />
          <text v-else class="captcha-placeholder">加载中</text>
        </view>
      </view>

      <!-- 登录按钮 -->
      <view
        class="submit-btn"
        :class="{ disabled: submitting }"
        @click="handleLogin"
      >
        <text class="submit-text">{{ submitting ? '登录中...' : '登录' }}</text>
      </view>

      <!-- 底部链接 -->
      <view class="login-footer">
        <view class="footer-link" @click="goForgotPassword">
          <text class="link-text">忘记密码？</text>
        </view>
        <view class="footer-link" @click="goRegister">
          <text class="link-text">注册账号</text>
        </view>
      </view>

      <!-- 错误提示 -->
      <view v-if="errorMsg" class="error-banner">
        <text class="error-text">{{ errorMsg }}</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { getCaptcha, login } from '@/api/auth'
import { useAuthStore } from '@/store/auth'
import type { LoginRequest } from '@/types/auth'

const authStore = useAuthStore()

const submitting = ref(false)
const showPassword = ref(false)
const errorMsg = ref<string | null>(null)
const captchaId = ref('')
const captchaImage = ref('')

const formData = reactive({
  username: '',
  password: '',
  captcha_solution: ''
})

/**
 * 加载图形验证码
 */
async function refreshCaptcha() {
  try {
    const res = await getCaptcha()
    if (res.code === 200 && res.data) {
      captchaId.value = res.data.captcha_id
      captchaImage.value = res.data.captcha_image
      formData.captcha_solution = ''
    }
  } catch (err) {
    console.error('加载验证码失败', err)
  }
}

/**
 * 前端密码强度校验（注册时需要，登录时不做强校验但提示）
 */
function validatePassword(pwd: string): string | null {
  if (pwd.length < 8) return '密码至少8位'
  if (!/[A-Z]/.test(pwd)) return '密码需包含大写字母'
  if (!/[a-z]/.test(pwd)) return '密码需包含小写字母'
  if (!/\d/.test(pwd)) return '密码需包含数字'
  return null
}

/**
 * 登录处理
 * 错误码映射：4012(验证码错误), 4013(登录失败), 4014(账号禁用)
 * HTTP 429：登录失败次数过多，账号临时锁定
 */
async function handleLogin() {
  errorMsg.value = null

  if (!formData.username) {
    errorMsg.value = '请输入用户名'
    return
  }
  if (!formData.password) {
    errorMsg.value = '请输入密码'
    return
  }
  if (!formData.captcha_solution) {
    errorMsg.value = '请输入验证码'
    return
  }

  submitting.value = true
  try {
    const data: LoginRequest = {
      username: formData.username,
      password: formData.password,
      captcha_id: captchaId.value,
      captcha_solution: formData.captcha_solution
    }
    await authStore.login(data)
    uni.showToast({ title: '登录成功', icon: 'success' })
    // 返回上一页或首页
    setTimeout(() => {
      uni.navigateBack({ delta: 1, fail: () => uni.switchTab({ url: '/pages/home/Home' }) })
    }, 500)
  } catch (err: any) {
    if (err.statusCode === 429) {
      errorMsg.value = '登录失败次数过多，请稍后再试'
    } else {
      errorMsg.value = err.message || '登录失败，请检查用户名密码和验证码'
    }
    refreshCaptcha()
  } finally {
    submitting.value = false
  }
}

function goRegister() {
  uni.navigateTo({ url: '/pages/auth/Register' })
}

function goForgotPassword() {
  uni.navigateTo({ url: '/pages/auth/ForgotPassword' })
}

onMounted(() => refreshCaptcha())
</script>

<style lang="scss" scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-background);
  padding: var(--spacing-lg);
}

.login-card {
  width: 100%;
  max-width: 640rpx;
  padding: var(--spacing-xl);
  background: var(--color-card);
  border-radius: var(--border-radius-lg);
}

.login-title {
  display: block;
  text-align: center;
  font-size: var(--font-size-xl);
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-xl);
}

.form-item {
  margin-bottom: var(--spacing-md);
  position: relative;
}

.form-input {
  width: 100%;
  padding: var(--spacing-md);
  background: var(--color-bg-secondary);
  border-radius: var(--border-radius-base);
  font-size: var(--font-size-base);
}

.toggle-pwd {
  position: absolute;
  right: var(--spacing-md);
  top: 50%;
  transform: translateY(-50%);
}

.toggle-text {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

.captcha-row {
  display: flex;
  gap: var(--spacing-md);
}

.captcha-input {
  flex: 1;
}

.captcha-image {
  width: 200rpx;
  height: 80rpx;
  flex-shrink: 0;
  border-radius: var(--border-radius-sm);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-secondary);
}

.captcha-img {
  width: 100%;
  height: 100%;
}

.captcha-placeholder {
  font-size: var(--font-size-xs);
  color: var(--color-text-hint);
}

.submit-btn {
  margin-top: var(--spacing-lg);
  padding: var(--spacing-md);
  background: var(--color-primary);
  border-radius: var(--border-radius-base);
  text-align: center;
}

.submit-btn.disabled {
  opacity: 0.6;
}

.submit-text {
  color: #fff;
  font-size: var(--font-size-base);
  font-weight: 500;
}

.login-footer {
  display: flex;
  justify-content: space-between;
  margin-top: var(--spacing-md);
}

.link-text {
  font-size: var(--font-size-sm);
  color: var(--color-primary);
}

.error-banner {
  margin-top: var(--spacing-md);
  padding: var(--spacing-sm) var(--spacing-md);
  background: #fff2f0;
  border-radius: var(--border-radius-sm);
}

.error-text {
  font-size: var(--font-size-sm);
  color: var(--color-danger);
}
</style>
```

</details>

### 9.3 注册页 RegisterChoice.vue + Register.vue

> **V3.1 约定**：注册经 **`RegisterChoice`** 分流；`Register.vue` **单模式**，由 URL `?mode=phone|email` 决定表单；无 `mode` 时 `redirectTo RegisterChoice`。页内「切换注册方式」回到选择页（**禁止** `.register-alt` pill 同页切换）。  
> **V3 手机注册**三步 Ticket 流程见 V3 增量文档 §5.3。以下代码为**邮箱模式（`mode=email`）**功能参考。

```vue
<!-- src/pages/auth/Register.vue -->
<template>
  <view class="register-page">
    <view class="register-card">
      <text class="register-title">注册账号</text>

      <!-- 用户名 -->
      <view class="form-item">
        <input
          v-model="formData.username"
          class="form-input"
          placeholder="用户名（3-50字符）"
          maxlength="50"
        />
      </view>

      <!-- 邮箱 -->
      <view class="form-item">
        <input
          v-model="formData.email"
          class="form-input"
          placeholder="邮箱地址"
          maxlength="200"
        />
      </view>

      <!-- 昵称（V1.1 新增，对齐 RegisterRequest.nickname） -->
      <view class="form-item">
        <input
          v-model="formData.nickname"
          class="form-input"
          placeholder="昵称（1-100字符）"
          maxlength="100"
        />
      </view>

      <!-- 图形验证码 + 发送邮箱验证码 -->
      <view class="form-item captcha-row">
        <input
          v-model="formData.captcha_solution"
          class="form-input captcha-input"
          placeholder="图形验证码"
          maxlength="10"
        />
        <view class="captcha-image" @click="refreshCaptcha">
          <image
            v-if="captchaImage"
            :src="captchaImage"
            class="captcha-img"
            mode="aspectFit"
          />
          <text v-else class="captcha-placeholder">加载中</text>
        </view>
      </view>

      <view class="form-item verify-row">
        <input
          v-model="formData.verification_code"
          class="form-input verify-input"
          placeholder="邮箱验证码"
          maxlength="6"
        />
        <view
          class="send-code-btn"
          :class="{ disabled: cooldown > 0 }"
          @click="handleSendCode"
        >
          <text class="send-code-text">
            {{ cooldown > 0 ? `${cooldown}s` : '发送验证码' }}
          </text>
        </view>
      </view>

      <!-- 密码 -->
      <view class="form-item">
        <input
          v-model="formData.password"
          class="form-input"
          placeholder="密码（8位+大小写+数字）"
          :password="true"
          maxlength="100"
        />
      </view>

      <!-- 密码强度提示 -->
      <view v-if="formData.password" class="password-strength">
        <view :class="['strength-item', { met: passwordChecks.length }]">
          <text>8位以上</text>
        </view>
        <view :class="['strength-item', { met: passwordChecks.upper }]">
          <text>大写字母</text>
        </view>
        <view :class="['strength-item', { met: passwordChecks.lower }]">
          <text>小写字母</text>
        </view>
        <view :class="['strength-item', { met: passwordChecks.digit }]">
          <text>数字</text>
        </view>
      </view>

      <!-- 确认密码 -->
      <view class="form-item">
        <input
          v-model="formData.confirmPassword"
          class="form-input"
          placeholder="确认密码"
          :password="true"
          maxlength="100"
        />
      </view>

      <!-- 注册按钮 -->
      <view
        class="submit-btn"
        :class="{ disabled: submitting }"
        @click="handleRegister"
      >
        <text class="submit-text">{{ submitting ? '注册中...' : '注册' }}</text>
      </view>

      <!-- 底部链接 -->
      <view class="register-footer">
        <text class="footer-hint">已有账号？</text>
        <view class="footer-link" @click="goLogin">
          <text class="link-text">去登录</text>
        </view>
      </view>

      <!-- 错误提示 -->
      <view v-if="errorMsg" class="error-banner">
        <text class="error-text">{{ errorMsg }}</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { getCaptcha, sendVerificationCode, register } from '@/api/auth'
import type { RegisterRequest } from '@/types/auth'

const submitting = ref(false)
const errorMsg = ref<string | null>(null)
const captchaId = ref('')
const captchaImage = ref('')
const cooldown = ref(0)
let cooldownTimer: ReturnType<typeof setInterval> | null = null

const formData = reactive({
  username: '',
  email: '',
  nickname: '',
  captcha_solution: '',
  verification_code: '',
  password: '',
  confirmPassword: ''
})

/** 密码强度检查 */
const passwordChecks = computed(() => ({
  length: formData.password.length >= 8,
  upper: /[A-Z]/.test(formData.password),
  lower: /[a-z]/.test(formData.password),
  digit: /\d/.test(formData.password)
}))

async function refreshCaptcha() {
  try {
    const res = await getCaptcha()
    if (res.code === 200 && res.data) {
      captchaId.value = res.data.captcha_id
      captchaImage.value = res.data.captcha_image
      formData.captcha_solution = ''
    }
  } catch (err) {
    console.error('加载验证码失败', err)
  }
}

/**
 * 发送邮箱验证码
 * 使用 scenario: 'REGISTER'
 */
async function handleSendCode() {
  errorMsg.value = null
  if (!formData.email) {
    errorMsg.value = '请先输入邮箱'
    return
  }
  if (!formData.captcha_solution) {
    errorMsg.value = '请先输入图形验证码'
    return
  }

  try {
    await sendVerificationCode({
      channel: 'EMAIL',
      recipient: formData.email,
      scenario: 'REGISTER',
      captcha_id: captchaId.value,
      captcha_solution: formData.captcha_solution
    })
    uni.showToast({ title: '验证码已发送', icon: 'success' })
    cooldown.value = 60
    cooldownTimer = setInterval(() => {
      cooldown.value--
      if (cooldown.value <= 0 && cooldownTimer) {
        clearInterval(cooldownTimer)
        cooldownTimer = null
      }
    }, 1000)
  } catch (err: any) {
    errorMsg.value = err.message || '发送验证码失败'
    refreshCaptcha()
  }
}

/**
 * 注册处理
 * 校验：用户名3-50、昵称1-100、邮箱格式、密码强度、确认密码一致、验证码
 */
async function handleRegister() {
  errorMsg.value = null

  if (formData.username.length < 3 || formData.username.length > 50) {
    errorMsg.value = '用户名需3-50个字符'
    return
  }
  if (!formData.nickname || formData.nickname.length < 1 || formData.nickname.length > 100) {
    errorMsg.value = '昵称需1-100个字符'
    return
  }
  if (!formData.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
    errorMsg.value = '请输入有效的邮箱地址'
    return
  }
  if (!formData.verification_code) {
    errorMsg.value = '请输入邮箱验证码'
    return
  }
  if (formData.password.length < 8) {
    errorMsg.value = '密码至少8位'
    return
  }
  if (!/[A-Z]/.test(formData.password) || !/[a-z]/.test(formData.password) || !/\d/.test(formData.password)) {
    errorMsg.value = '密码需包含大写字母、小写字母和数字'
    return
  }
  if (formData.password !== formData.confirmPassword) {
    errorMsg.value = '两次密码不一致'
    return
  }

  submitting.value = true
  try {
    const data: RegisterRequest = {
      username: formData.username,
      email: formData.email,
      nickname: formData.nickname,
      password: formData.password,
      verification_code: formData.verification_code
    }
    await register(data)
    uni.showToast({ title: '注册成功，请登录', icon: 'success' })
    setTimeout(() => {
      uni.redirectTo({ url: '/pages/auth/Login' })
    }, 1000)
  } catch (err: any) {
    errorMsg.value = err.message || '注册失败'
  } finally {
    submitting.value = false
  }
}

function goLogin() {
  uni.navigateBack({ delta: 1, fail: () => uni.redirectTo({ url: '/pages/auth/Login' }) })
}

onMounted(() => refreshCaptcha())
</script>

<style lang="scss" scoped>
.register-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-background);
  padding: var(--spacing-lg);
}

.register-card {
  width: 100%;
  max-width: 680rpx;
  padding: var(--spacing-xl);
  background: var(--color-card);
  border-radius: var(--border-radius-lg);
}

.register-title {
  display: block;
  text-align: center;
  font-size: var(--font-size-xl);
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-xl);
}

.form-item {
  margin-bottom: var(--spacing-md);
}

.form-input {
  width: 100%;
  padding: var(--spacing-md);
  background: var(--color-bg-secondary);
  border-radius: var(--border-radius-base);
  font-size: var(--font-size-base);
}

.captcha-row, .verify-row {
  display: flex;
  gap: var(--spacing-md);
}

.captcha-input, .verify-input {
  flex: 1;
}

.captcha-image {
  width: 200rpx;
  height: 80rpx;
  flex-shrink: 0;
  border-radius: var(--border-radius-sm);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-secondary);
}

.captcha-img { width: 100%; height: 100%; }
.captcha-placeholder { font-size: var(--font-size-xs); color: var(--color-text-hint); }

.send-code-btn {
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-primary);
  border-radius: var(--border-radius-base);
  flex-shrink: 0;
}

.send-code-btn.disabled { opacity: 0.5; }
.send-code-text { color: #fff; font-size: var(--font-size-sm); white-space: nowrap; }

.password-strength {
  display: flex;
  gap: var(--spacing-xs);
  margin-bottom: var(--spacing-md);
  flex-wrap: wrap;
}

.strength-item {
  padding: 2px 8px;
  border-radius: var(--border-radius-sm);
  background: #f5f5f5;
  font-size: var(--font-size-xs);
  color: var(--color-text-hint);
}

.strength-item.met {
  color: #52c41a;
  background: #f6ffed;
}

.submit-btn {
  margin-top: var(--spacing-lg);
  padding: var(--spacing-md);
  background: var(--color-primary);
  border-radius: var(--border-radius-base);
  text-align: center;
}

.submit-btn.disabled { opacity: 0.6; }
.submit-text { color: #fff; font-size: var(--font-size-base); font-weight: 500; }

.register-footer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-xs);
  margin-top: var(--spacing-md);
}

.footer-hint { font-size: var(--font-size-sm); color: var(--color-text-secondary); }
.link-text { font-size: var(--font-size-sm); color: var(--color-primary); }

.error-banner {
  margin-top: var(--spacing-md);
  padding: var(--spacing-sm) var(--spacing-md);
  background: #fff2f0;
  border-radius: var(--border-radius-sm);
}

.error-text { font-size: var(--font-size-sm); color: var(--color-danger); }
</style>
```

### 9.4 忘记密码页 ForgotPassword.vue

```vue
<!-- src/pages/auth/ForgotPassword.vue -->
<template>
  <view class="forgot-page">
    <view class="forgot-card">
      <text class="forgot-title">重置密码</text>

      <!-- 步骤1：发送重置请求 -->
      <view v-if="step === 1">
        <view class="form-item">
          <input
            v-model="step1Data.email"
            class="form-input"
            placeholder="注册邮箱"
            maxlength="200"
          />
        </view>

        <view class="form-item captcha-row">
          <input
            v-model="step1Data.captcha_solution"
            class="form-input captcha-input"
            placeholder="图形验证码"
            maxlength="10"
          />
          <view class="captcha-image" @click="refreshCaptcha">
            <image
              v-if="captchaImage"
              :src="captchaImage"
              class="captcha-img"
              mode="aspectFit"
            />
            <text v-else class="captcha-placeholder">加载中</text>
          </view>
        </view>

        <view
          class="submit-btn"
          :class="{ disabled: submitting }"
          @click="handleRequestReset"
        >
          <text class="submit-text">{{ submitting ? '发送中...' : '发送重置邮件' }}</text>
        </view>
      </view>

      <!-- 步骤2：输入新密码 -->
      <view v-if="step === 2">
        <view class="success-hint">
          <text class="hint-text">重置邮件已发送到您的邮箱，请查收并输入邮件中的重置令牌。</text>
        </view>

        <view class="form-item">
          <input
            v-model="step2Data.reset_token"
            class="form-input"
            placeholder="重置令牌"
          />
        </view>

        <view class="form-item">
          <input
            v-model="step2Data.new_password"
            class="form-input"
            placeholder="新密码（至少8位）"
            :password="true"
            maxlength="100"
          />
        </view>

        <view class="form-item">
          <input
            v-model="step2Data.confirm_password"
            class="form-input"
            placeholder="确认新密码"
            :password="true"
            maxlength="100"
          />
        </view>

        <view
          class="submit-btn"
          :class="{ disabled: submitting }"
          @click="handleResetPassword"
        >
          <text class="submit-text">{{ submitting ? '重置中...' : '重置密码' }}</text>
        </view>
      </view>

      <!-- 错误提示 -->
      <view v-if="errorMsg" class="error-banner">
        <text class="error-text">{{ errorMsg }}</text>
      </view>

      <view class="back-link" @click="goLogin">
        <text class="link-text">返回登录</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { getCaptcha, requestPasswordReset, resetPassword } from '@/api/auth'

const step = ref(1)
const submitting = ref(false)
const errorMsg = ref<string | null>(null)
const captchaId = ref('')
const captchaImage = ref('')

const step1Data = reactive({
  email: '',
  captcha_solution: ''
})

const step2Data = reactive({
  reset_token: '',
  new_password: '',
  confirm_password: ''
})

async function refreshCaptcha() {
  try {
    const res = await getCaptcha()
    if (res.code === 200 && res.data) {
      captchaId.value = res.data.captcha_id
      captchaImage.value = res.data.captcha_image
    }
  } catch (err) {
    console.error('加载验证码失败', err)
  }
}

/** 步骤1：申请密码重置 */
async function handleRequestReset() {
  errorMsg.value = null
  if (!step1Data.email) {
    errorMsg.value = '请输入邮箱'
    return
  }
  if (!step1Data.captcha_solution) {
    errorMsg.value = '请输入验证码'
    return
  }

  submitting.value = true
  try {
    await requestPasswordReset({
      email: step1Data.email,
      captcha_id: captchaId.value,
      captcha_solution: step1Data.captcha_solution
    })
    uni.showToast({ title: '重置邮件已发送', icon: 'success' })
    step.value = 2
  } catch (err: any) {
    errorMsg.value = err.message || '发送失败'
    refreshCaptcha()
  } finally {
    submitting.value = false
  }
}

/** 步骤2：执行密码重置（对齐后端 PasswordReset：仅 min 8） */
async function handleResetPassword() {
  errorMsg.value = null
  if (!step2Data.reset_token) {
    errorMsg.value = '请输入重置令牌'
    return
  }
  if (step2Data.new_password.length < 8) {
    errorMsg.value = '密码至少8位'
    return
  }
  if (step2Data.new_password !== step2Data.confirm_password) {
    errorMsg.value = '两次密码不一致'
    return
  }

  submitting.value = true
  try {
    await resetPassword({
      reset_token: step2Data.reset_token,
      new_password: step2Data.new_password
    })
    uni.showToast({ title: '密码重置成功，请登录', icon: 'success' })
    setTimeout(() => {
      uni.redirectTo({ url: '/pages/auth/Login' })
    }, 1000)
  } catch (err: any) {
    errorMsg.value = err.message || '重置失败，请检查令牌是否正确'
  } finally {
    submitting.value = false
  }
}

function goLogin() {
  uni.navigateBack({ delta: 1, fail: () => uni.redirectTo({ url: '/pages/auth/Login' }) })
}

onMounted(() => refreshCaptcha())
</script>

<style lang="scss" scoped>
.forgot-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-background);
  padding: var(--spacing-lg);
}

.forgot-card {
  width: 100%;
  max-width: 640rpx;
  padding: var(--spacing-xl);
  background: var(--color-card);
  border-radius: var(--border-radius-lg);
}

.forgot-title {
  display: block;
  text-align: center;
  font-size: var(--font-size-xl);
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-xl);
}

.form-item {
  margin-bottom: var(--spacing-md);
}

.form-input {
  width: 100%;
  padding: var(--spacing-md);
  background: var(--color-bg-secondary);
  border-radius: var(--border-radius-base);
  font-size: var(--font-size-base);
}

.captcha-row {
  display: flex;
  gap: var(--spacing-md);
}

.captcha-input { flex: 1; }

.captcha-image {
  width: 200rpx;
  height: 80rpx;
  flex-shrink: 0;
  border-radius: var(--border-radius-sm);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-secondary);
}

.captcha-img { width: 100%; height: 100%; }
.captcha-placeholder { font-size: var(--font-size-xs); color: var(--color-text-hint); }

.success-hint {
  margin-bottom: var(--spacing-md);
  padding: var(--spacing-md);
  background: #f6ffed;
  border-radius: var(--border-radius-base);
}

.hint-text {
  font-size: var(--font-size-sm);
  color: #52c41a;
}

.submit-btn {
  margin-top: var(--spacing-lg);
  padding: var(--spacing-md);
  background: var(--color-primary);
  border-radius: var(--border-radius-base);
  text-align: center;
}

.submit-btn.disabled { opacity: 0.6; }
.submit-text { color: #fff; font-size: var(--font-size-base); font-weight: 500; }

.back-link {
  text-align: center;
  margin-top: var(--spacing-md);
}

.link-text { font-size: var(--font-size-sm); color: var(--color-primary); }

.error-banner {
  margin-top: var(--spacing-md);
  padding: var(--spacing-sm) var(--spacing-md);
  background: #fff2f0;
  border-radius: var(--border-radius-sm);
}

.error-text { font-size: var(--font-size-sm); color: var(--color-danger); }
</style>
```

### 9.5 个人中心页面（已有，改造要点）

以下为 `src/pages/profile/Profile.vue` 和 `src/pages/profile/ProfileEdit.vue` 的改造要点，需接入真实 API：

**Profile.vue 改造要点**：
- `onShow` 时调用 `authStore.fetchUserInfo()` 获取最新用户信息
- 显示 loading/error/empty 三种状态
- 使用 `uni.getStorageSync('access_token')` 检查登录态，未登录跳转登录页
- 头像、昵称、邮箱、手机号展示来自 `UserProfile` 类型

**ProfileEdit.vue 改造要点**：
- 修改昵称/简介调用 `updateMyProfile({ nickname, bio })`（禁止 PATCH `avatar_url`）
- 修改头像调用 `uploadMyAvatar(filePath)`（`POST /users/me/avatar`，multipart 字段 `file`），成功后同步 `authStore.userInfo.avatar_url`
- nickname/bio/头像需按 V2 内容安全文档处理 2004/2005 错误码
- 修改密码已迁移至 `ChangePassword.vue`，ProfileEdit 不再内嵌
- 绑定手机号/邮箱已迁移至独立详细页
- 注销账号弹出 `uni.showModal` 确认后调用 `deleteMyAccount()`

### 9.6 Token 管理工具

```typescript
// src/utils/token.ts

const ACCESS_TOKEN_KEY = 'access_token'
const REFRESH_TOKEN_KEY = 'refresh_token'

/** 获取 Access Token */
export function getAccessToken(): string | null {
  return uni.getStorageSync(ACCESS_TOKEN_KEY) || null
}

/** 获取 Refresh Token */
export function getRefreshToken(): string | null {
  return uni.getStorageSync(REFRESH_TOKEN_KEY) || null
}

/** 存储双 Token */
export function setTokens(accessToken: string, refreshToken: string): void {
  uni.setStorageSync(ACCESS_TOKEN_KEY, accessToken)
  uni.setStorageSync(REFRESH_TOKEN_KEY, refreshToken)
}

/** 清除双 Token */
export function clearTokens(): void {
  uni.removeStorageSync(ACCESS_TOKEN_KEY)
  uni.removeStorageSync(REFRESH_TOKEN_KEY)
}

/** 是否已登录 */
export function isLoggedIn(): boolean {
  return !!getAccessToken()
}
```

> **说明**：项目已有 `src/utils/request.ts`，Token 管理已集成在其中（使用 `uni.getStorageSync('access_token')`）。此工具函数作为补充，供 store 和页面直接调用。

### 9.7 Pinia 认证状态管理

```typescript
// src/store/auth.ts

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { setTokens, clearTokens, isLoggedIn } from '@/utils/token'
import { login as loginApi, ssoLogin as ssoLoginApi, logout as logoutApi, refreshToken as refreshApi } from '@/api/auth'
import { getMyProfile } from '@/api/user'
import type { UserProfile, LoginRequest, LoginResponse, RefreshTokenRequest, SSOLoginRequest } from '@/types/auth'

/**
 * 认证状态管理
 * - login/ssoLogin/logout/fetchUserInfo
 * - 自动 Token 刷新
 * - 角色判断（isAdmin, isExpert）
 */
export const useAuthStore = defineStore('auth', () => {
  const userInfo = ref<UserProfile | null>(null)
  const token = ref(isLoggedIn())

  /** 是否管理员 */
  const isAdmin = computed(() => userInfo.value?.role === 'admin')

  /** 是否专家 */
  const isExpert = computed(() => userInfo.value?.role === 'expert')

  /** 是否已登录 */
  const isLoggedInState = computed(() => token.value && !!userInfo.value)

  /**
   * 登录
   * 1. 调用 POST /auth/login 获取双 Token
   * 2. 存储 Token
   * 3. 拉取用户信息
   */
  async function login(data: LoginRequest): Promise<void> {
    const res = await loginApi(data)
    if (res.code === 200 && res.data) {
      setTokens(res.data.access_token, res.data.refresh_token)
      token.value = true
      await fetchUserInfo()
    }
  }

  /**
   * SSO 登录（Authing 一键登录）
   * 1. 调用 POST /auth/sso-login 获取双 Token
   * 2. 存储 Token
   * 3. 拉取用户信息
   */
  async function ssoLogin(data: SSOLoginRequest): Promise<void> {
    const res = await ssoLoginApi(data)
    if (res.code === 200 && res.data) {
      setTokens(res.data.access_token, res.data.refresh_token)
      token.value = true
      await fetchUserInfo()
    }
  }

  /**
   * 登出
   * 1. 调用 POST /auth/logout（撤销 Refresh Token）
   * 2. 清除本地 Token
   * 3. 清空用户信息
   */
  async function logout(): Promise<void> {
    try {
      await logoutApi()
    } catch {
      // 即使后端登出失败，前端也清理
    }
    clearTokens()
    userInfo.value = null
    token.value = false
  }

  /**
   * 拉取当前用户信息
   * GET /users/me
   */
  async function fetchUserInfo(): Promise<void> {
    if (!isLoggedIn()) {
      userInfo.value = null
      token.value = false
      return
    }
    try {
      const res = await getMyProfile()
      if (res.code === 200 && res.data) {
        userInfo.value = res.data
      }
    } catch {
      clearTokens()
      token.value = false
      userInfo.value = null
    }
  }

  /**
   * 刷新 Token
   * POST /auth/refresh
   */
  async function refreshAccessToken(): Promise<boolean> {
    const refreshTokenVal = uni.getStorageSync('refresh_token')
    if (!refreshTokenVal) return false
    try {
      const res = await refreshApi({ refresh_token: refreshTokenVal })
      if (res.code === 200 && res.data) {
        setTokens(res.data.access_token, res.data.refresh_token)
        return true
      }
    } catch {
      // 刷新失败，清理状态
    }
    clearTokens()
    token.value = false
    userInfo.value = null
    return false
  }

  return {
    userInfo,
    token,
    isAdmin,
    isExpert,
    isLoggedInState,
    login,
    ssoLogin,
    logout,
    fetchUserInfo,
    refreshAccessToken
  }
})
```

### 9.8 认证组合函数

```typescript
// src/composables/useAuth.ts

import { computed } from 'vue'
import { useAuthStore } from '@/store/auth'

/**
 * 认证组合函数
 * 提供登录态检查、密码强度校验等工具
 */
export function useAuth() {
  const authStore = useAuthStore()

  /** 是否已登录 */
  const isLoggedIn = computed(() => authStore.isLoggedInState)

  /** 当前用户信息 */
  const userInfo = computed(() => authStore.userInfo)

  /** 是否管理员 */
  const isAdmin = computed(() => authStore.isAdmin)

  /**
   * 密码强度校验（注册 / 修改密码场景）
   * 规则：min 8, 大写+小写+数字（对齐后端 RegisterRequest / ChangePasswordRequest）
   * 注意：忘记密码重置（PasswordReset）仅要求 min 8，不使用此函数
   * @returns null 表示通过，否则返回错误信息
   */
  function validatePassword(pwd: string): string | null {
    if (pwd.length < 8) return '密码至少8位'
    if (!/[A-Z]/.test(pwd)) return '密码需包含大写字母'
    if (!/[a-z]/.test(pwd)) return '密码需包含小写字母'
    if (!/\d/.test(pwd)) return '密码需包含数字'
    return null
  }

  /**
   * 登录失败错误码映射
   * 对齐后端业务状态码；HTTP 429 在页面层按 statusCode 单独处理
   */
  function mapLoginErrorCode(code: number): string {
    const map: Record<number, string> = {
      4011: 'Token 已失效，请重新登录',
      4012: '验证码错误',
      4013: '用户名或密码错误',
      4014: '账号已被禁用，请联系管理员'
    }
    return map[code] || '登录失败，请稍后重试'
  }

  return {
    isLoggedIn,
    userInfo,
    isAdmin,
    validatePassword,
    mapLoginErrorCode
  }
}
```

---

## 十、对接清单

| # | 任务 | 文件路径 | 说明 |
|---|------|---------|------|
| 1 | 创建类型定义 | `src/types/auth.ts` | 按第三节，含 RegisterResponse / BIND_EMAIL / SSOLoginRequest |
| 2 | 创建认证 API | `src/api/auth.ts` | 按第四节 + V3 增量 §三 |
| 3 | 创建用户 API | `src/api/user.ts` | 按第四节 + V3 增量 §三 |
| 4 | 配置 API 路径 | `src/config/api.ts` | AUTH + USER + ADMIN 段（已存在，需追加 ADMIN.USERS） |
| 5 | 创建 Token 工具 | `src/utils/token.ts` | 按第九节 9.6 |
| 6 | 创建 Pinia Store | `src/store/auth.ts` | 按第九节 9.7，login/ssoLogin/logout/fetchUserInfo |
| 7 | 创建认证组合函数 | `src/composables/useAuth.ts` | 按第九节 9.8 |
| 8 | 实现一键登录页 | `src/pages/auth/OneTapLogin.vue` | 按第九节 9.1 |
| 9 | 实现密码登录页 | `src/pages/auth/Login.vue` | 按第九节 9.2（含 HTTP 429 锁定处理） |
| 10 | 实现注册选择页 + 注册页 | `RegisterChoice.vue` + `Register.vue` | 按第九节 9.3 / V3 §5.3 |
| 11 | 实现忘记密码页 | `src/pages/auth/ForgotPassword.vue` | 按第八节 8.1（PasswordReset 仅 min 8） |
| 12 | 改造个人中心 | `src/pages/profile/Profile.vue` | 按第九节 9.5 接入真实 API |
| 13 | 改造编辑资料 | `src/pages/profile/ProfileEdit.vue` | 按第九节 9.5 接入真实 API |
| 14 | 实现账号与安全主页面 | `src/pages/settings/AccountSecurity.vue` | 按第七节 7.2，重构为导航式，去除内嵌弹窗 |
| 15 | 实现绑定手机号详细页 | `src/pages/settings/BindPhone.vue` | 按第七节 7.3（含图形验证码） |
| 16 | 实现绑定邮箱详细页 | `src/pages/settings/BindEmail.vue` | 按第七节 7.4，独立页面 |
| 17 | 实现修改密码详细页 | `src/pages/settings/ChangePassword.vue` | 按第七节 7.5，独立页面 |
| 18 | 实现管理员用户管理 | `src/pages/admin/user/UserList.vue` | 按第六节（含邮箱/验证状态筛选 UI） |
| 19 | 补全 register API 函数 | `src/api/auth.ts` | register() → POST /users/register，返回 RegisterResponse |
| 20 | 补全 bindMyEmail API 函数 | `src/api/user.ts` | bindMyEmail() → POST /users/me/email |
| 21 | 补全 uploadMyAvatar API 函数 | `src/api/user.ts` | uploadMyAvatar() → POST /users/me/avatar |
| 22 | 补全 ssoLogin API 函数 | `src/api/auth.ts` | ssoLogin() → POST /auth/sso-login |
| 23 | 补全 admin 用户 API 函数 | `src/api/user.ts` | getAdminUsers() + adminUpdateUser()（含邮箱/验证状态筛选） |
| 24 | 补全 ADMIN 路由配置 | `src/config/api.ts` | ADMIN.USERS + ADMIN.USER_DETAIL |
| 25 | 更新 pages.json | `src/pages.json` | 添加 BindEmail、Register、PhoneLogin、UserList 路由 |
| 26 | 对齐 V2 内容安全 | 见 V2 增量文档 | ProfileEdit 头像/昵称/bio 分通道保存 |
| 27 | 实现 V3 手机注册/登录/一键登录 | 见 V3 增量文档 §六 | PhoneLogin、RegisterChoice、Register 单模式、OneTapLogin 改造 |
| 28 | 实现 useOtpTicket composable | `src/composables/useOtpTicket.ts` | 发码 + verify 封装 |
| 29 | 改造 BindPhone ticket 绑定 | `src/pages/settings/BindPhone.vue` | V3 §5.4 |
| 30 | ForgotPassword SMS 路径 | `src/pages/auth/ForgotPassword.vue` | V3 §5.5 |
| 31 | 补全 V3 API 函数 | `src/api/auth.ts` | verifyVerificationCode、loginByPhone、loginByEmail、registerByPhone、oneTap* |
| 32 | 邮箱验证码登录闭环 | `PhoneLogin.vue` + `authStore` | EMAIL OTP → verify → `POST /auth/login/email`（后端已就绪） |

---

## 十一、API 链路总结

### 后端路由表（20 个端点 + V3 扩展）

| # | 方法 | 后端路径 | 认证 | 前端函数 | 说明 |
|---|------|---------|------|---------|------|
| 1 | GET | `/auth/captcha` | Public | `getCaptcha()` | 获取图形验证码 |
| 2 | POST | `/auth/login` | Public | `login(data)` | 密码登录 |
| 3 | POST | `/auth/logout` | JWT | `logout()` | 登出 |
| 4 | POST | `/auth/refresh` | Public | `refreshToken(data)` | 刷新 Token |
| 5 | POST | `/auth/verification-codes` | Public | `sendVerificationCode(data)` | 发送 OTP |
| 6 | POST | `/auth/verification-codes/verify` | Public | `verifyVerificationCode(data)` | **V3** 校验 OTP → ticket |
| 7 | POST | `/auth/password-reset-request` | Public | `requestPasswordReset(data)` | 邮箱重置申请 |
| 8 | POST | `/auth/password-reset` | Public | `resetPassword(data)` | 重置密码（token 或 ticket） |
| 9 | POST | `/auth/sso-login` | Public | `ssoLogin(data)` | Authing SSO（可选） |
| 10 | POST | `/auth/login/phone` | Public | `loginByPhone(data)` | **V3** 手机 ticket 登录 |
| 10b | POST | `/auth/login/email` | Public | `loginByEmail(data)` | **V3.5** 邮箱 ticket 登录 |
| 11 | POST | `/auth/one-tap-login` | Public | `oneTapLogin(data)` | **V3** 运营商一键登录 |
| 12 | POST | `/auth/one-tap-login/cloud-function` | Public | `oneTapLoginCloudFunction(data)` | **V3** 云函数 HMAC |
| 13 | POST | `/users/register` | Public | `register(data)` | 邮箱注册 |
| 14 | POST | `/users/register/phone` | Public | `registerByPhone(data)` | **V3** 手机 ticket 注册 + JWT |
| 15 | GET | `/users/me` | JWT | `getMyProfile()` | 获取个人信息 |
| 16 | PATCH | `/users/me` | JWT | `updateMyProfile(data)` | 更新昵称/简介 |
| 17 | POST | `/users/me/avatar` | JWT | `uploadMyAvatar(filePath)` | 上传头像 |
| 18 | POST | `/users/me/password` | JWT | `changeMyPassword(data)` | 修改密码 |
| 19 | POST | `/users/me/phone` | JWT | `bindMyPhone(data)` | 绑定手机（**V3** bind_ticket） |
| 20 | POST | `/users/me/email` | JWT | `bindMyEmail(data)` | 绑定邮箱 |
| 21 | DELETE | `/users/me` | JWT | `deleteMyAccount(data)` | 注销账号 |
| 22 | GET | `/admin/users` | JWT+Admin | `getAdminUsers(params)` | 管理端用户列表 |
| 23 | PATCH | `/admin/users/{userId}` | JWT+Admin | `adminUpdateUser(userId, data)` | 管理员更新用户 |

> V3 端点详细契约见《Live-Saas-Wechat-10-用户认证与管理-手机号与运营商登录-前端设计文档-v3.5.md》

### 错误码映射

| 错误码 | 说明 | 前端处理 |
|--------|------|---------|
| 200 | 成功 | 正常处理 |
| 1002 | 数据库错误 | 提示"服务器内部错误" |
| 2001 | 资源不存在 | 提示"用户不存在" |
| 2002 | 资源已存在 | 提示"用户名/邮箱/手机号已注册" |
| 2004 | 业务逻辑错误 | 提示「旧密码错误」或「暂时无法提交，请稍后再试」（内容安全） |
| 2005 | 内容审核不通过 | 头像上传：提示「暂无法使用此图片，请更换后再试」 |
| 3001 | 未授权 | 跳转登录页 |
| 3002 | 权限不足 / 未同意条款 | 管理端：提示"需要管理员权限"；一键登录：提示勾选协议 |
| 4003 | 图形验证码错误 | 注销账号：提示「图形验证码错误或已过期」，刷新验证码 |
| 4001 | 参数校验失败 | 提示具体校验错误 |
| 4011 | JWT / Ticket 无效 | 清除 Token 或提示重新获取验证码（ticket 过期） |
| 4012 | 验证码错误 | 提示"验证码错误或已过期"，刷新验证码 |
| 4013 | 登录失败 | 提示"用户名或密码错误"，刷新验证码 |
| 4014 | 账号已禁用 | 提示"账号已被禁用，请联系管理员" |
| HTTP 429 | 登录失败锁定 | 提示"登录失败次数过多，请稍后再试"（5 次失败锁定 300 秒） |

### Token 刷新链路

```
1. uni.request 发出请求
   → 2. 响应 401 + code=4011
   → 3. request.ts 拦截器捕获
   → 4. 检查 refresh_token 是否存在
   → 5. POST /auth/refresh { refresh_token }
   → 6. 成功：setTokens() → 重试原始请求
   → 7. 失败：clearTokens() → 跳转登录页
```

---

## 十二、自测清单

> 修改范围：同步后端 V1.2 + V3（双通道注册、Ticket 闭环、运营商一键登录）；V2 内容安全见 V2 增量文档
> 请在真机或模拟器中逐项验证，在「状态」列标注 ✅（通过）或 ❌（失败）

### 12.1 页面导航测试

| # | 测试场景 | 预期结果 | 状态 |
|---|---------|---------|------|
| 1 | 从「我的」页点击「账号与安全」 | 跳转 `AccountSecurity.vue` | ⬜ |
| 2 | AccountSecurity 个人信息区点击 | 跳转 `ProfileEdit.vue` | ⬜ |
| 3 | AccountSecurity 手机号行点击 | 跳转 `BindPhone.vue` | ⬜ |
| 4 | AccountSecurity 修改密码行点击 | 跳转 `ChangePassword.vue` | ⬜ |
| 5 | AccountSecurity 注销账号点击 | 先 showModal 警示，再弹出图形验证码层，填写后 DELETE /me | ⬜ |

### 12.2 个人信息展示测试

| # | 测试场景 | 预期结果 | 状态 |
|---|---------|---------|------|
| 6 | 已登录用户查看 AccountSecurity | 头像、昵称、用户名与「我的」页一致 | ⬜ |
| 7 | 未登录用户访问 AccountSecurity | 自动跳转登录页 | ⬜ |
| 8 | 网络加载失败 | 显示错误提示 + 重试按钮 | ⬜ |

### 12.3 手机号绑定测试

| # | 测试场景 | 预期结果 | 状态 |
|---|---------|---------|------|
| 9 | 未绑定手机号进入 BindPhone | 页面标题显示「绑定手机号」 | ⬜ |
| 10 | 已绑定手机号进入 BindPhone | 页面标题显示「更换手机号」，输入框预填原号码 | ⬜ |
| 11 | 输入正确手机号，点击获取验证码 | 先填图形验证码，再调用 `POST /auth/verification-codes`（SMS/BIND_PHONE + captcha），按钮进入60s倒计时 | ⬜ |
| 12 | 输入错误格式手机号 | 提示「请输入正确的手机号」 | ⬜ |
| 13 | 输入验证码+手机号，点击确认 | verify → `bind_ticket` → `POST /users/me/phone`，成功提示后返回 | ⬜ |
| 14 | API 返回错误（如手机号已被绑定） | 显示具体错误提示 | ⬜ |

### 12.4 邮箱绑定测试

| # | 测试场景 | 预期结果 | 状态 |
|---|---------|---------|------|
| 15 | AccountSecurity 邮箱行显示「绑定」标签 | 未绑定时显示「绑定」+ 右箭头 | ⬜ |
| 16 | AccountSecurity 邮箱行显示脱敏邮箱 | 已绑定时显示 `a***@domain.com` | ⬜ |
| 17 | 点击邮箱行跳转 BindEmail | 跳转 `BindEmail.vue` | ⬜ |
| 18 | 已绑定邮箱进入 BindEmail，输入框预填 | 页面标题显示「更换邮箱」，输入框有原邮箱 | ⬜ |
| 19 | 输入邮箱+验证码提交 | 调用 `POST /users/me/email`（scenario=BIND_EMAIL） | ⬜ |

### 12.5 修改密码测试

| # | 测试场景 | 预期结果 | 状态 |
|---|---------|---------|------|
| 20 | 进入 ChangePassword | 页面标题显示「修改密码」 | ⬜ |
| 21 | 输入不符合强度的新密码 | 密码强度指示器实时反馈 | ⬜ |
| 22 | 新密码与确认密码不一致 | 提交时提示「两次密码不一致」 | ⬜ |
| 23 | 新密码与旧密码相同 | 提交时提示「新密码不能与旧密码相同」 | ⬜ |
| 24 | 输入正确信息提交 | 调用 `POST /users/me/password`，成功提示后自动登出并跳转登录页 | ⬜ |
| 25 | 旧密码错误 | 提示「旧密码错误」或 API 返回的错误信息 | ⬜ |

### 12.6 管理员用户管理测试

| # | 测试场景 | 预期结果 | 状态 |
|---|---------|---------|------|
| 26 | 管理员进入用户管理页 | 显示用户列表，可筛选/分页 | ⬜ |
| 27 | 按邮箱 / 邮箱验证 / 手机验证筛选 | 筛选参数正确传给 `GET /admin/users` | ⬜ |
| 28 | 点击编辑按钮弹出编辑弹窗 | 可修改用户角色和状态 | ⬜ |
| 29 | 确认编辑提交 | 调用 `PATCH /admin/users/{userId}`，成功提示后刷新列表 | ⬜ |

### 12.7 危险操作测试

| # | 测试场景 | 预期结果 | 状态 |
|---|---------|---------|------|
| 30 | 点击「注销账号」 | 弹出确认弹窗，内容明确警示 | ⬜ |
| 31 | 取消注销 | 弹窗关闭，无操作 | ⬜ |
| 32 | 确认注销 | 携带 captcha 调用 `DELETE /users/me`，成功后登出并跳转首页 | ⬜ |
| 32a | 注销 captcha 错误 | 返回 4003，刷新图形验证码并提示 | ⬜ |
| 32b | 注销存在活跃订阅 | 返回 2002/403，提示无法注销 | ⬜ |

### 12.8 注册测试

| # | 测试场景 | 预期结果 | 状态 |
|---|---------|---------|------|
| 33 | 进入注册页 | 显示注册表单（含昵称字段） | ⬜ |
| 34 | 填写信息提交注册 | 调用 `POST /users/register`（含 nickname），成功后跳转登录 | ⬜ |

### 12.9 头像与简介测试

| # | 测试场景 | 预期结果 | 状态 |
|---|---------|---------|------|
| 35 | ProfileEdit 修改昵称/简介 | 调用 `PATCH /users/me`，不传 avatar_url | ⬜ |
| 36 | ProfileEdit 上传头像 | 调用 `POST /users/me/avatar`（字段 file），成功后更新展示 | ⬜ |
| 37 | 头像审核不通过 | 返回 2005，提示更换图片 | ⬜ |

### 12.10 SSO / 一键登录测试

| # | 测试场景 | 预期结果 | 状态 |
|---|---------|---------|------|
| 38 | OneTapLogin 运营商/云函数一键登录 | 获取凭据后调用 V3 端点，返回 JWT | ⬜ |
| 39 | 一键登录成功 | 存储双 Token 并跳转 redirect | ⬜ |
| 39a | 新用户一键登录 | `is_new_user=true`，自动注册 | ⬜ |
| 39b | 未同意条款 | 3002，提示勾选协议 | ⬜ |

### 12.11 V3 手机号注册/登录测试

> 完整清单见 V3 增量文档 §七

| # | 测试场景 | 预期结果 | 状态 |
|---|---------|---------|------|
| 40 | PhoneLogin 图形验证码 UI | 页面展示 captcha 行；进入页加载 `GET /auth/captcha` | ⬜ |
| 40a | PhoneLogin 未填图形码点发码 | 提示「请先输入图形验证码」，不请求发码接口 | ⬜ |
| 40b | PhoneLogin 手机发码 | scenario=LOGIN、channel=SMS；请求体含 captcha 字段 | ⬜ |
| 40c | PhoneLogin 邮箱发码 | scenario=LOGIN、channel=EMAIL；请求体含 captcha 字段 | ⬜ |
| 40d | PhoneLogin 非法账号 | 提示手机号或邮箱格式错误 | ✅ 单元测试 |
| 41 | Register 手机注册 | register_ticket → 直接登录 | ⬜ |
| 42 | BindPhone ticket 绑定 | bind_ticket 消费成功 | ⬜ |

### 12.12 登录页 UI 大样式自测（v1）

> 详细清单见 V3 增量文档 §1.1 与 `src/common/auth.scss`

| # | 测试场景 | 预期结果 | 状态 |
|---|---------|---------|------|
| 43 | 未登录跳转 | 默认 OneTapLogin，非 Login | ⬜ |
| 44 | 登录页切换 | 三页 auth-alt 互跳：一键 / 密码 / 验证码 | ⬜ |
| 45 | 登录页视觉一致 | 容器/标题/按钮 tokens 相同 | ⬜ |
| 46 | RegisterChoice 分流 | 选择页进入 phone/email 注册；无 mode 重定向 | ⬜ |
| 47 | Mobile / Desktop 断点 | 容器宽度、padding-top、按钮高度符合 wireframe | ⬜ |
| 48 | 连续登录失败 5 次 | 返回 HTTP 429，提示锁定信息 | ⬜ |

### 12.13 忘记密码测试

| # | 测试场景 | 预期结果 | 状态 |
|---|---------|---------|------|
| 49 | 邮箱路径：步骤2 新密码仅 7 位 | 提示「密码至少8位」 | ⬜ |
| 50 | 邮箱路径：步骤2 新密码 8 位纯小写 | 允许提交（对齐后端 PasswordReset） | ⬜ |
| 51 | SMS 路径：reset_ticket 重置 | 手机号 OTP → verify → 重置成功 | ⬜ |

### 12.14 回归测试

| # | 测试场景 | 预期结果 | 状态 |
|---|---------|---------|------|
| 52 | 登录/忘记密码页不受影响 | 原有功能正常 | ⬜ |
| 53 | Profile.vue 原有功能正常 | 个人中心功能不受影响 | ⬜ |
| 54 | ProfileEdit.vue 原有功能正常 | 编辑资料功能不受影响 | ⬜ |
| 55 | Settings.vue 中「账号与安全」入口正常 | 点击可跳转 AccountSecurity | ⬜ |

---

## 📝 文档修订历史

| 版本 | 日期 | 修订内容 | 作者 |
|------|------|----------|------|
| V1.0 | 2026-06-07 | 初始版本，AccountSecurity 重构 + 登录 UI v1 | Claude |
| V1.1 | 2026-07-09 | 同步后端 V1.1：18 端点、SSO、邮箱绑定、头像独立上传、bio/验证状态字段、注册昵称、管理端筛选 | Copilot |
| V1.2 | 2026-07-13 | 契约审查修订：BindPhone 图形验证码、RegisterResponse、PasswordReset 仅 min 8、HTTP 429 锁定、管理端全量筛选 UI、PATCH 2004、章节与对接清单修正 | Cursor |
| V1.3 | 2026-07-13 | 对齐后端注销 captcha（DeactivateAccountRequest + AccountSecurity 验证码层）、BindEmail captcha 结构、ForgotPassword 入口、Captcha 双字段兼容、Admin status 收窄 | Cursor |
| V1.4 | 2026-07-13 | 对齐后端 V1.2 + V3：双通道注册摘要、Ticket 闭环、BindPhone bind_ticket、OneTapLogin 运营商登录、API 路由表扩展；详情见 V3 前端增量文档 | Cursor |
| V1.5 | 2026-07-13 | 产品结构定稿：三主登录（一键/密码/验证码）+ RegisterChoice 注册分流；Register 单模式；同步 V3.1 增量文档 | Cursor |
| V1.6 | 2026-07-13 | 明确验证码登录（PhoneLogin）整页无图形验证码；§1.2.1 三主登录对照表；PhoneLogin 支持手机/邮箱 | Cursor |
| V1.7 | 2026-07-13 | **修正**：验证码登录发码前必填图形验证码；§9.1.1 补充 captcha 页面结构 | Cursor |
| V1.7.1 | 2026-07-16 | 同步 V3.5：API 表补 `POST /auth/login/email`；对接清单 #32 邮箱验证码登录闭环 | Cursor |

---

**文档结束** ✅
