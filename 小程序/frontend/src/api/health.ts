/**
 * 健康检查API - 重构版本
 */

import { request } from '@/utils/request'

export type HealthStatus = {
	status: 'healthy' | 'unhealthy' | string
	service?: string
	version?: string
}

export type ReadinessStatus = {
	status: 'ready' | 'not_ready' | string
	database?: 'connected' | 'disconnected' | string
	service?: string
}

export type ConfigInfo = {
	environment: string
	database: {
		server: string
		port: number
		database: string
		user: string
	}
	cors_origins: string[]
	debug: boolean
	jwt_algorithm: string
}

// §3.4.1 GET /api/v1/health
export const healthCheck = () => request.get('/health', { auth: false, showError: false })
// §3.4.1 GET /api/v1/health/ready
export const readinessCheck = () => request.get('/health/ready', { auth: false, showError: false })
// §3.4.1 GET /api/v1/health/config
export const getConfigInfo = () => request.get('/health/config', { auth: false, showError: false })

export default { healthCheck, readinessCheck, getConfigInfo }
