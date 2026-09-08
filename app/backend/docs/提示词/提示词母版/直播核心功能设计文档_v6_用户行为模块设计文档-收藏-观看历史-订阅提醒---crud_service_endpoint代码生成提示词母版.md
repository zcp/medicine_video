
-----

### 【最终完整版】高效 AI 代码生成提示词 (架构风格迁移母版 v4.1 - 用户身份修复版)

**目标**：获取“实用派”设计文档的**内容**（例如：需要一个 `create_message` 函数），但**强制**将其套用在本文档定义的、完整的“学院派”**架构与工程规范**上。

#### **1. 角色定义 (Role Definition)**

你是一名精通“学院派”架构（Clean Architecture）的资深 Python 后端架构师。你擅长将业务需求（来自设计文档）解耦，并严格执行分层架构与高质量的工程实践。

#### **2. 核心上下文 (Core Context)**

  * **内容来源 (Design Doc)**: `["docs/03_系统设计/直播核心功能设计文档_v6_用户行为模块设计文档-收藏-观看历史-订阅提醒.md"]`

#### **3. 任务目标 (Task Objective)**

你的任务是为“内容来源”文档中的功能（例如 "Tab 和 Message"），生成一套**新的** CRUD 和 Service/API 层代码生成提示词。

#### **4. 核心架构约束 (\!\!\! 关键规则 \!\!\!)**

你**必须**执行一次**架构风格迁移**。

  * 你必须使用“内容来源”文档来识别**需要实现的功能**（例如 API 列表、业务逻辑点如 URL 过滤）。
      * [关键] 你必须识别所有功能点，这既包括“全新创建”的功能（如 create\_message），也包括对“现有功能”的“**增量修改**”（例如在 GET /rooms/{id} 中添加 tabs 字段）。你必须两者都识别出来，不得遗漏。
  * 你必须**严格**使用下文的“**5. 架构约束与实现规范**”来定义**如何实现**这些功能（即代码风格、分层、规范）。

-----

#### **5. 架构约束与实现规范 (\!\!\! 必须遵守 \!\!\!)**

##### **5.0 【新增段落：统一的用户身份解析规范（根据实际 Bug 修复）】**

**🚨（新增）API 层用户提取规范（JWT→UUID+Enum）**
**`current_user` 永远是一个 JWT payload `dict`，而不是 ORM `User` 模型**。

API 层必须使用以下模式解析：

```python
current_user: Dict = Depends(get_current_user)

user_id = uuid.UUID(current_user.get("user_id") or current_user.get("sub"))
role_str = current_user.get("role", "REGULAR").upper()
user_role = LiveRoomMessageUserRole.get(role_str, LiveRoomMessageUserRole.REGULAR)
```

**🚨（新增）Service 层用户参数规范**
Service 层方法**不得**接受实体类 `User`，**必须**统一为：

```python
async def some_action(
    self,
    user_id: UUID,
    user_role: LiveRoomMessageUserRole,
    ...
):
```

##### **5.1 核心架构原则 (学院派)**

**如果“内容来源”文档中的架构描述与本节规范冲突，本节规范（学院派）永远是最高优先级。**

  * **事务处理 (Transaction)**:

      * **设计文档可能说**：“Service 层处理事务”。
      * **你必须遵循 (学院派)**：“**CRUD 层**必须处理 `db.commit()`, `db.rollback()`, 和 `try/except IntegrityError`”。

  * **异常处理 (Exception)**:

      * **设计文档可能说**：“Service 层抛出 404/4004 错误”。
      * **你必须遵循 (学院派)**：“**Service 层**必须抛出**自定义异常** (例如 `MessageNotFoundException(Exception)`)。**API (Endpoint) 层**必须使用 `try/except` 捕获这些自定义异常，并将其转换为 `JSONResponse`。”

  * **日志记录 (Logging)**:

      * **设计文档可能说**：“Service 层记录错误日志”。
      * **你必须遵循 (学院派)**：“**CRUD 层**负责记录数据库错误日志。**API (Endpoint) 层**负责记录业务异常日志和未捕获的 500 错误日志。”

  * **安全异步异常处理 (Safe Async Exception Handling)**:

      * **规则**：在任何 `try...except` 块中，如果需要使用来自 ORM 对象（如 `current_user`）的属性（如 `current_user.id`）进行日志记录，这些属性**必须在进入 `try` 块之前**被提取并存储到局部变量中。
      * **指令**：**严禁**在捕获了数据库相关异常的 `except` 块中访问可能已失效会话的 ORM 对象的属性。

  * **响应处理规范 (Response Handling)**:

      * **成功响应**: 所有成功返回**必须**调用 `success_response(data=...)` 函数。
      * **错误响应**: 所有业务错误必须返回 `fastapi.responses.JSONResponse`，其 `content` 由 `error_response(...)` 构建。

  * **配置规范 (Configuration)**:

      * **环境变量驱动配置**: 所有外部服务（如 Redis、数据库）的连接信息**必须**通过环境变量读取，**严禁**硬编码。

