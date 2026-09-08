# 专家模块 - Service层和API层代码生成提示词

**模块名称**: experts  
**功能模块名称**: 专家模块设计文档-专家信息-专家关注  
**目标文件**: 
- `backend/live_core_service/app/services/expert_service.py`
- `backend/live_core_service/app/api/v1/endpoints/experts.py`

**生成日期**: 2026-01-18  

---

## 1. 角色定义

你是一名精通Clean Architecture和FastAPI的资深Python后端架构师。你的任务是根据本提示词文档，生成专家模块的Service层和API层代码。

---

## 2. 核心要求

### 2.1. Service层职责

Service层是业务逻辑层，负责：
- ✅ 业务编排（调用多个CRUD函数）
- ✅ 权限检查（通过权限守卫函数）
- ✅ 业务验证（检查数据有效性）
- ✅ 事务控制（commit/rollback）
- ✅ 响应构造（将CRUD结果转换为Schema响应）
- ✅ 异常处理（转换为HTTP异常）
- ❌ 不负责数据库操作（由CRUD层处理）
- ❌ 不负责HTTP请求解析（由Endpoint层处理）

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
7. **安全异步异常处理**: 在`try`块之前提取用于日志的变量

---

## 3. 项目结构与上下文信息

**项目目录结构**:
```
app/
├── models/          # SQLAlchemy 模型（数据层）
│   ├── __init__.py
│   ├── experts.py  # ✅ 已生成的专家模块模型
│   └── ...
├── schemas/         # Pydantic Schema（数据验证层）
│   ├── __init__.py
│   ├── experts.py  # ✅ 已生成的专家模块Schema
│   └── ...
├── crud/            # CRUD 层（数据访问层）
│   ├── __init__.py
│   ├── experts.py  # ✅ 已生成的专家模块CRUD
│   └── ...
├── services/        # Service 层（业务逻辑层）
│   ├── __init__.py
│   ├── expert_service.py  # 📋 待生成的专家模块Service
│   ├── topic_service.py  # 参考：专题模块Service（app/services/topic_service.py）
│   └── ...
└── api/             # API 层（HTTP端点层）
    └── v1/
        ├── api.py      # 📋 需要更新路由注册
        ├── endpoints/
        │   ├── __init__.py
        │   ├── experts.py  # 📋 待生成的专家模块端点
        │   ├── topic.py  # 参考：专题模块端点（app/api/v1/endpoints/topic.py）
        │   └── ...
```

**文件命名规范**:
- Service文件: `expert_service.py`（注意：单数形式）
- Endpoint文件: `experts.py`

**导入路径规范**:
- CRUD导入: `from app.crud.experts import (所有CRUD函数)`
- Service导入: `from app.services.expert_service import ExpertService`
- Schema导入: `from app.schemas.experts import ExpertCreate, ExpertUpdate, ExpertItem, ...`

**现有代码参考**:
- 专题模块Service: `app/services/topic_service.py`（可作为代码风格和结构参考）
- 专题模块Endpoint: `app/api/v1/endpoints/topic.py`（可作为代码风格和结构参考）

---

## 4. Schema摘要（来自实际代码）

**重要提示**: 以下Schema定义引用自已生成的代码：`backend/live_core_service/app/schemas/experts.py`

**执行者指令**: 
1. 使用 `read_file()` 工具读取 `backend/live_core_service/app/schemas/experts.py` 文件
2. 提取所有Schema类的字段定义
3. 识别嵌套结构（如 `data` 字典包含业务数据）
4. 记录必需字段、可选字段、默认值

### 4.1. 专家信息Schemas

- `ExpertBase`: 专家基础Schema（name, title, hospital, department, expertise_areas, bio, avatar_url）
- `ExpertCreate`: 创建专家请求（继承ExpertBase，添加user_id, is_featured, sort_order, contact_info）
- `ExpertUpdate`: 更新专家请求（所有字段Optional，部分更新）
- `ExpertItem`: 专家响应（继承ExpertBase，添加id, user_id, is_featured, sort_order, created_at, updated_at）
- `FeaturedExpertItem`: 首页推荐专家简要Schema（id, name, title, hospital, avatar_url）

### 4.2. 专家关注Schemas

- `ExpertFollowRequest`: 关注专家请求（expert_id）
- `ExpertFollowResponse`: 关注专家响应（code, message, data, timestamp）
- `FollowedExpertItem`: 关注的专家响应（expert_id, name, title, hospital, avatar_url, subscribed_at, live_status）
- `FollowedExpertsResponse`: 关注列表响应（code, message, data: List[FollowedExpertItem], timestamp）

### 4.3. 场次专家关联Schemas

- `SessionExpertItem`: 场次专家关联信息（id, name, title, hospital, avatar_url, role, sort_order）

---

## 5. Service层代码生成（ExpertService类）

### 5.1. 类定义

```python
class ExpertService:
    """专家模块Service层"""
    
    def __init__(self, db: AsyncSession):
        """
        初始化Service，存储数据库会话
        
        Args:
            db: 数据库会话对象
        """
        self.db = db
        self.logger = logging.getLogger(__name__)
```

### 5.2. 🚨 [强制要求] 批量验证规范（最高优先级）

**Service层负责对输入列表进行业务验证**：

* **必须**在Service层方法中对输入列表（如 `expert_ids`、`tag_ids`）进行业务验证
* **必须**检查列表长度限制（如 `len(expert_ids) > 100` 时抛出异常）
* **必须**检查列表中的每个元素是否有效（如检查专家是否存在）
* **必须**在调用CRUD层之前完成所有批量验证

