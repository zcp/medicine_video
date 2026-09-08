# 专家模块设计文档-专家信息-专家关注 CRUD/Service/API 代码生成提示词母版

**版本**: V1.0  
**创建日期**: 2026-01-18  
**生成器**: AI 自动化生成系统  
**基于母版**: @docs/提示词/自动化后端代码生成/crud_service_endpoint代码生成提示词母版.md  
**设计文档**: @docs/03_系统设计/直播核心功能设计文档_v6_专家模块设计文档-专家信息-专家关注.md

---

## 1. 角色定义 (Role Definition)

你是一名精通"学院派"架构（Clean Architecture）的资深 Python 后端架构师。你擅长将业务需求（来自设计文档）解耦，并严格执行分层架构与高质量的工程实践。

---

## 2. 核心上下文 (Core Context)

### 2.1. 内容来源 (Design Doc)
- **设计文档路径**: `docs/03_系统设计/直播核心功能设计文档_v6_专家模块设计文档-专家信息-专家关注.md`
- **设计文档内容**: 专家信息管理、专家关注、场次专家关联的完整功能定义

### 2.2. 项目路径
- **项目路径**: `backend/live_core_service`

### 2.3. 项目结构与上下文信息

**项目目录结构**:
```
app/
├── models/          # SQLAlchemy 模型（数据层）
│   ├── __init__.py
│   ├── experts.py  # ✅ 已生成的专家模块模型
│   ├── live_core.py
│   ├── content_management.py
│   ├── topic.py
│   ├── user_behavior.py
│   └── ...
├── schemas/         # Pydantic Schema（数据验证层）
│   ├── __init__.py
│   ├── experts.py  # ✅ 已生成的专家模块Schema
│   ├── live_core.py
│   ├── content_management.py
│   ├── topic.py
│   ├── user_behavior.py
│   └── ...
├── crud/            # CRUD 层（数据访问层）
│   ├── __init__.py
│   ├── experts.py  # 📋 待生成的专家模块CRUD
│   ├── topic.py     # 参考：专题模块CRUD（app/crud/topic.py）
│   ├── content_management.py
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

### 2.4. 文件命名规范

- 模型文件: `experts.py`
- Schema文件: `experts.py`
- CRUD文件: `experts.py`
- Service文件: `expert_service.py`（注意：单数形式）
- Endpoint文件: `experts.py`

### 2.5. 导入路径规范

- 模型导入: `from app.models.experts import Expert, UserExpertSubscription, LiveSessionExpert`
- Schema导入: `from app.schemas.experts import (所有需要的Schema)`
- CRUD导入: `from app.crud.experts import (所有CRUD函数)`
- Service导入: `from app.services.expert_service import ExpertService`

### 2.6. 模块依赖关系

- CRUD 层 → Models（依赖）
- Service 层 → CRUD 层（依赖）
- Endpoint 层 → Service 层 + Schemas（依赖）

### 2.7. 现有代码参考

- 专题模块CRUD: `app/crud/topic.py`（可作为代码风格和结构参考）
- 专题模块Service: `app/services/topic_service.py`（可作为代码风格和结构参考）
- 专题模块Endpoint: `app/api/v1/endpoints/topic.py`（可作为代码风格和结构参考）

---

## 3. 模型定义来源说明

**重要：本文档优先使用已生成的代码，而不是从设计文档中提取**

### 3.1. 专家模块模型定义（已生成）

**模型文件路径**: `backend/live_core_service/app/models/experts.py`

**以下模型定义引用自已生成的代码：app/models/experts.py**

1. **Expert** - 专家信息模型
2. **UserExpertSubscription** - 用户专家订阅模型
3. **LiveSessionExpert** - 直播场次专家关联模型

**字段说明**：
- 所有字段已在生成的代码中定义
- 所有关系已在生成的代码中定义
- 所有约束和索引已在生成的代码中定义
- 所有时间戳字段使用 `TIMESTAMP(timezone=True)` 和 `server_default=func.now()`

### 3.2. 专家模块Schema定义（已生成）

**Schema文件路径**: `backend/live_core_service/app/schemas/experts.py`

**以下Schema定义引用自已生成的代码：app/schemas/experts.py**

1. **专家信息Schemas**:
   - `ExpertBase` - 专家基础Schema
   - `ExpertCreate` - 创建专家请求Schema
   - `ExpertUpdate` - 更新专家请求Schema
   - `ExpertItem` - 专家响应Schema
   - `FeaturedExpertItem` - 首页推荐专家简要Schema

2. **专家关注Schemas**:
   - `ExpertFollowRequest` - 关注专家请求Schema
   - `ExpertFollowResponse` - 关注专家响应Schema
   - `FollowedExpertItem` - 关注的专家响应Schema
   - `FollowedExpertsResponse` - 关注列表响应Schema

3. **场次专家关联Schemas**:
   - `SessionExpertItem` - 场次专家关联信息Schema

---

## 4. 任务目标 (Task Objective)

你的任务是为专家模块（Experts）生成一套**新的** CRUD 和 Service/API 层代码生成提示词，包含：

1. **专家信息管理功能**：
   - 创建专家
   - 更新专家
   - 删除专家（软删除）
   - 获取专家详情
   - 获取专家列表（分页）
   - 获取首页推荐专家列表
   - 设置专家为推荐/取消推荐

2. **专家关注功能**：
   - 关注专家
   - 取消关注
   - 获取关注的专家列表（分页）
   - 检查是否已关注
   - 批量获取关注专家的直播状态

3. **场次专家关联功能**：
   - 为场次设置专家
   - 获取场次的专家列表

---

## 5. 核心架构约束 (\!\!\! 关键规则 \!\!\!)

你必须**严格**使用以下架构约束来定义**如何实现**这些功能：

### 5.1. 核心架构原则 (学院派)

**如果设计文档中的架构描述与本节规范冲突，本节规范（学院派）永远是最高优先级。**

* **事务处理 (Transaction)**:
   * **你必须遵循 (学院派)**："**CRUD 层**必须处理 `db.commit()`, `db.rollback()`, 和 `try/except IntegrityError`"。

* **异常处理 (Exception)**:
   * **你必须遵循 (学院派)**："**Service 层**必须抛出**自定义异常** (例如 `ExpertNotFoundException(Exception)`)。**API (Endpoint) 层**必须使用 `try/except` 捕获这些自定义异常，并将其转换为 `JSONResponse`。"

* **日志记录 (Logging)**:
   * **你必须遵循 (学院派)**："**CRUD 层**负责记录数据库错误日志。**API (Endpoint) 层**负责记录业务异常日志和未捕获的 500 错误日志。"

* **安全异步异常处理 (Safe Async Exception Handling)**:
   * **规则**：在任何 `try...except` 块中，如果需要使用来自 ORM 对象（如 `current_user`）的属性（如 `current_user.id`）进行日志记录，这些属性**必须在进入 `try` 块之前**被提取并存储到局部变量中。
   * **指令**：**严禁**在捕获了数据库相关异常的 `except` 块中访问可能已失效会话的 ORM 对象的属性。

* **响应处理规范 (Response Handling)**:
   * **成功响应**: 所有成功返回**必须**调用 `success_response(data=...)` 函数。
   * **错误响应**: 所有业务错误必须返回 `fastapi.responses.JSONResponse`，其 `content` 由 `error_response(...)` 构建。

* **配置规范 (Configuration)**:
   * **环境变量驱动配置**: 所有外部服务（如 Redis、数据库）的连接信息**必须**通过环境变量读取，**严禁**硬编码。

### 5.2. 全项目通用安全与一致性规范（最高优先级）

* **内部 ID 不得对外暴露**:
   * 所有对外 API 的 Response Schema 中，**禁止**直接暴露数据库内部主键（如 `id`, `user_id`）。
   * 对外唯一标识统一使用 `public_id` 或业务编号。

* **严格区分 API Schema 与 内部 CRUD Schema**:
   1. **API 输入/输出 Schema** (对外边界，安全优先):
      * **不得包含**任何内部控制字段或敏感字段（如 `role`, `is_admin`, `user_id` 等）。
   2. **内部 CRUD Schema** (仅服务内部使用):
      * 用途: 封装 Service / CRUD 层写入数据库所需的**完整字段集合**（可包含 `role`, `user_id` 等）。
      * 约束: **禁止**在 API 端点函数中直接作为请求体暴露给外部。

* **Enum 字段声明规范（适用于所有 Model）**:
   * **必须**使用 Python `enum.Enum` 类，并配合 `sqlalchemy.Enum`。
   * **必须**使用 `native_enum=False`（除非有特殊原因），并显式声明：
     ```python
     status = Column(
         SQLEnum(StatusEnum, native_enum=False),
         nullable=False, ...
     )
     ```

* **RESTful API 设计原则（必须遵守）**:
   * **资源导向 (Resource-Oriented)**:
     * URL必须是**资源（名词）**，而不是**动作（动词）**。
     * ✅ 正确：`GET /api/v1/users/me/followed-experts`（资源是`followed-experts`）
     * ❌ 错误：`GET /api/v1/users/me/follow-expert`（`follow-expert`是动作）
   
   * **层次结构 (Hierarchical Structure)**:
     * URL应该有清晰的**父子关系**，反映资源的层次关系。
     * ✅ 正确：`GET /api/v1/experts/{expert_id}/sessions`（专家→场次）
     * ✅ 正确：`GET /api/v1/users/me/followed-experts`（用户→当前用户→关注专家）
   
   * **HTTP方法表示操作 (HTTP Methods Represent Actions)**:
     * `GET`: 获取资源（如`GET /api/v1/experts`）
     * `POST`: 创建资源（如`POST /api/v1/experts`）
     * `PATCH`: 部分更新资源（如`PATCH /api/v1/experts/{expert_id}`）
     * `PUT`: 完整替换资源（如`PUT /api/v1/experts/{expert_id}`）
     * `DELETE`: 删除资源（如`DELETE /api/v1/experts/{expert_id}`）
   
   * **统一接口 (Uniform Interface)**:
     * **用户相关的操作**：统一在 `/api/v1/users/me/` 命名空间下
     * **管理员相关的操作**：统一在 `/api/v1/admin/` 命名空间下
     * **资源相关的操作**：统一在 `/api/v1/{resource}/` 命名空间下

* **日志与错误消息脱敏规范**:
   * **禁止在日志中打印敏感信息**:
     * ❌ **禁止**: 打印完整的数据库连接 URL（包含密码）
     * ✅ **必须**: 只打印非敏感的连接信息（不包含密码）
   
   * **日志脱敏规范**:
     * 创建日志脱敏工具函数 `app/core/logging_utils.py`
     * 提供统一的脱敏工具函数（如 `sanitize_log(data)`），用于对日志内容中的敏感字段进行处理
     * 业务代码禁止自行实现零散的脱敏逻辑，必须复用统一工具函数
     * 敏感信息识别规则：基于字段名与内容模式进行识别（如 `password`、`secret`、`token`、`authorization`、`api_key`）
   
   * **错误消息脱敏**:
     * **禁止**在异常处理中暴露敏感信息
     * **必须**只返回通用的错误消息给客户端
     * 记录详细错误信息到日志，但不返回给客户端

### 5.3. 详细实现模式与工程规范 (学院派)

**你必须同时遵循以下来自项目模板的详细工程规范：**

#### A. CRUD 层实现规范

* **事务处理**: (见 5.1) CRUD 层的"写"操作（create, update, remove）**必须**包含完整的 `try/except IntegrityError/finally` 块，并处理 `db.commit()` 和 `db.rollback()`。
* **N+1 防治**: 对于需要加载关系的查询（如 `get_with_sessions`），**必须**使用 `selectinload` 或 `joinedload` 预加载关系。
* **分页模式**: 分页查询（如 `get_multi_and_total`）**必须**通过两次查询实现：
   1. `select(func.count()).where(...)` 获取总数。
   2. `select(...).where(...).offset(skip).limit(limit)` 获取数据列表。
* **复杂查询**: 允许使用 `join` 并返回 `List[Dict]`，但业务逻辑（如计算 `heat` 值）**禁止**在 CRUD 层进行。

#### B. 数据库初始化脚本更新规范（必须执行）

**⚠️ 关键：数据库表创建前提**

当你生成新的 SQLAlchemy 模型代码（如 `app/models/experts.py`）时，**必须同时**更新数据库初始化脚本，否则新表不会被创建。

**两种更新方式（选择其一或两者都更新）**:

##### 方式1：更新 `models/__init__.py`（推荐，适用于 `init_db.py`）

如果项目使用 `app/init_db.py` 并通过 `import app.models` 自动导入所有模型，**必须**在生成CRUD层代码时，同时更新 `app/models/__init__.py`：

```python
# 在 app/models/__init__.py 中添加导入语句
# 专家模块模型（新增）
from .experts import Expert, UserExpertSubscription, LiveSessionExpert
```

**操作指令**（最小幅度修改要求）:
- **必须**识别新生成的所有模型类名称
- **必须**先检查文件末尾是否已有相同的导入语句（避免重复添加）
- **必须**在文件末尾追加新导入（保持空行和注释格式一致）
- **必须**添加注释说明这是新增模块
- **严禁**修改、删除或重新排序任何现有导入语句
- **严禁**修改文件中的任何其他代码

##### 方式2：更新 `app/scripts/create_tables.py`（适用于显式导入方式）

如果项目使用 `app/scripts/create_tables.py` 并显式导入每个模型，**必须**在生成CRUD层代码时，同时更新该脚本：

```python
# 在 app/scripts/create_tables.py 的 init_db() 函数中添加导入
# 导入专家模块模型（新增）
from ..models.experts import Expert, UserExpertSubscription, LiveSessionExpert
```

**操作指令**（最小幅度修改要求）:
- **必须**识别新生成的所有模型类名称
- **必须**先检查 `init_db()` 函数中是否已有相同的导入语句（避免重复添加）
- **必须**在现有模型导入区域之后追加新导入（保持相同的缩进级别）
- **必须**在 `init_db()` 函数中，在导入Base之后添加新模型的导入语句
- **必须**添加注释说明这是新增模块（例如：`# 导入专家模块模型（新增）`）
- **严禁**修改、删除或重新排序任何现有导入语句
- **严禁**修改函数中的任何其他代码或逻辑