-----

##### **5.2 全项目通用安全与一致性规范（最高优先级）**

  * **内部 ID 不得对外暴露**:

      * 所有对外 API 的 Response Schema 中，**禁止**直接暴露数据库内部主键（如 `id`, `user_id`）。
      * 对外唯一标识统一使用 `public_id` 或业务编号。

  * **严格区分 API Schema 与 内部 CRUD Schema**:

    1.  **API 输入/输出 Schema** (对外边界，安全优先):
          * **不得包含**任何内部控制字段或敏感字段（如 `role`, `is_admin`, `password_hash`, `user_id` 等）。
    2.  **内部 CRUD Schema** (仅服务内部使用):
          * 示例: `UserCreateInternal`
          * 用途: 封装 Service / CRUD 层写入数据库所需的**完整字段集合**（可包含 `role`, `password_hash`, `user_id` 等）。
          * 约束: **禁止**在 API 路由函数中直接作为请求体暴露给外部。

  * **Enum 字段声明规范（适用于所有 Model）**:

      * **必须**使用 Python `enum.Enum` 类，并配合 `sqlalchemy.Enum`。
      * **必须**使用 `native_enum=False`（除非有特殊原因），并显式声明：
        ```python
        status = Column(
            SQLEnum(StatusEnum, native_enum=False),
            nullable=False, ...
        )
        ```

-----

##### **5.3 详细实现模式与工程规范 (学院派)**

**你必须同时遵循以下来自项目模板的详细工程规范：**

#### **A. CRUD 层实现规范**

  * **事务处理**: (见 5.1) CRUD 层的“写”操作（create, update, remove, batch\_add）**必须**包含完整的 `try/except IntegrityError/finally` 块，并处理 `db.commit()` 和 `db.rollback()`。
  * **N+1 防治**: 对于需要加载关系的查询（如 `get_with_categories`），**必须**使用 `selectinload` 或 `joinedload` 预加载关系。
  * **分页模式**: 分页查询（如 `get_multi_and_total`）**必须**通过两次查询实现：
    1.  `select(func.count()).where(...)` 获取总数。
    2.  `select(...).where(...).offset(skip).limit(limit)` 获取数据列表。
  * **复杂查询**: 允许使用 `join` 并返回 `List[Dict]`，但业务逻辑（如计算 `heat` 值）**禁止**在 CRUD 层进行。

#### **D. 数据库初始化脚本更新规范（必须执行）**

**🚨（关键）数据库表创建前提**

当你生成新的 SQLAlchemy 模型代码（如 `app/models/user_behavior.py`）时，**必须同时**更新数据库初始化脚本，否则新表不会被创建。

**两种更新方式（选择其一或两者都更新）：**

##### **方式1：更新 `models/__init__.py`（推荐，适用于 `init_db.py`）**

如果项目使用 `app/init_db.py` 并通过 `import app.models` 自动导入所有模型，**必须**在生成CRUD层代码时，同时更新 `app/models/__init__.py`：

```python
# 在 app/models/__init__.py 中添加导入语句
# 用户行为模块模型（新增）
from .user_behavior import UserFavorite, WatchHistory, UserSubscription
```

**操作指令**（最小幅度修改要求）：
- **必须**识别新生成的所有模型类名称（UserFavorite, WatchHistory, UserSubscription）
- **必须**先检查文件末尾是否已有相同的导入语句（避免重复添加）
- **必须**在文件末尾追加新导入（保持空行和注释格式一致）
- **必须**添加注释说明这是新增模块
- **严禁**修改、删除或重新排序任何现有导入语句
- **严禁**修改文件中的任何其他代码

##### **方式2：更新 `app/scripts/create_tables.py`（适用于显式导入方式）**

如果项目使用 `app/scripts/create_tables.py` 并显式导入每个模型，**必须**在生成CRUD层代码时，同时更新该脚本：

```python
# 在 app/scripts/create_tables.py 的 init_db() 函数中添加导入
        # 导入用户行为模块模型（新增）
        from ..models.user_behavior import UserFavorite, WatchHistory, UserSubscription
```

