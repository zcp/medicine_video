# 直播核心功能 - 权限管理增量改造 - Service 与 API 层代码生成提示词

## ⚠️ 使用说明（重要）

**本提示词用于改造已有代码，不是生成新代码。**

在使用本提示词之前，**必须**在 Cursor 聊天框中先 `@` 引用本提示词文档和所有需要改造的代码文件：

```
@docs/提示词/直播核心功能---权限管理增量改造-Service与API层代码生成提示词.md
@app/core/deps.py
@app/core/security.py
@app/api/endpoints/room.py
@app/api/endpoints/session.py
@app/api/endpoints/tab.py
@app/api/endpoints/message.py
@app/api/endpoints/batch_import.py
@app/services/room.py
@app/services/session.py
@app/services/tab.py
@app/services/message.py
@app/services/batch_import.py
@app/crud/room.py
@app/crud/session.py
...（其他相关文件）
```

**⚠️ 关键**：AI 需要读取现有的代码文件，才能进行增量改造。如果不引用已有代码文件，AI 无法知道现有代码的结构和内容，将无法正确执行增量改造。

---

## 1. 角色定义

你是一名精通「学院派架构（Clean Architecture）」的资深 Python 后端架构师，专门负责对**已有代码进行权限管理的增量改造**。  

**你的任务**：
1. **读取上下文**：用户已经在提示词的开头使用了 Cursor 的 `@` 标记引用了**已有的代码文件**（例如 `@app/api/endpoints/room.py`、`@app/services/room.py` 等）。
2. **分析现有代码**：**读取**这些 `@` 引用的代码文件内容，分析现有的API接口、Service方法、业务逻辑等。
3. **增量改造**：在**不破坏现有业务逻辑**的前提下，为所有 API 接口和 Service 方法**最小幅度地融合权限设计**。

**⚠️ 重要**：你已经在上一版中完成了所有业务功能的实现（Room、Session、Tab、Message、Batch Import 等），现在只需要进行权限管理的增量改造，**严禁重写或删除任何已有业务逻辑代码**。

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

### 2.2 改造范围

根据《直播核心功能设计文档 v6.1：权限体系与接口改造全案》，需要对以下22个接口进行权限融合：

| 模块 | 接口数量 | 主要改造点 |
|------|---------|-----------|
| Room 模块 | 9个接口 | Optional Auth（读操作）+ Strict Auth（写操作） |
| Session 模块 | 6个接口 | 继承 Room 的 is_private 权限 |
| Tab 模块 | 4个接口 | Owner + Admin 权限校验 |
| Message 模块 | 2个接口 | URL 过滤（房间创建者在自己房间允许URL）+ 继承 Room 权限 |
| Batch Import | 1个接口 | Admin Only 权限校验 |

## 3. 项目文件组织结构

### 3.1 项目目录结构

```
backend/live_core_service/
├── app/
│   ├── api/
│   │   ├── deps.py                    # 依赖注入（get_current_user, get_current_user_optional）
│   │   └── endpoints/
│   │       ├── room.py                # Room模块API接口
│   │       ├── session.py             # Session模块API接口
│   │       ├── tab.py                  # Tab模块API接口
│   │       ├── message.py             # Message模块API接口
│   │       └── batch_import.py        # Batch Import模块API接口
│   ├── core/
│   │   ├── deps.py                    # 核心依赖注入函数
│   │   └── security.py                # JWT Token生成和验证
│   ├── services/
│   │   ├── base.py                    # BaseService（权限守卫函数）
│   │   ├── room.py                    # Room Service
│   │   ├── session.py                 # Session Service
│   │   ├── tab.py                     # Tab Service
│   │   ├── message.py                 # Message Service
│   │   └── batch_import.py            # Batch Import Service
│   ├── crud/
│   │   ├── room.py                    # Room CRUD
│   │   ├── session.py                 # Session CRUD
│   │   ├── tab.py                     # Tab CRUD
│   │   └── message.py                 # Message CRUD
│   ├── models/
│   │   ├── room.py                    # LiveRoom模型
│   │   ├── session.py                 # LiveSession模型
│   │   ├── tab.py                     # LiveRoomTab模型
│   │   └── message.py                 # LiveRoomMessage模型
│   └── schemas/
│       ├── room.py                    # Room Schema
│       ├── session.py                 # Session Schema
│       ├── tab.py                     # Tab Schema
│       └── message.py                 # Message Schema
```

### 3.2 必须引用的代码文件（⚠️ 重要）

在使用本提示词时，用户**必须**通过 `@` 引用以下代码文件：

#### Core层文件（必须引用）
- `@app/core/deps.py` - 依赖注入函数（需要实现 `get_current_user` 和 `get_current_user_optional`）
- `@app/core/security.py` - JWT Token生成和验证（如果存在）

#### API层文件（必须引用）
- `@app/api/endpoints/room.py` - Room模块API接口（9个接口）
- `@app/api/endpoints/session.py` - Session模块API接口（6个接口）
- `@app/api/endpoints/tab.py` - Tab模块API接口（4个接口）
- `@app/api/endpoints/message.py` - Message模块API接口（2个接口）
- `@app/api/endpoints/batch_import.py` - Batch Import模块API接口（1个接口）

