# 用户偏好与通知模块 - Pydantic Schema代码生成提示词

**版本**: V1.0  
**创建日期**: 2026-01-18  
**模块名**: user_preference_notification  
**功能模块**: 用户偏好与通知  
**开发模式**: 增量开发（新增Schema文件）

---

## 1. 角色定义

你是一名精通Pydantic v2和FastAPI的资深Python后端工程师。你的任务是根据本文档的要求，生成符合项目规范的Pydantic Schema代码。

**核心要求**:
- 严格遵循Pydantic v2最佳实践
- 遵循Clean Architecture（学院派）架构风格
- 确保Schema与设计文档完全一致
- 使用`ConfigDict(from_attributes=True)`支持ORM模型转换
- 使用`Field`进行字段验证和文档化
- 实现自定义验证器（`field_validator`和`model_validator`）
- 使用`Literal`类型限制枚举值

---

## 2. 项目结构信息

### 2.1 目标文件路径

**新增文件**: `backend/live_core_service/app/schemas/user_preference_notification.py`

**更新文件**: `backend/live_core_service/app/schemas/__init__.py`（增量模式：添加新Schema的导入）

### 2.2 项目技术栈

- **Python版本**: 3.9+
- **Pydantic版本**: 2.0+
- **FastAPI版本**: 0.100+

---

## 3. Schema定义

### 3.1 User Preferences Schemas

#### 3.1.1 UserPreferencesBase（基础Schema）

```python
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List, Dict, Any, Literal
import uuid
import datetime

class UserPreferencesBase(BaseModel):
    """用户偏好基础Schema"""
    theme_mode: Literal["auto", "light", "dark", "scheduled"] = Field(
        default="auto", 
        description="昼夜模式：auto=跟随系统, light=浅色, dark=深色, scheduled=定时切换"
    )
    theme_scheduled_dark_time: Optional[datetime.time] = Field(
        None, 
        description="定时深色模式开始时间（定时切换时使用）"
    )
    theme_scheduled_light_time: Optional[datetime.time] = Field(
        None, 
        description="定时浅色模式开始时间（定时切换时使用）"
    )
    pinned_categories: Optional[List[uuid.UUID]] = Field(
        None, 
        max_length=5, 
        description="固定的科室ID，最多5个"
    )
    homepage_view_mode: Literal["double", "single"] = Field(
        default="double", 
        description="首页视图模式：double=双列瀑布流, single=单列列表"
    )
    cellular_warning_enabled: Optional[bool] = Field(
        True, 
        description="是否启用流量提醒"
    )
    auto_reduce_quality: Optional[bool] = Field(
        True, 
        description="流量下自动降画质"
    )
    auto_play_on_wifi: Optional[bool] = Field(
        False, 
        description="WiFi下自动播放"
    )
    extra: Optional[Dict[str, Any]] = Field(
        None, 
        description="其他扩展偏好设置"
    )
    
    @field_validator('pinned_categories')
    @classmethod
    def validate_pinned_categories(cls, v: Optional[List[uuid.UUID]]) -> Optional[List[uuid.UUID]]:
        """验证固定科室数量"""
        if v is not None and len(v) > 5:
            raise ValueError('固定科室最多5个')
        return v
    
    @model_validator(mode='after')
    def validate_scheduled_times(self):
        """验证定时切换时间"""
        if self.theme_mode == 'scheduled':
            if not self.theme_scheduled_dark_time or not self.theme_scheduled_light_time:
                raise ValueError('定时切换模式需要设置深色和浅色模式的开始时间')
        return self
```

**关键说明**:
1. **Literal类型**: 使用`Literal`限制`theme_mode`和`homepage_view_mode`的可选值
2. **Field验证**: 使用`max_length=5`限制`pinned_categories`数组长度
3. **field_validator**: 自定义验证器检查`pinned_categories`长度
4. **model_validator**: 跨字段验证，确保`scheduled`模式下必须设置时间

#### 3.1.2 UserPreferencesUpdate（更新请求Schema）

```python
class UserPreferencesUpdate(UserPreferencesBase):
    """更新用户偏好请求Schema（部分更新）"""
    theme_mode: Optional[Literal["auto", "light", "dark", "scheduled"]] = None
    homepage_view_mode: Optional[Literal["double", "single"]] = None
```

**关键说明**:
- 继承自`UserPreferencesBase`
- 所有字段都是可选的，支持部分更新（PATCH）
- 重写`theme_mode`和`homepage_view_mode`为`Optional`

#### 3.1.3 UserPreferencesItem（响应Schema）

```python
from pydantic import ConfigDict

class UserPreferencesItem(UserPreferencesBase):
    """用户偏好响应Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime
```

