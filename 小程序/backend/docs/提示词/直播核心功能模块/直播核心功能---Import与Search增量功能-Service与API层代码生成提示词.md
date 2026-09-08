# LiveCore Service - Import与Search增量功能 Service 与 API 层代码生成提示词

## 1. 角色定义

你是一名精通"学院派"架构（Clean Architecture）的资深 Python 后端架构师，专门负责实现业务逻辑层（Service Layer）和 API 接口层（Endpoint Layer）。你严格遵循分层解耦、异常处理、权限验证的最佳实践。

## 2. 任务目标

为 LiveCore Service 的"Import与Search增量功能"生成完整的 Service 层和 API 层代码，包括：
1. **Import Session**：导入创建会话功能
2. **Search**：搜索直播间功能
3. **Batch Import**：批量导入直播间和会话功能

## 3. 内容来源

基于《LiveCore Service - Import 与 Search 增量功能设计文档 (V5.0)》的技术规范。

## 4. 核心架构约束（最高优先级）

### 4.1 统一的用户身份解析规范（关键修复）

**🚨 API 层用户提取规范（JWT→UUID）**

`current_user` **永远是一个 JWT payload `dict`**，而不是 ORM `User` 模型。

API 层**必须**使用以下模式解析：

```python
from fastapi import Depends
from typing import Dict
from uuid import UUID

# API 层依赖注入
current_user: Dict = Depends(get_current_user)

# 提取用户公开标识（从 JWT 的 public_id 字段）
public_id = UUID(current_user.get("public_id"))
role_str = current_user.get("role", "REGULAR").upper()

# 注意：本项目使用 public_id 作为用户的对外标识
# JWT payload 中的 public_id 对应 users 表的 public_id 字段
```

**🚨 Service 层用户参数规范**

Service 层方法**不得**接受实体类 `User`，**必须**统一为：

```python
async def some_action(
    self,
    public_id: UUID,
    room_id: UUID,
    ...
):
    """
    业务逻辑方法
    
    参数：
    - public_id: 当前用户的公开标识（从 JWT 提取）
    - room_id: 目标资源 ID
    """
```

### 4.2 Service 层职责（学院派核心）

**必须遵守的规则**：
1. ✅ **必须**负责所有业务逻辑（权限检查、规则校验）
2. ✅ **必须**抛出自定义 Python 异常（如 `PermissionDeniedException`）
3. ❌ **严禁**抛出 `HTTPException`
4. ❌ **严禁**控制事务（`db.commit()` / `db.rollback()`）
5. ✅ **必须**调用一个或多个 CRUD 函数来组合业务
6. ✅ **必须**在 `try` 之前提取日志变量（安全异步异常处理）

### 4.3 API 层职责（学院派核心）

**必须遵守的规则**：
1. ✅ **必须**使用 `try...except` 块捕获所有异常
2. ✅ **必须**将自定义异常转换为 `JSONResponse`
3. ✅ **必须**在 `try` 之前提取日志变量
4. ✅ **必须**使用 `success_response()` 和 `error_response()` 构建响应
5. ❌ **严禁**在 API 层执行业务逻辑或权限检查
6. ✅ **必须**依赖 `Depends(get_current_user)` 获取 JWT payload `Dict`

### 4.4 异常处理流程（学院派三层模式）

**完整调用链**：

```
API 层 (try...except)
  ↓ 调用
Service 层 (raise 自定义异常)
  ↓ 调用
CRUD 层 (try...except, raise DatabaseException)
```

**示例代码**：

**Service 层**：
```python
async def import_create_session(self, room_id: UUID, public_id: UUID, session_in: dict):
    # 业务校验
    room = await crud_room.get(self.db, id=room_id)
    if not room:
        raise RoomNotFoundException(f"房间 {room_id} 不存在")
    
    if room.user_id != public_id:
        raise PermissionDeniedException("您无权在此房间导入会话")
    
    # 调用 CRUD（不捕获异常，任其上浮）
    return await crud_session.create(self.db, obj_in=session_data)
```

