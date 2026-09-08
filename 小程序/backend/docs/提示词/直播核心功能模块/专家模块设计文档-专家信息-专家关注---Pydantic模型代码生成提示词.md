# 专家模块设计文档-专家信息-专家关注 - Pydantic模型代码生成提示词文档

**版本**: V1.0  
**创建日期**: 2026-01-18  
**生成器**: AI 自动化生成系统  
**基于设计文档**: @docs/03_系统设计/直播核心功能设计文档_v6_专家模块设计文档-专家信息-专家关注.md

---

## 📌 文档用途

本文档是用于指导 AI 代码生成器根据设计文档生成 Pydantic Schema 代码的详细提示词文档。

**生成目标**：
- 生成完整的 Pydantic Schema 代码（用于 API 请求和响应）
- 确保生成的代码与设计文档完全一致
- 遵循项目架构规范和最佳实践

---

## 🎯 核心设计原则

### 1. 不使用 featured_expert_id

**关键要求**：
- ❌ **禁止定义** `featured_expert_id` 字段
- ❌ **禁止定义** 单个专家的关联字段
- ✅ **必须定义** `experts` 数组或 `session_experts` 数组字段
- ✅ **必须支持** `role` 和 `sort_order` 字段

### 2. 支持多个专家

**响应结构**：
- 使用数组（`List[Type]`）定义多个专家
- 包含 `role` 字段区分专家角色（主讲、主持、嘉宾）
- 包含 `sort_order` 字段控制显示顺序

---

## 📐 Pydantic Schema 生成要求

### 1. 通用要求

**遵循项目架构**：
- Schema 文件路径：`backend/live_core_service/app/schemas/experts.py`
- 基类：`pydantic.BaseModel`
- 配置：`model_config = ConfigDict(from_attributes=True)`（支持 ORM 模式）

**类型验证**：
- 所有字段必须使用 `Field()` 添加验证和描述
- 字符串字段必须限制长度（`min_length`, `max_length`）
- 可选字段使用 `Optional[type]` 和 `None` 默认值

**枚举类型**：
- 使用 Pydantic `str` 定义角色枚举（或使用 `Literal`）
- 如果使用了 SQLAlchemy 枚举，需要定义对应的 Pydantic 枚举

**嵌套模型**：
- 使用 `List[Model]` 或 `Optional[Model]` 定义嵌套结构
- 使用 `model_config = ConfigDict(from_attributes=True)` 支持嵌套模型

**响应模型**：
- 统一响应结构：`code`, `message`, `data`, `timestamp`
- 分页响应结构：`total`, `page`, `size`, `items`

---

### 2. 专家信息 Schemas

**Schema 列表**：

1. **ExpertBase** - 专家基础 Schema
2. **ExpertCreate** - 创建专家请求 Schema
3. **ExpertUpdate** - 更新专家请求 Schema
4. **ExpertItem** - 专家响应 Schema
5. **FeaturedExpertItem** - 首页推荐专家简要 Schema

**ExpertBase 要求**：
```python
class ExpertBase(BaseModel):
    """专家基础Schema"""
    name: str = Field(..., min_length=1, max_length=120, description="专家姓名")
    title: Optional[str] = Field(None, max_length=120, description="职称")
    hospital: Optional[str] = Field(None, max_length=200, description="所属医院")
    department: Optional[str] = Field(None, max_length=120, description="科室")
    expertise_areas: Optional[str] = Field(None, description="擅长领域")
    bio: Optional[str] = Field(None, max_length=1000, description="个人简介")
    avatar_url: Optional[str] = Field(None, max_length=512)
```

**ExpertCreate 要求**：
```python
class ExpertCreate(ExpertBase):
    """创建专家请求Schema"""
    user_id: Optional[uuid.UUID] = Field(None, description="关联用户ID（可选）")
    is_featured: Optional[bool] = Field(False, description="是否首页推荐")
    sort_order: Optional[int] = Field(0, ge=0)
    contact_info: Optional[dict] = Field(None, description="联系方式JSONB")
```

**ExpertUpdate 要求**：
```python
class ExpertUpdate(BaseModel):
    """更新专家请求Schema（部分更新）"""
    model_config = ConfigDict(from_attributes=True)
    
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    title: Optional[str] = None
    hospital: Optional[str] = None
    department: Optional[str] = None
    expertise_areas: Optional[str] = None
    bio: Optional[str] = Field(None, max_length=1000)
    avatar_url: Optional[str] = None
    is_featured: Optional[bool] = None
    sort_order: Optional[int] = Field(None, ge=0)
```

