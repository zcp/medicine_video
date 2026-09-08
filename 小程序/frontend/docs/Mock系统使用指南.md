# Mock API 系统使用指南

**版本**：v1.0  
**创建时间**：2024-12-01  
**适用环境**：开发环境

---

## 📋 概述

Mock API 系统允许前端在后端 API 未实现时，使用模拟数据进行开发和测试。系统会自动拦截 API 请求，返回预设的模拟数据。

---

## 🚀 快速开始

### 1. Mock 系统已自动启用

Mock 系统在 `src/main.ts` 中自动初始化，**开发环境默认启用**：

```typescript
// src/main.ts
if (process.env.NODE_ENV === 'development') {
  setupMock()
}
```

### 2. 运行项目

```bash
npm run dev:mp-weixin
```

控制台会显示：
```
🎭 初始化 Mock API...
  ✓ Tags Mock 已注册
  ✓ Brands Mock 已注册
  ✓ Notifications Mock 已注册
  ✓ Favorites Mock 已注册
✅ Mock API 已启用 (XX 个规则)
📝 Mock 请求日志已启用
```

### 3. 查看 Mock 日志

每次 API 请求都会在控制台显示：
```
🎭 Mock Request: GET /api/v1/tags/popular
✅ Mock Response: { code: 200, data: [...] }
```

---

## ⚙️ 配置选项

### 修改 Mock 配置

编辑 `src/mock/index.ts`：

```typescript
export const mockConfig = {
  enabled: true,        // 是否启用 Mock
  delay: 300,          // 模拟网络延迟（毫秒）
  logRequests: true    // 是否打印请求日志
}
```

**配置说明**：
- `enabled`: 设为 `false` 可临时禁用 Mock，使用真实 API
- `delay`: 调整延迟可模拟不同网络环境（0-2000ms）
- `logRequests`: 关闭日志可减少控制台输出

---

## 📦 已实现的 Mock 模块

### 1. Tags 模块（4个接口）

| 接口 | 路径 | 方法 | 说明 |
|------|------|------|------|
| 获取标签详情 | `/api/v1/tags/:tagId` | GET | 返回单个标签信息 |
| 搜索标签 | `/api/v1/tags/search` | GET | 关键词搜索标签 |
| 获取热门标签 | `/api/v1/tags/popular` | GET | 返回热门标签列表 |
| 获取标签统计 | `/api/v1/tags/statistics` | GET | 返回统计数据 |

**使用示例**：
```typescript
import { useTagsStore } from '@/store/tags'

const tagsStore = useTagsStore()
// 会自动使用 Mock 数据
await tagsStore.fetchPopularTags(10)
```

---

### 2. Brands 模块（3个接口）

| 接口 | 路径 | 方法 | 说明 |
|------|------|------|------|
| 获取品牌详情 | `/api/v1/brands/:brandId` | GET | 返回品牌详情和关联专题 |
| 获取热门品牌 | `/api/v1/brands/popular` | GET | 返回热门品牌 |
| 获取品牌统计 | `/api/v1/brands/statistics` | GET | 返回统计数据 |

---

### 3. Notifications 模块（8个接口）

| 接口 | 路径 | 方法 | 说明 |
|------|------|------|------|
| 获取通知详情 | `/api/v1/users/me/notifications/:id` | GET | 单条通知详情 |
| 全部已读 | `/api/v1/users/me/notifications/read-all` | POST | 全部标记为已读 |
| 批量已读 | `/api/v1/users/me/notifications/batch-read` | POST | 批量标记 |
| 删除通知 | `/api/v1/users/me/notifications/:id` | DELETE | 删除单条 |
| 未读数量 | `/api/v1/users/me/notifications/unread-count` | GET | 获取未读数 |
| 通知统计 | `/api/v1/users/me/notifications/statistics` | GET | 统计信息 |
| 获取设置 | `/api/v1/users/me/notification-settings` | GET | 通知偏好 |
| 更新设置 | `/api/v1/users/me/notification-settings` | PATCH | 更新偏好 |

---

### 4. Favorites 模块（6个接口）

| 接口 | 路径 | 方法 | 说明 |
|------|------|------|------|
| 检查收藏状态 | `/api/v1/users/me/favorites/check` | GET | 是否已收藏 |
| 收藏统计 | `/api/v1/users/me/favorites/statistics` | GET | 统计数据 |
| 创建文件夹 | `/api/v1/users/me/favorite-folders` | POST | 新建收藏夹 |
| 文件夹列表 | `/api/v1/users/me/favorite-folders` | GET | 所有文件夹 |
| 批量收藏 | `/api/v1/users/me/favorites/batch` | POST | 批量添加 |
| 批量取消 | `/api/v1/users/me/favorites/batch` | DELETE | 批量删除 |

---

## 🔧 自定义 Mock 数据

### 修改现有 Mock 数据

编辑对应的模块文件，例如 `src/mock/modules/tags.ts`：

```typescript
// 修改 Mock 标签数据
const mockTags = [
  { 
    id: 'tag_1', 
    name: '心血管', 
    description: '心血管相关内容', 
    usage_count: 1000 
  },
  // 添加更多标签...
]
```

### 添加新的 Mock 规则

在对应模块文件中使用 `registerMockRule`：

```typescript
import { registerMockRule, mockSuccess } from '../index'

// 注册新规则
registerMockRule({
  pattern: '/api/v1/custom-endpoint',  // 可以是字符串或正则
  method: 'GET',
  handler: (params) => {
    // 处理逻辑
    return mockSuccess({
      message: 'Custom data',
      data: []
    })
  }
})
```

---

## 🎯 使用场景

### 场景 1：前端独立开发

