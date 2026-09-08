# 首页与搜索模块 - Service层和API层代码生成提示词 (Phase1: 焦点图CRUD)

**模块名称**: homepage_search  
**功能模块名称**: 首页与搜索模块设计文档-焦点图-首页API-搜索API  
**Phase**: Phase1 - 焦点图CRUD  
**目标文件**: 
- `backend/live_core_service/app/services/homepage_search_service.py`
- `backend/live_core_service/app/api/v1/endpoints/homepage_search.py`

**生成日期**: 2026-01-18  

---

## 📋 实施说明

本模块采用**分阶段实施策略**：
- **Phase1（本文档）**: 焦点图CRUD - Service层和API层
- **Phase2（待生成）**: 首页API - 复杂查询的Service和API
- **Phase3（待生成）**: 搜索API - 全文搜索的Service和API

---

## 1. 角色定义

你是一名精通Clean Architecture和FastAPI的资深Python后端架构师。你的任务是根据本提示词文档，生成首页与搜索模块Phase1（焦点图CRUD）的Service层和API层代码。

---

## 2. 核心要求

### 2.1. Service层职责

Service层是业务逻辑层，负责：
- ✅ 业务编排（调用CRUD函数）
- ✅ 权限检查（管理员权限守卫）
- ✅ 业务验证（目标资源验证）
- ✅ 响应构造（将CRUD结果转换为Schema响应）
- ❌ 不负责数据库操作（由CRUD层处理）
- ❌ 不负责HTTP请求解析（由API层处理）

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
   - Public Access: 公开读操作无需认证
3. **焦点图特点**: 公开查询无需认证，所有写操作需要管理员权限
4. **响应标准化**: 所有响应包含`code`, `message`, `data`, `timestamp`
5. **角色转换强制要求**: 在try块之前调用`.upper()`
6. **日志脱敏**: UUID只记录前8位

---

## 3. Service层方法清单（6个）

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

### 3.2. Featured Content Service方法（5个）

#### 方法2: `get_featured_content_list`

**函数签名**:
```python
async def get_featured_content_list(
    self,
    db: AsyncSession
) -> dict
```

**功能**: 获取焦点图列表（公开接口）

**执行流程**:
1. 调用CRUD层：`items = await crud.get_featured_content_list(db, include_inactive=False)`
2. 序列化：`[FeaturedContentItem.model_validate(item) for item in items]`
3. 构造响应
4. 记录日志

**实现模板**:
```python
async def get_featured_content_list(
    self,
    db: AsyncSession
) -> dict:
    items = await crud.get_featured_content_list(db, include_inactive=False)
    content_items = [FeaturedContentItem.model_validate(item) for item in items]
    
    logger.info(f"查询焦点图列表（公开），返回{len(content_items)}条")
    
    return {
        "code": 200,
        "message": "success",
        "data": content_items,
        "timestamp": datetime.utcnow()
    }
```

---

#### 方法3: `create_featured_content`

**函数签名**:
```python
async def create_featured_content(
    self,
    db: AsyncSession,
    content_data: FeaturedContentCreate,
    current_user_id: UUID,
    role: str
) -> dict
```

**功能**: 创建焦点图（管理员功能）

**执行流程**:
```python
# 1. 权限检查
self._check_admin_permission(role)

# 2. 目标资源验证（如果提供了target_id）
if content_data.target_id and content_data.target_type:
    await self._validate_target_resource(db, content_data.target_type, content_data.target_id)

# 3. 调用CRUD层创建
content = await crud.create_featured_content(db, content_data)

# 4. 序列化并返回
content_item = FeaturedContentItem.model_validate(content)

logger.info(f"创建焦点图: {str(content.id)[:8]}, 管理员={str(current_user_id)[:8]}")

return {
    "code": 200,
    "message": "success",
    "data": content_item,
    "timestamp": datetime.utcnow()
}
```

