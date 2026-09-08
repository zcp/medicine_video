/**
 * 设置相关 API
 */

import { request } from '@/utils/request'
import { API_PATHS } from '@/config/api'
import type { ApiResponse } from '@/types/common'
import type { UserSettings } from '@/types/settings'

export const getUserSettings = (): Promise<ApiResponse<UserSettings>> => {
  // 走 users-service
  return request.get(API_PATHS.USER.SETTINGS, { showError: false })
}

export const updateUserSettings = (data: Partial<UserSettings>): Promise<ApiResponse<UserSettings>> => {
  return request.put(API_PATHS.USER.SETTINGS, data, { loading: true, loadingText: '保存中...' })
}

export const getSystemConfig = (): Promise<ApiResponse<any>> => {
  // 后端可能未实现：store 会吞掉错误
  return request.get(API_PATHS.SETTINGS.SYSTEM_CONFIG, { showError: false })
}

export default {
  getUserSettings,
  updateUserSettings,
  getSystemConfig
}
