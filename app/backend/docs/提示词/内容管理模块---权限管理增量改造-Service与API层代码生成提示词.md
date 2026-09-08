# 内容管理模块 - 权限管理增量改造 Service 与 API 层代码生成提示词

**版本**: V1.0
**创建日期**: 2026-01-12
**目标**: 指导 AI 对内容管理模块的 Service 和 API 层进行权限管理增量改造

---

## 1. 任务概述

**目标模块**: 内容管理模块（Content Management Module）

**需要更新的代码文件**:
- `app/services/content_management_service.py`
- `app/api/v1/endpoints/content_management.py`

**目标**: 将现有的内容管理模块 Service 和 API 层代码更新，使其符合通用权限管理策略（母版 Section 5.0.5）

---

## 2. 核心权限管理策略

### 2.1. 三层权限职责分工

**API 层 (Endpoint)**：负责 Authentication（认证）
- 使用 `get_current_user` 或 `get_current_user_optional` 获取用户信息
- 从 JWT Payload 中提取 `user_id` (UUID) 和 `role` (str)
- 将用户身份传递给 Service 层
- **不做权限判断**，不直接拒绝请求

**Service 层**：全权负责 Authorization（鉴权）
- 接收 `user_id: UUID` 和 `user_role: str` 参数
- 调用权限守卫函数（如 `_check_tag_visibility`、`_check_write_permission`）
- 根据权限检查结果决定是否允许访问
- 对于需要权限过滤的列表查询，将 `current_user_id` 和 `role` 传递给 CRUD 层

**CRUD 层**：负责在 SQL 层面应用权限过滤
- 接收 `current_user_id: Optional[UUID]` 和 `role: Optional[str]` 参数
- 在 WHERE 条件中应用权限过滤逻辑
- Admin 查询：无过滤
- Regular User 查询：`WHERE status='published'`
- Anonymous 查询：`WHERE status='published'`
- 业务筛选与权限过滤：AND 关系

### 2.2. 双轨鉴权模式

| 模式 | 行为 | 适用场景 | API 层依赖 |
|-------|------|---------|-------------|
| **Strict Auth**（强制鉴权） | 无 Token → 401<br>Token 无效 → 401 | 所有写操作（创建、修改、删除） | `get_current_user` |
| **Optional Auth**（可选鉴权） | 无 Token → None<br>Token 无效 → 401 | 所有读操作（列表、详情） | `get_current_user_optional` |

**关键原则**：
1. **严禁降级为匿名**：Token 无效时必须报 401，不能返回 `None` 降级为匿名用户。否则已登录用户在 Token 过期时会莫名其妙看不到自己的私有资源，导致前端状态错乱。
2. **职责清晰**：API 层只负责解析"你是谁"（User vs Anonymous），Service 层负责判定"你能看吗/你能改吗"。

### 2.3. 权限守卫函数（Service 层专用）

**类型 1：资源可见性检查**

```python
def _check_tag_visibility(
    self,
    tag: Tag,
    user_id: Optional[UUID],
    user_role: Optional[str]
) -> None:
    """
    标签可见性校验（基于 status 字段）
    
    权限判断流程：
        1. 公开标签（status='published'）：匿名用户可访问
        2. 已登录用户：可访问公开标签
        3. Admin：上帝视角，可访问所有标签（包括草稿和归档）
    
    Raises:
        TagNotFoundException(404): 标签不存在或无权访问（隐藏私有资源的存在性）
    """
    # 1. 公开标签：直接通过
    if tag.status == 'published':
        return
    
    # 2. 未登录用户：拒绝（返回404）
    if not user_id:
        raise TagNotFoundException("Tag not found")
    
    # 3. 管理员：上帝视角通过
    if user_role in ['ADMIN', 'SUPERADMIN']:
        return
    
    # 4. 其他用户：拒绝（返回404 隐藏存在性）
    raise TagNotFoundException("Tag not found")
```

