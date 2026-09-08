# 用户认证与管理 — 手机号与运营商登录增量前端设计文档（V3）

**版本**: V3.5  
**日期**: 2026-07-16  
**状态**: ✅ 已实现（对齐代码）；**后端 `POST /auth/login/email` 已就绪**  
**基于**: 《Live-Saas-Wechat-10-用户认证与管理-前端设计文档-v1.7.md》V1.5  
**后端对齐**: 《10-用户认证与管理-后端设计文档.md》V1.2、《10-用户认证与管理-V3-手机号与运营商登录增量设计文档.md》V3.0（含 EMAIL LOGIN → `login/email`）  
**UI 对齐**: 《登录注册找回-统一设计语言与自适配方案.md》§5（手机号快速注册）、登录大样式 `auth.scss`

---

## ⚠️ 重要声明

- 本文档为 **增量**，不替代 V1.5 主文档中的邮箱注册、密码登录、Admin 用户管理等设计
- V2 昵称/头像内容安全设计 **不变**
- V1.4 主文档中 **邮箱注册**（`POST /users/register` + 明文 `verification_code`）**保持不变**
- 本次新增/修改聚焦于：**OTP → Ticket 闭环**、手机号注册/登录、**邮箱验证码登录**、运营商一键登录、绑定手机 ticket 化
- 未标注内容以 V1.5 主文档为准
- **V3.5**：确认后端邮箱验证码登录消费端点 `POST /auth/login/email` 已可用；前端 `PhoneLogin` 双通道链路与行动清单对齐闭环

---

## 📌 变更范围

| 变更类型 | 说明 |
|----------|------|
| 【新增页面】 | `PhoneLogin.vue` — 验证码登录（手机/邮箱 OTP → Ticket → `login/phone` 或 `login/email`） |
| 【新增页面】 | `RegisterChoice.vue` — 注册方式选择（手机号注册 / 邮箱注册） |
| 【改造页面】 | `Register.vue` — 单模式注册页（`?mode=phone\|email`；无 mode 重定向 RegisterChoice） |
| 【改造页面】 | `OneTapLogin.vue` — 对接运营商 `one-tap-login` / 云函数 HMAC |
| 【改造页面】 | `BindPhone.vue` — `bind_ticket` 替代明文 OTP |
| 【改造页面】 | `ForgotPassword.vue` — 增加 SMS 重置路径（`PASSWORD_RESET` + `reset_ticket`） |
| 【新增类型】 | `VerifyCodeRequest/Response`、`PhoneRegisterRequest/Response`、`PhoneLoginRequest`、`EmailLoginRequest`、`OneTapLoginRequest`、`OneTapLoginResponse` |
| 【修改类型】 | `BindPhoneRequest`：`phone_number` + `bind_ticket`；`VerificationCodeRequest`：`LOGIN` 发码须传 captcha；`ScenarioType` 增加 `LOGIN` |
| 【新增 API】 | `verifyVerificationCode`、`loginByPhone`、`loginByEmail`、`registerByPhone`、`oneTapLogin`、`oneTapLoginCloudFunction` |
| 【新增 composable】 | `useOtpTicket.ts` — 封装发码 → verify → 持 ticket 提交的统一逻辑；`detectLoginRecipient` 识别手机/邮箱 |

---

## 一、页面与路由

### 1.1 认证页导航关系（V3.1 · 三主登录 + 注册选择页）