**目标资源验证辅助方法**:
```python
async def _validate_target_resource(
    self,
    db: AsyncSession,
    target_type: str,
    target_id: UUID
) -> None:
    """验证目标资源是否存在"""
    if target_type == "room":
        from app.models.live_core import LiveRoom
        stmt = select(LiveRoom).where(LiveRoom.id == target_id)
        result = await db.execute(stmt)
        if not result.scalar_one_or_none():
            raise InvalidParameterException(f"直播间不存在: {target_id}")
    
    elif target_type == "session":
        from app.models.live_core import LiveSession
        stmt = select(LiveSession).where(LiveSession.id == target_id)
        result = await db.execute(stmt)
        if not result.scalar_one_or_none():
            raise InvalidParameterException(f"场次不存在: {target_id}")
    
    elif target_type == "topic":
        from app.models.topic import Topic
        stmt = select(Topic).where(Topic.id == target_id)
        result = await db.execute(stmt)
        if not result.scalar_one_or_none():
            raise InvalidParameterException(f"专题不存在: {target_id}")
    
    elif target_type == "brand":
        from app.models.brand import Brand
        stmt = select(Brand).where(Brand.id == target_id, Brand.is_active == True)
        result = await db.execute(stmt)
        if not result.scalar_one_or_none():
            raise InvalidParameterException(f"品牌不存在: {target_id}")
    
    elif target_type == "external":
        # 外部链接不需要验证target_id
        pass
    
    else:
        raise InvalidParameterException(f"不支持的目标类型: {target_type}")
```

---

#### 方法4: `update_featured_content`

**函数签名**:
```python
async def update_featured_content(
    self,
    db: AsyncSession,
    content_id: UUID,
    content_data: FeaturedContentUpdate,
    current_user_id: UUID,
    role: str
) -> dict
```

**功能**: 更新焦点图（管理员功能）

**执行流程**:
```python
# 1. 权限检查
self._check_admin_permission(role)

# 2. 目标资源验证（如果更新了target_id和target_type）
update_dict = content_data.model_dump(exclude_unset=True)
if "target_id" in update_dict and "target_type" in update_dict:
    await self._validate_target_resource(db, update_dict["target_type"], update_dict["target_id"])

# 3. 调用CRUD层更新
content = await crud.update_featured_content(db, content_id, content_data)

# 4. 404检查
if not content:
    raise NotFoundException(f"焦点图不存在: {content_id}")

# 5. 序列化并返回
content_item = FeaturedContentItem.model_validate(content)

logger.info(f"更新焦点图: {str(content_id)[:8]}, 更新字段={list(update_dict.keys())}")

return {
    "code": 200,
    "message": "success",
    "data": content_item,
    "timestamp": datetime.utcnow()
}
```

---

#### 方法5: `delete_featured_content`

**函数签名**:
```python
async def delete_featured_content(
    self,
    db: AsyncSession,
    content_id: UUID,
    current_user_id: UUID,
    role: str
) -> dict
```

**功能**: 删除焦点图（软删除，管理员功能）

**执行流程**:
```python
# 1. 权限检查
self._check_admin_permission(role)

# 2. 调用CRUD层删除（软删除）
success = await crud.delete_featured_content(db, content_id, soft_delete=True)

# 3. 404检查
if not success:
    raise NotFoundException(f"焦点图不存在: {content_id}")

# 4. 返回删除状态
logger.warning(f"删除焦点图: {str(content_id)[:8]}, 管理员={str(current_user_id)[:8]}")

return {
    "code": 200,
    "message": "success",
    "data": {
        "id": content_id,
        "status": "deleted",
        "deleted_at": datetime.utcnow()
    },
    "timestamp": datetime.utcnow()
}
```

---

#### 方法6: `get_featured_content_list_admin`

**函数签名**:
```python
async def get_featured_content_list_admin(
    self,
    db: AsyncSession,
    current_user_id: UUID,
    role: str
) -> dict
```

**功能**: 获取焦点图列表（管理员接口，显示所有状态）

**执行流程**:
```python
# 1. 权限检查
self._check_admin_permission(role)

# 2. 调用CRUD层（包含未启用的）
items = await crud.get_featured_content_list(db, include_inactive=True)

# 3. 序列化并返回
content_items = [FeaturedContentItem.model_validate(item) for item in items]

logger.info(f"查询焦点图列表（管理员），返回{len(content_items)}条")

return {
    "code": 200,
    "message": "success",
    "data": content_items,
    "timestamp": datetime.utcnow()
}
```

---

## 4. API层端点清单（5个）

### 4.1. 公开端点（1个）

#### 端点1: 获取焦点图列表（公开）

**路由定义**:
```python
@router.get("/featured-content", response_model=None, tags=["Featured Content"])
async def get_featured_content_list_endpoint(
    db: AsyncSession = Depends(get_db)
):
    """
    获取首页焦点图列表（公开接口）
    
    - 仅返回已启用且在有效期内的焦点图
    - 按排序权重升序排列
    - 最多返回10条
    """
    try:
        service = HomepageSearchService()
        result = await service.get_featured_content_list(db)
        
        return JSONResponse(
            status_code=200,
            content=result
        )
    
    except Exception as e:
        logger.error(f"获取焦点图列表失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=5001, message="服务器内部错误")
        )
```

