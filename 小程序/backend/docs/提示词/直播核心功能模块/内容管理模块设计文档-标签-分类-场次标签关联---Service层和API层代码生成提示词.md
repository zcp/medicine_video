# 内容管理模块 - Service层和API层代码生成提示词

**模块名称**: content_management  
**功能模块名称**: 内容管理模块设计文档-标签-分类-场次标签关联  
**目标文件**: 
- `backend/live_core_service/app/services/content_management_service.py`
- `backend/live_core_service/app/api/v1/endpoints/content_management.py`

**生成日期**: 2026-01-18  

---

## 1. 角色定义

你是一名精通Clean Architecture和FastAPI的资深Python后端架构师。你的任务是根据本提示词文档，生成内容管理模块的Service层和API层代码。

---

## 2. 核心要求

### 2.1. Service层职责

Service层是业务逻辑层，负责：
- ✅ 业务编排（调用多个CRUD函数）
- ✅ 权限检查（通过权限守卫函数）
- ✅ 业务验证（检查数据有效性）
- ✅ **批量验证**（对输入列表进行业务验证，详见下方说明）
- ✅ 事务控制（commit/rollback）
- ✅ 响应构造（将CRUD结果转换为Schema响应）
- ✅ 异常处理（转换为HTTP异常）
- ❌ 不负责数据库操作（由CRUD层处理）
- ❌ 不负责HTTP请求解析（由Endpoint层处理）

**🚨 [强制要求] 批量验证规范（最高优先级）**：

Service层负责对输入列表进行业务验证，**必须**在调用CRUD层之前完成所有验证：

1. **批量ID验证**：
   ```python
   # 示例：验证tag_ids列表中的所有ID是否存在
   tags_query = select(Tag).where(Tag.id.in_(request_data.tag_ids))
   result = await db.execute(tags_query)
   existing_tags = result.scalars().all()
   existing_tag_ids = {tag.id for tag in existing_tags}
   
   # 检查是否有不存在的ID
   missing_ids = set(request_data.tag_ids) - existing_tag_ids
   if missing_ids:
       raise InvalidParameterException(f"部分标签ID不存在: {missing_ids}")
   ```

2. **批量数据验证**：
   - **必须**在单个事务中完成所有验证
   - **必须**在验证失败时抛出明确的异常（如`InvalidParameterException`）
   - **必须**在验证通过后再调用CRUD层进行数据操作

3. **业务编排示例**：
   ```python
   # 1. 权限检查
   self._check_write_permission(role)
   
   # 2. 批量验证（在调用CRUD之前）
   tags_query = select(Tag).where(Tag.id.in_(request_data.tag_ids))
   result = await db.execute(tags_query)
   existing_tags = result.scalars().all()
   if len(existing_tags) != len(request_data.tag_ids):
       raise InvalidParameterException("部分标签ID不存在")
   
   # 3. 调用CRUD层
   tags = await set_session_tags(db, session_id, request_data.tag_ids, request_data.mode)
   
   # 4. 提交事务
   await db.commit()
   
   # 5. 构造响应
   return SessionTagsSetResponse(...)
   ```

### 2.2. API层职责

API层（Endpoint层）是HTTP端点层，负责：
- ✅ 请求解析（Path参数、Query参数、Body参数）
- ✅ 依赖注入（get_db, get_current_user等）
- ✅ 调用Service层方法
- ✅ 返回HTTP响应
- ❌ 不负责业务逻辑（由Service层处理）
- ❌ 不负责权限检查（由Service层处理）
- ❌ 不负责数据库操作（由CRUD层处理）

### 2.3. 关键原则

1. **权限检查在Service层**: 使用权限守卫函数（`_check_admin_permission`等）
2. **双轨鉴权模式**: 
   - Strict Auth: 写操作使用`Depends(get_current_user)`
   - Optional Auth: 读操作使用`Depends(get_current_user_optional)`
3. **404伪装机制**: 未授权资源返回404而非403
4. **响应标准化**: 所有响应包含`code`, `message`, `data`, `timestamp`
5. **日志脱敏**: UUID只记录前8位
6. **错误消息脱敏**: 不暴露内部实现细节

---

## 3. Schema摘要（来自实际代码）

### 3.1. Tags Schemas

- `TagCreate`: 创建标签请求（name, slug, description, is_active）
- `TagUpdate`: 更新标签请求（所有字段Optional）
- `TagItem`: 标签响应（id, name, slug, description, is_active, created_at, updated_at）
- `TagListResponse`: 标签列表响应（code, message, data: List[TagItem], timestamp）

### 3.2. Categories Schemas

