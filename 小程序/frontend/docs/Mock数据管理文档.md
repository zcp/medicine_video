# Mock数据管理文档

## 1. Mock数据概述

### 1.1 使用目的
- **前后端分离开发**：前端开发不依赖后端接口完成度
- **快速原型验证**：使用真实数据结构快速验证功能
- **测试数据准备**：为功能测试提供稳定的数据基础
- **演示数据支撑**：为产品演示提供完整的数据场景

### 1.2 Mock策略
```typescript
开发阶段Mock策略：
├── 阶段0-1: 静态Mock数据（JSON文件）
├── 阶段2: 组件Mock数据（单组件测试）
├── 阶段3: 页面Mock数据（完整业务流程）
└── 联调阶段: 动态Mock服务（Mock Server）
```

## 2. Mock数据架构

### 2.1 文件组织结构
```
src/mock/
├── index.ts                 // Mock服务入口
├── config.ts               // Mock配置
├── interceptor.ts          // 请求拦截器
├── data/                   // 静态数据文件
│   ├── home.ts            // 首页数据
│   ├── expert.ts          // 专家数据
│   ├── brand.ts           // 品牌数据
│   ├── room.ts            // 房间数据
│   ├── live.ts            // 直播数据
│   ├── search.ts          // 搜索数据
│   └── user.ts            // 用户数据
├── services/               // Mock服务
│   ├── homeService.ts     // 首页服务Mock
│   ├── expertService.ts   // 专家服务Mock
│   ├── brandService.ts    // 品牌服务Mock
│   └── searchService.ts   // 搜索服务Mock
└── utils/                  // Mock工具函数
    ├── dataGenerator.ts   // 数据生成器
    ├── pagination.ts      // 分页处理
    └── delay.ts          // 延迟模拟
```

### 2.2 Mock配置管理
```typescript
// src/mock/config.ts
export interface MockConfig {
  enabled: boolean           // 是否启用Mock
  delay: number             // 请求延迟(ms)
  errorRate: number         // 错误率(0-1)
  baseURL: string           // Mock服务地址
  modules: {                // 模块配置
    home: boolean
    expert: boolean
    brand: boolean
    room: boolean
    live: boolean
    search: boolean
    user: boolean
  }
}

export const mockConfig: MockConfig = {
  enabled: true,
  delay: 300,
  errorRate: 0.05,
  baseURL: '/api/mock',
  modules: {
    home: true,
    expert: true,
    brand: true,
    room: true,
    live: true,
    search: true,
    user: false  // 用户相关接口暂不Mock
  }
}
```

## 3. Mock数据定义

### 3.1 首页Mock数据
```typescript
// src/mock/data/home.ts
import type { Banner, Category, FeedItem } from '@/types/home'

export const mockBanners: Banner[] = [
  {
    id: 'banner_001',
    title: '心血管疾病诊疗新进展',
    image_url: '/static/banners/cardiology.png',
    link_type: 'room',
    link_target: 'room_001',
    order: 1,
    is_active: true
  },
  {
    id: 'banner_002', 
    title: '肿瘤治疗前沿技术',
    image_url: '/static/banners/oncology.png',
    link_type: 'expert',
    link_target: 'expert_002',
    order: 2,
    is_active: true
  }
]

export const mockCategories: Category[] = [
  {
    id: 'cat_001',
    name: '心血管内科',
    icon_url: '/static/categories/cardiology.png',
    order: 1,
    is_featured: true
  },
  {
    id: 'cat_002',
    name: '肿瘤科',
    icon_url: '/static/categories/oncology.png', 
    order: 2,
    is_featured: true
  }
]

export const mockFeedList: FeedItem[] = [
  {
    id: 'feed_001',
    type: 'live_session',
    title: '急性心梗的诊断与治疗',
    description: '详细讲解急性心梗的最新诊断标准和治疗方案...',
    cover_url: '/static/sessions/acute-mi.png',
    category: {
      id: 'cat_001',
      name: '心血管内科'
    },
    expert: {
      id: 'expert_001',
      name: '张教授',
      avatar_url: '/static/experts/zhang.png',
      title: '主任医师'
    },
    stats: {
      view_count: 1245,
      like_count: 89,
      comment_count: 23
    },
    start_time: '2024-12-01 14:00:00',
    status: 'upcoming',
    is_featured: true
  }
]
```