**类型 2：写权限检查**

```python
def _check_write_permission(
    self,
    resource: Any,
    user_id: UUID,
    user_role: str
) -> None:
    """
    通用的写操作权限校验（修改、删除）
    
    权限判断流程：
        1. Admin（role in ['ADMIN', 'SUPERADMIN']）→ 通过
        2. Owner（resource.user_id == user_id）→ 通过
        3. 其他情况 → 403（已登录但无权）
    
    Raises:
        PermissionDeniedException(403): 权限不足
    """
    # 管理员：上帝视角通过
    if user_role in ['ADMIN', 'SUPERADMIN']:
        return
    
    # 资源创建者：通过
    if resource.user_id == user_id:
        return
    
    # 其他用户：拒绝（返回 403）
    raise PermissionDeniedException(
        "You don't have permission to modify this resource"
    )
```

**类型 3：管理员权限检查**

```python
def _check_admin_permission(
    self,
    user_role: str
) -> None:
    """
    管理员权限校验（用于写操作）
    
    权限判断流程：
        1. Admin（role in ['ADMIN', 'SUPERADMIN']）→ 通过
        2. 其他情况 → 403（权限不足）
    
    Raises:
        PermissionDeniedException(403): 权限不足
    """
    if user_role not in ['ADMIN', 'SUPERADMIN']:
        raise PermissionDeniedException(
            "需要管理员权限"
        )
```

---

## 3. 更新前检查清单

### 3.1. 文档结构检查

- [ ] 确认目标文件路径正确
- [ ] 确认模块名称正确（内容管理模块）
- [ ] 确认需要更新的代码文件（Service 和 API 层）

### 3.2. 现有代码分析

- [ ] 读取 `app/services/content_management_service.py` 现有代码
- [ ] 读取 `app/api/v1/endpoints/content_management.py` 现有代码
- [ ] 识别所有需要权限改造的 Service 方法
- [ ] 识别所有需要权限改造的 API 端点
- [ ] 检查现有的权限实现方式

### 3.3. 改造范围确认

- [ ] 确认 Service 方法数量（13+个）
- [ ] 确认 API 端点数量（13+个）
- [ ] 确认需要添加的权限参数（user_id, user_role）
- [ ] 确认需要实现的权限守卫函数

---

## 4. Service 层改造指南

### 4.1. 需要改造的 Service 方法清单

**所有需要改造的 Service 方法**：

1. **标签管理**（6个方法）：
   - `create_tag` - 创建标签
   - `update_tag` - 更新标签
   - `delete_tag` - 删除标签
   - `get_tag_detail` - 获取标签详情
   - `get_tags_paginated` - 获取标签列表（分页）
   - `get_tag_sessions` - 获取标签的场次列表

2. **分类管理**（6个方法）：
   - `create_category` - 创建分类
   - `update_category` - 更新分类
   - `delete_category` - 删除分类
   - `get_category_detail` - 获取分类详情
   - `get_categories_paginated` - 获取分类列表（分页）
   - `get_category_tags` - 获取分类的标签列表

3. **场次标签关联管理**（2个方法）：
   - `set_session_tags` - 为场次设置标签
   - `get_session_tags` - 获取场次的标签列表

**总计**: 14个 Service 方法

### 4.2. Service 方法改造规范

#### 4.2.1. 方法签名更新

**所有需要权限检查的 Service 方法，都必须更新方法签名**：

```python
# 改造前（旧签名）
async def get_tag_detail(
    self,
    tag_id: uuid.UUID,
    db: AsyncSession
) -> TagItem:
    """获取标签详情"""
    ...

# 改造后（新签名）
async def get_tag_detail(
    self,
    tag_id: uuid.UUID,
    user_id: Optional[uuid.UUID],  # ← 用户 ID（可选参数）
    user_role: Optional[str],  # ← 用户角色（可选参数）
    db: AsyncSession
) -> TagItem:
    """获取标签详情（带权限检查）"""
    ...
```

