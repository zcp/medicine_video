# 会话API完整分析

## 📋 概述

会话（场次）API负责直播场次的CRUD、观众管理、流地址、标签管理等，全部通过 Core Service 提供服务。

## 📁 相关文件

- **独立文件**: `src/api/session.ts`
- **配置文件**: `src/config/api.ts` (API_PATHS.SESSION / API_PATHS.ADMIN)
- **Store**: `src/store/session.ts`

## 🌐 服务信息

- **服务**: Core Service
- **Base URL**: `https://mp.dayilive.com/api/core`

---

## 🔗 API接口详细分析

### 场次基本 CRUD

#### 1. 创建场次
- **HTTP方法**: POST
- **路径**: `/rooms/{roomId}/sessions`
- **完整URL**: `https://mp.dayilive.com/api/core/rooms/{roomId}/sessions` ✓

#### 2. 获取房间场次列表
- **HTTP方法**: GET
- **路径**: `/rooms/{roomId}/sessions`
- **完整URL**: `https://mp.dayilive.com/api/core/rooms/{roomId}/sessions` ✓

#### 3. 获取场次详情
- **HTTP方法**: GET
- **路径**: `/sessions/{sessionId}`
- **完整URL**: `https://mp.dayilive.com/api/core/sessions/{sessionId}` ✓

#### 4. 更新场次
- **HTTP方法**: PATCH
- **路径**: `/sessions/{sessionId}`
- **完整URL**: `https://mp.dayilive.com/api/core/sessions/{sessionId}` ✓

#### 5. 删除场次
- **HTTP方法**: DELETE
- **路径**: `/sessions/{sessionId}`
- **完整URL**: `https://mp.dayilive.com/api/core/sessions/{sessionId}` ✓

#### 6. 导入场次
- **HTTP方法**: POST
- **路径**: `/rooms/{roomId}/sessions/import`
- **完整URL**: `https://mp.dayilive.com/api/core/rooms/{roomId}/sessions/import` ✓

### 场次状态管理

#### 7. 开始直播
- **HTTP方法**: POST
- **路径**: `/sessions/{sessionId}/start`
- **完整URL**: `https://mp.dayilive.com/api/core/sessions/{sessionId}/start`

#### 8. 结束直播
- **HTTP方法**: POST
- **路径**: `/sessions/{sessionId}/end`
- **完整URL**: `https://mp.dayilive.com/api/core/sessions/{sessionId}/end`

### 场次扩展信息

#### 9. 获取场次观看人数 ✅
- **HTTP方法**: GET
- **路径**: `/sessions/{sessionId}/viewers`
- **完整URL**: `https://mp.dayilive.com/api/core/sessions/{sessionId}/viewers` ✓

#### 10. 获取场次直播流地址 ✅
- **HTTP方法**: GET
- **路径**: `/sessions/{sessionId}/stream-url`
- **完整URL**: `https://mp.dayilive.com/api/core/sessions/{sessionId}/stream-url` ✓

#### 11. 获取场次标签
- **HTTP方法**: GET
- **路径**: `/sessions/{sessionId}/tags`
- **完整URL**: `https://mp.dayilive.com/api/core/sessions/{sessionId}/tags` ✓

#### 12. 按标签搜索场次
- **HTTP方法**: GET
- **路径**: `/sessions/search`
- **完整URL**: `https://mp.dayilive.com/api/core/sessions/search` ✓

#### 13. 记录观看行为
- **HTTP方法**: POST
- **路径**: `/sessions/{sessionId}/watch`
- **完整URL**: `https://mp.dayilive.com/api/core/sessions/{sessionId}/watch`

#### 14. 播放统计上报（分享）
- **HTTP方法**: POST
- **路径**: `/playback/stats`
- **完整URL**: `https://mp.dayilive.com/api/core/playback/stats` ✓

### 管理员场次管理

#### 15. 设置场次标签（管理员）
- **HTTP方法**: POST
- **路径**: `/admin/sessions/{sessionId}/tags`
- **完整URL**: `https://mp.dayilive.com/api/core/admin/sessions/{sessionId}/tags` ✓

#### 16. 删除场次标签（管理员）
- **HTTP方法**: DELETE
- **路径**: `/admin/sessions/{sessionId}/tags/{tagId}`
- **完整URL**: `https://mp.dayilive.com/api/core/admin/sessions/{sessionId}/tags/{tagId}` ✓

#### 17. 关联场次专家（管理员）
- **HTTP方法**: POST
- **路径**: `/admin/sessions/{sessionId}/experts`
- **完整URL**: `https://mp.dayilive.com/api/core/admin/sessions/{sessionId}/experts` ✓

---

## 🗺️ 路径映射表

| 方法 | 相对路径 | 完整URL |
|------|---------|---------|
| POST | `/rooms/{id}/sessions` | `https://mp.dayilive.com/api/core/rooms/{id}/sessions` |
| GET | `/rooms/{id}/sessions` | `https://mp.dayilive.com/api/core/rooms/{id}/sessions` |
| GET | `/sessions/{id}` | `https://mp.dayilive.com/api/core/sessions/{id}` |
| PATCH | `/sessions/{id}` | `https://mp.dayilive.com/api/core/sessions/{id}` |
| DELETE | `/sessions/{id}` | `https://mp.dayilive.com/api/core/sessions/{id}` |
| POST | `/rooms/{id}/sessions/import` | `https://mp.dayilive.com/api/core/rooms/{id}/sessions/import` |
| POST | `/sessions/{id}/start` | `https://mp.dayilive.com/api/core/sessions/{id}/start` |
| POST | `/sessions/{id}/end` | `https://mp.dayilive.com/api/core/sessions/{id}/end` |
| GET | `/sessions/{id}/viewers` | `https://mp.dayilive.com/api/core/sessions/{id}/viewers` |
| GET | `/sessions/{id}/stream-url` | `https://mp.dayilive.com/api/core/sessions/{id}/stream-url` |
| GET | `/sessions/{id}/tags` | `https://mp.dayilive.com/api/core/sessions/{id}/tags` |
| GET | `/sessions/search` | `https://mp.dayilive.com/api/core/sessions/search` |
| POST | `/sessions/{id}/watch` | `https://mp.dayilive.com/api/core/sessions/{id}/watch` |
| POST | `/playback/stats` | `https://mp.dayilive.com/api/core/playback/stats` |
| POST | `/admin/sessions/{id}/tags` | `https://mp.dayilive.com/api/core/admin/sessions/{id}/tags` |
| DELETE | `/admin/sessions/{id}/tags/{tagId}` | `https://mp.dayilive.com/api/core/admin/sessions/{id}/tags/{tagId}` |
| POST | `/admin/sessions/{id}/experts` | `https://mp.dayilive.com/api/core/admin/sessions/{id}/experts` |

---

**分析完成时间**: 2026-04-22
**API数量**: 17个（全部 Core Service）