```
OneTapLogin.vue（默认未登录入口）
  ├─ [主] 一键登录 → POST /auth/one-tap-login（或 cloud-function）
  ├─ [auth-alt] 密码登录 → Login.vue
  ├─ [auth-alt] 验证码登录 → PhoneLogin.vue
  └─ [auth-link] 注册账号 → RegisterChoice.vue

Login.vue（密码登录）
  ├─ [主] 账号（手机号/邮箱/用户名）+ 密码 + 图形验证码 → POST /auth/login
  ├─ [auth-alt] 一键登录 → OneTapLogin
  ├─ [auth-alt] 验证码登录 → PhoneLogin
  ├─ [auth-link] 注册账号 → RegisterChoice
  └─ [auth-link] 忘记密码 → ForgotPassword.vue

PhoneLogin.vue（验证码登录）
  ├─ [主] 手机号或邮箱 + OTP → login_ticket → login/phone（SMS）或 login/email（EMAIL）
  ├─ [auth-alt] 一键登录 → OneTapLogin
  ├─ [auth-alt] 密码登录 → Login
  └─ [auth-link] 注册账号 → RegisterChoice

RegisterChoice.vue
  ├─ [主] 手机号注册 → Register?mode=phone
  └─ [次] 邮箱注册 → Register?mode=email

Register.vue（单模式，由 URL mode 决定）
  ├─ mode=phone：手机号 + OTP → register_ticket → register/phone → 直接登录
  ├─ mode=email：沿用 V1.4 邮箱注册表单 → POST /users/register → 跳转登录
  ├─ 无 mode：redirectTo RegisterChoice
  └─ [link] 切换注册方式 → RegisterChoice
```

> **产品结构**：登录三主入口（一键 / 密码 / 验证码）互相可切换；**不再**将「邮箱登录」「手机号登录」拆为独立主入口。注册统一经 `RegisterChoice` 分流。

### 1.2 注册页 UI 约定

| 页面 | 说明 |
|------|------|
| `RegisterChoice` | 两个全宽按钮：「手机号注册」「邮箱注册」；底部「去登录」 |
| `Register?mode=phone` | 副标题「使用手机号快速注册」；手机 Ticket 三步注册 |
| `Register?mode=email` | 副标题「使用邮箱注册」；邮箱 OTP 注册（V1.4 逻辑不变） |

| mode | 副标题 | 表单字段 | 提交接口 |
|------|--------|----------|----------|
| `phone` | 使用手机号快速注册 | 手机号、图形验证码、短信 OTP、昵称、密码、确认密码 | `register/phone`（三步 Ticket） |
| `email` | 使用邮箱注册 | 用户名、邮箱、昵称、图形验证码、邮箱 OTP、密码、确认密码 | `POST /users/register`（V1.4 不变） |

`pages.json` 路由与导航栏标题：

```json
{
  "path": "pages/auth/OneTapLogin",
  "style": { "navigationBarTitleText": "登录" }
},
{
  "path": "pages/auth/Login",
  "style": { "navigationBarTitleText": "密码登录" }
},
{
  "path": "pages/auth/PhoneLogin",
  "style": { "navigationBarTitleText": "验证码登录" }
},
{
  "path": "pages/auth/RegisterChoice",
  "style": { "navigationBarTitleText": "选择注册方式" }
},
{
  "path": "pages/auth/Register",
  "style": { "navigationBarTitleText": "注册" }
}
```

`Register.vue` 在 `onLoad` 读取 `mode`，并 `setNavigationBarTitle` 为「手机号注册」或「邮箱注册」。

---

## 二、类型定义增量

> 追加至 `src/types/auth.ts`