**✅ 正确示例**：
```python
async def set_session_experts(
    self,
    session_id: uuid.UUID,
    expert_data_list: List[Dict[str, Any]],
    current_user_id: uuid.UUID,
    role: str
) -> Dict[str, Any]:
    """为场次设置专家列表"""
    # 1. 批量验证：检查列表长度
    if len(expert_data_list) > 100:
        raise InvalidParameterException("专家数量不能超过100个", code=4001)
    
    # 2. 批量验证：检查专家是否存在
    expert_ids = [data["expert_id"] for data in expert_data_list]
    for expert_id in expert_ids:
        expert = await crud.get_expert(self.db, expert_id)
        if expert is None:
            raise InvalidParameterException(f"专家不存在: {expert_id}", code=2001)
    
    # 3. 批量验证：检查角色是否有效
    valid_roles = ["主讲", "主持", "嘉宾"]
    for data in expert_data_list:
        if data["role"] not in valid_roles:
            raise InvalidParameterException(f"无效的角色: {data['role']}", code=4001)
    
    # 4. 验证通过后，调用CRUD层
    session_experts = await crud.set_session_experts(self.db, session_id, expert_data_list)
    # ...
```

**❌ 错误示例（禁止使用）**：
```python
# ❌ 错误：没有批量验证，直接调用CRUD层
async def set_session_experts(...):
    session_experts = await crud.set_session_experts(self.db, session_id, expert_data_list)
    # 缺少批量验证，可能导致数据库错误
```

---