**ExpertItem 要求**：
```python
class ExpertItem(ExpertBase):
    """专家响应Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    is_featured: bool
    sort_order: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
```

**FeaturedExpertItem 要求**：
```python
class FeaturedExpertItem(BaseModel):
    """首页推荐专家简要Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    name: str
    title: Optional[str] = None
    hospital: Optional[str] = None
    avatar_url: Optional[str] = None
```

---

### 3. 专家关注 Schemas

**Schema 列表**：

1. **ExpertFollowRequest** - 关注专家请求 Schema
2. **ExpertFollowResponse** - 关注专家响应 Schema
3. **FollowedExpertItem** - 关注的专家响应 Schema
4. **FollowedExpertsResponse** - 关注列表响应 Schema

**ExpertFollowRequest 要求**：
```python
class ExpertFollowRequest(BaseModel):
    """关注专家请求Schema"""
    expert_id: uuid.UUID = Field(..., description="专家ID")
```

**ExpertFollowResponse 要求**：
```python
class ExpertFollowResponse(BaseModel):
    """关注专家响应Schema"""
    code: int = Field(200, description="状态码")
    message: str = Field("关注成功", description="响应消息")
    data: dict
    timestamp: datetime.datetime
```

**FollowedExpertItem 要求**：
```python
class FollowedExpertItem(BaseModel):
    """关注的专家响应Schema"""
    expert_id: uuid.UUID
    name: str
    title: Optional[str] = None
    hospital: Optional[str] = None
    avatar_url: Optional[str] = None
    subscribed_at: datetime.datetime
    live_status: Optional[dict] = Field(None, description="直播状态信息")
```

**FollowedExpertsResponse 要求**：
```python
class FollowedExpertsResponse(BaseModel):
    """关注列表响应Schema"""
    code: int = Field(200, description="状态码")
    message: str = Field("success", description="响应消息")
    data: List[FollowedExpertItem]
    timestamp: datetime.datetime
```

---

### 4. SessionExpert Schemas

**Schema 列表**：

1. **SessionExpertRole** - 专家角色枚举
2. **SessionExpertItem** - 场次专家关联信息 Schema

**SessionExpertRole 要求**：
```python
class SessionExpertRole(str, Enum):
    """专家角色枚举（Pydantic版本）"""
    MAIN_SPEAKER = "主讲"
    HOST = "主持"
    GUEST = "嘉宾"
```

**SessionExpertItem 要求**：
```python
class SessionExpertItem(BaseModel):
    """场次专家关联信息Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    name: str
    title: Optional[str] = None
    hospital: Optional[str] = None
    avatar_url: Optional[str] = None
    role: Optional[str] = Field(None, description="专家角色（主讲、主持、嘉宾）")
    sort_order: Optional[int] = Field(None, description="显示顺序")
```

---

## 🚫 禁止事项

- ❌ **禁止定义** 单个 `featured_expert` 字段
- ❌ **禁止定义** 单个专家的关联字段
- ✅ **必须定义** `experts` 数组或 `session_experts` 数组字段
- ✅ **必须支持** `role` 和 `sort_order` 字段

---

## 📊 输出文件规范

**文件路径**: `backend/live_core_service/app/schemas/experts.py`

