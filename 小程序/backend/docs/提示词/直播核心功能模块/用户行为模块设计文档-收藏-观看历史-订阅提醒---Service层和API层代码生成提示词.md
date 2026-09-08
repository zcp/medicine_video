# 用户行为模块 - Service层和API层代码生成提示词

**模块名称**: user_behavior  
**功能模块名称**: 用户行为模块设计文档-收藏-观看历史-订阅提醒  
**目标文件**:  
- `backend/live_core_service/app/services/user_behavior_service.py`  
- `backend/live_core_service/app/api/v1/endpoints/user_behavior.py`  

**生成日期**: 2026-01-18  

---

## 1. 角色定义

你是一名精通 Clean Architecture 和 FastAPI 的资深 Python 后端架构师。你的任务是根据本提示词文档，为**用户行为模块**生成 Service 层和 API 层代码。

**🚨 [强制要求] 异常处理（最高优先级）**：
- **所有API端点**必须遵循母版的API端点实现强制模板（见母版 `crud_service_endpoint代码生成提示词母版.md` 第1477-1540行）
- **所有API端点**必须包含完整的 try-except 异常处理
- 详细要求见本文档第5.2节"示例端点（收藏）"

---

## 2. 职责划分

### 2.1 Service 层职责

Service 层是**业务逻辑层**，负责：

- ✅ 业务编排（调用多个 CRUD 函数）  
- ✅ 权限检查（通过权限守卫函数或统一的用户身份检查）  
- ✅ 业务验证（例如防止重复收藏、防止重复订阅）  
- ✅ 事务控制（`commit` / `rollback`）  
- ✅ 将 CRUD 结果转换为 Schema（Pydantic）对象或 Python dict  
- ❌ 不直接操作 HTTP 层（不处理 Request/Response）  

### 2.2 API 层职责

API 层（Endpoint）负责：

- ✅ 定义路由（路径、方法、标签）  
- ✅ 解析请求（Path / Query / Body）  
- ✅ 注入依赖（`get_db`, `get_current_user` 等）  
- ✅ 调用 Service 层方法  
- ✅ 使用统一的 `success_response` / `error_response` 构造响应  
- ✅ **异常处理**：所有端点**必须**包含完整的 try-except 异常处理（详见第5.2节）
- ❌ 不实现业务逻辑或数据库访问  

---

## 3. Schema 摘要（来自 `schemas/user_behavior.py`）

> **请在生成代码前使用 `read_file()` 读取 `app/schemas/user_behavior.py`，并根据实际字段生成代码。这里仅列出主要 Schema 名称作为参考。**

### 3.1 收藏相关

- `FavoriteCreate(room_id)`  
- `FavoriteItem(id, room_id, is_active, created_at)`  
- `FavoriteListResponse(items: List[FavoriteItem])`  

### 3.2 观看历史相关

- `WatchEventRequest(session_id, progress?)`  
- `WatchHistoryItem(id, session_id, progress?, watched_at, is_latest)`  
- `WatchHistoryListResponse(items: List[WatchHistoryItem])`  

### 3.3 订阅提醒相关

- `SubscriptionTargetType(room|session)`  
- `SubscriptionCreate(target_type, room_id?, session_id?)`  
- `SubscriptionItem(id, target_type, room_id?, session_id?, is_active, created_at)`  
- `SubscriptionListResponse(items: List[SubscriptionItem])`  

---

## 4. Service 层设计 (user_behavior_service.py)

### 4.1 Service 类结构

```python
from uuid import UUID
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import user_behavior as crud_user_behavior
from app.schemas.user_behavior import (
    FavoriteCreate,
    FavoriteItem,
    FavoriteListResponse,
    WatchEventRequest,
    WatchHistoryItem,
    WatchHistoryListResponse,
    SubscriptionTargetType,
    SubscriptionCreate,
    SubscriptionItem,
    SubscriptionListResponse,
)
from app.exceptions import (
    NotFoundException,
    InvalidParameterException,
    DatabaseIntegrityException,
)


class UserBehaviorService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.logger = logging.getLogger(__name__)
```

### 4.2 收藏相关 Service 方法

建议实现以下方法：

```python
    async def add_favorite(self, current_user_id: UUID, room_id: UUID) -> FavoriteItem:
        """
        当前用户收藏指定直播间。
        - 如果已收藏且仍然有效，抛出 InvalidParameterException("已收藏", code=2002)。
        - 如果存在 is_active=False 的历史记录，则恢复为 True。
        """
        ...

    async def remove_favorite(self, current_user_id: UUID, room_id: UUID) -> None:
        """
        当前用户取消收藏指定直播间。
        - 如果不存在收藏记录，视为幂等操作，不抛异常。
        """
        ...

    async def get_favorites(self, current_user_id: UUID) -> FavoriteListResponse:
        """
        获取当前用户的收藏列表（仅 is_active=True）。
        """
        ...
```

### 4.3 观看历史相关 Service 方法

```python
    async def record_watch_event(
        self,
        current_user_id: UUID,
        watch_event: WatchEventRequest,
    ) -> WatchHistoryItem:
        """
        记录用户观看某场直播的事件。
        - 使用 CRUD 层 record_watch_history。
        """
        ...

    async def get_watch_history(
        self,
        current_user_id: UUID,
        limit: int = 50,
    ) -> WatchHistoryListResponse:
        """
        获取当前用户的观看历史（只返回 is_latest=True 的记录）。
        """
        ...
```

### 4.4 订阅提醒相关 Service 方法

