

### 2\. 【完整修改版】SQLAlchemy 模型与 Pydantic Schema 一致性检查提示词

这是我为您修改后的“一致性检查提示词”。它现在**强制检查** `ENUM` 类型的一致性，以匹配您的学院派规范。

# 直播间 Tab & 留言功能 SQLAlchemy 模型与 Pydantic Schema 一致性检查提示词 (学院派 ENUM 版)

-----

## **AI 提示词：用于审查 Tab & 留言功能 Model 与 Schema 逻辑一致性**

### **1. 角色定义 (Role Definition)**

你是一名资深的 FastAPI 后端架构师，专注于 API 设计和数据模型的最佳实践。你的任务是审查 Tab 和 留言 功能的 SQLAlchemy 模型（`live_features.py`）和 Pydantic Schema（`schemas/live_features.py`）之间的一致性、安全性和功能适配性。

**核心职责**:

  * 验证数据模型的完整性和一致性
  * 识别潜在的安全风险和数据泄露问题
  * 确保 API 设计（`Create` / `Response` Schemas）严格符合 V3.3 设计文档
  * 检查数据验证规则的完备性

-----

### **2. 任务目标 (Task Objective)**

你的目标**不是**检查两个文件是否逐字相同，而是要：

1.  ✅ **验证 Pydantic Schemas 是否是 SQLAlchemy Models 合理且安全的"API 视图"**

      * Schema 是否正确映射了 Model 的字段？
      * API Schemas (Create/Response) 是否严格遵循了 V3.3 设计文档的定义？

2.  ✅ **确保数据在"外部世界"（API）和"内部世界"（数据库）之间能够安全、高效地转换**

      * 类型转换是否正确？（`UUID`, `datetime`, `Boolean`, **`ENUM`**）

3.  ✅ **找出任何可能导致数据泄露、验证错误或 API 使用不便的设计缺陷**

      * `Response` Schema 是否暴露了不该暴露的字段？
      * `Create` Schema 是否错误地包含了应从上下文（路径、JWT）获取的字段？
      * 验证规则（如 `max_length`）是否缺失？

-----

### **3. 核心输入 (Core Input)**

#### **3.1. SQLAlchemy 模型代码**

**文件路径**: `live_core_service/app/models/live_features.py`
*(注：此处应粘贴 `live_features.py` 的**模型代码**，该代码应包含 `SAEnum(LiveRoomMessageUserRole, ...)`)*

-----

#### **3.2. Pydantic Schema 代码 (学院派 ENUM 版)**

**文件路径**: `live_core_service/app/schemas/live_features.py`
*(注：此处应粘贴 `schemas/live_features.py` 的 **Schema 代码**)*