##### 验证要求

运行数据库初始化脚本后，检查日志输出，确认新表出现在创建列表中。

#### C. Service 层实现规范

* **业务编排**: Service 层负责编排一个或多个 CRUD 调用，并组合业务逻辑（例如，`get_expert_with_sessions` 调用 `crud.get_with_sessions` 和 `crud.get_experts_by_session_id`，并执行相关逻辑）。
* **批量验证**: Service 层负责对输入列表（如 `expert_ids`）进行业务验证（例如检查列表长度 `len(expert_ids) > 100`）。
* **权限控制**: Service 层的所有需要权限检查的方法，**必须**接收 `user_id: UUID` 和 `user_role: Enum` 作为参数。
  * **必须**在函数内部执行业务逻辑检查（例如 `if not is_admin and expert.user_id != user_id:` 或 `if user_role not in [ADMIN, SUPERADMIN]:`）。
  * 如果检查失败，**必须** `raise PermissionDeniedException("权限不足...")`。

#### D. API (FastAPI) 层实现规范

* **权限控制**:
  * **必须**遵循 `5.0` 规范。API 端点**必须**依赖 `Depends(get_current_user)` 来获取 `Dict` (JWT Payload)。
  * **必须**在 `try` 块**之前**安全地解析出 `user_id: UUID` 和 `user_role: Enum`（见 `5.0` 示例代码）。
  * **严禁**使用 `Depends(get_current_admin_user)` 这类会直接抛出 `HTTPException` 的依赖。
  * **必须**在 `try/except` 块中捕获 Service 层抛出的 `PermissionDeniedException`，并返回 `JSONResponse(status_code=403, content=error_response(code=3003, ...))`。

