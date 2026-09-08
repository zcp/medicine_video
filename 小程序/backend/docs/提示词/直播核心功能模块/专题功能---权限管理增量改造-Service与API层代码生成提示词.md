# 专题功能 - 权限管理增量改造 - Service 与 API 层代码生成提示词

## ⚠️ 使用说明（重要）

**本提示词用于改造已有代码，不是生成新代码。**

在使用本提示词之前，**必须**在 Cursor 聊天框中先 `@` 引用本提示词文档和所有需要改造的代码文件：

```
@docs/提示词/专题功能---权限管理增量改造-Service与API层代码生成提示词.md
@app/core/deps.py
@app/core/security.py
@app/api/v1/endpoints/topic.py
@app/services/topic_service.py
@app/crud/topic.py
@app/models/topic.py
...（其他相关文件）
```

**⚠️ 关键**：AI 需要读取现有的代码文件，才能进行增量改造。如果不引用已有代码文件，AI 无法知道现有代码的结构和内容，将无法正确执行增量改造。

---

## 1. 角色定义

你是一名精通「学院派架构（Clean Architecture）」的资深 Python 后端架构师，专门负责对**已有代码进行权限管理的增量改造**。  

**你的任务**：
1. **读取上下文**：用户已经在提示词的开头使用了 Cursor 的 `@` 标记引用了**已有的代码文件**（例如 `@app/api/v1/endpoints/topic.py`、`@app/services/topic_service.py` 等）。
2. **分析现有代码**：**读取**这些 `@` 引用的代码文件内容，分析现有的API接口、Service方法、业务逻辑等。
3. **增量改造**：在**不破坏现有业务逻辑**的前提下，为所有 API 接口和 Service 方法**最小幅度地融合权限设计**。

**⚠️ 重要**：你已经在上一版中完成了所有专题功能的实现（Topic、TopicCategory、TopicCategoryRoom 等），现在只需要进行权限管理的增量改造，**严禁重写或删除任何已有业务逻辑代码**。

## 2. 任务目标（权限增量范围）

本次任务 **只做权限管理相关的最小增量改造**，严禁重写或删除任何已有业务逻辑代码：

### 2.1 核心改造原则（⚠️ 必须严格遵守）

1. **最小幅度修改原则**：
   - ✅ **只增加**权限相关的代码（依赖注入、参数传递、权限校验调用）
   - ✅ **只修改**方法签名（增加 `user_id`、`role` 参数）
   - ❌ **禁止**修改任何业务逻辑执行流程
   - ❌ **禁止**删除或重命名任何现有方法
   - ❌ **禁止**改变任何方法的返回值结构（除非设计文档明确要求）

2. **职责分层原则**：
   - **API 层 (Controller/Dependency)**：仅负责 **Authentication (认证)** —— 解析"你是谁"（User 还是 Anonymous）
   - **Service 层 (Domain Logic)**：全权负责 **Authorization (鉴权)** —— 判定"你能看吗/你能改吗"

3. **向后兼容原则**：
   - 所有权限相关的改动必须对现有调用方透明
   - 新增的权限参数必须使用合适的默认值或 Optional 类型
   - 响应结构保持不变（除非设计文档明确要求新增字段）

4. **专题功能特殊说明**：
   - 专题功能使用 `status` 字段（ENUM: draft/published/archived）而非 `is_private` 字段
   - **权限映射关系**：
     - `status = 'published'` ↔ `is_private = false`（公开，支持匿名访问）
     - `status = 'draft'` 或 `status = 'archived'` ↔ `is_private = true`（私有，仅Owner/Admin可访问）
   - 权限守卫函数使用 `_check_topic_visibility` 和 `_check_write_permission`（基于 `status` 字段）

### 2.2 改造范围

根据《直播核心功能设计文档_v6_增加专题功能权限管理增量设计版.md》，需要对以下16个接口进行权限融合：

| 模块 | 接口数量 | 主要改造点 |
|------|---------|-----------|
| Topic 模块 | 6个接口 | Optional Auth（读操作）+ Strict Auth（写操作） |
| Category 模块 | 4个接口 | 继承 Topic 的 status 权限 |
| Association 模块 | 4个接口 | 双重权限过滤（Topic status + Room is_private） |
| Auxiliary 模块 | 2个接口 | Optional Auth + 双重权限过滤 |

**详细接口清单**：

