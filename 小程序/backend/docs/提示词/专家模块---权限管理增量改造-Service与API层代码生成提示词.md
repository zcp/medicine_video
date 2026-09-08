# 专家模块 - 权限管理增量改造 Service 与 API 层代码生成提示词

**版本**: V1.0
**创建日期**: 2026-01-12
**目标**: 指导 AI 对专家模块的 Service 和 API 层进行权限管理增量改造

---

## 1. 任务概述

**目标模块**: 专家模块（Expert Module）

**需要更新的代码文件**:
- `app/services/expert_service.py`
- `app/api/v1/endpoints/experts.py`

**目标**: 将现有的专家模块 Service 和 API 层代码更新，使其符合通用权限管理策略（母版 Section 5.0.5）

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
- 调用权限守卫函数（如 `_check_expert_visibility`、`_check_write_permission`）
- 根据权限检查结果决定是否允许访问
- 对于需要权限过滤的列表查询，将 `current_user_id` 和 `role` 传递给 CRUD 层

**CRUD 层**：负责在 SQL 层面应用权限过滤
- 接收 `current_user_id: Optional[UUID]` 和 `role: Optional[str]` 参数
- 在 WHERE 条件中应用权限过滤逻辑
- Admin 查询：无过滤
- Regular User 查询：`WHERE (is_active=True OR (is_active=False AND user_id=current_user_id))`
- Anonymous 查询：`WHERE is_active=True`
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
def _check_expert_visibility(
    self,
    expert: Expert,
    user_id: Optional[UUID],
    user_role: Optional[str]
) -> None:
    """
    专家可见性校验（基于 is_active 字段）
    
    权限判断流程：
        1. 公开专家（is_active=True）：匿名用户可访问
        2. 已登录用户：可访问公开+已停用专家
        3. Admin：上帝视角，可访问所有专家（包括已停用专家）
    
    Raises:
        ExpertNotFoundException(404): 专家不存在或无权访问（隐藏私有资源的存在性）
    """
    # 1. 公开专家：直接通过
    if expert.is_active:
        return
    
    # 2. 已停用专家且未登录：拒绝（返回404）
    if not user_id:
        raise ExpertNotFoundException("Expert not found")
    
    # 3. 管理员：上帝视角通过
    if user_role in ['ADMIN', 'SUPERADMIN']:
        return
    
    # 4. 专家创建者：通过
    if expert.user_id == user_id:
        return
    
    # 5. 其他用户：拒绝（返回404 隐藏存在性）
    raise ExpertNotFoundException("Expert not found")
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

### 2.4. 404 伪装机制

**关键原则**：
对于无权访问的私有资源，必须抛出 `NotFoundException`（404），而非 `PermissionDeniedException`（403）。

**原因**：
- 如果返回 403，攻击者可以通过遍历 ID，根据返回码（404 vs 403）判断哪些 ID 是真实存在的私密资源。
- 返回 404 可以隐藏资源的存在性，提高安全性。

**实现示例**：
```python
# ❌ 错误：返回 403 暴露资源存在性
if not expert.is_active and not user.is_admin:
    raise PermissionDeniedException("无权访问")  # 返回 403，攻击者可以推断出专家ID存在

# ✅ 正确：返回 404 伪装资源不存在
if not expert.is_active and not user.is_admin:
    raise ExpertNotFoundException("Expert not found")  # 返回 404，攻击者无法推断出专家ID是否存在
```

---

## 3. 更新前检查清单

### 3.1. 文档结构检查

- [ ] 确认目标文件路径正确
- [ ] 确认模块名称正确（专家模块）
- [ ] 确认需要更新的代码文件（Service 和 API 层）

### 3.2. 现有代码分析

- [ ] 读取 `app/services/expert_service.py` 现有代码
- [ ] 读取 `app/api/v1/endpoints/experts.py` 现有代码
- [ ] 识别所有需要权限改造的 Service 方法
- [ ] 识别所有需要权限改造的 API 端点
- [ ] 检查现有的权限实现方式

### 3.3. 改造范围确认

- [ ] 确认 Service 方法数量（13个）
- [ ] 确认 API 端点数量（15个）
- [ ] 确认需要添加的权限参数（user_id, user_role）
- [ ] 确认需要实现的权限守卫函数

---

## 4. Service 层改造指南

### 4.1. 需要改造的 Service 方法清单

**所有需要改造的 Service 方法**：