- `CategoryCreate`: 创建分类请求（name, slug, icon, description, sort_order, is_active）
- `CategoryUpdate`: 更新分类请求（所有字段Optional）
- `CategoryItem`: 分类响应（id, name, slug, icon, description, sort_order, is_active, created_at, updated_at）
- `CategoryListResponse`: 分类列表响应（code, message, data: List[CategoryItem], timestamp）
- `PaginatedData[T]`: 通用分页数据（total, page, size, items）
- `CategoryAdminListResponse`: 分类管理员列表响应（code, message, data: PaginatedData[CategoryItem], timestamp）

### 3.3. Session_Tags Schemas

- `SessionTagsSetRequest`: 设置场次标签请求（tag_ids: List[UUID], mode: "replace"|"append"）
- `TagBriefItem`: 标签简要信息（id, name）
- `SessionTagsSetResponse`: 设置场次标签响应（code, message, data: dict, timestamp）
- `SessionTagsListResponse`: 场次标签列表响应（code, message, data: List[TagItem], timestamp）

---

## 4. Service层代码生成（ContentManagementService类）

### 4.1. 类定义

```python
class ContentManagementService:
    """内容管理Service层"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
```

### 4.2. 权限守卫函数（3个）

#### 方法1: `_check_admin_permission`

**函数签名**:
```python
def _check_admin_permission(self, role: Optional[str]) -> None
```

**功能**: 检查管理员权限

**实现逻辑**:
```python
def _check_admin_permission(self, role: Optional[str]) -> None:
    """
    检查管理员权限（admin或superadmin）
    
    Args:
        role: 用户角色
        
    Raises:
        PermissionDeniedException: 如果不是管理员
    """
    if role not in ['ADMIN', 'SUPERADMIN']:  # 🚨 必须使用大写
        self.logger.warning(f"权限不足: 需要管理员权限，当前角色={role}")
        raise PermissionDeniedException("需要管理员权限")
```

---

#### 方法2: `_check_write_permission`

**函数签名**:
```python
def _check_write_permission(self, role: Optional[str]) -> None
```

**功能**: 检查写权限

**实现逻辑**:
```python
    def _check_write_permission(self, role: Optional[str]) -> None:
        """
        检查写权限（REGULAR、admin或superadmin）
        
        Args:
            role: 用户角色
            
        Raises:
            PermissionDeniedException: 如果无写权限
        """
        if role not in ['REGULAR', 'ADMIN', 'SUPERADMIN']:  # 🚨 必须使用大写，使用REGULAR而非USER
            self.logger.warning(f"权限不足: 需要写权限，当前角色={role}")
            raise PermissionDeniedException("需要登录后才能执行此操作")
```

---

#### 方法3: `_check_tag_visibility`

**函数签名**:
```python
def _check_tag_visibility(
    self, 
    tag: Tag, 
    current_user_id: Optional[UUID], 
    role: Optional[str]
) -> None
```

**功能**: 检查标签可见性（404伪装）

**实现逻辑**:
```python
def _check_tag_visibility(
    self, 
    tag: Tag, 
    current_user_id: Optional[UUID], 
    role: Optional[str]
) -> None:
    """
    检查标签可见性
    
    如果标签is_active=False且用户不是管理员，抛出NotFoundException（404伪装）
    
    Args:
        tag: 标签对象
        current_user_id: 当前用户ID（可选）
        role: 用户角色（可选）
        
    Raises:
        NotFoundException: 如果标签不可见
    """
    if not tag.is_active and role not in ['ADMIN', 'SUPERADMIN']:  # 🚨 必须使用大写
        self.logger.warning(f"标签不可见: id={str(tag.id)[:8]}, is_active=False")
        raise NotFoundException("标签不存在")
```

---

### 4.3. Tags Service方法（4个）

#### 方法4: `get_tags_list`

**函数签名**:
```python
async def get_tags_list(
    self, 
    db: AsyncSession, 
    current_user_id: Optional[UUID], 
    role: Optional[str]
) -> TagListResponse
```

**功能**: 获取标签列表

**权限逻辑**: 
- 管理员可查询所有标签
- 普通用户只能查询is_active=True的标签

**执行流程**:
1. 确定is_active过滤条件：
   ```python
   if role in ['ADMIN', 'SUPERADMIN']:  # 🚨 必须使用大写
       is_active = None  # 管理员可查询所有
   else:
       is_active = True  # 普通用户只能查询启用的
   ```
2. 调用CRUD层：`tags = await get_tags(db, is_active, current_user_id, role)`
3. 构造响应：
   ```python
   return TagListResponse(
       code=200,
       message="success",
       data=[TagItem.model_validate(tag) for tag in tags],
       timestamp=datetime.now()
   )
   ```
4. 记录日志：`self.logger.info(f"查询标签列表成功，返回{len(tags)}条记录")`

---

#### 方法5: `create_tag`

**函数签名**:
```python
async def create_tag(
    self, 
    db: AsyncSession, 
    tag_data: TagCreate, 
    current_user_id: UUID, 
    role: str
) -> TagItem
```

