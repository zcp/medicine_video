# 品牌模块 - Service层和API层代码生成提示词

**模块名称**: brand  
**功能模块名称**: 品牌模块设计文档-品牌管理-品牌专题关联-品牌直播间关联  
**目标文件**: 
- `backend/live_core_service/app/services/brand_service.py`
- `backend/live_core_service/app/api/v1/endpoints/brand.py`

**生成日期**: 2026-01-18  

---

## 1. 角色定义

你是一名精通Clean Architecture和FastAPI的资深Python后端架构师。你的任务是根据本提示词文档，生成品牌模块的Service层和API层代码。

---

## 2. 核心要求

### 2.1. Service层职责

Service层是业务逻辑层，负责：
- ✅ 业务编排（调用多个CRUD函数）
- ✅ 权限检查（通过权限守卫函数）
- ✅ 业务验证（批量ID验证、数据有效性检查）
- ✅ 事务控制（默认依赖API层事务）
- ✅ 响应构造（将CRUD结果转换为Schema响应）
- ❌ 不负责数据库操作（由CRUD层处理）
- ❌ 不负责HTTP请求解析（由Endpoint层处理）

**🚨 批量验证规范（强制要求）**：

Service层必须在调用CRUD层之前完成所有批量验证：
```python
# 示例：验证品牌ID列表
stmt = select(Brand).where(Brand.id.in_(brand_ids), Brand.is_active == True)
result = await db.execute(stmt)
existing_brands = result.scalars().all()
existing_ids = {b.id for b in existing_brands}
invalid_ids = set(brand_ids) - existing_ids

if invalid_ids:
    raise InvalidParameterException(f"部分品牌ID不存在: {[str(id) for id in invalid_ids]}")
```

### 2.2. API层职责

API层（Endpoint层）是HTTP端点层，负责：
- ✅ 请求解析（Path、Query、Body参数）
- ✅ 依赖注入（get_db, get_current_user等）
- ✅ 提前提取role并调用`.upper()`（🚨 强制要求）
- ✅ 调用Service层方法
- ✅ 完整的异常处理（try-except）
- ✅ 返回JSON响应（使用JSONResponse + error_response）
- ❌ 不负责业务逻辑（由Service层处理）

### 2.3. 关键原则

1. **权限检查在Service层**: 使用`_check_admin_permission(role)`
2. **双轨鉴权模式**: 
   - Strict Auth: 写操作使用`Depends(get_current_user)`
   - Optional Auth: 读操作使用`Depends(get_current_user_optional)`
3. **品牌模块特点**: 品牌信息是公开资源，所有写操作需要管理员权限
4. **响应标准化**: 所有响应包含`code`, `message`, `data`, `timestamp`
5. **角色转换强制要求**: 在try块之前调用`.upper()`
6. **日志脱敏**: UUID只记录前8位
7. **响应函数使用规范**:
   - **成功响应**: 直接使用 `return success_response(data=...)`，FastAPI自动序列化为JSON（状态码200）
   - **错误响应**: **必须**使用 `return JSONResponse(status_code=xxx, content=error_response(...))`，因为`error_response()`仅返回字典，需要通过`JSONResponse`指定HTTP状态码

---

## 3. Service层方法清单（14个）

### 3.1. 权限守卫函数（1个）

#### 方法1: `_check_admin_permission`

**函数签名**:
```python
def _check_admin_permission(self, user_role: str) -> None
```

**功能**: 管理员权限检查

**实现**:
```python
def _check_admin_permission(self, user_role: str) -> None:
    """管理员权限检查"""
    if user_role not in ['ADMIN', 'SUPERADMIN']:  # 🚨 必须使用大写
        raise PermissionDeniedException("权限不足，需要管理员权限")
```

---

### 3.2. Brands Service方法（7个）

#### 方法2: `get_brands_list`

**函数签名**:
```python
async def get_brands_list(
    self,
    db: AsyncSession,
    limit: int,
    q: Optional[str],
    current_user_id: Optional[UUID],
    role: Optional[str]
) -> dict
```

**功能**: 获取品牌列表（公开接口）

**执行流程**:
1. 调用CRUD层：`brands = await crud.get_brands(db, limit, q)`
2. 序列化：`[BrandItem.model_validate(b) for b in brands]`
3. 构造响应：返回包含品牌列表的字典
4. 记录日志

**实现模板**:
```python
async def get_brands_list(
    self,
    db: AsyncSession,
    limit: int,
    q: Optional[str],
    current_user_id: Optional[UUID],
    role: Optional[str]
) -> List[BrandItem]:
    brands = await crud.get_brands(db, limit, q)
    brand_items = [BrandItem.model_validate(b) for b in brands]
    
    return brand_items  # ✅ Service层返回业务对象，由API层使用success_response包装
```

---

#### 方法3: `get_brand_content`

