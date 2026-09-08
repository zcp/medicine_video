import { registerMockRule, mockSuccess, mockError, mockPaginatedResponse } from '../index'
import { DEFAULT_CONFIG } from '@/common/constants'

// 简单内存态模拟关注关系
const followSet = new Set<string>(['expert_001'])

const featuredExperts = [
  {
    id: 'expert_001',
    name: '郭少雷',
    avatar_url: DEFAULT_CONFIG.DEFAULT_AVATAR,
    title: '副主任医师',
    hospital: '中山大学附属第一医院',
    department: '心内科'
  },
  {
    id: 'expert_002',
    name: '廖创新',
    avatar_url: DEFAULT_CONFIG.DEFAULT_AVATAR,
    title: '副主任医师',
    hospital: '中山大学附属第一医院',
    department: '神经外科'
  },
  {
    id: 'expert_003',
    name: '张文博',
    avatar_url: DEFAULT_CONFIG.DEFAULT_AVATAR,
    title: '主任医师',
    hospital: '华中科技大学同济医学院附属医院',
    department: '消化内科'
  },
  {
    id: 'expert_004',
    name: '陈志远',
    avatar_url: DEFAULT_CONFIG.DEFAULT_AVATAR,
    title: '主任医师',
    hospital: '复旦大学附属中山医院',
    department: '骨科'
  }
]

function buildFollowedExpertList() {
  return Array.from(followSet).map(expertId => {
    const expert = featuredExperts.find(item => item.id === expertId)
    return {
      expert_id: expertId,
      name: expert?.name || `专家${expertId}`,
      avatar_url: expert?.avatar_url || DEFAULT_CONFIG.DEFAULT_AVATAR,
      title: expert?.title || '专家',
      hospital: expert?.hospital || '平台认证专家',
      subscribed_at: '2026-05-01T00:00:00Z',
      live_status: {
        is_live: false,
        session_id: null
      }
    }
  })
}

export function setupExpertsMock() {
  // 专家列表/搜索
  registerMockRule({
    pattern: /\/api\/v1\/experts(?:\?|$)/,
    method: 'GET',
    handler: (params?: any) => {
      const keyword = String(params?.keyword || params?.q || '').trim().toLowerCase()
      const page = Number(params?.page || 1)
      const size = Number(params?.size || 20)

      const pool = featuredExperts.map((item) => ({
        ...item,
        title: item.title,
        hospital: item.hospital,
        department: item.department,
        bio: `${item.name} ${item.title || ''} ${item.hospital || ''} ${item.department || ''}`.trim()
      }))

      const filtered = keyword
        ? pool.filter((item) => {
            const haystack = [item.name, item.title, item.hospital, item.department, item.bio]
              .filter(Boolean)
              .join(' ')
              .toLowerCase()
            return haystack.includes(keyword)
          })
        : pool

      return mockPaginatedResponse(filtered, page, size)
    }
  })

  // 精选专家列表
  registerMockRule({
    pattern: /\/api\/v1\/featured-experts/,
    method: 'GET',
    handler: (params?: any) => {
      const limit = Number(params?.limit || 6)
      return mockSuccess(featuredExperts.slice(0, limit))
    }
  })

  // 当前关注专家列表
  registerMockRule({
    pattern: /\/api\/v1\/users\/me\/followed-experts/,
    method: 'GET',
    handler: () => {
      return mockSuccess(buildFollowedExpertList())
    }
  })

  // 查询关注状态
  registerMockRule({
    pattern: /\/api\/v1\/experts\/(.+)\/follow\/status/,
    method: 'GET',
    handler: (params?: any) => {
      const id = typeof params?.expert_id === 'string' ? params.expert_id : 'e1'
      const isFollowing = followSet.has(id)
      return mockSuccess({ expert_id: id, is_following: isFollowing })
    }
  })

  // 关注专家
  registerMockRule({
    pattern: /\/api\/v1\/experts\/(.+)\/follow/,
    method: 'POST',
    handler: (params?: any) => {
      const id = typeof params?.expert_id === 'string' ? params.expert_id : 'e1'
      if (followSet.has(id)) {
        return mockError(400, '已关注')
      }
      followSet.add(id)
      return mockSuccess({ expert_id: id, following: true })
    }
  })

  // 取消关注专家
  registerMockRule({
    pattern: /\/api\/v1\/experts\/(.+)\/follow/,
    method: 'DELETE',
    handler: (params?: any) => {
      const id = typeof params?.expert_id === 'string' ? params.expert_id : 'e1'
      if (!followSet.has(id)) {
        return mockError(400, '未关注')
      }
      followSet.delete(id)
      return mockSuccess({ expert_id: id, following: false })
    }
  })
}
