/**
 * Tab管理相关 Mock API
 * 以后端设计文档为准：《06-直播间Tab管理-后端设计文档.md》
 * DDL: id, room_id, title, content, image_url, sort_order, is_active, created_at, updated_at
 * 路径: /api/v1/content/admin/rooms/{roomId}/tabs
 */

import { registerMockRule, mockSuccess, mockDelay } from '../index'
import { DEFAULT_CONFIG } from '@/common/constants'
import type { LiveRoomTab } from '@/api/tabs'

const mockTabs: LiveRoomTab[] = [
  {
    id: 'tab_001',
    room_id: 'room_001',
    title: '直播间简介',
    content: '这是一个关于心血管疾病诊疗的直播间',
    image_url: null,
    sort_order: 0,
    is_active: true,
    created_at: '2025-01-20T10:00:00Z',
    updated_at: '2025-01-20T10:00:00Z'
  },
  {
    id: 'tab_002',
    room_id: 'room_001',
    title: '医生简介',
    content: '张教授，主任医师',
    image_url: DEFAULT_CONFIG.DEFAULT_AVATAR,
    sort_order: 1,
    is_active: true,
    created_at: '2025-01-20T10:00:00Z',
    updated_at: '2025-01-20T10:00:00Z'
  }
]

export function setupTabsMock() {
  // 1. 查询直播间 Tab 列表（管理端）
  registerMockRule({
    pattern: /\/api\/v1\/content\/admin\/rooms\/([^/]+)\/tabs$/,
    method: 'GET',
    handler: async (_params: any, url?: string) => {
      await mockDelay()
      let roomId = 'room_001'
      if (url) {
        const match = url.match(/\/content\/admin\/rooms\/([^/]+)\/tabs/)
        if (match?.[1]) roomId = match[1]
      }
      const roomTabs = mockTabs.filter(tab => tab.room_id === roomId)
      return mockSuccess({ items: roomTabs })
    }
  })

  // 2. 创建 Tab
  registerMockRule({
    pattern: /\/api\/v1\/content\/admin\/rooms\/([^/]+)\/tabs$/,
    method: 'POST',
    handler: async (params: any, url?: string) => {
      await mockDelay()
      let roomId = 'room_001'
      if (url) {
        const match = url.match(/\/content\/admin\/rooms\/([^/]+)\/tabs/)
        if (match?.[1]) roomId = match[1]
      }
      const newTab: LiveRoomTab = {
        id: `tab_${Date.now()}`,
        room_id: roomId,
        title: params.title || '',
        content: params.content || null,
        image_url: params.image_url || null,
        sort_order: params.sort_order || 0,
        is_active: params.is_active ?? true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }
      mockTabs.push(newTab)
      return mockSuccess(newTab)
    }
  })

  // 3. 更新 Tab
  registerMockRule({
    pattern: /\/api\/v1\/content\/admin\/tabs\/([^/]+)$/,
    method: 'PATCH',
    handler: async (params: any, url?: string) => {
      await mockDelay()
      let tabId = ''
      if (url) {
        const match = url.match(/\/content\/admin\/tabs\/([^/]+)/)
        if (match?.[1]) tabId = match[1]
      }
      const tabIndex = mockTabs.findIndex(tab => tab.id === tabId)
      if (tabIndex === -1) throw new Error('Tab not found')
      mockTabs[tabIndex] = { ...mockTabs[tabIndex], ...params, updated_at: new Date().toISOString() }
      return mockSuccess(mockTabs[tabIndex])
    }
  })

  // 4. 删除 Tab
  registerMockRule({
    pattern: /\/api\/v1\/content\/admin\/tabs\/([^/]+)$/,
    method: 'DELETE',
    handler: async (_params: any, url?: string) => {
      await mockDelay()
      let tabId = ''
      if (url) {
        const match = url.match(/\/content\/admin\/tabs\/([^/]+)/)
        if (match?.[1]) tabId = match[1]
      }
      const tabIndex = mockTabs.findIndex(tab => tab.id === tabId)
      if (tabIndex === -1) throw new Error('Tab not found')
      mockTabs.splice(tabIndex, 1)
      return mockSuccess(null)
    }
  })

  // 5. 批量排序
  registerMockRule({
    pattern: /\/api\/v1\/content\/admin\/rooms\/([^/]+)\/tabs\/sort$/,
    method: 'PATCH',
    handler: async (params: any) => {
      await mockDelay()
      if (params?.tab_ids) {
        params.tab_ids.forEach((id: string, index: number) => {
          const tab = mockTabs.find(t => t.id === id)
          if (tab) tab.sort_order = index
        })
      }
      return mockSuccess(null)
    }
  })

  // 6. 公开Tab列表
  registerMockRule({
    pattern: /\/api\/v1\/content\/rooms\/([^/]+)\/tabs$/,
    method: 'GET',
    handler: async (_params: any, url?: string) => {
      await mockDelay()
      let roomId = 'room_001'
      if (url) {
        const match = url.match(/\/content\/rooms\/([^/]+)\/tabs/)
        if (match?.[1]) roomId = match[1]
      }
      const roomTabs = mockTabs.filter(tab => tab.room_id === roomId && tab.is_active)
      return mockSuccess({ items: roomTabs })
    }
  })
}