```typescript
/** scenario 扩展：V3 新增 LOGIN */
export type ScenarioType =
  | 'REGISTER'
  | 'PASSWORD_RESET'
  | 'LOGIN'
  | 'BIND_PHONE'
  | 'BIND_EMAIL'

/**
 * 发送验证码（V3：所有 scenario 含 LOGIN 发码前须传 captcha）
 */
export interface VerificationCodeRequest {
  channel: ChannelType
  recipient: string
  scenario: ScenarioType
  captcha_id?: string
  captcha_solution?: string
}

/** 校验 OTP 并签发 Ticket */
export interface VerifyCodeRequest {
  channel: ChannelType
  recipient: string
  scenario: ScenarioType
  code: string
}

export interface VerifyCodeResponse {
  ticket: string
  expires_in: number  // 默认 600
}

/** 手机号 Ticket 注册 */
export interface PhoneRegisterRequest {
  register_ticket: string
  password: string
  nickname: string     // 1-50（对齐后端 PhoneRegisterRequest）
}

export interface PhoneRegisterResponse {
  public_id: string
  username: string
  nickname: string
  phone_number: string   // 掩码，如 138****8000
  is_phone_verified: boolean
  is_new_user: boolean
  access_token: string
  refresh_token: string
  token_type: 'bearer'
}

/** 手机号 Ticket 登录 */
export interface PhoneLoginRequest {
  login_ticket: string
}

/** 邮箱 Ticket 登录（与 PhoneLoginRequest 同构，消费端点不同） */
export interface EmailLoginRequest {
  login_ticket: string
}

/** 运营商一键登录（方案 A） */
export interface OneTapLoginRequest {
  carrier_token: string
  provider?: string
  agreed_to_terms: boolean
}

/** 云函数 HMAC 一键登录（方案 B · 微信小程序推荐） */
export interface CloudFunctionLoginRequest {
  phone: string
  sign: string
  timestamp: number
}

export interface OneTapLoginResponse {
  access_token: string
  refresh_token: string
  token_type: 'bearer'
  is_new_user?: boolean
  phone_masked?: string
  user_public_id?: string
  username?: string
  nickname?: string
}

/**
 * 绑定手机号（V3：bind_ticket 替代 verification_code）
 */
export interface BindPhoneRequest {
  phone_number: string
  bind_ticket: string
}

/** 密码重置（双路径：邮箱 reset_token 或 SMS reset_ticket） */
export interface PasswordReset {
  reset_token?: string
  reset_ticket?: string
  new_password: string
}
```

---

## 三、API 封装增量

> 追加至 `src/api/auth.ts`；`registerByPhone` 可放 `auth.ts` 或 `user.ts`

```typescript
// src/config/api.ts AUTH 段追加
AUTH: {
  // ... 现有 ...
  VERIFICATION_CODES_VERIFY: '/auth/verification-codes/verify',
  LOGIN_PHONE: '/auth/login/phone',
  LOGIN_EMAIL: '/auth/login/email',
  ONE_TAP_LOGIN: '/auth/one-tap-login',
  ONE_TAP_LOGIN_CF: '/auth/one-tap-login/cloud-function',
  CAPTCHA_IMAGE: (id: string) => `/auth/captcha/image/${id}`
},
USER: {
  // ... 现有 ...
  REGISTER_PHONE: '/register/phone'
}

/** 校验 OTP → 签发 ticket */
export const verifyVerificationCode = (
  data: VerifyCodeRequest
): Promise<ApiResponse<VerifyCodeResponse>> => {
  return request.post(API_PATHS.AUTH.VERIFICATION_CODES_VERIFY, data, { auth: false })
}

/** 手机号 ticket 登录 */
export const loginByPhone = (
  data: PhoneLoginRequest
): Promise<ApiResponse<LoginResponse>> => {
  return request.post(API_PATHS.AUTH.LOGIN_PHONE, data, { auth: false })
}

/** 邮箱 ticket 登录 */
export const loginByEmail = (
  data: EmailLoginRequest
): Promise<ApiResponse<LoginResponse>> => {
  return request.post(API_PATHS.AUTH.LOGIN_EMAIL, data, { auth: false })
}

/** 手机号 ticket 注册（成功直接返回 JWT） */
export const registerByPhone = (
  data: PhoneRegisterRequest
): Promise<ApiResponse<PhoneRegisterResponse>> => {
  return request.post(API_PATHS.USER.REGISTER_PHONE, data, { auth: false })
}

/** 运营商一键登录 */
export const oneTapLogin = (
  data: OneTapLoginRequest
): Promise<ApiResponse<OneTapLoginResponse>> => {
  return request.post(API_PATHS.AUTH.ONE_TAP_LOGIN, data, { auth: false })
}

/** 云函数 HMAC 一键登录 */
export const oneTapLoginCloudFunction = (
  data: CloudFunctionLoginRequest
): Promise<ApiResponse<OneTapLoginResponse>> => {
  return request.post(API_PATHS.AUTH.ONE_TAP_LOGIN_CF, data, { auth: false })
}
```

`bindMyPhone` 请求体改为 `BindPhoneRequest`（`phone_number` + `bind_ticket`）。

---

## 四、OTP → Ticket 通用逻辑

### 4.1 composable：`useOtpTicket.ts`

