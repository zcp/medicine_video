/**
 * Brands 模块 Mock 数据
 */

import { registerMockRule, mockSuccess, mockPaginatedResponse } from '../index'

// Mock 数据
const mockBrands = [
  { id: 'brand_1', name: '医药品牌A', logo: '/static/brands/brand-a.png', description: '专注心血管领域的医药品牌', followers_count: 5000, sessions_count: 120, topics_count: 15, isFeatured: true, level: 'gold', category: '制药' },
  { id: 'brand_2', name: '医疗器械B', logo: '/static/brands/brand-b.png', description: '领先的医疗器械制造商', followers_count: 3800, sessions_count: 95, topics_count: 12, isFeatured: true, level: 'platinum', category: '医疗设备' },
  { id: 'brand_3', name: '健康科技C', logo: '/static/brands/brand-c.png', description: '互联网+医疗健康平台', followers_count: 3200, sessions_count: 80, topics_count: 10, isFeatured: false, level: 'silver', category: '软件' },
  { id: 'brand_4', name: '耗材供应D', logo: '/static/brands/brand-d.png', description: '高品质医疗耗材供应商', followers_count: 2100, sessions_count: 60, topics_count: 8, isFeatured: false, level: 'bronze', category: '耗材' },
  { id: 'brand_5', name: '远程诊疗E', logo: '/static/brands/brand-e.png', description: '远程医疗服务提供商', followers_count: 2700, sessions_count: 70, topics_count: 9, isFeatured: true, level: 'gold', category: '软件' }
]

export function setupBrandsMock() {
  // 品牌列表（支持搜索、分页）
  registerMockRule({
    pattern: '/api/v1/brands',
    method: 'GET',
    handler: (params) => {
      const q = (params?.q || params?.keyword || '').toLowerCase()
      const filtered = q ? mockBrands.filter(b => b.name.toLowerCase().includes(q) || (b.description||'').toLowerCase().includes(q)) : mockBrands
      const page = Number(params?.page || 1)
      const size = Number(params?.pageSize || params?.size || 20)
      // 返回分页结构，兼容 store 的双格式处理
      return mockPaginatedResponse(filtered, page, size)
    }
  })

  // 获取品牌详情
  registerMockRule({
    pattern: /\/api\/v1\/brands\/[^/]+$/,
    method: 'GET',
    handler: (params) => {
      const brandId = params?.brandId || 'brand_1'
      const brand = mockBrands.find(b => b.id === brandId) || mockBrands[0]
      return mockSuccess({
        ...brand,
        website_url: 'https://brand.com',
        sort_order: 1,
        is_active: true,
        topics: [
          { id: 'topic_1', title: '专题一', cover_url: '/static/topics/1.png' },
          { id: 'topic_2', title: '专题二', cover_url: '/static/topics/2.png' }
        ],
        statistics: {
          topic_count: brand.topics_count,
          session_count: brand.sessions_count,
          follower_count: brand.followers_count
        }
      })
    }
  })

  // 获取品牌内容（详情+关联专题）
  registerMockRule({
    pattern: /\/api\/v1\/brands\/[^/]+\/content$/,
    method: 'GET',
    handler: (params) => {
      const brandId = params?.brandId || 'brand_1'
      const brand = mockBrands.find(b => b.id === brandId) || mockBrands[0]
      return mockSuccess({
        brand_info: {
          id: brand.id,
          name: brand.name,
          logo: brand.logo,
          banner_url: '/static/brands/banner-default.png',
          description: brand.description,
          followers_count: brand.followers_count,
          topics_count: brand.topics_count,
          sessions_count: brand.sessions_count
        },
        associated_topics: [
          { id: 'topic_1', title: `${brand.name} 专题A`, banner_url: '/static/topics/1.png', status: 'published', created_at: new Date().toISOString() },
          { id: 'topic_2', title: `${brand.name} 专题B`, banner_url: '/static/topics/2.png', status: 'published', created_at: new Date().toISOString() }
        ]
      })
    }
  })

  // 获取热门品牌
  registerMockRule({
    pattern: '/api/v1/brands/popular',
    method: 'GET',
    handler: (params) => {
      const limit = params?.limit || 10
      return mockSuccess(
        mockBrands
          .sort((a, b) => b.followers_count - a.followers_count)
          .slice(0, limit)
      )
    }
  })

  // 获取品牌统计
  registerMockRule({
    pattern: /\/api\/v1\/brands.*\/statistics/,
    method: 'GET',
    handler: () => {
      return mockSuccess({
        total_brands: mockBrands.length,
        active_brands: mockBrands.length,
        total_topics: mockBrands.reduce((sum, b) => sum + b.topics_count, 0),
        total_sessions: mockBrands.reduce((sum, b) => sum + b.sessions_count, 0),
        total_followers: mockBrands.reduce((sum, b) => sum + b.followers_count, 0)
      })
    }
  })

  console.log('  ✓ Brands Mock 已注册')
}