### 5.3. 权限守卫函数（3个）

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
    检查写权限（user、admin或superadmin）
    
    Args:
        role: 用户角色
        
    Raises:
        PermissionDeniedException: 如果无写权限
    """
    if role not in ['REGULAR', 'ADMIN', 'SUPERADMIN']:  # 🚨 必须使用大写，使用REGULAR而非user
        self.logger.warning(f"权限不足: 需要写权限，当前角色={role}")
        raise PermissionDeniedException("需要登录后才能执行此操作")
```

---

#### 方法3: `_check_expert_visibility`

**函数签名**:
```python
def _check_expert_visibility(
    self, 
    expert: Expert, 
    current_user_id: Optional[UUID], 
    role: Optional[str]
) -> None
```

**功能**: 检查专家可见性（404伪装）

**实现逻辑**:
```python
def _check_expert_visibility(
    self, 
    expert: Expert, 
    current_user_id: Optional[UUID], 
    role: Optional[str]
) -> None:
    """
    检查专家可见性
    
    如果专家不存在或已软删除，抛出NotFoundException（404伪装）
    
    Args:
        expert: 专家对象（可能为None）
        current_user_id: 当前用户ID（可选）
        role: 用户角色（可选）
        
    Raises:
        NotFoundException: 如果专家不存在或不可见
    """
    if expert is None:
        raise NotFoundException("专家不存在")
    
    # 软删除检查：is_featured=False表示已删除
    if not expert.is_featured and role not in ['ADMIN', 'SUPERADMIN']:  # 🚨 必须使用大写
        self.logger.warning(f"专家不可见: id={str(expert.id)[:8]}, is_featured=False")
        raise NotFoundException("专家不存在")
```

---

### 5.4. 专家信息管理Service方法（7个）

#### 方法4: `get_featured_experts`

**函数签名**:
```python
async def get_featured_experts(
    self,
    limit: int = 10
) -> List[FeaturedExpertItem]
```

**功能**: 获取首页推荐专家列表

**权限逻辑**: 无需权限检查（公开接口）

**执行流程**:
1. 调用CRUD层：`experts = await crud.get_featured_experts(self.db, limit)`
2. 构造响应：
   ```python
   return [FeaturedExpertItem.model_validate(expert) for expert in experts]
   ```
3. 记录日志：`self.logger.info(f"查询推荐专家列表成功，返回{len(experts)}条记录")`

---

#### 方法5: `get_expert_detail`

**函数签名**:
```python
async def get_expert_detail(
    self,
    expert_id: uuid.UUID,
    current_user_id: Optional[uuid.UUID],
    role: Optional[str]
) -> ExpertItem
```

**功能**: 获取专家详情

**权限逻辑**: 无需权限检查（公开接口），但需要检查可见性

**执行流程**:
1. 调用CRUD层：`expert = await crud.get_expert(self.db, expert_id)`
2. 可见性检查：`self._check_expert_visibility(expert, current_user_id, role)`
3. 构造响应：`return ExpertItem.model_validate(expert)`
4. 记录日志：`self.logger.info(f"查询专家详情成功: expert_id={str(expert_id)[:8]}")`

---

#### 方法6: `get_expert_sessions`

**函数签名**:
```python
async def get_expert_sessions(
    self,
    expert_id: uuid.UUID,
    page: int = 1,
    size: int = 10,
    role: Optional[str] = None,
    current_user_id: Optional[uuid.UUID] = None,
    role_user: Optional[str] = None
) -> Dict[str, Any]
```

**功能**: 获取专家详情及其参与的所有直播场次（分页）

**权限逻辑**: 无需权限检查（公开接口），但需要检查可见性

**执行流程**:
1. 调用CRUD层：`expert = await crud.get_expert(self.db, expert_id)`
2. 可见性检查：`self._check_expert_visibility(expert, current_user_id, role_user)`
3. 计算分页：`skip = (page - 1) * size`
4. 调用CRUD层：`session_experts, total = await crud.get_expert_sessions(self.db, expert_id, role, skip, size)`
5. 构造响应：
   ```python
   return {
       "expert_info": ExpertItem.model_validate(expert),
       "sessions": {
           "total": total,
           "page": page,
           "size": size,
           "items": [
               {
                   "id": str(se.session.id),
                   "room_title": se.session.room.title if se.session.room else None,
                   "role": se.role,
                   "sort_order": se.sort_order,
                   "status": se.session.status.value if hasattr(se.session.status, 'value') else str(se.session.status),
                   "start_time": se.session.start_time.isoformat() + "Z" if se.session.start_time else None,
                   "cover_url": se.session.room.cover_url if se.session.room else None
               }
               for se in session_experts
           ]
       }
   }
   ```
6. 记录日志：`self.logger.info(f"查询专家场次列表成功: expert_id={str(expert_id)[:8]}, total={total}")`

---

#### 方法7: `create_expert`

**函数签名**:
```python
async def create_expert(
    self,
    expert_data: ExpertCreate,
    current_user_id: uuid.UUID,
    role: str
) -> ExpertItem
```

**功能**: 创建专家

**权限检查**: `_check_admin_permission(role)`

**业务验证**:
1. 如果提供了`user_id`，检查用户是否存在（可选，根据业务需求）
2. 如果提供了`user_id`，检查该用户是否已被其他专家绑定

**执行流程**:
1. 权限检查：`self._check_admin_permission(role)`
2. 业务验证：
   ```python
   if expert_data.user_id:
       # 检查user_id是否已被绑定
       existing_expert = await crud.get_expert_by_user_id(self.db, expert_data.user_id)
       if existing_expert:
           raise InvalidParameterException("该用户已绑定到其他专家档案", code=2004)
   ```
3. 调用CRUD层：`expert = await crud.create_expert(self.db, expert_data)`
4. 提交事务：`await db.commit()`
5. 刷新对象：`await db.refresh(expert)`
6. 构造响应：`return ExpertItem.model_validate(expert)`
7. 记录日志：`self.logger.info(f"创建专家成功: id={str(expert.id)[:8]}, user_id={str(current_user_id)[:8]}")`
8. 异常处理：
   ```python
   try:
       # ... 执行创建
   except DatabaseIntegrityException as e:
       await self.db.rollback()
       raise InvalidParameterException("该用户已绑定到其他专家档案", code=2004)
   except Exception as e:
       await self.db.rollback()
       self.logger.error(f"创建专家失败: {str(e)}")
       raise
   ```

---

#### 方法8: `get_experts_list`

**函数签名**:
```python
async def get_experts_list(
    self,
    page: int = 1,
    size: int = 10,
    name: Optional[str] = None,
    is_featured: Optional[bool] = None,
    hospital: Optional[str] = None,
    sort: Optional[str] = None,
    current_user_id: Optional[uuid.UUID] = None,
    role: Optional[str] = None
) -> Dict[str, Any]
```

**功能**: 获取专家列表（分页，管理员接口）

**权限检查**: `_check_admin_permission(role)`

**执行流程**:
1. 权限检查：`self._check_admin_permission(role)`
2. 计算分页：`skip = (page - 1) * size`
3. 调用CRUD层：`experts, total = await crud.get_experts_multi_and_total(self.db, skip, limit, name, is_featured, hospital, sort)`
4. 构造响应：
   ```python
   return {
       "total": total,
       "page": page,
       "size": size,
       "items": [ExpertItem.model_validate(expert) for expert in experts]
   }
   ```
5. 记录日志：`self.logger.info(f"查询专家列表成功（Admin），page={page}, size={size}, total={total}")`

---

#### 方法9: `update_expert`

**函数签名**:
```python
async def update_expert(
    self,
    expert_id: uuid.UUID,
    expert_data: ExpertUpdate,
    current_user_id: uuid.UUID,
    role: str
) -> ExpertItem
```

**功能**: 更新专家信息

**权限检查**: `_check_admin_permission(role)`

**业务验证**:
1. 如果更新了`user_id`字段，检查该用户是否已被其他专家绑定

**执行流程**:
1. 权限检查：`self._check_admin_permission(role)`
2. 调用CRUD层：`expert = await crud.update_expert(self.db, expert_id, expert_data)`
3. 404检查：
   ```python
   if expert is None:
       raise NotFoundException("专家不存在")
   ```
4. 业务验证（如果更新了user_id）：
   ```python
   if expert_data.user_id and expert_data.user_id != expert.user_id:
       existing_expert = await crud.get_expert_by_user_id(self.db, expert_data.user_id)
       if existing_expert and existing_expert.id != expert_id:
           raise InvalidParameterException("该用户已绑定到其他专家档案", code=2004)
   ```
5. 提交事务：`await self.db.commit()`
6. 刷新对象：`await self.db.refresh(expert)`
7. 构造响应：`return ExpertItem.model_validate(expert)`
8. 记录日志和异常处理（同create_expert）

---

#### 方法10: `delete_expert`

**函数签名**:
```python
async def delete_expert(
    self,
    expert_id: uuid.UUID,
    current_user_id: uuid.UUID,
    role: str
) -> Dict[str, Any]
```

**功能**: 删除专家（软删除）

**权限检查**: `_check_admin_permission(role)`

**执行流程**:
1. 权限检查：`self._check_admin_permission(role)`
2. 调用CRUD层：`success = await crud.delete_expert(self.db, expert_id)`
3. 404检查：
   ```python
   if not success:
       raise NotFoundException("专家不存在")
   ```
4. 提交事务：`await self.db.commit()`
5. 构造响应：`return {"id": str(expert_id), "status": "deleted"}`
6. 记录日志：`self.logger.warning(f"删除专家成功（软删除）: id={str(expert_id)[:8]}, user_id={str(current_user_id)[:8]}")`
7. 异常处理（同create_expert）

---

### 5.5. 专家关注Service方法（4个）

#### 方法11: `follow_expert`

**函数签名**:
```python
async def follow_expert(
    self,
    expert_id: uuid.UUID,
    current_user_id: uuid.UUID,
    role: str
) -> Dict[str, Any]
```

**功能**: 关注专家

**权限检查**: `_check_write_permission(role)`

**业务验证**:
1. 检查专家是否存在
2. 检查是否已关注

**执行流程**:
1. 权限检查：`self._check_write_permission(role)`
2. 检查专家是否存在：
   ```python
   expert = await crud.get_expert(self.db, expert_id)
   if expert is None:
       raise NotFoundException("专家不存在")
   ```
3. 检查是否已关注：
   ```python
   existing_subscription = await crud.get_subscription(self.db, current_user_id, expert_id)
   if existing_subscription:
       raise InvalidParameterException("您已关注该专家", code=2002)
   ```
4. 调用CRUD层：`subscription = await crud.create_subscription(self.db, current_user_id, expert_id)`
5. 提交事务：`await self.db.commit()`
6. 刷新对象：`await self.db.refresh(subscription)`
7. 构造响应：
   ```python
   return {
       "user_id": str(current_user_id),
       "expert_id": str(expert_id),
       "subscribed_at": subscription.created_at.isoformat() + "Z"
   }
   ```
8. 记录日志：`self.logger.info(f"关注专家成功: user_id={str(current_user_id)[:8]}, expert_id={str(expert_id)[:8]}")`
9. 异常处理：
   ```python
   try:
       # ... 执行关注
   except DatabaseIntegrityException as e:
       await self.db.rollback()
       raise InvalidParameterException("您已关注该专家", code=2002)
   except Exception as e:
       await self.db.rollback()
       self.logger.error(f"关注专家失败: {str(e)}")
       raise
   ```

---

#### 方法12: `unfollow_expert`

**函数签名**:
```python
async def unfollow_expert(
    self,
    expert_id: uuid.UUID,
    current_user_id: uuid.UUID,
    role: str
) -> Dict[str, Any]
```

**功能**: 取消关注专家

**权限检查**: `_check_write_permission(role)`

**执行流程**:
1. 权限检查：`self._check_write_permission(role)`
2. 调用CRUD层：`success = await crud.delete_subscription(self.db, current_user_id, expert_id)`
3. 404检查：
   ```python
   if not success:
       raise NotFoundException("未关注该专家")
   ```
4. 提交事务：`await self.db.commit()`
5. 构造响应：`return {"message": "取消关注成功"}`
6. 记录日志：`self.logger.info(f"取消关注专家成功: user_id={str(current_user_id)[:8]}, expert_id={str(expert_id)[:8]}")`
7. 异常处理（同follow_expert）

---

#### 方法13: `get_followed_experts`

**函数签名**:
```python
async def get_followed_experts(
    self,
    current_user_id: uuid.UUID,
    role: str,
    include_live_status: bool = True
) -> List[FollowedExpertItem]
```

**功能**: 获取关注的专家列表（包含直播状态）

**权限检查**: `_check_write_permission(role)`

**执行流程**:
1. 权限检查：`self._check_write_permission(role)`
2. 调用CRUD层：`subscriptions = await crud.get_user_subscriptions(self.db, current_user_id)`
3. 提取专家ID列表：`expert_ids = [sub.expert_id for sub in subscriptions]`
4. 查询直播状态（如果include_live_status=True）：
   ```python
   live_status_map = {}
   if include_live_status and expert_ids:
       # 批量查询直播状态（需要查询live_session_experts和live_sessions表）
       # 这里需要根据实际业务逻辑实现
       # 示例：查询每个专家最近的直播场次
       for expert_id in expert_ids:
           # 查询专家参与的正在直播的场次
           # 实现逻辑根据业务需求
           live_status_map[expert_id] = {...}  # 直播状态信息
   ```
5. 构造响应：
   ```python
   return [
       FollowedExpertItem(
           expert_id=sub.expert_id,
           name=sub.expert.name,
           title=sub.expert.title,
           hospital=sub.expert.hospital,
           avatar_url=sub.expert.avatar_url,
           subscribed_at=sub.created_at,
           live_status=live_status_map.get(sub.expert_id)
       )
       for sub in subscriptions
   ]
   ```
6. 记录日志：`self.logger.info(f"查询关注列表成功: user_id={str(current_user_id)[:8]}, 返回{len(subscriptions)}条记录")`

---

#### 方法14: `check_is_followed`

**函数签名**:
```python
async def check_is_followed(
    self,
    expert_id: uuid.UUID,
    current_user_id: uuid.UUID,
    role: str
) -> Dict[str, bool]
```

**功能**: 检查是否已关注专家

**权限检查**: `_check_write_permission(role)`

**执行流程**:
1. 权限检查：`self._check_write_permission(role)`
2. 调用CRUD层：`subscription = await crud.get_subscription(self.db, current_user_id, expert_id)`
3. 构造响应：`return {"is_followed": subscription is not None}`
4. 记录日志：`self.logger.debug(f"检查关注状态: user_id={str(current_user_id)[:8]}, expert_id={str(expert_id)[:8]}, is_followed={subscription is not None}")`

---

### 5.6. 场次专家关联Service方法（2个）

#### 方法15: `set_session_experts`

**函数签名**:
```python
async def set_session_experts(
    self,
    session_id: uuid.UUID,
    expert_data_list: List[Dict[str, Any]],  # 格式: [{"expert_id": UUID, "role": str, "sort_order": int}, ...]
    current_user_id: uuid.UUID,
    role: str
) -> Dict[str, Any]
```

**功能**: 为场次设置专家列表

**权限检查**: `_check_admin_permission(role)`

**业务验证**:
1. 检查专家是否存在
2. 检查角色是否有效（"主讲"、"主持"、"嘉宾"）

**执行流程**:
1. 权限检查：`self._check_admin_permission(role)`
2. 业务验证：
   ```python
   expert_ids = [data["expert_id"] for data in expert_data_list]
   # 查询专家是否存在
   for expert_id in expert_ids:
       expert = await crud.get_expert(self.db, expert_id)
       if expert is None:
           raise InvalidParameterException(f"专家不存在: {expert_id}", code=2001)
   
   # 验证角色
   valid_roles = ["主讲", "主持", "嘉宾"]
   for data in expert_data_list:
       if data["role"] not in valid_roles:
           raise InvalidParameterException(f"无效的角色: {data['role']}", code=4001)
   ```
3. 调用CRUD层：`session_experts = await crud.set_session_experts(self.db, session_id, expert_data_list)`
4. 提交事务：`await self.db.commit()`
5. 构造响应：
   ```python
   return {
       "session_id": str(session_id),
       "experts": [
           {
               "expert_id": str(se.expert_id),
               "role": se.role,
               "sort_order": se.sort_order
           }
           for se in session_experts
       ]
   }
   ```
6. 记录日志：`self.logger.info(f"设置场次专家列表成功: session_id={str(session_id)[:8]}, 专家数量={len(session_experts)}")`
7. 异常处理（同create_expert）

---

#### 方法16: `get_session_experts`

**函数签名**:
```python
async def get_session_experts(
    self,
    session_id: uuid.UUID,
    role: Optional[str] = None,
    current_user_id: Optional[uuid.UUID] = None,
    role_user: Optional[str] = None
) -> List[SessionExpertItem]
```

**功能**: 获取场次的专家列表

**权限逻辑**: 无需权限检查（公开接口）

**执行流程**:
1. 调用CRUD层：`session_experts = await crud.get_session_experts(self.db, session_id, role)`
2. 构造响应：
   ```python
   return [
       SessionExpertItem(
           id=se.expert.id,
           name=se.expert.name,
           title=se.expert.title,
           hospital=se.expert.hospital,
           avatar_url=se.expert.avatar_url,
           role=se.role,
           sort_order=se.sort_order
       )
       for se in session_experts
   ]
   ```
3. 记录日志：`self.logger.info(f"查询场次专家列表成功: session_id={str(session_id)[:8]}, 返回{len(session_experts)}条记录")`

---

## 6. API层代码生成（experts.py）

### 6.1. 文件头部

```python
"""
专家模块 API Endpoint 层