**改造规则**：
1. **写操作方法**（create, update, delete, set_session_tags）：
   - 必须添加 `user_id: uuid.UUID` 参数
   - 必须添加 `user_role: str` 参数
   - 参数类型：非可选（UUID 和 str）

2. **读操作方法**（get_tag_detail, get_tags_paginated, get_category_detail, get_categories_paginated）：
   - 必须添加 `user_id: Optional[uuid.UUID]` 参数
   - 必须添加 `user_role: Optional[str]` 参数
   - 参数类型：可选（Optional[UUID] 和 Optional[str]）

#### 4.2.2. 权限守卫函数实现

**在 ContentManagementService 类中实现以下权限守卫函数**：

```python
class ContentManagementService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    def _check_tag_visibility(
        self,
        tag: Tag,
        user_id: Optional[UUID],
        user_role: Optional[str]
    ) -> None:
        """
        标签可见性校验（基于 status 字段）
        """
        # 1. 公开标签：直接通过
        if tag.status == 'published':
            return
        
        # 2. 未登录用户：拒绝（返回404）
        if not user_id:
            raise TagNotFoundException("Tag not found")
        
        # 3. 管理员：上帝视角通过
        if user_role in ['ADMIN', 'SUPERADMIN']:
            return
        
        # 4. 其他用户：拒绝（返回404 隐藏存在性）
        raise TagNotFoundException("Tag not found")
    
    def _check_write_permission(
        self,
        resource: Any,
        user_id: UUID,
        user_role: str
    ) -> None:
        """
        通用的写操作权限校验
        """
        # 管理员：上帝视角通过
        if user_role in ['ADMIN', 'SUPERADMIN']:
            return
        
        # 资源创建者：通过
        if resource.user_id == user_id:
            return
        
        # 其他用户：拒绝（返回 403）
        raise PermissionDeniedException(
            "You don't have permission to modify this resource"
        )
    
    def _check_admin_permission(
        self,
        user_role: str
    ) -> None:
        """
        管理员权限校验（用于写操作）
        """
        if user_role not in ['ADMIN', 'SUPERADMIN']:
            raise PermissionDeniedException(
                "需要管理员权限"
            )
```

#### 4.2.3. 方法内部权限检查实现

**写操作方法的权限检查示例**：

```python
async def create_tag(
    self,
    user_id: uuid.UUID,
    user_role: str,
    tag_in: TagCreate,
    db: AsyncSession
) -> TagItem:
    """创建标签（仅管理员）"""
    
    # 权限检查：仅管理员可创建标签
    self._check_admin_permission(user_role=user_role)
    
    # 调用 CRUD 创建标签
    tag = await crud_tag.create(db=db, obj_in=tag_in)
    
    # 返回结果
    return tag
```

**读操作方法的权限检查示例**：

```python
async def get_tag_detail(
    self,
    tag_id: uuid.UUID,
    user_id: Optional[uuid.UUID],
    user_role: Optional[str],
    db: AsyncSession
) -> TagItem:
    """获取标签详情（公开资源）"""
    
    # 调用 CRUD 获取标签
    tag = await crud_tag.get(db=db, tag_id=tag_id)
    
    # 检查标签是否存在
    if not tag:
        raise TagNotFoundException("Tag not found")
    
    # 调用权限守卫函数
    self._check_tag_visibility(
        tag=tag,
        user_id=user_id,
        user_role=user_role
    )
    
    # 返回结果
    return tag
```

**列表查询方法的权限检查示例**：

```python
async def get_tags_paginated(
    self,
    user_id: Optional[uuid.UUID],
    user_role: Optional[str],
    page: int,
    size: int,
    search: Optional[str] = None,
    db: AsyncSession
) -> Tuple[List[TagItem], int]:
    """获取标签列表（分页）"""
    
    # 调用 CRUD 获取标签列表（带权限过滤）
    tags, total = await crud_tag.get_tags_paginated(
        db=db,
        current_user_id=user_id,
        role=user_role,
        page=page,
        size=size,
        search=search
    )
    
    # 返回结果
    return tags, total
```

