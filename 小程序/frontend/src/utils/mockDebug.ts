/**
 * Mock 调试工具
 */

import { getMockRules, mockConfig } from '@/mock'

/**
 * 打印 Mock 状态
 */
export function debugMockStatus() {
  console.log('=== Mock 调试信息 ===')
  console.log('Mock 启用:', mockConfig.enabled)
  console.log('Mock 延迟:', mockConfig.delay, 'ms')
  console.log('日志启用:', mockConfig.logRequests)
  
  const rules = getMockRules()
  console.log('已注册规则数:', rules.length)
  
  if (rules.length > 0) {
    console.log('\n已注册的 Mock 规则:')
    rules.forEach((rule, index) => {
      console.log(`  ${index + 1}. ${rule.method} ${rule.pattern}`)
    })
  } else {
    console.warn('⚠️ 没有注册任何 Mock 规则!')
  }
  
  console.log('==================')
}

/**
 * 在全局暴露调试函数（兼容多端）
 */
// @ts-ignore
const globalObj = typeof window !== 'undefined' ? window : typeof global !== 'undefined' ? global : {}
// @ts-ignore
globalObj.debugMock = debugMockStatus
