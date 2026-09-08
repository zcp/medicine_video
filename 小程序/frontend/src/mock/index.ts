/**
 * Mock API 系统
 * 在后端 API 未实现前，使用模拟数据进行开发和测试
 */

import { setupTagsMock } from './modules/tags'
import { setupBrandsMock } from './modules/brands'
import { setupNotificationsMock } from './modules/notifications'
import { setupFavoritesMock } from './modules/favorites'
import { setupMessagesMock } from './modules/messages'
import { setupTabsMock } from './modules/tabs'
import { setupRoomTabsMock } from './modules/room-tabs'
import { setupExpertsMock } from './modules/experts'
import { setupImportMock } from './modules/import'
import { setupHealthMock } from './modules/health'

/**
 * Mock 配置
 * 从环境变量读取配置，默认启用
 */
export const mockConfig = {
  // 重要：核心链路禁止依赖 mock。
  // 仅当显式设置 VITE_USE_MOCK=true 时才启用（默认关闭）。
  enabled: import.meta.env?.VITE_USE_MOCK === 'true',
  delay: 150, // 模拟网络延迟（毫秒）
  logRequests: true // 是否打印请求日志
}

// 开发环境输出 Mock 配置状态
if (process.env.NODE_ENV === 'development') {
  console.log('🎭 Mock 配置状态:')
  console.log('  - VITE_USE_MOCK:', import.meta.env?.VITE_USE_MOCK)
  console.log('  - Mock 启用:', mockConfig.enabled)
}

/**
 * Mock API 路径匹配规则
 */
export interface MockRule {
  pattern: RegExp | string
  method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  handler: (params?: any) => any
}

const mockRules: MockRule[] = []

/**
 * 导出 mockRules 用于调试
 */
export function getMockRules() {
  return mockRules
}

/**
 * 注册 Mock 规则
 */
export function registerMockRule(rule: MockRule) {
  mockRules.push(rule)
  if (mockConfig.logRequests) {
    console.log(`  📌 注册 Mock 规则: ${rule.method} ${rule.pattern}`)
  }
}

/**
 * 查找匹配的 Mock 规则
 */
export function findMockRule(url: string, method: string): MockRule | null {
  if (mockConfig.logRequests) {
    console.log(`🔍 查找 Mock 规则: ${method} ${url}`)
    console.log(`   当前已注册 ${mockRules.length} 个规则`)
  }
  
  const rule = mockRules.find(rule => {
    const methodMatch = rule.method === method
    const urlMatch = typeof rule.pattern === 'string'
      ? url.includes(rule.pattern)
      : rule.pattern.test(url)
    
    if (mockConfig.logRequests && (methodMatch || urlMatch)) {
      console.log(`   检查规则: ${rule.method} ${rule.pattern} - 方法:${methodMatch} URL:${urlMatch}`)
    }
    
    return methodMatch && urlMatch
  }) || null
  
  if (mockConfig.logRequests) {
    console.log(`   ${rule ? '✅ 找到匹配' : '❌ 未找到匹配'}`)
  }
  
  return rule
}

/**
 * 初始化所有 Mock 模块
 */
export function setupMock() {
  if (!mockConfig.enabled) {
    console.log('🚫 Mock API 已禁用')
    return
  }

  console.log('🎭 初始化 Mock API...')
  
  // 注册各模块的 Mock
  setupTagsMock()
  setupBrandsMock()
  setupNotificationsMock()
  setupFavoritesMock()
  setupMessagesMock()
  setupTabsMock()
  setupRoomTabsMock()
  setupExpertsMock()
  setupImportMock()
  setupHealthMock()
  
  console.log(`✅ Mock API 已启用 (${mockRules.length} 个规则)`)
  if (mockConfig.logRequests) {
    console.log('📝 Mock 请求日志已启用')
  }
}

/**
 * 模拟网络延迟
 */
export function mockDelay(): Promise<void> {
  return new Promise(resolve => {
    setTimeout(resolve, mockConfig.delay)
  })
}

/**
 * 生成统一的成功响应
 */
export function mockSuccess<T>(data: T, message = 'success') {
  return {
    code: 200,
    message,
    data,
    timestamp: new Date().toISOString()
  }
}

/**
 * 生成统一的错误响应
 */
export function mockError(code: number, message: string) {
  return {
    code,
    message,
    data: null,
    timestamp: new Date().toISOString()
  }
}

/**
 * 生成分页响应
 */
export function mockPaginatedResponse<T>(
  items: T[],
  page: number = 1,
  size: number = 20
) {
  const start = (page - 1) * size
  const end = start + size
  const pagedItems = items.slice(start, end)
  
  return mockSuccess({
    total: items.length,
    page,
    size,
    items: pagedItems,
    hasMore: end < items.length
  })
}