---

## 5. API 层改造指南

### 5.1. 需要改造的 API 端点清单

**所有需要改造的 API 端点**：

1. **标签管理**（6个端点）：
   - `POST /api/v1/tags` - 创建标签
   - `PUT /api/v1/tags/{tag_id}` - 更新标签
   - `DELETE /api/v1/tags/{tag_id}` - 删除标签
   - `GET /api/v1/tags/{tag_id}` - 获取标签详情
   - `GET /api/v1/tags` - 获取标签列表（分页）
   - `GET /api/v1/tags/{tag_id}/sessions` - 获取标签的场次列表

2. **分类管理**（6个端点）：
   - `POST /api/v1/categories` - 创建分类
   - `PUT /api/v1/categories/{category_id}` - 更新分类
   - `DELETE /api/v1/categories/{category_id}` - 删除分类
   - `GET /api/v1/categories/{category_id}` - 获取分类详情
   - `GET /api/v1/categories` - 获取分类列表（分页）
   - `GET /api/v1/categories/{category_id}/tags` - 获取分类的标签列表

3. **场次标签关联管理**（2个端点）：
   - `POST /api/v1/sessions/{session_id}/tags` - 为场次设置标签
   - `GET /api/v1/sessions/{session_id}/tags` - 获取场次的标签列表

**总计**: 14个 API 端点

### 5.2. API 端点改造规范

#### 5.2.1. 端点认证方式更新

**所有需要改造的 API 端点，都必须更新认证方式**：

```python
# 改造前（旧方式）
@router.post("/")
async def create_tag(
    tag_in: TagCreate,
    current_user: User = Depends(get_current_user)  # ← 直接获取 User 模型
    db: AsyncSession = Depends(get_db)
) -> TagItem:
    """创建标签（旧方式）"""
    ...

# 改造后（新方式）
@router.post("/")
async def create_tag(
    tag_in: TagCreate,
    current_user: Dict = Depends(get_current_user),  # ← 使用 JWT Payload Dict
    db: AsyncSession = Depends(get_db)
) -> TagItem:
    """创建标签（新方式 - 带权限检查）"""
    # 解析用户身份
    user_id = uuid.UUID(current_user.get("user_id"))  # ← 从 user_id 字段获取用户ID（UUID字符串）
    user_role = current_user.get("role", "REGULAR").upper()  # ← 直接使用字符串
    
    # 调用 Service 层（传递 user_id 和 user_role）
    tag = await content_management_service.create_tag(
        db=db,
        user_id=user_id,
        user_role=user_role,
        tag_in=tag_in
    )
    
    return success_response(data=tag)
```

#### 5.2.2. 双轨鉴权模式应用

**Strict Auth 模式**（写操作）：

```python
# 写操作必须使用 Strict Auth
@router.post("/")
async def create_tag(
    tag_in: TagCreate,
    current_user: Dict = Depends(get_current_user),  # ← Strict Auth
    db: AsyncSession = Depends(get_db)
) -> TagItem:
    # 解析用户身份
    user_id = uuid.UUID(current_user.get("user_id"))
    user_role = current_user.get("role", "REGULAR").upper()
    
    # 调用 Service 层
    tag = await content_management_service.create_tag(
        db=db,
        user_id=user_id,
        user_role=user_role,
        tag_in=tag_in
    )
    
    return success_response(data=tag)
```

**Optional Auth 模式**（读操作）：