```python
"""
直播间 Tab 和留言功能的 Pydantic Schema (学院派 ENUM 版)
"""

# 标准库导入
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
import uuid

# 第三方库导入
from pydantic import BaseModel, Field, ConfigDict, field_validator

# ==================== [学院派迁移] 导入 Python ENUM ====================
class LiveRoomMessageUserRole(str, Enum):
    REGULAR = 'REGULAR'
    MODERATOR = 'MODERATOR'
    ADMIN = 'ADMIN'
    SUPERADMIN = 'SUPERADMIN'

class LiveRoomTabContentType(str, Enum):
    TEXT = 'text'
    IMAGE = 'image'
    MIXED = 'mixed'

# ==================== LiveRoomTab Schema 部分 ====================

class LiveRoomTabBase(BaseModel):
    """Tab 基础 Schema"""
    tab_key: str = Field(..., max_length=64, description="系统级 key")
    title: str = Field(..., max_length=128, description="展示名称")
    content_type: LiveRoomTabContentType = Field(..., description="内容类型")
    text_content: Optional[str] = Field(None, description="文本内容")
    image_url: Optional[str] = Field(None, description="图片 URL")
    sort_order: int = Field(default=0, ge=0, description="排序顺序")
    is_active: bool = Field(default=True, description="是否激活")

class LiveRoomTabCreate(LiveRoomTabBase):
    """
    创建 Tab 请求 Schema
    用于 POST /api/v1/admin/rooms/{room_id}/tabs
    room_id 从路径获取
    """
    pass

class LiveRoomTabUpdate(BaseModel):
    """
    更新 Tab 请求 Schema
    用于 PATCH /api/v1/admin/tabs/{tab_id}
    所有字段可选
    """
    tab_key: Optional[str] = Field(None, max_length=64)
    title: Optional[str] = Field(None, max_length=128)
    content_type: Optional[LiveRoomTabContentType] = Field(None, description="内容类型")
    text_content: Optional[str] = None
    image_url: Optional[str] = None
    sort_order: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None

class LiveRoomTabInDB(LiveRoomTabBase):
    """数据库中的 Tab Schema"""
    id: uuid.UUID
    room_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class LiveRoomTabResponse(LiveRoomTabInDB):
    """
    Tab 响应 Schema
    用于 GET /api/v1/admin/rooms/{room_id}/tabs
    """
    pass


# ==================== LiveRoomMessage Schema 部分 ====================

class LiveRoomMessageBase(BaseModel):
    """留言基础 Schema"""
    content: str = Field(
        ..., 
        min_length=1, 
        max_length=500, 
        description="留言内容, 长度 1-500 字符"
    )

class LiveRoomMessageCreate(LiveRoomMessageBase):
    """
    创建留言请求 Schema
    用于 POST /api/v1/rooms/{room_id}/messages
    (room_id, user_id, user_role 均从请求上下文获取)
    """
    pass

class LiveRoomMessageUpdate(BaseModel):
    """更新留言 Schema (后台管理用)"""
    content: Optional[str] = Field(None, min_length=1, max_length=500)
    is_deleted: Optional[bool] = None

class LiveRoomMessageInDB(LiveRoomMessageBase):
    """数据库中的留言 Schema"""
    id: uuid.UUID
    room_id: uuid.UUID
    session_id: Optional[uuid.UUID]
    user_id: uuid.UUID
    user_role: LiveRoomMessageUserRole
    created_at: datetime
    is_deleted: bool
    extra: Optional[Dict[str, Any]]
    
    model_config = ConfigDict(from_attributes=True)

class LiveRoomMessagePostResponse(BaseModel):
    """
    创建留言响应 Schema
    严格遵循 V3.3 API 3.3.1 响应体
    """
    id: uuid.UUID
    room_id: uuid.UUID
    user_id: uuid.UUID
    user_role: LiveRoomMessageUserRole
    content: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class LiveRoomMessageListResponseItem(BaseModel):
    """
    获取留言列表项 Schema
    严格遵循 V3.3 API 3.3.2 items 字段
    """
    id: uuid.UUID
    user_role: LiveRoomMessageUserRole
    content: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class PaginatedLiveRoomMessageResponse(BaseModel):
    """
    获取留言列表分页响应 Schema
    严格遵循 V3.3 API 3.3.2 响应体
    """
    total: int
    page: int
    size: int
    items: List[LiveRoomMessageListResponseItem]
```

-----

## ✅ **4. 审查清单（基础逻辑）**

请根据以下维度对比 Model 与 Schema 设计是否一致、合理：

### **4.1 字段命名一致性**

**检查项**:

  * [ ] `LiveRoomTab` 模型的字段名称是否与 `LiveRoomTab*` Schema 中的字段名称完全一致？
  * [ ] `LiveRoomMessage` 模型的字段名称是否与 `LiveRoomMessage*` Schema 中的字段名称完全一致？
  * [ ] 是否存在拼写差异或语义偏移？

**重点字段检查**:
| Model 字段 | Schema 字段 | 是否一致 |
|---|---|---|
| `LiveRoomTab.tab_key` | `LiveRoomTabBase.tab_key` | ? |
| `LiveRoomTab.title` | `LiveRoomTabBase.title` | ? |
| `LiveRoomTab.content_type` | `LiveRoomTabBase.content_type` | ? |
| `LiveRoomTab.text_content` | `LiveRoomTabBase.text_content` | ? |
| `LiveRoomTab.image_url` | `LiveRoomTabBase.image_url` | ? |
| `LiveRoomTab.sort_order` | `LiveRoomTabBase.sort_order` | ? |
| `LiveRoomTab.is_active` | `LiveRoomTabBase.is_active` | ? |
| `LiveRoomMessage.content` | `LiveRoomMessageBase.content` | ? |
| `LiveRoomMessage.is_deleted`| `LiveRoomMessageUpdate.is_deleted`| ? |
| `LiveRoomMessage.extra` | `LiveRoomMessageInDB.extra` | ? |
| `LiveRoomMessage.user_role` | `LiveRoomMessageInDB.user_role` | ? |

-----

### **4.2 数据类型兼容性**