**功能**: 创建标签

**权限检查**: `_check_admin_permission(role)`

**执行流程**:
1. 权限检查：`self._check_admin_permission(role)`
2. 调用CRUD层：`tag = await create_tag(db, tag_data)`
3. 提交事务：`await db.commit()`
4. 刷新对象：`await db.refresh(tag)`
5. 构造响应：`return TagItem.model_validate(tag)`
6. 记录日志：`self.logger.info(f"创建标签成功: id={str(tag.id)[:8]}, user_id={str(current_user_id)[:8]}")`
7. 异常处理：
   ```python
   try:
       # ... 执行创建
   except DatabaseIntegrityException as e:
       await db.rollback()
       raise  # 重新抛出，由Endpoint层处理
   except Exception as e:
       await db.rollback()
       self.logger.error(f"创建标签失败: {str(e)}")
       raise
   ```

---

#### 方法6: `update_tag`

**函数签名**:
```python
async def update_tag(
    self, 
    db: AsyncSession, 
    tag_id: UUID, 
    tag_data: TagUpdate, 
    current_user_id: UUID, 
    role: str
) -> TagItem
```

**功能**: 更新标签

**权限检查**: `_check_admin_permission(role)`

**执行流程**:
1. 权限检查：`self._check_admin_permission(role)`
2. 调用CRUD层：`tag = await update_tag(db, tag_id, tag_data)`
3. 404检查：
   ```python
   if tag is None:
       raise NotFoundException("标签不存在")
   ```
4. 提交事务：`await db.commit()`
5. 刷新对象：`await db.refresh(tag)`
6. 构造响应：`return TagItem.model_validate(tag)`
7. 记录日志和异常处理（同create_tag）

---

#### 方法7: `delete_tag`

**函数签名**:
```python
async def delete_tag(
    self, 
    db: AsyncSession, 
    tag_id: UUID, 
    current_user_id: UUID, 
    role: str
) -> dict
```

**功能**: 删除标签（软删除）

**权限检查**: `_check_admin_permission(role)`

**执行流程**:
1. 权限检查：`self._check_admin_permission(role)`
2. 调用CRUD层：`success = await delete_tag(db, tag_id)`
3. 404检查：
   ```python
   if not success:
       raise NotFoundException("标签不存在")
   ```
4. 提交事务：`await db.commit()`
5. 构造响应：`return {"message": "删除成功"}`
6. 记录日志和异常处理（同create_tag）

---

### 4.4. Categories Service方法（5个）

#### 方法8: `get_categories_list`

**函数签名**:
```python
async def get_categories_list(
    self, 
    db: AsyncSession, 
    current_user_id: Optional[UUID], 
    role: Optional[str]
) -> CategoryListResponse
```

**功能**: 获取分类列表（公开接口，不分页）

**权限逻辑**: 无需权限检查，自动过滤is_active=True

**执行流程**:
1. 调用CRUD层：`categories = await get_categories(db, current_user_id, role)`
2. 构造响应：
   ```python
   return CategoryListResponse(
       code=200,
       message="success",
       data=[CategoryItem.model_validate(category) for category in categories],
       timestamp=datetime.now()
   )
   ```
3. 记录日志：`self.logger.info(f"查询分类列表成功（公开），返回{len(categories)}条记录")`

---

#### 方法9: `get_categories_paginated`

**函数签名**:
```python
async def get_categories_paginated(
    self, 
    db: AsyncSession, 
    page: int, 
    size: int, 
    is_active: Optional[bool], 
    current_user_id: UUID, 
    role: str
) -> CategoryAdminListResponse
```

**功能**: 获取分类列表（管理员接口，分页）

**权限检查**: `_check_admin_permission(role)`

**执行流程**:
1. 权限检查：`self._check_admin_permission(role)`
2. 调用CRUD层：`categories, total = await get_categories_paginated(db, page, size, is_active, current_user_id, role)`
3. 构造响应：
   ```python
   return CategoryAdminListResponse(
       code=200,
       message="success",
       data=PaginatedData[CategoryItem](
           total=total,
           page=page,
           size=size,
           items=[CategoryItem.model_validate(category) for category in categories]
       ),
       timestamp=datetime.now()
   )
   ```
4. 记录日志：`self.logger.info(f"查询分类列表成功（Admin），page={page}, size={size}, total={total}")`

---

#### 方法10-12: `create_category`, `update_category`, `delete_category`

**实现逻辑**: 与Tags的create/update/delete方法类似，替换Tag为Category，tag_id为category_id即可。

---

### 4.5. Session_Tags Service方法（4个）

#### 方法13: `set_session_tags`