| 接口序号 | 接口路径 | 方法 | Auth策略 | 改造类型 |
|---------|---------|------|---------|---------|
| 1 | `/api/v1/topics` | POST | Strict | ✅ 需要改造 |
| 2 | `/api/v1/topics/{topic_id}/banner` | POST | Strict | ✅ 需要改造 |
| 3 | `/api/v1/topics` | GET | Optional | ✅ 需要改造 |
| 4 | `/api/v1/topics/{topic_id}` | GET | Optional | ✅ 需要改造 |
| 5 | `/api/v1/topics/{topic_id}` | PATCH | Strict | ✅ 需要改造 |
| 6 | `/api/v1/topics/{topic_id}` | DELETE | Strict | ✅ 需要改造 |
| 7 | `/api/v1/topics/{topic_id}/categories` | POST | Strict | ✅ 需要改造 |
| 8 | `/api/v1/topics/{topic_id}/categories` | GET | Optional | ✅ 需要改造 |
| 9 | `/api/v1/topic-categories/{category_id}` | PATCH | Strict | ✅ 需要改造 |
| 10 | `/api/v1/topic-categories/{category_id}` | DELETE | Strict | ✅ 需要改造 |
| 11 | `/api/v1/topic-categories/{category_id}/rooms` | POST | Strict | ✅ 需要改造 |
| 12 | `/api/v1/topic-categories/{category_id}/rooms` | GET | Optional | ✅ 需要改造 |
| 13 | `/api/v1/topic-categories/{category_id}/rooms/sort-order` | PATCH | Strict | ✅ 需要改造 |
| 14 | `/api/v1/topic-categories/{category_id}/rooms` | DELETE | Strict | ✅ 需要改造 |
| 15 | `/api/v1/rooms/{room_id}/topics` | GET | Optional | ✅ 需要改造 |
| 16 | `/api/v1/rooms/batch-status` | POST | Optional | ✅ 需要改造 |

## 3. 项目文件组织结构

### 3.1 项目目录结构

```
backend/live_core_service/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   └── endpoints/
│   │   │       └── topic.py            # Topic模块API接口
│   │   └── deps.py                     # 依赖注入（get_current_user, get_current_user_optional）
│   ├── core/
│   │   ├── deps.py                     # 核心依赖注入函数
│   │   └── security.py                 # JWT Token生成和验证
│   ├── services/
│   │   ├── topic_service.py            # Topic Service
│   │   ├── category_service.py         # Category Service
│   │   ├── association_service.py      # Association Service
│   │   └── auxiliary_service.py        # Auxiliary Service
│   ├── crud/
│   │   └── topic.py                    # Topic CRUD
│   ├── models/
│   │   └── topic.py                    # Topic模型
│   └── schemas/
│       └── topic.py                    # Topic Schema
```

### 3.2 必须引用的代码文件（⚠️ 重要）

在使用本提示词时，用户**必须**通过 `@` 引用以下代码文件：

#### Core层文件（必须引用）
- `@app/core/deps.py` - 依赖注入函数（需要实现 `get_current_user` 和 `get_current_user_optional`）
- `@app/core/security.py` - JWT Token生成和验证（如果存在）

#### API层文件（必须引用）
- `@app/api/v1/endpoints/topic.py` - Topic模块API接口（16个接口）

#### Service层文件（必须引用）
- `@app/services/topic_service.py` - Topic Service（6个方法）
- `@app/services/category_service.py` - Category Service（4个方法）
- `@app/services/association_service.py` - Association Service（4个方法）
- `@app/services/auxiliary_service.py` - Auxiliary Service（2个方法）

#### CRUD层文件（推荐引用，用于了解数据访问层）
- `@app/crud/topic.py` - Topic CRUD（需要了解 `get_multi` 方法）

#### Models和Schemas文件（可选引用）
- `@app/models/topic.py` - Topic模型（了解字段定义）
- `@app/schemas/topic.py` - Topic Schema（了解请求/响应结构）

**⚠️ 重要**：
- 如果某些文件不存在，可以只引用存在的文件
- AI 需要读取这些文件来了解现有代码的结构和内容
- 如果不引用这些文件，AI 无法知道现有代码，将无法正确执行增量改造

## 4. 内容来源（设计文档）

所有实现必须严格对齐以下设计文档，**不得自创权限逻辑或偏离语义**：

- **主设计文档**：`docs/03_系统设计/直播核心功能设计文档_v6_深度融合最终版.md`
  - 提供所有接口的原始业务逻辑定义
  - 提供数据库 Schema 和字段定义
  
- **专题功能设计文档**：`docs/03_系统设计/直播核心功能设计文档_v6_增加专题功能完整设计文档-修正版.md`
  - 提供专题功能的业务逻辑定义

