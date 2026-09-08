# 房间API完整分析

## 📋 概述

房间API负责直播间的基本CRUD、扩展信息查询（专家/专题/品牌/收藏状态/Tab）等，全部通过 Core Service 提供服务。

## 📁 相关文件

- **独立文件**: `src/api/room.ts`
- **配置文件**: `src/config/api.ts` (API_PATHS.ROOM)
- **Store**: `src/store/room.ts`

## 🌐 服务信息

- **服务**: Core Service
- **Base URL**: `https://mp.dayilive.com/api/core`

---

## 🔗 API接口详细分析

### 房间基本 CRUD

#### 1. 获取房间列表
- **函数名**: `getRooms`
- **HTTP方法**: GET
- **路径**: `/rooms`
- **完整URL**: `https://mp.dayilive.com/api/core/rooms` ✓

#### 2. 首页房间列表
- **函数名**: `getHomepageRooms`
- **HTTP方法**: GET
- **路径**: `/homepage/rooms`
- **完整URL**: `https://mp.dayilive.com/api/core/homepage/rooms` ✓

#### 3. 获取房间详情
- **函数名**: `getRoomById`
- **HTTP方法**: GET
- **路径**: `/rooms/{roomId}`
- **完整URL**: `https://mp.dayilive.com/api/core/rooms/{roomId}` ✓

#### 4. 创建房间
- **函数名**: `createRoom`
- **HTTP方法**: POST
- **路径**: `/rooms`
- **完整URL**: `https://mp.dayilive.com/api/core/rooms` ✓

#### 5. 更新房间
- **函数名**: `updateRoom`
- **HTTP方法**: PATCH
- **路径**: `/rooms/{roomId}`
- **完整URL**: `https://mp.dayilive.com/api/core/rooms/{roomId}` ✓

#### 6. 删除房间
- **函数名**: `deleteRoom`
- **HTTP方法**: DELETE
- **路径**: `/rooms/{roomId}`
- **完整URL**: `https://mp.dayilive.com/api/core/rooms/{roomId}` ✓

### 房间扩展信息

#### 7. 获取房间场次列表
- **函数名**: `getRoomSessions`
- **HTTP方法**: GET
- **路径**: `/rooms/{roomId}/sessions`
- **完整URL**: `https://mp.dayilive.com/api/core/rooms/{roomId}/sessions` ✓

#### 8. 获取房间分会场
- **函数名**: `getRoomSubVenues`
- **HTTP方法**: GET
- **路径**: `/rooms/{roomId}/sub-venues`
- **完整URL**: `https://mp.dayilive.com/api/core/rooms/{roomId}/sub-venues` ✓

#### 9. 获取房间封面上传
- **函数名**: `uploadRoomCover`
- **HTTP方法**: POST
- **路径**: `/rooms/{roomId}/cover`
- **完整URL**: `https://mp.dayilive.com/api/core/rooms/{roomId}/cover` ✓

#### 10. 获取房间品牌列表
- **函数名**: `getRoomBrands`
- **HTTP方法**: GET
- **路径**: `/rooms/{roomId}/brands`
- **完整URL**: `https://mp.dayilive.com/api/core/rooms/{roomId}/brands` ✓

#### 11. 获取房间专家列表 ✅
- **函数名**: `getRoomExperts`
- **HTTP方法**: GET
- **路径**: `/rooms/{roomId}/experts`
- **完整URL**: `https://mp.dayilive.com/api/core/rooms/{roomId}/experts` ✓

#### 12. 获取房间所属专题 ✅
- **函数名**: `getRoomTopics`
- **HTTP方法**: GET
- **路径**: `/rooms/{roomId}/topics`
- **完整URL**: `https://mp.dayilive.com/api/core/rooms/{roomId}/topics` ✓

#### 13. 检查房间收藏状态 ✅
- **函数名**: `checkRoomFavorited`
- **HTTP方法**: GET
- **路径**: `/rooms/{roomId}/is-favorited`
- **完整URL**: `https://mp.dayilive.com/api/core/rooms/{roomId}/is-favorited` ✓