**函数签名**:
```python
async def set_session_tags(
    self, 
    db: AsyncSession, 
    session_id: UUID, 
    request_data: SessionTagsSetRequest, 
    current_user_id: UUID, 
    role: str
) -> SessionTagsSetResponse
```

**功能**: 为场次设置标签

**权限检查**: `_check_write_permission(role)`

**业务验证**:
1. 检查tag_ids是否存在（调用CRUD层查询标签）
2. 检查session_id是否存在（可选，根据业务需求）

**执行流程**:
1. 权限检查：`self._check_write_permission(role)`
2. 业务验证：
   ```python
   # 查询标签是否存在
   tags_query = select(Tag).where(Tag.id.in_(request_data.tag_ids))
   result = await db.execute(tags_query)
   existing_tags = result.scalars().all()
   
   if len(existing_tags) != len(request_data.tag_ids):
       raise InvalidParameterException("部分标签ID不存在")
   ```
3. 调用CRUD层：`tags = await set_session_tags(db, session_id, request_data.tag_ids, request_data.mode)`
4. 提交事务：`await db.commit()`
5. 构造响应：
   ```python
   return SessionTagsSetResponse(
       code=200,
       message="success",
       data={
           "session_id": str(session_id),
           "mode": request_data.mode,
           "tags": [TagBriefItem.model_validate(tag) for tag in tags]
       },
       timestamp=datetime.now()
   )
   ```
6. 记录日志和异常处理

---

#### 方法14: `get_session_tags`

**函数签名**:
```python
async def get_session_tags(
    self, 
    db: AsyncSession, 
    session_id: UUID, 
    current_user_id: Optional[UUID], 
    role: Optional[str]
) -> SessionTagsListResponse
```

**功能**: 获取场次标签列表

**权限逻辑**: 无需权限检查（公开接口）

**执行流程**:
1. 调用CRUD层：`tags = await get_tags_by_session_id(db, session_id)`
2. 构造响应：
   ```python
   return SessionTagsListResponse(
       code=200,
       message="success",
       data=[TagItem.model_validate(tag) for tag in tags],
       timestamp=datetime.now()
   )
   ```
3. 记录日志

---

#### 方法15-16: `get_sessions_by_tags`, `remove_session_tag`

**实现逻辑**: 
- `get_sessions_by_tags`: 无需权限检查，调用CRUD层，返回List[UUID]
- `remove_session_tag`: 需要写权限检查，调用CRUD层，返回{"message": "删除成功"}

---

## 5. API层代码生成（Endpoint函数）

### 5.0. 🚨 [强制要求] API端点实现强制模板（最高优先级）

**所有API端点必须遵循以下完整模板**：

```python
from fastapi import APIRouter, Depends, Query, Path
from fastapi.responses import JSONResponse
from app.exceptions import PermissionDeniedException, NotFoundException, InvalidParameterException
from app.core.response import success_response, error_response
import logging

logger = logging.getLogger(__name__)

@router.post("/tags", ...)
async def create_tag(
    tag_data: TagCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Any:
    """创建标签（Strict Auth + Admin）"""
    # 🚨 必须：在try块之前提取并转换role
    current_user_id = UUID(current_user["user_id"])
    role = current_user.get("role", "REGULAR").upper()  # ✅ 必须调用.upper()
    user_id_for_logging = str(current_user_id)[:8]
    
    try:
        # 调用Service层
        result = await service.create_tag(db, tag_data, current_user_id, role)
        return result  # Service层返回的响应对象
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: user_id={user_id_for_logging}, role={role}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message="权限不足")
        )
    except NotFoundException as e:
        logger.warning(f"资源不存在: user_id={user_id_for_logging}, error={str(e)}")
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
    except Exception as e:
        logger.error(f"创建标签异常: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )
```

**❌ 错误示例（禁止使用）**：
```python
# ❌ 错误1：缺少.upper()调用
role = current_user.get("role")  # ❌

# ❌ 错误2：缺少异常处理
return await service.create_tag(...)  # ❌ 直接返回，没有try-except

# ❌ 错误3：在try块内提取role
try:
    role = current_user.get("role")  # ❌ 应该在try之前提取

# ❌ 错误4：使用HTTPException
raise HTTPException(status_code=403, detail=str(e))  # ❌ 禁止使用
```

**✅ 正确示例（必须使用）**：
```python
# ✅ 正确：完整的端点实现
async def create_tag(...):
    # 🚨 必须在try之前提取user_id和role
    current_user_id = UUID(current_user["user_id"])
    role = current_user.get("role", "REGULAR").upper()  # ✅
    user_id_for_logging = str(current_user_id)[:8]
    
    try:
        result = await service.create_tag(db, tag_data, current_user_id, role)
        return result
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: user_id={user_id_for_logging}, role={role}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message="权限不足")
        )
    except NotFoundException as e:
        logger.warning(f"资源不存在: user_id={user_id_for_logging}, error={str(e)}")
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
    except Exception as e:
        logger.error(f"创建标签异常: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )
```

