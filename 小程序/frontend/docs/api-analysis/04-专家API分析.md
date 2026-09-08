# 专家API完整分析

## 📋 概述

专家API负责专家信息展示、场次关联、关注管理等功能，全部通过 Core Service 提供服务。

## 📁 相关文件

- **独立文件**: `src/api/expert.ts`
- **配置文件**: `src/config/api.ts` (API_PATHS.EXPERT / API_PATHS.USER_BEHAVIOR / API_PATHS.ADMIN)
- **Store**: `src/store/expert.ts`

## 🌐 服务信息

- **服务**: Core Service
- **Base URL**: `https://mp.dayilive.com/api/core`

---

## 🔗 API接口详细分析

### 专家基本信息 (Core Service)

#### 1. 获取专家列表
- **函数名**: `getExpertList`
- **HTTP方法**: GET
- **相对路径**: `/experts`
- **完整URL**: `https://mp.dayilive.com/api/core/experts`
- **路由判断**: Core Service（不以 /me/ /auth 开头）

#### 2. 获取推荐专家
- **函数名**: `getFeaturedExperts`
- **HTTP方法**: GET
- **相对路径**: `/featured-experts`
- **完整URL**: `https://mp.dayilive.com/api/core/featured-experts`

#### 3. 获取专家详情
- **函数名**: `getExpertDetail`
- **HTTP方法**: GET
- **相对路径**: `/experts/{expertId}`
- **完整URL**: `https://mp.dayilive.com/api/core/experts/{expertId}`

#### 4. 获取专家场次
- **函数名**: `getExpertSessions`
- **HTTP方法**: GET
- **相对路径**: `/experts/{expertId}/sessions`
- **完整URL**: `https://mp.dayilive.com/api/core/experts/{expertId}/sessions`

#### 5. 获取专家内容
- **函数名**: `getExpertContent`
- **HTTP方法**: GET
- **相对路径**: `/professors/{expertId}/content`
- **完整URL**: `https://mp.dayilive.com/api/core/professors/{expertId}/content`

#### 6. 检查专家关注状态 ✅
- **函数名**: `getExpertFollowStatus`
- **HTTP方法**: GET
- **相对路径**: `/experts/{expertId}/is-followed`
- **完整URL**: `https://mp.dayilive.com/api/core/experts/{expertId}/is-followed`
- **配置**: `{ showError: false }`
- **用途**: 检查当前用户是否关注了指定专家

### 场次专家管理

#### 7. 获取场次专家列表
- **函数名**: `getSessionExperts`
- **HTTP方法**: GET
- **相对路径**: `/sessions/{sessionId}/experts`
- **完整URL**: `https://mp.dayilive.com/api/core/sessions/{sessionId}/experts`

#### 8. 设置场次专家
- **函数名**: `setSessionExperts`
- **HTTP方法**: POST
- **相对路径**: `/sessions/{sessionId}/experts`
- **完整URL**: `https://mp.dayilive.com/api/core/sessions/{sessionId}/experts`

### 用户关注专家行为 (Core Service)

#### 9. 获取已关注专家列表
- **函数名**: `getMyFollowedExperts`
- **HTTP方法**: GET
- **相对路径**: `/users/me/followed-experts`
- **完整URL**: `https://mp.dayilive.com/api/core/users/me/followed-experts`

#### 10. 关注专家
- **函数名**: `followExpert`
- **HTTP方法**: POST
- **相对路径**: `/users/me/followed-experts`
- **完整URL**: `https://mp.dayilive.com/api/core/users/me/followed-experts`
- **请求体**: `{ expert_id: string }`

#### 11. 取消关注专家
- **函数名**: `unfollowExpert`
- **HTTP方法**: DELETE
- **相对路径**: `/users/me/followed-experts/{expertId}`
- **完整URL**: `https://mp.dayilive.com/api/core/users/me/followed-experts/{expertId}`

### 管理员专家管理

#### 12. 管理员专家列表
- **函数名**: `getAdminExpertList`
- **HTTP方法**: GET
- **路径**: `/admin/experts`
- **完整URL**: `https://mp.dayilive.com/api/core/admin/experts`

#### 13. 创建专家
- **函数名**: `createExpert`
- **HTTP方法**: POST
- **路径**: `/admin/experts`
- **完整URL**: `https://mp.dayilive.com/api/core/admin/experts`

#### 14. 更新专家
- **函数名**: `updateExpert`
- **HTTP方法**: PATCH
- **路径**: `/admin/experts/{expertId}`
- **完整URL**: `https://mp.dayilive.com/api/core/admin/experts/{expertId}`

#### 15. 删除专家
- **函数名**: `deleteExpert`
- **HTTP方法**: DELETE
- **路径**: `/admin/experts/{expertId}`
- **完整URL**: `https://mp.dayilive.com/api/core/admin/experts/{expertId}`

#### 16. 关联场次专家（管理员）
- **函数名**: `setSessionExperts`（通过 ADMIN.SESSION_EXPERTS）
- **HTTP方法**: POST
- **路径**: `/admin/sessions/{sessionId}/experts`
- **完整URL**: `https://mp.dayilive.com/api/core/admin/sessions/{sessionId}/experts`

---

## 🗺️ 路径映射表

| 函数名 | 方法 | 相对路径 | 完整URL |
|-------|------|---------|---------|
| `getExpertList` | GET | `/experts` | `https://mp.dayilive.com/api/core/experts` |
| `getFeaturedExperts` | GET | `/featured-experts` | `https://mp.dayilive.com/api/core/featured-experts` |
| `getExpertDetail` | GET | `/experts/{id}` | `https://mp.dayilive.com/api/core/experts/{id}` |
| `getExpertSessions` | GET | `/experts/{id}/sessions` | `https://mp.dayilive.com/api/core/experts/{id}/sessions` |
| `getExpertContent` | GET | `/professors/{id}/content` | `https://mp.dayilive.com/api/core/professors/{id}/content` |
| `getExpertFollowStatus` | GET | `/experts/{id}/is-followed` | `https://mp.dayilive.com/api/core/experts/{id}/is-followed` |
| `getSessionExperts` | GET | `/sessions/{id}/experts` | `https://mp.dayilive.com/api/core/sessions/{id}/experts` |
| `setSessionExperts` | POST | `/sessions/{id}/experts` | `https://mp.dayilive.com/api/core/sessions/{id}/experts` |
| `getMyFollowedExperts` | GET | `/users/me/followed-experts` | `https://mp.dayilive.com/api/core/users/me/followed-experts` |
| `followExpert` | POST | `/users/me/followed-experts` | `https://mp.dayilive.com/api/core/users/me/followed-experts` |
| `unfollowExpert` | DELETE | `/users/me/followed-experts/{id}` | `https://mp.dayilive.com/api/core/users/me/followed-experts/{id}` |
| `getAdminExpertList` | GET | `/admin/experts` | `https://mp.dayilive.com/api/core/admin/experts` |
| `createExpert` | POST | `/admin/experts` | `https://mp.dayilive.com/api/core/admin/experts` |
| `updateExpert` | PATCH | `/admin/experts/{id}` | `https://mp.dayilive.com/api/core/admin/experts/{id}` |
| `deleteExpert` | DELETE | `/admin/experts/{id}` | `https://mp.dayilive.com/api/core/admin/experts/{id}` |

---

**分析完成时间**: 2026-04-22
**API数量**: 16个
**主要服务**: Core Service