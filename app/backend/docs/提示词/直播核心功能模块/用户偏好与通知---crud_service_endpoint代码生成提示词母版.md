# 用户偏好与通知模块 - CRUD/Service/API代码生成提示词母版

**版本**: V1.0  
**创建日期**: 2026-01-18  
**模块名**: user_preference_notification  
**功能模块**: 用户偏好与通知  
**开发模式**: 增量开发

---

## 1. 角色定义

你是一名精通"学院派"架构（Clean Architecture）的资深Python后端架构师。你擅长将业务需求解耦，并严格执行分层架构与高质量的工程实践。

---

## 2. 核心上下文信息

### 2.1 项目结构

```
backend/live_core_service/
├── app/
│   ├── models/                           # SQLAlchemy模型（数据层）
│   │   ├── __init__.py
│   │   ├── user_preference_notification.py  # ✅ 已生成
│   │   └── ...
│   ├── schemas/                          # Pydantic Schema（数据验证层）
│   │   ├── __init__.py
│   │   ├── user_preference_notification.py  # ✅ 已生成
│   │   └── ...
│   ├── crud/                             # CRUD层（数据访问层）
│   │   ├── __init__.py
│   │   ├── user_preference_notification.py  # 📝 待生成
│   │   └── ...
│   ├── services/                         # Service层（业务逻辑层）
│   │   ├── __init__.py
│   │   ├── user_preference_notification_service.py  # 📝 待生成
│   │   └── ...
│   ├── api/                              # API层（HTTP端点层）
│   │   └── v1/
│   │       ├── api.py                    # 路由注册
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── user_preference_notification.py  # 📝 待生成
│   │           └── ...
│   ├── core/                             # 核心模块
│   │   ├── deps.py                       # 依赖注入
│   │   ├── response.py                   # 统一响应
│   │   └── ...
│   └── exceptions.py                     # 自定义异常
```

### 2.2 设计文档来源

**文档路径**: `docs/03_系统设计/直播核心功能设计文档_v6_用户偏好与通知模块设计文档.md`

**模块范围**:
- 2张数据表：`user_preferences`、`notifications`
- 11个API接口：User Preferences (2个)、Notifications (9个)

---

## 3. 已生成模型和Schema摘要

### 3.1 SQLAlchemy模型摘要 (app/models/user_preference_notification.py)

#### 3.1.1 UserPreferences模型

**表名**: `user_preferences`

**关键字段**:
- `id`: UUID, 主键, default=uuid.uuid4()
- `user_id`: UUID, 唯一, 非空（users.public_id）
- `theme_mode`: String(20), default="auto"（auto/light/dark/scheduled）
- `theme_scheduled_dark_time`: Time, 可空
- `theme_scheduled_light_time`: Time, 可空
- `pinned_categories`: JSONB, 可空（最多5个UUID）
- `homepage_view_mode`: String(20), default="double"（double/single）
- `cellular_warning_enabled`: Boolean, default=True
- `auto_reduce_quality`: Boolean, default=True
- `auto_play_on_wifi`: Boolean, default=False
- `extra`: JSONB, 可空
- `created_at`: TIMESTAMP(timezone=True), server_default=func.now()
- `updated_at`: TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()

**索引**:
- `idx_user_preferences_user_id` on (`user_id`)

**约束**:
- `user_id` UNIQUE（一对一关系）

#### 3.1.2 Notification模型

**表名**: `notifications`

**关键字段**:
- `id`: UUID, 主键, default=uuid.uuid4()
- `user_id`: UUID, 非空（users.public_id）
- `title`: String(255), 非空
- `content`: Text, 可空
- `notification_type`: String(50), default="system"（system/subscription/interaction）
- `related_id`: UUID, 可空（关联资源ID）
- `related_type`: String(50), 可空（关联资源类型）
- `is_read`: Boolean, default=False
- `created_at`: TIMESTAMP(timezone=True), server_default=func.now()