本模块实现所有专家相关的 RESTful API 接口。

职责：
- HTTP请求/响应处理
- 调用Service层
- 异常转换为HTTP响应

所有端点遵循安全异步异常处理原则。
"""

# 标准库导入
import uuid
import logging
from typing import List, Optional, Dict, Any

# 第三方库导入
from fastapi import APIRouter, Depends, Query, HTTPException, Request, Body
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

# 项目内导入
from app.database import get_db
from app.core.deps import get_current_user, get_current_user_optional
from app.core.response import success_response, error_response
from app.services.expert_service import ExpertService
from app.schemas.experts import (
    ExpertCreate, ExpertUpdate, ExpertItem, FeaturedExpertItem,
    ExpertFollowRequest, ExpertFollowResponse, FollowedExpertItem,
    FollowedExpertsResponse, SessionExpertItem
)
from app.exceptions import (
    NotFoundException,
    PermissionDeniedException,
    InvalidParameterException,
    DatabaseIntegrityException
)

# 配置日志
logger = logging.getLogger(__name__)

# ==================== 主路由器：专家管理 ====================

router = APIRouter(tags=["专家管理"])  # prefix 在 api.py 中指定
```

**⚠️ 重要：路由定义说明**：
1. **APIRouter 定义**: 在 `endpoints/experts.py` 文件中定义 `APIRouter(tags=["专家管理"])`，**严禁**在此时指定 `prefix`。
2. **Prefix 挂载**: `prefix` **必须**在顶层 `api/v1/api.py` 文件的 `api_router.include_router(...)` 中统一指定。
3. **避免重复前缀**：
   - **全局路由前缀**：`main.py` 中已经配置了全局前缀 `/api/v1`（通过 `settings.API_V1_STR`）
   - **子路由前缀**：子路由前缀**不应该**包含 `/api/v1`，只包含模块路径（如 `/experts`）
   - **最终路径**：`{全局前缀}/{子路由前缀}/{端点路径}`（如 `/api/v1/experts/{expert_id}`）
   - **避免**：子路由前缀包含 `/api/v1`（如 `/api/v1/experts`），导致最终路径为 `/api/v1/api/v1/experts/{expert_id}`
4. **端点路径**：
   - 集合端点 (如 `POST /experts`, `GET /experts`) **必须**使用 `path=""`（或 `/`）。
   - 单资源端点 (如 `GET /experts/{id}`) **必须**使用 `path="/{expert_id}"`。
   - 嵌套资源 (如 `GET /experts/{id}/sessions`) **必须**使用 `path="/{expert_id}/sessions"`。

**路由前缀层级示例**：
```python
# 层级 1：main.py（全局前缀）
app.include_router(api_router, prefix="/api/v1")

# 层级 2：api.py（子路由前缀）
api_router.include_router(
    experts.router,
    prefix="/experts",  # ✅ 正确：只包含模块路径
)
# 最终路径：/api/v1/experts/{expert_id}

# ❌ 错误：子路由前缀包含 /api/v1
api_router.include_router(
    experts.router,
    prefix="/api/v1/experts",  # ❌ 错误：重复 /api/v1
)
# 最终路径：/api/v1/api/v1/experts/{expert_id}
```

### 6.2. 响应格式化函数

```python
def format_expert_response(expert, request: Request = None) -> dict:
    """格式化专家响应数据"""
    data = {
        "id": str(expert.id),
        "user_id": str(expert.user_id) if expert.user_id else None,
        "name": expert.name,
        "title": expert.title,
        "hospital": expert.hospital,
        "department": expert.department,
        "expertise_areas": expert.expertise_areas,
        "bio": expert.bio,
        "avatar_url": expert.avatar_url,
        "is_featured": expert.is_featured,
        "sort_order": expert.sort_order,
        "created_at": expert.created_at.isoformat() + "Z",
        "updated_at": expert.updated_at.isoformat() + "Z"
    }
    
    # URL拼接（如果需要）
    if request and data["avatar_url"]:
        base_url = str(request.base_url).rstrip('/')
        if not data["avatar_url"].startswith('http'):
            data["avatar_url"] = f"{base_url}{data['avatar_url']}"
    
    return data
```

### 6.3. 专家信息管理API端点（7个）

#### 端点1: `GET /api/v1/featured-experts`

```python
@router.get("/featured-experts")
async def get_featured_experts(
    request: Request,
    limit: int = Query(default=10, ge=1, le=50, description="返回数量"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取首页推荐专家列表（公开）
    """
    try:
        service = ExpertService(db)
        experts = await service.get_featured_experts(limit=limit)
        
        # 格式化响应（URL拼接）
        experts_data = [
            {
                "id": str(expert.id),
                "name": expert.name,
                "title": expert.title,
                "hospital": expert.hospital,
                "avatar_url": format_avatar_url(expert.avatar_url, request) if expert.avatar_url else None
            }
            for expert in experts
        ]
        
        return success_response(data=experts_data)
        
    except Exception as e:
        logger.error(f"获取推荐专家列表异常: {str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库操作错误")
        )