**API 层**：
```python
@router.post("/rooms/{room_id}/sessions/import")
async def import_session(
    room_id: UUID,
    payload: SessionImportCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    # 提取日志变量（从 JWT 提取用户公开标识）
    public_id = UUID(current_user.get("public_id"))
    
    try:
        service = SessionImportService(db)
        session = await service.import_create_session(
            room_id=room_id,
            public_id=public_id,
            session_in=payload.dict()
        )
        return success_response(data=session)
    
    except RoomNotFoundException as e:
        logger.warning(f"资源未找到: room_id={room_id}, error={e}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="房间不存在")
        )
    
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: public_id={public_id}, room_id={room_id}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3002, message="权限不足")
        )
    
    except DatabaseIntegrityException as e:
        logger.warning(f"数据冲突: {e.message}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message="数据冲突或参数错误")
        )
    
    except Exception as e:
        logger.error(f"未知错误: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=error_response(code=1000, message="服务器内部错误")
        )
```

### 4.5 路由定义规范

**关键规则**：
1. ✅ **必须**在 `app/api/v1/endpoints/xxx.py` 中定义 `APIRouter(tags=["..."])`
2. ❌ **严禁**在 Router 定义时指定 `prefix`
3. ✅ `prefix` **必须**在 `app/api/v1/api.py` 的 `api_router.include_router(...)` 中统一指定

**端点路径规则**：
- 集合端点：`path=""`（如 `POST /rooms/{room_id}/sessions/import`）
- 资源端点：`path="/{item_id}"`（如 `GET /sessions/{session_id}`）
- 嵌套资源：`path="/{item_id}/sub_items"`

**示例**：
```python
# app/api/v1/endpoints/session_import.py
from fastapi import APIRouter

router = APIRouter(tags=["Session Import"])  # ❌ 不要写 prefix="/rooms"

@router.post("/{room_id}/sessions/import")  # ✅ 完整路径（相对于 prefix）
async def import_session(...):
    pass

# app/api/v1/api.py
from app.api.v1.endpoints import session_import

api_router = APIRouter()
api_router.include_router(
    session_import.router,
    prefix="/rooms",  # ✅ 在这里统一指定 prefix
    tags=["Session Import"]
)
```

## 5. 具体功能实现要求

### 5.1 Import Session 功能

#### Service 层：`SessionImportService`

**文件路径**：`app/services/session_import.py`

**类定义**：
```python
class SessionImportService:
    """导入会话服务（学院派实现）"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def import_create_session(
        self, 
        room_id: UUID, 
        public_id: UUID, 
        session_in: dict
    ) -> LiveSession:
        """
        导入创建会话（业务逻辑层）
        
        职责：
        1. 验证房间存在性
        2. 验证用户权限
        3. 验证参数合法性
        4. 调用 CRUD 层创建会话
        
        抛出异常：
        - RoomNotFoundException: 房间不存在
        - PermissionDeniedException: 用户无权操作
        - InvalidParameterException: 参数不合法
        """
```

**实现要点**：
1. 调用 `crud_room.get(self.db, id=room_id)` 验证房间存在性
2. 验证权限：`if room.user_id != public_id: raise PermissionDeniedException(...)`
3. 验证参数：
   - `status` 必须为 `'finished'` 或 `'ready'`
   - `playback_url` 必须非空
4. 构建 `session_data` 字典（包含 `playback_url`）
5. 调用 `crud_session.create(self.db, obj_in=session_data)`
6. 同时调用 `crud_session_statistics.create()` 创建统计记录
7. 记录 `logger.info()` 日志

#### API 层：`POST /api/v1/rooms/{room_id}/sessions/import`

**文件路径**：`app/api/v1/endpoints/session_import.py`

**Pydantic Schema**：
```python
class SessionImportCreate(BaseModel):
    """导入创建会话的请求体"""
    start_time: datetime = Field(..., description="会话开始时间（必填）")
    end_time: Optional[datetime] = Field(None, description="会话结束时间")
    status: str = Field(..., description="会话状态，限制为 'finished' 或 'ready'")
    playback_url: str = Field(..., max_length=1024, description="回放地址（必填）")
    title: Optional[str] = Field(None, max_length=100, description="会话标题")
    description: Optional[str] = Field(None, description="会话描述")
    
    @validator('status')
    def validate_status(cls, v):
        if v not in ['finished', 'ready']:
            raise ValueError("导入会话的 status 只能为 'finished' 或 'ready'")
        return v
    
    @validator('playback_url')
    def validate_playback_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError("playback_url 必须以 http:// 或 https:// 开头")
        return v
```

