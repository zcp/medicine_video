# API完整分析总览

## 📋 项目概述

本文档提供了Live-Saas-Wechat项目中所有API接口的完整分析，包括每个API的详细信息、完整URL路径、使用位置和函数映射。

## 🗂️ API文件结构

项目共 **21个API文件**，均采用单文件独立模块方式（`all-apis.ts` 和 `index.ts` 已删除）。

### 功能模块API文件
1. **认证相关**: `auth.ts`
2. **用户管理**: `user.ts`
3. **房间管理**: `room.ts`
4. **专家管理**: `expert.ts`
5. **会话管理**: `session.ts`
6. **收藏功能**: `favorites.ts`
7. **订阅功能**: `subscriptions.ts`
8. **观看历史**: `history.ts`
9. **通知系统**: `notifications.ts`
10. **品牌管理**: `brands.ts`
11. **分类管理**: `categories.ts`
12. **搜索功能**: `search.ts`
13. **标签管理**: `tags.ts`
14. **消息系统**: `messages.ts`
15. **标签页管理**: `tabs.ts`
16. **会话标签**: `sessionTags.ts`
17. **设置管理**: `settings.ts`
18. **精选内容**: `featuredContent.ts`
19. **导入功能**: `import.ts`
20. **专题管理**: `topics.ts`

## 🌐 服务架构

项目采用微服务架构，主要包含两个服务。

### 1. Users Service (用户服务)
- **Base URL（生产）**: `https://mp.dayilive.com/api/users`
- **Base URL（本地）**: `http://localhost:8080/api/users`
- **负责功能**: 用户认证、用户信息管理、用户偏好

### 2. Core Service (核心服务)
- **Base URL（生产）**: `https://mp.dayilive.com/api/core`
- **Base URL（本地）**: `http://localhost:8080/api/core`
- **负责功能**: 房间管理、专家管理、会话管理、用户行为、内容管理等

## 📊 API统计信息

| 分类 | API端点数 | 主要功能 |
|------|-----------|----------|
| 认证相关 | 9 | 登录、注册、验证码、密码重置等 |
| 用户管理 | 8 | 用户信息、头像上传、偏好设置等 |
| 房间管理 | 18 | 房间CRUD、封面、专家/专题/收藏状态、消息、Tab |
| 专家管理 | 16 | 专家信息、关注检查、管理员操作 |
| 会话管理 | 17 | 会话CRUD、观众/流地址、标签、导入 |
| 用户行为 | 12 | 收藏、订阅/检查、关注专家、观看历史/清空 |
| 内容管理 | 37 | 品牌/分类/标签/焦点图/Tab/专题管理 |
| 系统功能 | 8 | 全局搜索、通知、播放统计 |
| **总计** | **约 125个** | 严格对齐后端文档 |

## 🔗 URL路径拼接机制

### 机制说明
1. **环境变量**: 提供基础URL
   - `VITE_BASE_API_URL=https://mp.dayilive.com/api/core`（Core Service）
   - `VITE_AUTH_API_URL=https://mp.dayilive.com/api/users`（Users Service）
   - `VITE_API_PATH_PREFIX=`（空，不追加前缀）

2. **API_PATHS**: 定义相对路径（如 `/rooms`, `/me`, `/auth/login`）

3. **路由判断** `shouldUseUsersGateway(path)`：
   - 路径以 `/auth`、`/me`、`/register`、`/admin/users` 开头 → Users Service
   - 其他路径 → Core Service

### 路径拼接示例
```
Core Service:
  Base URL: https://mp.dayilive.com/api/core
  Path:     /rooms
  Final:    https://mp.dayilive.com/api/core/rooms

Users Service:
  Base URL: https://mp.dayilive.com/api/users
  Path:     /auth/login
  Final:    https://mp.dayilive.com/api/users/auth/login
```

> ⚠️ 注意：`/users/me/notifications` 不以 `/me/` 开头，会路由到 Core Service：
> → `https://mp.dayilive.com/api/core/users/me/notifications` ✓（无双前缀问题）

## 📁 文档结构

1. **01-认证API分析.md** - 认证相关API详细分析
2. **02-用户API分析.md** - 用户管理API详细分析
3. **03-房间API分析.md** - 房间管理API详细分析
4. **04-专家API分析.md** - 专家管理API详细分析
5. **05-会话API分析.md** - 会话管理API详细分析
6. **06-用户行为API分析.md** - 收藏、订阅、历史API分析
7. **07-内容管理API分析.md** - 品牌、分类、标签、专题、Tab API分析
8. **08-系统功能API分析.md** - 搜索、通知、播放统计等API分析
9. **09-使用位置映射表.md** - 所有API函数的使用位置
10. **10-完整URL路径表.md** - 所有API的完整URL路径

## ⚠️ 修复记录（2026-04-22 最终版）

### ✅ 已修复

| 文件 | 问题 | 修复 |
|------|------|------|
| `notifications.ts` | `markNotificationAsRead` 用 PATCH | 改为 **POST** |
| `notifications.ts` | `markAllNotificationsAsRead`/`deleteNotification`/`getUnreadCount` 不在文档 | 全部删除 |
| `subscriptions.ts` | 请求体格式不符 | 改为 `{ room_id }` |
| `config/api.ts` | `ADMIN.UPDATE_TAB`/`DELETE_TAB` 带多余 roomId | 改为 `/admin/tabs/{tabId}` |
| `config/api.ts` | 焦点图 admin 增删改路径错误 | 改为 `/featured-content/admin[/{id}]` |
| `tabs.ts` | `updateTab`/`deleteTab` 函数签名携带多余 roomId | 修正为只需 tabId |
| `CreateLive.vue` | 调用 `updateTab(roomId, tabId, data)` 旧签名 | 修正为 `updateTab(tabId, data)` |
| `search.ts` | 缺少 `/search` 全局搜索端点 | 新增 `globalSearch` 函数 |
| `history.ts` | 缺少 `POST /users/me/watch-history/clear` | 新增 `clearWatchHistory` |
| `subscriptions.ts` | 缺少 `checkSubscription`、`clearSubscriptionHistory` | 恢复/新增 |
| `room.ts` | 缺少 `getRoomExperts`、`getRoomTopics`、`checkRoomFavorited` | 恢复 |
| `expert.ts` | 缺少 `getExpertFollowStatus` | 恢复 |

### ✅ 当前状态：所有端点严格对齐后端文档

---

**更新时间**: 2026-04-22
**合规状态**: 所有端点严格对齐后端文档，无多余/缺失端点