```

---

#### 端点2: `GET /api/v1/experts/{expert_id}`

```python
@router.get("/{expert_id}")
async def get_expert_detail(
    expert_id: str,
    request: Request,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    获取专家详情（公开）
    """
    try:
        expert_uuid = uuid.UUID(expert_id)
    except ValueError:
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message="无效的专家ID")
        )
    
    # 提前提取用户信息（在try之前）
    user_id = uuid.UUID(current_user["user_id"]) if current_user else None
    role = current_user.get("role") if current_user else None
    
    user_id_for_logging = str(user_id)[:8] if user_id else "anonymous"
    
    try:
        service = ExpertService(db)
        expert = await service.get_expert_detail(
            expert_id=expert_uuid,
            current_user_id=user_id,
            role=role
        )
        
        return success_response(data=format_expert_response(expert, request))
        
    except NotFoundException as e:
        logger.warning(f"专家不存在: expert_id={expert_id}, user_id={user_id_for_logging}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在", data={"resource": "Expert", "id": expert_id})
        )
    except Exception as e:
        logger.error(f"获取专家详情异常: expert_id={expert_id}, user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库操作错误")
        )
```

---

#### 端点3: `GET /api/v1/experts/{expert_id}/sessions`

```python
@router.get("/{expert_id}/sessions")
async def get_expert_sessions(
    expert_id: str,
    request: Request,
    page: int = Query(default=1, ge=1, description="页码"),
    size: int = Query(default=10, ge=1, le=100, description="每页数量"),
    role: Optional[str] = Query(default=None, description="专家角色筛选"),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    获取专家详情及其参与的所有直播场次（分页，公开）
    """
    try:
        expert_uuid = uuid.UUID(expert_id)
    except ValueError:
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message="无效的专家ID")
        )
    
    # 提前提取用户信息（在try之前）
    user_id = uuid.UUID(current_user["user_id"]) if current_user else None
    role_user = current_user.get("role") if current_user else None
    
    user_id_for_logging = str(user_id)[:8] if user_id else "anonymous"
    
    try:
        service = ExpertService(db)
        result = await service.get_expert_sessions(
            expert_id=expert_uuid,
            page=page,
            size=size,
            role=role,
            current_user_id=user_id,
            role_user=role_user
        )
        
        return success_response(data=result)
        
    except NotFoundException as e:
        logger.warning(f"专家不存在: expert_id={expert_id}, user_id={user_id_for_logging}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在", data={"resource": "Expert", "id": expert_id})
        )
    except Exception as e:
        logger.error(f"获取专家场次列表异常: expert_id={expert_id}, user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库操作错误")
        )