1. **专家信息管理**（8个方法）：
   - `create_expert` - 创建专家
   - `update_expert` - 更新专家
   - `delete_expert` - 删除专家（软删除）
   - `get_expert_detail` - 获取专家详情
   - `get_experts_paginated` - 获取专家列表（分页）
   - `get_featured_experts` - 获取首页推荐专家列表
   - `set_expert_featured` - 设置专家为推荐
   - `unset_expert_featured` - 取消专家推荐

2. **专家关注功能**（5个方法）：
   - `follow_expert` - 关注专家
   - `unfollow_expert` - 取消关注
   - `get_followed_experts_paginated` - 获取关注的专家列表（分页）
   - `is_expert_followed` - 检查是否已关注
   - `get_followed_experts_live_status` - 批量获取关注专家的直播状态

3. **场次专家关联功能**（2个方法）：
   - `set_session_experts` - 为场次设置专家
   - `get_session_experts` - 获取场次的专家列表

**总计**: 15个 Service 方法

### 4.2. Service 方法改造规范

#### 4.2.1. 方法签名更新

**所有需要权限检查的 Service 方法，都必须更新方法签名**：

```python
# 改造前（旧签名）
async def get_expert_detail(
    self,
    expert_id: uuid.UUID,
    db: AsyncSession
) -> ExpertItem:
    """获取专家详情"""
    ...

# 改造后（新签名）
async def get_expert_detail(
    self,
    expert_id: uuid.UUID,
    user_id: uuid.UUID,  # ← 新增：用户 ID（必选参数）
    user_role: str,  # ← 新增：用户角色（必选参数）
    db: AsyncSession
) -> ExpertItem:
    """获取专家详情（带权限检查）"""
    ...
```

**改造规则**：
1. **写操作方法**（create, update, delete, set_featured, unset_featured）：
   - 必须添加 `user_id: uuid.UUID` 参数
   - 必须添加 `user_role: str` 参数
   - 参数类型：`user_id` 是非可选的（UUID）
   - 参数类型：`user_role` 是非可选的（str）

2. **读操作方法**（get_expert_detail, get_experts_paginated, get_featured_experts, is_expert_followed）：
   - 必须添加 `user_id: Optional[uuid.UUID]` 参数
   - 必须添加 `user_role: Optional[str]` 参数
   - 参数类型：`user_id` 是可选的（Optional[UUID]）
   - 参数类型：`user_role` 是可选的（Optional[str]）

3. **私有资源读操作方法**（get_followed_experts_paginated, get_followed_experts_live_status）：
   - 必须添加 `user_id: uuid.UUID` 参数（必选）
   - 必须添加 `user_role: str` 参数（必选）
   - 参数类型：`user_id` 是非可选的（UUID）
   - 参数类型：`user_role` 是非可选的（str）

#### 4.2.2. 权限守卫函数实现

**在 ExpertService 类中实现以下权限守卫函数**：

```python
class ExpertService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    def _check_expert_visibility(
        self,
        expert: Expert,
        user_id: Optional[UUID],
        user_role: Optional[str]
    ) -> None:
        """
        专家可见性校验（基于 is_active 字段）
        """
        # 1. 公开专家：直接通过
        if expert.is_active:
            return
        
        # 2. 已停用专家且未登录：拒绝（返回404）
        if not user_id:
            raise ExpertNotFoundException("Expert not found")
        
        # 3. 管理员：上帝视角通过
        if user_role in ['ADMIN', 'SUPERADMIN']:
            return
        
        # 4. 专家创建者：通过
        if expert.user_id == user_id:
            return
        
        # 5. 其他用户：拒绝（返回404 隐藏存在性）
        raise ExpertNotFoundException("Expert not found")
    
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
```

#### 4.2.3. 方法内部权限检查实现

**写操作方法的权限检查示例**：

```python
async def create_expert(
    self,
    user_id: uuid.UUID,
    user_role: str,
    expert_in: ExpertCreate,
    db: AsyncSession
) -> ExpertItem:
    """创建专家（仅管理员）"""
    
    # 权限检查：仅管理员可创建专家
    if user_role not in ['ADMIN', 'SUPERADMIN']:
        raise PermissionDeniedException(
            "权限不足，需要管理员权限"
        )
    
    # 调用 CRUD 创建专家
    expert = await crud_expert.create(db=db, obj_in=expert_in)
    
    # 返回结果
    return expert
```