```python
# 读操作必须使用 Optional Auth
@router.get("/{tag_id}")
async def get_tag_detail(
    tag_id: str,
    current_user: Optional[Dict] = Depends(get_current_user_optional),  # ← Optional Auth
    db: AsyncSession = Depends(get_db)
) -> TagItem:
    # 解析用户身份
    user_id = uuid.UUID(current_user["user_id"]) if current_user else None
    user_role = current_user.get("role", "REGULAR").upper() if current_user else None
    
    # 调用 Service 层（传递 user_id 和 user_role）
    tag = await content_management_service.get_tag_detail(
        db=db,
        tag_id=uuid.UUID(tag_id),
        user_id=user_id,
        user_role=user_role
    )
    
    return success_response(data=tag)
```

#### 5.2.3. 异常处理更新

**所有 API 端点都必须更新异常处理**：

```python
from fastapi import HTTPException
from app.core.security import TagNotFoundException, PermissionDeniedException
from app.utils.response import success_response, error_response

@router.get("/{tag_id}")
async def get_tag_detail(
    tag_id: str,
    current_user: Optional[Dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
) -> TagItem:
    """获取标签详情"""
    
    # 解析用户身份
    user_id = uuid.UUID(current_user["user_id"]) if current_user else None
    user_role = current_user.get("role", "REGULAR").upper() if current_user else None
    
    try:
        # 调用 Service 层
        tag = await content_management_service.get_tag_detail(
            db=db,
            tag_id=uuid.UUID(tag_id),
            user_id=user_id,
            user_role=user_role
        )
        
        return success_response(data=tag)
    
    except TagNotFoundException as e:
        # 捕获 404 异常（资源不存在或无权访问）
        return JSONResponse(
            status_code=404,
            content=error_response(
                code=4004,
                message="Tag not found"
            )
        )
    
    except PermissionDeniedException as e:
        # 捕获 403 异常（权限不足）
        return JSONResponse(
            status_code=403,
            content=error_response(
                code=3003,
                message=e.message or "Permission denied"
            )
        )
    
    except Exception as e:
        # 捕获其他异常
        logger.error(f"获取标签详情失败: {type(e).__name__}")
        return JSONResponse(
            status_code=500,
            content=error_response(
                code=5000,
                message="Internal server error"
            )
        )
```

---

## 6. 改造后检查清单

### 6.1. Service 层改造后检查

**方法签名检查**：
- [ ] 所有写操作方法都添加了 `user_id: uuid.UUID` 和 `user_role: str` 参数
- [ ] 所有读操作方法都添加了 `user_id: Optional[uuid.UUID]` 和 `user_role: Optional[str]` 参数
- [ ] 参数类型定义正确（UUID vs Optional[UUID], str vs Optional[str]）

**权限守卫函数检查**：
- [ ] `_check_tag_visibility` 函数已实现
- [ ] `_check_category_visibility` 函数已实现
- [ ] `_check_write_permission` 函数已实现
- [ ] `_check_admin_permission` 函数已实现
- [ ] 权限守卫函数逻辑正确（公开资源直接通过、私密+未登录返回404、管理员上帝视角）
- [ ] 权限守卫函数调用位置正确（在调用 CRUD 之前）

**权限检查实现检查**：
- [ ] 写操作方法都调用了权限检查（仅管理员检查）
- [ ] 读操作方法都调用了权限守卫函数
- [ ] 列表查询方法都传递了权限参数给 CRUD 层
- [ ] 权限检查失败时抛出正确的异常（404 或 403）

**CRUD 层参数传递检查**：
- [ ] 需要权限过滤的列表查询方法都传递了 `current_user_id` 和 `role` 给 CRUD 层
- [ ] 参数名称和类型与 CRUD 层定义一致

### 6.2. API 层改造后检查

**认证方式检查**：
- [ ] 所有写操作端点都使用了 `Depends(get_current_user)`
- [ ] 所有读操作端点都使用了 `Depends(get_current_user_optional)`
- [ ] 没有使用 `Depends(require_admin)` 这类直接抛出 HTTPException 的依赖

