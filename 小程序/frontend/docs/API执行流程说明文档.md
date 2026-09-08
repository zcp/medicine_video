# API 执行流程说明（前端 → 后端 → 前端）

> 说明基于当前仓库代码，重点文件：
> - `src/utils/request.ts`
> - `src/api/auth.ts`
> - `src/api/user.ts`
> - `src/types/common.ts`
> - `src/store/auth.ts`
>
> 文档目标：说明一次 API 调用从页面/Store 发起，到后端接口，再到前端拿到数据渲染的完整执行链路，并精确到关键函数和文件位置。
>
> 本文分为两部分：
> - **基础版**：整体架构和关键代码位置（适合先有全局印象）
> - **进阶版**：以“点击微信登录按钮”为例，从页面到后端再回来的完整故事（适合初学者一步一步跟着代码走）

---

## 基础版：API 执行流程总览

## 一、整体调用链概览

一次完整的 API 请求时序可以概括为：

1. **页面 / Store 触发业务调用**  
   例如登录、刷新 Token、获取当前用户信息等。
2. 调用 **`src/api/*.ts` 中的接口函数**  
   如 `login`、`wechatLogin`、`getCurrentUser`、`refreshToken` 等。
3. 这些接口函数内部调用统一封装的 **`request` 工具**（`src/utils/request.ts`）。
4. `request` 工具：
   - 处理 Mock（可选）
   - 执行请求拦截器（日志等）
   - 组装 `baseURL + url`、请求头、Token、loading 等
   - 使用 **`uni.request`** 把 HTTP 请求真正发往后端服务器
5. **后端 HTTP 服务** 接收请求，根据 `URL + Method` 匹配到对应接口，执行业务逻辑，返回统一格式的 JSON 数据（`ApiResponse<T>`）。
6. 前端 **响应拦截器** 统一处理后端返回：
   - 校验 `code` 是否为 200
   - 统一抛出业务错误
   - 把 `ApiResponse<T>` 的 `data` 字段“解包”成真正的业务数据
7. 页面 / Store 得到业务数据，更新状态，渲染 UI。

简化时序图：

```text
页面/Store → src/api/*.ts → src/utils/request.ts → uni.request
   → 后端接口（/api/...）→ 返回 ApiResponse<T>
   → 响应拦截器解包 → 业务代码拿到 data
```

---

## 二、前端发起请求的链路（以登录/用户信息为例）

### 2.1 页面 / Store 调用 API 模块

示例：在认证 Store 中调用刷新 Token（`src/store/auth.ts`，节选）：

```ts
const response = await refreshTokenApi({ refreshToken: this.refreshToken })
```

其中 `refreshTokenApi` 来自 `src/api/auth.ts`：

```ts
import { refreshToken as refreshTokenApi } from '@/api/auth'
```

同理，登录、获取用户信息等，都会通过 `src/api/*.ts` 中导出的函数间接调用网络请求。

### 2.2 API 模块：业务语义到 HTTP 请求的映射

以认证相关 API 为例（`src/api/auth.ts`）：

```ts
import { request } from '@/utils/request'
import type { 
  LoginResponse, 
  RegisterRequest, 
  RegisterResponse,
  RefreshTokenRequest,
  RefreshTokenResponse,
  ResetPasswordRequest,
  ChangePasswordRequest,
  SendSmsRequest,
  VerifySmsRequest,
  WechatLoginRequest,
  LogoutRequest
} from '@/types/auth'
import type { ApiResponse } from '@/types/common'
```

#### 2.2.1 传统登录（APP / H5）

```ts
// #ifdef APP-PLUS || H5
export const login = (data: LoginRequest): Promise<ApiResponse<LoginResponse>> => {
  return request({
    url: '/auth/login',
    method: 'POST',
    data,
    auth: false,
    loading: true,
    loadingText: '登录中...'
  })
}
// #endif
```

#### 2.2.2 微信登录（跨平台）

```ts
export const wechatLogin = (data: WechatLoginRequest): Promise<ApiResponse<LoginResponse>> => {
  let apiUrl = '/api/v1/auth/wechat-login'
  
  // #ifdef MP-WEIXIN
  apiUrl = '/api/v1/auth/mp-login'
  // #endif
  // #ifdef APP-PLUS
  apiUrl = '/api/v1/auth/wechat-login'
  // #endif
  // #ifdef H5
  apiUrl = '/api/v1/auth/wechat-h5-login'
  // #endif

  return request({
    url: apiUrl,
    method: 'POST',
    data,
    auth: false,
    loading: true,
    loadingText: '微信登录中...'
  })
}
```

