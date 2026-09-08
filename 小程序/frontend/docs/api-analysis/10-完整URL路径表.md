# 完整URL路径表

## 环境配置

| 变量 | 值 | 说明 |
|------|-----|------|
| `VITE_BASE_API_URL` | `https://mp.dayilive.com/api/core` | Core Service 基础URL |
| `VITE_AUTH_API_URL` | `https://mp.dayilive.com/api/users` | Users Service 基础URL |
| `VITE_MEDIA_BASE_URL` | `https://mp.dayilive.com` | 媒体资源基础URL |

## 路由规则

`shouldUseUsersGateway(path)` 返回 true 的路径 → Users Service；其余 → Core Service：

| 路径前缀 | 路由目标 |
|---------|---------|
| `/auth/...` | Users Service |
| `/me` 或 `/me/...` | Users Service |
| `/register` | Users Service |
| `/admin/users/...` | Users Service |
| 其他（`/rooms`, `/sessions`, `/users/me/...` 等） | Core Service |

---

## 一、Users Service API

**Base URL**: `https://mp.dayilive.com/api/users`

| 方法 | 相对路径 | 完整URL | 说明 |
|------|---------|---------|------|
| GET | `/auth/captcha` | `https://mp.dayilive.com/api/users/auth/captcha` | 获取验证码 |
| POST | `/auth/verification-codes` | `https://mp.dayilive.com/api/users/auth/verification-codes` | 发送验证码 |
| POST | `/auth/login` | `https://mp.dayilive.com/api/users/auth/login` | 用户登录 |
| POST | `/auth/logout` | `https://mp.dayilive.com/api/users/auth/logout` | 用户登出 |
| POST | `/auth/refresh` | `https://mp.dayilive.com/api/users/auth/refresh` | 刷新Token |
| POST | `/auth/password-reset-request` | `https://mp.dayilive.com/api/users/auth/password-reset-request` | 请求密码重置 |
| POST | `/auth/password-reset` | `https://mp.dayilive.com/api/users/auth/password-reset` | 执行密码重置 |
| POST | `/auth/sso-login` | `https://mp.dayilive.com/api/users/auth/sso-login` | SSO登录 |
| POST | `/register` | `https://mp.dayilive.com/api/users/register` | 用户注册 |
| GET | `/me` | `https://mp.dayilive.com/api/users/me` | 获取当前用户 |
| PATCH | `/me` | `https://mp.dayilive.com/api/users/me` | 更新个人资料 |
| DELETE | `/me` | `https://mp.dayilive.com/api/users/me` | 注销账号 |
| POST | `/me/avatar` | `https://mp.dayilive.com/api/users/me/avatar` | 上传头像 |
| POST | `/me/phone` | `https://mp.dayilive.com/api/users/me/phone` | 绑定/换绑手机 |
| POST | `/me/password` | `https://mp.dayilive.com/api/users/me/password` | 修改密码 |
| GET | `/me/preferences` | `https://mp.dayilive.com/api/users/me/preferences` | 获取用户偏好 |
| PATCH | `/me/preferences` | `https://mp.dayilive.com/api/users/me/preferences` | 更新用户偏好 |

---

## 二、Core Service API

**Base URL**: `https://mp.dayilive.com/api/core`

### 房间管理

| 方法 | 相对路径 | 完整URL |
|------|---------|---------|
| GET | `/rooms` | `https://mp.dayilive.com/api/core/rooms` |
| POST | `/rooms` | `https://mp.dayilive.com/api/core/rooms` |
| GET | `/homepage/rooms` | `https://mp.dayilive.com/api/core/homepage/rooms` |
| GET | `/rooms/{id}` | `https://mp.dayilive.com/api/core/rooms/{id}` |
| PATCH | `/rooms/{id}` | `https://mp.dayilive.com/api/core/rooms/{id}` |
| DELETE | `/rooms/{id}` | `https://mp.dayilive.com/api/core/rooms/{id}` |
| GET | `/rooms/{id}/sessions` | `https://mp.dayilive.com/api/core/rooms/{id}/sessions` |
| GET | `/rooms/{id}/sub-venues` | `https://mp.dayilive.com/api/core/rooms/{id}/sub-venues` |
| POST | `/rooms/{id}/cover` | `https://mp.dayilive.com/api/core/rooms/{id}/cover` |
| GET | `/rooms/{id}/brands` | `https://mp.dayilive.com/api/core/rooms/{id}/brands` |
| GET | `/rooms/{id}/experts` | `https://mp.dayilive.com/api/core/rooms/{id}/experts` |
| GET | `/rooms/{id}/topics` | `https://mp.dayilive.com/api/core/rooms/{id}/topics` |
| GET | `/rooms/{id}/is-favorited` | `https://mp.dayilive.com/api/core/rooms/{id}/is-favorited` |
| GET | `/rooms/{id}/messages` | `https://mp.dayilive.com/api/core/rooms/{id}/messages` |
| POST | `/rooms/{id}/messages` | `https://mp.dayilive.com/api/core/rooms/{id}/messages` |
| GET | `/rooms/{id}/tabs` | `https://mp.dayilive.com/api/core/rooms/{id}/tabs` |
| POST | `/rooms/batch-status` | `https://mp.dayilive.com/api/core/rooms/batch-status` |