**端点实现要点**：
1. 依赖注入：`current_user: Dict = Depends(get_current_user)`
2. 提取用户信息：`public_id = UUID(current_user.get("public_id"))`
3. 使用完整的 `try...except` 块捕获以下异常：
   - `RoomNotFoundException` → 404/2001
   - `PermissionDeniedException` → 403/3002
   - `InvalidParameterException` → 400/4001
   - `DatabaseIntegrityException` → 400/4001
   - `Exception` → 500/1000
4. 成功返回：`success_response(data=session)`

---

### 5.2 Search 功能

#### Service 层：`RoomService`（扩展现有服务）

**文件路径**：`app/services/room.py`

**新增方法**：
```python
async def search_rooms(
    self, 
    public_id: UUID,
    q: Optional[str] = None,
    page: int = 1,
    size: int = 10,
    sort: Optional[str] = None
) -> dict:
    """
    搜索直播间（业务逻辑层）
    
    职责：
    1. 构建搜索条件
    2. 调用 CRUD 层查询
    
    返回：
    - {"total": int, "page": int, "size": int, "items": [Room]}
    """
```

**实现要点**：
1. 构建 `search_filters = {}` 字典
2. 若 `q` 非空：
   - 使用正则表达式判断是否为 UUID 格式：`^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$`
   - UUID 格式：`search_filters['id_or_title'] = ('id', q)`
   - 非 UUID 格式：`search_filters['id_or_title'] = ('title', f'%{q}%')`
3. 调用 `crud_room.list_with_search(self.db, filters=search_filters, page=page, size=size, sort=sort)`
4. 记录 `logger.info()` 日志

#### API 层：`GET /api/v1/rooms?q=<keyword>`（扩展现有端点）

**文件路径**：`app/api/v1/endpoints/rooms.py`

**修改现有端点**：
```python
@router.get("")
async def list_rooms(
    q: Optional[str] = Query(None, max_length=100, description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    sort: Optional[str] = Query(None, description="排序字段，格式为 field:direction，例如 created_at:desc"),
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    获取直播间列表（支持搜索）
    
    参数：
    - q: 搜索关键词（可选），支持按 ID 或标题搜索
    - page: 页码
    - size: 每页数量
    - sort: 排序字段（可选），格式为 field:direction
    """
```

**实现要点**：
1. 提取用户信息：`public_id = UUID(current_user.get("public_id"))`
2. 调用 `room_service.search_rooms(public_id=public_id, q=q, page=page, size=size, sort=sort)`
3. 捕获异常：
   - `InvalidParameterException` → 400/4001
   - `Exception` → 500/1000
4. 成功返回：`success_response(data={"total": ..., "page": ..., "size": ..., "items": ...})`

---

### 5.3 Batch Import 功能

#### Service 层：`BatchImportService`

**文件路径**：`app/services/batch_import.py`

**类定义**：
```python
class BatchImportService:
    """批量导入服务（学院派实现）"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def import_from_file(
        self,
        public_id: UUID,
        file: UploadFile,
        mode: str = 'dry_run',
        encoding_hint: Optional[str] = None
    ) -> dict:
        """
        从 CSV/Excel 文件批量导入
        
        职责：
        1. 读取并解析文件
        2. 验证必需列
        3. 逐行处理（行级事务隔离）
        4. 根据 mode 决定是否提交
        
        返回：
        - {"total_rows": int, "success_count": int, "failed_count": int, "items": []}
        """
```

**实现要点**：
1. 读取文件：`content = await file.read()`
2. 自动探测编码：`utf-8-sig → utf-8 → gbk → chardet`
3. 解析 CSV：使用 `csv.DictReader(io.StringIO(text))`，对表头统一做小写与去空格处理，并在进入必需列校验前完成**别名映射**（例如：`标题 → room_title`，`播放url（以及历史表头“播放url1”）→ playback_url`，`封面图片 → cover_url`），得到逻辑字段集合
4. 在逻辑字段层面验证必需列：`{'room_title', 'playback_url'}.issubset(columns)`，若缺失则抛出 `InvalidParameterException`（错误信息保持为 `"CSV 文件缺少必需列：room_title, playback_url"`，方便与设计文档对齐）
5. 逐行处理：调用 `_process_row()` 方法
6. 记录结果：`{"row_no": int, "room_id": str, "session_id": str, "status": "success"|"failed", "error": str}`
7. 返回导入报告