- **权限设计文档**：`docs/03_系统设计/直播核心功能设计文档_v6_增加专题功能权限管理增量设计版.md`
  - **重点章节**：
    - § 1「核心设计原则」—— 5条核心原则
    - § 2「身份模型与鉴权策略」—— Strict Auth vs Optional Auth
    - § 3「全量 API 接口改造详单」—— 16个接口的详细改造方案
    - § 3.5「Service层方法补充（权限集成示例）」—— 16个Service方法的权限集成示例
    - § 4「实施层代码规范」—— 依赖注入、守卫函数、Repository 优化、API 层示例
    - § 6「完整接口权限矩阵」—— 快速参考表
    - § 10.2「Service方法覆盖验证」—— 16个Service方法的权限参数验证

**⚠️ 重要**：如权限设计文档与主设计文档存在歧义，以 **权限设计文档（v6.1 Topic Permission Edition）** 为最终口径。

## 5. 核心架构与编码约束（继承原有规范）

完全继承原有「Service 与 API 层代码生成提示词」中的全部规范，包括但不限于：

### 5.1 用户身份解析规范（JWT → UUID + Role）

**API 层**必须使用以下模式解析 JWT Token：

```python
from typing import Optional, Dict
from uuid import UUID
from fastapi import Depends
from app.core.deps import get_current_user, get_current_user_optional

# 场景 A：Strict Auth（写操作、敏感读操作）
current_user: Dict = Depends(get_current_user)
user_id = UUID(current_user["user_id"])  # 从JWT的user_id字段提取
role = current_user.get("role")  # 从JWT的role字段提取（Strict Auth场景下JWT应包含role字段）

# 场景 B：Optional Auth（读操作，支持匿名访问）
current_user: Optional[Dict] = Depends(get_current_user_optional)
user_id = UUID(current_user["user_id"]) if current_user else None
role = current_user.get("role") if current_user else None
```

**⚠️ 关键约束**：
- JWT Payload 使用 `user_id` 字段（而非 JWT 标准的 `sub` 字段）
- `user_id` 存储的是用户的 `public_id`（UUID 格式）
- `role` 为字符串枚举值：`REGULAR`、`MODERATOR`、`ADMIN`、`SUPERADMIN`

### 5.2 Service 层权限参数规范

Service 层方法**必须**接收权限相关参数，但**不得**接受 ORM `User` 实体：

```python
# ✅ 正确：接收基础类型参数
async def create_topic(
    self,
    data: TopicCreate,
    user_id: UUID,           # 从JWT的user_id字段提取
    role: str                # 从JWT的role字段提取
) -> Topic:
    ...

# ✅ 正确：Optional Auth 场景
async def list_topics(
    self,
    pagination: PageParams,
    status: Optional[str] = None,
    user_id: Optional[UUID] = None,  # 匿名时为None
    role: Optional[str] = None       # 匿名时为None
) -> Tuple[List[Topic], int]:
    ...

# ❌ 错误：不要接受ORM实体
async def create_topic(
    self,
    data: TopicCreate,
    current_user: User  # 禁止！
) -> Topic:
    ...
```

### 5.3 分层职责（学院派核心）

- **Service 层**：
  - ✅ 负责业务逻辑与权限校验
  - ✅ 抛出自定义 Python 异常（`TopicNotFoundException`、`PermissionDeniedException` 等）
  - ✅ 调用权限守卫函数（`_check_topic_visibility`、`_check_write_permission` 等）
  - ❌ 不抛出 `HTTPException`
  - ❌ 不处理事务（不调用 `db.commit()` / `db.rollback()`）

- **API 层**：
  - ✅ 使用 `try...except` 捕获所有 Service 抛出的自定义异常
  - ✅ 使用 `JSONResponse` + `error_response()` 构建错误响应
  - ✅ 使用 `success_response()` 构建成功响应
  - ✅ 在 `try` 块**之前**提取用户信息（避免在 `except` 中访问已失效对象）
  - ❌ 不做复杂业务逻辑与权限判断（只做最薄的参数层封装）

### 5.4 异常与错误码映射

沿用原有规范，将异常映射到 HTTP 状态码 + 业务错误码：

| Service 层异常 | HTTP 状态码 | 业务错误码 | 说明 |
|---------------|-----------|-----------|------|
| `TopicNotFoundException` / `NotFoundException` | 404 | 2001 | 专题不存在或无权访问（Draft/Archived专题隐藏） |
| `PermissionDeniedException` | 403 | 3002 | 权限不足（已登录但非Owner/Admin） |
| `InvalidParameterException` | 400 | 4xxx | 参数校验失败 |
| `DatabaseIntegrityException` | 400 | 4001 | 数据库唯一约束冲突 |
| 未捕获异常 | 500 | 1000 | 系统内部错误 |