可以看到：

- 上层业务只关心 **“我要微信登录”**，不关心 HTTP 细节。
- 当前平台对应到不同的后端 URL：
  - 小程序：`/api/v1/auth/mp-login`
  - APP：`/api/v1/auth/wechat-login`
  - H5：`/api/v1/auth/wechat-h5-login`
- 最终统一传给 `request({ ... })` 来执行网络请求。

#### 2.2.3 用户信息相关 API（`src/api/user.ts`）

```ts
import { request } from '@/utils/request'
import type { User, UserProfile } from '@/types/user'
import type { ApiResponse } from '@/types/common'

export const getCurrentUser = (): Promise<ApiResponse<User>> => {
  return request({
    url: '/api/v1/users/me',
    method: 'GET'
  })
}

export const getUserById = (userId: string): Promise<ApiResponse<UserProfile>> => {
  return request({
    url: `/api/v1/users/${userId}`,
    method: 'GET',
    auth: false
  })
}
```

这里同样是把“业务语义”映射到了具体的后端 URL 和 HTTP Method，再交给统一的 `request` 工具处理后续细节。

---

## 三、`request` 工具如何构造并发送 HTTP 请求

统一封装位于：`src/utils/request.ts`。

### 3.1 请求配置结构 `RequestConfig`

```ts
export interface RequestConfig {
  url: string
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH'
  data?: any
  headers?: Record<string, string>
  timeout?: number
  loading?: boolean
  loadingText?: string
  showError?: boolean
  auth?: boolean
  retry?: number
}
```

- `url`：接口路径（不含 baseURL）
- `method`：HTTP 方法，默认 `GET`
- `data`：请求体（`POST/PUT/PATCH`）或查询参数
- `auth`：是否自动带上 Token（默认 `true`）
- `loading` / `loadingText`：是否展示加载中提示
- `showError`：是否自动弹出错误 toast
- `retry`：失败后重试次数

### 3.2 BaseURL 处理：`setBaseURL` & `getFullURL`

```ts
private baseURL: string = ''

constructor() {
  this.setBaseURL()
}

private setBaseURL() {
  // #ifdef H5
  this.baseURL = process.env.NODE_ENV === 'development' 
    ? 'http://localhost:3000/api'
    : 'https://api.yourdomain.com'
  // #endif

  // #ifdef MP-WEIXIN
  this.baseURL = process.env.NODE_ENV === 'development'
    ? 'https://dev-api.yourdomain.com'
    : 'https://api.yourdomain.com'
  // #endif
}

private getFullURL(url: string): string {
  if (url.startsWith('http')) {
    return url
  }
  return `${this.baseURL}${url.startsWith('/') ? url : '/' + url}`
}
```

流程要点：

1. `Request` 实例构造时调用 `setBaseURL()`，按 **平台 + 环境** 设置不同的基础地址。
2. 在真正发送请求前，通过 `getFullURL(url)` 把业务层写的相对路径组装成完整 HTTP URL：
   - 例如 H5 开发环境：`http://localhost:3000/api` + `/api/v1/auth/wechat-h5-login`
   - 小程序开发环境：`https://dev-api.yourdomain.com` + `/api/v1/auth/mp-login`

### 3.3 核心请求方法 `request<T>()` 执行顺序

定义位置：`src/utils/request.ts` 中 `Request` 类的 `async request<T = any>(config: RequestConfig): Promise<T>`。

核心步骤：

1. **合并默认配置**

   ```ts
   const finalConfig: RequestConfig = {
     method: 'GET',
     timeout: this.timeout,
     loading: false,
     loadingText: '加载中...',
     showError: true,
     auth: true,
     retry: 0,
     ...config
   }
   ```