**🚨 强制检查清单（每个端点必须验证）**：
- [ ] 是否在try块之前提取了`user_id`和`role`？
- [ ] 是否调用了`.upper()`转换role为大写？
- [ ] 是否提取了`user_id_for_logging`？
- [ ] 是否添加了完整的异常处理（try-except）？
- [ ] 是否捕获了`PermissionDeniedException`并使用`JSONResponse`+`error_response()`返回403？
- [ ] 是否捕获了`NotFoundException`并使用`JSONResponse`+`error_response()`返回404？
- [ ] 是否捕获了`InvalidParameterException`并使用`JSONResponse`+`error_response()`返回400？
- [ ] 是否捕获了通用`Exception`并使用`JSONResponse`+`error_response()`返回500？
- [ ] 是否导入了`JSONResponse`和`error_response`？
- [ ] 是否禁止使用`raise HTTPException`？

### 5.1. Router定义

**🚨 重要：APIRouter定义严禁指定`prefix`，`prefix`必须在顶层`api/v1/api.py`中统一指定**：

```python
# ✅ 正确：在endpoints/content_management.py中
router = APIRouter(tags=["Content Management"])  # 不指定prefix
service = ContentManagementService()

# 在api/v1/api.py中统一指定prefix
api_router.include_router(
    content_management.router,
    prefix="/content",  # ✅ 正确：只包含模块路径，不包含/api/v1
)
# 最终路径：/api/v1/content/tags

# ❌ 错误：在endpoints/content_management.py中指定prefix
router = APIRouter(prefix="/content-management", tags=["Content Management"])  # ❌ 错误
```

### 5.1.1. URL拼接规范

**🚨 [强制要求] URL拼接规范（最高优先级）**：

1. **数据库存储规范**：
   - **必须**只存储相对路径（如`/images/avatar.jpg`），**禁止**存储完整URL（如`https://example.com/images/avatar.jpg`）
   - **必须**在API响应时动态拼接完整URL

2. **API响应URL拼接**：
   ```python
   from fastapi import Request
   
   @router.get("/categories/{category_id}")
   async def get_category_by_id(
       category_id: UUID,
       request: Request,  # ✅ 必须注入Request依赖
       db: AsyncSession = Depends(get_db),
       current_user: Optional[dict] = Depends(get_current_user_optional)
   ) -> CategoryItem:
       # 调用Service层
       category = await service.get_category_by_id(db, category_id, current_user_id, role)
       
       # 如果category.icon是相对路径，拼接完整URL
       if category.icon and not category.icon.startswith("http"):
           category.icon = str(request.base_url).rstrip("/") + category.icon
       
       return category
   ```

3. **Service层返回Schema时的URL处理**：
   - Service层**不应**处理URL拼接（保持业务逻辑层纯净）
   - URL拼接**必须**在API层完成，使用`Request`依赖获取`base_url`

### 5.1.2. 响应格式化规范

**🚨 [强制要求] 响应格式化规范（最高优先级）**：

1. **Service层返回Schema对象**：
   - Service层**必须**返回Pydantic Schema对象（如`TagListResponse`, `CategoryItem`）
   - **禁止**在Service层返回字典或ORM对象

2. **API层响应格式化**：
   ```python
   # ✅ 正确：Service层返回Schema对象，API层直接返回
   @router.get("/tags")
   async def get_tags(...) -> TagListResponse:
       result = await service.get_tags_list(db, current_user_id, role)
       return result  # ✅ 直接返回Schema对象
   
   # ✅ 正确：Service层返回Schema对象，需要转换为字典时使用model_dump()
   @router.get("/sessions/{session_id}/tags")
   async def get_session_tags(...):
       result = await service.get_session_tags(db, session_id, current_user_id, role)
       return success_response(data=result.model_dump())  # ✅ 使用model_dump()转换
   ```

3. **推荐使用辅助函数**（可选）：
   ```python
   # 推荐：为常用ORM对象定义格式化辅助函数
   def format_tag_response(tag: Tag) -> dict:
       """将Tag ORM对象格式化为字典"""
       return {
           "id": str(tag.id),
           "name": tag.name,
           "slug": tag.slug,
           "description": tag.description,
           "is_active": tag.is_active,
           "created_at": tag.created_at.isoformat(),
           "updated_at": tag.updated_at.isoformat()
       }
   ```

4. **禁止的做法**：
   ```python
   # ❌ 错误：在API层直接返回ORM对象
   return tag  # ❌ 禁止
   
   # ❌ 错误：在Service层返回字典
   return {"id": str(tag.id), "name": tag.name}  # ❌ 禁止
   
   # ❌ 错误：手动构造响应字典
   return {"code": 200, "data": {...}}  # ❌ 禁止，应使用Schema对象
   ```