```

---

#### 端点4: `POST /api/v1/admin/experts`

```python
@router.post("/admin/experts")
async def create_expert(
    expert_create: ExpertCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    创建专家（需要管理员权限）
    """
    # 提前提取用户信息（在try之前）
    user_id = uuid.UUID(current_user["user_id"])
    role = current_user.get("role")
    
    user_id_for_logging = str(user_id)[:8]
    
    try:
        service = ExpertService(db)
        expert = await service.create_expert(
            expert_data=expert_create,
            current_user_id=user_id,
            role=role
        )
        
        logger.info(f"专家创建成功: expert_id={expert.id}, user_id={user_id_for_logging}")
        
        return success_response(data=format_expert_response(expert))
        
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
            content=error_response(code=e.code if hasattr(e, 'code') else 4001, message=str(e))
        )
    except Exception as e:
        logger.error(f"创建专家异常: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库操作错误")
        )
```

---

#### 端点5: `GET /api/v1/admin/experts`

```python
@router.get("/admin/experts")
async def get_experts_list(
    request: Request,
    page: int = Query(default=1, ge=1, description="页码"),
    size: int = Query(default=10, ge=1, le=100, description="每页数量"),
    name: Optional[str] = Query(default=None, description="按姓名模糊搜索"),
    is_featured: Optional[bool] = Query(default=None, description="筛选推荐状态"),
    hospital: Optional[str] = Query(default=None, description="按医院筛选"),
    sort: Optional[str] = Query(default=None, description="排序规则"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取专家列表（需要管理员权限，分页）
    """
    # 提前提取用户信息（在try之前）
    user_id = uuid.UUID(current_user["user_id"])
    role = current_user.get("role")
    
    user_id_for_logging = str(user_id)[:8]
    
    try:
        service = ExpertService(db)
        result = await service.get_experts_list(
            page=page,
            size=size,
            name=name,
            is_featured=is_featured,
            hospital=hospital,
            sort=sort,
            current_user_id=user_id,
            role=role
        )
        
        # 格式化响应（URL拼接）
        result["items"] = [format_expert_response(expert, request) for expert in result["items"]]
        
        return success_response(data=result)
        
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: user_id={user_id_for_logging}, role={role}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message="权限不足")
        )
    except Exception as e:
        logger.error(f"获取专家列表异常: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库操作错误")
        )