2. **Mock 拦截（如启用）**

   ```ts
   if (mockConfig.enabled) {
     const mockRule = findMockRule(finalConfig.url, finalConfig.method || 'GET')
     if (mockRule) {
       // 可选：显示 loading
       // await mockDelay() 模拟网络延迟
       const mockData = mockRule.handler(finalConfig.data)
       return mockData as T
     }
   }
   ```

   - 如果匹配到 Mock 规则，则**不再执行真实网络请求**，而是直接返回本地模拟数据。

3. **执行请求拦截器**

   ```ts
   const interceptedConfig = await this.runRequestInterceptors(finalConfig)
   ```

   - 当前默认请求拦截器主要用于写日志：

     ```ts
     requestInstance.addRequestInterceptor((config) => {
       const timestamp = Date.now()
       logger.debug('network', 'HTTP request start', {
         url: config.url,
         method: config.method,
         timestamp
       })
       return config
     })
     ```

4. **组装 `uni.request` 的参数**

   ```ts
   const requestOptions: UniApp.RequestOptions = {
     url: this.getFullURL(interceptedConfig.url),
     method: interceptedConfig.method as any,
     data: interceptedConfig.data,
     timeout: interceptedConfig.timeout,
     header: {
       'Content-Type': 'application/json',
       ...interceptedConfig.headers
     }
   }
   ```

5. **自动附加 Token（`auth: true` 时）**

   ```ts
   if (interceptedConfig.auth) {
     const token = this.getToken()
     if (token) {
       requestOptions.header!['Authorization'] = `Bearer ${token}`
     }
   }
   ```

   - `getToken()` 当前实现：`uni.getStorageSync('access_token') || null`。

6. **显示 Loading（可选）**

   ```ts
   if (interceptedConfig.loading) {
     this.showLoading(interceptedConfig.loadingText)
   }
   ```

7. **通过 `uni.request` 向后端发送 HTTP 请求**

   ```ts
   const response = await new Promise<UniApp.RequestSuccessCallbackResult>((resolve, reject) => {
     uni.request({
       ...requestOptions,
       success: resolve,
       fail: reject
     })
   })
   ```

   - 从这一行开始，数据离开前端，进入 **后端服务**：
     - 后端根据 `Method + URL` 路由到对应控制器
     - 执行业务逻辑（验证 Token、操作数据库等）
     - 最终返回统一格式的 JSON 响应。

8. **HTTP 状态码检查**

   ```ts
   if (response.statusCode >= 400) {
     this.handleError({ statusCode: response.statusCode }, interceptedConfig)
   }
   ```

   - `handleError` 会：
     - 根据 `HTTP_STATUS_MESSAGES` 映射用户可读错误文案
     - 记录错误日志
     - `showError !== false` 时，调用 `uni.showToast` 提示
     - 抛出一个带 `statusCode` 和 `config` 的 `Error` 对象

9. **执行响应拦截器**

   ```ts
   const interceptedResponse = await this.runResponseInterceptors(response)
   ```

10. **记录成功日志 & 返回数据**

    ```ts
    logger.debug('network', 'HTTP request success', {
      url: interceptedConfig.url,
      method: interceptedConfig.method,
      statusCode: response.statusCode
    })

    return interceptedResponse.data
    ```

    - 注意：这里返回的是 **拦截器处理后的 `data` 字段**，而不是原始的 `response` 对象。

11. **失败分支中的重试逻辑**

    ```ts
    if (interceptedConfig.retry && interceptedConfig.retry > 0) {
      const retryConfig = { ...interceptedConfig, retry: interceptedConfig.retry - 1 }
      return this.request<T>(retryConfig)
    }

    this.handleError(error, interceptedConfig)
    ```

    - 如果配置了 `retry` 大于 0，则会自动递归重试指定次数。

---

## 四、后端响应格式与前端响应拦截

### 4.1 统一响应类型 `ApiResponse<T>`

文件：`src/types/common.ts`

```ts
export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T | null
  timestamp: string
}
```

约定的标准后端返回 JSON 格式为：

```json
{
  "code": 200,
  "message": "OK",
  "data": { "...": "业务数据" },
  "timestamp": "2025-12-05T07:00:00Z"
}
```

- `code`：业务状态码，**不是 HTTP 状态码**
- `message`：错误或提示信息
- `data`：真正的业务数据载荷
- `timestamp`：时间戳，便于排查问题

### 4.2 响应拦截器：统一处理 `ApiResponse`

文件：`src/utils/request.ts`：

