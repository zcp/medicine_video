# 直播间Tab管理模块设计文档（Live Room Tabs）

**版本**: V1.1  
**日期**: 2026-06-08  
**状态**: ✅ 已同步后端实际代码，可直接开发  
**基于**: 《直播核心功能设计文档_v6_内容管理模块设计文档-标签-分类-场次标签关联-合并版.md》

---

## 📌 核心定位说明

### 1. 本文档的定位

本文档专注于**直播间Tab管理（Live Room Tabs）**的完整后端实现设计，包括：

**包含模块**:
- **Live_Room_Tabs（直播间Tab）**: 直播间自定义Tab页签管理
- **Tab内容管理**: 结构化内容（text纯文本 / image纯图片 / mixed图文混排）、图片上传

**模块范围**:
- 1张数据表（`live_room_tabs`）
- 7个API接口（Tab CRUD 4个、图片上传1个、排序1个、公开查询1个）
- 完整的Pydantic Schemas定义
- 完整的数据库DDL及索引设计

### 2. 本文档的核心特点

- ✅ **内容完整性**: 包含直播间Tab管理的所有后端设计内容
- ✅ **独立可开发**: 可作为独立的后端开发文档
- ✅ **结构化内容**: Tab支持三种内容类型（text纯文本 / image纯图片 / mixed图文混排）
- ✅ **系统级标识**: 通过 `tab_key` 字段支持前端逻辑识别（如 intro、agenda、speakers）
- ✅ **支持排序**: 支持手动拖拽排序

### 3. 业务价值说明

**直播间Tab管理（Live Room Tabs）**:
- 为直播间提供自定义内容展示区域
- 支持结构化内容类型（纯文本、纯图片、图文混排），前端可按类型分支渲染
- 通过 `tab_key` 系统级标识符支持前端逻辑判断（不依赖 title 变动）
- 支持排序和启用/禁用控制
- 提升直播间的信息展示能力

---

## 📚 依赖文档清单

| 序号 | 文档名称 | 依赖关系 | 影响范围 |
|------|---------|---------|---------|
| 1 | 《直播核心功能设计文档_v6_深度融合最终版.md》 | 📋 **主设计文档** | `live_rooms` 表定义、JWT字段、API规范 |
| 2 | 《直播核心功能设计文档_v6_内容管理模块设计文档》 | 📋 **模块设计文档** | Tab模块DDL、API、执行流程 |

**⚠️ 重要说明**:
- `live_room_tabs` 表依赖 `live_rooms` 表的 `id` 字段
- 删除直播间时，关联的Tab应级联删除
- 所有时间字段使用 `TIMESTAMPTZ`（带时区）

---

## 📖 文档规范说明

### 统一响应结构

```json
{
  "code": 200,
  "message": "success",
  "data": { ... },
  "timestamp": "2026-06-07T10:00:00Z"
}
```

### 统一分页格式