### 场次管理

| 方法 | 相对路径 | 完整URL |
|------|---------|---------|
| POST | `/rooms/{id}/sessions` | `https://mp.dayilive.com/api/core/rooms/{id}/sessions` |
| POST | `/rooms/{id}/sessions/import` | `https://mp.dayilive.com/api/core/rooms/{id}/sessions/import` |
| GET | `/sessions/{id}` | `https://mp.dayilive.com/api/core/sessions/{id}` |
| PATCH | `/sessions/{id}` | `https://mp.dayilive.com/api/core/sessions/{id}` |
| DELETE | `/sessions/{id}` | `https://mp.dayilive.com/api/core/sessions/{id}` |
| POST | `/sessions/{id}/start` | `https://mp.dayilive.com/api/core/sessions/{id}/start` |
| POST | `/sessions/{id}/end` | `https://mp.dayilive.com/api/core/sessions/{id}/end` |
| GET | `/sessions/{id}/viewers` | `https://mp.dayilive.com/api/core/sessions/{id}/viewers` |
| GET | `/sessions/{id}/stream-url` | `https://mp.dayilive.com/api/core/sessions/{id}/stream-url` |
| GET | `/sessions/{id}/tags` | `https://mp.dayilive.com/api/core/sessions/{id}/tags` |
| GET | `/sessions/search` | `https://mp.dayilive.com/api/core/sessions/search` |
| POST | `/sessions/{id}/watch` | `https://mp.dayilive.com/api/core/sessions/{id}/watch` |

### 专家管理

| 方法 | 相对路径 | 完整URL |
|------|---------|---------|
| GET | `/experts` | `https://mp.dayilive.com/api/core/experts` |
| GET | `/featured-experts` | `https://mp.dayilive.com/api/core/featured-experts` |
| GET | `/experts/{id}` | `https://mp.dayilive.com/api/core/experts/{id}` |
| GET | `/experts/{id}/sessions` | `https://mp.dayilive.com/api/core/experts/{id}/sessions` |
| GET | `/experts/{id}/is-followed` | `https://mp.dayilive.com/api/core/experts/{id}/is-followed` |
| GET | `/professors/{id}/content` | `https://mp.dayilive.com/api/core/professors/{id}/content` |
| GET | `/sessions/{id}/experts` | `https://mp.dayilive.com/api/core/sessions/{id}/experts` |
| POST | `/sessions/{id}/experts` | `https://mp.dayilive.com/api/core/sessions/{id}/experts` |

### 用户行为

| 方法 | 相对路径 | 完整URL |
|------|---------|---------|
| POST | `/users/me/followed-experts` | `https://mp.dayilive.com/api/core/users/me/followed-experts` |
| GET | `/users/me/followed-experts` | `https://mp.dayilive.com/api/core/users/me/followed-experts` |
| DELETE | `/users/me/followed-experts/{id}` | `https://mp.dayilive.com/api/core/users/me/followed-experts/{id}` |
| POST | `/users/me/favorites` | `https://mp.dayilive.com/api/core/users/me/favorites` |
| GET | `/users/me/favorites` | `https://mp.dayilive.com/api/core/users/me/favorites` |
| DELETE | `/users/me/favorites/{roomId}` | `https://mp.dayilive.com/api/core/users/me/favorites/{roomId}` |
| POST | `/users/me/watch-history` | `https://mp.dayilive.com/api/core/users/me/watch-history` |
| GET | `/users/me/watch-history` | `https://mp.dayilive.com/api/core/users/me/watch-history` |
| DELETE | `/users/me/watch-history/{id}` | `https://mp.dayilive.com/api/core/users/me/watch-history/{id}` |
| POST | `/users/me/watch-history/clear` | `https://mp.dayilive.com/api/core/users/me/watch-history/clear` |
| POST | `/users/me/subscriptions` | `https://mp.dayilive.com/api/core/users/me/subscriptions` |
| GET | `/users/me/subscriptions` | `https://mp.dayilive.com/api/core/users/me/subscriptions` |
| DELETE | `/users/me/subscriptions/{roomId}` | `https://mp.dayilive.com/api/core/users/me/subscriptions/{roomId}` |
| GET | `/users/me/subscriptions/check/{targetId}` | `https://mp.dayilive.com/api/core/users/me/subscriptions/check/{targetId}` |
| POST | `/users/me/subscriptions/clear-history` | `https://mp.dayilive.com/api/core/users/me/subscriptions/clear-history` |

