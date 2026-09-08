# 用户偏好与通知模块 - 设计文档摘要

**生成时间**: 2026-01-18
**用途**: 用于测试代码生成和一致性检测的真相源

## 1. 模块基本信息

- **模块名**: user_preference_notification
- **功能模块名**: 用户偏好与通知
- **数据表**: 2张（user_preferences、notifications）
- **API接口**: 11个（User Preferences 2个、Notifications 9个）

## 2. 数据表定义（DDL）

### 2.1 user_preferences（用户偏好设置表）

**关键字段**:
- `id`: UUID PRIMARY KEY（应用层生成）
- `user_id`: UUID NOT NULL UNIQUE（关联 users.public_id，一对一关系）
- `theme_mode`: VARCHAR(20) DEFAULT 'auto'（昼夜模式：auto/light/dark/scheduled）
- `theme_scheduled_dark_time`: TIME NULL（定时深色模式开始时间）
- `theme_scheduled_light_time`: TIME NULL（定时浅色模式开始时间）
- `pinned_categories`: JSONB NULL（固定的科室ID数组，最多5个）
- `homepage_view_mode`: VARCHAR(20) DEFAULT 'double'（首页视图模式：double/single）
- `cellular_warning_enabled`: BOOLEAN DEFAULT true（是否启用流量提醒）
- `auto_reduce_quality`: BOOLEAN DEFAULT true（流量下自动降画质）
- `auto_play_on_wifi`: BOOLEAN DEFAULT false（WiFi下自动播放）
- `extra`: JSONB NULL（其他扩展偏好设置）
- `created_at`: TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
- `updated_at`: TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP

**索引**:
- `idx_user_preferences_user_id` ON user_preferences(user_id)

### 2.2 notifications（用户通知表）

**关键字段**:
- `id`: UUID PRIMARY KEY（应用层生成）
- `user_id`: UUID NOT NULL（接收通知的用户ID，关联 users.public_id）
- `title`: VARCHAR(255) NOT NULL（通知标题）
- `content`: TEXT NULL（通知内容）
- `notification_type`: VARCHAR(50) DEFAULT 'system'（通知类型：system/subscription/interaction）
- `related_id`: UUID NULL（关联资源ID，如：room_id, session_id等）
- `related_type`: VARCHAR(50) NULL（关联资源类型，如：room, session, expert等）
- `is_read`: BOOLEAN DEFAULT false（是否已读）
- `created_at`: TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP

**索引**:
- `idx_notifications_user_id` ON notifications(user_id)
- `idx_notifications_user_is_read` ON notifications(user_id, is_read)
- `idx_notifications_created_at` ON notifications(created_at)

## 3. Schema定义

### 3.1 User Preferences Schemas

- `UserPreferencesBase`: 用户偏好基础Schema
  - `theme_mode`: Literal["auto", "light", "dark", "scheduled"] = "auto"
  - `pinned_categories`: Optional[List[UUID]]（最多5个）
  - `homepage_view_mode`: Literal["double", "single"] = "double"
  - 其他字段...
- `UserPreferencesUpdate`: 更新用户偏好请求Schema（部分更新）
- `UserPreferencesItem`: 用户偏好响应Schema（包含id、user_id、created_at、updated_at）

### 3.2 Notifications Schemas

- `NotificationBase`: 通知基础Schema
  - `title`: str（min_length=1, max_length=255）
  - `notification_type`: Literal["system", "subscription", "interaction"] = "system"
  - 其他字段...
- `NotificationItem`: 通知响应Schema（包含id、user_id、is_read、created_at）
- `NotificationCreateRequest`: Admin创建通知请求Schema
- `NotificationBatchCreateResponse`: 批量创建通知响应Schema
- `NotificationUpdateRequest`: Admin更新通知请求Schema
- `NotificationBatchDeleteRequest`: 批量删除通知请求Schema
- `NotificationListResponse`: 通知列表响应Schema（包含items、total、page、size、has_more）

## 4. API接口定义

### 4.1 User Preferences API

1. **GET /api/v1/users/me/preferences**
   - 描述: 获取当前登录用户的个性化偏好设置
   - 认证: Strict Auth（强制鉴权）
   - 成功响应: 200 OK，返回 UserPreferencesItem

