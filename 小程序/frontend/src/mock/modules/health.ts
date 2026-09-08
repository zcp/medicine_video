/**
 * 健康检查相关 Mock API
 * 严格遵循《直播核心功能设计文档_v6_深度融合最终版.md》第6.3节"健康检查 API（监控与运维）"定义
 */

import { registerMockRule, mockSuccess, mockDelay } from '../index'
import type { HealthStatus, ReadinessStatus, ConfigInfo } from '@/api/health'

/**
 * 初始化健康检查相关 Mock
 */
export function setupHealthMock() {
  // 1. 基础健康检查
  registerMockRule({
    pattern: /\/api\/v1\/health$/,
    method: 'GET',
    handler: async () => {
      await mockDelay()
      
      const response: HealthStatus = {
        status: 'healthy',
        service: 'LiveCore Service',
        version: '1.0.0'
      }
      
      return mockSuccess(response)
    }
  })

  // 2. 就绪检查（Readiness Probe）
  registerMockRule({
    pattern: /\/api\/v1\/health\/ready$/,
    method: 'GET',
    handler: async () => {
      await mockDelay()
      
      const response: ReadinessStatus = {
        status: 'ready',
        database: 'connected',
        service: 'LiveCore Service'
      }
      
      return mockSuccess(response)
    }
  })

  // 3. 配置检查（Configuration Check）
  registerMockRule({
    pattern: /\/api\/v1\/health\/config$/,
    method: 'GET',
    handler: async () => {
      await mockDelay()
      
      const response: ConfigInfo = {
        environment: 'development',
        database: {
          server: 'localhost',
          port: 5432,
          database: 'live_core',
          user: 'postgres'
        },
        cors_origins: ['http://localhost:5175', 'http://localhost:3000'],
        debug: true,
        jwt_algorithm: 'HS256'
      }
      
      return mockSuccess(response)
    }
  })
}