**索引**:
- `idx_notifications_user_id` on (`user_id`)
- `idx_notifications_user_is_read` on (`user_id`, `is_read`)
- `idx_notifications_created_at` on (`created_at`)

---

### 3.2 Pydantic Schema摘要 (app/schemas/user_preference_notification.py)

#### 3.2.1 User Preferences Schemas

**UserPreferencesBase**:
- 基础Schema，包含所有可更新字段
- 带验证器：`validate_pinned_categories`（最多5个）、`validate_scheduled_times`（scheduled模式验证）

**UserPreferencesUpdate**:
- 继承自UserPreferencesBase
- 所有字段可选，支持部分更新

**UserPreferencesItem**:
- 响应Schema，包含完整字段
- `ConfigDict(from_attributes=True)`

#### 3.2.2 Notifications Schemas

**NotificationBase**:
- 基础Schema，包含通知基本信息
- `title`必填，`content`可选

**NotificationItem**:
- 响应Schema，包含完整字段
- `ConfigDict(from_attributes=True)`

**NotificationCreateRequest**:
- Admin创建通知请求
- `user_ids`为空列表表示全部用户

**NotificationBatchCreateResponse**:
- 批量创建响应：`total_created`、`user_ids`

**NotificationUpdateRequest**:
- Admin更新通知请求
- 仅`title`和`content`可更新

**NotificationBatchDeleteRequest**:
- 批量删除请求
- 支持按ID列表或时间删除
- 带验证器：`check_params`（至少提供一个删除条件）

**NotificationListResponse**:
- 分页响应：`items`、`total`、`page`、`size`、`has_more`

---

## 4. 全项目通用安全与一致性规范

### 4.1 安全异步异常处理规范

**问题**: 在异步ORM操作中，如果在`try`块内访问ORM对象属性后发生异常，可能导致属性无法访问。

**强制要求**:
```python
# ❌ 错误示例
try:
    expert = await db.get(Expert, expert_id)
    await db.commit()
    return expert.user_id  # 如果commit()失败，expert可能已失效
except Exception as e:
    await db.rollback()
    raise
```

```python
# ✅ 正确示例
try:
    expert = await db.get(Expert, expert_id)
    user_id_value = expert.user_id  # 提前提取
    await db.commit()
    return user_id_value
except Exception as e:
    await db.rollback()
    raise
```

### 4.2 内部ID不得对外暴露规范

**强制要求**: 所有对外API响应中，不得直接暴露数据库内部自增ID。

- ✅ 使用UUID作为公开标识符
- ❌ 禁止在API响应中返回自增ID

### 4.3 API Schema与内部CRUD Schema严格区分规范

**强制要求**: API层的Schema定义与CRUD层的数据库查询分离。

- API Schema：定义对外响应结构
- CRUD层：返回ORM对象或字典
- Service层：负责转换

### 4.4 Enum字段声明规范

**强制要求**: SQLAlchemy中的Enum字段必须使用`native_enum=False`，避免PostgreSQL原生Enum类型限制。

```python
# ✅ 正确
Column(Enum(..., native_enum=False), ...)

# ❌ 错误
Column(Enum(...), ...)  # 默认native_enum=True
```

**本模块说明**: 本模块使用String类型存储枚举值（`theme_mode`、`notification_type`），Pydantic使用`Literal`类型限制。

### 4.5 环境变量驱动配置规范

**强制要求**:
- 所有配置通过`app.core.config.Settings`读取
- 禁止硬编码配置值
- 使用`.env`文件管理环境变量

### 4.6 RESTful API设计原则

1. **资源导向**: URL应表示资源，而非动作
   - ✅ `GET /api/v1/users/me/preferences`
   - ❌ `GET /api/v1/get_user_preferences`

2. **HTTP方法语义**:
   - GET: 查询
   - POST: 创建
   - PATCH: 部分更新
   - DELETE: 删除