**函数签名**:
```python
async def get_brand_content(
    self,
    db: AsyncSession,
    brand_id: UUID,
    current_user_id: Optional[UUID],
    role: Optional[str]
) -> dict
```

**功能**: 获取品牌详情及关联专题

**执行流程**:
1. 调用CRUD层：`brand, topics = await crud.get_brand_with_topics(db, brand_id)`
2. 404检查：如果品牌不存在，抛出`NotFoundException`
3. 序列化品牌和专题
4. 构造响应

---

#### 方法4-8: 其他Brands Service方法

- `create_brand`: 创建品牌（需管理员权限）
- `get_brands_paginated`: 获取品牌列表（管理员分页）
- `get_brand_by_id`: 获取单个品牌（管理员）
- `update_brand`: 更新品牌（需管理员权限）
- `delete_brand`: 删除品牌（软删除需ADMIN，硬删除需SUPERADMIN）

**关键点**:
- 所有写操作：先调用`self._check_admin_permission(role)`
- `delete_brand`: 硬删除前需检查引用关系

---

### 3.3. Brand_Topics Service方法（3个）

#### 方法9: `batch_add_brand_topics`

**函数签名**:
```python
async def batch_add_brand_topics(
    self,
    db: AsyncSession,
    brand_id: UUID,
    topic_ids: List[UUID],
    current_user_id: UUID,
    role: str
) -> dict
```

**功能**: 批量关联专题到品牌

**执行流程**:
```python
# 1. 权限检查
self._check_admin_permission(role)

# 2. 验证品牌存在
brand = await crud.get_brand_by_id(db, brand_id)
if not brand or not brand.is_active:
    raise NotFoundException("品牌不存在")

# 3. 批量验证专题ID
stmt = select(Topic.id).where(Topic.id.in_(topic_ids))
result = await db.execute(stmt)
existing_ids = set(result.scalars().all())
invalid_ids = set(topic_ids) - existing_ids

if invalid_ids:
    raise InvalidParameterException(f"部分专题ID不存在: {[str(id) for id in invalid_ids]}")

# 4. 执行批量关联
added_count = await crud.batch_add_brand_topics(db, brand_id, topic_ids)

# 5. 返回结果
return {
    "brand_id": str(brand_id),
    "added_count": added_count,
    "topic_ids": [str(id) for id in topic_ids]
}  # ✅ Service层返回业务数据字典，由API层使用success_response包装
```

---

#### 方法10-11: 其他Brand_Topics Service方法

- `delete_brand_topic`: 解除单个品牌-专题关联
- `get_brand_topics_paginated`: 获取品牌关联专题列表（管理员分页）

---

### 3.4. Brand_Rooms Service方法（3个）

#### 方法12: `bind_room_brands`

**函数签名**:
```python
async def bind_room_brands(
    self,
    db: AsyncSession,
    room_id: UUID,
    brand_ids: List[UUID],
    current_user_id: UUID,
    role: str
) -> dict
```

**功能**: 为直播间绑定品牌（全量替换策略）

**执行流程**:
```python
# 1. 权限检查
self._check_admin_permission(role)

# 2. 验证直播间存在
stmt = select(LiveRoom).where(LiveRoom.id == room_id)
result = await db.execute(stmt)
room = result.scalar_one_or_none()
if not room:
    raise NotFoundException("直播间不存在")

# 3. 批量验证品牌ID（is_active=True）
if brand_ids:
    stmt = select(Brand.id).where(
        Brand.id.in_(brand_ids),
        Brand.is_active == True
    )
    result = await db.execute(stmt)
    existing_ids = set(result.scalars().all())
    invalid_ids = set(brand_ids) - existing_ids
    
    if invalid_ids:
        raise InvalidParameterException(f"部分品牌ID不存在或已禁用: {[str(id) for id in invalid_ids]}")

# 4. 执行绑定（全量替换）
bound_ids = await crud.bind_room_brands(db, room_id, brand_ids)

# 5. 返回结果
return {
    "room_id": str(room_id),
    "brand_ids": [str(id) for id in bound_ids],
    "updated_at": datetime.utcnow()
}  # ✅ Service层返回业务数据字典，由API层使用success_response包装
```

---

#### 方法13-14: 其他Brand_Rooms Service方法

- `get_room_brands_admin`: 获取直播间绑定的品牌（管理员）
- `get_room_brands_for_tab`: 获取直播间品牌Tab内容（公开）

---

## 4. API层端点清单（13个）

### 4.1. API端点实现强制模板

**🚨 所有端点必须遵循以下模板**：