**⚠️ 安全关键**：对于无权访问的 Draft/Archived 专题，必须返回 **404 Not Found**，严禁返回 403，以防止恶意用户通过枚举 ID 探测资源的存在性。

## 6. 权限改造实施模式（最小幅度修改）

### 6.1 API 层改造模式

#### 模式 A：Strict Auth（强制鉴权）- 写操作

**改造前**：
```python
@router.post("", response_model=TopicResponse)
async def create_topic(
    data: TopicCreate,
    service: TopicService = Depends()
):
    topic = await service.create_topic(data)
    return success_response(data=topic)
```

**改造后**（最小幅度修改）：
```python
@router.post("", response_model=TopicResponse)
async def create_topic(
    data: TopicCreate,
    current_user: Dict = Depends(get_current_user),  # ← 新增：依赖注入
    service: TopicService = Depends()
):
    # ← 新增：提取用户信息（在try之前）
    user_id = UUID(current_user["user_id"])
    role = current_user.get("role")  # Strict Auth场景下JWT应包含role字段
    
    try:
        # ← 修改：传递权限参数
        topic = await service.create_topic(data, user_id, role)
        
        # ✅ 记录业务操作成功日志（INFO级别）
        logger.info(
            f"专题创建成功: topic_id={topic.id}, user={user_id}, "
            f"status={topic.status}, title={topic.title}"
        )
        
        return success_response(data=topic)
    except Exception as e:
        # 异常处理逻辑保持不变
        logger.error(f"创建专题失败: user={user_id}, error={e}", exc_info=True)
        return error_response(code=1000, message=str(e))
```

#### 模式 B：Optional Auth（可选鉴权）- 读操作

**改造前**：
```python
@router.get("", response_model=PaginatedResponse)
async def list_topics(
    pagination: PageParams = Depends(),
    status: Optional[str] = None,
    service: TopicService = Depends()
):
    topics, total = await service.list_topics(pagination, status)
    return success_response(data={"items": topics, "total": total})
```

**改造后**（最小幅度修改）：
```python
@router.get("", response_model=PaginatedResponse)
async def list_topics(
    pagination: PageParams = Depends(),
    status: Optional[str] = None,
    current_user: Optional[Dict] = Depends(get_current_user_optional),  # ← 修改：Optional依赖
    service: TopicService = Depends()
):
    # ← 新增：提取用户信息（可能为None）
    user_id = UUID(current_user["user_id"]) if current_user else None
    role = current_user.get("role") if current_user else None
    
    try:
        # ← 修改：传递权限参数（可能为None）
        topics, total = await service.list_topics(pagination, status, user_id, role)
        return success_response(data={
            "items": topics,
            "total": total,
            "page": pagination.page,
            "size": pagination.size
        })
    except Exception as e:
        # 异常处理逻辑保持不变
        return error_response(code=1000, message=str(e))
```

#### 模式 C：Optional Auth + 404 伪装

**改造前**：
```python
@router.get("/{topic_id}", response_model=TopicResponse)
async def get_topic_detail(
    topic_id: UUID,
    service: TopicService = Depends()
):
    topic = await service.get_topic_detail(topic_id)
    return success_response(data=topic)
```

**改造后**（最小幅度修改）：
```python
@router.get("/{topic_id}", response_model=TopicResponse)
async def get_topic_detail(
    topic_id: UUID,
    current_user: Optional[Dict] = Depends(get_current_user_optional),  # ← 修改：Optional依赖
    service: TopicService = Depends()
):
    # ← 新增：提取用户信息
    user_id = UUID(current_user["user_id"]) if current_user else None
    role = current_user.get("role") if current_user else None
    
    try:
        # ← 修改：传递权限参数
        topic = await service.get_topic_detail(topic_id, user_id, role)
        return success_response(data=topic)
    except NotFoundException as e:  # ← 新增：捕获404异常
        # ← 新增：返回404（隐藏Draft/Archived专题存在性）
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="Topic not found")
        )
    except Exception as e:
        # 其他异常处理逻辑保持不变
        return error_response(code=1000, message=str(e))
```

### 6.2 Service 层改造模式

#### 模式 A：Strict Auth Service 方法

**改造前**：
```python
async def create_topic(
    self,
    data: TopicCreate
) -> Topic:
    """创建专题"""
    # 业务逻辑：生成UUID、创建记录等
    topic_data = {
        "id": uuid.uuid4(),
        "title": data.title,
        "status": data.status or "draft",
        # ... 其他字段
    }
    topic = await self.crud.topic.create(self.db, topic_data)
    return topic
```