```

---

#### 端点6: `PATCH /api/v1/admin/experts/{expert_id}`

```python
@router.patch("/admin/experts/{expert_id}")
async def update_expert(
    expert_id: str,
    expert_update: ExpertUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新专家信息（需要管理员权限）
    """
    try:
        expert_uuid = uuid.UUID(expert_id)
    except ValueError:
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message="无效的专家ID")
        )
    
    # 提前提取用户信息（在try之前）
    user_id = uuid.UUID(current_user["user_id"])
    role = current_user.get("role")
    
    user_id_for_logging = str(user_id)[:8]
    
    try:
        service = ExpertService(db)
        expert = await service.update_expert(
            expert_id=expert_uuid,
            expert_data=expert_update,
            current_user_id=user_id,
            role=role
        )
        
        logger.info(f"专家更新成功: expert_id={expert_id}, user_id={user_id_for_logging}")
        
        return success_response(data=format_expert_response(expert))
        
    except NotFoundException as e:
        logger.warning(f"专家不存在: expert_id={expert_id}, user_id={user_id_for_logging}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在", data={"resource": "Expert", "id": expert_id})
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
            content=error_response(code=e.code if hasattr(e, 'code') else 4001, message=str(e))
        )
    except Exception as e:
        logger.error(f"更新专家异常: expert_id={expert_id}, user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库操作错误")
        )
```

---

#### 端点7: `DELETE /api/v1/admin/experts/{expert_id}`

```python
@router.delete("/admin/experts/{expert_id}")
async def delete_expert(
    expert_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除专家（需要管理员权限，软删除）
    """
    try:
        expert_uuid = uuid.UUID(expert_id)
    except ValueError:
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message="无效的专家ID")
        )
    
    # 提前提取用户信息（在try之前）
    user_id = uuid.UUID(current_user["user_id"])
    role = current_user.get("role")
    
    user_id_for_logging = str(user_id)[:8]
    
    try:
        service = ExpertService(db)
        result = await service.delete_expert(
            expert_id=expert_uuid,
            current_user_id=user_id,
            role=role
        )
        
        logger.warning(f"专家删除成功（软删除）: expert_id={expert_id}, user_id={user_id_for_logging}")
        
        return success_response(data=result)
        
    except NotFoundException as e:
        logger.warning(f"专家不存在: expert_id={expert_id}, user_id={user_id_for_logging}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在", data={"resource": "Expert", "id": expert_id})
        )
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: user_id={user_id_for_logging}, role={role}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message="权限不足")
        )
    except Exception as e:
        logger.error(f"删除专家异常: expert_id={expert_id}, user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库操作错误")
        )
```

---

### 6.4. 专家关注API端点（4个）

#### 端点8: `POST /api/v1/users/me/followed-experts`

```python
@router.post("/users/me/followed-experts")
async def follow_expert(
    follow_request: ExpertFollowRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    关注专家（需要登录）
    """
    # 提前提取用户信息（在try之前）
    user_id = uuid.UUID(current_user["user_id"])
    role = current_user.get("role")
    
    user_id_for_logging = str(user_id)[:8]
    
    try:
        service = ExpertService(db)
        result = await service.follow_expert(
            expert_id=follow_request.expert_id,
            current_user_id=user_id,
            role=role
        )
        
        logger.info(f"关注专家成功: user_id={user_id_for_logging}, expert_id={follow_request.expert_id}")
        
        return success_response(data=result, message="关注成功")
        
    except NotFoundException as e:
        logger.warning(f"专家不存在: expert_id={follow_request.expert_id}, user_id={user_id_for_logging}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在", data={"resource": "Expert", "id": str(follow_request.expert_id)})
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
            status_code=409,
            content=error_response(code=e.code if hasattr(e, 'code') else 2002, message=str(e))
        )
    except Exception as e:
        logger.error(f"关注专家异常: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库操作错误")
        )
```

---

#### 端点9: `DELETE /api/v1/users/me/followed-experts/{expert_id}`

```python
@router.delete("/users/me/followed-experts/{expert_id}")
async def unfollow_expert(
    expert_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    取消关注专家（需要登录）
    """
    try:
        expert_uuid = uuid.UUID(expert_id)
    except ValueError:
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message="无效的专家ID")
        )
    
    # 提前提取用户信息（在try之前）
    user_id = uuid.UUID(current_user["user_id"])
    role = current_user.get("role")
    
    user_id_for_logging = str(user_id)[:8]
    
    try:
        service = ExpertService(db)
        result = await service.unfollow_expert(
            expert_id=expert_uuid,
            current_user_id=user_id,
            role=role
        )
        
        logger.info(f"取消关注专家成功: user_id={user_id_for_logging}, expert_id={expert_id}")
        
        return success_response(data=result, message="取消关注成功")
        
    except NotFoundException as e:
        logger.warning(f"未关注该专家: expert_id={expert_id}, user_id={user_id_for_logging}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在", data={"reason": "未关注该专家"})
        )
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: user_id={user_id_for_logging}, role={role}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message="权限不足")
        )
    except Exception as e:
        logger.error(f"取消关注专家异常: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库操作错误")
        )