### 3.2 专家Mock数据
```typescript
// src/mock/data/expert.ts
import type { Expert, ExpertDetail } from '@/types/expert'

export const mockExperts: Expert[] = [
  {
    id: 'expert_001',
    name: '张明华',
    avatar_url: '/static/experts/zhang.png',
    title: '主任医师、教授、博士生导师',
    hospital: '北京协和医院',
    department: '心血管内科',
    specialties: ['心血管介入', '心脏起搏器', '心律失常'],
    bio: '从事心血管内科临床工作30余年，擅长冠心病介入治疗...',
    stats: {
      followers_count: 1520,
      sessions_count: 45,
      total_views: 25680
    },
    verified: true,
    rating: 4.9
  }
]

export const mockExpertDetail: ExpertDetail = {
  ...mockExperts[0],
  education: [
    {
      school: '北京医科大学',
      degree: '医学博士',
      major: '心血管内科',
      year: '1985-1992'
    }
  ],
  experience: [
    {
      hospital: '北京协和医院',
      department: '心血管内科',
      position: '主任医师',
      start_year: 2005,
      end_year: null,
      is_current: true
    }
  ],
  achievements: [
    '国家科技进步二等奖（2018）',
    '中华医学会心血管病学分会委员',
    '发表SCI论文80余篇'
  ],
  upcoming_sessions: [
    {
      id: 'session_001',
      title: '冠心病介入治疗新进展',
      start_time: '2024-12-01 14:00:00',
      room_id: 'room_001'
    }
  ]
}
```

### 3.3 品牌Mock数据
```typescript
// src/mock/data/brand.ts
import type { Brand, BrandTopic } from '@/types/brand'

export const mockBrands: Brand[] = [
  {
    id: 'brand_001',
    name: '强生医疗',
    description: '全球医疗设备和制药行业的领导者',
    logo_url: '/static/brands/johnson.png',
    banner_url: '/static/brands/johnson-banner.png',
    website_url: 'https://www.jnj.com/innovation/healthcare',
    is_featured: true,
    categories: ['医疗设备', '制药'],
    stats: {
      topics_count: 12,
      sessions_count: 35,
      followers_count: 2840
    },
    verified: true
  },
  {
    id: 'brand_002',
    name: '飞利浦医疗',
    description: '致力于通过创新改善人们的健康和福祉',
    logo_url: '/static/brands/philips.png',
    banner_url: '/static/brands/philips-banner.png', 
    website_url: 'https://www.philips.com/healthcare',
    is_featured: true,
    categories: ['医疗设备', '医疗影像'],
    stats: {
      topics_count: 8,
      sessions_count: 22,
      followers_count: 1960
    },
    verified: true
  }
]

export const mockBrandTopics: BrandTopic[] = [
  {
    id: 'topic_001',
    brand_id: 'brand_001',
    title: '微创手术技术专题',
    description: '探索强生医疗在微创手术领域的最新技术和产品',
    cover_url: '/static/topics/minimally-invasive.png',
    sessions_count: 5,
    is_featured: true,
    created_at: '2024-11-01T00:00:00Z'
  }
]
```

## 4. Mock服务实现

### 4.1 请求拦截器
```typescript
// src/mock/interceptor.ts
import type { MockConfig } from './config'
import { mockServices } from './services'

export class MockInterceptor {
  private config: MockConfig
  
  constructor(config: MockConfig) {
    this.config = config
  }
  
  // 安装拦截器
  install() {
    if (!this.config.enabled) return
    
    uni.addInterceptor('request', {
      invoke: this.handleRequest.bind(this),
      success: this.handleSuccess.bind(this),
      fail: this.handleFail.bind(this)
    })
  }
  
  // 处理请求
  private async handleRequest(args: any) {
    const { url, method = 'GET' } = args
    
    // 检查是否需要Mock
    if (this.shouldMock(url)) {
      const mockResponse = await this.getMockResponse(url, method, args.data)
      
      // 模拟延迟
      await this.delay()
      
      // 模拟错误
      if (this.shouldSimulateError()) {
        throw new Error('Mock Error: Network Error')
      }
      
      return mockResponse
    }
    
    return args
  }
  
  // 判断是否需要Mock
  private shouldMock(url: string): boolean {
    return url.includes('/api/') && this.config.enabled
  }
  
  // 获取Mock响应
  private async getMockResponse(url: string, method: string, data: any) {
    const routeKey = this.getRouteKey(url, method)
    const mockService = mockServices[routeKey]
    
    if (mockService) {
      return await mockService(data)
    }
    
    throw new Error(`Mock service not found for: ${routeKey}`)
  }
  
  // 模拟延迟
  private delay(): Promise<void> {
    return new Promise(resolve => {
      setTimeout(resolve, this.config.delay)
    })
  }
  
  // 模拟错误
  private shouldSimulateError(): boolean {
    return Math.random() < this.config.errorRate
  }
  
  // 获取路由键
  private getRouteKey(url: string, method: string): string {
    // 将URL和方法转换为路由键
    const path = url.replace(/^.*\/api\//, '').replace(/\?.*$/, '')
    return `${method.toUpperCase()} ${path}`
  }
}
```

