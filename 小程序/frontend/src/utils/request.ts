import type { ApiResponse } from '@/types/common'
import { logger } from '@/logs/logger'
import { useAuthStore } from '@/store/auth'

export type HTTPMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH'

export interface RequestConfig {
  url: string
  baseURL?: string
  method?: HTTPMethod
  data?: any
  headers?: Record<string, string>
  timeout?: number
  loading?: boolean
  loadingText?: string
  showError?: boolean
  auth?: boolean
  /**
   * 静默失败：不弹 toast、不打 ERROR（预期内的 404 等，如已下架专家补头像）
   */
  quiet?: boolean
  /**
   * 允许的业务码：HTTP 4xx 但 body.code 命中时视为正常返回（不 throw、不弹错）。
   * 例：兼容旧后端 GET /experts/me 未绑定 → HTTP 404 + code 2004（权威契约改为 200 + data=null）
   */
  acceptCodes?: number[]
}

export interface UploadConfig {
  url: string
  filePath: string
  name?: string
  baseURL?: string
  formData?: Record<string, any>
  headers?: Record<string, string>
  timeout?: number
  loading?: boolean
  loadingText?: string
  showError?: boolean
  auth?: boolean
}

const DEFAULT_TIMEOUT = 10000

/**
 * 过滤对象中的 undefined/null 值，避免序列化为字符串 "undefined"/"null"
 * 🚨 这是一个常见的前端坑：当使用 { q: undefined } 时，uni.request 会将其序列化为 q=undefined
 * GET 查询再跳过空字符串，避免 brand_id= / status= 被后端当成过滤条件
 */
function cleanQueryParams(data: any, options?: { skipEmptyString?: boolean }): any {
  if (data === undefined || data === null) return undefined
  if (typeof data !== 'object' || data instanceof Date) return data
  if (Array.isArray(data)) return data.map((item) => cleanQueryParams(item, options))

  const skipEmptyString = options?.skipEmptyString === true
  const cleaned: Record<string, any> = {}
  for (const [key, value] of Object.entries(data)) {
    if (value === undefined || value === null) continue
    if (skipEmptyString && value === '') continue
    cleaned[key] = value
  }
  return Object.keys(cleaned).length > 0 ? cleaned : undefined
}

function sanitizeEnvURL(value: string | undefined | null): string {
  return String(value ?? '').trim().replace(/\/+$/, '')
}

function normalizeGatewayBaseURL(rawBaseURL: string): string {
  const trimmed = sanitizeEnvURL(rawBaseURL)
  return trimmed
}

/**
 * 获取 API 路径前缀（可通过环境变量配置）
 * - VITE_API_PATH_PREFIX="" → 不追加前缀（当前项目默认）
 * - 路径由 API_BASE_MAP 决定网关
 */
function getApiPathPrefix(): string {
  const prefix = import.meta.env?.VITE_API_PATH_PREFIX
  // 未定义时不追加前缀；由 env 和显式路径共同决定最终地址
  if (prefix === undefined || prefix === null) {
    return ''
  }
  return String(prefix).trim()
}

function normalizePathForGateway(url: string, normalizedBaseURL: string): string {
  const path = url.startsWith('/') ? url : '/' + url
  // 检查 baseURL 是否已经包含 /api/v1（兼容后端直连模式）
  const baseHasApiV1 = /\/api\/(core|users)\/api\/v1(?:\/|$)/.test(normalizedBaseURL)
  const normalizedPath = baseHasApiV1 ? path.replace(/^\/api\/v1(?=\/|$)/, '') || '/' : path
  const prefix = getApiPathPrefix()
  
  if (baseHasApiV1) {
    return normalizedPath
  }

  // 如果前缀为空，不追加
  if (!prefix) {
    return normalizedPath
  }
  
  // 避免重复添加前缀
  if (normalizedPath.startsWith(prefix + '/') || normalizedPath === prefix) {
    return normalizedPath
  }
  
  return `${prefix}${normalizedPath}`
}