**检查项**:

  * [ ] `UUID` 类型字段是否在 Schema 中映射为 `uuid.UUID`？
  * [ ] `String(n)` 类型字段是否在 Schema 中映射为 `str`，并使用 `Field(max_length=n)` 限制？
  * [ ] `Text` 类型字段是否在 Schema 中映射为 `str`？
  * [ ] `Integer` 类型字段是否在 Schema 中映射为 `int`？
  * [ ] `TIMESTAMP(timezone=True)` 类型字段是否在 Schema 中映射为 `datetime`？
  * [ ] `Boolean` 类型字段是否在 Schema 中映射为 `bool`？
  * [ ] `JSONB` 类型字段是否在 Schema 中映射为 `Optional[Dict[str, Any]]`？
  * [ ] **[学院派]** `SAEnum` 类型字段是否在 Schema 中映射为对应的 Python `enum.Enum` 类？

**类型映射表**:
| SQLAlchemy 类型 | Pydantic 类型 | 验证规则 | 是否正确映射 |
|---|---|---|---|
| `UUID(as_uuid=True)` | `uuid.UUID` | - | ? |
| `SAEnum(LiveRoomTabContentType)` | `LiveRoomTabContentType` | (Python Enum) | ? |
| `SAEnum(LiveRoomMessageUserRole)` | `LiveRoomMessageUserRole` | (Python Enum) | ? |
| `String(64)` | `str` | `Field(max_length=64)` | ? |
| `String(128)` | `str` | `Field(max_length=128)`| ? |
| `Text` | `str` | (e.g., `max_length=500` for content) | ? |
| `Integer` | `int` | `Field(ge=0)` | ? |
| `Boolean` | `bool` | - | ? |
| `JSONB` | `Optional[Dict[str, Any]]`| - | ? |
| `TIMESTAMP(timezone=True)` | `datetime` | - | ? |

-----

### **4.3 Create Schema 审查 (V3.3 API 规范)**

**检查项**:

  * [ ] `LiveRoomTabCreate` 是否继承自 `LiveRoomTabBase`？
  * [ ] `LiveRoomTabCreate` 是否**正确排除**了系统生成字段（`id`, `created_at`, `updated_at`）？
  * [ ] `LiveRoomTabCreate` 是否**正确排除**了外键字段（`room_id`，从路径参数获取）？
  * [ ] `LiveRoomMessageCreate` 是否继承自 `LiveRoomMessageBase`？
  * [ ] `LiveRoomMessageCreate` 是否**只包含** `content` 字段（如 V3.3 API 3.3.1 请求体定义）？
  * [ ] `LiveRoomMessageCreate` 是否**正确排除**了 `id`, `room_id`, `session_id`, `user_id`, `user_role`, `created_at`, `is_deleted`, `extra`（均从上下文或后端逻辑生成）？

-----

### **4.4 Update Schema 审查**

**检查项**:

  * [ ] `LiveRoomTabUpdate` 中的所有字段是否都定义为 `Optional[...]`？
  * [ ] `LiveRoomTabUpdate` 是否**正确排除**了不可更新字段（`id`, `room_id`, `created_at`, `updated_at`）？
  * [ ] `LiveRoomMessageUpdate`（后台用）中的字段是否都定义为 `Optional`？

-----

### **4.5 Response Schema 审查 (V3.3 API 规范)**

#### **4.5.1 安全与规范审计**

**检查项**:

  * [ ] **(V3.3 API 3.3.1)** `LiveRoomMessagePostResponse` 是否**精确包含** `id`, `room_id`, `user_id`, `user_role`, `content`, `created_at`？
  * [ ] **(V3.3 API 3.3.2)** `LiveRoomMessageListResponseItem` 是否**精确包含** `id`, `user_role`, `content`, `created_at`？ (注意：此视图**不**暴露 `user_id` 和 `room_id`)
  * [ ] **(V3.3 API 3.2.1)** `LiveRoomTabResponse` 是否包含所有必要字段（`id`, `room_id`, `created_at`, `updated_at` 及 Base 字段）？

#### **4.5.2 结构审计**

  * [ ] `PaginatedLiveRoomMessageResponse` 是否正确嵌套了 `items: List[LiveRoomMessageListResponseItem]`？
  * [ ] `PaginatedLiveRoomMessageResponse` 是否包含 `total`, `page`, `size`？

**`from_attributes` 配置检查**:

  * [ ] 所有 `Response` Schema（`LiveRoomTabResponse`, `LiveRoomMessagePostResponse`, `LiveRoomMessageListResponseItem`）是否设置了 `model_config = ConfigDict(from_attributes=True)`？
  * [ ] 所有 `*InDB` Schema 是否设置了 `model_config = ConfigDict(from_attributes=True)`？

-----

## 🔒 **5. 安全与设计一致性增强项**

### **5.1 默认值一致性**