**辅助方法**：
```python
async def _process_row(
    self,
    public_id: UUID,
    row_no: int,
    row: dict,
    mode: str
) -> dict:
    """处理单行数据（行级事务）"""
```

**辅助函数**：
```python
def _detect_encoding(self, content: bytes, hint: Optional[str]) -> str:
    """自动探测文件编码"""

def _generate_stream_key(self) -> str:
    """生成唯一的推流密钥"""
    import secrets
    return f"sk_live_{secrets.token_hex(16)}"
```

#### API 层：`POST /api/v1/rooms/import/batch`

**文件路径**：`app/api/v1/endpoints/batch_import.py`

**端点定义**：
```python
@router.post("/import/batch")
async def batch_import_rooms(
    file: UploadFile = File(...),
    mode: str = Query("dry_run", regex="^(dry_run|apply)$"),
    encoding_hint: Optional[str] = Query(None, regex="^(utf-8-sig|utf-8|gbk)$"),
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    批量导入直播间和会话
    
    参数：
    - file: CSV 或 Excel 文件
    - mode: dry_run（仅校验）或 apply（实际写库）
    - encoding_hint: 文件编码提示（可选）
    """
```

**实现要点**：
1. 提取用户信息：`public_id = UUID(current_user.get("public_id"))`
2. 验证文件类型：`if not file.filename.endswith(('.csv', '.xlsx')): raise InvalidParameterException(...)`
3. 调用 `batch_import_service.import_from_file(public_id, file, mode, encoding_hint)`
4. 捕获异常：
   - `InvalidParameterException` → 400/4001 或 400/4002
   - `Exception` → 500/1000
5. 成功返回：`success_response(data=import_report)`

---

## 6. 自定义异常类定义

**必需的异常类**（在 `app/core/exceptions.py` 中定义）：

```python
class RoomNotFoundException(Exception):
    """房间不存在"""
    def __init__(self, message: str = "房间不存在"):
        self.message = message
        super().__init__(self.message)

class PermissionDeniedException(Exception):
    """权限不足"""
    def __init__(self, message: str = "权限不足"):
        self.message = message
        super().__init__(self.message)

class InvalidParameterException(Exception):
    """参数非法"""
    def __init__(self, message: str = "参数非法", code: int = 4001):
        self.message = message
        self.code = code
        super().__init__(self.message)

class DatabaseIntegrityException(Exception):
    """数据库完整性错误"""
    def __init__(self, message: str = "数据库完整性冲突"):
        self.message = message
        super().__init__(self.message)

class DatabaseOperationException(Exception):
    """数据库操作错误"""
    def __init__(self, message: str = "数据库操作失败"):
        self.message = message
        super().__init__(self.message)
```

---

## 7. 响应构建辅助函数

**必需的辅助函数**（在 `app/core/response.py` 中定义）：

```python
from datetime import datetime
from typing import Any

def success_response(data: Any = None, message: str = "success", code: int = 200) -> dict:
    """构建成功响应"""
    return {
        "code": code,
        "message": message,
        "data": data,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

def error_response(code: int, message: str, data: Any = None) -> dict:
    """构建错误响应"""
    return {
        "code": code,
        "message": message,
        "data": data,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
```

---

## 8. 路由注册

**在 `app/api/v1/api.py` 中注册**：

```python
from app.api.v1.endpoints import session_import, batch_import, rooms

api_router = APIRouter()

# Import Session 路由
api_router.include_router(
    session_import.router,
    prefix="/rooms",
    tags=["Session Import"]
)

# Batch Import 路由
api_router.include_router(
    batch_import.router,
    prefix="/rooms",
    tags=["Batch Import"]
)

# Rooms 路由（已存在，包含 Search 功能）
api_router.include_router(
    rooms.router,
    prefix="/rooms",
    tags=["Rooms"]
)
```

