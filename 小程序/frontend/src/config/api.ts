/**
 * 统一API配置 - 根据标准答案重构
 * 严格按照后端API设计规范
 */

// 统一API路径定义（先保留相对路径，文件尾统一转换为绝对网关地址）
const RAW_API_PATHS = {
  // ===== 一、认证相关 API (users服务) =====
  AUTH: {
    CAPTCHA: '/auth/captcha',
    LOGIN: '/auth/login',
    REFRESH: '/auth/refresh',
    LOGOUT: '/auth/logout',
    SSO_LOGIN: '/auth/sso-login',
    PASSWORD_RESET_REQUEST: '/auth/password-reset-request',
    PASSWORD_RESET: '/auth/password-reset',
    VERIFICATION_CODES: '/auth/verification-codes',
    VERIFICATION_CODES_VERIFY: '/auth/verification-codes/verify',
    LOGIN_PHONE: '/auth/login/phone',
    LOGIN_EMAIL: '/auth/login/email',
    ONE_TAP_LOGIN: '/auth/one-tap-login',
    ONE_TAP_LOGIN_CF: '/auth/one-tap-login/cloud-function',
    CAPTCHA_IMAGE: (id: string) => `/auth/captcha/image/${id}`
  },

  // ===== 用户相关接口 (users服务) =====
  USER: {
    REGISTER: '/register',
    REGISTER_PHONE: '/register/phone',
    ME: '/me',
    PHONE: '/me/phone',
    EMAIL: '/me/email',
    DELETE: '/me',
    PASSWORD: '/me/password',
    UPDATE: '/me',
    AVATAR: '/me/avatar',
    SETTINGS: '/me/settings',
    NOTIFICATION_SETTINGS: '/me/notification-settings'
  },

  // ===== 用户偏好设置 (core服务, 独立路由: /api/v1/users/me/preferences → core_api) =====
  USER_PREFERENCES: {
    GET: '/users/me/preferences',
    UPDATE: '/users/me/preferences'
  },

  // ===== 品牌模块 (core服务) =====
  BRAND: {
    LIST: '/brands',
    CONTENT: (brandId: string) => `/brands/${brandId}/content`,
    ROOM_BRANDS: (roomId: string) => `/rooms/${roomId}/brands`,
    ADMIN_LIST: '/admin/brands',
    ADMIN_DETAIL: (brandId: string) => `/admin/brands/${brandId}`,
    ADMIN_LOGO: (brandId: string) => `/admin/brands/${brandId}/logo`,
    ADMIN_ROOMS: (brandId: string) => `/admin/brands/${brandId}/rooms`,
    ADMIN_TOPICS: (brandId: string) => `/admin/brands/${brandId}/topics`,
    ADMIN_TOPIC_DETAIL: (brandId: string, topicId: string) => `/admin/brands/${brandId}/topics/${topicId}`
  },

  // ===== 分类模块 (core服务) =====
  // 后端设计文档: 公开 /api/v1/content/categories, 管理端 /api/v1/admin/categories
  CATEGORY: {
    LIST: '/content/categories',
    ADMIN_LIST: '/admin/categories',
    ADMIN_DETAIL: (categoryId: string) => `/admin/categories/${categoryId}`,
    ADMIN_MIGRATE: (categoryId: string) => `/admin/categories/${categoryId}/migrate`,
    ADMIN_MERGE: '/admin/categories/merge',
    ICON: (categoryId: string) => `/admin/categories/${categoryId}/icon`,
    // 直播间-分类关联（后端设计文档: 公开 /api/v1/rooms/{roomId}/categories, 管理端 /api/v1/admin/rooms/{roomId}/categories）
    ROOM_CATEGORIES: (roomId: string) => `/rooms/${roomId}/categories`,
    ADMIN_SET_ROOM_CATEGORIES: (roomId: string) => `/admin/rooms/${roomId}/categories`,
    ADMIN_REMOVE_ROOM_CATEGORY: (roomId: string, categoryId: string) => `/admin/rooms/${roomId}/categories/${categoryId}`
  },

  // ===== 专家科室受控词表 (core服务,《20》后端) =====
  EXPERT_DEPARTMENT: {
    ADMIN_LIST: '/admin/expert-departments',
    ADMIN_CREATE: '/admin/expert-departments',
    ADMIN_DETAIL: (id: string) => `/admin/expert-departments/${id}`,
    ADMIN_UPDATE: (id: string) => `/admin/expert-departments/${id}`,
    ADMIN_DELETE: (id: string) => `/admin/expert-departments/${id}`,
    ADMIN_UNMAPPED: '/admin/expert-departments/unmapped',
    ADMIN_MERGE: '/admin/expert-departments/merge',
    ADMIN_CATEGORY: (id: string) => `/admin/expert-departments/${id}/category`,
    ADMIN_BATCH_VERIFY: '/admin/expert-departments/batch-verify'
  },

  // 标签管理 (core服务, 公开读 /api/v1/content/tags, 管理端写 /api/v1/admin/tags)
  TAGS: {
    LIST: '/content/tags',
    DETAIL: (tagId: string) => `/content/tags/${tagId}`,
    /** 《02-V2》§3.4 / 前端 v2.0 §9.2：用户侧解析或创建 */
    RESOLVE: '/content/tags/resolve',
    SEARCH_SESSIONS: '/content/tags/search/sessions',
    ADMIN_LIST: '/admin/tags',
    CREATE: '/admin/tags',
    UPDATE: (tagId: string) => `/admin/tags/${tagId}`,
    DELETE: (tagId: string) => `/admin/tags/${tagId}`
  },

  // 观看记录（core服务端点，用户端点在 WATCH_HISTORY 中）
  HISTORY: {
    RECORD_WATCH: (sessionId: string) => `/sessions/${sessionId}/watch`
  },

  // 设置管理（仅core服务端点，用户端点在 USER 模块中）
  SETTINGS: {
    SYSTEM_CONFIG: '/system/config'
  },

  // ===== 二、核心业务 API (core服务) =====

  // 房间管理
  ROOM: {
    LIST: '/rooms',
    DETAIL: (roomId: string) => `/rooms/${roomId}`,
    CREATE: '/rooms',
    UPDATE: (roomId: string) => `/rooms/${roomId}`,
    DELETE: (roomId: string) => `/rooms/${roomId}`,
    SUB_VENUES: (roomId: string) => `/rooms/${roomId}/sub-venues`,
    SESSIONS: (roomId: string) => `/rooms/${roomId}/sessions`,
    COVER: (roomId: string) => `/rooms/${roomId}/cover`,
    BRANDS: (roomId: string) => `/rooms/${roomId}/brands`,
    EXPERTS: (roomId: string) => `/rooms/${roomId}/experts`,
    TOPICS: (roomId: string) => `/rooms/${roomId}/topics`,
    IS_FAVORITED: (roomId: string) => `/rooms/${roomId}/is-favorited`,
    MESSAGES: (roomId: string) => `/rooms/${roomId}/messages`,
    TABS: (roomId: string) => `/rooms/${roomId}/tabs`,
    BATCH_STATUS: '/rooms/batch-status',
    IMPORT_BATCH: '/import/sessions',
    /** 文档 18：为正式间确保测播间（幂等）POST /rooms/{id}/test-room */
    TEST_ROOM: (roomId: string) => `/rooms/${roomId}/test-room`,
  },

  // 场次管理
  // 说明：Live Core 当前将单场次 CRUD 挂在 /sessions/sessions/{id}
  //（OpenAPI: GET/PATCH/DELETE），与设计文档的 /sessions/{id} 不一致；
  // 走文档路径会得到 FastAPI 404 {"detail":"Not Found"}。
  SESSION: {
    LIST: '/sessions',
    DETAIL: (sessionId: string) => `/sessions/sessions/${sessionId}`,
    CREATE: (roomId: string) => `/rooms/${roomId}/sessions`,
    UPDATE: (sessionId: string) => `/sessions/sessions/${sessionId}`,
    DELETE: (sessionId: string) => `/sessions/sessions/${sessionId}`,
    IMPORT: (roomId: string) => `/rooms/${roomId}/sessions/import`,
    VIEWERS: (sessionId: string) => `/sessions/${sessionId}/viewers`,
    STREAM_URL: (sessionId: string) => `/sessions/${sessionId}/stream-url`,
    TAGS: (sessionId: string) => `/content/sessions/${sessionId}/tags`,
    SEARCH: '/sessions/search',
    STATISTICS: (sessionId: string) => `/sessions/${sessionId}/statistics`,
    START: (sessionId: string) => `/sessions/${sessionId}/start`,
    END: (sessionId: string) => `/sessions/${sessionId}/end`,
    WATCH: (sessionId: string) => `/sessions/${sessionId}/watch`
  },

  // 专家管理
  EXPERT: {
    LIST: '/experts',
    /** @deprecated V2.2 已裁剪：专家认领 /experts/me* 后端已删除，勿再调用 */
    ME: '/experts/me',
    /** @deprecated V2.2 已裁剪 */
    ME_AVATAR: '/experts/me/avatar',
    FEATURED: '/featured-experts',
    DETAIL: (expertId: string) => `/experts/${expertId}`,
    SESSIONS: (expertId: string) => `/experts/${expertId}/sessions`,
    CONTENT: (expertId: string) => `/professors/${expertId}/content`,
    SESSION_EXPERTS: (sessionId: string) => `/experts/sessions/${sessionId}/experts`,
    SET_SESSION_EXPERTS: (sessionId: string) => `/experts/sessions/${sessionId}/experts`,
    IS_FOLLOWED: (expertId: string) => `/experts/${expertId}/is-followed`
  },

  // 用户行为 - 专家关注 (core服务)
  // 独立路由: /api/v1/users/me/followed-experts → core_api
  USER_EXPERT_FOLLOW: {
    FOLLOW_EXPERT: '/users/me/followed-experts',
    UNFOLLOW_EXPERT: (expertId: string) => `/users/me/followed-experts/${expertId}`,
    FOLLOWED_EXPERTS: '/users/me/followed-experts'
  },

  // 用户行为 - 我的直播间 (core服务)
  // 独立路由: /api/v1/users/me/rooms → core_api
  USER_ROOMS: {
    MY_ROOMS: '/users/me/rooms'
  },

  // 收藏 (core服务)
  FAVORITE: {
    LIST: '/users/me/favorites',
    ADD: '/users/me/favorites',
    REMOVE: (roomId: string) => `/users/me/favorites/${roomId}`
  },

  // 订阅 (core服务)
  SUBSCRIPTION: {
    LIST: '/users/me/subscriptions',
    ADD: '/users/me/subscriptions',
    REMOVE: (roomId: string) => `/users/me/subscriptions?target_type=room&target_id=${encodeURIComponent(roomId)}`,
    CHECK: (targetId: string) => `/users/me/subscriptions/check/${targetId}`,
    CLEAR_HISTORY: '/users/me/subscriptions/clear-history'
  },

  // 观看历史 (core服务)
  WATCH_HISTORY: {
    LIST: '/users/me/watch-history',
    DELETE: (historyId: string) => `/users/me/watch-history/${historyId}`,
    RECORD: '/users/me/watch-history',
    CLEAR: '/users/me/watch-history/clear'
  },

  // 内容管理
  CONTENT: {
    CATEGORIES: '/content/categories',
    CATEGORY_DETAIL: (categoryId: string) => `/content/categories/${categoryId}`,
    CATEGORY_CONTENT: (categoryId: string) => `/content/categories/${categoryId}/content`,
    FEATURED_CONTENT: '/featured-content',
    BRANDS: '/brands',
    BRAND_DETAIL: (brandId: string) => `/brands/${brandId}`,
    BRAND_CONTENT: (brandId: string) => `/brands/${brandId}/content`,
    TAGS: '/tags',
    TAG_DETAIL: (tagId: string) => `/tags/${tagId}`,
    TAG_CONTENT: (tagId: string) => `/tags/${tagId}/content`
  },

  // 专题管理
  TOPIC: {
    LIST: '/topics',
    DETAIL: (topicId: string) => `/topics/${topicId}`,
    CREATE: '/topics',
    UPDATE: (topicId: string) => `/topics/${topicId}`,
    DELETE: (topicId: string) => `/topics/${topicId}`,
    CATEGORIES: (topicId: string) => `/topics/${topicId}/categories`,
    CREATE_CATEGORY: (topicId: string) => `/topics/${topicId}/categories`,
    UPDATE_CATEGORY: (categoryId: string) => `/topic-categories/${categoryId}`,
    DELETE_CATEGORY: (categoryId: string) => `/topic-categories/${categoryId}`,
    CATEGORY_ROOMS: (categoryId: string) => `/topic-categories/${categoryId}/rooms`,
    ADD_ROOM_TO_CATEGORY: (categoryId: string) => `/topic-categories/${categoryId}/rooms`,
    SORT_ROOMS: (categoryId: string) => `/topic-categories/${categoryId}/rooms/sort-order`,
    REMOVE_ROOM_FROM_CATEGORY: (categoryId: string) => `/topic-categories/${categoryId}/rooms`
  },

  // 其他功能
  OTHER: {
    HOMEPAGE_ROOMS: '/homepage/rooms',
    ROOMS_SEARCH: '/rooms',
    SEARCH: '/search',
    PLAYBACK_STATS: '/playback/stats'
  },

  // ===== 三、通知模块 (core服务, 独立路由: /api/v1/users/me/notifications → core_api) =====
  NOTIFICATION: {
    LIST: '/users/me/notifications',
    DETAIL: (id: string) => `/users/me/notifications/${id}`,
    MARK_READ: (id: string) => `/users/me/notifications/${id}/read`,
    UNREAD_COUNT: '/users/me/notifications/unread-count'
  },

  // ===== 管理员接口 (core服务) =====
  ADMIN: {
    // 专家管理
    EXPERTS: '/admin/experts',
    CREATE_EXPERT: '/admin/experts',
    UPDATE_EXPERT: (expertId: string) => `/admin/experts/${expertId}`,
    DELETE_EXPERT: (expertId: string) => `/admin/experts/${expertId}`,
    /** 管理端上传专家头像 POST multipart file */
    EXPERT_AVATAR: (expertId: string) => `/admin/experts/${expertId}/avatar`,
    // 分类管理 (后端设计文档: /api/v1/admin/categories)
    CATEGORIES: '/admin/categories',
    CREATE_CATEGORY: '/admin/categories',
    UPDATE_CATEGORY: (categoryId: string) => `/admin/categories/${categoryId}`,
    DELETE_CATEGORY: (categoryId: string) => `/admin/categories/${categoryId}`,

    // 焦点图管理 (路径以后端设计文档为准: /api/v1/admin/featured-content)
    FEATURED_CONTENT: '/admin/featured-content',
    CREATE_FEATURED: '/admin/featured-content',
    UPDATE_FEATURED: (contentId: string) => `/admin/featured-content/${contentId}`,
    DELETE_FEATURED: (contentId: string) => `/admin/featured-content/${contentId}`,
    UPLOAD_FEATURED_IMAGE: (contentId: string) => `/admin/featured-content/${contentId}/image`,

    // 品牌管理
    BRANDS: '/admin/brands',
    CREATE_BRAND: '/admin/brands',
    UPDATE_BRAND: (brandId: string) => `/admin/brands/${brandId}`,
    DELETE_BRAND: (brandId: string) => `/admin/brands/${brandId}`,
    /** 管理端上传品牌 Logo POST multipart file */
    BRAND_LOGO: (brandId: string) => `/admin/brands/${brandId}/logo`,
    BIND_ROOM_BRAND: (roomId: string) => `/admin/rooms/${roomId}/brands`,
    BRAND_TOPICS: (brandId: string) => `/admin/brands/${brandId}/topics`,
    BIND_BRAND_TOPICS: (brandId: string) => `/admin/brands/${brandId}/topics`,
    UNBIND_BRAND_TOPIC: (brandId: string, topicId: string) => `/admin/brands/${brandId}/topics/${topicId}`,

    // 标签管理 (路径以后端设计文档为准: /api/v1/content/tags)
    // 注: 标签CRUD已移至 TAGS 模块，此处保留场次标签关联
    SESSION_TAGS: (sessionId: string) => `/content/sessions/${sessionId}/tags`,
    DELETE_SESSION_TAG: (sessionId: string, tagId: string) => `/content/sessions/${sessionId}/tags/${tagId}`,

    // 管理端全站房间列表（17 P0：GET /api/v1/admin/rooms）
    ROOMS: '/admin/rooms',

    // Tab管理 (路径以后端设计文档为准: /api/v1/admin/rooms/{roomId}/tabs)
    ROOM_TABS: (roomId: string) => `/admin/rooms/${roomId}/tabs`,
    CREATE_TAB: (roomId: string) => `/admin/rooms/${roomId}/tabs`,
    UPDATE_TAB: (tabId: string) => `/admin/tabs/${tabId}`,
    DELETE_TAB: (tabId: string) => `/admin/tabs/${tabId}`,
    UPLOAD_TAB_IMAGE: (roomId: string) => `/admin/rooms/${roomId}/tabs/image`,
    SORT_TABS: (roomId: string) => `/admin/rooms/${roomId}/tabs/sort`,

    // 通知管理
    NOTIFICATIONS: '/admin/notifications',
    CREATE_NOTIFICATION: '/admin/notifications',
    NOTIFICATION_DETAIL: (id: string) => `/admin/notifications/${id}`,
    UPDATE_NOTIFICATION: (id: string) => `/admin/notifications/${id}`,
    DELETE_NOTIFICATION: (id: string) => `/admin/notifications/${id}`,
    BATCH_DELETE_NOTIFICATIONS: '/admin/notifications/batch-delete'
  },

  // ===== 管理端用户管理 (users服务, 网关: /api/users/admin/*) =====
  ADMIN_USER: {
    USERS: '/admin/users',
    USER_DETAIL: (userUuid: string) => `/admin/users/${userUuid}`
  },

  // ===== 留言管理 (core服务, 《07-直播间留言-后端设计文档.md》V1.1: 用户端3 + 管理端3) =====
  MESSAGE: {
    ROOM_MESSAGES: (roomId: string) => `/rooms/${roomId}/messages`,
    MESSAGE_DETAIL: (roomId: string, messageId: string) => `/rooms/${roomId}/messages/${messageId}`,
    ADMIN_LIST: '/admin/messages',
    ADMIN_BATCH_DELETE: '/admin/messages/batch-delete',
    ADMIN_CLEAR_ROOM: (roomId: string) => `/admin/rooms/${roomId}/messages`
  },

  // ===== 内容安全管理 (core服务) =====
  CONTENT_SAFETY: {
    RULES: '/admin/content-safety/rules',
    RULE: (ruleId: string) => `/admin/content-safety/rules/${ruleId}`,
    LOGS: '/admin/content-safety/logs'
  },

  // ===== 媒体下载服务 (独立微服务, port 8001) =====
  DOWNLOAD: {
    // 任务管理
    TASKS: '/download/tasks',
    TASK_DETAIL: (taskId: string) => `/download/tasks/${taskId}`,
    TASK_START: (taskId: string) => `/download/tasks/${taskId}/start`,
    TASK_RETRY: (taskId: string) => `/download/tasks/${taskId}/retry`,
    TASK_FAILURES: (taskId: string) => `/download/tasks/${taskId}/failures`,
    TASK_VIDEOS: (taskId: string) => `/download/tasks/${taskId}/videos`,
    FAILURE_RETRY: (taskId: string, failureId: string) => `/download/tasks/${taskId}/failures/${failureId}/retry`,
    FAILURE_ABANDON: (taskId: string, failureId: string) => `/download/tasks/${taskId}/failures/${failureId}/abandon`,
    // 视频库
    VIDEOS: '/download/videos',
    VIDEO_DETAIL: (videoId: string) => `/download/videos/${videoId}`,
    // 批量导入
    BATCH_IMPORT: '/download/tasks/batch-import',
    CRAWL_IMPORT: '/download/tasks/crawl-and-import',
    CRAWL_STATUS: '/download/tasks/crawl-import-status'
  }
}