```python
from fastapi import APIRouter, Depends, Query, Path, Body
from fastapi.responses import JSONResponse
from app.exceptions import PermissionDeniedException, NotFoundException, InvalidParameterException, ConflictException
from app.core.response import success_response, error_response
import logging

logger = logging.getLogger(__name__)
router = APIRouter()  # ⚠️ 不指定prefix

@router.post("/admin/brands")
async def create_brand(
    brand_data: BrandCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Any:
    """创建品牌（Strict Auth + Admin）"""
    # 🚨 步骤1：在try块之前提取所有必要信息
    current_user_id = UUID(current_user["user_id"])
    role = current_user.get("role", "REGULAR").upper()  # ✅ 必须调用.upper()
    user_id_for_logging = str(current_user_id)[:8]
    
    try:
        # 🚨 步骤2：调用Service层
        result = await brand_service.create_brand(db, brand_data, current_user_id, role)
        # ✅ 使用success_response包装Service层返回的业务对象
        return success_response(data=result, message="品牌创建成功")
        
    # 🚨 步骤3：捕获所有可能的异常
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: user_id={user_id_for_logging}, role={role}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message="权限不足")
        )
    except NotFoundException as e:
        logger.warning(f"资源不存在: user_id={user_id_for_logging}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在")
        )
    except InvalidParameterException as e:
        logger.warning(f"参数验证失败: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message=str(e))
        )
    except ConflictException as e:
        logger.warning(f"操作冲突: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=409,
            content=error_response(code=2003, message=str(e))
        )
    except Exception as e:
        logger.error(f"创建品牌异常: user_id={user_id_for_logging}, error={type(e).__name__}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )
```

---

### 4.2. Brands端点（7个）

#### 端点1: `GET /api/v1/brands`

**功能**: 获取品牌列表（Public + Optional Auth）

**关键点**:
- 使用`Depends(get_current_user_optional)`
- 支持`limit`和`q`参数
- 无需权限检查

---

#### 端点2: `GET /api/v1/brands/{brand_id}/content`

**功能**: 获取品牌详情及关联专题（Public + Optional Auth）

**关键点**:
- 使用`Depends(get_current_user_optional)`
- 返回品牌信息和关联的已发布专题

---

#### 端点3-7: 其他Brands端点

- `POST /api/v1/admin/brands`: 创建品牌（Admin）
- `GET /api/v1/admin/brands`: 获取品牌列表（Admin分页）
- `GET /api/v1/admin/brands/{brand_id}`: 获取单个品牌（Admin）
- `PATCH /api/v1/admin/brands/{brand_id}`: 更新品牌（Admin）
- `DELETE /api/v1/admin/brands/{brand_id}`: 删除品牌（Admin/SuperAdmin）

**关键点**:
- 所有Admin端点使用`Depends(get_current_user)`
- DELETE端点支持`hard_delete`参数（Query）

---

### 4.3. Brand_Topics端点（3个）

#### 端点8: `POST /api/v1/admin/brands/{brand_id}/topics`

**功能**: 批量关联专题到品牌（Admin）

**参数**:
- Path: `brand_id`
- Body: `BrandTopicBindIn`（topic_ids列表）

**关键点**:
- 使用`Depends(get_current_user)`
- 调用`brand_service.batch_add_brand_topics`

---

#### 端点9-10: 其他Brand_Topics端点

- `DELETE /api/v1/admin/brands/{brand_id}/topics/{topic_id}`: 解除关联
- `GET /api/v1/admin/brands/{brand_id}/topics`: 获取关联专题列表（分页）

---

### 4.4. Brand_Rooms端点（3个）

#### 端点11: `POST /api/v1/admin/rooms/{room_id}/brands`

**功能**: 绑定直播间品牌（Admin）

**参数**:
- Path: `room_id`
- Body: `BrandRoomBindIn`（brand_ids列表）

**关键点**:
- 使用全量替换策略
- 允许brand_ids为空数组（清空绑定）

---

#### 端点12: `GET /api/v1/admin/rooms/{room_id}/brands`

**功能**: 获取直播间绑定的品牌（Admin）

---

#### 端点13: `GET /api/v1/rooms/{room_id}/brands`

**功能**: 获取直播间品牌Tab内容（Public + Optional Auth）

**关键点**:
- 支持`include_topic_brands`参数（bool）
- 如果`include_topic_brands=True`，还需`topic_id`参数
- 返回结构化数据或简单列表

---

## 5. 关键实现规范

### 5.1. 批量验证规范

**强制模式**:
```python
# 验证品牌ID列表
stmt = select(Brand).where(Brand.id.in_(brand_ids), Brand.is_active == True)
result = await db.execute(stmt)
existing_brands = result.scalars().all()
existing_ids = {b.id for b in existing_brands}
invalid_ids = set(brand_ids) - existing_ids

if invalid_ids:
    raise InvalidParameterException(f"部分品牌ID不存在: {[str(id) for id in invalid_ids]}")
```

### 5.2. URL拼接规范