**改造后**（最小幅度修改）：
```python
async def create_topic(
    self,
    data: TopicCreate,
    user_id: UUID,  # ← 新增：权限参数
    role: str       # ← 新增：权限参数
) -> Topic:
    """创建专题（所有登录用户可创建）"""
    # 业务逻辑保持不变，只增加user_id设置
    topic_data = {
        "id": uuid.uuid4(),
        "title": data.title,
        "status": data.status or "draft",
        "user_id": user_id,  # ← 新增：设置创建者（Owner）
        # ... 其他字段
    }
    topic = await self.crud.topic.create(self.db, topic_data)
    logger.info(f"专题创建成功: topic_id={topic.id}, user={user_id}")
    return topic
```

#### 模式 B：Optional Auth Service 方法（列表查询）

**改造前**：
```python
async def list_topics(
    self,
    pagination: PageParams,
    status: Optional[str] = None
) -> Tuple[List[Topic], int]:
    """获取专题列表"""
    topics, total = await self.crud.topic.get_multi(
        self.db,
        page=pagination.page,
        size=pagination.size,
        status=status
    )
    return topics, total
```

**改造后**（最小幅度修改）：
```python
async def list_topics(
    self,
    pagination: PageParams,
    status: Optional[str] = None,
    user_id: Optional[UUID] = None,  # ← 新增：权限参数
    role: Optional[str] = None       # ← 新增：权限参数
) -> Tuple[List[Topic], int]:
    """获取专题列表（支持匿名访问）"""
    # 业务逻辑保持不变，只传递权限参数到CRUD层
    topics, total = await self.crud.topic.get_multi(
        self.db,
        user_id=user_id,  # ← 新增：传递权限参数
        role=role,        # ← 新增：传递权限参数
        page=pagination.page,
        size=pagination.size,
        status=status
    )
    return topics, total
```

#### 模式 C：Optional Auth Service 方法（详情查询 + 权限守卫）

**改造前**：
```python
async def get_topic_detail(
    self,
    topic_id: UUID
) -> Topic:
    """获取专题详情"""
    topic = await self.crud.topic.get(self.db, id=topic_id)
    if not topic:
        raise TopicNotFoundException(f"专题 {topic_id} 不存在")
    
    # 业务逻辑：关联查询分类和直播间
    # ...
    return topic
```

**改造后**（最小幅度修改）：
```python
async def get_topic_detail(
    self,
    topic_id: UUID,
    user_id: Optional[UUID] = None,  # ← 新增：权限参数
    role: Optional[str] = None       # ← 新增：权限参数
) -> Topic:
    """获取专题详情（支持匿名访问）"""
    topic = await self.crud.topic.get(self.db, id=topic_id)
    if not topic:
        raise TopicNotFoundException(f"专题 {topic_id} 不存在")
    
    # ← 新增：权限校验（调用守卫函数）
    self._check_topic_visibility(topic, user_id, role)
    
    # 业务逻辑保持不变：关联查询分类和直播间
    # ...
    return topic
```

#### 模式 D：Strict Auth Service 方法（写操作 + 权限守卫）

**改造前**：
```python
async def update_topic(
    self,
    topic_id: UUID,
    data: TopicUpdate
) -> Topic:
    """更新专题"""
    topic = await self.crud.topic.get(self.db, id=topic_id)
    if not topic:
        raise TopicNotFoundException(f"专题 {topic_id} 不存在")
    
    # 业务逻辑：更新字段
    updated_topic = await self.crud.topic.update(self.db, id=topic_id, data=data)
    return updated_topic
```

**改造后**（最小幅度修改）：
```python
async def update_topic(
    self,
    topic_id: UUID,
    data: TopicUpdate,
    user_id: UUID,  # ← 新增：权限参数
    role: str       # ← 新增：权限参数
) -> Topic:
    """更新专题（Owner/Admin Only）"""
    topic = await self.crud.topic.get(self.db, id=topic_id)
    if not topic:
        raise TopicNotFoundException(f"专题 {topic_id} 不存在")
    
    # ← 新增：权限校验（调用守卫函数）
    self._check_write_permission(topic, user_id, role)
    
    # 业务逻辑保持不变：更新字段
    updated_topic = await self.crud.topic.update(self.db, id=topic_id, data=data)
    
    # ✅ 记录业务操作成功日志（INFO级别）
    logger.info(f"专题更新成功: topic_id={topic_id}, user={user_id}")
    
    return updated_topic
```

### 6.3 Service 层权限守卫函数

