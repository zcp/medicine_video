/**
 * Tags 模块 Mock 数据
 */

import { registerMockRule, mockSuccess } from '../index'

// Mock 数据
const mockTags = [
  { id: 'tag_1', name: '心血管', description: '心血管相关内容', usage_count: 1000, icon: '❤️', color: '#FF4D4F' },
  { id: 'tag_2', name: '神经科', description: '神经科相关内容', usage_count: 800, icon: '🧠', color: '#FF7A45' },
  { id: 'tag_3', name: '肿瘤科', description: '肿瘤科相关内容', usage_count: 650, icon: '🎗️', color: '#FFA940' },
  { id: 'tag_4', name: '骨科', description: '骨科相关内容', usage_count: 500, icon: '🦴', color: '#52C41A' },
  { id: 'tag_5', name: '儿科', description: '儿科相关内容', usage_count: 450, icon: '👶', color: '#0F766E' },
  { id: 'tag_6', name: '妇产科', description: '妇产科相关内容', usage_count: 400, icon: '👶', color: '#722ED1' },
  { id: 'tag_7', name: '呼吸内科', description: '呼吸内科相关内容', usage_count: 350, icon: '🫁', color: '#13C2C2' },
  { id: 'tag_8', name: '消化内科', description: '消化内科相关内容', usage_count: 300, icon: '🍽️', color: '#FA8C16' }
]

export function setupTagsMock() {
  // 获取标签详情
  registerMockRule({
    pattern: /\/api\/v1\/tags\/[^/]+$/,
    method: 'GET',
    handler: (params) => {
      const tagId = params?.tagId || 'tag_1'
      const tag = mockTags.find(t => t.id === tagId) || mockTags[0]
      return mockSuccess({
        ...tag,
        is_active: true,
        sort_order: 1,
        created_at: '2024-01-01T00:00:00Z'
      })
    }
  })

  // 搜索标签
  registerMockRule({
    pattern: '/api/v1/tags/search',
    method: 'GET',
    handler: (params) => {
      const keyword = params?.keyword || ''
      const limit = params?.limit || 20
      const results = mockTags
        .filter(tag => tag.name.includes(keyword) || tag.description.includes(keyword))
        .slice(0, limit)
      return mockSuccess(results)
    }
  })

  // 获取热门标签
  registerMockRule({
    pattern: '/api/v1/tags/popular',
    method: 'GET',
    handler: (params) => {
      const limit = params?.limit || 20
      const popular = [...mockTags]
        .sort((a, b) => b.usage_count - a.usage_count)
        .slice(0, limit)
        .map(tag => ({
          ...tag,
          trend: tag.usage_count > 600 ? 'rising' : tag.usage_count > 400 ? 'stable' : 'falling'
        }))
      return mockSuccess(popular)
    }
  })

  // 获取标签统计
  registerMockRule({
    pattern: /\/api\/v1\/tags.*\/statistics/,
    method: 'GET',
    handler: () => {
      return mockSuccess({
        total_tags: mockTags.length,
        active_tags: mockTags.length - 1,
        total_usage: mockTags.reduce((sum, tag) => sum + tag.usage_count, 0),
        top_tags: mockTags.slice(0, 5).map(tag => ({
          id: tag.id,
          name: tag.name,
          usage_count: tag.usage_count
        }))
      })
    }
  })

  console.log('  ✓ Tags Mock 已注册')
}