3. **统一接口**: 使用标准响应格式
   ```json
   {
     "code": 200,
     "message": "success",
     "data": {...},
     "timestamp": "2026-01-18T10:00:00Z"
   }
   ```

4. **版本化**: 路由包含版本号（`/api/v1/`）

### 4.7 日志与错误消息脱敏规范

**强制要求**:
- UUID只记录前8位
- 敏感信息不记录
- 错误消息不暴露内部实现细节

```python
# ✅ 正确
logger.info(f"查询用户偏好: user_id={str(user_id)[:8]}")

# ❌ 错误
logger.info(f"查询用户偏好: user_id={user_id}, password={password}")
```

---

## 5. 详细实现模式与工程规范

### 5.1 CRUD层实现规范

#### 5.1.1 N+1问题防治

**强制使用**: `selectinload()` 或 `joinedload()`

```python
from sqlalchemy.orm import selectinload

# ✅ 正确
query = select(Notification).options(
    selectinload(Notification.user)  # 如果有关联
)
```

#### 5.1.2 分页模式

**强制要求**: 使用两次查询（COUNT + SELECT）

```python
# 1. COUNT查询
count_query = select(func.count()).select_from(query.subquery())
total = await db.scalar(count_query)

# 2. 数据查询
query = query.offset((page - 1) * size).limit(size)
result = await db.execute(query)
items = list(result.scalars().all())
```

#### 5.1.3 SQL级权限过滤

**强制要求**: 在SQL查询中添加权限过滤条件

```python
# 普通用户只能查看自己的通知
if role not in ['ADMIN', 'SUPERADMIN']:
    query = query.where(Notification.user_id == current_user_id)
```

#### 5.1.4 数据库初始化脚本更新

**强制要求**: 新增模型后，必须更新`app/models/__init__.py`

#### 5.1.5 事务处理

**CRUD层职责**: 只执行数据库操作，不调用`commit()`或`rollback()`，由Service层统一管理事务。

---

### 5.2 Service层实现规范

#### 5.2.1 业务编排

Service层负责：
- 调用多个CRUD函数
- 业务逻辑验证
- 权限检查
- 事务管理（`commit()`/`rollback()`）

#### 5.2.2 批量验证规范

**强制要求**: 对输入列表进行业务验证

```python
# ✅ 正确：批量验证用户ID是否存在
async def create_notifications_batch(self, user_ids: List[UUID], ...):
    if not user_ids:  # 空列表表示全部用户
        user_ids = await self._get_all_user_ids()
    else:
        # 验证用户ID
        valid_ids = await self._validate_user_ids(user_ids)
        if len(valid_ids) != len(user_ids):
            raise InvalidParameterException("部分用户ID不存在")
    # 批量创建
    ...
```

#### 5.2.3 权限模式

**强制使用**: 权限守卫函数（大写角色比较）

```python
def _check_admin_permission(self, user_role: Optional[str]) -> None:
    """检查管理员权限"""
    if user_role not in ['ADMIN', 'SUPERADMIN']:
        raise PermissionDeniedException("权限不足，需要管理员权限")
```

**角色检查强制要求**:
- 使用`['ADMIN', 'SUPERADMIN']`而非`['admin', 'superadmin']`
- 使用`['REGULAR', 'ADMIN', 'SUPERADMIN']`而非`['USER', 'ADMIN']`

---

### 5.3 API层实现规范

#### 5.3.1 API端点实现强制模板

**必须完整复制此模板**:

```python
from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.core.deps import get_db, get_current_user
from app.core.response import success_response, error_response
from app.exceptions import NotFoundException, PermissionDeniedException, InvalidParameterException

logger = logging.getLogger(__name__)
router = APIRouter(tags=["User Preferences & Notifications"])

@router.get("/users/me/preferences")
async def get_user_preferences(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取用户偏好设置"""
    # 🚨 必须在try之前提取user_id
    user_id = UUID(current_user.get("user_id") or current_user.get("sub"))
    user_id_for_logging = str(user_id)[:8]
    role = current_user.get("role", "REGULAR").upper()
    
    try:
        service = UserPreferenceNotificationService(db)
        result = await service.get_preferences(user_id, role)
        logger.info(f"获取用户偏好成功: user_id={user_id_for_logging}")
        return success_response(data=result)
    except NotFoundException as e:
        logger.warning(f"获取用户偏好失败（资源不存在）: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在")
        )
    except PermissionDeniedException as e:
        logger.warning(f"获取用户偏好失败（权限不足）: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=4003, message=str(e))
        )
    except InvalidParameterException as e:
        logger.warning(f"获取用户偏好失败（参数错误）: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message=str(e))
        )
    except Exception as e:
        logger.error(f"获取用户偏好失败（系统错误）: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )
```

**关键要点**:
1. 使用`JSONResponse`和`error_response()`，不使用`HTTPException`
2. `user_id`在`try`之前提取
3. 角色使用`.upper()`转大写
4. 每个异常类型单独捕获
5. 记录日志（UUID只取前8位）

#### 5.3.2 导入规范

**强制导入**:
```python
from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.core.deps import get_db, get_current_user
from app.core.response import success_response, error_response
from app.exceptions import NotFoundException, PermissionDeniedException, InvalidParameterException
```

**禁止导入**:
```python
from fastapi import HTTPException  # ❌ 禁止使用
```

#### 5.3.3 路由定义规范

**APIRouter定义**:

```python
# ✅ 正确：不指定prefix
router = APIRouter(tags=["User Preferences & Notifications"])

# ❌ 错误：不要在这里指定prefix
router = APIRouter(prefix="/preferences", tags=[...])  # ❌
```

**路由前缀层级**:
- **顶层注册**（`app/api/v1/api.py`）：`/user-preferences-notifications`
- **端点路径**：`/users/me/preferences`、`/users/me/notifications`、`/admin/notifications`
- **完整URL**：`/api/v1/users/me/preferences`

**URL拼接规范**:
- 禁止手动拼接URL
- 使用`Request.url_for()`或直接返回相对路径

#### 5.3.4 响应格式化规范

**Service层返回**: Pydantic Schema对象

```python
# Service层
async def get_preferences(self, user_id: UUID, role: str) -> UserPreferencesItem:
    prefs = await crud.get_preferences(db, user_id)
    return UserPreferencesItem.model_validate(prefs)
```

**API层格式化**: 使用`success_response()`

```python
# API层
result = await service.get_preferences(user_id, role)
return success_response(data=result)  # 自动调用model_dump()
```

---

## 6. 交付物

### 6.1 CRUD层代码（app/crud/user_preference_notification.py）

**需要实现的函数**:

1. **User Preferences CRUD**:
   - `get_preferences(db, user_id)`: 获取用户偏好（首次访问返回默认值）
   - `create_or_update_preferences(db, user_id, prefs_in)`: 创建或更新用户偏好

2. **Notifications CRUD**:
   - `get_notifications(db, user_id, page, size, is_read, notification_type)`: 获取通知列表（分页）
   - `get_unread_count(db, user_id)`: 获取未读通知数量
   - `mark_as_read(db, notification_id, user_id)`: 标记通知为已读
   - `mark_all_as_read(db, user_id)`: 标记所有通知为已读
   - `create_notification(db, notification)`: 创建单条通知
   - `bulk_create_notifications(db, notifications_list)`: 批量创建通知
   - `get_notifications_admin(db, page, size, user_id, notification_type, is_read)`: 管理员获取通知列表
   - `update_notification(db, notification_id, update_data)`: 更新通知
   - `delete_notification(db, notification_id)`: 删除单条通知
   - `batch_delete_notifications(db, notification_ids, delete_before, notification_type, is_read)`: 批量删除通知

---

### 6.2 Service层代码（app/services/user_preference_notification_service.py）