**检查项**:

  * [ ] `LiveRoomTab.sort_order` 在 Model 中的默认值（`0`）是否与 Schema (`LiveRoomTabBase.sort_order`) 中一致（`default=0`）？
  * [ ] `LiveRoomTab.is_active` 在 Model 中的默认值（`True`）是否与 Schema (`LiveRoomTabBase.is_active`) 中一致（`default=True`）？
  * [ ] `LiveRoomMessage.is_deleted` 在 Model 中的默认值（`False`）是否在 Schema (`LiveRoomMessageUpdate`) 中体现（虽然 `Update` 是 `Optional`，但在 `InDB` 中应有体现）？

-----

### **5.2 [学院派] 枚举类型一致性**

  * [ ] **(V3.3 学院派检查)** `models/live_features.py` 中定义的 Python ENUM（`LiveRoomMessageUserRole`, `LiveRoomTabContentType`）是否与 `schemas/live_features.py` 中定义的 **Python ENUM** 完全一致（包括名称和值）？
  * [ ] Pydantic Schema 是否正确导入并使用了这些 ENUM 类，而不是 `str`？

-----

### **5.3 字段约束映射**

**检查项**:

  * [ ] Model 中 `nullable=False` 的字段是否在 `Base` Schema 中标记为必填（`...` 或有默认值）？
  * [ ] Model 中 `nullable=True` 的字段是否在 `Base` Schema 中标记为 `Optional`？
  * [ ] Model 中的字符串长度限制（`String(n)`）是否在 Schema 中通过 `Field(max_length=n)` 体现？
  * [ ] `LiveRoomMessage.content` 的 `TEXT` 类型，是否根据 API 规范在 `LiveRoomMessageBase` 中正确约束为 `Field(..., min_length=1, max_length=500)`？

**约束映射表**:
| Model 字段 | Model 约束 | Schema 验证规则 | 是否正确映射 |
|---|---|---|---|
| `LiveRoomTab.tab_key` | `String(64)` | `Field(..., max_length=64)` | ? |
| `LiveRoomTab.title` | `String(128)` | `Field(..., max_length=128)` | ? |
| `LiveRoomTab.content_type`| `SAEnum(LiveRoomTabContentType)` | `LiveRoomTabContentType` (Enum) | ? |
| `LiveRoomTab.text_content`| `nullable=True`| `Optional[str]` | ? |
| `LiveRoomTab.image_url` | `nullable=True`| `Optional[str]` | ? |
| `LiveRoomTab.sort_order`| `default=0` | `Field(default=0, ge=0)` | ? |
| `LiveRoomTab.is_active` | `default=True` | `Field(default=True)` | ? |
| `LiveRoomMessage.content` | `Text` | `Field(..., min_length=1, max_length=500)` | ? |
| `LiveRoomMessage.user_role`| `SAEnum(LiveRoomMessageUserRole)` | `LiveRoomMessageUserRole` (Enum) (InDB) | ? |

-----

## 🧩 **6. 嵌套结构与复合 Schema 审查**

### **6.1 嵌套 Schema 合理性**

**检查项**:

  * [ ] `PaginatedLiveRoomMessageResponse` 嵌套 `List[LiveRoomMessageListResponseItem]` 是否合理？
  * [ ] 是否存在不必要的嵌套（例如 `LiveRoomTabResponse` 嵌套 `LiveRoom`，V3.3 未要求）？

-----

### **6.2 复合对象字段控制**

**检查项**:

  * [ ] `LiveRoomMessageCreate` 是否严格控制只接收 `content`？
  * [ ] `LiveRoomTabCreate` 是否严格控制只接收 `LiveRoomTabBase` 中的字段？

-----

## 🧰 **7. Schema 继承与通用结构审查（高级）**

### **7.1 继承结构审查**

**检查项**:

  * [ ] `LiveRoomTabCreate` 是否继承自 `LiveRoomTabBase`？
  * [ ] `LiveRoomTabInDB` 是否继承自 `LiveRoomTabBase`？
  * [ ] `LiveRoomTabResponse` 是否继承自 `LiveRoomTabInDB`？
  * [ ] `LiveRoomMessageCreate` 是否继承自 `LiveRoomMessageBase`？
  * [ ] `LiveRoomMessageInDB` 是否继承自 `LiveRoomMessageBase`？
  * [ ] `LiveRoomMessagePostResponse` 和 `LiveRoomMessageListResponseItem` 是否（正确地）**未**继承 `Base`，而是根据 API 规范独立定义？

-----

### **7.2 ORM 映射配置审查**