### 4.2 Mock服务定义
```typescript
// src/mock/services/homeService.ts
import { mockBanners, mockCategories, mockFeedList } from '../data/home'
import { createMockResponse, paginate } from '../utils'

export const homeServices = {
  // 获取轮播图
  'GET banners': () => {
    return createMockResponse(mockBanners.filter(b => b.is_active))
  },
  
  // 获取分类
  'GET categories': () => {
    return createMockResponse(mockCategories)
  },
  
  // 获取Feed流
  'GET sessions': (params: any = {}) => {
    const { page = 1, size = 10, category_id } = params
    
    let feedList = [...mockFeedList]
    
    // 分类筛选
    if (category_id && category_id !== 'recommend') {
      feedList = feedList.filter(item => item.category.id === category_id)
    }
    
    // 分页处理
    const paginatedResult = paginate(feedList, page, size)
    
    return createMockResponse(paginatedResult)
  }
}
```

### 4.3 Mock工具函数
```typescript
// src/mock/utils/index.ts

// 创建Mock响应
export const createMockResponse = <T>(data: T, code = 200, message = 'success') => {
  return {
    statusCode: 200,
    data: {
      code,
      message,
      data,
      timestamp: new Date().toISOString()
    }
  }
}

// 创建分页响应
export const createPaginatedResponse = <T>(
  items: T[],
  total: number,
  page: number,
  size: number
) => {
  return createMockResponse({
    total,
    page,
    size,
    items
  })
}

// 分页处理
export const paginate = <T>(
  data: T[],
  page: number,
  size: number
): {
  total: number
  page: number
  size: number
  items: T[]
} => {
  const startIndex = (page - 1) * size
  const endIndex = startIndex + size
  const items = data.slice(startIndex, endIndex)
  
  return {
    total: data.length,
    page,
    size,
    items
  }
}

// ID生成器
export const generateId = (prefix: string = ''): string => {
  const timestamp = Date.now().toString(36)
  const random = Math.random().toString(36).substring(2, 8)
  return `${prefix}${prefix ? '_' : ''}${timestamp}_${random}`
}

// 随机数生成
export const randomInt = (min: number, max: number): number => {
  return Math.floor(Math.random() * (max - min + 1)) + min
}

// 随机选择数组元素
export const randomChoice = <T>(array: T[]): T => {
  return array[Math.floor(Math.random() * array.length)]
}
```

## 5. Mock数据生成器

### 5.1 动态数据生成
```typescript
// src/mock/utils/dataGenerator.ts

// 专家数据生成器
export const generateMockExperts = (count: number = 50): Expert[] => {
  const names = ['张明华', '李小红', '王建国', '刘美丽', '陈志强']
  const hospitals = ['北京协和医院', '上海华山医院', '广州中山医院', '四川华西医院']
  const departments = ['心血管内科', '肿瘤科', '神经外科', '骨科', '妇产科']
  const titles = ['主任医师', '副主任医师', '主治医师']
  
  return Array.from({ length: count }, (_, index) => ({
    id: generateId('expert'),
    name: randomChoice(names),
    avatar_url: `/static/experts/expert_${(index % 20) + 1}.png`,
    title: randomChoice(titles),
    hospital: randomChoice(hospitals),
    department: randomChoice(departments),
    specialties: generateSpecialties(),
    bio: '从事临床工作多年，具有丰富的诊疗经验...',
    stats: {
      followers_count: randomInt(100, 5000),
      sessions_count: randomInt(5, 100),
      total_views: randomInt(1000, 50000)
    },
    verified: Math.random() > 0.3,
    rating: parseFloat((4.0 + Math.random() * 1.0).toFixed(1))
  }))
}

// 生成专业领域
const generateSpecialties = (): string[] => {
  const specialties = [
    '冠心病', '高血压', '心律失常', '心力衰竭',
    '肺癌', '乳腺癌', '胃癌', '肝癌',
    '脑梗死', '脑出血', '癫痫', '帕金森病'
  ]
  
  const count = randomInt(2, 4)
  const selected = []
  
  for (let i = 0; i < count; i++) {
    const specialty = randomChoice(specialties)
    if (!selected.includes(specialty)) {
      selected.push(specialty)
    }
  }
  
  return selected
}

// 直播会话生成器
export const generateMockSessions = (count: number = 100): Session[] => {
  const titles = [
    '心血管疾病诊疗新进展',
    '肿瘤精准治疗策略',
    '神经系统疾病前沿',
    '内分泌代谢病管理'
  ]
  
  return Array.from({ length: count }, () => ({
    id: generateId('session'),
    title: randomChoice(titles),
    description: '详细讲解最新的诊断和治疗方案...',
    cover_url: `/static/sessions/session_${randomInt(1, 20)}.png`,
    expert_id: generateId('expert'),
    category_id: generateId('category'),
    start_time: generateFutureDateTime(),
    end_time: generateFutureDateTime(),
    status: randomChoice(['upcoming', 'live', 'ended']),
    stats: {
      view_count: randomInt(100, 10000),
      like_count: randomInt(10, 500),
      reserved_count: randomInt(50, 2000)
    }
  }))
}

// 生成未来时间
const generateFutureDateTime = (): string => {
  const now = new Date()
  const futureTime = new Date(now.getTime() + randomInt(1, 30) * 24 * 60 * 60 * 1000)
  return futureTime.toISOString()
}
```