type ApiBaseType = 'core' | 'users'

const DEFAULT_CORE_API_BASE_URL = 'http://localhost:8080/api/core'
const DEFAULT_USERS_API_BASE_URL = 'http://localhost:8080/api/users'

function resolveGatewayBaseURL(rawBaseURL: string | undefined | null, fallbackBaseURL: string): string {
  const trimmed = String(rawBaseURL ?? '').trim().replace(/\/+$/, '') || fallbackBaseURL
  return trimmed
}

function buildAbsoluteApiPath(baseURL: string, path: string): string {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  const normalizedBase = baseURL.replace(/\/+$/, '')
  const baseHasApiV1 = /\/api\/(core|users)\/api\/v1$/.test(normalizedBase)

  if (baseHasApiV1 && normalizedPath.startsWith('/api/v1')) {
    const strippedPath = normalizedPath.slice('/api/v1'.length) || '/'
    return `${normalizedBase}${strippedPath}`
  }

  return `${normalizedBase}${normalizedPath}`
}

function transformApiNode<T>(node: T, baseURL: string): T {
  if (typeof node === 'string') {
    return buildAbsoluteApiPath(baseURL, node) as T
  }

  if (typeof node === 'function') {
    return ((...args: any[]) => transformApiNode((node as any)(...args), baseURL)) as T
  }

  if (node && typeof node === 'object') {
    const entries = Object.entries(node as Record<string, any>).map(([key, value]) => [
      key,
      transformApiNode(value, baseURL)
    ])
    return Object.fromEntries(entries) as T
  }

  return node
}