```ts
requestInstance.addResponseInterceptor((response) => {
  const { data } = response
  
  if (data && typeof data === 'object' && 'code' in data) {
    const apiResponse = data as ApiResponse
    
    if (apiResponse.code !== 200) {
      throw new Error(apiResponse.message || '请求失败')
    }
    
    return { ...response, data: apiResponse.data }
  }

  return response
})
```

执行逻辑：

1. 如果 `response.data` 是对象并包含 `code` 字段，则认为后端遵守了统一 `ApiResponse<T>` 协议。
2. 当 `code !== 200`：
   - 抛出一个 `Error(apiResponse.message || '请求失败')`
   - 上层 `await request(...)` 的地方会收到异常，需要用 `try/catch` 捕获。
3. 当 `code === 200`：
   - 把 `response.data` 替换成 `apiResponse.data`，即仅保留业务数据。
   - 返回新的对象 `{ ...response, data: apiResponse.data }`。

### 4.3 `request()` 返回给业务代码的实际数据

在 `request()` 末尾：

```ts
const interceptedResponse = await this.runResponseInterceptors(response)
...
return interceptedResponse.data
```

- 业务层最终拿到的是 **`ApiResponse<T>` 里的 `data` 字段**。
- 类型声明上很多 API 函数是 `Promise<ApiResponse<T>>`，但由于响应拦截器已经“解包”，**实际运行时得到的是 `T` 本身**。

> 提示：后续可以统一一下约定：
> - 要么 API 层返回 `Promise<T>`（完全依赖拦截器），
> - 要么响应拦截器不解包，始终返回完整 `ApiResponse<T>`，由业务自行判断 `code`。

---

## 五、错误处理与重试机制

### 5.1 HTTP 层错误处理：`handleError`

当 `response.statusCode >= 400`，或者 `uni.request` 失败时，调用：

```ts
private handleError(error: any, config: RequestConfig): never {
  const { statusCode, errMsg } = error

  let message = '网络请求失败'

  if (statusCode) {
    message = HTTP_STATUS_MESSAGES[statusCode] || `请求失败 (${statusCode})`
  } else if (errMsg) {
    if (errMsg.includes('timeout')) {
      message = '请求超时，请检查网络连接'
    } else if (errMsg.includes('fail')) {
      message = '网络连接失败，请检查网络'
    }
  }

  logger.error('network', 'HTTP request failed', {
    url: config.url,
    method: config.method,
    statusCode,
    errMsg,
    message
  })

  if (config.showError !== false) {
    this.showError(message)
  }

  const requestError = new Error(message)
  ;(requestError as any).statusCode = statusCode
  ;(requestError as any).config = config
  
  throw requestError
}
```

- 统一把 HTTP / 网络层错误转为易读的中文提示，并记录日志。
- 抛出的 `Error` 对象里附带 `statusCode` 和原始 `config` 方便定位。

### 5.2 业务层错误

- 当后端返回 `code !== 200`，响应拦截器会直接抛 `Error(apiResponse.message || '请求失败')`。
- 业务代码可以通过 `try/catch` 捕获并根据需要自定义 UI 提示。

### 5.3 重试机制

在 `catch` 块中：

```ts
if (interceptedConfig.retry && interceptedConfig.retry > 0) {
  const retryConfig = { ...interceptedConfig, retry: interceptedConfig.retry - 1 }
  return this.request<T>(retryConfig)
}

this.handleError(error, interceptedConfig)
```

- 允许在配置中设置 `retry` 次数，在网络失败时自动重试。

---

## 六、认证 Token 的前后端交互

### 6.1 后端返回 Token

- 登录成功、刷新 Token 等接口通过 `ApiResponse<LoginResponse>` 的 `data` 字段返回：
  - `accessToken`
  - `refreshToken`
  - `expiresIn` 等信息（具体字段定义在 `src/types/auth.ts`）。

### 6.2 前端存储 Token

在 `src/store/auth.ts` 中（节选）：

```ts
if (response.code === 200 && response.data) {
  this.token = response.data.accessToken
  this.tokenExpireTime = Date.now() + response.data.expiresIn * 1000

  uni.setStorageSync('token', this.token)
  uni.setStorageSync('tokenExpireTime', this.tokenExpireTime)
}
```