function fixDuplicatePath(url: string): string {
  return url
    .replace(/\/api\/core\/api\/core/g, '/api/core')
    .replace(/\/api\/users\/api\/users/g, '/api/users')
    .replace(/\/api\/v1\/api\/v1/g, '/api/v1')
}

function joinURL(baseURL: string, path: string): string {
  const b = sanitizeEnvURL(baseURL)
  const p = path.startsWith('/') ? path : '/' + path
  return fixDuplicatePath(`${b}${p}`)
}

function shouldUseUsersGateway(path: string): boolean {
  // 提取路径部分（如果是完整URL，去掉协议和主机部分）
  let p = path

  // 处理完整URL：http://localhost:8080/api/users/me/notifications → /api/users/me/notifications
  if (p.startsWith('http://') || p.startsWith('https://')) {
    const protocolEnd = p.indexOf('://')
    if (protocolEnd !== -1) {
      const afterProtocol = p.slice(protocolEnd + 3)
      const pathStart = afterProtocol.indexOf('/')
      if (pathStart !== -1) {
        p = afterProtocol.slice(pathStart)
      }
    }
  }

  // 确保路径以 / 开头
  if (!p.startsWith('/')) {
    p = '/' + p
  }

  // 检查是否是用户相关的路径（支持完整路径和相对路径）
  return (
    p.startsWith('/auth') ||
    p === '/me' ||
    p.startsWith('/me/') ||
    p === '/register' ||
    p.startsWith('/admin/users') ||
    p.startsWith('/users/me') ||
    // 支持完整路径：/api/users/me/...
    p.startsWith('/api/users/me') ||
    p.startsWith('/api/users/auth')
  )
}

function getCurrentPath(): string {
  try {
    const pages = getCurrentPages()
    if (pages.length > 0) {
      const currentPage = pages[pages.length - 1]
      const route = (currentPage as any).route || (currentPage as any).__route__ || ''
      const options = (currentPage as any).options || {}
      const query = Object.keys(options)
        .map((key) => `${key}=${encodeURIComponent(options[key])}`)
        .join('&')
      return query ? `/${route}?${query}` : `/${route}`
    }
  } catch {}
  return '/pages/home/Home'
}

function getToken(): string | null {
  return (
    uni.getStorageSync('access_token') ||
    uni.getStorageSync('token') ||
    null
  )
}

function normalizeApiResponse<T>(data: any): ApiResponse<T> {
  if (data && typeof data === 'object' && 'code' in data) return data as ApiResponse<T>
  return {
    code: 200,
    message: 'success',
    data: data as T,
    timestamp: new Date().toISOString()
  }
}

/** 从响应体提取业务 code（兼容 uni 已解析 JSON / 字符串） */
function extractBusinessCode(payload: any): number | undefined {
  const data = payload?.data ?? payload
  const raw = typeof data === 'string'
    ? (() => {
        try {
          return JSON.parse(data)
        } catch {
          return null
        }
      })()
    : data
  const code = raw?.code
  return typeof code === 'number' ? code : undefined
}

/** 是否为调用方声明可接受的业务空态/业务结果 */
function isAcceptedBusinessResult(config: RequestConfig, payload: any): boolean {
  if (!config.acceptCodes?.length) return false
  const code = extractBusinessCode(payload)
  return typeof code === 'number' && config.acceptCodes.includes(code)
}