---

### 4.2. 管理员端点（4个）

#### 端点2: 获取焦点图列表（管理员）

**路由定义**:
```python
@router.get("/admin/featured-content", response_model=None, tags=["Featured Content Admin"])
async def get_featured_content_list_admin_endpoint(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取焦点图列表（管理员接口）
    
    - 返回所有焦点图（包括未启用和未到上线时间的）
    - 需要ADMIN或SUPERADMIN权限
    """
    # 🚨 强制要求：在try块之前提取并转换role
    user_id = UUID(current_user.get("user_id") or current_user.get("sub"))
    role = (current_user.get("role") or "REGULAR").upper()
    
    try:
        service = HomepageSearchService()
        result = await service.get_featured_content_list_admin(db, user_id, role)
        
        return JSONResponse(
            status_code=200,
            content=result
        )
    
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: {str(e)}, 用户={str(user_id)[:8]}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3002, message=str(e))
        )
    
    except Exception as e:
        logger.error(f"获取焦点图列表失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=5001, message="服务器内部错误")
        )
```

---

#### 端点3: 创建焦点图

**路由定义**:
```python
@router.post("/admin/featured-content", response_model=None, tags=["Featured Content Admin"])
async def create_featured_content_endpoint(
    content_data: FeaturedContentCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    创建焦点图（管理员功能）
    
    - 需要ADMIN或SUPERADMIN权限
    - 自动生成UUID
    - 支持定时上下线
    """
    user_id = UUID(current_user.get("user_id") or current_user.get("sub"))
    role = (current_user.get("role") or "REGULAR").upper()
    
    try:
        service = HomepageSearchService()
        result = await service.create_featured_content(db, content_data, user_id, role)
        
        return JSONResponse(
            status_code=200,
            content=result
        )
    
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: {str(e)}, 用户={str(user_id)[:8]}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3002, message=str(e))
        )
    
    except InvalidParameterException as e:
        logger.warning(f"参数错误: {str(e)}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message=str(e))
        )
    
    except Exception as e:
        logger.error(f"创建焦点图失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=5001, message="服务器内部错误")
        )
```

---

#### 端点4: 更新焦点图

**路由定义**:
```python
@router.patch("/admin/featured-content/{content_id}", response_model=None, tags=["Featured Content Admin"])
async def update_featured_content_endpoint(
    content_id: UUID,
    content_data: FeaturedContentUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新焦点图（管理员功能）
    
    - 需要ADMIN或SUPERADMIN权限
    - 支持部分更新
    - 自动更新updated_at字段
    """
    user_id = UUID(current_user.get("user_id") or current_user.get("sub"))
    role = (current_user.get("role") or "REGULAR").upper()
    
    try:
        service = HomepageSearchService()
        result = await service.update_featured_content(db, content_id, content_data, user_id, role)
        
        return JSONResponse(
            status_code=200,
            content=result
        )
    
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: {str(e)}, 用户={str(user_id)[:8]}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3002, message=str(e))
        )
    
    except NotFoundException as e:
        logger.warning(f"资源不存在: {str(e)}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message=str(e))
        )
    
    except InvalidParameterException as e:
        logger.warning(f"参数错误: {str(e)}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message=str(e))
        )
    
    except Exception as e:
        logger.error(f"更新焦点图失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=5001, message="服务器内部错误")
        )
```

---

#### 端点5: 删除焦点图

**路由定义**:
```python
@router.delete("/admin/featured-content/{content_id}", response_model=None, tags=["Featured Content Admin"])
async def delete_featured_content_endpoint(
    content_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除焦点图（管理员功能）
    
    - 需要ADMIN或SUPERADMIN权限
    - 软删除（设置is_active=false）
    """
    user_id = UUID(current_user.get("user_id") or current_user.get("sub"))
    role = (current_user.get("role") or "REGULAR").upper()
    
    try:
        service = HomepageSearchService()
        result = await service.delete_featured_content(db, content_id, user_id, role)
        
        return JSONResponse(
            status_code=200,
            content=result
        )
    
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: {str(e)}, 用户={str(user_id)[:8]}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3002, message=str(e))
        )
    
    except NotFoundException as e:
        logger.warning(f"资源不存在: {str(e)}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message=str(e))
        )
    
    except Exception as e:
        logger.error(f"删除焦点图失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=5001, message="服务器内部错误")
        )
```