```python
    async def create_subscription(
        self,
        current_user_id: UUID,
        sub_in: SubscriptionCreate,
    ) -> SubscriptionItem:
        """
        创建订阅记录：
        - 校验 target_type 与 room_id/session_id 的组合是否有效。
        - 防止重复订阅（已有 is_active=True 时抛异常）。
        """
        ...

    async def cancel_subscription(
        self,
        current_user_id: UUID,
        target_type: SubscriptionTargetType,
        room_id: Optional[UUID] = None,
        session_id: Optional[UUID] = None,
    ) -> None:
        """
        取消订阅。
        - 如果没有找到相应记录，视为幂等操作。
        """
        ...

    async def get_subscriptions(
        self,
        current_user_id: UUID,
        target_type: Optional[SubscriptionTargetType] = None,
    ) -> SubscriptionListResponse:
        """
        获取当前用户的订阅列表。
        """
        ...
```

> **注意**：Service 层所有写操作必须在成功路径上执行 `await self.db.commit()`，在捕获已知异常（如 `InvalidParameterException`, `DatabaseIntegrityException`）时执行 `await self.db.rollback()`。

---

## 5. API 层设计 (endpoints/user_behavior.py)

### 5.1 路由器与前缀

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any
from uuid import UUID

from app.core.deps import get_db, get_current_user
from app.services.user_behavior_service import UserBehaviorService
from app.schemas.user_behavior import (
    FavoriteCreate,
    WatchEventRequest,
    SubscriptionCreate,
    SubscriptionTargetType,
)
from app.core.response import success_response, error_response


router = APIRouter()
```

API 路径建议如下（统一前缀在 `api.py` 中挂 `/api/v1`，此处只写相对路径）：

- 收藏：
  - `POST /users/me/favorites`  
  - `GET /users/me/favorites`  
  - `DELETE /users/me/favorites/{room_id}`  

- 观看历史：
  - `POST /users/me/watch-history`  
  - `GET /users/me/watch-history`  

- 订阅：
  - `POST /users/me/subscriptions`  
  - `GET /users/me/subscriptions`  
  - `DELETE /users/me/subscriptions`（可以用 Query/Body 指定 target_type + room_id/session_id）  

### 5.2 示例端点（收藏）

**🚨 [强制要求] 异常处理（最高优先级）**：
- **所有API端点**必须遵循母版的API端点实现强制模板（见母版 `crud_service_endpoint代码生成提示词母版.md` 第1477-1540行）
- **所有API端点**必须包含完整的 try-except 异常处理
- **必须在 try 块之前**提取 `user_id` 和 `role`（如果使用）
- **必须捕获** `PermissionDeniedException`, `NotFoundException`, `InvalidParameterException` 等自定义异常
- **必须将异常转换为** `JSONResponse`，使用 `error_response()` 构建错误响应

```python
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from app.exceptions import (
    NotFoundException,
    PermissionDeniedException,
    InvalidParameterException,
    DatabaseIntegrityException,
)
from app.core.response import success_response, error_response
import logging

logger = logging.getLogger(__name__)

@router.post("/users/me/favorites")
async def add_favorite(
    favorite_in: FavoriteCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """创建收藏"""
    # 🚨 必须在 try 之前提取 user_id
    user_id = UUID(current_user["user_id"])
    
    try:
        service = UserBehaviorService(db)
        result = await service.add_favorite(user_id, favorite_in.room_id)
        return success_response(data=result)
    except InvalidParameterException as e:
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message=str(e))
        )
    except Exception as e:
        logger.error(f"创建收藏失败: {e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )


@router.get("/users/me/favorites")
async def get_favorites(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """获取收藏列表"""
    # 🚨 必须在 try 之前提取 user_id
    user_id = UUID(current_user["user_id"])
    
    try:
        service = UserBehaviorService(db)
        result = await service.get_favorites(user_id)
        return success_response(data=result.model_dump())
    except Exception as e:
        logger.error(f"获取收藏列表失败: {e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )


@router.delete("/users/me/favorites/{room_id}")
async def remove_favorite(
    room_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """取消收藏"""
    # 🚨 必须在 try 之前提取 user_id
    user_id = UUID(current_user["user_id"])
    
    try:
        service = UserBehaviorService(db)
        await service.remove_favorite(user_id, room_id)
        return success_response()
    except NotFoundException as e:
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message=str(e))
        )
    except Exception as e:
        logger.error(f"取消收藏失败: {e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )
```

### 5.3 观看历史与订阅端点

请遵循与收藏相同的模式（**必须包含完整的异常处理**）：

- **必须在 try 块之前**从 `current_user["user_id"]` 提取 `UUID` 形式的 `user_id`；  
- 注入 `AsyncSession`；  
- 调用 Service 层方法；  
- 使用 `success_response(data=...)` 返回结果；  
- **必须包含完整的 try-except 异常处理**，捕获 `InvalidParameterException`, `NotFoundException` 等自定义异常，并转换为 `JSONResponse`；  
- 对业务异常（如 `InvalidParameterException`）在 Service 层转为自定义异常，在 API 层统一包装为 JSON 错误响应。  

---

## 6. 路由注册 (api.py)

在 `app/api/v1/api.py` 中，增加用户行为模块路由注册（注意避免之前因模块缺失而被注释的旧代码，按当前实现重新注册）：  

```python
from app.api.v1.endpoints import ..., user_behavior

api_router.include_router(
    user_behavior.router,
    prefix="/api/v1",
    tags=["用户行为"],
)
```

> 确保只添加一次路由注册，并与其它模块的前缀命名规范保持一致。*** End Patch***}]} -->