### 5.2. Tags端点（4个）

#### 端点1: `GET /api/v1/tags`

**路由装饰器**:
```python
@router.get(
    "/tags",
    response_model=TagListResponse,
    summary="获取标签列表",
    description="获取所有标签列表，管理员可查询所有标签，普通用户只能查询启用的标签"
)
```

**函数签名**:
```python
async def get_tags(
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
) -> TagListResponse
```

**实现逻辑**:
```python
async def get_tags(
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
) -> TagListResponse:
    """获取标签列表（Public + Optional Auth）"""
    # 🚨 必须：在try块之前提取并转换role
    current_user_id = UUID(current_user["user_id"]) if current_user else None
    role = current_user.get("role", "REGULAR").upper() if current_user else None  # ✅ 必须调用.upper()
    user_id_for_logging = str(current_user_id)[:8] if current_user_id else "anonymous"
    
    try:
        return await service.get_tags_list(db, current_user_id, role)
    except Exception as e:
        logger.error(f"获取标签列表异常: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )
```

---

#### 端点2: `POST /api/v1/tags`

**路由装饰器**:
```python
@router.post(
    "/tags",
    response_model=TagItem,
    status_code=201,
    summary="创建标签",
    description="创建新标签，需要管理员权限"
)
```

**函数签名**:
```python
async def create_tag(
    tag_data: TagCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> TagItem
```

**实现逻辑**:
```python
async def create_tag(
    tag_data: TagCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> TagItem:
    """创建标签（Strict Auth + Admin）"""
    # 🚨 必须：在try块之前提取并转换role
    current_user_id = UUID(current_user["user_id"])
    role = current_user.get("role", "REGULAR").upper()  # ✅ 必须调用.upper()
    user_id_for_logging = str(current_user_id)[:8]
    
    try:
        return await service.create_tag(db, tag_data, current_user_id, role)
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: user_id={user_id_for_logging}, role={role}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message="权限不足")
        )
    except InvalidParameterException as e:
        logger.warning(f"参数验证失败: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message=str(e))
        )
    except Exception as e:
        logger.error(f"创建标签异常: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )
```

---

#### 端点3-4: `PUT /api/v1/tags/{tag_id}`, `DELETE /api/v1/tags/{tag_id}`

**实现逻辑**: 类似端点2，使用Strict Auth + Admin权限

---

### 5.3. Categories端点（6个）

#### 端点5: `GET /api/v1/categories`

**路由装饰器**:
```python
@router.get(
    "/categories",
    response_model=CategoryListResponse,
    summary="获取分类列表（公开接口）",
    description="获取所有启用的分类列表，按sort_order排序"
)
```

**函数签名**:
```python
async def get_categories(
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
) -> CategoryListResponse
```

**实现逻辑**: 类似Tags的get_tags

---

#### 端点6: `GET /api/v1/categories/admin`

**路由装饰器**:
```python
@router.get(
    "/categories/admin",
    response_model=CategoryAdminListResponse,
    summary="获取分类列表（管理员接口）",
    description="获取分类列表，支持分页和按is_active过滤，需要管理员权限"
)
```

**函数签名**:
```python
async def get_categories_admin(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    is_active: Optional[bool] = Query(None, description="是否启用（true/false/null）"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> CategoryAdminListResponse
```

**实现逻辑**:
```python
async def get_categories_admin(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    is_active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> CategoryAdminListResponse:
    """获取分类列表（Admin接口，分页）"""
    # 🚨 必须：在try块之前提取并转换role
    current_user_id = UUID(current_user["user_id"])
    role = current_user.get("role", "REGULAR").upper()  # ✅ 必须调用.upper()
    user_id_for_logging = str(current_user_id)[:8]
    
    try:
        return await service.get_categories_paginated(db, page, size, is_active, current_user_id, role)
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: user_id={user_id_for_logging}, role={role}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message="权限不足")
        )
    except NotFoundException as e:
        logger.warning(f"资源不存在: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在")
        )
    except Exception as e:
        logger.error(f"获取分类列表异常: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )
```

---

#### 端点7-10: 创建、更新、删除、查询单个分类

**实现逻辑**: 类似Tags端点，使用Strict Auth + Admin权限

---

### 5.4. Session_Tags端点（4个）

#### 端点11: `POST /api/v1/sessions/{session_id}/tags`

**路由装饰器**:
```python
@router.post(
    "/sessions/{session_id}/tags",
    response_model=SessionTagsSetResponse,
    summary="为场次设置标签",
    description="为指定场次设置标签，支持替换或追加模式，需要写权限"
)
```

**函数签名**:
```python
async def set_session_tags(
    session_id: UUID,
    request_data: SessionTagsSetRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> SessionTagsSetResponse
```

