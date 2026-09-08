# Admin+Owner 接口权限变更对照表

> 生成日期：2026-06-20
> 用途：前后端对齐接口权限变更

---

## 一、权限收紧的旧端点（8 个）

这些端点路径不变，但权限从"ADMIN 或房间创建者"收紧为**仅 ADMIN/SUPERADMIN**。创建者需改用下方 §二 的新端点。

### 1.1 Tab 管理（5 个）

#### ① 获取 Tab 列表（管理端）

| 项目 | 说明 |
|------|------|
| **方法路径** | `GET /api/v1/admin/rooms/{room_id}/tabs` |
| **认证** | `Authorization: Bearer <access_token>` |
| **权限** | **仅 ADMIN/SUPERADMIN** |
| **请求参数** | 无（room_id 来自路径） |
| **响应** | `{ code, message, data: { total, items: [LiveRoomTab] }, timestamp }` |
| **返回字段** | `id, room_id, tab_key, title, content_type, text_content, image_url, sort_order, is_active, created_at, updated_at` |

#### ② 创建 Tab

| 项目 | 说明 |
|------|------|
| **方法路径** | `POST /api/v1/admin/rooms/{room_id}/tabs` |
| **认证** | `Authorization: Bearer <access_token>` |
| **权限** | **仅 ADMIN/SUPERADMIN** |
| **请求体** | `{ tab_key, title, content_type: "text"\|"image"\|"mixed", text_content?, image_url?, sort_order?, is_active? }` |
| **响应** | `{ code:200, message, data: LiveRoomTab, timestamp }` |

#### ③ 更新 Tab

| 项目 | 说明 |
|------|------|
| **方法路径** | `PATCH /api/v1/admin/tabs/{tab_id}` |
| **认证** | `Authorization: Bearer <access_token>` |
| **权限** | **仅 ADMIN/SUPERADMIN** |
| **请求体** | 部分更新：`{ tab_key?, title?, content_type?, text_content?, image_url?, sort_order?, is_active? }` |
| **响应** | `{ code:200, message, data: LiveRoomTab, timestamp }` |

#### ④ 删除 Tab

| 项目 | 说明 |
|------|------|
| **方法路径** | `DELETE /api/v1/admin/tabs/{tab_id}` |
| **认证** | `Authorization: Bearer <access_token>` |
| **权限** | **仅 ADMIN/SUPERADMIN** |
| **响应** | `{ code:200, message:"success", data: { message:"Tab 删除成功", tab_id }, timestamp }` |

#### ⑤ 上传 Tab 图片

| 项目 | 说明 |
|------|------|
| **方法路径** | `POST /api/v1/admin/rooms/{room_id}/tabs/image` |
| **认证** | `Authorization: Bearer <access_token>` |
| **权限** | **仅 ADMIN/SUPERADMIN** |
| **请求体** | `multipart/form-data`，字段名 `file` |
| **响应** | `{ code:200, message, data: { image_url: "/media/rooms/..." }, timestamp }` |

---

### 1.2 分类管理（2 个）

#### ⑥ 设置直播间分类

| 项目 | 说明 |
|------|------|
| **方法路径** | `POST /api/v1/admin/rooms/{room_id}/categories` |
| **认证** | `Authorization: Bearer <access_token>` |
| **权限** | **仅 ADMIN/SUPERADMIN** |
| **请求体** | `{ category_ids: ["uuid",...], primary_category_id: "uuid", mode: "replace"\|"append" }` |
| **响应** | `{ code:200, message, data: { room_id, mode, categories: [...] }, timestamp }` |

#### ⑦ 删除直播间分类关联

| 项目 | 说明 |
|------|------|
| **方法路径** | `DELETE /api/v1/admin/rooms/{room_id}/categories/{category_id}` |
| **认证** | `Authorization: Bearer <access_token>` |
| **权限** | **仅 ADMIN/SUPERADMIN** |
| **响应** | `{ message: "删除成功" }`（纯 dict，非标准包装） |

---

### 1.3 品牌管理（1 个）

#### ⑧ 绑定直播间品牌

| 项目 | 说明 |
|------|------|
| **方法路径** | `POST /api/v1/admin/rooms/{room_id}/brands` |
| **认证** | `Authorization: Bearer <access_token>` |
| **权限** | **仅 ADMIN/SUPERADMIN** |
| **请求体** | `{ brand_ids: ["uuid",...] }` |
| **响应** | `{ room_id, brand_ids: [...], updated_at }` |

---

## 二、新增的创建者端点（7 个）

这些是**新增**的端点，路径为 `/api/v1/rooms/...`，权限为 **ADMIN/SUPERADMIN 或房间创建者**。前端已切换到此路径。

### 2.1 Tab 管理（4 个）

#### ① 创建 Tab（创建者用）

| 项目 | 说明 |
|------|------|
| **方法路径** | `POST /api/v1/rooms/{room_id}/tabs` |
| **认证** | `Authorization: Bearer <access_token>` |
| **权限** | ADMIN/SUPERADMIN 或房间创建者 |
| **请求体** | `{ tab_key, title, content_type: "text"\|"image"\|"mixed", text_content?, image_url?, sort_order?, is_active? }` |
| **响应** | `{ code:200, message, data: LiveRoomTab, timestamp }` |

#### ② 上传 Tab 图片（创建者用）