**用户身份解析检查**：
- [ ] 所有端点都正确解析了 `user_id`（使用 `uuid.UUID(current_user.get("user_id"))`）
- [ ] 所有端点都正确解析了 `user_role`（使用 `current_user.get("role", "REGULAR").upper()`）
- [ ] Optional Auth 端点都正确处理了 `current_user` 为 `None` 的情况

**Service 层调用检查**：
- [ ] 所有端点都将 `user_id` 和 `user_role` 传递给 Service 层
- [ ] Service 层参数名称与类型一致（UUID vs Optional[UUID], str vs Optional[str]）

**异常处理检查**：
- [ ] 所有端点都捕获了 `TagNotFoundException` 并返回 404
- [ ] 所有端点都捕获了 `CategoryNotFoundException` 并返回 404
- [ ] 所有端点都捕获了 `PermissionDeniedException` 并返回 403
- [ ] 所有端点都捕获了通用异常并返回 500
- [ ] 错误响应使用了 `error_response()` 函数
- [ ] 成功响应使用了 `success_response()` 函数

**响应格式检查**：
- [ ] 所有成功响应都包含 `success_response(data=...)`
- [ ] 所有错误响应都包含 `JSONResponse(status_code=..., content=error_response(...))`

---

## 7. 最终检查清单

### 7.1. 通用检查

- [ ] 所有 14个 Service 方法都已更新
- [ ] 所有 14个 API 端点都已更新
- [ ] 权限守卫函数已实现（4个函数）
- [ ] 所有权限检查都已实现

### 7.2. 一致性检查

- [ ] 所有改造都与母版 Section 5.0.5 保持一致
- [ ] 权限守卫函数逻辑与母版一致
- [ ] 用户身份解析方式与母版一致
- [ ] 双轨鉴权模式应用正确
- [ ] 字符串比较方式一致（`if user_role not in ['ADMIN', 'SUPERADMIN']:`）

### 7.3. 无遗漏检查

- [ ] 没有遗漏任何 Service 方法
- [ ] 没有遗漏任何 API 端点
- [ ] 没有遗漏任何权限检查
- [ ] 没有遗漏任何异常处理

### 7.4. 无冲突检查

- [ ] 没有与现有业务逻辑冲突
- [ ] 没有改变方法的返回值结构
- [ ] 没有引入新的依赖
- [ ] 所有改造都是最小幅度修改

---

## 8. 使用说明

### 8.1. Cursor 使用说明

**改造代码时必须使用 Cursor 的 `@` 标记引用**：

```python
# 正确的引用方式
@app.crud.content_management  # ← 使用 @app.crud.content_management 引用 CRUD 文件
from app.services.content_management_service import ContentManagementService  # ← 使用 @app.services.content_management_service 引用 Service 文件

# 改造 Service 层时
from app.crud.content_management import (
    get_tag,
    create_tag,
    update_tag,
    # ← 使用 @app.crud.content_management 引用所有需要用到的 CRUD 函数
)

# 改造 API 层时
from app.services.content_management_service import ContentManagementService  # ← 使用 @app.services.content_management_service 引用 Service 文件
```

### 8.2. 读取现有代码

**改造前必须读取现有代码**：
1. 使用 `@app/services/content_management_service` 读取 `app/services/content_management_service.py`
2. 使用 `@app/api/v1/endpoints/content_management` 读取 `app/api/v1/endpoints/content_management.py`
3. 仔细分析现有方法签名和权限实现
4. 只修改权限相关的代码，不改变业务逻辑

### 8.3. 最小幅度修改原则

**改造时必须遵守的原则**：
1. 只添加或修改权限相关的代码
2. 不修改任何业务逻辑执行流程
3. 不删除或重命名任何现有方法
4. 不改变任何方法的返回值结构
5. 保持代码风格和结构一致

---

**文档版本**: V1.0
**创建日期**: 2026-01-12
**状态**: 准备就绪

