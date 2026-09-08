/**
 * 用户偏好设置（V2.1）
 * 对齐《直播核心功能设计文档_v6_后端新增api接口和模块设计文档-v2.md》4.15
 */

export type ThemeMode = 'light' | 'dark' | 'auto' | 'scheduled'

export type HomepageViewMode = 'double' | 'single'

export interface UserPreferencesV2 {
  id: string
  user_id: string

  theme_mode: ThemeMode
  theme_scheduled_dark_time?: string | null
  theme_scheduled_light_time?: string | null

  /** 首页科室星标：最多 5 个，顺序即展示顺序 */
  pinned_categories: string[]

  /** 首页Feed视图：双列/单列 */
  homepage_view_mode: HomepageViewMode

  cellular_warning_enabled: boolean
  auto_reduce_quality: boolean
  auto_play_on_wifi: boolean

  created_at: string
  updated_at: string
}

export interface UpdateUserPreferencesRequest {
  theme_mode?: ThemeMode
  theme_scheduled_dark_time?: string | null
  theme_scheduled_light_time?: string | null
  pinned_categories?: string[]
  homepage_view_mode?: HomepageViewMode
  cellular_warning_enabled?: boolean
  auto_reduce_quality?: boolean
  auto_play_on_wifi?: boolean
}