function extractErrorMessage(payload: any, statusCode?: number, errMsg?: string): string {
  const data = payload?.data ?? payload
  const bizCode = typeof data?.code === 'number' ? data.code : undefined

  // 内容安全（临时对接 2026-08-08）：422 + 2005/2004 原样展示后端中文审核文案
  if (bizCode === 2005) {
    const hint = typeof data?.message === 'string' ? data.message.trim() : ''
    if (hint && hint !== '[object Object]') return hint
    return '内容未通过审核，请修改后重试'
  }
  if (bizCode === 2004) {
    const hint = typeof data?.message === 'string' ? data.message.trim() : ''
    if (hint && hint !== '[object Object]') return hint
    return statusCode === 422 ? '审核服务暂不可用，请稍后再试' : '暂时无法提交，请稍后再试'
  }

  const candidates = [
    typeof data?.message === 'string' ? data.message : null,
    typeof data?.detail === 'string' ? data.detail : null,
    typeof data?.error === 'string' ? data.error : null
  ].filter(Boolean) as string[]

  if (candidates.length) {
    const text = candidates[0].trim()
    if (text && text !== '[object Object]') return text
  }

  // FastAPI / 校验类：detail 常为对象数组，不能 String() 成 [object Object]
  if (Array.isArray(data?.detail) || Array.isArray(data?.message)) {
    return '填写内容有误，请检查后再试'
  }
  if (data?.message && typeof data.message === 'object') {
    return '操作失败，请稍后再试'
  }
  if (data?.detail && typeof data.detail === 'object') {
    return '操作失败，请稍后再试'
  }

  if (statusCode === 401) return '未授权，请重新登录'
  if (statusCode === 403) return '拒绝访问'
  if (statusCode === 404) return '请求的资源不存在'
  if (statusCode === 408) return '请求超时'
  if (statusCode === 422) return '填写内容有误，请检查后再试'
  if (statusCode && statusCode >= 500) return '服务器内部错误'

  const msg = String(errMsg || '').toLowerCase()
  if (msg.includes('timeout')) return '请求超时'
  if (msg.includes('fail')) return '网络连接失败'

  return '网络请求失败'
}

class RequestClient {
  private loadingCount = 0
  private coreBaseURL: string
  private usersBaseURL: string

  constructor() {
    this.coreBaseURL = normalizeGatewayBaseURL(
      sanitizeEnvURL(import.meta.env?.VITE_BASE_API_URL) || 'http://localhost:8080/api/core'
    )
    this.usersBaseURL = normalizeGatewayBaseURL(
      sanitizeEnvURL(import.meta.env?.VITE_AUTH_API_URL) ||
        sanitizeEnvURL(import.meta.env?.VITE_USERS_API_URL) ||
        'http://localhost:8080/api/users'
    )
  }

  private showLoading(text: string) {
    this.loadingCount++
    if (this.loadingCount === 1) {
      uni.showLoading({ title: text || '加载中...', mask: true })
    }
  }

  private hideLoading() {
    if (this.loadingCount <= 0) return
    this.loadingCount--
    if (this.loadingCount === 0) {
      uni.hideLoading()
    }
  }

  private resolveBaseURL(url: string, overrideBaseURL?: string): string {
    if (overrideBaseURL) return normalizeGatewayBaseURL(overrideBaseURL)

    const isUsersGateway = shouldUseUsersGateway(url)
    const selectedBaseURL = isUsersGateway ? this.usersBaseURL : this.coreBaseURL

    // 【诊断日志】记录网关选择
    logger.debug('network', '[resolveBaseURL] 网关选择', {
      输入URL: url,
      是否用户网关: isUsersGateway
    })

    return selectedBaseURL
  }

  private resolveFullURL(url: string, overrideBaseURL?: string): string {
    if (url.startsWith('http://') || url.startsWith('https://')) {
      logger.debug('network', '[resolveFullURL] 已是完整URL', { url })
      return fixDuplicatePath(url)
    }

    const baseURL = this.resolveBaseURL(url, overrideBaseURL)
    const normalizedPath = normalizePathForGateway(url, baseURL)
    const fullURL = joinURL(baseURL, normalizedPath)

    // 【诊断日志】记录 URL 解析过程
    logger.debug('network', '[resolveFullURL] URL解析详情', {
      原始url: url,
      最终fullURL: fullURL
    })

    return fullURL
  }