**关键说明**:
- 使用`ConfigDict(from_attributes=True)`支持从ORM模型转换
- 包含完整的数据库字段（id, user_id, 时间戳）

---

### 3.2 Notifications Schemas

#### 3.2.1 NotificationBase（基础Schema）

```python
class NotificationBase(BaseModel):
    """通知基础Schema"""
    title: str = Field(
        ..., 
        min_length=1, 
        max_length=255, 
        description="通知标题"
    )
    content: Optional[str] = Field(
        None, 
        description="通知内容"
    )
    notification_type: Literal["system", "subscription", "interaction"] = Field(
        default="system", 
        description="通知类型：system=系统通知, subscription=订阅通知, interaction=互动通知"
    )
    related_id: Optional[uuid.UUID] = Field(
        None, 
        description="关联资源ID"
    )
    related_type: Optional[str] = Field(
        None, 
        max_length=50, 
        description="关联资源类型"
    )
```

**关键说明**:
1. **必填字段**: `title`使用`...`标记为必填
2. **长度限制**: `title`限制1-255字符，`related_type`限制50字符
3. **Literal类型**: `notification_type`限制为三个可选值

#### 3.2.2 NotificationItem（响应Schema）

```python
class NotificationItem(NotificationBase):
    """通知响应Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    user_id: uuid.UUID
    is_read: bool
    created_at: datetime.datetime
```

**关键说明**:
- 包含完整的数据库字段
- `is_read`字段用于标识通知已读状态

#### 3.2.3 NotificationCreateRequest（Admin创建通知请求）

```python
class NotificationCreateRequest(BaseModel):
    """Admin创建通知请求Schema"""
    user_ids: List[uuid.UUID] = Field(
        ..., 
        description="接收通知的用户ID列表，空列表表示全部用户"
    )
    title: str = Field(..., min_length=1, max_length=255)
    content: Optional[str] = None
    notification_type: Literal["system", "subscription", "interaction"] = Field(default="system")
    related_id: Optional[uuid.UUID] = None
    related_type: Optional[str] = None
```

**关键说明**:
- `user_ids`为空列表时表示发送给所有用户
- 包含通知的基本信息字段

#### 3.2.4 NotificationBatchCreateResponse（批量创建响应）

```python
class NotificationBatchCreateResponse(BaseModel):
    """批量创建通知响应Schema"""
    total_created: int = Field(..., description="成功创建的通知数量")
    user_ids: List[uuid.UUID] = Field(..., description="接收通知的用户ID列表")
```

#### 3.2.5 NotificationUpdateRequest（Admin更新通知请求）

```python
class NotificationUpdateRequest(BaseModel):
    """Admin更新通知请求Schema"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = None
```

**关键说明**:
- 所有字段可选，支持部分更新
- 只能更新`title`和`content`字段

#### 3.2.6 NotificationBatchDeleteRequest（批量删除请求）

```python
class NotificationBatchDeleteRequest(BaseModel):
    """批量删除通知请求Schema"""
    notification_ids: Optional[List[uuid.UUID]] = Field(
        None, 
        description="通知ID列表"
    )
    delete_before: Optional[datetime.datetime] = Field(
        None, 
        description="删除此日期之前的通知"
    )
    notification_type: Optional[Literal["system", "subscription", "interaction"]] = None
    is_read: Optional[bool] = None
    
    @model_validator(mode='after')
    def check_params(self):
        """验证至少提供一个删除条件"""
        if not self.notification_ids and not self.delete_before:
            raise ValueError("必须提供 notification_ids 或 delete_before 参数之一")
        return self
```

**关键说明**:
- 支持按ID列表删除或按时间删除
- 使用`model_validator`确保至少提供一个删除条件
- 可选的类型和已读状态筛选

---

### 3.3 分页响应Schemas

#### 3.3.1 NotificationListResponse（通知列表响应）

```python
class NotificationListResponse(BaseModel):
    """通知列表响应Schema"""
    items: List[NotificationItem] = Field(..., description="通知列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    has_more: bool = Field(..., description="是否有更多数据")
```

**关键说明**:
- 标准分页响应结构
- `has_more`字段方便前端判断是否还有更多数据

---

## 4. 完整文件结构