**实现逻辑**:
```python
async def set_session_tags(
    session_id: UUID,
    request_data: SessionTagsSetRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> SessionTagsSetResponse:
    """为场次设置标签（Strict Auth + Write）"""
    # 🚨 必须：在try块之前提取并转换role
    current_user_id = UUID(current_user["user_id"])
    role = current_user.get("role", "REGULAR").upper()  # ✅ 必须调用.upper()
    user_id_for_logging = str(current_user_id)[:8]
    
    try:
        return await service.set_session_tags(db, session_id, request_data, current_user_id, role)
    except NotFoundException as e:
        logger.warning(f"资源不存在: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在")
        )
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: user_id={user_id_for_logging}, role={role}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message="权限不足")
        )
    except InvalidParameterException as e:
        logger.warning(f"参数验证失败: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message=str(e))
        )
    except Exception as e:
        logger.error(f"为场次设置标签异常: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )
```

---

#### 端点12: `GET /api/v1/sessions/{session_id}/tags`

**路由装饰器**:
```python
@router.get(
    "/sessions/{session_id}/tags",
    response_model=SessionTagsListResponse,
    summary="获取场次标签列表",
    description="获取指定场次的所有启用标签"
)
```

**函数签名**:
```python
async def get_session_tags(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
) -> SessionTagsListResponse
```

**实现逻辑**: 类似Tags的get_tags，使用Optional Auth

---

#### 端点13-14: 根据标签查询场次、删除场次标签关联

**实现逻辑**: 
- 端点13: `GET /api/v1/tags/search/sessions?tag_ids=...&match_all=...`，使用Optional Auth
- 端点14: `DELETE /api/v1/sessions/{session_id}/tags/{tag_id}`，使用Strict Auth + Write权限

---

## 6. 导入清单

### 6.1. Service层导入

```python
from typing import List, Optional
from uuid import UUID
from datetime import datetime
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content_management import Tag, Category, SessionTag
from app.schemas.content_management import (
    TagCreate, TagUpdate, TagItem, TagListResponse,
    CategoryCreate, CategoryUpdate, CategoryItem, CategoryListResponse, CategoryAdminListResponse,
    SessionTagsSetRequest, SessionTagsSetResponse, SessionTagsListResponse,
    TagBriefItem, PaginatedData
)
from app.crud.content_management import (
    get_tags, create_tag, update_tag, delete_tag,
    get_categories, get_categories_paginated, create_category, update_category, delete_category, get_category_by_id,
    set_session_tags, get_tags_by_session_id, get_sessions_by_tags, remove_session_tag
)
from app.core.exceptions import (
    NotFoundException, PermissionDeniedException, DatabaseIntegrityException, InvalidParameterException
)

logger = logging.getLogger(__name__)
```

### 6.2. API层导入

**🚨 强制要求：必须导入JSONResponse、error_response、success_response，禁止使用HTTPException**：

```python
from typing import List, Optional
from uuid import UUID
import logging

from fastapi import APIRouter, Depends, Query, Path
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.deps import get_current_user, get_current_user_optional
from app.core.response import success_response, error_response
from app.exceptions import PermissionDeniedException, NotFoundException, InvalidParameterException
from app.schemas.content_management import (
    TagCreate, TagUpdate, TagItem, TagListResponse,
    CategoryCreate, CategoryUpdate, CategoryItem, CategoryListResponse, CategoryAdminListResponse,
    SessionTagsSetRequest, SessionTagsSetResponse, SessionTagsListResponse
)
from app.services.content_management_service import ContentManagementService

logger = logging.getLogger(__name__)

# 🚨 重要：APIRouter定义严禁指定prefix，prefix必须在顶层api/v1/api.py中统一指定
router = APIRouter(tags=["Content Management"])  # ✅ 正确：不指定prefix
service = ContentManagementService()
```

---

## 7. 文件结构模板

### 7.1. Service层文件结构

```python
"""
内容管理模块的Service层
负责业务逻辑编排、权限检查、事务控制
"""
# ... imports ...

logger = logging.getLogger(__name__)


class ContentManagementService:
    """内容管理Service层"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    # ========================================================================
    # 权限守卫函数
    # ========================================================================
    
    def _check_admin_permission(self, role: Optional[str]) -> None:
        """检查管理员权限"""
        # 实现...
    
    # ... 其他守卫函数
    
    # ========================================================================
    # Tags Service方法
    # ========================================================================
    
    async def get_tags_list(...) -> TagListResponse:
        """获取标签列表"""
        # 实现...
    
    # ... 其他Tags方法
    
    # ========================================================================
    # Categories Service方法
    # ========================================================================
    
    # ... 实现
    
    # ========================================================================
    # Session_Tags Service方法
    # ========================================================================
    
    # ... 实现
```

### 7.2. API层文件结构