  private handleError(error: any, config: RequestConfig): never {
    const statusCode = error?.statusCode
    const message = extractErrorMessage(error, statusCode, error?.errMsg)
    const quiet = config.quiet === true

    if (quiet) {
      logger.debug('network', 'Request failed (quiet)', {
        url: config.url,
        method: config.method,
        statusCode,
        message
      })
    } else {
      logger.error('network', 'Request failed', {
        url: config.url,
        method: config.method,
        statusCode,
        message
      })
    }

    // 401 未授权：清除登录态并跳转登录页
    if (statusCode === 401) {
      try {
        const authStore = useAuthStore()
        if (authStore.isLoggedIn) {
          authStore.clearAuth()
          uni.reLaunch({
            url: '/pages/auth/OneTapLogin?redirect=' + encodeURIComponent(getCurrentPath())
          })
        }
      } catch (e) {
        logger.error('network', '401 处理失败', e as any)
      }
    }

    // hideLoading 由 request() 的 finally 统一处理，这里不再重复调用
    // __handled：本请求已走过 handleError，防二次包装
    // __toastShown：仅当本层真正弹过 Toast；showError:false 时留给页面 handleContentSafetyError
    const didToast = !quiet && config.showError !== false
    if (didToast) {
      // 延迟弹 toast，避免与 hideLoading 原生过渡冲突导致 toast 被吞
      // 2005/2004：extractErrorMessage 已优先透传 body.message
      const toastTitle =
        typeof message === 'string' && message.trim() && message !== '[object Object]'
          ? message.trim()
          : '操作失败，请稍后再试'
      setTimeout(() => {
        uni.showToast({ title: toastTitle, icon: 'none', duration: 2000 })
      }, 200)
    }

    const err = new Error(message)
    ;(err as any).statusCode = statusCode
    ;(err as any).code = extractBusinessCode(error)
    ;(err as any).config = config
    ;(err as any).raw = error
    ;(err as any).__handled = true
    ;(err as any).__toastShown = didToast
    throw err
  }

  async request<T = any>(config: RequestConfig): Promise<T> {
    const finalConfig: RequestConfig = {
      method: 'GET',
      timeout: DEFAULT_TIMEOUT,
      loading: false,
      loadingText: '加载中...',
      showError: true,
      auth: true,
      ...config
    }

    if (finalConfig.loading) this.showLoading(finalConfig.loadingText || '加载中...')

    // 🚨 关键修复：过滤 data 中的 undefined/null 值，避免序列化为 "undefined"/"null" 字符串
    // GET 同时去掉空字符串，避免把「全部」筛选项当成 brand_id=/status= 强制过滤
    if (finalConfig.data && typeof finalConfig.data === 'object') {
      const isGet = String(finalConfig.method || 'GET').toUpperCase() === 'GET'
      finalConfig.data = cleanQueryParams(finalConfig.data, { skipEmptyString: isGet })
    }

    const fullURL = this.resolveFullURL(finalConfig.url, finalConfig.baseURL)

    // 【诊断日志】记录实际发出的请求
    const baseLog = {
      fullURL,
      method: finalConfig.method,
      hasAuth: finalConfig.auth !== false,
      hasToken: !!getToken(),
      dataKeys: finalConfig.data ? Object.keys(finalConfig.data) : [],
      dataPreview: JSON.stringify(finalConfig.data)?.slice(0, 300)
    }

    // 【留言特殊日志】记录留言相关请求的详细信息
    if (finalConfig.url.includes('/messages') && finalConfig.data?.content) {
      logger.info('live', '[留言] 发送留言请求详情', {
        url: finalConfig.url,
        roomId: finalConfig.url.match(/rooms\/([^/]+)/)?.[1],
        method: finalConfig.method,
        content: finalConfig.data.content,
        contentLength: finalConfig.data.content?.length || 0,
        sessionId: finalConfig.data.session_id || null,
        timestamp: new Date().toISOString()
      })
    } else if (finalConfig.url.includes('/messages') && finalConfig.method === 'GET') {
      logger.info('live', '[留言] 获取留言列表请求', {
        url: finalConfig.url,
        roomId: finalConfig.url.match(/rooms\/([^/]+)/)?.[1],
        method: finalConfig.method,
        queryParams: finalConfig.data,
        timestamp: new Date().toISOString()
      })
    }

    logger.info('network', '[request] 发出请求', baseLog)

    const header: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(finalConfig.headers || {})
    }

    if (finalConfig.auth !== false) {
      const token = getToken()
      if (token) header.Authorization = `Bearer ${token}`
    }