#### Service层文件（必须引用）
- `@app/services/base.py` - BaseService（需要实现权限守卫函数）
- `@app/services/room.py` - Room Service（9个方法）
- `@app/services/session.py` - Session Service（6个方法）
- `@app/services/tab.py` - Tab Service（4个方法）
- `@app/services/message.py` - Message Service（2个方法）
- `@app/services/batch_import.py` - Batch Import Service（1个方法）

#### CRUD层文件（推荐引用，用于了解数据访问层）
- `@app/crud/room.py` - Room CRUD（需要了解 `get_multi` 和 `search` 方法）
- `@app/crud/session.py` - Session CRUD（可选）
- `@app/crud/message.py` - Message CRUD（可选）

#### Models和Schemas文件（可选引用）
- `@app/models/room.py` - LiveRoom模型（了解字段定义）
- `@app/schemas/room.py` - Room Schema（了解请求/响应结构）

**⚠️ 重要**：
- 如果某些文件不存在，可以只引用存在的文件
- AI 需要读取这些文件来了解现有代码的结构和内容
- 如果不引用这些文件，AI 无法知道现有代码，将无法正确执行增量改造

## 4. 内容来源（设计文档）

所有实现必须严格对齐以下设计文档，**不得自创权限逻辑或偏离语义**：

- **主设计文档**：`docs/03_系统设计/直播核心功能设计文档_v6_深度融合最终版.md`
  - 提供所有接口的原始业务逻辑定义
  - 提供数据库 Schema 和字段定义
  
- **权限设计文档**：`docs/03_系统设计/直播核心功能设计文档_v6_增加权重设计版(非独立版).md`
  - **重点章节**：
    - § 1「核心设计原则」—— 5条核心原则
    - § 2「身份模型与鉴权策略」—— Strict Auth vs Optional Auth
    - § 3「全量 API 接口改造详单」—— 22个接口的详细改造方案
    - § 4「实施层代码规范」—— 依赖注入、守卫函数、Repository 优化、API 层示例
    - § 6「完整接口权限矩阵」—— 快速参考表

**⚠️ 重要**：如权限设计文档与主设计文档存在歧义，以 **权限设计文档（v6.1）** 为最终口径。

## 5. 核心架构与编码约束（继承原有规范）

完全继承原有「Service 与 API 层代码生成提示词」中的全部规范，包括但不限于：

### 5.1 用户身份解析规范（JWT → UUID + Role）

**API 层**必须使用以下模式解析 JWT Token：

```python
from typing import Optional, Dict
from uuid import UUID
from fastapi import Depends
from app.api.deps import get_current_user, get_current_user_optional

# 场景 A：Strict Auth（写操作、敏感读操作）
current_user: Dict = Depends(get_current_user)
user_id = UUID(current_user["user_id"])  # 从JWT的user_id字段提取
role = current_user.get("role", "REGULAR")  # 从JWT的role字段提取

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
async def some_action(
    self,
    room_id: UUID,
    data: RoomUpdate,
    user_id: UUID,           # 从JWT的user_id字段提取
    role: str                # 从JWT的role字段提取
) -> Room:
    ...

# ✅ 正确：Optional Auth 场景
async def list_rooms(
    self,
    pagination: PageParams,
    user_id: Optional[UUID] = None,  # 匿名时为None
    role: Optional[str] = None       # 匿名时为None
) -> Tuple[List[Room], int]:
    ...

# ❌ 错误：不要接受ORM实体
async def some_action(
    self,
    room_id: UUID,
    data: RoomUpdate,
    current_user: User  # 禁止！
) -> Room:
    ...
```

### 5.3 分层职责（学院派核心）

- **Service 层**：
  - ✅ 负责业务逻辑与权限校验
  - ✅ 抛出自定义 Python 异常（`RoomNotFoundException`、`PermissionDeniedException` 等）
  - ✅ 调用权限守卫函数（`_check_room_visibility`、`_check_write_permission` 等）
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
| `NotFoundException` / `RoomNotFoundException` | 404 | 2001 | 房间不存在或无权访问（Private资源隐藏） |
| `PermissionDeniedException` | 403 | 3002 | 权限不足（已登录但非Owner/Admin） |
| `InvalidParameterException` | 400 | 4xxx | 参数校验失败 |
| `ActionForbiddenException` | 403 | 3003 | 业务规则禁止（如直播中禁止修改） |
| `DatabaseIntegrityException` | 400 | 4001 | 数据库唯一约束冲突 |
| 未捕获异常 | 500 | 1000 | 系统内部错误 |

**⚠️ 安全关键**：对于无权访问的 Private 资源，必须返回 **404 Not Found**，严禁返回 403，以防止恶意用户通过枚举 ID 探测资源的存在性。

## 6. 权限改造实施模式（最小幅度修改）

### 6.1 API 层改造模式

#### 模式 A：Strict Auth（强制鉴权）- 写操作

**改造前**：
```python
@router.post("", response_model=RoomResponse)
async def create_room(
    data: RoomCreate,
    service: RoomService = Depends()
):
    room = await service.create_room(data)
    return success_response(data=room)
```