分页接口使用统一的分页响应结构：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 100,
    "page": 1,
    "size": 20,
    "items": [ ... ]
  },
  "timestamp": "2026-06-07T10:00:00Z"
}
```

### JWT Token格式说明

```json
{
  "user_id": "uuid-string",
  "username": "admin",
  "role": "admin",
  "exp": 1717756800
}
```

> **重要说明**: JWT Payload中用户标识字段为 `user_id`（非 `sub`），所有需要获取当前用户的接口均通过 `user_id` 字段提取用户身份。

### 统一认证规范

- **公开访问（Public）**: 获取直播间Tab列表（用户端）
- **管理员权限（ADMIN）**: Tab的CRUD操作

### 业务状态码

| 状态码 | 说明 | 使用场景 |
|--------|------|----------|
| `200` | 成功 | 所有成功响应 |
| `1002` | 数据库错误 | 数据库操作异常 |
| `2001` | 资源不存在 | Tab ID不存在、直播间不存在 |
| `3001` | 未授权 | JWT Token缺失或无效 |
| `3002` | 权限不足 | 非管理员访问管理端接口 |
| `4001` | 参数校验失败 | 请求参数不符合规范 |

---

## 🎯 设计要点与约定

### 1.1 数据库设计规范

1. **UUID主键**: 所有表使用 `UUID` 类型作为主键
2. **时间戳**: 所有时间字段使用 `TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP`
3. **外键约束**: `room_id` 外键关联 `live_rooms(id)`，级联删除
4. **软删除**: `live_room_tabs` 表使用 `is_active` 字段实现软删除
5. **排序**: `sort_order` 字段控制Tab显示顺序

### 1.2 API设计规范

1. **HTTP方法**: GET（查询）、POST（创建）、PATCH（部分更新）、DELETE（删除）
2. **URL路径**: 使用 `/api/v1/admin/rooms/{roomId}/tabs` 格式
3. **认证策略**: 公开读取（用户端）+ 管理员写入

### 1.3 软删除策略

| 表名 | 策略 | 说明 |
|------|------|------|
| `live_room_tabs` | `is_active` 字段 | 删除时设置 `is_active = false`，用户端查询默认过滤 |

### 1.4 安全与配置规范

**架构分层原则**:
- **API 层**: 仅负责认证（`Depends(get_current_user)` 或 `Depends(get_current_user_optional)`）
- **Service 层**: 负责授权（权限守卫函数）
- **CRUD 层**: 负责SQL级别的权限过滤

**双轨鉴权模式**:
- **严格鉴权（Strict Auth）**: 所有CUD操作，需要有效的JWT Token
- **可选鉴权（Optional Auth）**: 公开读取操作，允许匿名访问

**权限守卫函数**:

```python
def _check_admin_permission(user_role: str) -> None:
    """检查管理员权限，非管理员抛出403异常"""
    if user_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": 3002, "message": "权限不足：需要管理员权限"}
        )
```

**CRUD层权限过滤**:

```python
# 用户端查询：默认只返回 is_active = true 的Tab
async def get_room_tabs(db: AsyncSession, room_id: UUID, include_inactive: bool = False):
    query = select(LiveRoomTab).where(LiveRoomTab.room_id == room_id)
    if not include_inactive:
        query = query.where(LiveRoomTab.is_active == True)
    query = query.order_by(LiveRoomTab.sort_order.asc())
    return await db.execute(query)
```

---

## 1. 数据库Schema设计（DDL）

### 1.0 前置准备：触发器函数

```sql
-- 自动更新 updated_at 触发器函数（如已创建则跳过）
CREATE OR REPLACE FUNCTION trigger_set_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

### 1.1 live_room_tabs（直播间Tab表）