```python
"""
内容管理模块的API端点
负责HTTP请求解析、依赖注入、调用Service层
"""
# ... imports ...

# 🚨 重要：APIRouter定义严禁指定prefix，prefix必须在顶层api/v1/api.py中统一指定
router = APIRouter(tags=["Content Management"])  # ✅ 正确：不指定prefix
service = ContentManagementService()


# ============================================================================
# Tags端点
# ============================================================================

@router.get("/tags", ...)
async def get_tags(...) -> TagListResponse:
    """获取标签列表"""
    # 实现...


# ... 其他Tags端点


# ============================================================================
# Categories端点
# ============================================================================

# ... 实现


# ============================================================================
# Session_Tags端点
# ============================================================================

# ... 实现
```

---

## 8. 关键约束和注意事项

1. **权限检查在Service层**: 使用`_check_admin_permission`等守卫函数
2. **双轨鉴权**: 写操作用`get_current_user`，读操作用`get_current_user_optional`
3. **404伪装**: 未授权资源返回NotFoundException而非PermissionDeniedException
4. **响应标准化**: 所有响应包含`code`, `message`, `data`, `timestamp`
5. **事务控制**: Service层负责commit/rollback
6. **日志脱敏**: UUID只记录前8位
7. **🚨 API层异常处理（强制要求，最高优先级）**：
   - **必须**在try块之前提取并转换role：`role = current_user.get("role", "REGULAR").upper()`
   - **必须**在try块之前提取`user_id_for_logging = str(current_user_id)[:8]`
   - **必须**添加完整的异常处理（try-except），捕获Service层抛出的异常并转换为`JSONResponse`
   - **必须**导入异常类：`from app.exceptions import PermissionDeniedException, NotFoundException, InvalidParameterException`
   - **必须**导入`JSONResponse`和`error_response`：`from fastapi.responses import JSONResponse`，`from app.core.response import error_response`
   - **禁止**使用`raise HTTPException`，**必须**使用`JSONResponse` + `error_response()`
   - **异常转换规则**：
     - `PermissionDeniedException` → `JSONResponse(status_code=403, content=error_response(code=3003, message="权限不足"))`
     - `NotFoundException` → `JSONResponse(status_code=404, content=error_response(code=2001, message="资源不存在"))`
     - `InvalidParameterException` → `JSONResponse(status_code=400, content=error_response(code=4001, message=str(e)))`
     - `Exception` → `JSONResponse(status_code=500, content=error_response(code=1002, message="内部服务器错误"))`
   - **必须**在异常处理中记录日志（使用`user_id_for_logging`）
8. **🚨 角色值大小写（强制要求）**：
   - **API层**：必须调用`.upper()`转换role为大写
   - **Service层**：必须使用大写`['ADMIN', 'SUPERADMIN']`或`['REGULAR', 'ADMIN', 'SUPERADMIN']`
   - **CRUD层**：必须使用大写`['ADMIN', 'SUPERADMIN']`进行角色检查
   - **禁止**使用小写或混合大小写

---

## 9. 执行指引

### 9.1. 生成顺序

1. **先生成Service层代码** (`content_management_service.py`)
   - 权限守卫函数
   - Tags Service方法
   - Categories Service方法
   - Session_Tags Service方法

2. **再生成API层代码** (`content_management.py`)
   - Tags端点
   - Categories端点
   - Session_Tags端点

### 9.2. 验证要求

生成代码后，请验证：
- ✅ Service层：所有16个方法都已生成
- ✅ API层：所有14个端点都已生成
- ✅ **API-Service对应关系验证**：
  * 对于每个API端点，验证Service层中是否有对应的Service方法（排除权限守卫函数如`_check_*`）
  * 对应规则：
    - `GET /resource` → `get_resources_list(...) -> ResourceListResponse` 或 `get_resources(...) -> ResourceListResponse`
    - `GET /resource/{id}` → `get_resource_by_id(...) -> ResourceItem`
    - `POST /resource` → `create_resource(...) -> ResourceItem`
    - `PUT /resource/{id}` → `update_resource(...) -> ResourceItem`
    - `DELETE /resource/{id}` → `delete_resource(...) -> dict`
    - 其他端点根据业务逻辑和命名约定确定对应关系
  * 如果发现API端点缺少对应的Service方法，**必须补充**Service方法
  * 如果发现Service方法缺少对应的API端点，检查是否为权限守卫函数（`_check_*`）或内部方法，否则需要说明原因
- ✅ 权限检查：所有写操作都有权限检查
- ✅ 双轨鉴权：写操作用Strict Auth，读操作用Optional Auth
- ✅ 响应构造：所有响应符合Schema定义
- ✅ 日志记录：所有操作记录INFO日志，UUID脱敏

---

**版本历史**:
- V1.0 (2026-01-18): 初始版本，基于模块特定母版生成