### 内容管理

| 方法 | 相对路径 | 完整URL |
|------|---------|---------|
| GET | `/categories` | `https://mp.dayilive.com/api/core/categories` |
| GET | `/categories/{id}` | `https://mp.dayilive.com/api/core/categories/{id}` |
| GET | `/categories/{id}/content` | `https://mp.dayilive.com/api/core/categories/{id}/content` |
| GET | `/featured-content` | `https://mp.dayilive.com/api/core/featured-content` |
| GET | `/brands` | `https://mp.dayilive.com/api/core/brands` |
| GET | `/brands/{id}` | `https://mp.dayilive.com/api/core/brands/{id}` |
| GET | `/brands/{id}/content` | `https://mp.dayilive.com/api/core/brands/{id}/content` |
| GET | `/tags` | `https://mp.dayilive.com/api/core/tags` |
| GET | `/tags/popular` | `https://mp.dayilive.com/api/core/tags/popular` |
| GET | `/tags/{id}` | `https://mp.dayilive.com/api/core/tags/{id}` |
| GET | `/tags/{id}/content` | `https://mp.dayilive.com/api/core/tags/{id}/content` |

### 专题管理

| 方法 | 相对路径 | 完整URL |
|------|---------|---------|
| GET | `/topics` | `https://mp.dayilive.com/api/core/topics` |
| POST | `/topics` | `https://mp.dayilive.com/api/core/topics` |
| GET | `/topics/{id}` | `https://mp.dayilive.com/api/core/topics/{id}` |
| PATCH | `/topics/{id}` | `https://mp.dayilive.com/api/core/topics/{id}` |
| DELETE | `/topics/{id}` | `https://mp.dayilive.com/api/core/topics/{id}` |
| GET | `/topics/{id}/categories` | `https://mp.dayilive.com/api/core/topics/{id}/categories` |
| POST | `/topics/{id}/categories` | `https://mp.dayilive.com/api/core/topics/{id}/categories` |
| PATCH | `/topic-categories/{id}` | `https://mp.dayilive.com/api/core/topic-categories/{id}` |
| DELETE | `/topic-categories/{id}` | `https://mp.dayilive.com/api/core/topic-categories/{id}` |
| GET | `/topic-categories/{id}/rooms` | `https://mp.dayilive.com/api/core/topic-categories/{id}/rooms` |
| POST | `/topic-categories/{id}/rooms` | `https://mp.dayilive.com/api/core/topic-categories/{id}/rooms` |
| PUT | `/topic-categories/{id}/rooms/sort-order` | `https://mp.dayilive.com/api/core/topic-categories/{id}/rooms/sort-order` |
| DELETE | `/topic-categories/{id}/rooms` | `https://mp.dayilive.com/api/core/topic-categories/{id}/rooms` |

### 其他功能

| 方法 | 相对路径 | 完整URL |
|------|---------|---------|
| GET | `/search` | `https://mp.dayilive.com/api/core/search` |
| POST | `/playback/stats` | `https://mp.dayilive.com/api/core/playback/stats` |

### 通知模块

| 方法 | 相对路径 | 完整URL |
|------|---------|---------|
| GET | `/users/me/notifications` | `https://mp.dayilive.com/api/core/users/me/notifications` |
| POST | `/users/me/notifications/{id}/read` | `https://mp.dayilive.com/api/core/users/me/notifications/{id}/read` |

### 管理员接口