#### 14. 获取房间留言
- **函数名**: `getRoomMessages`
- **HTTP方法**: GET
- **路径**: `/rooms/{roomId}/messages`
- **完整URL**: `https://mp.dayilive.com/api/core/rooms/{roomId}/messages` ✓

#### 15. 发送房间留言
- **函数名**: `sendRoomMessage`
- **HTTP方法**: POST
- **路径**: `/rooms/{roomId}/messages`
- **完整URL**: `https://mp.dayilive.com/api/core/rooms/{roomId}/messages` ✓

#### 16. 获取房间 Tab 列表
- **函数名**: `getRoomTabs`
- **HTTP方法**: GET
- **路径**: `/rooms/{roomId}/tabs`
- **完整URL**: `https://mp.dayilive.com/api/core/rooms/{roomId}/tabs` ✓

### 批量操作

#### 17. 批量查询房间状态 ✅
- **函数名**: `batchGetRoomStatus`
- **HTTP方法**: POST
- **路径**: `/rooms/batch-status`
- **完整URL**: `https://mp.dayilive.com/api/core/rooms/batch-status` ✓

### 管理员操作

#### 18. 设置房间品牌（管理员）
- **函数名**: `setAdminRoomBrands`
- **HTTP方法**: POST
- **路径**: `/admin/rooms/{roomId}/brands`
- **完整URL**: `https://mp.dayilive.com/api/core/admin/rooms/{roomId}/brands` ✓

---

## 🗺️ 路径映射表

| 函数名 | 方法 | 相对路径 | 完整URL |
|-------|------|---------|---------|
| `getRooms` | GET | `/rooms` | `https://mp.dayilive.com/api/core/rooms` |
| `getHomepageRooms` | GET | `/homepage/rooms` | `https://mp.dayilive.com/api/core/homepage/rooms` |
| `getRoomById` | GET | `/rooms/{id}` | `https://mp.dayilive.com/api/core/rooms/{id}` |
| `createRoom` | POST | `/rooms` | `https://mp.dayilive.com/api/core/rooms` |
| `updateRoom` | PATCH | `/rooms/{id}` | `https://mp.dayilive.com/api/core/rooms/{id}` |
| `deleteRoom` | DELETE | `/rooms/{id}` | `https://mp.dayilive.com/api/core/rooms/{id}` |
| `getRoomSessions` | GET | `/rooms/{id}/sessions` | `https://mp.dayilive.com/api/core/rooms/{id}/sessions` |
| `getRoomSubVenues` | GET | `/rooms/{id}/sub-venues` | `https://mp.dayilive.com/api/core/rooms/{id}/sub-venues` |
| `uploadRoomCover` | POST | `/rooms/{id}/cover` | `https://mp.dayilive.com/api/core/rooms/{id}/cover` |
| `getRoomBrands` | GET | `/rooms/{id}/brands` | `https://mp.dayilive.com/api/core/rooms/{id}/brands` |
| `getRoomExperts` | GET | `/rooms/{id}/experts` | `https://mp.dayilive.com/api/core/rooms/{id}/experts` |
| `getRoomTopics` | GET | `/rooms/{id}/topics` | `https://mp.dayilive.com/api/core/rooms/{id}/topics` |
| `checkRoomFavorited` | GET | `/rooms/{id}/is-favorited` | `https://mp.dayilive.com/api/core/rooms/{id}/is-favorited` |
| `getRoomMessages` | GET | `/rooms/{id}/messages` | `https://mp.dayilive.com/api/core/rooms/{id}/messages` |
| `sendRoomMessage` | POST | `/rooms/{id}/messages` | `https://mp.dayilive.com/api/core/rooms/{id}/messages` |
| `getRoomTabs` | GET | `/rooms/{id}/tabs` | `https://mp.dayilive.com/api/core/rooms/{id}/tabs` |
| `batchGetRoomStatus` | POST | `/rooms/batch-status` | `https://mp.dayilive.com/api/core/rooms/batch-status` |
| `setAdminRoomBrands` | POST | `/admin/rooms/{id}/brands` | `https://mp.dayilive.com/api/core/admin/rooms/{id}/brands` |

---

**分析完成时间**: 2026-04-22
**API数量**: 18个（全部 Core Service）