```

---

#### 端点10: `GET /api/v1/users/me/followed-experts`

```python
@router.get("/users/me/followed-experts")
async def get_followed_experts(
    request: Request,
    include_live_status: bool = Query(default=True, description="是否包含直播状态"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取关注的专家列表（需要登录）
    """
    # 提前提取用户信息（在try之前）
    user_id = uuid.UUID(current_user["user_id"])
    role = current_user.get("role")
    
    user_id_for_logging = str(user_id)[:8]
    
    try:
        service = ExpertService(db)
        experts = await service.get_followed_experts(
            current_user_id=user_id,
            role=role,
            include_live_status=include_live_status
        )
        
        # 格式化响应（URL拼接）
        experts_data = [
            {
                "expert_id": str(expert.expert_id),
                "name": expert.name,
                "title": expert.title,
                "hospital": expert.hospital,
                "avatar_url": format_avatar_url(expert.avatar_url, request) if expert.avatar_url else None,
                "subscribed_at": expert.subscribed_at.isoformat() + "Z",
                "live_status": expert.live_status
            }
            for expert in experts
        ]
        
        return success_response(data=experts_data)
        
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: user_id={user_id_for_logging}, role={role}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message="权限不足")
        )
    except Exception as e:
        logger.error(f"获取关注列表异常: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库操作错误")
        )
```

---

#### 端点11: `GET /api/v1/experts/{expert_id}/is-followed`

```python
@router.get("/{expert_id}/is-followed")
async def check_is_followed(
    expert_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    检查是否已关注专家（需要登录）
    """
    try:
        expert_uuid = uuid.UUID(expert_id)
    except ValueError:
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message="无效的专家ID")
        )
    
    # 提前提取用户信息（在try之前）
    user_id = uuid.UUID(current_user["user_id"])
    role = current_user.get("role")
    
    user_id_for_logging = str(user_id)[:8]
    
    try:
        service = ExpertService(db)
        result = await service.check_is_followed(
            expert_id=expert_uuid,
            current_user_id=user_id,
            role=role
        )
        
        return success_response(data=result)
        
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: user_id={user_id_for_logging}, role={role}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message="权限不足")
        )
    except Exception as e:
        logger.error(f"检查关注状态异常: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库操作错误")
        )
```

---

### 6.5. 场次专家关联API端点（2个）

#### 端点12: `POST /api/v1/sessions/{session_id}/experts`

```python
@router.post("/sessions/{session_id}/experts")
async def set_session_experts(
    session_id: str,
    expert_data_list: List[Dict[str, Any]] = Body(..., description="专家列表"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    为场次设置专家列表（需要管理员权限）
    """
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message="无效的场次ID")
        )
    
    # 提前提取用户信息（在try之前）
    user_id = uuid.UUID(current_user["user_id"])
    role = current_user.get("role")
    
    user_id_for_logging = str(user_id)[:8]
    
    try:
        service = ExpertService(db)
        result = await service.set_session_experts(
            session_id=session_uuid,
            expert_data_list=expert_data_list,
            current_user_id=user_id,
            role=role
        )
        
        logger.info(f"设置场次专家列表成功: session_id={session_id}, user_id={user_id_for_logging}")
        
        return success_response(data=result)
        
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
            content=error_response(code=e.code if hasattr(e, 'code') else 4001, message=str(e))
        )
    except Exception as e:
        logger.error(f"设置场次专家列表异常: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库操作错误")
        )
```

---

#### 端点13: `GET /api/v1/sessions/{session_id}/experts`

```python
@router.get("/sessions/{session_id}/experts")
async def get_session_experts(
    session_id: str,
    request: Request,
    role: Optional[str] = Query(default=None, description="专家角色筛选"),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    获取场次的专家列表（公开）
    """
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message="无效的场次ID")
        )
    
    # 提前提取用户信息（在try之前）
    user_id = uuid.UUID(current_user["user_id"]) if current_user else None
    role_user = current_user.get("role") if current_user else None
    
    try:
        service = ExpertService(db)
        experts = await service.get_session_experts(
            session_id=session_uuid,
            role=role,
            current_user_id=user_id,
            role_user=role_user
        )
        
        # 格式化响应（URL拼接）
        experts_data = [
            {
                "id": str(expert.id),
                "name": expert.name,
                "title": expert.title,
                "hospital": expert.hospital,
                "avatar_url": format_avatar_url(expert.avatar_url, request) if expert.avatar_url else None,
                "role": expert.role,
                "sort_order": expert.sort_order
            }
            for expert in experts
        ]
        
        return success_response(data=experts_data)
        
    except Exception as e:
        logger.error(f"获取场次专家列表异常: session_id={session_id}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库操作错误")
        )
```

---

## 7. 路由注册更新要求

**⚠️ 关键：路由注册**

生成API端点代码后，**必须同时**更新 `app/api/v1/api.py` 文件，注册新的路由。

**操作指令**:
1. 读取 `app/api/v1/api.py` 文件
2. 在 `api_router.include_router(...)` 调用中添加：
   ```python
   from app.api.v1.endpoints import experts
   
   api_router.include_router(
       experts.router,
       prefix="/experts",
       tags=["专家管理"]
   )
   ```
3. **必须**在文件末尾追加新路由注册（保持格式一致）
4. **严禁**修改、删除或重新排序任何现有路由注册

---

## 8. 代码生成要求

### 8.1. Service层代码要求

1. **所有方法必须有完整的类型提示**
2. **所有方法必须有文档字符串**（说明参数、返回值、异常）
3. **所有权限检查必须使用权限守卫函数**
4. **所有事务操作必须包含异常处理**（try/except/finally）
5. **所有日志记录必须使用UUID脱敏**（只记录前8位）

### 8.2. API层代码要求

1. **所有端点必须有文档字符串**（OpenAPI文档）
2. **所有端点必须使用安全异步异常处理**（提前提取变量）
3. **所有响应必须使用success_response或error_response**
4. **所有异常必须转换为JSONResponse**
5. **所有URL拼接必须在API层处理**（使用Request依赖）

### 8.3. 参考代码风格

参考 `app/services/topic_service.py` 和 `app/api/v1/endpoints/topic.py` 的代码风格和结构，确保生成的代码风格一致。

---

## 9. 最终交付

生成完整的两个文件：
1. `app/services/expert_service.py` - 包含所有16个Service方法
2. `app/api/v1/endpoints/experts.py` - 包含所有13个API端点

**文件路径**: 
- `backend/live_core_service/app/services/expert_service.py`
- `backend/live_core_service/app/api/v1/endpoints/experts.py`

---

**文档版本**: V1.0  
**创建日期**: 2026-01-18  
**状态**: 准备就绪