```sql
-- ==========================================================
-- 枚举类型：live_room_tab_content_type
-- 说明：Tab内容类型，决定前端渲染方式
-- ==========================================================
CREATE TYPE live_room_tab_content_type AS ENUM ('text', 'image', 'mixed');

-- ==========================================================
-- 表：live_room_tabs（直播间Tab表）
-- 说明：存储直播间自定义Tab页签信息，支持结构化内容（文本/图片/混排）、排序
-- ==========================================================

CREATE TABLE live_room_tabs (
    id UUID PRIMARY KEY,
    room_id UUID NOT NULL,
    tab_key VARCHAR(64) NOT NULL,
    title VARCHAR(128) NOT NULL,
    content_type live_room_tab_content_type NOT NULL,
    text_content TEXT,
    image_url TEXT,
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_tab_room FOREIGN KEY (room_id)
        REFERENCES live_rooms(id) ON DELETE CASCADE
);

-- 复合索引：room_id + sort_order（用于排序查询）
CREATE INDEX idx_live_room_tabs_room_sort ON live_room_tabs(room_id, sort_order);

-- 触发器：自动更新 updated_at
CREATE TRIGGER set_timestamp_live_room_tabs
    BEFORE UPDATE ON live_room_tabs
    FOR EACH ROW
    EXECUTE FUNCTION trigger_set_timestamp();

-- 表注释
COMMENT ON TABLE live_room_tabs IS '直播间Tab表 - 自定义Tab页签管理';
COMMENT ON COLUMN live_room_tabs.id IS 'Tab UUID主键';
COMMENT ON COLUMN live_room_tabs.room_id IS '直播间UUID（外键，级联删除）';
COMMENT ON COLUMN live_room_tabs.tab_key IS '系统级 key，用于逻辑识别（如 intro、agenda、speakers）';
COMMENT ON COLUMN live_room_tabs.title IS 'Tab展示名称';
COMMENT ON COLUMN live_room_tabs.content_type IS '内容类型：text（纯文本）、image（纯图片）、mixed（图文混排）';
COMMENT ON COLUMN live_room_tabs.text_content IS '文本内容（当 content_type 为 text 或 mixed 时使用）';
COMMENT ON COLUMN live_room_tabs.image_url IS '图片URL（当 content_type 为 image 或 mixed 时使用）';
COMMENT ON COLUMN live_room_tabs.sort_order IS '排序权重（升序，数值越小越靠前）';
COMMENT ON COLUMN live_room_tabs.is_active IS '是否启用（软删除标记）';
COMMENT ON COLUMN live_room_tabs.created_at IS '创建时间（UTC）';
COMMENT ON COLUMN live_room_tabs.updated_at IS '最后更新时间（UTC）';
```

---

## 2. Pydantic Schemas定义

```python
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from enum import Enum


class LiveRoomTabContentType(str, Enum):
    """Tab内容类型枚举"""
    TEXT = 'text'
    IMAGE = 'image'
    MIXED = 'mixed'


class LiveRoomTabBase(BaseModel):
    """直播间Tab基础Schema"""
    tab_key: str = Field(..., max_length=64, description="系统级 key，用于前端逻辑判断")
    title: str = Field(..., max_length=128, description="Tab展示名称")
    content_type: LiveRoomTabContentType = Field(..., description="内容类型：text、image、mixed")
    text_content: Optional[str] = Field(None, description="文本内容（当 content_type 为 text 或 mixed 时）")
    image_url: Optional[str] = Field(None, description="图片URL（当 content_type 为 image 或 mixed 时）")
    sort_order: int = Field(0, ge=0, description="排序权重")
    is_active: bool = Field(True, description="是否启用")


class LiveRoomTabCreate(LiveRoomTabBase):
    """创建Tab请求Schema"""
    pass


class LiveRoomTabUpdate(BaseModel):
    """更新Tab请求Schema（部分更新）"""
    tab_key: Optional[str] = Field(None, max_length=64, description="系统级 key")
    title: Optional[str] = Field(None, max_length=128, description="Tab展示名称")
    content_type: Optional[LiveRoomTabContentType] = Field(None, description="内容类型")
    text_content: Optional[str] = Field(None, description="文本内容")
    image_url: Optional[str] = Field(None, description="图片URL")
    sort_order: Optional[int] = Field(None, ge=0, description="排序权重")
    is_active: Optional[bool] = Field(None, description="是否启用")

    model_config = ConfigDict(from_attributes=True)


class LiveRoomTabItem(LiveRoomTabBase):
    """Tab响应Schema"""
    id: UUID
    room_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LiveRoomTabSortRequest(BaseModel):
    """Tab排序请求Schema"""
    tab_ids: List[UUID] = Field(..., description="Tab UUID列表（按新顺序排列）")

    @field_validator("tab_ids")
    @classmethod
    def validate_tab_ids(cls, v: List[UUID]) -> List[UUID]:
        """校验tab_ids不为空"""
        if len(v) == 0:
            raise ValueError("tab_ids 不能为空")
        return v
```

---

## 3. API接口设计（完整CRUD）

### 3.1 管理端API

#### 3.1.1 获取直播间Tab列表（ADMIN）

**Endpoint**: `GET /api/v1/admin/rooms/{roomId}/tabs`