**改造后**（最小幅度修改）：
```python
@router.post("", response_model=RoomResponse)
async def create_room(
    data: RoomCreate,
    current_user: Dict = Depends(get_current_user),  # ← 新增：依赖注入
    service: RoomService = Depends()
):
    # ← 新增：提取用户信息（在try之前）
    user_id = UUID(current_user["user_id"])
    role = current_user.get("role", "REGULAR")
    
    try:
        # ← 修改：传递权限参数
        room = await service.create_room(data, user_id, role)
        return success_response(data=room)
    except Exception as e:
        # 异常处理逻辑保持不变
        ...
```

#### 模式 B：Optional Auth（可选鉴权）- 读操作

**改造前**：
```python
@router.get("", response_model=PaginatedResponse)
async def list_rooms(
    pagination: PageParams = Depends(),
    service: RoomService = Depends()
):
    rooms, total = await service.list_rooms(pagination)
    return success_response(data={"items": rooms, "total": total})
```

**改造后**（最小幅度修改）：
```python
@router.get("", response_model=PaginatedResponse)
async def list_rooms(
    pagination: PageParams = Depends(),
    current_user: Optional[Dict] = Depends(get_current_user_optional),  # ← 修改：Optional依赖
    service: RoomService = Depends()
):
    # ← 新增：提取用户信息（可能为None）
    user_id = UUID(current_user["user_id"]) if current_user else None
    role = current_user.get("role") if current_user else None
    
    try:
        # ← 修改：传递权限参数（可能为None）
        rooms, total = await service.list_rooms(pagination, user_id, role)
        return success_response(data={"items": rooms, "total": total})
    except Exception as e:
        # 异常处理逻辑保持不变
        ...
```

#### 模式 C：Optional Auth + 404 伪装

**改造前**：
```python
@router.get("/{room_id}", response_model=RoomResponse)
async def get_room_detail(
    room_id: UUID,
    service: RoomService = Depends()
):
    room = await service.get_room_detail(room_id)
    return success_response(data=room)
```

**改造后**（最小幅度修改）：
```python
@router.get("/{room_id}", response_model=RoomResponse)
async def get_room_detail(
    room_id: UUID,
    current_user: Optional[Dict] = Depends(get_current_user_optional),  # ← 修改：Optional依赖
    service: RoomService = Depends()
):
    # ← 新增：提取用户信息
    user_id = UUID(current_user["user_id"]) if current_user else None
    role = current_user.get("role") if current_user else None
    
    try:
        # ← 修改：传递权限参数
        room = await service.get_room_detail(room_id, user_id, role)
        return success_response(data=room)
    except NotFoundException as e:  # ← 新增：捕获404异常
        # ← 新增：返回404（隐藏Private资源存在性）
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="Room not found")
        )
    except Exception as e:
        # 其他异常处理逻辑保持不变
        ...
```

### 6.2 Service 层改造模式

#### 模式 A：Strict Auth Service 方法

**改造前**：
```python
async def create_room(
    self,
    data: RoomCreate
) -> Room:
    """创建直播间"""
    # 业务逻辑：生成stream_key、创建记录等
    stream_key = generate_stream_key()
    room_data = {
        "id": uuid.uuid4(),
        "title": data.title,
        "stream_key": stream_key,
        # ... 其他字段
    }
    room = await self.crud.create(self.db, obj_in=room_data)
    return room
```

**改造后**（最小幅度修改）：
```python
async def create_room(
    self,
    data: RoomCreate,
    user_id: UUID,      # ← 新增：权限参数
    role: str           # ← 新增：权限参数
) -> Room:
    """创建直播间"""
    # ← 业务逻辑保持不变
    stream_key = generate_stream_key()
    room_data = {
        "id": uuid.uuid4(),
        "user_id": user_id,  # ← 新增：设置创建者（权限相关）
        "title": data.title,
        "stream_key": stream_key,
        # ... 其他字段
    }
    room = await self.crud.create(self.db, obj_in=room_data)
    return room
```

#### 模式 B：Optional Auth Service 方法 + 权限守卫

**改造前**：
```python
async def get_room_detail(
    self,
    room_id: UUID
) -> Room:
    """获取直播间详情"""
    room = await self.crud.get(self.db, id=room_id)
    if not room:
        raise RoomNotFoundException(f"房间 {room_id} 不存在")
    
    # 业务逻辑：查询tabs等
    tabs = await self.crud_tab.get_by_room(self.db, room_id=room_id)
    room.tabs = tabs
    return room
```

**改造后**（最小幅度修改）：
```python
async def get_room_detail(
    self,
    room_id: UUID,
    user_id: Optional[UUID] = None,  # ← 新增：权限参数
    role: Optional[str] = None        # ← 新增：权限参数
) -> Room:
    """获取直播间详情（支持匿名访问）"""
    room = await self.crud.get(self.db, id=room_id)
    if not room:
        raise RoomNotFoundException(f"房间 {room_id} 不存在")
    
    # ← 新增：权限校验（在业务逻辑之前）
    self._check_room_visibility(room, user_id, role)
    
    # ← 业务逻辑保持不变
    tabs = await self.crud_tab.get_by_room(self.db, room_id=room_id)
    room.tabs = tabs
    return room
```

#### 模式 C：写操作权限校验

**改造前**：
```python
async def update_room(
    self,
    room_id: UUID,
    data: RoomUpdate
) -> Room:
    """更新直播间信息"""
    room = await self.crud.get(self.db, id=room_id)
    if not room:
        raise RoomNotFoundException(f"房间 {room_id} 不存在")
    
    # 业务逻辑：检查直播状态、更新字段等
    if await self._is_room_live(room_id):
        raise ActionForbiddenException("房间正在直播中，禁止修改")
    
    updated_room = await self.crud.update(self.db, db_obj=room, obj_in=data)
    return updated_room
```

