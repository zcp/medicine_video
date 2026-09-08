# 用户偏好与通知模块 - SQLAlchemy模型与Pydantic模型一致性检查提示词

**版本**: V1.0  
**创建日期**: 2026-01-18  
**模块名**: user_preference_notification  
**功能模块**: 用户偏好与通知  
**检测类型**: SQLAlchemy模型 ↔ Pydantic Schema 一致性

---

## 1. 角色定义

你是一名精通代码审查和质量保证的资深技术架构师。你的任务是检查SQLAlchemy模型和Pydantic Schema之间的一致性，确保两者定义完全匹配。

**核心要求**:
- 逐字段对比SQLAlchemy模型和Pydantic Schema
- 检查字段名、类型、约束是否一致
- 检查必填/可选字段是否匹配
- 生成详细的一致性检测报告

---

## 2. 检测目标文件

### 2.1 SQLAlchemy模型文件

**文件路径**: `backend/live_core_service/app/models/user_preference_notification.py`

**包含模型**:
- `UserPreferences`
- `Notification`

### 2.2 Pydantic Schema文件

**文件路径**: `backend/live_core_service/app/schemas/user_preference_notification.py`

**包含Schema**:
- `UserPreferencesBase`
- `UserPreferencesUpdate`
- `UserPreferencesItem`
- `NotificationBase`
- `NotificationItem`
- `NotificationCreateRequest`
- `NotificationBatchCreateResponse`
- `NotificationUpdateRequest`
- `NotificationBatchDeleteRequest`
- `NotificationListResponse`

---

## 3. 检测清单

### 3.1 UserPreferences模型 ↔ UserPreferencesItem Schema

#### 3.1.1 字段名称一致性

检查以下字段是否在两者中都存在且名称完全一致：

- [ ] `id`
- [ ] `user_id`
- [ ] `theme_mode`
- [ ] `theme_scheduled_dark_time`
- [ ] `theme_scheduled_light_time`
- [ ] `pinned_categories`
- [ ] `homepage_view_mode`
- [ ] `cellular_warning_enabled`
- [ ] `auto_reduce_quality`
- [ ] `auto_play_on_wifi`
- [ ] `extra`
- [ ] `created_at`
- [ ] `updated_at`

#### 3.1.2 字段类型一致性

| 字段名 | SQLAlchemy类型 | Pydantic类型 | 是否一致 |
|--------|----------------|--------------|----------|
| `id` | `UUID(as_uuid=True)` | `uuid.UUID` | ✅ |
| `user_id` | `UUID(as_uuid=True)` | `uuid.UUID` | ✅ |
| `theme_mode` | `String(20)` | `Literal["auto", "light", "dark", "scheduled"]` | ✅ |
| `theme_scheduled_dark_time` | `Time` | `Optional[datetime.time]` | ✅ |
| `theme_scheduled_light_time` | `Time` | `Optional[datetime.time]` | ✅ |
| `pinned_categories` | `JSONB` | `Optional[List[uuid.UUID]]` | ✅ |
| `homepage_view_mode` | `String(20)` | `Literal["double", "single"]` | ✅ |
| `cellular_warning_enabled` | `Boolean` | `Optional[bool]` | ✅ |
| `auto_reduce_quality` | `Boolean` | `Optional[bool]` | ✅ |
| `auto_play_on_wifi` | `Boolean` | `Optional[bool]` | ✅ |
| `extra` | `JSONB` | `Optional[Dict[str, Any]]` | ✅ |
| `created_at` | `TIMESTAMP(timezone=True)` | `datetime.datetime` | ✅ |
| `updated_at` | `TIMESTAMP(timezone=True)` | `datetime.datetime` | ✅ |

#### 3.1.3 必填/可选字段一致性

| 字段名 | SQLAlchemy | Pydantic | 是否一致 |
|--------|------------|----------|----------|
| `id` | 主键（必填） | 必填 | ✅ |
| `user_id` | `nullable=False` | 必填 | ✅ |
| `theme_mode` | `nullable=False, default="auto"` | `default="auto"` | ✅ |
| `theme_scheduled_dark_time` | `nullable=True` | `Optional` | ✅ |
| `theme_scheduled_light_time` | `nullable=True` | `Optional` | ✅ |
| `pinned_categories` | `nullable=True` | `Optional` | ✅ |
| `homepage_view_mode` | `nullable=False, default="double"` | `default="double"` | ✅ |
| `cellular_warning_enabled` | `nullable=False, default=True` | `Optional[bool] = True` | ✅ |
| `auto_reduce_quality` | `nullable=False, default=True` | `Optional[bool] = True` | ✅ |
| `auto_play_on_wifi` | `nullable=False, default=False` | `Optional[bool] = False` | ✅ |
| `extra` | `nullable=True` | `Optional` | ✅ |
| `created_at` | `nullable=False, server_default` | 必填 | ✅ |
| `updated_at` | `nullable=False, server_default` | 必填 | ✅ |