**描述**: 获取指定直播间的所有Tab（包含已禁用的）

**认证**: JWT认证 + 管理员权限

**路径参数**:
- `roomId` (UUID, required): 直播间UUID

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": "uuid-string",
        "room_id": "room-uuid",
        "tab_key": "intro",
        "title": "科室介绍",
        "content_type": "text",
        "text_content": "肝胆胰外科简介...",
        "image_url": null,
        "sort_order": 0,
        "is_active": true,
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z"
      }
    ]
  },
  "timestamp": "2026-06-07T10:00:00Z"
}
```

**执行流程**:

1. **接收请求**: API路由接收GET请求，解析路径参数
2. **JWT验证**: 通过 `Depends(get_current_user)` 提取当前用户
3. **权限检查**: 调用 `_check_admin_permission(user.role)` 校验管理员权限
4. **构建查询**: `SELECT * FROM live_room_tabs WHERE room_id = :roomId ORDER BY sort_order ASC`
5. **执行查询**: 异步执行数据库查询
6. **返回响应**: 返回Tab列表

---

#### 3.1.2 创建Tab（ADMIN）

**Endpoint**: `POST /api/v1/admin/rooms/{roomId}/tabs`

**描述**: 为直播间创建新的Tab

**认证**: JWT认证 + 管理员权限

**路径参数**:
- `roomId` (UUID, required): 直播间UUID

**请求体**:
```json
{
  "tab_key": "speakers",
  "title": "专家团队",
  "content_type": "text",
  "text_content": "专家团队介绍...",
  "image_url": null,
  "sort_order": 2,
  "is_active": true
}
```

**成功响应** (`201 Created`):
```json
{
  "code": 200,
  "message": "Tab创建成功",
  "data": {
    "id": "new-uuid-string",
    "room_id": "room-uuid",
    "tab_key": "speakers",
    "title": "专家团队",
    "content_type": "text",
    "text_content": "专家团队介绍...",
    "image_url": null,
    "sort_order": 2,
    "is_active": true,
    "created_at": "2026-06-07T10:00:00Z",
    "updated_at": "2026-06-07T10:00:00Z"
  },
  "timestamp": "2026-06-07T10:00:00Z"
}
```

**执行流程**:

1. **接收请求**: API路由接收POST请求，解析路径参数和请求体
2. **JWT验证**: 通过 `Depends(get_current_user)` 提取当前用户
3. **权限检查**: 调用 `_check_admin_permission(user.role)` 校验管理员权限
4. **Pydantic校验**: 使用 `LiveRoomTabCreate` Schema校验请求体
5. **直播间存在性检查**: 查询 `live_rooms` 表确认直播间存在
6. **生成UUID**: 生成新的UUID作为主键
7. **插入数据库**: `INSERT INTO live_room_tabs (...) VALUES (...)`
8. **提交事务**: `await db.commit()`
9. **返回响应**: 返回创建的Tab信息

**HTTP状态码**:
- `201 Created`: 创建成功
- `401 Unauthorized`: JWT Token无效（code=3001）
- `403 Forbidden`: 非管理员（code=3002）
- `404 Not Found`: 直播间不存在（code=2001）
- `422 Unprocessable Entity`: 参数校验失败（code=4001）

---

#### 3.1.3 更新Tab（ADMIN，部分更新）

**Endpoint**: `PATCH /api/v1/admin/tabs/{tabId}`

**描述**: 部分更新Tab信息

**认证**: JWT认证 + 管理员权限

**路径参数**:
- `tabId` (UUID, required): Tab UUID

**请求体**:
```json
{
  "title": "专家团队（更新）",
  "sort_order": 1
}
```

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "Tab更新成功",
  "data": { ... },
  "timestamp": "2026-06-07T10:00:00Z"
}
```

**执行流程**:

1. **接收请求**: API路由接收PATCH请求，解析路径参数和请求体
2. **JWT验证**: 通过 `Depends(get_current_user)` 提取当前用户
3. **权限检查**: 调用 `_check_admin_permission(user.role)` 校验管理员权限
4. **Pydantic校验**: 使用 `LiveRoomTabUpdate` Schema校验请求体
5. **存在性检查**: 查询Tab是否存在，若不存在抛出 `404` 异常
6. **部分更新**: 只更新请求体中提供的字段
7. **更新数据库**: `UPDATE live_room_tabs SET ... WHERE id = :tabId`
8. **提交事务**: `await db.commit()`
9. **返回响应**: 返回更新后的Tab信息

---

#### 3.1.4 删除Tab（ADMIN，软删除）

**Endpoint**: `DELETE /api/v1/admin/tabs/{tabId}`

**描述**: 软删除Tab（设置 `is_active = false`）

**认证**: JWT认证 + 管理员权限

**路径参数**:
- `tabId` (UUID, required): Tab UUID

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "Tab删除成功",
  "data": null,
  "timestamp": "2026-06-07T10:00:00Z"
}
```

**执行流程**:

1. **接收请求**: API路由接收DELETE请求，解析路径参数
2. **JWT验证**: 通过 `Depends(get_current_user)` 提取当前用户
3. **权限检查**: 调用 `_check_admin_permission(user.role)` 校验管理员权限
4. **存在性检查**: 查询Tab是否存在，若不存在抛出 `404` 异常
5. **软删除**: `UPDATE live_room_tabs SET is_active = false WHERE id = :tabId`
6. **提交事务**: `await db.commit()`
7. **返回响应**: 返回删除成功响应

---

### 3.2 图片上传API

#### 3.2.1 上传Tab图片（Admin 或房间 owner）

**Endpoint**: `POST /api/v1/admin/rooms/{roomId}/tabs/image`

**描述**: 上传Tab图片

**认证**: JWT认证 + Admin/SUPERADMIN 或该房间 owner（与 Tab CRUD 一致）

**路径参数**:
- `roomId` (UUID, required): 直播间UUID

**请求体**: `multipart/form-data`
- `file` (File, required): 图片文件（支持 jpg, png, webp，最大2MB）

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "图片上传成功",
  "data": {
    "image_url": "/uploads/tabs/uuid-image.jpg"
  },
  "timestamp": "2026-06-07T10:00:00Z"
}
```

**执行流程**:

1. **接收请求**: API路由接收POST请求，解析multipart文件
2. **JWT验证**: 通过 `Depends(get_current_user)` 提取当前用户
3. **权限检查**: `_check_tab_management_permission` — Admin/SUPERADMIN 或房间 owner
4. **文件校验**: 检查文件类型（MIME type）和大小（≤2MB）
5. **生成文件名**: 使用 `uuid + 原始扩展名` 生成唯一文件名
6. **存储文件**: 保存到 `uploads/tabs/` 目录
7. **返回响应**: 返回图片URL

---

### 3.3 排序API

#### 3.3.1 批量排序Tab（ADMIN）

**Endpoint**: `PATCH /api/v1/admin/rooms/{roomId}/tabs/sort`

**描述**: 批量更新Tab的排序顺序

**认证**: JWT认证 + 管理员权限

**路径参数**:
- `roomId` (UUID, required): 直播间UUID