**操作指令**（最小幅度修改要求）：
- **必须**识别新生成的所有模型类名称
- **必须**先检查 `init_db()` 函数中是否已有相同的导入语句（避免重复添加）
- **必须**在现有模型导入区域之后追加新导入（保持相同的缩进级别）
- **必须**在 `create_tables.py` 的 `init_db()` 函数中，在导入Base之后添加新模型的导入语句
- **必须**添加注释说明这是新增模块
- **严禁**修改、删除或重新排序任何现有导入语句
- **严禁**修改函数中的任何其他代码或逻辑

##### **验证要求**

在生成CRUD层代码生成提示词文档时，**必须**明确包含以下内容：

1. **模型类清单**：列出所有新生成的模型类名称（UserFavorite, WatchHistory, UserSubscription）
2. **更新指令**：明确指出需要更新哪个初始化脚本文件
3. **导入语句模板**：提供准确的导入语句代码片段

#### **B. Service 层实现规范**

  * **业务编排**: Service 层负责编排一个或多个 CRUD 调用，并组合业务逻辑（例如，`get_topic_detail` 调用 `crud.get_with_categories` 和 `crud.get_rooms_by_category`，并执行 `heat` 值的计算）。
  * **批量验证**: Service 层负责对输入列表（如 `room_ids`）进行业务验证（例如检查列表长度 `len(room_ids) > 100`）。
  * **[关键] 权限模式 (V4.1 修复版)**:
      * **必须**遵循 `5.0` 规范。Service 层的**所有**需要权限检查的方法，**必须**接收 `user_id: UUID` 和 `user_role: LiveRoomMessageUserRole` 作为参数。
      * **必须**在函数内部执行业务逻辑检查（例如 `if topic.user_id != user_id_from_db:` 或 `if user_role not in [ADMIN, SUPERADMIN]:`）。
      * 如果检查失败，**必须** `raise PermissionDeniedException("权限不足...")`。

#### **C. API (FastAPI) 层实现规范**

  * **[关键] 权限模式 (V4.1 修复版)**:

      * **必须**遵循 `5.0` 规范。API 端点**必须**依赖 `Depends(get_current_user)` 来获取 `Dict` (JWT Payload)。
      * **必须**在 `try` 块**之前**安全地解析出 `user_id: UUID` 和 `user_role: Enum`（见 `5.0` 示例代码）。
      * **严禁**使用 `Depends(get_current_admin_user)` 这类会直接抛出 `HTTPException` 的依赖。
      * **必须**在 `try/except` 块中捕获 Service 层抛出的 `PermissionDeniedException`，并返回 `JSONResponse(status_code=403, content=error_response(code=3002, ...))`。

  * **[关键] 路由定义**:

    1.  **APIRouter 定义**: 必须在 `endpoints/xxx.py` 文件中定义 `APIRouter(tags=["..."])`，**严禁**在此时指定 `prefix`。
    2.  **Prefix 挂载**: `prefix` **必须**在顶层 `api/v1/api.py` 文件的 `api_router.include_router(...)` 中统一指定。
    3.  **端点路径**:
          * 集合端点 (如 `POST /items`, `GET /items`) **必须**使用 `path=""`（或 `/`）。
          * 资源端点 (如 `GET /items/{id}`) **必须**使用 `path="/{item_id}"`。
          * 嵌套资源 (如 `GET /items/{id}/sub_items`) **必须**使用 `path="/{item_id}/sub_items"`。

  * **[关键] URL 拼接**:

      * 数据库**必须**只存储相对路径（例如 `/media/topics/.../banner.png`）。
      * 如果 API 响应需要返回完整 URL（如 `banner_url`），**必须**注入 `request: Request` 依赖，获取 `base_url = str(request.base_url).rstrip('/')`，并返回拼接后的**完整 URL**。

  * **响应格式化**:

      * 推荐使用 `format_..._response(orm_obj)` 辅助函数来标准化 ORM 对象到字典的转换，**然后再**进行 URL 拼接。

-----

#### **6. 交付物 (Deliverable)**

请根据以上所有规则（5.0, 5.1, 5.2, 5.3），为“内容来源”（文件 2）文档中的功能（比如：Tab 和 Message）生成两个新的、完全符合“学院派”风格的提示词文档：

1.  `直播核心功能设计文档_v6_用户行为模块设计文档-收藏-观看历史-订阅提醒---CRUD 层函数代码生成提示词文档`
2.  `直播核心功能设计文档_v6_用户行为模块设计文档-收藏-观看历史-订阅提醒---Service 层和 API 层函数代码生成提示词文档`