**资源导向设计**:
```python
# ✅ 正确
GET /api/v1/brands
POST /api/v1/admin/brands
POST /api/v1/admin/brands/{brand_id}/topics
POST /api/v1/admin/rooms/{room_id}/brands

# ❌ 错误
GET /api/v1/get_brands
POST /api/v1/create_brand
```

### 5.3. 响应格式化规范

**标准响应结构**:
```python
return {
    "code": 200,
    "message": "success",
    "data": {...},  # 业务数据
    "timestamp": datetime.utcnow()
}
```

### 5.4. 路由定义规范

**禁止在Endpoint文件中指定prefix**:
```python
# ✅ 正确（endpoints/brand.py）
router = APIRouter()

# ❌ 错误
router = APIRouter(prefix="/api/v1")
```

**prefix在api.py中统一指定**:
```python
# ✅ 正确（api/v1/api.py）
from app.api.v1.endpoints import brand

api_router = APIRouter()
api_router.include_router(brand.router, prefix="/api/v1", tags=["brands"])
```

### 5.5. 权限模式规范

**角色比较必须使用大写**:
```python
# ✅ 正确
if role not in ['ADMIN', 'SUPERADMIN']:
    raise PermissionDeniedException("权限不足")

# ❌ 错误
if role not in ['admin', 'superadmin']:  # 禁止使用小写
```

### 5.6. 角色转换强制要求

**在try块之前提取并转换**:
```python
# ✅ 正确
current_user_id = UUID(current_user["user_id"])
role = current_user.get("role", "REGULAR").upper()  # 必须调用.upper()
user_id_for_logging = str(current_user_id)[:8]

try:
    result = await service.some_method(..., role)
    ...

# ❌ 错误
role = current_user.get("role")  # 缺少.upper()调用
try:
    role = current_user.get("role", "REGULAR").upper()  # 在try块内提取
```

---

## 6. 导入语句

### 6.1. Service层导入

```python
import logging
from typing import List, Optional, Tuple
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import brand as crud
from app.models.brand import Brand, BrandTopic, BrandRoom
from app.models.topic import Topic  # 专题模型
from app.models.live_core import LiveRoom  # 直播间模型
from app.schemas.brand import (
    BrandCreate, BrandUpdate, BrandItem,
    BrandContentData, BrandContentResponse,
    BrandTopicBindIn, BrandTopicBindOut,
    BrandRoomBindIn, BrandRoomBindOut,
    TopicBriefItem, RoomBrandItem
)
from app.core.exceptions import (
    NotFoundException,
    PermissionDeniedException,
    InvalidParameterException,
    ConflictException
)

logger = logging.getLogger(__name__)


class BrandService:
    """品牌服务类"""
    
    def _check_admin_permission(self, user_role: str) -> None:
        """管理员权限检查"""
        if user_role not in ['ADMIN', 'SUPERADMIN']:
            raise PermissionDeniedException("权限不足，需要管理员权限")
    
    # ... Service方法
```

### 6.2. API层导入

```python
import logging
from typing import Any, Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Path, Body
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.deps import get_current_user, get_current_user_optional
from app.core.response import error_response
from app.exceptions import (
    PermissionDeniedException,
    NotFoundException,
    InvalidParameterException,
    ConflictException
)
from app.schemas.brand import (
    BrandCreate, BrandUpdate,
    BrandTopicBindIn, BrandRoomBindIn
)
from app.services.brand_service import BrandService

logger = logging.getLogger(__name__)
router = APIRouter()  # ⚠️ 不指定prefix
brand_service = BrandService()
```

---

## 7. 增量开发模式

**🚨 重要**：如果目标文件已存在：
1. **检测现有代码**：读取文件内容，识别已实现的方法/端点
2. **仅生成缺失部分**：只生成文件中不存在的方法/端点
3. **最小化修改**：不修改已有方法的实现
4. **追加模式**：将新方法追加到类/文件末尾

如果文件不存在，则生成完整的Service层和API层代码文件。

---

## 8. 交付物

### 8.1. Service层代码

生成完整的`backend/live_core_service/app/services/brand_service.py`文件，包含：
1. 完整的导入语句
2. logger初始化
3. BrandService类定义
4. 14个Service方法的完整实现
5. 每个方法包含完整的权限检查、业务验证、异常处理

### 8.2. API层代码

生成完整的`backend/live_core_service/app/api/v1/endpoints/brand.py`文件，包含：
1. 完整的导入语句
2. logger和router初始化
3. BrandService实例化
4. 13个API端点的完整实现
5. 每个端点遵循API端点实现强制模板
6. 完整的异常处理和日志记录

**代码风格**:
- 使用4空格缩进
- 函数之间空2行
- 注释使用中文
- 类型提示完整
- Docstring使用三引号字符串

---

**生成完成时间**: 2026-01-18T12:50:00Z
