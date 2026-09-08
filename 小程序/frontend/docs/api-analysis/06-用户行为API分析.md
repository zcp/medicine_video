# 用户行为API完整分析

## 📋 概述

用户行为API包括收藏、订阅、观看历史、关注专家等功能，全部通过 Core Service 处理。

## 📁 相关文件

- `src/api/favorites.ts`
- `src/api/subscriptions.ts`
- `src/api/history.ts`
- `src/api/expert.ts`（关注专家部分）
- **配置**: `src/config/api.ts` (API_PATHS.USER_BEHAVIOR)

## 🌐 服务信息

- **服务**: Core Service
- **Base URL**: `https://mp.dayilive.com/api/core`
- **路由判断**: `/users/me/...` 路径不以 `/me/` 开头，均路由到 Core Service ✓

---

## 🔗 API接口详细分析

### 收藏管理

#### 1. 添加收藏
- **函数名**: `addFavorite`
- **HTTP方法**: POST
- **路径**: `/users/me/favorites`
- **完整URL**: `https://mp.dayilive.com/api/core/users/me/favorites`
- **请求体**: `{ room_id: string }`

#### 2. 获取收藏列表
- **函数名**: `getFavoriteList`
- **HTTP方法**: GET
- **路径**: `/users/me/favorites`
- **完整URL**: `https://mp.dayilive.com/api/core/users/me/favorites`

#### 3. 取消收藏
- **函数名**: `removeFavorite`
- **HTTP方法**: DELETE
- **路径**: `/users/me/favorites/{roomId}`
- **完整URL**: `https://mp.dayilive.com/api/core/users/me/favorites/{roomId}`

### 订阅管理

#### 4. 添加订阅
- **函数名**: `addSubscription`
- **HTTP方法**: POST
- **路径**: `/users/me/subscriptions`
- **完整URL**: `https://mp.dayilive.com/api/core/users/me/subscriptions`
- **请求体**: `{ room_id: string }`

#### 5. 获取订阅列表
- **函数名**: `getSubscriptionList`
- **HTTP方法**: GET
- **路径**: `/users/me/subscriptions`
- **完整URL**: `https://mp.dayilive.com/api/core/users/me/subscriptions`

#### 6. 取消订阅
- **函数名**: `removeSubscription`
- **HTTP方法**: DELETE
- **路径**: `/users/me/subscriptions/{roomId}`
- **完整URL**: `https://mp.dayilive.com/api/core/users/me/subscriptions/{roomId}`

#### 7. 检查订阅状态 ✅
- **函数名**: `checkSubscription`
- **HTTP方法**: GET
- **路径**: `/users/me/subscriptions/check/{targetId}`
- **完整URL**: `https://mp.dayilive.com/api/core/users/me/subscriptions/check/{targetId}`

#### 8. 清除订阅历史 ✅
- **函数名**: `clearSubscriptionHistory`
- **HTTP方法**: POST
- **路径**: `/users/me/subscriptions/clear-history`
- **完整URL**: `https://mp.dayilive.com/api/core/users/me/subscriptions/clear-history`

### 观看历史

#### 9. 记录观看历史
- **函数名**: `recordWatchHistory`
- **HTTP方法**: POST
- **路径**: `/users/me/watch-history`
- **完整URL**: `https://mp.dayilive.com/api/core/users/me/watch-history`

#### 10. 获取观看历史列表
- **函数名**: `getWatchHistory`
- **HTTP方法**: GET
- **路径**: `/users/me/watch-history`
- **完整URL**: `https://mp.dayilive.com/api/core/users/me/watch-history`

#### 11. 删除单条观看历史
- **函数名**: `deleteWatchHistory`
- **HTTP方法**: DELETE
- **路径**: `/users/me/watch-history/{historyId}`
- **完整URL**: `https://mp.dayilive.com/api/core/users/me/watch-history/{historyId}`

#### 12. 清空观看历史 ✅
- **函数名**: `clearWatchHistory`
- **HTTP方法**: POST
- **路径**: `/users/me/watch-history/clear`
- **完整URL**: `https://mp.dayilive.com/api/core/users/me/watch-history/clear`

---

## 🗺️ 路径映射表

| 函数名 | 方法 | 相对路径 | 完整URL |
|-------|------|---------|---------|
| `addFavorite` | POST | `/users/me/favorites` | `https://mp.dayilive.com/api/core/users/me/favorites` |
| `getFavoriteList` | GET | `/users/me/favorites` | `https://mp.dayilive.com/api/core/users/me/favorites` |
| `removeFavorite` | DELETE | `/users/me/favorites/{roomId}` | `https://mp.dayilive.com/api/core/users/me/favorites/{roomId}` |
| `addSubscription` | POST | `/users/me/subscriptions` | `https://mp.dayilive.com/api/core/users/me/subscriptions` |
| `getSubscriptionList` | GET | `/users/me/subscriptions` | `https://mp.dayilive.com/api/core/users/me/subscriptions` |
| `removeSubscription` | DELETE | `/users/me/subscriptions/{roomId}` | `https://mp.dayilive.com/api/core/users/me/subscriptions/{roomId}` |
| `checkSubscription` | GET | `/users/me/subscriptions/check/{targetId}` | `https://mp.dayilive.com/api/core/users/me/subscriptions/check/{targetId}` |
| `clearSubscriptionHistory` | POST | `/users/me/subscriptions/clear-history` | `https://mp.dayilive.com/api/core/users/me/subscriptions/clear-history` |
| `recordWatchHistory` | POST | `/users/me/watch-history` | `https://mp.dayilive.com/api/core/users/me/watch-history` |
| `getWatchHistory` | GET | `/users/me/watch-history` | `https://mp.dayilive.com/api/core/users/me/watch-history` |
| `deleteWatchHistory` | DELETE | `/users/me/watch-history/{historyId}` | `https://mp.dayilive.com/api/core/users/me/watch-history/{historyId}` |
| `clearWatchHistory` | POST | `/users/me/watch-history/clear` | `https://mp.dayilive.com/api/core/users/me/watch-history/clear` |

---

**分析完成时间**: 2026-04-22
**API数量**: 12个
**主要服务**: Core Service