---

## 9. 导入依赖清单

**Service 层必需的导入**：
```python
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile
from uuid import UUID
from typing import Optional, Dict, List
from datetime import datetime
import logging
import re
import csv
import io
import chardet
import secrets

from app.crud import crud_room, crud_session, crud_session_statistics
from app.core.exceptions import (
    RoomNotFoundException,
    PermissionDeniedException,
    InvalidParameterException
)

logger = logging.getLogger(__name__)
```

**API 层必需的导入**：
```python
from fastapi import APIRouter, Depends, Query, File, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Dict, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime
import logging

from app.core.deps import get_db, get_current_user
from app.core.response import success_response, error_response
from app.services.session_import import SessionImportService
from app.services.room import RoomService
from app.services.batch_import import BatchImportService
from app.core.exceptions import (
    RoomNotFoundException,
    PermissionDeniedException,
    InvalidParameterException,
    DatabaseIntegrityException
)

logger = logging.getLogger(__name__)
```

---

## 10. 交付清单

请生成以下 Service 层和 API 层代码：

### 10.1 Service 层
- [ ] `app/services/session_import.py`：新增 `SessionImportService` 类
- [ ] `app/services/room.py`：扩展 `RoomService.search_rooms()` 方法
- [ ] `app/services/batch_import.py`：新增 `BatchImportService` 类

### 10.2 API 层
- [ ] `app/api/v1/endpoints/session_import.py`：新增 Import Session 端点
- [ ] `app/api/v1/endpoints/rooms.py`：扩展 `list_rooms()` 端点（新增 `q` 参数）
- [ ] `app/api/v1/endpoints/batch_import.py`：新增 Batch Import 端点

### 10.3 Pydantic Schema
- [ ] `app/schemas/session_import.py`：新增 `SessionImportCreate` 和 `SessionImportResponse`
- [ ] `app/schemas/batch_import.py`：新增 `BatchImportRow` 和 `BatchImportResponse`

### 10.4 辅助模块
- [ ] `app/core/exceptions.py`：确保包含所有必需的自定义异常类
- [ ] `app/core/response.py`：确保包含 `success_response()` 和 `error_response()` 函数

### 10.5 路由注册
- [ ] `app/api/v1/api.py`：注册所有新增路由

---

## 11. 代码质量检查清单

在生成代码后，请自查以下项：

### Service 层
- [ ] 所有方法都只抛出自定义异常（无 `HTTPException`）
- [ ] 所有方法都不处理事务（无 `db.commit()` / `db.rollback()`）
- [ ] 所有权限检查都在方法内部实现
- [ ] 所有日志变量都在异常处理前提取
- [ ] 所有参数验证都完整且清晰

### API 层
- [ ] 所有端点都使用 `try...except` 块
- [ ] 所有端点都正确提取 `public_id`（从 JWT 的 `public_id` 字段）
- [ ] 所有异常都正确映射到 HTTP 状态码和业务错误码
- [ ] 所有成功响应都使用 `success_response()`
- [ ] 所有错误响应都使用 `JSONResponse` + `error_response()`
- [ ] 所有路由定义都符合 4.5 节规范（无 prefix）

### 通用
- [ ] 所有日志都使用正确的级别（`info` / `warning` / `error`）
- [ ] 所有 `logger.error()` 都包含 `exc_info=True`（仅在 API 层的 `except Exception` 块中）
- [ ] 代码符合 PEP 8 规范
- [ ] 所有类型注解都完整且正确

---

## 12. 注意事项

1. **严格遵循用户身份解析规范（4.1 节）**：这是最容易出错的地方
2. **不要在 API 层执行业务逻辑**：所有业务逻辑必须在 Service 层
3. **不要在 Service 层抛出 HTTPException**：只能抛出自定义异常
4. **CSV 解析要容错**：支持多种编码、列名大小写不敏感、空白字符处理
5. **批量导入要行级隔离**：一行失败不影响其他行
6. **所有路径都相对于 prefix**：不要在 Router 定义时指定 prefix

---

**请根据以上所有要求，生成完整的 Service 层和 API 层代码。**