```python
"""
用户偏好与通知模块 - Pydantic Schema定义

本模块包含用户偏好设置和通知系统的API数据验证和序列化模型。
"""

from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from typing import Optional, List, Dict, Any, Literal
import uuid
import datetime


# ==================== User Preferences Schemas ====================

class UserPreferencesBase(BaseModel):
    """用户偏好基础Schema"""
    # ... (完整定义见3.1.1节)


class UserPreferencesUpdate(UserPreferencesBase):
    """更新用户偏好请求Schema（部分更新）"""
    # ... (完整定义见3.1.2节)


class UserPreferencesItem(UserPreferencesBase):
    """用户偏好响应Schema"""
    # ... (完整定义见3.1.3节)


# ==================== Notifications Schemas ====================

class NotificationBase(BaseModel):
    """通知基础Schema"""
    # ... (完整定义见3.2.1节)


class NotificationItem(NotificationBase):
    """通知响应Schema"""
    # ... (完整定义见3.2.2节)


class NotificationCreateRequest(BaseModel):
    """Admin创建通知请求Schema"""
    # ... (完整定义见3.2.3节)


class NotificationBatchCreateResponse(BaseModel):
    """批量创建通知响应Schema"""
    # ... (完整定义见3.2.4节)


class NotificationUpdateRequest(BaseModel):
    """Admin更新通知请求Schema"""
    # ... (完整定义见3.2.5节)


class NotificationBatchDeleteRequest(BaseModel):
    """批量删除通知请求Schema"""
    # ... (完整定义见3.2.6节)


class NotificationListResponse(BaseModel):
    """通知列表响应Schema"""
    # ... (完整定义见3.3.1节)
```

---

## 5. 代码生成要求

### 5.1 导入顺序

```python
# 标准库
import uuid
import datetime

# 第三方库
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from typing import Optional, List, Dict, Any, Literal
```

### 5.2 代码规范

1. **类文档字符串**: 每个Schema类必须有docstring
2. **Field描述**: 所有字段使用`Field`的`description`参数
3. **类型注解**: 使用完整的类型注解（包括`Optional`、`List`等）
4. **验证器**: 使用`@classmethod`装饰器和类型注解
5. **分组注释**: 使用注释分隔不同功能的Schema组

### 5.3 命名规范

- **Schema类名**: 大驼峰+功能后缀（如`UserPreferencesItem`、`NotificationCreateRequest`）
- **字段名**: 小写+下划线（如`theme_mode`、`notification_type`）
- **验证器方法**: `validate_{field_name}`

---

## 6. 更新__init__.py文件

在生成Schema代码后，必须更新`backend/live_core_service/app/schemas/__init__.py`文件：

```python
# 在文件末尾添加以下导入
from app.schemas.user_preference_notification import (
    UserPreferencesBase,
    UserPreferencesUpdate,
    UserPreferencesItem,
    NotificationBase,
    NotificationItem,
    NotificationCreateRequest,
    NotificationBatchCreateResponse,
    NotificationUpdateRequest,
    NotificationBatchDeleteRequest,
    NotificationListResponse,
)

# 更新__all__列表
__all__ = [
    # ... 现有Schema ...
    "UserPreferencesBase",
    "UserPreferencesUpdate",
    "UserPreferencesItem",
    "NotificationBase",
    "NotificationItem",
    "NotificationCreateRequest",
    "NotificationBatchCreateResponse",
    "NotificationUpdateRequest",
    "NotificationBatchDeleteRequest",
    "NotificationListResponse",
]
```

---

## 7. 验证清单

生成代码后，请验证以下内容：

- [ ] 所有Schema类都有docstring
- [ ] 所有字段都使用`Field`并包含`description`
- [ ] `Literal`类型正确限制枚举值
- [ ] `UserPreferencesUpdate`的所有字段都是`Optional`
- [ ] 响应Schema使用`ConfigDict(from_attributes=True)`
- [ ] `pinned_categories`有长度验证（最多5个）
- [ ] `scheduled`模式有时间验证
- [ ] `NotificationBatchDeleteRequest`有参数验证
- [ ] 所有UUID字段使用`uuid.UUID`类型
- [ ] 所有时间字段使用`datetime.datetime`或`datetime.time`类型
- [ ] 代码通过linter检查（无语法错误）

---

## 8. 注意事项

1. **Pydantic v2语法**: 使用`ConfigDict`而非`Config`类
2. **验证器装饰器**: 使用`@field_validator`和`@model_validator`（v2语法）
3. **from_attributes**: 替代v1的`orm_mode=True`
4. **Field约束**: 使用`min_length`、`max_length`、`ge`、`le`等约束
5. **Optional vs 默认值**: 区分可选字段（`Optional`）和有默认值的字段
6. **Literal类型**: 用于限制字符串枚举值，提供更好的类型检查

---

**生成指令**: 请严格按照本文档的要求生成Pydantic Schema代码，保存到`backend/live_core_service/app/schemas/user_preference_notification.py`，并更新`__init__.py`文件。