const CORE_API_BASE_URL = resolveGatewayBaseURL(
  import.meta.env?.VITE_BASE_API_URL,
  DEFAULT_CORE_API_BASE_URL
)

const USERS_API_BASE_URL = resolveGatewayBaseURL(
  import.meta.env?.VITE_AUTH_API_URL || import.meta.env?.VITE_USERS_API_URL,
  DEFAULT_USERS_API_BASE_URL
)

const API_BASE_MAP: Record<string, { baseType: ApiBaseType; baseURL: string }> = {
  AUTH: { baseType: 'users', baseURL: USERS_API_BASE_URL },
  USER: { baseType: 'users', baseURL: USERS_API_BASE_URL },
  HISTORY: { baseType: 'core', baseURL: CORE_API_BASE_URL },
  SETTINGS: { baseType: 'core', baseURL: CORE_API_BASE_URL },
  // 专家关注 - core服务 (独立路由: /api/v1/users/me/followed-experts → core_api)
  USER_EXPERT_FOLLOW: { baseType: 'core', baseURL: CORE_API_BASE_URL },
  // 我的直播间 - core服务 (独立路由: /api/v1/users/me/rooms → core_api)
  USER_ROOMS: { baseType: 'core', baseURL: CORE_API_BASE_URL },
  // 用户偏好设置 - core服务 (独立路由: /api/v1/users/me/preferences → core_api)
  USER_PREFERENCES: { baseType: 'core', baseURL: CORE_API_BASE_URL },
  // 收藏 - core服务
  FAVORITE: { baseType: 'core', baseURL: CORE_API_BASE_URL },
  // 观看历史 - core服务
  WATCH_HISTORY: { baseType: 'core', baseURL: CORE_API_BASE_URL },
  // 订阅 - core服务
  SUBSCRIPTION: { baseType: 'core', baseURL: CORE_API_BASE_URL },
  // 通知 - core服务 (独立路由: /api/v1/users/me/notifications → core_api)
  NOTIFICATION: { baseType: 'core', baseURL: CORE_API_BASE_URL },
  BRAND: { baseType: 'core', baseURL: CORE_API_BASE_URL },
  CATEGORY: { baseType: 'core', baseURL: CORE_API_BASE_URL },
  EXPERT_DEPARTMENT: { baseType: 'core', baseURL: CORE_API_BASE_URL },
  TAGS: { baseType: 'core', baseURL: CORE_API_BASE_URL },
  ROOM: { baseType: 'core', baseURL: CORE_API_BASE_URL },
  SESSION: { baseType: 'core', baseURL: CORE_API_BASE_URL },
  EXPERT: { baseType: 'core', baseURL: CORE_API_BASE_URL },
  CONTENT: { baseType: 'core', baseURL: CORE_API_BASE_URL },
  TOPIC: { baseType: 'core', baseURL: CORE_API_BASE_URL },
  OTHER: { baseType: 'core', baseURL: CORE_API_BASE_URL },
  ADMIN: { baseType: 'core', baseURL: CORE_API_BASE_URL },
  ADMIN_USER: { baseType: 'users', baseURL: USERS_API_BASE_URL },
  CONTENT_SAFETY: { baseType: 'core', baseURL: CORE_API_BASE_URL },
  MESSAGE: { baseType: 'core', baseURL: CORE_API_BASE_URL },
  DOWNLOAD: { baseType: 'core', baseURL: CORE_API_BASE_URL }
}

export const API_PATHS = Object.fromEntries(
  Object.entries(RAW_API_PATHS).map(([key, value]) => {
    const baseConfig = API_BASE_MAP[key]
    return [key, transformApiNode(value, baseConfig?.baseURL ?? CORE_API_BASE_URL)]
  })
) as typeof RAW_API_PATHS

export default API_PATHS

