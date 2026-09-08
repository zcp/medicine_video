# 系统功能API完整分析

## 📋 概述

系统功能API包括全局搜索、播放统计、通知（含管理员）等功能。

## 📁 相关文件

- `src/api/search.ts`
- `src/api/notifications.ts`
- **配置**: `src/config/api.ts` (API_PATHS.OTHER / API_PATHS.NOTIFICATION / API_PATHS.ADMIN)

---

## 🔗 API接口详细分析

### 搜索功能

#### 1. 全局搜索 ✅
- **函数名**: `globalSearch`
- **HTTP方法**: GET
- **相对路径**: `/search`
- **完整URL**: `https://mp.dayilive.com/api/core/search`
- **参数**: `q: string, type?: string, page?: number, size?: number`
- **用途**: 全局搜索（房间/专家/品牌等）

#### 2. 按关键词搜索房间
- **函数名**: `searchRooms`
- **HTTP方法**: GET
- **相对路径**: `/rooms?q=...`
- **完整URL**: `https://mp.dayilive.com/api/core/rooms?q={keyword}`
- **用途**: 房间列表带关键词过滤

### 播放统计

#### 3. 播放统计上报
- **配置常量**: `OTHER.PLAYBACK_STATS`
- **HTTP方法**: POST
- **相对路径**: `/playback/stats`
- **完整URL**: `https://mp.dayilive.com/api/core/playback/stats`
- **用途**: 上报分享/播放统计数据

### 通知模块（路径路由说明）

> **路由分析**: `/users/me/notifications` 不以 `/me/` `/auth` 开头，路由到 Core Service。
> 完整 URL: `https://mp.dayilive.com/api/core/users/me/notifications` ✓ 无双前缀问题

#### 4. 获取通知列表
- **函数名**: `getNotificationList`
- **HTTP方法**: GET
- **相对路径**: `/users/me/notifications`
- **完整URL**: `https://mp.dayilive.com/api/core/users/me/notifications`

#### 5. 标记通知已读
- **函数名**: `markNotificationAsRead`
- **HTTP方法**: POST
- **相对路径**: `/users/me/notifications/{id}/read`
- **完整URL**: `https://mp.dayilive.com/api/core/users/me/notifications/{id}/read`

### 管理员通知管理

#### 6. 管理员通知列表
- **HTTP方法**: GET
- **相对路径**: `/admin/notifications`
- **完整URL**: `https://mp.dayilive.com/api/core/admin/notifications`

#### 7. 创建通知
- **HTTP方法**: POST
- **相对路径**: `/admin/notifications`
- **完整URL**: `https://mp.dayilive.com/api/core/admin/notifications`

#### 8. 批量创建通知
- **HTTP方法**: POST
- **相对路径**: `/admin/notifications/batch`
- **完整URL**: `https://mp.dayilive.com/api/core/admin/notifications/batch`

---

## 🗺️ 路径映射表

| 函数名 | 方法 | 相对路径 | 完整URL |
|-------|------|---------|---------|
| `globalSearch` | GET | `/search` | `https://mp.dayilive.com/api/core/search` |
| `searchRooms` | GET | `/rooms?q=...` | `https://mp.dayilive.com/api/core/rooms?q=...` |
| — | POST | `/playback/stats` | `https://mp.dayilive.com/api/core/playback/stats` |
| `getNotificationList` | GET | `/users/me/notifications` | `https://mp.dayilive.com/api/core/users/me/notifications` |
| `markNotificationAsRead` | POST | `/users/me/notifications/{id}/read` | `https://mp.dayilive.com/api/core/users/me/notifications/{id}/read` |
| — | GET | `/admin/notifications` | `https://mp.dayilive.com/api/core/admin/notifications` |
| — | POST | `/admin/notifications` | `https://mp.dayilive.com/api/core/admin/notifications` |
| — | POST | `/admin/notifications/batch` | `https://mp.dayilive.com/api/core/admin/notifications/batch` |

---

**分析完成时间**: 2026-04-22
**API数量**: 8个
**主要服务**: Core Service