* **路由定义**:
  1. **APIRouter 定义**: 必须在 `endpoints/experts.py` 文件中定义 `APIRouter(tags=["专家管理"])`，**严禁**在此时指定 `prefix`。
  2. **Prefix 挂载**: `prefix` **必须**在顶层 `api/v1/api.py` 文件的 `api_router.include_router(...)` 中统一指定。
  3. **[关键] 避免重复前缀**：
     * **全局路由前缀**：`main.py` 中已经配置了全局前缀 `/api/v1`（通过 `settings.API_V1_STR`）
     * **子路由前缀**：子路由前缀**不应该**包含 `/api/v1`，只包含模块路径（如 `/experts`）
     * **最终路径**：`{全局前缀}/{子路由前缀}/{端点路径}`（如 `/api/v1/experts/{expert_id}`）
     * **避免**：子路由前缀包含 `/api/v1`（如 `/api/v1/experts`），导致最终路径为 `/api/v1/api/v1/experts/{expert_id}`
  4. **端点路径**:
     * 集合端点 (如 `POST /experts`, `GET /experts`) **必须**使用 `path=""`（或 `/`）。
     * 单资源端点 (如 `GET /experts/{id}`) **必须**使用 `path="/{expert_id}"`。
     * 嵌套资源 (如 `GET /experts/{id}/sessions`) **必须**使用 `path="/{expert_id}/sessions"`。

  * **[关键] 路由前缀层级示例**：
    ```
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

  * **[关键] 路由前缀命名规范**：
    * 使用明确的模块路径（如 `/experts`）
    * 避免使用模糊或重复的路径
    * 保持路由前缀与模块名称一致

* **URL 拼接**:
  * 数据库**必须**只存储相对路径（例如 `/media/experts/.../banner.png`）。
  * 如果 API 响应需要返回完整 URL（如 `avatar_url`），**必须**注入 `request: Request` 依赖，获取 `base_url = str(request.base_url).rstrip('/')`，并返回拼接后的**完整 URL**。

* **响应格式化**:
  * 推荐使用 `format_..._response(orm_obj)` 辅助函数来标准化 ORM 对象到字典的转换，**然后再**进行 URL 拼接。

---

## 6. 功能需求提取

### 6.1. 专家信息管理功能

根据设计文档 Section 4.1（专家信息管理API），需要实现以下功能：

1. **创建专家**:
   - 端点：`POST /api/v1/experts`
   - 权限：仅管理员
   - 请求Schema：`ExpertCreate`
   - 响应：`ExpertItem`

2. **更新专家**:
   - 端点：`PUT /api/v1/experts/{expert_id}`
   - 权限：仅管理员
   - 请求Schema：`ExpertUpdate`
   - 响应：`ExpertItem`

3. **删除专家**:
   - 端点：`DELETE /api/v1/experts/{expert_id}`
   - 权限：仅管理员
   - 响应：成功消息

4. **获取专家详情**:
   - 端点：`GET /api/v1/experts/{expert_id}`
   - 权限：公开
   - 响应：`ExpertItem`

5. **获取专家列表**:
   - 端点：`GET /api/v1/experts`
   - 权限：公开
   - 参数：`page`, `size`
   - 响应：分页列表

6. **获取首页推荐专家列表**:
   - 端点：`GET /api/v1/experts/featured`
   - 权限：公开
   - 响应：`FeaturedExpertItem` 列表

7. **设置专家为推荐**:
   - 端点：`POST /api/v1/experts/{expert_id}/set-featured`
   - 权限：仅管理员
   - 响应：成功消息

8. **取消专家推荐**:
   - 端点：`DELETE /api/v1/experts/{expert_id}/set-featured`
   - 权限：仅管理员
   - 响应：成功消息

### 6.2. 专家关注功能

根据设计文档 Section 4.2（专家关注API），需要实现以下功能：

1. **关注专家**:
   - 端点：`POST /api/v1/experts/{expert_id}/follow`
   - 权限：需登录
   - 请求Schema：`ExpertFollowRequest`（只需token，无需请求体）
   - 响应：`ExpertFollowResponse`

2. **取消关注**:
   - 端点：`DELETE /api/v1/experts/{expert_id}/follow`
   - 权限：需登录
   - 响应：成功消息

3. **获取关注的专家列表**:
   - 端点：`GET /api/v1/experts/followed`
   - 权限：需登录
   - 参数：`page`, `size`
   - 响应：分页列表（包含直播状态）

4. **检查是否已关注**:
   - 端点：`GET /api/v1/experts/{expert_id}/is-followed`
   - 权限：需登录
   - 响应：是否关注

5. **批量获取关注专家的直播状态**:
   - 端点：`POST /api/v1/experts/followed/live-status`
   - 权限：需登录
   - 请求：`expert_ids` 列表
   - 响应：各专家的直播状态

### 6.3. 场次专家关联功能

根据设计文档 Section 4.1（专家信息管理API），需要实现以下功能：

1. **为场次设置专家**:
   - 端点：`POST /api/v1/sessions/{session_id}/experts`
   - 权限：仅管理员
   - 请求：专家列表（包含role和sort_order）
   - 响应：成功消息

2. **获取场次的专家列表**:
   - 端点：`GET /api/v1/sessions/{session_id}/experts`
   - 权限：公开
   - 响应：`SessionExpertItem` 列表

---

## 7. 交付物 (Deliverables)

请根据以上所有规则（5.0, 5.1, 5.2, 5.3），为专家模块生成两个新的、完全符合"学院派"风格的提示词文档：

### 7.1. CRUD 层函数代码生成提示词文档

- **输出路径**: `docs/提示词/直播核心功能模块/专家模块设计文档-专家信息-专家关注---CRUD层代码生成提示词.md`
- **这是用于直接生成CRUD层代码的提示词，不是母版**

### 7.2. Service 层和 API 层函数代码生成提示词文档

- **输出路径**: `docs/提示词/直播核心功能模块/专家模块设计文档-专家信息-专家关注---Service层和API层代码生成提示词.md`
- **这是用于直接生成Service层和API层代码的提示词，不是母版**

**生成要求**:
- **必须包含项目结构与上下文信息**：从"2. 核心上下文"部分提取项目结构信息，包含在生成的提示词文档中
- **必须明确模型定义来源**：在生成的CRUD层代码生成提示词文档中，明确标注模型定义是从已生成的代码文件（`backend/live_core_service/app/models/experts.py`）引用，而不是从设计文档提取
- **必须明确Schema定义来源**：在生成的Service/API层代码生成提示词文档中，明确标注Schema定义是从已生成的代码文件（`backend/live_core_service/app/schemas/experts.py`）引用，而不是从设计文档提取
- **优先使用已有代码**：首先检查 `backend/live_core_service/app/models/experts.py` 和 `backend/live_core_service/app/schemas/experts.py` 是否存在，如果存在，优先引用已有代码，而不是从设计文档提取
- **必须包含文件路径信息**：明确说明生成的代码文件应该放在哪里（如 `app/crud/experts.py`、`app/services/expert_service.py`、`app/api/v1/endpoints/experts.py`）
- **必须包含导入路径规范**：明确说明如何导入依赖的模块（如 `from app.models.experts import Expert, UserExpertSubscription, LiveSessionExpert`、`from app.schemas.experts import ExpertCreate, ExpertUpdate, ExpertItem, ...`）
- **必须包含现有代码参考**：列出类似模块的现有代码文件路径（如 `app/crud/topic.py`、`app/services/topic_service.py`、`app/api/v1/endpoints/topic.py`），作为代码风格和结构参考
- **必须读取项目目录结构**：确保生成的提示词文档反映实际的项目结构
- **必须包含数据库初始化脚本更新要求**：明确指出需要更新哪个初始化脚本文件，并提供准确的导入语句模板

**注意**：不要生成"要求生成文档的文档"，而是直接生成用于生成代码的提示词文档。

---

**文档版本**: V1.0  
**创建日期**: 2026-01-18  
**状态**: 准备就绪