```typescript
/**
 * 封装「发码 → verify → 返回 ticket」
 * @param scenario REGISTER | LOGIN | BIND_PHONE | PASSWORD_RESET
 * @param channel SMS | EMAIL
 */
export function useOtpTicket() {
  async function sendOtp(params: {
    channel: ChannelType
    recipient: string
    scenario: ScenarioType
    captchaId?: string
    captchaSolution?: string
  }): Promise<void> { /* POST /verification-codes */ }

  async function verifyOtp(params: {
    channel: ChannelType
    recipient: string
    scenario: ScenarioType
    code: string
  }): Promise<string> { /* 返回 ticket */ }

  return { sendOtp, verifyOtp }
}
```

### 4.2 图形验证码规则（V3 修订）

> **产品定稿**：验证码登录（`PhoneLogin`）发码前**必须**通过图形验证码，与注册/绑定/找回密码一致；仅一键登录（运营商信任链）豁免。

| scenario | 发码前是否需要图形验证码 | 典型页面 |
|----------|--------------------------|----------|
| `LOGIN` | ✅ **必填** | `PhoneLogin` |
| `REGISTER` | ✅ 必填 | `Register` |
| `BIND_PHONE` | ✅ 必填 | `BindPhone` |
| `BIND_EMAIL` | ✅ 必填 | `BindEmail` |
| `PASSWORD_RESET` | ✅ 必填 | `ForgotPassword`（SMS 路径） |

### 4.3 Ticket 时效与错误处理

| 情况 | 前端处理 |
|------|----------|
| verify 成功 | 缓存 `ticket` + `recipient`，**600s 内**调用消费端点 |
| ticket 过期/无效（4011） | Toast「验证已过期，请重新获取验证码」→ 清空 ticket，回到发码步骤 |
| OTP 错误（4012） | Toast「验证码错误」；累计 5 次后需重新发码 |
| 手机号已注册（2002） | 注册：提示去登录；绑定：提示换号 |
| 未同意条款（3002） | 一键登录：高亮协议区，要求勾选后再试 |

---

## 五、页面详细设计

### 5.1 OneTapLogin.vue（改造）

**主流程（生产 · 微信小程序）**：

1. 用户勾选/确认协议（`agreed_to_terms`）
2. 调用 DCloud `uni.login` + 云函数解密手机号（或运营商 SDK 取 `carrier_token`）
3. **方案 B（推荐）**：云函数返回 `{ phone, sign, timestamp }` → `oneTapLoginCloudFunction`
4. **方案 A（备选）**：`carrier_token` → `oneTapLogin({ carrier_token, agreed_to_terms: true })`
5. 成功：`setTokens` → `authStore.fetchUserInfo()` → 跳转 redirect
6. `is_new_user=true` 时可 Toast「欢迎加入」

**开发 Mock**：`carrier_token = "mock:+8613800138000"`（仅 dev）

**次入口**：

- `auth-alt`「密码登录」→ `Login.vue`
- `auth-alt`「验证码登录」→ `PhoneLogin.vue`
- `auth-link`「注册账号」→ `RegisterChoice.vue`

**移除/降级**：原 `POST /auth/sso-login`（Authing `id_token`）降为可选扩展，V3 主路径不再依赖。

### 5.2 PhoneLogin.vue（新增 · V3.2 支持手机/邮箱）

> **图形验证码**：本页**必须**包含图形验证码组件；`onMounted` 调用 `GET /auth/captcha`；点击「获取验证码」前校验 captcha 已填；发码请求携带 `captcha_id` + `captcha_solution`。

```
PhoneLogin.vue
├─ auth-title: H1「验证码登录」+ 副标题「验证码将发送至您的手机或邮箱」
├─ 账号输入框（placeholder「手机号 / 邮箱」）
├─ 图形验证码行（复用 auth.scss `.captcha-row` / `.captcha-box`，与 Login 一致）
├─ OTP 验证码行
│    ├─ OTP 输入框（短信/邮箱验证码）
│    └─ 「获取验证码」按钮（cooldown 60s）
│         └─ POST /verification-codes (channel=SMS|EMAIL, scenario=LOGIN, captcha 必填)
├─ 「登录」主按钮
│    ├─ Step A: verify → login_ticket
│    └─ Step B: SMS → POST /auth/login/phone；EMAIL → POST /auth/login/email
├─ auth-alt「一键登录」→ OneTapLogin
├─ auth-alt「密码登录」→ Login
└─ auth-link「注册账号」→ RegisterChoice
```