**请求体**:
```json
{
  "tab_ids": ["uuid-1", "uuid-2", "uuid-3"]
}
```

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "排序更新成功",
  "data": null,
  "timestamp": "2026-06-07T10:00:00Z"
}
```

**执行流程**:

1. **接收请求**: API路由接收PATCH请求
2. **JWT验证**: 通过 `Depends(get_current_user)` 提取当前用户
3. **权限检查**: 调用 `_check_admin_permission(user.role)` 校验管理员权限
4. **Pydantic校验**: 使用 `LiveRoomTabSortRequest` Schema校验请求体
5. **批量更新**: 遍历 `tab_ids`，按索引设置 `sort_order`
   ```python
   for index, tab_id in enumerate(tab_ids):
       await db.execute(
           update(LiveRoomTab)
           .where(LiveRoomTab.id == tab_id)
           .values(sort_order=index + 1)
       )
   ```
6. **提交事务**: `await db.commit()`
7. **返回响应**: 返回排序更新成功响应

---

### 3.4 公开API

#### 3.4.1 获取直播间Tab列表（公开）

**Endpoint**: `GET /api/v1/rooms/{roomId}/tabs`

**描述**: 获取指定直播间的启用Tab列表（用户端）

**认证**: 公开访问（Public）

**路径参数**:
- `roomId` (UUID, required): 直播间UUID

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": "uuid-string",
        "room_id": "room-uuid",
        "tab_key": "intro",
        "title": "科室介绍",
        "content_type": "text",
        "text_content": "肝胆胰外科简介...",
        "image_url": null,
        "sort_order": 0,
        "is_active": true,
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z"
      }
    ]
  },
  "timestamp": "2026-06-07T10:00:00Z"
}
```

**执行流程**:

1. **接收请求**: API路由接收GET请求，解析路径参数
2. **构建查询**: `SELECT * FROM live_room_tabs WHERE room_id = :roomId AND is_active = true ORDER BY sort_order ASC`
3. **执行查询**: 异步执行数据库查询
4. **返回响应**: 返回Tab列表

---

## 4. 执行流程详细说明

### 4.1 创建Tab完整流程

```
1. API路由接收POST请求
   → 2. JWT验证（Depends(get_current_user)）
   → 3. 权限检查（_check_admin_permission）
   → 4. Pydantic校验（LiveRoomTabCreate）
   → 5. 直播间存在性检查
   → 6. 生成UUID
   → 7. 插入数据库（INSERT INTO live_room_tabs）
   → 8. 提交事务（db.commit()）
   → 9. 返回JSON响应（201 Created）
```

### 4.2 批量排序完整流程

```
1. API路由接收PATCH请求
   → 2. JWT验证
   → 3. 权限检查
   → 4. Pydantic校验（LiveRoomTabSortRequest）
   → 5. 遍历tab_ids，按索引更新sort_order
   → 6. 提交事务
   → 7. 返回JSON响应
```

---

## 5. 错误处理与事务管理

### 5.1 错误处理策略

**业务异常**:
- 资源不存在（code=2001）→ HTTP 404

**系统异常**:
- 数据库连接失败 → HTTP 503

### 5.2 事务管理规范

**单表操作**: 使用单个事务，操作失败自动回滚

**批量排序**: 使用单个事务批量更新所有Tab的 `sort_order`

---

## 6. 性能优化建议

### 6.1 数据库优化

- **索引优化**: `(room_id, sort_order)` 复合索引加速排序查询
- **查询优化**: 用户端查询只返回 `is_active = true` 的记录

### 6.2 缓存策略

- **Redis缓存**: 用户端Tab列表可缓存5分钟（TTL=300s）
- **缓存键**: `room:{roomId}:tabs`
- **缓存失效**: 创建/更新/删除/排序Tab时清除缓存

---

## 7. 测试建议

### 7.1 单元测试

- Tab CRUD操作测试
- 软删除（is_active）测试
- 排序逻辑测试

### 7.2 集成测试

- API端点完整流程测试
- 权限验证测试
- 级联删除测试（删除直播间时Tab是否级联删除）

### 7.3 性能测试

- Tab列表查询性能（100+Tab）
- 并发排序操作测试
- 大量文本内容（text_content）的存储和查询性能

### 7.4 安全测试

- XSS测试（text_content 中的恶意脚本注入）
- 权限绕过测试

---

## 8. 错误码对照表

| 错误码 | 说明 | 使用场景 |
|--------|------|----------|
| `200` | 成功 | 所有成功响应 |
| `1002` | 数据库错误 | 数据库操作异常 |
| `2001` | 资源不存在 | Tab ID不存在、直播间不存在 |
| `3001` | 未授权 | JWT Token缺失或无效 |
| `3002` | 权限不足 | 非管理员访问管理端接口 |
| `4001` | 参数校验失败 | 请求参数不符合Schema规范 |