2. **PATCH /api/v1/users/me/preferences**
   - 描述: 更新当前登录用户的个性化偏好设置（部分更新）
   - 认证: Strict Auth（强制鉴权）
   - 请求体: UserPreferencesUpdate
   - 成功响应: 200 OK，返回 UserPreferencesItem
   - 失败响应: 4001 Parameter Error（如：固定科室最多5个）

### 4.2 Notifications API（用户）

3. **GET /api/v1/users/me/notifications**
   - 描述: 获取当前用户的通知列表（分页）
   - 认证: Strict Auth
   - 查询参数: page, size, is_read, notification_type, sort
   - 成功响应: 200 OK，返回 NotificationListResponse

4. **GET /api/v1/users/me/notifications/unread-count**
   - 描述: 获取未读通知数量
   - 认证: Strict Auth
   - 成功响应: 200 OK，返回 {"unread_count": int}

5. **POST /api/v1/users/me/notifications/{notification_id}/read**
   - 描述: 标记通知为已读
   - 认证: Strict Auth
   - 成功响应: 200 OK

6. **POST /api/v1/users/me/notifications/read-all**
   - 描述: 标记所有通知为已读
   - 认证: Strict Auth
   - 成功响应: 200 OK，返回 {"updated_count": int}

### 4.3 Notifications API（管理员）

7. **POST /api/v1/admin/notifications**
   - 描述: 批量创建通知（管理员）
   - 认证: Strict Auth + Admin权限
   - 请求体: NotificationCreateRequest
   - 成功响应: 200 OK，返回 NotificationBatchCreateResponse

8. **GET /api/v1/admin/notifications**
   - 描述: 获取通知列表（管理员，支持多条件筛选）
   - 认证: Strict Auth + Admin权限
   - 查询参数: page, size, user_id, notification_type, is_read
   - 成功响应: 200 OK，返回 NotificationListResponse

9. **PATCH /api/v1/admin/notifications/{notification_id}**
   - 描述: 更新通知（管理员，仅title和content）
   - 认证: Strict Auth + Admin权限
   - 请求体: NotificationUpdateRequest
   - 成功响应: 200 OK，返回 NotificationItem

10. **DELETE /api/v1/admin/notifications/{notification_id}**
    - 描述: 删除通知（管理员）
    - 认证: Strict Auth + Admin权限
    - 成功响应: 200 OK

11. **POST /api/v1/admin/notifications/batch-delete**
    - 描述: 批量删除通知（管理员）
    - 认证: Strict Auth + Admin权限
    - 请求体: NotificationBatchDeleteRequest
    - 成功响应: 200 OK，返回 {"deleted_count": int}

## 5. 权限设计

### 5.1 User Preferences权限

- 所有接口：仅限当前用户访问自己的偏好设置
- 无管理员权限要求

### 5.2 Notifications权限

- **用户接口**（/users/me/notifications/*）：仅限当前用户访问自己的通知
- **管理员接口**（/admin/notifications/*）：需要 ADMIN 或 SUPERADMIN 权限

## 6. 业务逻辑要点

1. **User Preferences**:
   - 首次访问时，如果没有记录，返回默认偏好（不保存到数据库）
   - 更新时，使用 Upsert 模式（不存在则创建，存在则更新）
   - `pinned_categories` 最多5个（Schema验证）
   - `theme_mode='scheduled'` 时，必须提供 `theme_scheduled_dark_time` 和 `theme_scheduled_light_time`（Schema验证）

2. **Notifications**:
   - 用户只能查看自己的通知（SQL级权限过滤）
   - 管理员可以查看所有用户的通知
   - 批量创建时，`user_ids=[]` 表示通知所有用户
   - 批量删除时，必须提供 `notification_ids` 或 `delete_before` 之一（Schema验证）

## 7. 响应格式

所有API返回统一响应结构：
```json
{
  "code": 200,
  "message": "success",
  "data": {...},
  "timestamp": "2026-01-06T10:00:00Z"
}
```

分页接口返回格式：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 100,
    "page": 1,
    "size": 10,
    "items": [...],
    "has_more": true
  },
  "timestamp": "2026-01-06T10:00:00Z"
}
```

## 8. 错误码

- `2001`: 资源不存在
- `4001`: 参数校验失败
- `4003`: 权限不足
- `1002`: 内部服务器错误