**recipient 识别规则**（`useOtpTicket.detectLoginRecipient`）：

| 输入特征 | channel | recipient 规范化 | 消费端点 |
|----------|---------|------------------|----------|
| 含 `@` 且通过邮箱正则 | `EMAIL` | `trim` + `toLowerCase` | `POST /auth/login/email` |
| 11 位 `1` 开头手机号 | `SMS` | `trim` | `POST /auth/login/phone` |
| 其他 | — | 校验失败，提示「请输入正确的手机号或邮箱」 | — |

**注意**：登录按钮可在用户填完 OTP 后一次性执行 verify + 对应 login 端点；或分步（获取验证码时仅发码，点登录时 verify+消费）。

### 5.3 RegisterChoice.vue（新增）+ Register.vue（单模式）

**RegisterChoice**：

- 主按钮「手机号注册」→ `Register?mode=phone`
- 次按钮「邮箱注册」→ `Register?mode=email`
- 底部「已有账号？去登录」→ `navigateBack` 或 `OneTapLogin`

**Register.vue**（`onLoad` 读取 `mode`）：

**mode=phone**：

```
1. 输入手机号、昵称、密码
2. 图形验证码 + 「获取验证码」
   → POST /verification-codes (SMS, REGISTER, captcha 必填)
3. 用户填 OTP，点「注册」
   → POST /verification-codes/verify (REGISTER) → register_ticket
   → POST /users/register/phone
4. 成功：setTokens → fetchUserInfo → 跳转首页（不经过 Login）
```

**mode=email**：保持 V1.4 邮箱注册表单与逻辑不变；成功后跳转 `OneTapLogin`。

**路由守卫**：无有效 `mode` 参数时 `redirectTo RegisterChoice`；页内「切换注册方式」同样回到 `RegisterChoice`（**禁止**页内 pill 切换）。

### 5.4 BindPhone.vue（改造）

```
原：发码 → 直接 POST /me/phone { phone, verification_code }
新：发码 → verify(BIND_PHONE) → bind_ticket → POST /me/phone { phone_number, bind_ticket }
```

- 发码：`POST /verification-codes`（SMS, BIND_PHONE, captcha 必填）
- verify：用户输入 OTP 后调用，或在「确认绑定」时合并 verify + bind
- 提交：`phone_number` 必须与 verify 时的 `recipient` 一致

### 5.5 ForgotPassword.vue（增量 · SMS 路径）

在现有邮箱两步流基础上，增加顶部 mode 切换（pill，非 tab）：

| mode | 流程 |
|------|------|
| `email`（默认） | V1.4 不变：`password-reset-request` → `reset_token` |
| `sms` | 手机号 + captcha → 发码(PASSWORD_RESET) → verify → `reset_ticket` → `POST /auth/password-reset` |

SMS 路径 `new_password` 校验规则仍对齐 V1.4：**仅 min 8**。

### 5.6 Pinia / Store 增量

`authStore` 新增：

```typescript
async function loginByPhoneTicket(login_ticket: string): Promise<void>
async function loginByEmailTicket(login_ticket: string): Promise<void>
async function loginByOtpTicket(login_ticket: string, channel: ChannelType): Promise<void>
async function registerByPhoneTicket(data: PhoneRegisterRequest): Promise<void>
async function oneTapLogin(data: OneTapLoginRequest): Promise<void>
async function oneTapLoginViaCloudFunction(data: CloudFunctionLoginRequest): Promise<void>
```

- `loginByOtpTicket`：`channel=EMAIL` → `loginByEmailTicket` → `POST /auth/login/email`；否则 → `loginByPhoneTicket`
- 手机号注册 / 一键登录 / 验证码登录成功后均：`setTokens` → `fetchUserInfo()`

### 5.7 邮箱验证码登录闭环（V3.5 确认）

