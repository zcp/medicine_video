/**
 * 直播间功能性 Tab 公开 Mock API
 * 路径：/api/v1/rooms/{room_id}/tabs
 * 说明：所有用户均可访问，用于直播间展示功能性 Tab
 */

import { registerMockRule, mockSuccess, mockDelay } from '../index'
import { DEFAULT_CONFIG } from '@/common/constants'
import type { RoomTab } from '@/api/room-tabs'

/**
 * 模拟功能性 Tab 数据
 */
const mockRoomTabs: RoomTab[] = [
  {
    id: 'tab_001',
    room_id: 'room_001',
    tab_key: 'intro',
    title: '直播间简介',
    content_type: 'text',
    text_content: '这是一个关于心血管疾病诊疗的直播间',
    image_url: null,
    sort_order: 0,
    is_active: true,
    created_at: '2025-01-20T10:00:00Z',
    updated_at: '2025-01-20T10:00:00Z'
  },
  {
    id: 'tab_002',
    room_id: 'room_001',
    tab_key: 'doctor_intro',
    title: '医生简介',
    content_type: 'mixed',
    text_content: '张教授，主任医师',
    image_url: DEFAULT_CONFIG.DEFAULT_AVATAR,
    sort_order: 1,
    is_active: true,
    created_at: '2025-01-20T10:00:00Z',
    updated_at: '2025-01-20T10:00:00Z'
  }
]

/**
 * 初始化直播间功能性 Tab 公开 Mock
 */
export function setupRoomTabsMock() {
  // 查询直播间功能性 Tab 列表（公开接口）
  registerMockRule({
    pattern: /\/api\/v1\/rooms\/([^/]+)\/tabs$/,
    method: 'GET',
    handler: async (_params: any, url?: string) => {
      await mockDelay()

      // 从URL中提取roomId
      let roomId = 'room_001'
      if (url) {
        const match = url.match(/\/api\/v1\/rooms\/([^/]+)\/tabs/)
        if (match && match[1]) {
          roomId = match[1]
        }
      }

      // 过滤该房间的功能性Tab
      const roomTabs = mockRoomTabs.filter(tab => tab.room_id === roomId)

      return mockSuccess(roomTabs)
    }
  })
}