---

## 5. 导入语句要求

### 5.1. Service层导入

```python
"""
首页与搜索模块的Service层 (Phase1: 焦点图CRUD)

本模块负责焦点图的业务逻辑处理。
"""
import uuid
from typing import Optional
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import homepage_search as crud
from app.schemas.homepage_search import (
    FeaturedContentCreate,
    FeaturedContentUpdate,
    FeaturedContentItem
)
from app.exceptions import (
    PermissionDeniedException,
    NotFoundException,
    InvalidParameterException
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class HomepageSearchService:
    """首页与搜索模块Service层"""
    
    # 权限守卫和业务方法...
```

### 5.2. API层导入

```python
"""
首页与搜索模块的API端点 (Phase1: 焦点图CRUD)
"""
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_current_user
from app.services.homepage_search_service import HomepageSearchService
from app.schemas.homepage_search import (
    FeaturedContentCreate,
    FeaturedContentUpdate
)
from app.exceptions import (
    PermissionDeniedException,
    NotFoundException,
    InvalidParameterException
)
from app.core.responses import error_response
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()
```

---

## 6. 路由注册要求

在`backend/live_core_service/app/api/v1/api.py`中注册路由：

```python
from app.api.v1.endpoints import homepage_search

# 在api_router中添加
api_router.include_router(
    homepage_search.router,
    prefix="/featured-content",  # 🚨 注意：prefix在这里指定
    tags=["Featured Content"]
)
```

**⚠️ 关键注意事项**:
- `prefix`在`api.py`中统一指定，不在`endpoints/homepage_search.py`的`APIRouter()`中指定
- 端点路径使用相对路径（如`""`、`"/admin/featured-content"`）

---

## 7. 异常处理规范

### 7.1. Service层异常

- `PermissionDeniedException`: 权限不足（403）
- `NotFoundException`: 资源不存在（404）
- `InvalidParameterException`: 参数错误（400）

### 7.2. API层异常处理

```python
try:
    # 调用Service层
    result = await service.some_method(...)
    return JSONResponse(status_code=200, content=result)

except PermissionDeniedException as e:
    logger.warning(f"权限不足: {str(e)}")
    return JSONResponse(
        status_code=403,
        content=error_response(code=3002, message=str(e))
    )

except NotFoundException as e:
    logger.warning(f"资源不存在: {str(e)}")
    return JSONResponse(
        status_code=404,
        content=error_response(code=2001, message=str(e))
    )

except InvalidParameterException as e:
    logger.warning(f"参数错误: {str(e)}")
    return JSONResponse(
        status_code=400,
        content=error_response(code=4001, message=str(e))
    )

except Exception as e:
    logger.error(f"操作失败: {str(e)}")
    return JSONResponse(
        status_code=500,
        content=error_response(code=5001, message="服务器内部错误")
    )
```

---

## 8. 测试验证要点

生成代码后，请确保：

1. ✅ Service层所有方法都有完整的类型提示
2. ✅ Service层所有写操作都调用了`_check_admin_permission`
3. ✅ Service层目标资源验证逻辑完整
4. ✅ API层所有端点都有完整的异常处理
5. ✅ API层在try块之前提取并转换role（`.upper()`）
6. ✅ 公开端点无需认证，管理员端点使用`Depends(get_current_user)`
7. ✅ 所有响应使用`JSONResponse`
8. ✅ 所有错误响应使用`error_response`函数
9. ✅ 日志记录完整（INFO、WARNING、ERROR）
10. ✅ UUID在日志中脱敏（只记录前8位）

---

## 9. Phase1完成标准

Phase1（焦点图CRUD的Service和API）完成后，应该能够：

1. ✅ 公开访问焦点图列表（GET `/featured-content`）
2. ✅ 管理员查看所有焦点图（GET `/admin/featured-content`）
3. ✅ 管理员创建焦点图（POST `/admin/featured-content`）
4. ✅ 管理员更新焦点图（PATCH `/admin/featured-content/{id}`）
5. ✅ 管理员删除焦点图（DELETE `/admin/featured-content/{id}`）
6. ✅ 所有操作都有完整的权限检查和异常处理
7. ✅ 目标资源验证（room/session/topic/brand）

**下一步**: Phase2将实现首页API的复杂查询（多表JOIN、热度计算、主讲专家信息等）

---

**版本历史**:
- V1.0 (2026-01-18): Phase1 - 焦点图CRUD的Service和API初始版本