| 方法 | 相对路径 | 完整URL |
|------|---------|---------|
| GET | `/admin/experts` | `https://mp.dayilive.com/api/core/admin/experts` |
| POST | `/admin/experts` | `https://mp.dayilive.com/api/core/admin/experts` |
| PATCH | `/admin/experts/{id}` | `https://mp.dayilive.com/api/core/admin/experts/{id}` |
| DELETE | `/admin/experts/{id}` | `https://mp.dayilive.com/api/core/admin/experts/{id}` |
| POST | `/admin/sessions/{id}/experts` | `https://mp.dayilive.com/api/core/admin/sessions/{id}/experts` |
| GET | `/admin/categories` | `https://mp.dayilive.com/api/core/admin/categories` |
| POST | `/admin/categories` | `https://mp.dayilive.com/api/core/admin/categories` |
| PATCH | `/admin/categories/{id}` | `https://mp.dayilive.com/api/core/admin/categories/{id}` |
| DELETE | `/admin/categories/{id}` | `https://mp.dayilive.com/api/core/admin/categories/{id}` |
| GET | `/admin/featured-content` | `https://mp.dayilive.com/api/core/admin/featured-content` |
| POST | `/admin/featured-content` | `https://mp.dayilive.com/api/core/admin/featured-content` |
| PATCH | `/admin/featured-content/{id}` | `https://mp.dayilive.com/api/core/admin/featured-content/{id}` |
| DELETE | `/admin/featured-content/{id}` | `https://mp.dayilive.com/api/core/admin/featured-content/{id}` |
| GET | `/admin/brands` | `https://mp.dayilive.com/api/core/admin/brands` |
| POST | `/admin/brands` | `https://mp.dayilive.com/api/core/admin/brands` |
| PATCH | `/admin/brands/{id}` | `https://mp.dayilive.com/api/core/admin/brands/{id}` |
| DELETE | `/admin/brands/{id}` | `https://mp.dayilive.com/api/core/admin/brands/{id}` |
| POST | `/admin/rooms/{id}/brands` | `https://mp.dayilive.com/api/core/admin/rooms/{id}/brands` |
| GET | `/admin/brands/{id}/topics` | `https://mp.dayilive.com/api/core/admin/brands/{id}/topics` |
| POST | `/admin/brands/{id}/topics` | `https://mp.dayilive.com/api/core/admin/brands/{id}/topics` |
| DELETE | `/admin/brands/{id}/topics/{topicId}` | `https://mp.dayilive.com/api/core/admin/brands/{id}/topics/{topicId}` |
| GET | `/admin/tags` | `https://mp.dayilive.com/api/core/admin/tags` |
| POST | `/admin/tags` | `https://mp.dayilive.com/api/core/admin/tags` |
| PATCH | `/admin/tags/{id}` | `https://mp.dayilive.com/api/core/admin/tags/{id}` |
| DELETE | `/admin/tags/{id}` | `https://mp.dayilive.com/api/core/admin/tags/{id}` |
| POST | `/admin/sessions/{id}/tags` | `https://mp.dayilive.com/api/core/admin/sessions/{id}/tags` |
| DELETE | `/admin/sessions/{id}/tags/{tagId}` | `https://mp.dayilive.com/api/core/admin/sessions/{id}/tags/{tagId}` |
| GET | `/admin/rooms/{id}/tabs` | `https://mp.dayilive.com/api/core/admin/rooms/{id}/tabs` |
| POST | `/admin/rooms/{id}/tabs` | `https://mp.dayilive.com/api/core/admin/rooms/{id}/tabs` |
| PATCH | `/admin/tabs/{id}` | `https://mp.dayilive.com/api/core/admin/tabs/{id}` |
| DELETE | `/admin/tabs/{id}` | `https://mp.dayilive.com/api/core/admin/tabs/{id}` |
| POST | `/admin/rooms/{id}/tabs/image` | `https://mp.dayilive.com/api/core/admin/rooms/{id}/tabs/image` |
| GET | `/admin/notifications` | `https://mp.dayilive.com/api/core/admin/notifications` |
| POST | `/admin/notifications` | `https://mp.dayilive.com/api/core/admin/notifications` |
| GET | `/admin/notifications/{id}` | `https://mp.dayilive.com/api/core/admin/notifications/{id}` |
| PATCH | `/admin/notifications/{id}` | `https://mp.dayilive.com/api/core/admin/notifications/{id}` |
| DELETE | `/admin/notifications/{id}` | `https://mp.dayilive.com/api/core/admin/notifications/{id}` |
| POST | `/admin/notifications/batch-delete` | `https://mp.dayilive.com/api/core/admin/notifications/batch-delete` |

---

**更新时间**: 2026-04-22
**总计**: 约 120+ 个端点