> 注意：目前 `request.ts` 中是从 `uni.getStorageSync('access_token')` 读取 Token，
> 而这里保存使用的是 `'token'`，二者存在 key 不一致的问题，后续需要统一。

### 6.3 后续请求自动携带 Token

在 `request()` 方法中：

```ts
if (interceptedConfig.auth) {
  const token = this.getToken()
  if (token) {
    requestOptions.header!['Authorization'] = `Bearer ${token}`
  }
}
```

- 对于 `auth: true`（默认） 的接口，都会自动在 Header 中加上 `Authorization: Bearer <token>`。
- 后端通过该 Header 解析 Token，完成用户身份认证和权限校验。

---

## 七、Mock 数据流程（前端伪造后端响应）

### 7.1 Mock 配置入口

在 `src/utils/request.ts` 顶部：

```ts
import { mockConfig, findMockRule, mockDelay } from '@/mock'
```

### 7.2 Mock 处理逻辑

在 `request()` 方法中：

```ts
if (mockConfig.enabled) {
  const mockRule = findMockRule(finalConfig.url, finalConfig.method || 'GET')
  if (mockRule) {
    if (mockConfig.logRequests) {
      logger.info('system', `🎭 Mock Request: ${finalConfig.method} ${finalConfig.url}`)
    }

    if (finalConfig.loading) {
      this.showLoading(finalConfig.loadingText)
    }

    await mockDelay()

    const mockData = mockRule.handler(finalConfig.data)

    if (finalConfig.loading) {
      this.hideLoading()
    }

    if (mockConfig.logRequests) {
      logger.info('system', `✅ Mock Response:`, mockData)
    }

    return mockData as T
  }
}
```

- 当开启 Mock 且命中规则时：
  - 不再调用 `uni.request`；
  - 直接在前端根据规则生成“伪造的后端响应”；
  - 对上层来说依然是 `await request(...)`，使用方式不变。

---

## 八、小结（基础版）

1. **调用路径**：
   - 页面 / Store → `src/api/*.ts`（业务接口定义）
   - → `src/utils/request.ts` 中的 `request()`（统一封装）
   - → `uni.request` 发送到后端 URL
   - → 后端接口处理并返回 `ApiResponse<T>`
   - → 响应拦截器校验并解包数据
   - → 业务代码拿到最终的 `data` 进行渲染或状态更新。

2. **前后端契约**：
   - URL 路径、HTTP 方法、请求体结构、响应体结构（`ApiResponse<T>`）
   - Token 放在 `Authorization: Bearer <token>` 头中。

3. **前端统一处理能力**：
   - Loading、错误提示、日志记录、Mock、重试、Token 注入、统一错误抛出与数据解包等，都集中在 `request.ts` 中处理。

这部分是“基础版”总结，可以快速了解整体架构。下面的“进阶版”会用一个微信登录的故事，从代码角度一步一步走完整条链路。

---

## 进阶版：从点击登录按钮开始的一次完整调用链（新手向详细版）

这一部分用一个**具体例子**来讲：小程序里点击“微信登录”按钮，一直到后端，再返回数据，一步一步跟着代码走。

例子以 **微信登录（`wechatLogin`）** 为主，其它接口的流程是一样的，只是 URL 和参数不同。

### A. 页面点击按钮 → 调用 API 函数

假设在小程序的登录页面里，有这样一个按钮（示意代码）：

```vue
<button @tap="onWechatLogin">微信登录</button>
```

对应的脚本中有一个事件处理函数：

```ts
import { wechatLogin } from '@/api/auth'

const onWechatLogin = async () => {
  // 1. 先通过 uni.login / wx.login 拿到微信临时 code（示意）
  const code = await getWechatCodeSomehow()

  // 2. 调用我们封装好的 API 函数
  const loginResult = await wechatLogin({ code })

  // 3. 登录成功后，loginResult 里是后端返回的业务数据（如 token、用户信息）
  //    可以存到 store 或本地存储，然后跳转页面
}
```

这一层只关心“我要微信登录”，**不需要管 HTTP 请求的细节**（URL、请求头、Token、错误处理等都交给后面几层）。

---

### B. 进入 `src/api/auth.ts` 的 `wechatLogin`

在 `src/api/auth.ts` 中，定义了 `wechatLogin` 函数：