**改造后**（最小幅度修改）：
```python
async def update_room(
    self,
    room_id: UUID,
    data: RoomUpdate,
    user_id: UUID,  # ← 新增：权限参数
    role: str       # ← 新增：权限参数
) -> Room:
    """更新直播间信息"""
    room = await self.crud.get(self.db, id=room_id)
    if not room:
        raise RoomNotFoundException(f"房间 {room_id} 不存在")
    
    # ← 新增：权限校验（在业务逻辑之前）
    self._check_write_permission(room, user_id, role)
    
    # ← 业务逻辑保持不变
    if await self._is_room_live(room_id):
        raise ActionForbiddenException("房间正在直播中，禁止修改")
    
    updated_room = await self.crud.update(self.db, db_obj=room, obj_in=data)
    return updated_room
```

### 6.3 Repository 层改造模式（SQL 权限过滤）

**改造前**：
```python
async def get_multi(
    self,
    db: AsyncSession,
    page: int,
    size: int
) -> Tuple[List[LiveRoom], int]:
    """获取房间列表"""
    stmt = select(LiveRoom)
    # 分页逻辑
    stmt = stmt.offset((page - 1) * size).limit(size)
    result = await db.execute(stmt)
    rooms = result.scalars().all()
    
    # 计算总数
    count_stmt = select(func.count()).select_from(LiveRoom)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()
    
    return list(rooms), total
```

**改造后**（最小幅度修改）：
```python
async def get_multi(
    self,
    db: AsyncSession,
    page: int,
    size: int,
    user_id: Optional[UUID] = None,  # ← 新增：权限参数
    role: Optional[str] = None       # ← 新增：权限参数
) -> Tuple[List[LiveRoom], int]:
    """获取房间列表（带权限过滤）"""
    stmt = select(LiveRoom)
    
    # ← 新增：根据权限构建WHERE条件（在分页之前）
    if role in ['ADMIN', 'SUPERADMIN']:
        # 管理员：无过滤，看所有
        pass
    elif user_id:
        # 普通用户：Public OR Own
        stmt = stmt.where(
            or_(
                LiveRoom.is_private == False,
                LiveRoom.user_id == user_id
            )
        )
    else:
        # 匿名用户：Only Public
        stmt = stmt.where(LiveRoom.is_private == False)
    
    # ← 分页逻辑保持不变
    stmt = stmt.offset((page - 1) * size).limit(size)
    result = await db.execute(stmt)
    rooms = result.scalars().all()
    
    # ← 计算总数（需要应用相同的WHERE条件）
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()
    
    return list(rooms), total
```

**⚠️ 性能关键**：必须在 Repository 层通过 SQL 过滤，禁止查出所有数据在内存过滤（性能陷阱）。

## 6. 权限守卫函数实现（BaseService）

所有 Service 类应继承 `BaseService` 或独立实现以下守卫函数：

### 6.1 `_check_room_visibility`（房间可见性校验）

```python
def _check_room_visibility(
    self,
    room: LiveRoom,
    user_id: Optional[UUID],
    role: Optional[str]
) -> None:
    """
    统一的房间可见性校验逻辑
    
    Args:
        room: 直播间对象
        user_id: 当前用户的public_id（匿名时为None）
        role: 当前用户的角色（匿名时为None）
        
    Raises:
        NotFoundException: 房间不存在或无权访问（404）
    """
    # 1. 公开资源：直接通过
    if not room.is_private:
        return
    
    # 2. 私有资源且未登录：拒绝（返回404隐藏存在性）
    if not user_id:
        raise NotFoundException("Room not found")
    
    # 3. 管理员：上帝视角通过
    if role in ['ADMIN', 'SUPERADMIN']:
        # ✅ 记录Admin查看Private资源的审计日志（INFO级别）
        if room.user_id != user_id:
            logger.info(
                f"Admin查看Private资源: admin={user_id}, role={role}, "
                f"room_id={room.id}, owner={room.user_id}"
            )
        return
    
    # 4. 资源创建者：通过
    # 注意：room.user_id存储的就是创建者的public_id
    if room.user_id == user_id:
        return
    
    # 5. 其他已登录用户：拒绝（返回404隐藏存在性）
    raise NotFoundException("Room not found")
```

### 7.2 `_check_write_permission`（写操作权限校验）

```python
def _check_write_permission(
    self,
    room: LiveRoom,
    user_id: UUID,
    role: str
) -> None:
    """
    写操作权限校验（修改/删除）
    
    Args:
        room: 直播间对象
        user_id: 当前用户的public_id
        role: 当前用户的角色
        
    Raises:
        PermissionDeniedException: 无权修改（403）
    """
    # 管理员：上帝视角通过
    if role in ['ADMIN', 'SUPERADMIN']:
        return
    
    # 资源创建者：通过
    if room.user_id == user_id:
        return
    
    # 其他用户：拒绝（返回403，因为已登录）
    raise PermissionDeniedException(
        "You don't have permission to modify this room"
    )
```

### 7.3 `_check_admin_role`（管理员角色校验）