专题功能需要实现专用的权限守卫函数，基于 `status` 字段而非 `is_private` 字段：

```python
# app/services/topic_service.py
from typing import Optional
from uuid import UUID
from app.core.exceptions import (
    NotFoundException,
    PermissionDeniedException,
)
from app.exceptions import TopicNotFoundException  # TopicNotFoundException继承自NotFoundException
from app.models.topic import Topic

class TopicService:
    """专题服务（包含权限守卫函数）"""
    
    def _check_topic_visibility(
        self,
        topic: Topic,
        user_id: Optional[UUID],
        role: Optional[str]
    ) -> None:
        """
        统一的专题可见性校验逻辑（基于status字段）
        
        Args:
            topic: 专题对象
            user_id: 当前用户的public_id（从JWT的user_id字段提取，匿名时为None）
            role: 当前用户的角色（匿名时为None）
            
        Raises:
            TopicNotFoundException: 专题不存在或无权访问（404）
        """
        # 1. 已发布专题：直接通过（相当于is_private=false）
        if topic.status == 'published':
            return
        
        # 2. 草稿/已归档专题且未登录：拒绝（返回404隐藏存在性）
        if not user_id:
            raise TopicNotFoundException("Topic not found")
        
        # 3. 管理员：上帝视角通过
        if role in ['ADMIN', 'SUPERADMIN']:
            # ✅ 记录Admin查看Private资源的审计日志（INFO级别）
            if topic.user_id != user_id:
                logger.info(
                    f"Admin查看Private专题: admin={user_id}, role={role}, "
                    f"topic_id={topic.id}, owner={topic.user_id}, status={topic.status}"
                )
            return
        
        # 4. 资源创建者：通过
        # 注意：topic.user_id存储的就是创建者的public_id
        if topic.user_id == user_id:
            return
        
        # 5. 其他已登录用户：拒绝（返回404隐藏存在性）
        raise TopicNotFoundException("Topic not found")
    
    def _check_write_permission(
        self,
        topic: Topic,
        user_id: UUID,
        role: str
    ) -> None:
        """
        写操作权限校验（修改/删除）
        
        Args:
            topic: 专题对象
            user_id: 当前用户的public_id
            role: 当前用户的角色
            
        Raises:
            PermissionDeniedException: 无权修改（403）
        """
        # 管理员：上帝视角通过
        if role in ['ADMIN', 'SUPERADMIN']:
            return
        
        # 资源创建者：通过
        # 注意：topic.user_id存储的就是创建者的public_id
        if topic.user_id == user_id:
            return
        
        # 其他用户：拒绝（返回403，因为已登录）
        raise PermissionDeniedException(
            "You don't have permission to modify this topic"
        )
```

**⚠️ 重要**：
- `_check_topic_visibility` 用于读操作（详情查询），基于 `status` 字段判断可见性
- `_check_write_permission` 用于写操作（修改/删除），检查 Owner/Admin 权限
- `TopicNotFoundException` 应继承自 `NotFoundException`，确保异常处理的一致性

### 6.4 双重权限过滤场景

专题功能中存在需要同时考虑专题权限和直播间权限的场景：

#### 场景 A：获取分类下的直播间列表

**接口**：`GET /api/v1/topic-categories/{category_id}/rooms`

**权限逻辑**：
1. 先检查专题可见性（专题必须是 `published`，或用户是专题 Owner/Admin）
2. 再在查询直播间时应用 Room 模块的权限过滤（直播间必须是 `is_private=false`，或用户是直播间 Owner/Admin）

**Service 层实现**：
```python
async def list_rooms_in_category(
    self,
    category_id: UUID,
    pagination: PageParams,
    user_id: Optional[UUID] = None,
    role: Optional[str] = None
) -> Tuple[List[LiveRoom], int]:
    """获取分类下的直播间列表（双重权限过滤）"""
    # 1. 获取分类（继承专题权限）
    category = await self.crud.category.get(self.db, id=category_id)
    if not category:
        raise CategoryNotFoundException(f"分类 {category_id} 不存在")
    
    # 2. 获取专题并检查可见性
    topic = await self.crud.topic.get(self.db, id=category.topic_id)
    if not topic:
        raise TopicNotFoundException(f"专题 {topic.id} 不存在")
    
    # ← 新增：检查专题可见性
    self._check_topic_visibility(topic, user_id, role)
    
    # 3. 查询直播间（应用Room模块的权限过滤）
    rooms, total = await self.crud.category_room.get_multi(
        self.db,
        category_id=category_id,
        user_id=user_id,  # ← 用于直播间权限过滤
        role=role,        # ← 用于直播间权限过滤
        page=pagination.page,
        size=pagination.size
    )
    
    return rooms, total
```