**读操作方法的权限检查示例**：

```python
async def get_expert_detail(
    self,
    expert_id: uuid.UUID,
    user_id: Optional[uuid.UUID],
    user_role: Optional[str],
    db: AsyncSession
) -> ExpertItem:
    """获取专家详情（公开资源）"""
    
    # 调用 CRUD 获取专家
    expert = await crud_expert.get(db=db, expert_id=expert_id)
    
    # 检查专家是否存在
    if not expert:
        raise ExpertNotFoundException("Expert not found")
    
    # 调用权限守卫函数
    self._check_expert_visibility(
        expert=expert,
        user_id=user_id,
        user_role=user_role
    )
    
    # 返回结果
    return expert
```

**私有资源读操作方法的权限检查示例**：

```python
async def get_followed_experts_paginated(
    self,
    user_id: uuid.UUID,
    user_role: str,
    page: int,
    size: int,
    db: AsyncSession
) -> Tuple[List[ExpertItem], int]:
    """获取关注的专家列表（仅当前用户可访问）"""
    
    # 调用 CRUD 获取关注的专家列表（带权限过滤）
    experts, total = await crud_expert.get_followed_experts_paginated(
        db=db,
        current_user_id=user_id,
        role=user_role,
        page=page,
        size=size
    )
    
    # 返回结果
    return experts, total
```

---

## 5. API 层改造指南

### 5.1. 需要改造的 API 端点清单

**所有需要改造的 API 端点**：

1. **专家信息管理**（8个端点）：
   - `POST /api/v1/experts` - 创建专家
   - `PUT /api/v1/experts/{expert_id}` - 更新专家
   - `DELETE /api/v1/experts/{expert_id}` - 删除专家
   - `GET /api/v1/experts/{expert_id}` - 获取专家详情
   - `GET /api/v1/experts` - 获取专家列表（分页）
   - `GET /api/v1/featured-experts` - 获取首页推荐专家列表
   - `POST /api/v1/experts/{expert_id}/set-featured` - 设置专家为推荐
   - `DELETE /api/v1/experts/{expert_id}/set-featured` - 取消专家推荐

2. **专家关注功能**（5个端点）：
   - `POST /api/v1/experts/{expert_id}/follow` - 关注专家
   - `DELETE /api/v1/experts/{expert_id}/follow` - 取消关注
   - `GET /api/v1/experts/followed` - 获取关注的专家列表（分页）
   - `GET /api/v1/experts/{expert_id}/is-followed` - 检查是否已关注
   - `POST /api/v1/experts/followed/live-status` - 批量获取关注专家的直播状态

3. **场次专家关联功能**（2个端点）：
   - `POST /api/v1/sessions/{session_id}/experts` - 为场次设置专家
   - `GET /api/v1/sessions/{session_id}/experts` - 获取场次的专家列表

**总计**: 15个 API 端点

### 5.2. API 端点改造规范

#### 5.2.1. 端点认证方式更新

**所有需要改造的 API 端点，都必须更新认证方式**：

```python
# 改造前（旧方式）
@router.post("/{expert_id}")
async def create_expert(
    expert_id: str,
    expert_in: ExpertCreate,
    current_user: User = Depends(get_current_user)  # ← 直接获取 User 模型
    db: AsyncSession = Depends(get_db)
) -> ExpertItem:
    """创建专家（旧方式）"""
    ...

# 改造后（新方式）
@router.post("/")
async def create_expert(
    expert_in: ExpertCreate,
    current_user: Dict = Depends(get_current_user),  # ← 使用 JWT Payload Dict
    db: AsyncSession = Depends(get_db)
) -> ExpertItem:
    """创建专家（新方式 - 带权限检查）"""
    # 解析用户身份
    user_id = uuid.UUID(current_user.get("user_id"))  # ← 从 user_id 字段获取用户ID（UUID字符串）
    user_role = current_user.get("role", "REGULAR").upper()  # ← 直接使用字符串
    
    # 调用 Service 层（传递 user_id 和 user_role）
    expert = await expert_service.create_expert(
        db=db,
        user_id=user_id,
        user_role=user_role,
        expert_in=expert_in
    )
    
    return success_response(data=expert)
```

#### 5.2.2. 双轨鉴权模式应用

**Strict Auth 模式**（写操作）：