```python
def _check_admin_role(self, role: str) -> None:
    """
    管理员角色校验（用于Batch Import等纯后台管理功能）
    
    ⚠️ 注意：Tab管理功能不使用此方法，改用 _check_tab_management_permission
    
    Args:
        role: 当前用户的角色
        
    Raises:
        PermissionDeniedException: 非Admin用户（403）
    """
    if role not in ['ADMIN', 'SUPERADMIN']:
        raise PermissionDeniedException("Admin role required")
```

### 7.4 `_validate_message_content`（留言内容校验）

```python
def _validate_message_content(
    self,
    content: str,
    role: str,
    user_id: UUID,
    room: LiveRoom  # ← 新增参数：用于判断是否为房间创建者
) -> None:
    """
    留言内容校验（房间创建者在自己房间允许URL）
    
    Args:
        content: 留言内容
        role: 当前用户的角色
        user_id: 当前用户的public_id
        room: 直播间对象（用于判断是否为创建者）
        
    Raises:
        InvalidParameterException: 内容校验失败（400）
    """
    # 1. 内容长度校验
    if not content or not content.strip():
        raise InvalidParameterException("留言内容不能为空")
    
    if len(content) > 1000:
        raise InvalidParameterException("留言内容不能超过1000字符")
    
    # 2. URL过滤逻辑
    content_lower = content.lower()
    has_url = 'http://' in content_lower or 'https://' in content_lower
    
    if has_url:
        # Admin：允许任意内容
        if role in ['ADMIN', 'SUPERADMIN']:
            return
        
        # 房间创建者：允许在自己房间发送URL
        if room.user_id == user_id:
            logger.info(
                f"房间创建者发送URL留言: user_id={user_id}, room_id={room.id}, "
                f"room_owner={room.user_id}"
            )
            return
        
        # 其他用户：禁止URL
        logger.warning(
            f"非管理员/创建者尝试发送URL留言: user_id={user_id}, role={role}, "
            f"room_id={room.id}, room_owner={room.user_id}"
        )
        raise InvalidParameterException(
            code=4004,
            message="非管理员用户不允许发送包含 URL 的留言"
        )
```

### 7.5 `_check_tab_management_permission`（Tab管理权限校验）

```python
def _check_tab_management_permission(
    self,
    room: LiveRoom,
    user_id: UUID,
    role: str
) -> None:
    """
    检查Tab管理权限（创建者或Admin）
    
    Args:
        room: 直播间对象
        user_id: 当前用户的public_id
        role: 当前用户的角色
        
    Raises:
        PermissionDeniedException: 无权管理Tab（403）
    """
    # Admin：可以管理所有房间
    if role in ['ADMIN', 'SUPERADMIN']:
        # ✅ 记录Admin管理他人房间Tab的审计日志
        if room.user_id != user_id:
            logger.info(
                f"Admin管理他人房间Tab: admin={user_id}, role={role}, "
                f"room_id={room.id}, room_owner={room.user_id}"
            )
        return
    
    # Regular：只能管理自己创建的房间
    if room.user_id == user_id:
        logger.info(f"房间创建者管理Tab: user_id={user_id}, room_id={room.id}")
        return
    
    # 其他情况：拒绝
    logger.warning(
        f"非创建者/Admin尝试管理Tab: user_id={user_id}, role={role}, "
        f"room_id={room.id}, room_owner={room.user_id}"
    )
    raise PermissionDeniedException("您只能管理自己创建的房间的Tab配置")
```

## 8. 依赖注入实现（app/api/deps.py）

### 8.1 Strict Auth 依赖（强制鉴权）

```python
async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict:
    """
    强制鉴权依赖注入
    
    Returns:
        用户信息字典 {"user_id": str(UUID), "role": str, "username": str}
        
    Raises:
        HTTPException(401): Token缺失或无效
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = verify_token_service(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
```

### 8.2 Optional Auth 依赖（可选鉴权）

```python
async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme)
) -> Optional[Dict]:
    """
    可选鉴权依赖注入
    
    Returns:
        - None: 匿名用户（无Token）
        - Dict: 用户信息字典（有有效Token）
        
    Raises:
        HTTPException(401): Token无效或过期（但不能降级为匿名）
    """
    # 场景 A: 无 Token → 返回 None，视为匿名用户
    if not token:
        return None
    
    # 场景 B: 有 Token → 必须验证
    user = verify_token_service(token)
    if not user:
        # 场景 C: Token 过期/伪造 → 必须报错！
        # 严禁降级为匿名，否则已登录用户看不到自己的私有资源
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
```

**⚠️ 关键约束**：Token 无效时必须报 401，严禁降级为匿名用户。否则已登录用户在 Token 过期时会莫名其妙看不到自己的私有房间，导致前端状态错乱。

## 9. 具体接口改造清单（按模块）

### 9.1 Room 模块（9个接口）