```ts
import { request } from '@/utils/request'
import type { WechatLoginRequest, LoginResponse } from '@/types/auth'
import type { ApiResponse } from '@/types/common'

export const wechatLogin = (data: WechatLoginRequest): Promise<ApiResponse<LoginResponse>> => {
  // 1. 根据不同平台选择不同的后端 URL
  let apiUrl = '/api/v1/auth/wechat-login'
  
  // #ifdef MP-WEIXIN
  apiUrl = '/api/v1/auth/mp-login'
  // #endif
  // #ifdef APP-PLUS
  apiUrl = '/api/v1/auth/wechat-login'
  // #endif
  // #ifdef H5
  apiUrl = '/api/v1/auth/wechat-h5-login'
  // #endif

  // 2. 调用统一的 request 封装
  return request({
    url: apiUrl,
    method: 'POST',
    data,
    auth: false,
    loading: true,
    loadingText: '微信登录中...'
  })
}
```

可以这样理解：

- `wechatLogin` 函数负责做一件事：**把“微信登录”这个业务，翻译成一个具体的 HTTP 请求配置**。
- 它会根据平台（小程序 / APP / H5）决定访问哪个后端 URL：
  - 小程序 → `/api/v1/auth/mp-login`
  - APP → `/api/v1/auth/wechat-login`
  - H5 → `/api/v1/auth/wechat-h5-login`
- 最后把这些信息（`url`、`method`、`data` 等）交给 `request({ ... })`，进入统一的网络层处理。

---

### C. 进入 `src/utils/request.ts` 的 `request(config)`

`request` 是一个统一的网络请求封装函数，位于 `src/utils/request.ts` 的 `Request` 类中：

```ts
async request<T = any>(config: RequestConfig): Promise<T> {
  // 1. 合并默认配置和调用方传入的配置
  const finalConfig: RequestConfig = {
    method: 'GET',
    timeout: this.timeout,
    loading: false,
    loadingText: '加载中...',
    showError: true,
    auth: true,
    retry: 0,
    ...config
  }

  // 2. 如果开启了 Mock，优先走 Mock
  // 3. 执行“请求拦截器”（主要做日志、公共处理）
  // 4. 拼出完整的 URL 和请求头
  // 5. （如需要）自动在 Header 中加上 Authorization: Bearer <token>
  // 6. （如需要）显示 loading 提示
  // 7. 调用 uni.request 真正发请求到后端
  // 8. 按 HTTP 状态码做一层错误判断
  // 9. 执行“响应拦截器”（检查业务 code，解包 data）
  // 10. 把最终的数据返回给调用方
}
```

下面把几个关键点再展开一点。

#### C.1 BaseURL 和完整 URL 是怎么拼出来的？

`Request` 类里有一个 `baseURL` 和两个相关方法：

```ts
private baseURL: string = ''

constructor() {
  this.setBaseURL()
}

private setBaseURL() {
  // #ifdef H5
  this.baseURL = process.env.NODE_ENV === 'development' 
    ? 'http://localhost:3000/api'
    : 'https://api.yourdomain.com'
  // #endif

  // #ifdef MP-WEIXIN
  this.baseURL = process.env.NODE_ENV === 'development'
    ? 'https://dev-api.yourdomain.com'
    : 'https://api.yourdomain.com'
  // #endif
}

private getFullURL(url: string): string {
  if (url.startsWith('http')) {
    return url
  }
  return `${this.baseURL}${url.startsWith('/') ? url : '/' + url}`
}
```

流程可以这样理解：

1. 创建 `Request` 实例时，构造函数会调用 `setBaseURL()`，根据“平台 + 开发/生产环境”为当前运行平台设置 `baseURL`。
2. 当你传进来的 `url` 是 `/api/v1/auth/mp-login` 这种相对路径时，`getFullURL` 会把它拼成完整的地址：
   - 小程序开发环境：`https://dev-api.yourdomain.com/api/v1/auth/mp-login`
   - 小程序生产环境：`https://api.yourdomain.com/api/v1/auth/mp-login`

#### C.2 什么时候会自动加上 Token？

```ts
if (interceptedConfig.auth) {
  const token = this.getToken()
  if (token) {
    requestOptions.header!['Authorization'] = `Bearer ${token}`
  }
}
```