```python
# 写操作必须使用 Strict Auth
@router.post("/")
async def create_expert(
    expert_in: ExpertCreate,
    current_user: Dict = Depends(get_current_user),  # ← Strict Auth
    db: AsyncSession = Depends(get_db)
) -> ExpertItem:
    # 解析用户身份
    user_id = uuid.UUID(current_user.get("user_id"))
    user_role = current_user.get("role", "REGULAR").upper()
    
    # 调用 Service 层
    expert = await expert_service.create_expert(
        db=db,
        user_id=user_id,
        user_role=user_role,
        expert_in=expert_in
    )
    
    return success_response(data=expert)
```

**Optional Auth 模式**（读操作）：

```python
# 读操作必须使用 Optional Auth
@router.get("/{expert_id}")
async def get_expert_detail(
    expert_id: str,
    current_user: Optional[Dict] = Depends(get_current_user_optional),  # ← Optional Auth
    db: AsyncSession = Depends(get_db)
) -> ExpertItem:
    # 解析用户身份
    user_id = uuid.UUID(current_user["user_id"]) if current_user else None
    user_role = current_user.get("role", "REGULAR").upper() if current_user else None
    
    # 调用 Service 层（传递 user_id 和 user_role）
    expert = await expert_service.get_expert_detail(
        db=db,
        expert_id=uuid.UUID(expert_id),
        user_id=user_id,
        user_role=user_role
    )
    
    return success_response(data=expert)
```

#### 5.2.3. 异常处理更新

**所有 API 端点都必须更新异常处理**：

```python
from fastapi import HTTPException
from app.core.security import ExpertNotFoundException, PermissionDeniedException
from app.utils.response import success_response, error_response

@router.get("/{expert_id}")
async def get_expert_detail(
    expert_id: str,
    current_user: Optional[Dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
) -> ExpertItem:
    """获取专家详情"""
    
    # 解析用户身份
    user_id = uuid.UUID(current_user["user_id"]) if current_user else None
    user_role = current_user.get("role", "REGULAR").upper() if current_user else None
    
    try:
        # 调用 Service 层
        expert = await expert_service.get_expert_detail(
            db=db,
            expert_id=uuid.UUID(expert_id),
            user_id=user_id,
            user_role=user_role
        )
        
        return success_response(data=expert)
    
    except ExpertNotFoundException as e:
        # 捕获 404 异常（资源不存在或无权访问）
        return JSONResponse(
            status_code=404,
            content=error_response(
                code=4004,
                message="Expert not found"
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
        logger.error(f"获取专家详情失败: {type(e).__name__}")
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
- [ ] 所有私有资源读操作方法都添加了 `user_id: uuid.UUID` 和 `user_role: str` 参数（非可选）
- [ ] 参数类型定义正确（UUID vs Optional[UUID], str vs Optional[str]）

**权限守卫函数检查**：
- [ ] `_check_expert_visibility` 函数已实现
- [ ] `_check_write_permission` 函数已实现
- [ ] 权限守卫函数逻辑正确（公开专家直接通过、已停用+未登录返回404、管理员上帝视角）
- [ ] 权限守卫函数调用位置正确（在调用 CRUD 之前）

**权限检查实现检查**：
- [ ] 写操作方法都调用了权限检查（仅管理员检查）
- [ ] 读操作方法都调用了权限守卫函数
- [ ] 私有资源读操作方法都调用了权限守卫函数
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
- [ ] 所有端点都捕获了 `ExpertNotFoundException` 并返回 404
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

- [ ] 所有 15个 Service 方法都已更新
- [ ] 所有 15个 API 端点都已更新
- [ ] 权限守卫函数已实现（2个函数）
- [ ] 404 伪装机制已实现
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
@app.crud.expert  # ← 使用 @app.crud.expert 引用 CRUD 文件
from app.services.expert_service import ExpertService  # ← 使用 @app.services.expert_service 引用 Service 文件

# 改造 Service 层时
from app.crud.expert import (
    get_expert,
    create_expert,
    update_expert,
    # ← 使用 @app.crud.expert 引用所有需要用到的 CRUD 函数
)

# 改造 API 层时
from app.services.expert_service import ExpertService  # ← 使用 @app.services.expert_service 引用 Service 文件
```

### 8.2. 读取现有代码

**改造前必须读取现有代码**：
1. 使用 `@app/services.expert_service` 读取 `app/services/expert_service.py`
2. 使用 `@app.api.v1.endpoints.experts` 读取 `app/api/v1/endpoints/experts.py`
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