#### 场景 B：获取直播间关联的专题列表

**接口**：`GET /api/v1/rooms/{room_id}/topics`

**权限逻辑**：
1. 先检查直播间可见性（直播间必须是 `is_private=false`，或用户是直播间 Owner/Admin）
2. 再在查询专题时应用 Topic 模块的权限过滤（专题必须是 `published`，或用户是专题 Owner/Admin）

**Service 层实现**：
```python
async def get_room_topics(
    self,
    room_id: UUID,
    user_id: Optional[UUID] = None,
    role: Optional[str] = None
) -> List[Dict]:
    """获取直播间关联的专题列表（双重权限过滤）"""
    # 1. 检查直播间可见性（使用Room模块的权限守卫函数）
    room = await self.crud.room.get(self.db, id=room_id)
    if not room:
        raise RoomNotFoundException(f"直播间 {room_id} 不存在")
    
    # ← 新增：检查直播间可见性（需要导入RoomService的守卫函数或复用）
    # 注意：这里需要调用Room模块的权限守卫函数
    # 如果RoomService已实现，可以通过依赖注入或服务组合的方式调用
    # 例如：from app.services.room_service import RoomService
    #      room_service = RoomService(self.db)
    #      room_service._check_room_visibility(room, user_id, role)
    
    # 2. 查询关联的专题（应用Topic模块的权限过滤）
    # 注意：get_topics_by_room 方法已在CRUD层实现（参见专题功能CRUD层代码生成提示词），
    # 通过三表JOIN查询：topic_category_rooms -> topic_categories -> topics
    # 根据用户身份应用不同的WHERE条件（参见权限设计文档 § 3.1 接口3的SQL策略）：
    # - Admin：无过滤，看所有状态的专题
    # - Regular User：Published OR (Draft/Archived AND Own)
    # - Anonymous：Only Published
    # 注意：该方法在权限增补时需要增加 user_id 和 role 参数，参见CRUD层权限增补提示词文档
    topics = await self.crud.topic.get_topics_by_room(
        self.db,
        room_id=room_id,
        user_id=user_id,  # ← 用于专题权限过滤（权限增补新增参数）
        role=role        # ← 用于专题权限过滤（权限增补新增参数）
    )
    
    return topics
```

## 7. 完整改造清单

### 7.1 Topic 模块接口改造（6个接口）

| 接口序号 | 接口路径 | 方法 | Auth策略 | API层改造 | Service层改造 | 状态 |
|---------|---------|------|---------|----------|-------------|------|
| 1 | `/api/v1/topics` | POST | Strict | ✅ 增加依赖注入+参数提取 | ✅ 增加user_id/role参数 | ✅ 必须改造 |
| 2 | `/api/v1/topics/{topic_id}/banner` | POST | Strict | ✅ 增加依赖注入+参数提取 | ✅ 增加user_id/role参数+权限守卫 | ✅ 必须改造 |
| 3 | `/api/v1/topics` | GET | Optional | ✅ 修改为Optional依赖+参数提取 | ✅ 增加user_id/role参数（Optional） | ✅ 必须改造 |
| 4 | `/api/v1/topics/{topic_id}` | GET | Optional | ✅ 修改为Optional依赖+参数提取+404捕获 | ✅ 增加user_id/role参数+权限守卫 | ✅ 必须改造 |
| 5 | `/api/v1/topics/{topic_id}` | PATCH | Strict | ✅ 增加依赖注入+参数提取 | ✅ 增加user_id/role参数+权限守卫 | ✅ 必须改造 |
| 6 | `/api/v1/topics/{topic_id}` | DELETE | Strict | ✅ 增加依赖注入+参数提取 | ✅ 增加user_id/role参数+权限守卫 | ✅ 必须改造 |

### 7.2 Category 模块接口改造（4个接口）

| 接口序号 | 接口路径 | 方法 | Auth策略 | API层改造 | Service层改造 | 状态 |
|---------|---------|------|---------|----------|-------------|------|
| 7 | `/api/v1/topics/{topic_id}/categories` | POST | Strict | ✅ 增加依赖注入+参数提取 | ✅ 增加user_id/role参数+继承专题权限 | ✅ 必须改造 |
| 8 | `/api/v1/topics/{topic_id}/categories` | GET | Optional | ✅ 修改为Optional依赖+参数提取 | ✅ 增加user_id/role参数+继承专题权限 | ✅ 必须改造 |
| 9 | `/api/v1/topic-categories/{category_id}` | PATCH | Strict | ✅ 增加依赖注入+参数提取 | ✅ 增加user_id/role参数+继承专题权限 | ✅ 必须改造 |
| 10 | `/api/v1/topic-categories/{category_id}` | DELETE | Strict | ✅ 增加依赖注入+参数提取 | ✅ 增加user_id/role参数+继承专题权限 | ✅ 必须改造 |