- 如果在调用 `request` 时没有显式写 `auth: false`，默认会认为这是一个“需要登录权限”的接口。
- 这种情况下会从本地存储里取出 Token（`getToken()`），并自动在请求头里加上一行：
  - `Authorization: Bearer <token>`。
- 登录接口 `wechatLogin` 自己是 `auth: false`，所以不会加 Token；但“获取当前用户信息”等接口通常会走这段逻辑。

#### C.3 什么时候真正“发出网络请求”？

```ts
const response = await new Promise<UniApp.RequestSuccessCallbackResult>((resolve, reject) => {
  uni.request({
    ...requestOptions,
    success: resolve,
    fail: reject
  })
})
```

这一段代码可以理解为：

- 构造好了 `url`、`method`、`data`、`header` 等信息后，交给 `uni.request`；
- `uni.request` 会通过网络把请求发到后端服务器；
- 等待后端返回结果后，把结果通过 `resolve` 传出来，放在 `response` 这个变量里。

到这里为止，**数据已经从前端发到了后端，并且后端返回了一份响应**，下一步是前端如何解释这份响应。

---

### D. 后端返回什么？前端怎么解读？

#### D.1 后端返回的统一结构：`ApiResponse<T>`

后端推荐返回类似这样的 JSON（对应 `src/types/common.ts` 中的类型）：

```json
{
  "code": 200,
  "message": "OK",
  "data": {
    "accessToken": "...",
    "refreshToken": "...",
    "expiresIn": 3600,
    "userInfo": { "...": "..." }
  },
  "timestamp": "2025-12-05T07:00:00Z"
}
```

- `code`：业务状态码（200 表示成功）
- `message`：错误或提示信息
- `data`：真正的业务数据
- `timestamp`：时间戳

#### D.2 响应拦截器如何处理这份返回

在 `src/utils/request.ts` 里，定义了一个默认的响应拦截器：

```ts
requestInstance.addResponseInterceptor((response) => {
  const { data } = response
  
  if (data && typeof data === 'object' && 'code' in data) {
    const apiResponse = data as ApiResponse
    
    if (apiResponse.code !== 200) {
      throw new Error(apiResponse.message || '请求失败')
    }
    
    return { ...response, data: apiResponse.data }
  }

  return response
})
```

这段逻辑的意思是：

1. 如果 `response.data` 里有 `code` 字段，就把它当成后端的统一返回结构 `ApiResponse<T>`。
2. 如果 `code !== 200`，认为是业务错误，直接抛出一个错误，错误信息用 `message`。
3. 如果 `code === 200`，则把 `response.data` 替换成里面的 `data` 字段（只保留真正的业务数据）。

在 `request()` 函数的最后，有：

```ts
const interceptedResponse = await this.runResponseInterceptors(response)
...
return interceptedResponse.data
```

因此，**调用方最终拿到的就是“已经解包后的 data”**，而不是包含 `code`、`message` 的完整结构。

---

### E. 再回到页面：拿到结果，更新状态

回到最开始的页面代码：

```ts
const loginResult = await wechatLogin({ code })
```

在这行代码背后，实际发生了很多步骤：

1. 进入 `src/api/auth.ts` 的 `wechatLogin`，根据平台选定 URL，并调用 `request({ ... })`。
2. `request` 在 `src/utils/request.ts` 中：
   - 合并默认配置
   - 处理 Mock（如果开启）
   - 执行请求拦截器（打日志等）
   - 通过 `getFullURL` 拼出完整 URL
   - （如需要）自动附加 Token
   - （如需要）显示 loading
   - 调用 `uni.request` 把请求发到后端
   - 检查 HTTP 状态码是否正常
   - 执行响应拦截器，检查业务 `code`，并解包出 `data`
3. 最终 `loginResult` 拿到的就是 **后端返回结构里的 `data` 部分**（比如包含 `accessToken`、`userInfo` 等）。

之后页面或 Store 通常会：

- 把 `accessToken` 等信息保存到 Pinia store 和本地存储；
- 然后跳转到首页、个人中心等页面。

通过这个微信登录的例子，你可以类比所有其他 API：**起点在页面/Store，经过 `src/api` 映射到 URL，再经过 `src/utils/request.ts` 发到后端，然后再返回数据给页面。**