---

### 3.2 Notification模型 ↔ NotificationItem Schema

#### 3.2.1 字段名称一致性

检查以下字段是否在两者中都存在且名称完全一致：

- [ ] `id`
- [ ] `user_id`
- [ ] `title`
- [ ] `content`
- [ ] `notification_type`
- [ ] `related_id`
- [ ] `related_type`
- [ ] `is_read`
- [ ] `created_at`

#### 3.2.2 字段类型一致性

| 字段名 | SQLAlchemy类型 | Pydantic类型 | 是否一致 |
|--------|----------------|--------------|----------|
| `id` | `UUID(as_uuid=True)` | `uuid.UUID` | ✅ |
| `user_id` | `UUID(as_uuid=True)` | `uuid.UUID` | ✅ |
| `title` | `String(255)` | `str` (max_length=255) | ✅ |
| `content` | `Text` | `Optional[str]` | ✅ |
| `notification_type` | `String(50)` | `Literal["system", "subscription", "interaction"]` | ✅ |
| `related_id` | `UUID(as_uuid=True)` | `Optional[uuid.UUID]` | ✅ |
| `related_type` | `String(50)` | `Optional[str]` (max_length=50) | ✅ |
| `is_read` | `Boolean` | `bool` | ✅ |
| `created_at` | `TIMESTAMP(timezone=True)` | `datetime.datetime` | ✅ |

#### 3.2.3 必填/可选字段一致性

| 字段名 | SQLAlchemy | Pydantic | 是否一致 |
|--------|------------|----------|----------|
| `id` | 主键（必填） | 必填 | ✅ |
| `user_id` | `nullable=False` | 必填 | ✅ |
| `title` | `nullable=False` | 必填 | ✅ |
| `content` | `nullable=True` | `Optional` | ✅ |
| `notification_type` | `nullable=False, default="system"` | `default="system"` | ✅ |
| `related_id` | `nullable=True` | `Optional` | ✅ |
| `related_type` | `nullable=True` | `Optional` | ✅ |
| `is_read` | `nullable=False, default=False` | 必填 | ✅ |
| `created_at` | `nullable=False, server_default` | 必填 | ✅ |

---

## 4. 特殊验证项

### 4.1 ConfigDict配置

- [ ] `UserPreferencesItem`使用`ConfigDict(from_attributes=True)`
- [ ] `NotificationItem`使用`ConfigDict(from_attributes=True)`

### 4.2 自定义验证器

- [ ] `UserPreferencesBase`有`validate_pinned_categories`验证器（最多5个）
- [ ] `UserPreferencesBase`有`validate_scheduled_times`验证器（scheduled模式必须设置时间）
- [ ] `NotificationBatchDeleteRequest`有`check_params`验证器（至少提供一个删除条件）

### 4.3 Literal类型限制

- [ ] `theme_mode`限制为`["auto", "light", "dark", "scheduled"]`
- [ ] `homepage_view_mode`限制为`["double", "single"]`
- [ ] `notification_type`限制为`["system", "subscription", "interaction"]`

---

## 5. 输出格式

请生成以下格式的检测报告：

```markdown
# 用户偏好与通知模块 - SQLAlchemy模型与Pydantic模型一致性检测报告

**检测日期**: 2026-01-18  
**检测结果**: ✅ 完全一致 / ⚠️ 发现问题

---

## 1. UserPreferences模型 ↔ UserPreferencesItem Schema

### 1.1 字段名称一致性
- ✅ 所有字段名称完全一致

### 1.2 字段类型一致性
- ✅ 所有字段类型匹配

### 1.3 必填/可选字段一致性
- ✅ 所有字段的必填/可选属性匹配

### 1.4 特殊验证
- ✅ ConfigDict配置正确
- ✅ 自定义验证器实现正确
- ✅ Literal类型限制正确

---

## 2. Notification模型 ↔ NotificationItem Schema

### 2.1 字段名称一致性
- ✅ 所有字段名称完全一致

### 2.2 字段类型一致性
- ✅ 所有字段类型匹配

### 2.3 必填/可选字段一致性
- ✅ 所有字段的必填/可选属性匹配

### 2.4 特殊验证
- ✅ ConfigDict配置正确
- ✅ Literal类型限制正确

---

## 3. 总体结论

✅ SQLAlchemy模型与Pydantic Schema完全一致，无需修复。

或

⚠️ 发现以下问题需要修复：
1. [问题描述]
2. [问题描述]

---

## 4. 建议修复方案

如果发现问题，提供详细的修复建议。
```

---

**执行指令**: 请严格按照本文档的检测清单，逐项检查SQLAlchemy模型和Pydantic Schema的一致性，并生成详细的检测报告。
