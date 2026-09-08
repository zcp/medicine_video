# 内容管理API完整分析

## 📋 概述

内容管理API涵盖品牌、分类、标签、焦点图、专题管理及Tab管理，全部通过 Core Service 提供服务。

## 📁 相关文件

- `src/api/brands.ts`
- `src/api/category.ts`
- `src/api/featuredContent.ts`
- `src/api/tabs.ts`
- **配置**: `src/config/api.ts` (API_PATHS.CONTENT / API_PATHS.TOPIC / API_PATHS.ADMIN)

## 🌐 服务信息

- **服务**: Core Service
- **Base URL**: `https://mp.dayilive.com/api/core`

---

## 🔗 API接口详细分析

### 品牌管理

#### 1. 品牌列表
- GET `/brands` → `https://mp.dayilive.com/api/core/brands` ✓

#### 2. 品牌详情
- GET `/brands/{brandId}` → `https://mp.dayilive.com/api/core/brands/{brandId}` ✓

#### 3. 品牌内容
- GET `/brands/{brandId}/content` → `https://mp.dayilive.com/api/core/brands/{brandId}/content` ✓

#### 4. 管理员品牌列表
- GET `/admin/brands` → `https://mp.dayilive.com/api/core/admin/brands` ✓

#### 5. 创建品牌
- POST `/admin/brands` → `https://mp.dayilive.com/api/core/admin/brands` ✓

#### 6. 更新品牌
- PATCH `/admin/brands/{brandId}` → `https://mp.dayilive.com/api/core/admin/brands/{brandId}` ✓

#### 7. 删除品牌
- DELETE `/admin/brands/{brandId}` → `https://mp.dayilive.com/api/core/admin/brands/{brandId}` ✓

#### 8. 绑定房间品牌
- POST `/admin/rooms/{roomId}/brands` → `https://mp.dayilive.com/api/core/admin/rooms/{roomId}/brands` ✓

#### 9. 品牌关联专题列表
- GET `/admin/brands/{brandId}/topics` → `https://mp.dayilive.com/api/core/admin/brands/{brandId}/topics` ✓

#### 10. 批量关联专题
- POST `/admin/brands/{brandId}/topics` → `https://mp.dayilive.com/api/core/admin/brands/{brandId}/topics` ✓

#### 11. 解除品牌专题关联
- DELETE `/admin/brands/{brandId}/topics/{topicId}` → `https://mp.dayilive.com/api/core/admin/brands/{brandId}/topics/{topicId}` ✓

### 分类管理

#### 12. 分类列表
- GET `/categories` → `https://mp.dayilive.com/api/core/categories` ✓

#### 13. 分类详情
- GET `/categories/{categoryId}` → `https://mp.dayilive.com/api/core/categories/{categoryId}` ✓

#### 14. 分类内容
- GET `/categories/{categoryId}/content` → `https://mp.dayilive.com/api/core/categories/{categoryId}/content` ✓

#### 15. 管理员分类列表
- GET `/admin/categories` → `https://mp.dayilive.com/api/core/admin/categories` ✓

#### 16. 创建分类
- POST `/admin/categories` → `https://mp.dayilive.com/api/core/admin/categories` ✓

#### 17. 更新分类
- PATCH `/admin/categories/{categoryId}` → `https://mp.dayilive.com/api/core/admin/categories/{categoryId}` ✓

#### 18. 删除分类
- DELETE `/admin/categories/{categoryId}` → `https://mp.dayilive.com/api/core/admin/categories/{categoryId}` ✓

### 标签管理

#### 19. 标签列表
- GET `/tags` → `https://mp.dayilive.com/api/core/tags` ✓

#### 20. 热门标签
- GET `/tags/popular` → `https://mp.dayilive.com/api/core/tags/popular` ✓

#### 21. 标签详情
- GET `/tags/{tagId}` → `https://mp.dayilive.com/api/core/tags/{tagId}` ✓

#### 22. 标签内容
- GET `/tags/{tagId}/content` → `https://mp.dayilive.com/api/core/tags/{tagId}/content` ✓

#### 23. 管理员标签列表
- GET `/admin/tags` → `https://mp.dayilive.com/api/core/admin/tags` ✓

#### 24. 创建标签
- POST `/admin/tags` → `https://mp.dayilive.com/api/core/admin/tags` ✓

#### 25. 更新标签
- PATCH `/admin/tags/{tagId}` → `https://mp.dayilive.com/api/core/admin/tags/{tagId}` ✓

#### 26. 删除标签
- DELETE `/admin/tags/{tagId}` → `https://mp.dayilive.com/api/core/admin/tags/{tagId}` ✓