| 项目 | 说明 |
|------|------|
| **方法路径** | `POST /api/v1/rooms/{room_id}/tabs/image` |
| **认证** | `Authorization: Bearer <access_token>` |
| **权限** | ADMIN/SUPERADMIN 或房间创建者 |
| **请求体** | `multipart/form-data`，字段名 `file` |
| **响应** | `{ code:200, message, data: { image_url: "/media/rooms/..." }, timestamp }` |

#### ③ 更新 Tab（创建者用）

| 项目 | 说明 |
|------|------|
| **方法路径** | `PATCH /api/v1/rooms/{room_id}/tabs/{tab_id}` |
| **认证** | `Authorization: Bearer <access_token>` |
| **权限** | ADMIN/SUPERADMIN 或房间创建者 |
| **请求体** | 部分更新：`{ tab_key?, title?, content_type?, text_content?, image_url?, sort_order?, is_active? }` |
| **响应** | `{ code:200, message, data: LiveRoomTab, timestamp }` |

#### ④ 删除 Tab（创建者用）

| 项目 | 说明 |
|------|------|
| **方法路径** | `DELETE /api/v1/rooms/{room_id}/tabs/{tab_id}` |
| **认证** | `Authorization: Bearer <access_token>` |
| **权限** | ADMIN/SUPERADMIN 或房间创建者 |
| **响应** | `{ code:200, message:"success", data: { message:"Tab 删除成功", tab_id }, timestamp }` |

---

### 2.2 分类管理（2 个）

#### ⑤ 设置直播间分类（创建者用）

| 项目 | 说明 |
|------|------|
| **方法路径** | `POST /api/v1/rooms/{room_id}/categories` |
| **认证** | `Authorization: Bearer <access_token>` |
| **权限** | ADMIN/SUPERADMIN 或房间创建者 |
| **请求体** | `{ category_ids: ["uuid",...], primary_category_id: "uuid", mode: "replace"\|"append" }` |
| **响应** | `{ code:200, message, data: { room_id, mode, categories: [...] }, timestamp }` |

#### ⑥ 删除直播间分类关联（创建者用）

| 项目 | 说明 |
|------|------|
| **方法路径** | `DELETE /api/v1/rooms/{room_id}/categories/{category_id}` |
| **认证** | `Authorization: Bearer <access_token>` |
| **权限** | ADMIN/SUPERADMIN 或房间创建者 |
| **响应** | `{ message: "删除成功" }`（纯 dict，非标准包装） |

---

### 2.3 品牌管理（1 个）

#### ⑦ 绑定直播间品牌（创建者用）

| 项目 | 说明 |
|------|------|
| **方法路径** | `POST /api/v1/rooms/{room_id}/brands` |
| **认证** | `Authorization: Bearer <access_token>` |
| **权限** | ADMIN/SUPERADMIN 或房间创建者 |
| **请求体** | `{ brand_ids: ["uuid",...] }` |
| **响应** | `{ room_id, brand_ids: [...], updated_at }` |

---

## 三、已有公开查询端点（未变动）

以下为**未变动**的公开查询端点，用于参考：

| 方法 | 路径 | 认证 | 说明 |
|:----:|------|:----:|------|
| `GET` | `/api/v1/rooms/{room_id}/tabs` | 可选（匿名可见公开房间的 active Tab） | 查询 Tab 列表（公开端，仅 `is_active=True`） |
| `GET` | `/api/v1/rooms/{room_id}/categories` | 可选 | 查询分类列表 |
| `GET` | `/api/v1/rooms/{room_id}/brands` | 可选 | 查询品牌列表 |

---

## 四、前端切换指南

### 4.1 按角色切换路径

```typescript
// 判断逻辑示例
function isAdmin(role: string): boolean {
  return role === 'ADMIN' || role === 'SUPERADMIN';
}

function getCreateTabUrl(roomId: string, role: string): string {
  if (isAdmin(role)) {
    return `/admin/rooms/${roomId}/tabs`;    // Admin 走旧路径
  }
  return `/rooms/${roomId}/tabs`;            // 创建者走新路径
}
```

### 4.2 统一路径（推荐）

如果管理后台同时被 ADMIN 和创建者使用，建议直接统一使用新路径：

```typescript
// 统一使用新路径，后端同时允许 ADMIN 和创建者
const API = {
  createTab: (roomId) => `/rooms/${roomId}/tabs`,
  updateTab: (roomId, tabId) => `/rooms/${roomId}/tabs/${tabId}`,
  deleteTab: (roomId, tabId) => `/rooms/${roomId}/tabs/${tabId}`,
  uploadTabImage: (roomId) => `/rooms/${roomId}/tabs/image`,
  setCategories: (roomId) => `/rooms/${roomId}/categories`,
  deleteCategory: (roomId, catId) => `/rooms/${roomId}/categories/${catId}`,
  bindBrands: (roomId) => `/rooms/${roomId}/brands`,
};
```

### 4.3 `updateRoomTab` 新增 `roomId` 参数

`PATCH /admin/tabs/{tab_id}` 之前不需要 `room_id`，但新路径 `PATCH /rooms/{room_id}/tabs/{tab_id}` 需要。调用时请传入：

```typescript
// 之前
updateRoomTab(tabId, data);

// 现在
updateRoomTab(roomId, tabId, data);
```

---

## 五、状态码速查

| HTTP 状态码 | 业务 code | 含义 |
|:----------:|:---------:|------|
| 200 | 200 | 成功 |
| 400 | 4001 | 参数校验失败 |
| 401 | 300x | Token 缺失或无效 |
| 403 | 3003 | 权限不足（非 ADMIN 调 admin 端点） |
| 404 | 2001 | 资源不存在 |
| 500 | 1002 | 服务器内部错误 |