**文件结构**:
```python
"""
专家模块 Pydantic Schemas 定义
包含专家信息、专家关注、场次专家关联的 Schema
"""

from pydantic import BaseModel, ConfigDict, Field
import uuid
import datetime
from typing import Optional, List
from enum import Enum


# 角色枚举
class SessionExpertRole(str, Enum):
    """专家角色枚举"""
    MAIN_SPEAKER = "主讲"
    HOST = "主持"
    GUEST = "嘉宾"


# ============== 专家信息 Schemas ==============

class ExpertBase(BaseModel):
    """专家基础Schema"""
    name: str = Field(..., min_length=1, max_length=120, description="专家姓名")
    title: Optional[str] = Field(None, max_length=120, description="职称")
    hospital: Optional[str] = Field(None, max_length=200, description="所属医院")
    department: Optional[str] = Field(None, max_length=120, description="科室")
    expertise_areas: Optional[str] = Field(None, description="擅长领域")
    bio: Optional[str] = Field(None, max_length=1000, description="个人简介")
    avatar_url: Optional[str] = Field(None, max_length=512)


class ExpertCreate(ExpertBase):
    """创建专家请求Schema"""
    user_id: Optional[uuid.UUID] = Field(None, description="关联用户ID（可选）")
    is_featured: Optional[bool] = Field(False, description="是否首页推荐")
    sort_order: Optional[int] = Field(0, ge=0, description="排序顺序")
    contact_info: Optional[dict] = Field(None, description="联系方式JSONB")


class ExpertUpdate(BaseModel):
    """更新专家请求Schema（部分更新）"""
    model_config = ConfigDict(from_attributes=True)
    
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    title: Optional[str] = None
    hospital: Optional[str] = None
    department: Optional[str] = None
    expertise_areas: Optional[str] = None
    bio: Optional[str] = Field(None, max_length=1000)
    avatar_url: Optional[str] = None
    is_featured: Optional[bool] = None
    sort_order: Optional[int] = Field(None, ge=0)


class ExpertItem(ExpertBase):
    """专家响应Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    is_featured: bool
    sort_order: int
    created_at: datetime.datetime
    updated_at: datetime.datetime


class FeaturedExpertItem(BaseModel):
    """首页推荐专家简要Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    name: str
    title: Optional[str] = None
    hospital: Optional[str] = None
    avatar_url: Optional[str] = None


# ============== 专家关注 Schemas ==============

class ExpertFollowRequest(BaseModel):
    """关注专家请求Schema"""
    expert_id: uuid.UUID = Field(..., description="专家ID")


class ExpertFollowResponse(BaseModel):
    """关注专家响应Schema"""
    code: int = Field(200, description="状态码")
    message: str = Field("关注成功", description="响应消息")
    data: dict
    timestamp: datetime.datetime


class FollowedExpertItem(BaseModel):
    """关注的专家响应Schema"""
    expert_id: uuid.UUID
    name: str
    title: Optional[str] = None
    hospital: Optional[str] = None
    avatar_url: Optional[str] = None
    subscribed_at: datetime.datetime
    live_status: Optional[dict] = Field(None, description="直播状态信息")


class FollowedExpertsResponse(BaseModel):
    """关注列表响应Schema"""
    code: int = Field(200, description="状态码")
    message: str = Field("success", description="响应消息")
    data: List[FollowedExpertItem]
    timestamp: datetime.datetime


# ============== 场次专家关联 Schemas ==============

class SessionExpertItem(BaseModel):
    """场次专家关联信息Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    name: str
    title: Optional[str] = None
    hospital: Optional[str] = None
    avatar_url: Optional[str] = None
    role: Optional[str] = Field(None, description="专家角色（主讲、主持、嘉宾）")
    sort_order: Optional[int] = Field(None, description="显示顺序")
```

---

## 📝 代码生成指令

**请根据以下要求和设计文档生成 Pydantic Schema 代码**：

**核心要求**：
1. **严格遵循设计文档**：所有字段、验证、嵌套结构必须与设计文档完全一致
2. **不使用 featured_expert_id**：禁止生成任何 `featured_expert_id` 相关的字段
3. **支持多个专家**：必须生成支持专家列表的响应结构（数组形式）
4. **遵循项目规范**：使用正确的基类、类型定义、验证方式
5. **完整验证**：所有字段都有 `Field()` 验证和描述

**设计文档路径**：`@docs/03_系统设计/直播核心功能设计文档_v6_专家模块设计文档-专家信息-专家关注.md`

**必须生成的文件**：
- `backend/live_core_service/app/schemas/experts.py`

**禁止事项**：
- ❌ 禁止生成 `featured_expert_id` 字段
- ❌ 禁止定义单个专家的关联字段
- ✅ 必须生成支持多个专家的数组结构
- ✅ 必须支持 `role` 和 `sort_order` 字段

---

## ✅ 验收标准

- [ ] 所有 Schema 类都使用 `model_config = ConfigDict(from_attributes=True)`
- [ ] 所有字段都有 `Field()` 验证和描述
- [ ] 所有 UUID 字段都使用 `uuid.UUID` 类型
- [ ] 所有可选字段都使用了 `Optional[类型]` 和 `None` 默认值
- [ ] 响应模型符合统一响应结构
- [ ] 分页模型符合分页响应结构
- [ ] 使用了 `SessionExpertRole` 枚举定义角色
- [ ] 支持多个专家的数组结构

---

**文档结束**