后端 API 未就绪，前端使用 Mock 数据先完成页面和交互：

```typescript
// 在 store 中正常调用
const tagsStore = useTagsStore()
await tagsStore.fetchPopularTags()  // 自动使用 Mock 数据
```

### 场景 2：测试特定数据

临时修改 Mock 数据，测试边界情况：

```typescript
// src/mock/modules/notifications.ts
let mockNotifications = [
  // 添加 100 条测试数据
  ...Array(100).fill(null).map((_, i) => ({
    id: `notif_${i}`,
    title: `测试通知 ${i}`,
    is_read: i % 2 === 0
  }))
]
```

### 场景 3：模拟网络延迟

测试加载状态和骨架屏：

```typescript
// src/mock/index.ts
export const mockConfig = {
  enabled: true,
  delay: 2000,  // 2秒延迟，测试 loading 效果
  logRequests: true
}
```

### 场景 4：切换真实 API

后端 API 就绪后，禁用 Mock：

```typescript
// src/mock/index.ts
export const mockConfig = {
  enabled: false,  // 禁用 Mock，使用真实 API
  delay: 300,
  logRequests: true
}
```

---

## 📝 Mock 数据格式

所有 Mock 响应遵循统一格式：

```typescript
{
  code: 200,              // 状态码
  message: "success",     // 消息
  data: { ... },          // 数据
  timestamp: "2024-12-01T00:00:00Z"  // 时间戳
}
```

### 成功响应

```typescript
import { mockSuccess } from '@/mock'

mockSuccess({
  id: '123',
  name: '测试数据'
})
```

### 错误响应

```typescript
import { mockError } from '@/mock'

mockError(2001, '资源不存在')
```

### 分页响应

```typescript
import { mockPaginatedResponse } from '@/mock'

mockPaginatedResponse(items, page, size)
```

---

## 🐛 调试技巧

### 1. 查看所有 Mock 规则

在浏览器控制台执行：

```javascript
console.log('Mock 规则数量:', mockRules.length)
```

### 2. 临时禁用单个模块

注释掉对应模块的注册：

```typescript
// src/mock/index.ts
export function setupMock() {
  setupTagsMock()
  // setupBrandsMock()  // 临时禁用品牌模块
  setupNotificationsMock()
  setupFavoritesMock()
}
```

### 3. 检查请求是否被 Mock

查看控制台日志：
- 有 `🎭 Mock Request` 说明被 Mock 拦截
- 没有日志说明走了真实 API

### 4. 对比 Mock 和真实数据

```typescript
// 临时切换测试
mockConfig.enabled = false  // 使用真实 API
// 测试完切回
mockConfig.enabled = true   // 使用 Mock
```

---

## ⚠️ 注意事项

### 1. 生产环境自动禁用

Mock 系统只在开发环境启用，生产环境自动禁用：

```typescript
if (process.env.NODE_ENV === 'development') {
  setupMock()  // 仅开发环境
}
```

### 2. Mock 数据仅供前端使用

- Mock 数据在内存中，刷新页面会重置
- 不要依赖 Mock 数据的持久性
- 切换到真实 API 前要做充分测试

### 3. 及时更新 Mock 数据

后端 API 修改后，同步更新 Mock 数据格式：
- 字段名变更
- 数据类型调整
- 新增/删除字段

### 4. URL 匹配规则

Mock 使用字符串包含或正则匹配：

```typescript
// 字符串匹配（包含即可）
pattern: '/api/v1/tags/popular'

// 正则匹配（精确控制）
pattern: /\/api\/v1\/tags\/[^/]+$/
```

---

## 🔄 从 Mock 切换到真实 API

### 步骤 1：禁用 Mock

```typescript
// src/mock/index.ts
export const mockConfig = {
  enabled: false,  // 关闭 Mock
  delay: 300,
  logRequests: false
}
```

### 步骤 2：配置真实 API 地址

```typescript
// src/utils/request.ts
this.baseURL = 'https://api.yourdomain.com'
```

### 步骤 3：测试所有功能

确保所有使用 Mock 的功能都能正常工作。

### 步骤 4：取消注释 Store 方法

之前注释的方法现在可以启用：

```typescript
// src/store/tags.ts
// 取消注释
async fetchPopularTags(limit: number = 20): Promise<void> {
  // ... 实现
}
```

---

## 📚 相关文档

- [前端需要的缺失API清单.md](./前端需要的缺失API清单.md) - 完整的 API 接口定义
- [后端新增api接口和模块设计文档-v2.md](./后端新增api接口和模块设计文档-v2.md) - 后端 API 文档

---

## 🆘 常见问题

### Q1: Mock 没有生效？

**检查清单**：
1. ✅ `mockConfig.enabled` 是否为 `true`
2. ✅ URL 匹配规则是否正确
3. ✅ 查看控制台是否有 Mock 日志
4. ✅ 确认是开发环境

### Q2: 如何添加新的 Mock 模块？

1. 在 `src/mock/modules/` 创建新文件
2. 使用 `registerMockRule` 注册规则
3. 在 `src/mock/index.ts` 的 `setupMock()` 中调用

### Q3: Mock 数据刷新后丢失？

Mock 数据在内存中，刷新页面会重置。需要持久化的测试数据应该：
- 使用真实 API
- 或在 Mock 初始化时从 localStorage 读取

### Q4: 可以部分使用 Mock 吗？

可以！只注释不需要 Mock 的模块：

```typescript
setupTagsMock()       // 使用 Mock
// setupBrandsMock()  // 使用真实 API
```

---

**更新记录**：
- v1.0 (2024-12-01): 初始版本，支持 Tags、Brands、Notifications、Favorites 四个模块