| 接口 | 路径 | 方法 | Auth模式 | 改造要点 |
|------|------|------|---------|---------|
| 创建房间 | `/api/v1/rooms` | POST | Strict | 增加 `user_id`、`role` 参数，设置 `room.user_id` |
| 房间列表 | `/api/v1/rooms` | GET | Optional | Repository 层 SQL 过滤（Admin/Regular/Anonymous），管理后台可选 owner-only 视图（Regular 仅看 Own，Admin 看全部） |
| 房间详情 | `/api/v1/rooms/{id}` | GET | Optional | 调用 `_check_room_visibility` |
| 更新房间 | `/api/v1/rooms/{id}` | PATCH | Strict | 调用 `_check_write_permission` |
| 删除房间 | `/api/v1/rooms/{id}` | DELETE | Strict | 调用 `_check_write_permission` |
| 上传封面 | `/api/v1/rooms/{id}/cover` | POST | Strict | 调用 `_check_write_permission` |
| 分会场列表 | `/api/v1/rooms/{id}/sub-venues` | GET | Optional | 先检查主会场权限，再过滤子会场 |
| 推流密钥 | `/api/v1/rooms/{id}/stream_key` | GET | Strict | 调用 `_check_write_permission`（严禁匿名） |
| 搜索房间 | `/api/v1/rooms/search` | GET | Optional | 复用列表接口的 SQL 过滤逻辑 |

### 9.2 Session 模块（6个接口）

| 接口 | 路径 | 方法 | Auth模式 | 改造要点 |
|------|------|------|---------|---------|
| 创建场次 | `/api/v1/rooms/{id}/sessions` | POST | Strict | 检查 Room 写权限 |
| 场次列表 | `/api/v1/rooms/{id}/sessions` | GET | Optional | 检查 Room 可见性 |
| 场次详情 | `/api/v1/sessions/{id}` | GET | Optional | 通过 Session 关联 Room，检查 Room 可见性 |
| 更新场次 | `/api/v1/sessions/{id}` | PATCH | Strict | 通过 Session 关联 Room，检查 Room 写权限 |
| 删除场次 | `/api/v1/sessions/{id}` | DELETE | Strict | 通过 Session 关联 Room，检查 Room 写权限 |
| Import场次 | `/api/v1/rooms/{id}/sessions/import` | POST | Strict | 检查 Room 写权限 |

**⚠️ 设计约束**：Session 实体不单独维护 `is_private` 字段，它**强制继承**所属 Room 的可见性。

### 9.3 Tab 模块（4个接口）- Owner + Admin

| 接口 | 路径 | 方法 | Auth模式 | 改造要点 |
|------|------|------|---------|---------|
| Tab列表 | `/api/v1/admin/rooms/{id}/tabs` | GET | Strict | 先查询room，调用 `_check_tab_management_permission` |
| 创建Tab | `/api/v1/admin/rooms/{id}/tabs` | POST | Strict | 先查询room，调用 `_check_tab_management_permission` |
| 更新Tab | `/api/v1/admin/rooms/{id}/tabs/{tid}` | PATCH | Strict | 先查询tab获取room_id，再查询room，调用 `_check_tab_management_permission` |
| 删除Tab | `/api/v1/admin/rooms/{id}/tabs/{tid}` | DELETE | Strict | 先查询tab获取room_id，再查询room，调用 `_check_tab_management_permission` |

**⚠️ 权限说明**：
- Tab 内容对所有用户可见（继承 Room 的 `is_private` 可见性）
- Tab 管理功能（编辑/删除）仅对房间创建者和 Admin 可见

### 9.4 Message 模块（2个接口）

| 接口 | 路径 | 方法 | Auth模式 | 改造要点 |
|------|------|------|---------|---------|
| 发送留言 | `/api/v1/rooms/{id}/messages` | POST | Strict | 先查询room，调用 `_validate_message_content(content, role, user_id, room)`（URL过滤，房间创建者在自己房间允许URL） |
| 留言列表 | `/api/v1/rooms/{id}/messages` | GET | Optional | 检查 Room 可见性（继承 Room 权限） |

### 9.5 Batch Import 模块（1个接口）

| 接口 | 路径 | 方法 | Auth模式 | 改造要点 |
|------|------|------|---------|---------|
| 批量导入 | `/api/v1/rooms/import/batch` | POST | Strict | 调用 `_check_admin_role`（Admin Only） |

## 10. 代码质量检查清单（权限增量）

在生成或修改代码后，请自检：

### 10.1 最小幅度修改检查

- [ ] **未删除或重命名**任何现有 Service / API 类与函数
- [ ] **未修改**任何业务逻辑执行流程（只增加了权限校验调用）
- [ ] **未改变**任何方法的返回值结构（除非设计文档明确要求）
- [ ] 所有新增的权限参数都使用了合适的类型（`UUID` / `Optional[UUID]`、`str` / `Optional[str]`）

### 10.2 权限逻辑检查

- [ ] **确定Auth模式**：该接口是 Strict 还是 Optional？
- [ ] **API层依赖注入**：使用 `get_current_user` 还是 `get_current_user_optional`？
- [ ] **Service方法签名**：`user_id` 和 `role` 参数类型是否正确？
- [ ] **权限守卫调用**：是否调用了 `_check_room_visibility` 或 `_check_write_permission`？
- [ ] **Admin特权处理**：Admin 角色是否正确绕过了 `is_private` 限制？
- [ ] **Repository层过滤**：列表查询是否在 SQL 层面应用了权限过滤？

### 10.3 字段一致性检查

- [ ] 使用 `is_private` 布尔字段（而非 `visibility` 枚举）
- [ ] 使用 `user_id` 存储 `public_id`（而非 `owner_public_id`）
- [ ] JWT 中使用 `user_id` 字段提取 `public_id`（而非 `sub`）