**检查项**:

  * [ ] 所有 `*InDB` Schema 是否设置了 `model_config = ConfigDict(from_attributes=True)`？
  * [ ] 所有 `*Response` Schema（`LiveRoomTabResponse`, `LiveRoomMessagePostResponse`, `LiveRoomMessageListResponseItem`）是否设置了 `model_config = ConfigDict(from_attributes=True)`？

-----

### **7.3 字段注释与文档字符串审查**

**检查项**:

  * [ ] 所有 Schema 类是否包含中文文档字符串，并**注明其 API 用途**（例如 `用于 POST ...`）？
  * [ ] 关键字段是否包含 `description` 参数？
  * [ ] `LiveRoomMessageBase.content` 是否包含 `min_length` 和 `max_length` 的描述？

-----

## 🔍 **8. 特殊功能审查**

### **8.1 自定义验证器审查**

  * [ ] **(V3.3 检查)** API 规范要求对 `content` 中的 URL 进行过滤，但这发生在 Service 层（基于 `user_role`）。
  * [ ] Pydantic Schema (`live_features.py`) 中**不应该**包含 URL 过滤的 `@field_validator`。

-----

## 📊 **9. 最终交付 (Final Deliverable)**

生成一份简明的审查报告，指出你发现的任何**逻辑不一致**（特别是与 V3.3 API 规范）、**安全风险**或**不符合最佳实践**的地方，并提供具体的修改建议。

### **9.1 报告结构**

```markdown
# Tab & 留言功能 Model 与 Schema 一致性审查报告

## 1. 总体评估
- 一致性评分: ?/100
- 发现问题数量: ?

## 2. 字段命名一致性
- [✅/❌] 检查结果: ...
- 问题清单: ...

## 3. 数据类型兼容性
- [✅/❌] 检查结果: ...
- 问题清单: (例如：JSONB 未映射为 Dict)

## 4. Create Schema 审查 (V3.3 规范)
- [✅/❌] 检查结果: ...
- 问题清单: (例如：`LiveRoomMessageCreate` 错误地包含了 `user_id`)

## 5. Update Schema 审查
- [✅/❌] 检查结果: ...
- 问题清单: (例如：`LiveRoomTabUpdate` 字段不是 Optional)

## 6. Response Schema 审查 (V3.3 规范)
- [✅/❌] 检查结果: ...
- 问题清单: (例如：`LiveRoomMessageListResponseItem` 错误地暴露了 `user_id`)

## 7. [学院派] ENUM 类型一致性
- [✅/❌] 检查结果: ...
- 问题清单: (例如: Schema 和 Model 中的 ENUM 值不匹配)

## 8. 默认值与约束映射
- [✅/❌] 检查结果: ...
- 问题清单: (例如：`content` 字段缺少 `max_length=500` 验证)

## 9. 嵌套结构与 ORM 配置
- [✅/❌] 检查结果: ...
- 问题清单: (例如：`LiveRoomMessagePostResponse` 缺少 `from_attributes=True`)

## 10. 总体建议
- 优先修复项: ...
```

-----

## 🎯 **10. 审查重点总结**

### **10.1 必须检查的项目（P0 优先级）**

1.  ✅ **[学院派] ENUM 检查**：`user_role` 和 `content_type` 必须在 Model (`SAEnum`) 和 Schema (`enum.Enum`) 中正确映射，**而不是 `str`**。
2.  ✅ **V3.3 API 规范**：`Create` 和 `Response` Schemas 是否**严格**按照 V3.3 文档 定义？
      * `LiveRoomMessageCreate` 只有 `content`。
      * `LiveRoomMessagePostResponse` 包含 `user_id`。
      * `LiveRoomMessageListResponseItem` **不**包含 `user_id`。
      * `PaginatedLiveRoomMessageResponse` 结构正确。
3.  ✅ **字段约束**：`content` 字段必须有 `min_length=1, max_length=500`。
4.  ✅ **上下文排除**：`Create` Schemas 绝不能包含 `id`, `room_id`, `user_id` 等上下文提供
    的字段。
5.  ✅ **`from_attributes=True`**：所有 `InDB` 和 `Response` Schemas 必须配置。
6.  ✅ **数据类型**：`Boolean` 和 `JSONB` 必须正确映射。

### **10.2 重要检查的项目（P1 优先级）**

1.  ✅ `Update` Schemas 必须所有字段 `Optional`。
2.  ✅ `Base` 和 `InDB` 之间的字段必须一致（`InDB` = `Base` + 系统字段）。
3.  ✅ `max_length` 约束必须与 Model `String(n)` 一致。
4.  ✅ 默认值（`sort_order`, `is_active`）必须一致。