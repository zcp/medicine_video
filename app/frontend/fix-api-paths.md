# API 路径统一修复方案

## 问题诊断

项目中 API 路径定义**不一致**：

### 老文件（不包含 /api/v1）
- ✅ room.ts: `/rooms`
- ✅ session.ts: `/sessions/{id}`
- ✅ topic.ts: `/topics`

### 新文件（包含 /api/v1）- 需要修复
- ❌ brand.ts: `/api/v1/brands` → 应改为 `/brands`
- ❌ tag.ts: `/api/v1/tags` → 应改为 `/tags`
- ❌ category.ts: `/api/v1/categories` → 应改为 `/categories`
- ❌ expert.ts: `/api/v1/experts` → 应改为 `/experts`
- ❌ homepage.ts: `/api/v1/homepage/rooms` → 应改为 `/homepage/rooms`
- ❌ watchHistory.ts: `/api/v1/sessions/{id}/watch` → 应改为 `/sessions/{id}/watch`
- ❌ favorite.ts: `/api/v1/users/me/favorites` → 应改为 `/users/me/favorites`
- ❌ subscription.ts: `/api/v1/users/me/subscriptions` → 应改为 `/users/me/subscriptions`
- ❌ sessionTags.ts: `/api/v1/sessions/{id}/tags` → 应改为 `/sessions/{id}/tags`
- ❌ brandTopics.ts: `/api/v1/admin/brands` → 应改为 `/admin/brands`
- ❌ featured.ts: `/api/v1/featured-content` → 应改为 `/featured-content`
- ❌ playback.ts: `/api/v1/playback/stats` → 应改为 `/playback/stats`

## 正确的配置

```.env
VITE_BASE_API_URL=http://124.220.235.226:8000
```

## URL 拼接逻辑

```
BASE_URL = 'http://124.220.235.226:8000'
相对路径 = '/rooms'
最终 URL = 'http://124.220.235.226:8000/rooms'
```

⚠️ 注意：后端 API 路径是 `/api/v1/rooms`，所以实际应该是：

```
相对路径应该写成 = '/api/v1/rooms'
最终 URL = 'http://124.220.235.226:8000/api/v1/rooms' ✅
```

## 等等！我发现问题了！

查看 room.ts：
```typescript
export const getRoomList = (params) => {
  return get<>('/rooms', params);  // ❌ 这会变成 http://124.220.235.226:8000/rooms
};
```

这样请求会失败！因为后端真实路径是 `/api/v1/rooms`

## 最终方案决策

需要检查后端实际的 API 路径：
1. 如果后端路径是 `/rooms` → BASE_URL应该包含 `/api/v1`
2. 如果后端路径是 `/api/v1/rooms` → BASE_URL不应该包含 `/api/v1`

根据你昨天的测试结果：
```
✅ http://124.220.235.226:8000/api/v1/rooms - 成功
```

所以后端路径确实包含 `/api/v1`！

那么有两个方案：

### 方案 A：BASE_URL 包含 /api/v1
```bash
VITE_BASE_API_URL=http://124.220.235.226:8000/api/v1
```

所有 API 文件都不写 `/api/v1`：
```typescript
// room.ts
get('/rooms')  → http://124.220.235.226:8000/api/v1/rooms ✅

// brand.ts (需要修改)
get('/brands')  → http://124.220.235.226:8000/api/v1/brands ✅
```

### 方案 B：BASE_URL 不包含 /api/v1
```bash
VITE_BASE_API_URL=http://124.220.235.226:8000
```

所有 API 文件都要写完整路径：
```typescript
// room.ts (需要修改)
get('/api/v1/rooms')  → http://124.220.235.226:8000/api/v1/rooms ✅

// brand.ts (已经是对的)
get('/api/v1/brands')  → http://124.220.235.226:8000/api/v1/brands ✅
```

## 推荐方案 A（更简洁）

修改步骤：
1. `.env` 文件：`VITE_BASE_API_URL=http://124.220.235.226:8000/api/v1`
2. 修改 brand.ts 等新文件，移除所有 `/api/v1` 前缀
3. room.ts, session.ts, topic.ts 不需要修改（已经正确）

这样所有 API 调用都统一，简洁易维护。