**类定义**:
```python
class UserPreferenceNotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.logger = logging.getLogger(__name__)
```

**需要实现的方法**:

**User Preferences Service**:
1. `get_preferences(user_id, role)`: 获取用户偏好
2. `update_preferences(user_id, prefs_update, role)`: 更新用户偏好

**Notifications Service**:
3. `get_notifications_list(user_id, page, size, is_read, notification_type, role)`: 获取通知列表
4. `get_unread_count(user_id)`: 获取未读数量
5. `mark_notification_as_read(notification_id, user_id, role)`: 标记通知为已读
6. `mark_all_notifications_as_read(user_id)`: 标记所有通知为已读
7. `create_notifications_batch(user_ids, notification_data, admin_role)`: Admin批量创建通知
8. `get_notifications_list_admin(page, size, user_id_filter, notification_type, is_read, admin_role)`: Admin获取通知列表
9. `update_notification(notification_id, update_data, admin_role)`: Admin更新通知
10. `delete_notification(notification_id, admin_role)`: Admin删除通知
11. `batch_delete_notifications(delete_request, admin_role)`: Admin批量删除通知

**权限守卫方法**:
- `_check_admin_permission(user_role)`: 检查管理员权限
- `_check_user_preferences_ownership(resource_owner_id, current_user_id, user_role)`: 检查用户资源所有权

---

### 6.3 API层代码（app/api/v1/endpoints/user_preference_notification.py）

**需要实现的端点**:

**User Preferences API**:
1. `GET /users/me/preferences`: 获取用户偏好设置
2. `PATCH /users/me/preferences`: 更新用户偏好设置

**Notifications API (User)**:
3. `GET /users/me/notifications`: 获取通知列表
4. `GET /users/me/notifications/unread-count`: 获取未读通知数量
5. `POST /users/me/notifications/{notification_id}/read`: 标记通知为已读
6. `POST /users/me/notifications/read-all`: 标记所有通知为已读

**Notifications API (Admin)**:
7. `POST /admin/notifications`: 创建通知（批量）
8. `GET /admin/notifications`: 获取通知列表（管理员）
9. `PATCH /admin/notifications/{notification_id}`: 更新通知
10. `DELETE /admin/notifications/{notification_id}`: 删除单条通知
11. `POST /admin/notifications/batch-delete`: 批量删除通知

**路由定义**:
```python
router = APIRouter(tags=["User Preferences & Notifications"])
```

---

## 7. 代码生成检查清单

生成代码后，必须验证以下项：

### 7.1 CRUD层检查
- [ ] 所有函数都使用`async def`
- [ ] 分页使用两次查询（COUNT + SELECT）
- [ ] 使用`selectinload()`防止N+1
- [ ] SQL级权限过滤（普通用户只能查看自己的数据）
- [ ] 不调用`commit()`或`rollback()`

### 7.2 Service层检查
- [ ] 所有方法都有权限检查
- [ ] 使用`_check_admin_permission()`检查管理员权限
- [ ] 事务管理正确（`commit()`/`rollback()`）
- [ ] 批量操作有验证逻辑
- [ ] 角色字符串使用大写（`REGULAR`、`ADMIN`、`SUPERADMIN`）

### 7.3 API层检查
- [ ] 所有端点都使用完整的异常处理模板
- [ ] 使用`JSONResponse`和`error_response()`
- [ ] `user_id`在`try`之前提取
- [ ] 记录日志（UUID只取前8位）
- [ ] `APIRouter`不指定`prefix`
- [ ] 导入`success_response`、`error_response`（不导入`HTTPException`）

### 7.4 API-Service对应关系检查
- [ ] 每个API端点都有对应的Service方法
- [ ] Service方法签名与API调用匹配
- [ ] 权限检查在Service层完成

---

**生成指令**: 请使用本母版生成CRUD层和Service/API层的具体代码生成提示词文档。