> **后端状态（2026-07-16）**：`POST /auth/login/email` 已实现，消费 `LOGIN` scenario 下 `channel=EMAIL` 签发的 `login_ticket`。

```
PhoneLogin（输入邮箱）
  1. GET /auth/captcha
  2. POST /auth/verification-codes
       { channel: EMAIL, recipient, scenario: LOGIN, captcha_id, captcha_solution }
  3. POST /auth/verification-codes/verify
       { channel: EMAIL, recipient, scenario: LOGIN, code } → login_ticket
  4. POST /auth/login/email
       { login_ticket } → JWT
  5. authStore.setTokens + fetchUserInfo → finishAuth()
```

| 规则 | 说明 |
|------|------|
| recipient 规范化 | `trim` + `toLowerCase` |
| 图形验证码 | 发码必填；发码成功后刷新 captcha（供重发） |
| 用户不存在 | 后端拒绝；前端展示接口 message（不自动注册） |
| 与邮箱密码登录区分 | 密码登录走 `Login.vue` → `POST /auth/login`；验证码登录走本页 |

---

## 六、行动清单（Action Checklist）

> **状态说明**：基于 2026-07-16 对 `src/` 源码静态审查；联调项见自测清单。

| # | 行动项 | 涉及文件 | 验收标准 | 状态 |
|---|--------|----------|----------|------|
| 1 | 扩展认证类型 | `src/types/auth.ts` | `EmailLoginRequest`、`VerifyCode*`、`ScenarioType.LOGIN` | ✅ 已实现 |
| 2 | 扩展 API 路径 | `src/config/api.ts` | `LOGIN_EMAIL`、`LOGIN_PHONE`、`VERIFICATION_CODES_VERIFY` | ✅ 已实现 |
| 3 | 封装 verify / loginByPhone / loginByEmail | `src/api/auth.ts` | 三函数可调用，路径正确 | ✅ 已实现 |
| 4 | 修改 bindMyPhone | `src/api/user.ts` | body 为 `phone_number` + `bind_ticket` | ✅ 已实现 |
| 5 | useOtpTicket + detectLoginRecipient | `src/composables/useOtpTicket.ts` | 发码/verify；手机/邮箱识别 | ✅ 已实现 |
| 6 | detectLoginRecipient 单元测试 | `test/loginRecipient.test.ts` | 手机/邮箱/非法输入用例通过 | ✅ 已实现 |
| 7 | 改造 OneTapLogin | `src/pages/auth/OneTapLogin.vue` | 运营商/云函数 + 三入口互跳 | ✅ 已实现 |
| 8 | PhoneLogin 双通道 UI | `src/pages/auth/PhoneLogin.vue` | 图形码 + OTP；副标题随账号类型变化 | ✅ 已实现 |
| 9 | PhoneLogin 邮箱登录消费 | 同上 + `authStore` | verify → `loginByEmail` → JWT | ✅ 已实现 |
| 10 | PhoneLogin 发码后刷新 captcha | `PhoneLogin.vue` | 发码成功清空并换新图形码 | ✅ 已实现 |
| 11 | RegisterChoice 分流 | `src/pages/auth/RegisterChoice.vue` | 手机/邮箱注册入口 | ✅ 已实现 |
| 12 | Register 单模式 | `src/pages/auth/Register.vue` | `?mode=phone\|email`；无 mode 重定向 | ✅ 已实现 |
| 13 | BindPhone ticket 绑定 | `src/pages/settings/BindPhone.vue` | verify → bind_ticket → `/me/phone` | ✅ 已实现 |
| 14 | ForgotPassword SMS 路径 | `src/pages/auth/ForgotPassword.vue` | reset_ticket 重置 | ✅ 已实现 |
| 15 | authStore OTP 登录方法 | `src/store/auth.ts` | `loginByEmailTicket` / `loginByOtpTicket` | ✅ 已实现 |
| 16 | pages.json 路由 | `src/pages.json` | PhoneLogin / RegisterChoice 标题正确 | ✅ 已实现 |
| 17 | authRoutes 常量 | `src/common/authRoutes.ts` | `CODE_LOGIN` / `REGISTER_CHOICE` 等 | ✅ 已实现 |
| 18 | 主文档 API 表补 `login/email` | `docs/...前端设计文档-v1.7.md` | 路由表含 `POST /auth/login/email` | ✅ 已同步 |

