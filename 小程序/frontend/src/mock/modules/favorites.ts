/**
 * Favorites 模块 Mock 数据
 */

import { registerMockRule, mockSuccess } from '../index'

// Mock 数据
const mockFavoriteStatus = new Map<string, boolean>([
  ['room_1', true],
  ['room_2', true],
  ['room_3', false]
])

const mockFolders = [
  {
    id: 'folder_1',
    name: '默认收藏夹',
    description: '系统默认收藏夹',
    item_count: 10,
    created_at: '2024-01-01T00:00:00Z'
  },
  {
    id: 'folder_2',
    name: '心血管专题',
    description: '心血管相关直播',
    item_count: 5,
    created_at: '2024-01-15T00:00:00Z'
  }
]

export function setupFavoritesMock() {
  // 检查收藏状态
  registerMockRule({
    pattern: '/api/v1/users/me/favorites/check',
    method: 'GET',
    handler: (params) => {
      const roomId = params?.room_id || 'room_1'
      const isFavorited = mockFavoriteStatus.get(roomId) || false
      return mockSuccess({
        is_favorited: isFavorited,
        favorite_id: isFavorited ? `fav_${roomId}` : null,
        created_at: isFavorited ? '2024-01-01T00:00:00Z' : null
      })
    }
  })

  // 获取收藏统计
  registerMockRule({
    pattern: '/api/v1/users/me/favorites/statistics',
    method: 'GET',
    handler: () => {
      const totalCount = Array.from(mockFavoriteStatus.values()).filter(Boolean).length
      return mockSuccess({
        total_count: totalCount,
        by_type: {
          room: totalCount
        },
        recent_count: Math.min(5, totalCount)
      })
    }
  })

  // 创建收藏文件夹
  registerMockRule({
    pattern: '/api/v1/users/me/favorite-folders',
    method: 'POST',
    handler: (params) => {
      const newFolder = {
        id: `folder_${Date.now()}`,
        name: params?.name || '新建收藏夹',
        description: params?.description || '',
        item_count: 0,
        created_at: new Date().toISOString()
      }
      mockFolders.push(newFolder)
      return mockSuccess(newFolder)
    }
  })

  // 获取收藏文件夹列表
  registerMockRule({
    pattern: '/api/v1/users/me/favorite-folders',
    method: 'GET',
    handler: () => {
      return mockSuccess(mockFolders)
    }
  })

  // 批量添加收藏
  registerMockRule({
    pattern: '/api/v1/users/me/favorites/batch',
    method: 'POST',
    handler: (params) => {
      const roomIds = params?.room_ids || []
      roomIds.forEach((id: string) => mockFavoriteStatus.set(id, true))
      return mockSuccess({
        success_count: roomIds.length,
        failed_count: 0,
        success_ids: roomIds,
        failed_ids: []
      })
    }
  })

  // 批量取消收藏
  registerMockRule({
    pattern: '/api/v1/users/me/favorites/batch',
    method: 'DELETE',
    handler: (params) => {
      const favoriteIds = params?.favorite_ids || []
      // 从 favorite_ids 提取 room_ids（假设格式为 fav_room_1）
      const roomIds = favoriteIds.map((id: string) => id.replace('fav_', ''))
      roomIds.forEach((id: string) => mockFavoriteStatus.set(id, false))
      return mockSuccess({
        deleted_count: favoriteIds.length,
        favorite_ids: favoriteIds
      })
    }
  })

  console.log('  ✓ Favorites Mock 已注册')
}