### 焦点图管理

#### 27. 焦点图列表（公开）
- GET `/featured-content` → `https://mp.dayilive.com/api/core/featured-content` ✓

#### 28. 管理员焦点图列表
- GET `/admin/featured-content` → `https://mp.dayilive.com/api/core/admin/featured-content` ✓

#### 29. 创建焦点图 ✅
- POST `/featured-content/admin` → `https://mp.dayilive.com/api/core/featured-content/admin` ✓
- **注**: 路径模式与列表不同，已对线上标准答案验证

#### 30. 更新焦点图 ✅
- PATCH `/featured-content/admin/{contentId}` → `https://mp.dayilive.com/api/core/featured-content/admin/{contentId}` ✓

#### 31. 删除焦点图 ✅
- DELETE `/featured-content/admin/{contentId}` → `https://mp.dayilive.com/api/core/featured-content/admin/{contentId}` ✓

### Tab 管理

#### 32. 获取 Tab 列表（公开）
- GET `/rooms/{roomId}/tabs` → `https://mp.dayilive.com/api/core/rooms/{roomId}/tabs` ✓

#### 33. 管理员 Tab 列表
- GET `/admin/rooms/{roomId}/tabs` → `https://mp.dayilive.com/api/core/admin/rooms/{roomId}/tabs` ✓

#### 34. 创建 Tab
- POST `/admin/rooms/{roomId}/tabs` → `https://mp.dayilive.com/api/core/admin/rooms/{roomId}/tabs` ✓

#### 35. 更新 Tab ✅
- PATCH `/admin/tabs/{tabId}` → `https://mp.dayilive.com/api/core/admin/tabs/{tabId}`
- **注**: 更新/删除不带 roomId，仅用 tabId

#### 36. 删除 Tab ✅
- DELETE `/admin/tabs/{tabId}` → `https://mp.dayilive.com/api/core/admin/tabs/{tabId}`

#### 37. 上传 Tab 图片 ✅
- POST `/admin/rooms/{roomId}/tabs/image` → `https://mp.dayilive.com/api/core/admin/rooms/{roomId}/tabs/image`

---

## 🗺️ 路径映射表

| 方法 | 相对路径 | 完整URL |
|------|---------|---------|
| GET | `/brands` | `https://mp.dayilive.com/api/core/brands` |
| GET | `/brands/{id}` | `https://mp.dayilive.com/api/core/brands/{id}` |
| GET | `/brands/{id}/content` | `https://mp.dayilive.com/api/core/brands/{id}/content` |
| GET | `/categories` | `https://mp.dayilive.com/api/core/categories` |
| GET | `/categories/{id}` | `https://mp.dayilive.com/api/core/categories/{id}` |
| GET | `/categories/{id}/content` | `https://mp.dayilive.com/api/core/categories/{id}/content` |
| GET | `/tags` | `https://mp.dayilive.com/api/core/tags` |
| GET | `/tags/popular` | `https://mp.dayilive.com/api/core/tags/popular` |
| GET | `/tags/{id}` | `https://mp.dayilive.com/api/core/tags/{id}` |
| GET | `/tags/{id}/content` | `https://mp.dayilive.com/api/core/tags/{id}/content` |
| GET | `/featured-content` | `https://mp.dayilive.com/api/core/featured-content` |
| GET | `/admin/featured-content` | `https://mp.dayilive.com/api/core/admin/featured-content` |
| POST | `/featured-content/admin` | `https://mp.dayilive.com/api/core/featured-content/admin` |
| PATCH | `/featured-content/admin/{id}` | `https://mp.dayilive.com/api/core/featured-content/admin/{id}` |
| DELETE | `/featured-content/admin/{id}` | `https://mp.dayilive.com/api/core/featured-content/admin/{id}` |
| GET | `/rooms/{id}/tabs` | `https://mp.dayilive.com/api/core/rooms/{id}/tabs` |
| GET | `/admin/rooms/{id}/tabs` | `https://mp.dayilive.com/api/core/admin/rooms/{id}/tabs` |
| POST | `/admin/rooms/{id}/tabs` | `https://mp.dayilive.com/api/core/admin/rooms/{id}/tabs` |
| PATCH | `/admin/tabs/{id}` | `https://mp.dayilive.com/api/core/admin/tabs/{id}` |
| DELETE | `/admin/tabs/{id}` | `https://mp.dayilive.com/api/core/admin/tabs/{id}` |
| POST | `/admin/rooms/{id}/tabs/image` | `https://mp.dayilive.com/api/core/admin/rooms/{id}/tabs/image` |

---

**分析完成时间**: 2026-04-22
**API数量**: 37个（全部 Core Service）