### 10.4 错误码正确性检查

- [ ] 无 Token 且需要 Strict Auth → 401
- [ ] Token 无效 → 401
- [ ] 权限不足（已登录但非 Owner/Admin）→ 403
- [ ] Private 资源但无权访问 → **404**（而非 403，安全关键）
- [ ] Token 无效时 Optional Auth → 401（严禁降级为匿名）

### 10.5 日志审计检查

- [ ] 敏感操作（如 Admin 查看 Private 资源）是否记录审计日志？
- [ ] 所有权限拒绝操作是否记录了警告日志？

### 10.6 性能检查

- [ ] 列表查询的权限过滤是否在 Repository 层通过 SQL 实现？
- [ ] 是否避免了在内存中过滤大量数据？

## 11. 覆盖完整性检查（⚠️ 必须验证）

在使用本提示词进行代码改造前，请确认以下覆盖完整性：

### 11.1 API接口覆盖检查（22个接口）

根据权限设计文档 §3 和 §6.2，需要改造的接口如下：

| 模块 | 接口数量 | 设计文档要求 | 提示词文档覆盖 | 状态 |
|------|---------|------------|--------------|------|
| Room 模块 | 9个 | 9个（§3.1） | 9个（§9.1） | ✅ 完全覆盖 |
| Session 模块 | 6个 | 6个（§3.2） | 6个（§9.2） | ✅ 完全覆盖 |
| Tab 模块 | 4个 | 4个（§3.3） | 4个（§9.3） | ✅ 完全覆盖 |
| Message 模块 | 2个 | 2个（§3.4） | 2个（§9.4） | ✅ 完全覆盖 |
| Batch Import | 1个 | 1个（§3.5） | 1个（§9.5） | ✅ 完全覆盖 |
| **总计** | **22个** | **22个** | **22个** | **✅ 100%覆盖** |

**详细接口清单**（对照权限设计文档 §6.2 接口权限矩阵）：

#### Room 模块（9个接口）
1. ✅ 创建房间 - `POST /api/v1/rooms`（§9.1）
2. ✅ 房间列表 - `GET /api/v1/rooms`（§9.1）
3. ✅ 房间详情 - `GET /api/v1/rooms/{id}`（§9.1）
4. ✅ 更新房间 - `PATCH /api/v1/rooms/{id}`（§9.1）
5. ✅ 删除房间 - `DELETE /api/v1/rooms/{id}`（§9.1）
6. ✅ 上传封面 - `POST /api/v1/rooms/{id}/cover`（§9.1）
7. ✅ 分会场列表 - `GET /api/v1/rooms/{id}/sub-venues`（§9.1）
8. ✅ 推流密钥 - `GET /api/v1/rooms/{id}/stream_key`（§9.1）
9. ✅ 搜索房间 - `GET /api/v1/rooms/search`（§9.1）

#### Session 模块（6个接口）
10. ✅ 创建场次 - `POST /api/v1/rooms/{id}/sessions`（§9.2）
11. ✅ 场次列表 - `GET /api/v1/rooms/{id}/sessions`（§9.2）
12. ✅ 场次详情 - `GET /api/v1/sessions/{id}`（§9.2）
13. ✅ 更新场次 - `PATCH /api/v1/sessions/{id}`（§9.2）
14. ✅ 删除场次 - `DELETE /api/v1/sessions/{id}`（§9.2）
15. ✅ Import场次 - `POST /api/v1/rooms/{id}/sessions/import`（§9.2）

#### Tab 模块（4个接口）
16. ✅ Tab列表 - `GET /api/v1/admin/rooms/{id}/tabs`（§9.3）
17. ✅ 创建Tab - `POST /api/v1/admin/rooms/{id}/tabs`（§9.3）
18. ✅ 更新Tab - `PATCH /api/v1/admin/rooms/{id}/tabs/{tid}`（§9.3）
19. ✅ 删除Tab - `DELETE /api/v1/admin/rooms/{id}/tabs/{tid}`（§9.3）

#### Message 模块（2个接口）
20. ✅ 发送留言 - `POST /api/v1/rooms/{id}/messages`（§9.4）
21. ✅ 留言列表 - `GET /api/v1/rooms/{id}/messages`（§9.4）

#### Batch Import 模块（1个接口）
22. ✅ 批量导入 - `POST /api/v1/rooms/import/batch`（§9.5）

### 11.2 Service方法覆盖检查

所有22个接口对应的Service方法都已覆盖：

| Service方法 | 对应接口 | 提示词文档覆盖 | 状态 |
|------------|---------|--------------|------|
| Room Service | 9个方法 | §9.1 + §6.2 | ✅ 完全覆盖 |
| Session Service | 6个方法 | §9.2 + §6.2 | ✅ 完全覆盖 |
| Tab Service | 4个方法 | §9.3 + §6.2 | ✅ 完全覆盖 |
| Message Service | 2个方法 | §9.4 + §6.2 | ✅ 完全覆盖 |
| Batch Import Service | 1个方法 | §9.5 + §6.2 | ✅ 完全覆盖 |

**详细Service方法清单**：