    try {
      const response = await new Promise<UniApp.RequestSuccessCallbackResult>((resolve, reject) => {
        uni.request({
          url: fullURL,
          method: finalConfig.method as any,
          data: finalConfig.data,
          timeout: finalConfig.timeout,
          header,
          success: resolve,
          fail: reject
        })
      })

      // 【诊断日志】记录响应概要
      logger.info('network', '[request] 收到响应', {
        fullURL,
        statusCode: response.statusCode,
        dataType: typeof response.data,
        dataPreview: JSON.stringify(response.data)?.slice(0, 500)
      })

      // 业务空态（如未绑定专家）：HTTP 4xx + acceptCodes，正常返回
      if (response.statusCode >= 400 && isAcceptedBusinessResult(finalConfig, response.data)) {
        const normalizedAccepted = normalizeApiResponse<any>(response.data)
        logger.info('network', '[request] 业务空态（已接受）', {
          fullURL,
          statusCode: response.statusCode,
          code: normalizedAccepted?.code,
          message: normalizedAccepted?.message
        })
        return normalizedAccepted as T
      }

      // 【留言特殊日志】分页 GET 为 { items, total }；单条 POST 为留言对象
      if (finalConfig.url.includes('/messages') && response.statusCode === 200) {
        const responseData = response.data as any
        const msgData = responseData?.data
        if (msgData && Array.isArray(msgData.items)) {
          logger.info('live', '[留言] 获取留言列表响应成功', {
            url: finalConfig.url,
            roomId: finalConfig.url.match(/rooms\/([^/]+)/)?.[1],
            messageCount: msgData.items.length,
            total: msgData.total ?? msgData.items.length,
            timestamp: new Date().toISOString()
          })
        } else if (msgData && Array.isArray(msgData)) {
          logger.info('live', '[留言] 获取留言列表响应成功', {
            url: finalConfig.url,
            roomId: finalConfig.url.match(/rooms\/([^/]+)/)?.[1],
            messageCount: msgData.length,
            timestamp: new Date().toISOString()
          })
        } else if (msgData && typeof msgData === 'object' && msgData.id && msgData.content != null) {
          logger.info('live', '[留言] 发送留言响应成功', {
            url: finalConfig.url,
            roomId: finalConfig.url.match(/rooms\/([^/]+)/)?.[1],
            messageId: msgData.id,
            contentLength: String(msgData.content || '').length,
            responseCode: responseData.code,
            timestamp: new Date().toISOString()
          })
        }
      }

      if (response.statusCode >= 400) {
        return this.handleError({ statusCode: response.statusCode, data: response.data }, finalConfig)
      }

      const normalized = normalizeApiResponse<any>(response.data)
      if (typeof normalized?.code === 'number' && normalized.code !== 200) {
        if (isAcceptedBusinessResult(finalConfig, normalized)) {
          return normalized as T
        }
        return this.handleError({ statusCode: response.statusCode, data: normalized }, finalConfig)
      }

      return normalized as T
    } catch (error: any) {
      if (error?.__handled) throw error
      return this.handleError(error, finalConfig)
    } finally {
      if (finalConfig.loading) {
        this.hideLoading()
        // 等待原生 hideLoading 过渡完成，避免后续 showToast（如"已收藏"）被吞
        await new Promise(r => setTimeout(r, 200))
      }
    }
  }

  get<T = any>(url: string, config?: Omit<RequestConfig, 'url' | 'method'>): Promise<T> {
    return this.request<T>({ ...config, url, method: 'GET' })
  }

  post<T = any>(url: string, data?: any, config?: Omit<RequestConfig, 'url' | 'method' | 'data'>): Promise<T> {
    return this.request<T>({ ...config, url, method: 'POST', data })
  }

  put<T = any>(url: string, data?: any, config?: Omit<RequestConfig, 'url' | 'method' | 'data'>): Promise<T> {
    return this.request<T>({ ...config, url, method: 'PUT', data })
  }

  patch<T = any>(url: string, data?: any, config?: Omit<RequestConfig, 'url' | 'method' | 'data'>): Promise<T> {
    return this.request<T>({ ...config, url, method: 'PATCH', data })
  }

  delete<T = any>(url: string, config?: Omit<RequestConfig, 'url' | 'method'>): Promise<T> {
    return this.request<T>({ ...config, url, method: 'DELETE' })
  }

  async upload<T = any>(config: UploadConfig): Promise<ApiResponse<T>> {
    const finalConfig: UploadConfig = {
      name: 'file',
      timeout: DEFAULT_TIMEOUT,
      loading: false,
      loadingText: '上传中...',
      showError: true,
      auth: true,
      ...config
    }

    if (finalConfig.loading) this.showLoading(finalConfig.loadingText || '上传中...')

    const fullURL = this.resolveFullURL(finalConfig.url, finalConfig.baseURL)
    const header: Record<string, string> = { ...(finalConfig.headers || {}) }
    if (finalConfig.auth !== false) {
      const token = getToken()
      if (token) header.Authorization = `Bearer ${token}`
    }

    try {
      const response = await new Promise<UniApp.UploadFileSuccessCallbackResult>((resolve, reject) => {
        uni.uploadFile({
          url: fullURL,
          filePath: finalConfig.filePath,
          name: finalConfig.name || 'file',
          formData: finalConfig.formData,
          header,
          timeout: finalConfig.timeout,
          success: resolve,
          fail: reject
        })
      })

      const raw = (response as any).data
      let parsed: any = raw
      if (typeof raw === 'string') {
        try {
          parsed = JSON.parse(raw)
        } catch {
          parsed = raw
        }
      }

      const normalized = normalizeApiResponse<T>(parsed)
      if (typeof normalized?.code === 'number' && normalized.code !== 200) {
        return this.handleError({ statusCode: (response as any).statusCode, data: normalized }, {
          url: finalConfig.url,
          method: 'POST',
          showError: finalConfig.showError,
          loading: false,
          auth: finalConfig.auth
        })
      }

      return normalized
    } catch (error: any) {
      if (error?.__handled) throw error
      return this.handleError(error, {
        url: finalConfig.url,
        method: 'POST',
        showError: finalConfig.showError,
        loading: false,
        auth: finalConfig.auth
      })
    } finally {
      if (finalConfig.loading) this.hideLoading()
    }
  }

  showGlobalLoading(text: string): void {
    this.showLoading(text)
  }

  hideGlobalLoading(): void {
    this.hideLoading()
  }
}