---

## 七、自测清单

| # | 场景 | 预期 | 状态 |
|---|------|------|------|
| 1 | OneTapLogin Mock 一键登录 | 返回 JWT，新用户 `is_new_user=true` | ⬜ 待联调 |
| 2 | 未勾选协议点一键登录 | 3002，提示同意条款 | ✅ 静态：前端拦截 + 后端 3002 |
| 3 | PhoneLogin 图形验证码 UI | 展示 captcha 行；进入页加载 captcha | ✅ 静态：页面含 captcha-row |
| 3a | PhoneLogin 未填图形码发码 | 前端拦截，提示先填图形验证码 | ✅ 静态 |
| 3b | PhoneLogin 手机发码（LOGIN） | SMS、请求体含 captcha，60s 冷却 | ⬜ 待联调 |
| 3c | PhoneLogin 邮箱发码（LOGIN） | EMAIL、请求体含 captcha，60s 冷却 | ⬜ 待联调（后端 EMAIL 可能仍日志模拟） |
| 4 | PhoneLogin 手机完整登录 | verify → login/phone → 进首页 | ⬜ 待联调 |
| 4b | PhoneLogin 邮箱完整登录 | verify → login/email → 进首页 | ⬜ 待联调（后端已就绪） |
| 4c | PhoneLogin 非法账号 | 提示「请输入正确的手机号或邮箱」 | ✅ 单元测试 |
| 4d | PhoneLogin 发码成功后图形码刷新 | captcha 输入清空且图片更新 | ✅ 静态 |
| 5 | RegisterChoice 分流 | 手机/邮箱按钮进入对应 Register | ✅ 静态 |
| 6 | Register 手机注册成功 | 直接持 JWT 进首页，不跳 Login | ⬜ 待联调 |
| 7 | Register 邮箱模式 | `?mode=email` 表单与 V1.4 行为一致 | ✅ 静态 |
| 8 | Register 无 mode | 自动重定向 RegisterChoice | ✅ 静态 |
| 9 | BindPhone ticket 绑定 | verify → bind_ticket → /me/phone 成功 | ⬜ 待联调 |
| 10 | ticket 过期后提交 | 4011，引导重新获取验证码 | ✅ 静态：`handleTicketError` |
| 11 | ForgotPassword SMS 路径 | reset_ticket 重置成功 | ⬜ 待联调 |
| 12 | V2 ProfileEdit 头像/昵称 | 不受 V3 影响，仍正常 | ✅ 静态：未改动 V2 路径 |
| 13 | 云函数 HMAC 签名错误 | 登录失败，友好提示 | ⬜ 待联调 |
| 14 | 三登录页互跳 | auth-alt 一键/密码/验证码均可达 | ✅ 静态 |

---

## 📝 修订历史

| 版本 | 日期 | 修订内容 | 作者 |
|------|------|----------|------|
| V3.0 | 2026-07-13 | 初版：Ticket 闭环、手机注册/登录、一键登录、BindPhone/ForgotPassword 改造 | Cursor |
| V3.1 | 2026-07-13 | 产品结构定稿：三主登录（一键/密码/验证码）+ RegisterChoice 注册分流；Register 单模式 | Cursor |
| V3.2 | 2026-07-13 | PhoneLogin 支持手机/邮箱双通道；`detectLoginRecipient` + `login/email` | Cursor |
| V3.3 | 2026-07-13 | 明确验证码登录整页无图形验证码（§4.2 / §5.2 / 自测项） | Cursor |
| V3.4 | 2026-07-13 | **修正**：验证码登录发码前必填图形验证码（对齐产品要求） | Cursor |
| V3.5 | 2026-07-16 | 后端邮箱验证码登录已就绪；补 §5.7 闭环、行动清单状态、发码后刷新 captcha、主文档 API 表同步 | Cursor |

---

**文档结束** ✅