### 7.3 Association 模块接口改造（4个接口）

| 接口序号 | 接口路径 | 方法 | Auth策略 | API层改造 | Service层改造 | 状态 |
|---------|---------|------|---------|----------|-------------|------|
| 11 | `/api/v1/topic-categories/{category_id}/rooms` | POST | Strict | ✅ 增加依赖注入+参数提取 | ✅ 增加user_id/role参数+双重权限过滤 | ✅ 必须改造 |
| 12 | `/api/v1/topic-categories/{category_id}/rooms` | GET | Optional | ✅ 修改为Optional依赖+参数提取 | ✅ 增加user_id/role参数+双重权限过滤 | ✅ 必须改造 |
| 13 | `/api/v1/topic-categories/{category_id}/rooms/sort-order` | PATCH | Strict | ✅ 增加依赖注入+参数提取 | ✅ 增加user_id/role参数+双重权限过滤 | ✅ 必须改造 |
| 14 | `/api/v1/topic-categories/{category_id}/rooms` | DELETE | Strict | ✅ 增加依赖注入+参数提取 | ✅ 增加user_id/role参数+双重权限过滤 | ✅ 必须改造 |

### 7.4 Auxiliary 模块接口改造（2个接口）

| 接口序号 | 接口路径 | 方法 | Auth策略 | API层改造 | Service层改造 | 状态 |
|---------|---------|------|---------|----------|-------------|------|
| 15 | `/api/v1/rooms/{room_id}/topics` | GET | Optional | ✅ 修改为Optional依赖+参数提取 | ✅ 增加user_id/role参数+双重权限过滤 | ✅ 必须改造 |
| 16 | `/api/v1/rooms/batch-status` | POST | Optional | ✅ 修改为Optional依赖+参数提取 | ✅ 增加user_id/role参数（Optional） | ✅ 必须改造 |

## 8. 编码规范（继承母版）

完全遵循 `docs/提示词/自动化后端代码生成/crud_service_endpoint代码生成提示词母版.md` 中定义的所有编码规范，包括但不限于：

- **学院派架构原则**
- **事务处理规范**
- **异常处理规范**
- **日志记录规范**
- **安全异步异常处理规范**
- **响应处理规范**
- **配置规范**

## 9. 实施检查清单

在完成改造后，请逐一检查：

- [ ] **1. API层依赖注入**：所有接口是否使用了正确的依赖注入（`get_current_user` 或 `get_current_user_optional`）？
- [ ] **2. API层参数提取**：是否在 `try` 块之前提取了 `user_id` 和 `role`？
- [ ] **3. Service方法签名**：`user_id` 和 `role` 参数类型是否正确（UUID/Optional[UUID] 和 str/Optional[str]）？
- [ ] **4. Service权限守卫**：读操作是否调用了 `_check_topic_visibility`？写操作是否调用了 `_check_write_permission`？
- [ ] **5. 404伪装**：无权访问的 Draft/Archived 专题是否返回 404 而非 403？
- [ ] **6. 双重权限过滤**：需要双重权限过滤的接口是否先检查专题权限，再检查直播间权限？
- [ ] **7. 业务逻辑完整性**：是否保留了所有原有的业务逻辑（关联查询、计算等）？
- [ ] **8. 异常处理**：是否捕获了所有 Service 层抛出的异常并转换为正确的 HTTP 响应？
- [ ] **9. 日志记录**：是否记录了业务操作成功日志和异常日志？
- [ ] **10. 代码完整性**：是否覆盖了所有16个API接口和16个Service方法？

## 10. 参考实现示例

完整的实现示例请参考权限设计文档：
- § 3.5「Service层方法补充（权限集成示例）」—— 16个Service方法的完整权限集成示例
- § 4.2「Service 层通用守卫函数」—— `_check_topic_visibility` 和 `_check_write_permission` 完整实现
- § 4.4「API 层实现示例」—— API 层完整实现示例

---

**文档版本**：v1.0  
**最后更新**：2025-01-XX  
**依赖文档**：
- 《直播核心功能设计文档_v6_深度融合最终版.md》
- 《直播核心功能设计文档_v6_增加专题功能完整设计文档-修正版.md》
- 《直播核心功能设计文档_v6_增加专题功能权限管理增量设计版.md》