#### Room Service（9个方法）
1. ✅ `create_room` - 创建房间（§9.1）
2. ✅ `list_rooms` - 房间列表（§9.1）
3. ✅ `get_room_detail` - 房间详情（§9.1）
4. ✅ `update_room` - 更新房间（§9.1）
5. ✅ `delete_room` - 删除房间（§9.1）
6. ✅ `upload_cover` - 上传封面（§9.1）
7. ✅ `list_sub_venues` - 分会场列表（§9.1）
8. ✅ `get_stream_key` - 推流密钥（§9.1）
9. ✅ `search_rooms` - 搜索房间（§9.1）

#### Session Service（6个方法）
10. ✅ `create_session` - 创建场次（§9.2）
11. ✅ `list_room_sessions` - 场次列表（§9.2）
12. ✅ `get_session_detail` - 场次详情（§9.2）
13. ✅ `update_session` - 更新场次（§9.2）
14. ✅ `delete_session` - 删除场次（§9.2）
15. ✅ `import_create_session` - Import场次（§9.2）

#### Tab Service（4个方法）
16. ✅ `list_tabs_for_admin` - Tab列表（§9.3）
17. ✅ `create_tab` - 创建Tab（§9.3）
18. ✅ `update_tab` - 更新Tab（§9.3）
19. ✅ `delete_tab` - 删除Tab（§9.3）

#### Message Service（2个方法）
20. ✅ `create_message` - 发送留言（§9.4）
21. ✅ `list_messages` - 留言列表（§9.4）

#### Batch Import Service（1个方法）
22. ✅ `batch_import` - 批量导入（§9.5）

### 11.3 CRUD方法覆盖检查

根据权限设计文档，CRUD层需要改造的方法：

| CRUD方法 | 设计文档要求 | 提示词文档覆盖 | 状态 |
|---------|------------|--------------|------|
| Room CRUD `get_multi` | 需要SQL权限过滤 | ✅ 覆盖（§7.1） | ✅ 完全覆盖 |
| Room CRUD `search` | 需要SQL权限过滤 | ✅ 覆盖（§7.1） | ✅ 完全覆盖 |
| Room CRUD `get` | 不在此层过滤 | ✅ 已说明（§2.2） | ✅ 正确说明 |
| Session CRUD `get_multi_by_room` | 不在此层过滤 | ✅ 已说明（§7.2） | ✅ 正确说明 |
| Message CRUD `get_multi_by_room` | 不在此层过滤 | ✅ 已说明（§7.3） | ✅ 正确说明 |

**结论**：✅ **100%覆盖所有需要改造的接口、Service方法和CRUD方法**

---

## 12. 实施步骤建议

1. **第一步：实现依赖注入函数**
   - 在 `app/core/deps.py` 中实现 `get_current_user` 和 `get_current_user_optional`
   - 实现 `verify_token_service` 函数

2. **第二步：实现权限守卫函数**
   - 在 `app/services/base.py` 中实现 `_check_room_visibility`、`_check_write_permission`、`_check_admin_role`、`_check_tab_management_permission`、`_validate_message_content`
   - 所有 Service 类继承 `BaseService` 或独立实现这些方法

3. **第三步：改造 Repository 层**
   - 为列表查询方法增加 `user_id`、`role` 参数
   - 在 SQL 查询中根据权限构建不同的 WHERE 条件

4. **第四步：改造 Service 层**
   - 为所有方法增加权限参数（`user_id`、`role`）
   - 在业务逻辑之前调用权限守卫函数
   - 保持所有业务逻辑不变

5. **第五步：改造 API 层**
   - 修改依赖注入（Strict / Optional）
   - 提取用户信息（在 `try` 之前）
   - 传递权限参数给 Service 层
   - 增加 404 异常处理（Optional Auth 场景）

6. **第六步：测试验证**
   - 匿名访问 Public 资源 → 成功
   - 匿名访问 Private 资源 → 404
   - Owner 访问自己的 Private 资源 → 成功
   - 非 Owner 访问他人 Private 资源 → 404
   - Admin 访问任意 Private 资源 → 成功
   - Token 过期访问 → 401
   - 写操作无 Token → 401
   - 写操作非 Owner/Admin → 403
   - **Tab 管理**：Owner 可以管理自己房间的 Tab，非 Owner 无法管理他人房间的 Tab → 403
   - **Tab 管理**：Admin 可以管理所有房间的 Tab → 成功
   - **留言 URL**：房间创建者在自己房间可以发送包含 URL 的留言 → 成功
   - **留言 URL**：非创建者在他人房间无法发送包含 URL 的留言 → 400

---

## 13. 交付物（最终输出）

根据本提示词，在**已引用的现有代码**基础上，以最小幅度修改的方式完成所有接口的权限管理增量改造。

### 13.1 输出要求

1. **修改现有代码文件**：
   - 直接修改用户通过 `@` 引用的代码文件
   - 为现有API接口添加权限依赖注入
   - 为现有Service方法添加权限参数和权限守卫调用
   - 保持现有业务逻辑不变

2. **新增代码**：
   - 在 `app/core/deps.py` 中实现依赖注入函数（如果不存在）
   - 在 `app/services/base.py` 中实现权限守卫函数（如果不存在）

3. **不删除任何内容**：
   - 严禁删除或重命名任何现有方法
   - 严禁删除任何现有业务逻辑

---

**请根据本提示词，在已引用的现有代码基础上，以最小幅度修改的方式完成所有接口的权限管理增量改造。**