## 6. Mock数据管理最佳实践

### 6.1 数据一致性
```typescript
// 数据关联管理
export const MockDataManager = {
  // 专家ID映射
  expertIds: new Set<string>(),
  
  // 房间ID映射 
  roomIds: new Set<string>(),
  
  // 确保专家ID在所有数据中一致
  ensureExpertConsistency() {
    const experts = mockExperts
    this.expertIds = new Set(experts.map(e => e.id))
    
    // 更新会话中的专家ID
    mockSessions.forEach(session => {
      if (!this.expertIds.has(session.expert_id)) {
        session.expert_id = randomChoice(Array.from(this.expertIds))
      }
    })
  }
}
```

### 6.2 Mock切换配置
```typescript
// src/mock/index.ts
export const setupMock = (config: Partial<MockConfig> = {}) => {
  const finalConfig = { ...mockConfig, ...config }
  
  // 开发环境自动启用Mock
  if (process.env.NODE_ENV === 'development') {
    finalConfig.enabled = true
  }
  
  // 生产环境禁用Mock
  if (process.env.NODE_ENV === 'production') {
    finalConfig.enabled = false
  }
  
  const interceptor = new MockInterceptor(finalConfig)
  interceptor.install()
  
  console.log('Mock服务配置:', finalConfig)
}
```

### 6.3 Mock数据版本管理
```typescript
// Mock数据版本控制
export const MOCK_DATA_VERSION = '1.0.0'

// 数据迁移
export const migrateMockData = (version: string) => {
  const currentVersion = uni.getStorageSync('mock_data_version') || '0.0.0'
  
  if (currentVersion !== MOCK_DATA_VERSION) {
    // 清除旧版本缓存数据
    uni.removeStorageSync('mock_cache')
    uni.setStorageSync('mock_data_version', MOCK_DATA_VERSION)
    console.log(`Mock数据已更新至版本 ${MOCK_DATA_VERSION}`)
  }
}
```

## 7. Mock测试和调试

### 7.1 Mock数据验证
```typescript
// Mock数据验证器
export const validateMockData = () => {
  const errors: string[] = []
  
  // 验证专家数据
  mockExperts.forEach(expert => {
    if (!expert.id || !expert.name) {
      errors.push(`专家数据不完整: ${expert.id}`)
    }
  })
  
  // 验证会话数据
  mockSessions.forEach(session => {
    if (!mockExperts.find(e => e.id === session.expert_id)) {
      errors.push(`会话关联的专家不存在: ${session.expert_id}`)
    }
  })
  
  if (errors.length > 0) {
    console.warn('Mock数据验证失败:', errors)
  } else {
    console.log('Mock数据验证通过')
  }
}
```

### 7.2 Mock调试工具
```typescript
// Mock调试面板
export const createMockDebugPanel = () => {
  // 在开发环境显示Mock状态
  if (process.env.NODE_ENV === 'development') {
    console.group('🔧 Mock Debug Info')
    console.log('Mock状态:', mockConfig.enabled ? '开启' : '关闭')
    console.log('延迟设置:', `${mockConfig.delay}ms`)
    console.log('错误率:', `${mockConfig.errorRate * 100}%`)
    console.log('数据量统计:', {
      专家: mockExperts.length,
      品牌: mockBrands.length,
      会话: mockSessions.length
    })
    console.groupEnd()
  }
}
```

## 8. 总结

Mock数据管理是前后端分离开发的重要基础设施，通过：

1. **完整的数据模型**：涵盖所有业务实体
2. **灵活的配置机制**：支持不同开发阶段的需求
3. **真实的数据关系**：保证数据一致性和完整性
4. **强大的生成工具**：快速创建大量测试数据
5. **便捷的调试功能**：提升开发效率

确保前端开发能够独立进行，同时为测试和演示提供稳定的数据支撑。
