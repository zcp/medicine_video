/**
 * 留言相关 Mock API
 * 对齐后端 V3：嵌套 user + 兼容 user_display_name
 */

import { registerMockRule, mockSuccess, mockPaginatedResponse, mockDelay } from '../index'
import type { RoomMessageItem } from '@/types/roomMessage'
import { log } from '@/logs/logger'

const mockMessages: RoomMessageItem[] = [
  {
    id: 'msg_001',
    room_id: 'room_001',
    user_id: 'user_001',
    content: '医生讲得很好 👍',
    created_at: '2025-01-20T14:05:00Z',
    user_role: 'REGULAR',
    user_display_name: '张三',
    user: {
      nickname: '张三',
      avatar_url: null
    }
  },
  {
    id: 'msg_002',
    room_id: 'room_001',
    user_id: 'user_002',
    content: '欢迎大家提问',
    created_at: '2025-01-20T14:10:00Z',
    user_role: 'ADMIN',
    user_display_name: '管理员',
    user: {
      nickname: '管理员',
      avatar_url: null
    }
  },
  {
    id: 'msg_003',
    room_id: 'room_001',
    user_id: 'user_003',
    content: '这个直播很有帮助',
    created_at: '2025-01-20T14:15:00Z',
    user_role: 'REGULAR',
    user_display_name: '李四',
    user: {
      nickname: '李四',
      avatar_url: '/uploads/avatars/demo.jpg'
    }
  }
]

export function setupMessagesMock() {
  registerMockRule({
    pattern: /\/api\/v1\/rooms\/([^/]+)\/messages$/,
    method: 'POST',
    handler: async (params: any) => {
      await mockDelay()

      const nickname = '当前用户'
      const newMessage: RoomMessageItem = {
        id: `msg_${Date.now()}`,
        room_id: params.room_id || 'room_001',
        user_id: 'user_current',
        content: params.content || '',
        created_at: new Date().toISOString(),
        user_role: 'REGULAR',
        user_display_name: nickname,
        user: {
          nickname,
          avatar_url: null
        }
      }

      mockMessages.unshift(newMessage)
      log.info('live', '[留言Mock] POST 发送留言成功', {
        messageId: newMessage.id,
        userName: newMessage.user?.nickname
      })
      return mockSuccess(newMessage)
    }
  })

  registerMockRule({
    pattern: /\/api\/v1\/rooms\/([^/]+)\/messages$/,
    method: 'GET',
    handler: async (params: any, url?: string) => {
      await mockDelay()

      let roomId = 'room_001'
      if (url) {
        const match = url.match(/\/api\/v1\/rooms\/([^/]+)\/messages/)
        if (match && match[1]) roomId = match[1]
      }

      const page = params?.page || 1
      const size = params?.page_size || params?.size || params?.limit || 20
      const roomMessages = mockMessages.filter(msg => msg.room_id === roomId)

      log.info('live', '[留言Mock] GET 获取留言列表成功', {
        roomId,
        totalMessageCount: roomMessages.length,
        messages: roomMessages.map(msg => ({
          id: msg.id,
          userName: msg.user?.nickname || msg.user_display_name,
          hasAvatar: !!msg.user?.avatar_url
        }))
      })

      return mockPaginatedResponse(roomMessages, page, size)
    }
  })
}