---

## 9. 部署与监控建议

### 9.1 部署检查清单

- [ ] 数据库迁移脚本已执行（live_room_tabs表）
- [ ] 触发器函数 `trigger_set_timestamp()` 已创建
- [ ] 上传目录 `uploads/tabs/` 已创建且有写入权限

### 9.2 监控指标

**API监控**:
- Tab CRUD接口响应时间（目标 < 200ms）
- 用户端查询响应时间（目标 < 100ms）

### 9.3 告警规则

**严重告警**:
- 数据库连接失败

**警告告警**:
- API响应时间 > 1s
- Tab数量异常增长（> 1000/直播间）

---

## 10. 后续开发建议

### 10.1 优先级P0（必须完成/第一批实现）

- [ ] live_room_tabs 表DDL创建
- [ ] Tab CRUD API实现（4个接口）
- [ ] 公开查询API实现

### 10.2 优先级P1（重要功能/第二批实现）

- [ ] 图片上传功能
- [ ] 批量排序功能
- [ ] Redis缓存集成

### 10.3 优先级P2（增强功能/优化阶段）

- [ ] text_content 内容清理（XSS过滤）
- [ ] Tab使用统计

---

## 📝 文档修订历史

| 版本 | 日期 | 修订内容 | 作者 |
|------|------|----------|------|
| V1.0 | 2026-06-07 | 初始版本 | Claude |
| V1.1 | 2026-06-08 | 同步后端实际代码：新增 tab_key、content_type 枚举字段，content 拆为 text_content + image_url，title 长度 200→128，新增枚举类型 DDL | Claude |

---

## 最终路由表

### ✅ 已实现（后端代码已存在）

| Domain | Endpoint | Method | Auth | Roles | Request Schema | Response Schema | Error Codes | Notes |
|--------|----------|--------|------|-------|----------------|-----------------|-------------|-------|
| admin | /api/v1/admin/rooms/{roomId}/tabs | GET | JWT | admin | Path: roomId | LiveRoomTabItem[] | 200, 3001, 3002, 1002 | 管理端Tab列表 |
| admin | /api/v1/admin/rooms/{roomId}/tabs | POST | JWT | admin | Body: LiveRoomTabCreate (tab_key, title, content_type, text_content?, image_url?, sort_order?, is_active?) | LiveRoomTabItem | 200, 2001, 3001, 3002, 4001, 1002 | 创建Tab |
| admin | /api/v1/admin/tabs/{tabId} | PATCH | JWT | admin | Body: LiveRoomTabUpdate (all optional) | LiveRoomTabItem | 200, 2001, 3001, 3002, 4001, 1002 | 更新Tab |
| admin | /api/v1/admin/tabs/{tabId} | DELETE | JWT | admin | Path: tabId | null | 200, 2001, 3001, 3002, 1002 | 软删除Tab |
| admin | /api/v1/admin/rooms/{roomId}/tabs/image | POST | JWT | Admin **或** 房间 owner | Path: roomId, Body: file | {image_url} | 200, 3001, 3002, 413, 415, 1002 | Tab 图片上传 |
| rooms | /api/v1/rooms/{roomId}/tabs | GET | Public | - | Path: roomId | LiveRoomTabItem[] | 200, 1002 | 用户端Tab列表 |

### 📋 待实现（设计已完成，后端未开发）

| Domain | Endpoint | Method | Auth | Roles | Request Schema | Response Schema | Error Codes | Notes | 优先级 |
|--------|----------|--------|------|-------|----------------|-----------------|-------------|-------|--------|
| admin | /api/v1/admin/rooms/{roomId}/tabs/sort | PATCH | JWT | admin | Body: LiveRoomTabSortRequest | null | 200, 3001, 3002, 4001, 1002 | 批量排序 | P1 |

---

**文档结束** ✅