export const requestInstance = new RequestClient()

export type RequestFn = (<T = any>(config: RequestConfig) => Promise<T>) & {
  get: typeof requestInstance.get
  post: typeof requestInstance.post
  put: typeof requestInstance.put
  patch: typeof requestInstance.patch
  delete: typeof requestInstance.delete
  upload: typeof requestInstance.upload
}

export const request = (async <T = any>(config: RequestConfig) => requestInstance.request<T>(config)) as RequestFn
request.get = requestInstance.get.bind(requestInstance)
request.post = requestInstance.post.bind(requestInstance)
request.put = requestInstance.put.bind(requestInstance)
request.patch = requestInstance.patch.bind(requestInstance)
request.delete = requestInstance.delete.bind(requestInstance)
request.upload = requestInstance.upload.bind(requestInstance)

export const get = request.get
export const post = request.post
export const put = request.put
export const patch = request.patch
export const del = request.delete

export const showGlobalLoading = (text: string) => requestInstance.showGlobalLoading(text)
export const hideGlobalLoading = () => requestInstance.hideGlobalLoading()

export function upload(config: UploadConfig): Promise<ApiResponse<any>>
export function upload(
  url: string,
  filePath: string,
  options?: Omit<UploadConfig, 'url' | 'filePath'>
): Promise<ApiResponse<any>>
export function upload(
  urlOrConfig: string | UploadConfig,
  filePath?: string,
  options?: Omit<UploadConfig, 'url' | 'filePath'>
): Promise<ApiResponse<any>> {
  if (typeof urlOrConfig === 'string') {
    return request.upload({
      url: urlOrConfig,
      filePath: String(filePath || ''),
      ...(options || {})
    })
  }
  return request.upload(urlOrConfig)
}

export default request
