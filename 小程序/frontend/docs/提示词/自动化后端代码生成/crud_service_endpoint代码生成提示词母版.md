
-----

### 【最终完整版】高效 AI 代码生成提示词 (架构风格迁移母版 v4.1 - 用户身份修复版)

**目标**：获取"实用派"设计文档的**内容**（例如：需要一个 `create_message` 函数），但**强制**将其套用在本文档定义的、完整的"学院派"**架构与工程规范**上。

#### **1. 角色定义 (Role Definition)**

你是一名精通"学院派"架构（Clean Architecture）的资深 Python 后端架构师。你擅长将业务需求（来自设计文档）解耦，并严格执行分层架构与高质量的工程实践。

#### **2. 核心上下文 (Core Context)**

  * **内容来源 (Design Doc)**: `["粘贴你的设计文档，比如，直播核心功能设计文档v3-增加tab和留言.md"]`

  * **项目路径**: `backend/live_core_service`（或根据实际项目路径调整）

  * **项目结构与上下文信息** (必须包含在生成的提示词文档中):
    
    **项目目录结构**:
    ```
    app/
    ├── models/          # SQLAlchemy 模型（数据层）
    │   ├── __init__.py
    │   ├── {module_name}.py  # 目标模块模型（如 Tag, Category, SessionTag）
    │   ├── topic.py     # 参考：专题模块模型（app/models/topic.py）
    │   └── ...
    ├── schemas/         # Pydantic Schema（数据验证层）
    │   ├── __init__.py
    │   ├── {module_name}.py  # 目标模块Schema
    │   ├── topic.py     # 参考：专题模块Schema（app/schemas/topic.py）
    │   └── ...
    ├── crud/            # CRUD 层（数据访问层）
    │   ├── __init__.py
    │   ├── {module_name}.py  # 目标模块CRUD（待生成）
    │   ├── topic.py     # 参考：专题模块CRUD（app/crud/topic.py）
    │   └── ...
    ├── services/        # Service 层（业务逻辑层）
    │   ├── __init__.py
    │   ├── {module_name}_service.py  # 目标模块Service（待生成）
    │   ├── topic_service.py  # 参考：专题模块Service（app/services/topic_service.py）
    │   └── ...
    ├── api/             # API 层（HTTP端点层）
    │   └── v1/
    │       ├── api.py   # 路由注册（app/api/v1/api.py）
    │       └── endpoints/
    │           ├── __init__.py
    │           ├── {module_name}.py  # 目标模块端点（待生成）
    │           ├── topic.py  # 参考：专题模块端点（app/api/v1/endpoints/topic.py）
    │           └── ...
    └── ...
    ```
    
    **文件命名规范**:
    - 模型文件: `{module_name}.py`（如 `content_management.py`）
    - Schema文件: `{module_name}.py`（如 `content_management.py`）
    - CRUD文件: `{module_name}.py`（如 `content_management.py`）
    - Service文件: `{module_name}_service.py`（如 `content_management_service.py`）
    - Endpoint文件: `{module_name}.py`（如 `content_management.py`）
    
    **导入路径规范**:
    - 模型导入: `from app.models.{module_name} import {ModelName}`
    - Schema导入: `from app.schemas.{module_name} import {SchemaName}`
    - CRUD导入: `from app.crud.{module_name} import {CRUDFunction}`
    - Service导入: `from app.services.{module_name}_service import {ServiceClass}`
    
    **模块依赖关系**:
    - CRUD 层 → Models（依赖）
    - Service 层 → CRUD 层（依赖）
    - Endpoint 层 → Service 层 + Schemas（依赖）
    
    **现有代码参考**:
    - 专题模块CRUD: `app/crud/topic.py`（可作为代码风格和结构参考）
    - 专题模块Service: `app/services/topic_service.py`（可作为代码风格和结构参考）
    - 专题模块Endpoint: `app/api/v1/endpoints/topic.py`（可作为代码风格和结构参考）
    
    **⚠️ 重要提示**:
    - 在生成具体模块的提示词文档时，**必须**将 `{module_name}` 替换为实际的模块名称（如 `content_management`）
    - **必须**读取项目目录结构，确认实际的文件路径和命名
    - **必须**列出类似模块的现有代码文件路径，作为代码风格和结构参考

  * **模型定义来源说明** (必须明确标注，优先使用已有代码):
    
    **在生成的CRUD层代码生成提示词文档中，模型定义应明确标注来源，并优先使用已有代码**:
    
    1. **优先使用已有代码**（推荐）:
       - **首先检查** `app/models/{module_name}.py` 是否存在
       - **如果存在**，直接引用已生成的模型文件路径：`app/models/{module_name}.py`
       - 标注：`【以下模型定义引用自已生成的代码：app/models/{module_name}.py】`
       - 或直接引用导入语句：`from app.models.{module_name} import {ModelName1}, {ModelName2}, ...`
       - **必须读取实际代码**，确保模型定义与已生成的代码一致
    
    2. **如果模型代码未生成**（从设计文档提取）:
       - 从设计文档（DDL）中提取模型定义
       - 标注：`【以下模型定义来自设计文档 DDL（Section 2），用于指导CRUD代码生成】`
       - 明确说明：这些模型定义是临时参考，实际代码应基于设计文档或已生成的模型代码
    
    3. **Schema定义来源**（同样优先使用已有代码）:
       - **首先检查** `app/schemas/{module_name}.py` 是否存在
       - **如果存在**，直接引用已生成的Schema文件路径：`app/schemas/{module_name}.py`
       - 标注：`【以下Schema定义引用自已生成的代码：app/schemas/{module_name}.py】`
       - **如果不存在**，从设计文档中提取Schema定义，并标注来源
    
    4. **建议流程**:
       - **推荐方案**：先根据设计文档生成模型和Schema代码，然后CRUD层代码生成提示词引用已生成的代码
       - **当前方案**：在CRUD层代码生成提示词中包含从设计文档提取的模型定义（需明确标注来源）
       - **关键原则**：**优先使用已有代码，避免重复定义**
    
       - **禁止**：在生成的提示词文档中重复定义已经在设计文档中明确定义的数据结构。

##### 5.2.1 依赖信息传递与读取规范 (MANDATORY)

**⚠️ 关键原则**：

在生成的具体模块提示词文档中，**必须**按照以下方式处理依赖关系和代码引用：

**A. 依赖信息的传递方式（动态读取，禁止硬编码）**：

1. **CRUD 层提示词文档**：
   - **必须**要求 AI "使用 `read_file()` 工具读取 Model 代码，提取所有字段名、类型、约束"
   - **必须**在生成的 CRUD 提示词中包含 Model 的字段摘要或引用（而非完整定义）
   - **目的**：确保 CRUD 操作时了解 Model 的结构

2. **Service/API 层提示词文档**：
   - **必须**要求 AI "使用 `read_file()` 工具读取 Model 代码，了解字段结构"
   - **必须**要求 AI "使用 `read_file()` 工具读取 Schema 代码，了解响应结构"
   - **必须**在生成的 Service/API 提示词中包含 Schema 的结构摘要或示例（而非完整定义）
   - **目的**：确保 Service 层构造响应时遵循 Schema 定义
   - **禁止**：在 Service/API 提示词中重复定义 Model 或 Schema 的完整代码

**B. 动态读取与上下文填充的抽象指导**：

> **核心方法论**：
> 生成的具体模块提示词文档**必须**引导 AI 动态读取实际代码，而非猜测。
>
> **关键原则**：
> 1. **禁止硬编码**：母版中不得硬编码任何具体 Model 的字段定义或 Schema 的完整结构
> 2. **强制读取**：必须要求 AI 使用 `read_file()` 工具读取依赖文件
> 3. **提取摘要**：提示词文档应包含从实际代码中提取的"关键信息摘要"（如字段名、类型、约束、响应结构）
> 4. **一致性保证**：确保字段名、函数名、变量名、返回类型结构与实际代码完全一致
>
> **具体实施步骤**（供生成的提示词文档遵循）：
>
> **步骤 1：读取 Model 代码并提取字段信息**
> ```markdown
> **执行者指令**：
> 1. 使用 `read_file()` 工具读取 Model 文件（如 `app/models/xxx.py`）
> 2. 提取所有字段信息：字段名、类型、约束（如 unique=True, nullable=False）
> 3. 记录主键、外键、索引等元信息
> 4. 识别验证器（如 `slug` 字段的验证规则）
>
> **生成提示词时，应包含摘要**：
> **Model 字段摘要**（基于 `app/models/xxx.py` 的实际定义）：
> - 主键字段：[字段名] (UUID)
> - 业务字段：
>   - [字段名1]: [类型] ([约束])
>   - [字段名2]: [类型] ([约束])
>   - [约束说明]：
>   - [唯一性字段1]: unique=True（必须使用唯一值）
>   - [验证规则字段]: [验证规则]
> ```
>
> **步骤 2：读取 Schema 代码并提取响应结构**
> ```markdown
> **执行者指令**：
> 1. 使用 `read_file()` 工具读取 Schema 文件（如 `app/schemas/xxx.py`）
> 2. 提取所有 Schema 类的字段定义
> 3. 识别嵌套结构（如 `data` 字典包含业务数据）
> 4. 记录必需字段、可选字段、默认值
>
> **生成提示词时，应包含摘要**：
> **Schema 响应结构摘要**（基于 `app/schemas/xxx.py` 的实际定义）：
> - 响应类名：[ResponseSchema]
> - 标准字段：code, message, timestamp
> - 业务数据结构：[嵌套结构说明]
> - 必需字段：[字段列表]
> ```
>
> **步骤 3：生成 CRUD 操作时的约束应用**
> ```markdown
> **执行者指令**：
> 1. 基于 Model 字段摘要，生成 CRUD 操作说明
> 2. 对于 unique=True 字段，**必须**使用唯一值（推荐：Faker 或 UUID）
> 3. 对于有验证器的字段（如 `slug`），**必须**符合验证规则
>
> **禁止行为**：
> - ❌ 禁止硬编码具体的字段值（如 "微创手术"）
> - ❌ 禁止违反验证规则（如 `slug` 包含下划线但规则要求连字符）
> - ❌ 禁止使用不符合类型的值（如 datetime 字段使用字符串）
>
> **推荐行为**：
> - ✅ 使用唯一值生成模式：`f"{fake.word()}_{uuid.uuid4().hex[:6]}"`
> - ✅ 遵循验证器规则：根据实际验证规则生成有效值
> - ✅ 使用正确的字段类型：datetime 使用 `datetime.now()`，而非 ISO 字符串
> ```
>
> **步骤 4：生成 Service 层返回时的响应构造**
> ```markdown
> **执行者指令**：
> 1. 基于 Schema 响应结构摘要，生成 Service 返回说明
> 2. **必须**按照 Schema 定义的嵌套结构构造返回对象
> 3. 业务数据**必须**在嵌套结构中（通常是 `data` 字典）
>
> **禁止行为**：
> - ❌ 禁止将业务数据作为顶层字段（如 `session_id`, `mode`, `tags`）
> - ❌ 禁止使用 Schema 未定义的字段
> - ❌ 禁止违反嵌套结构要求
>
> **推荐行为**：
> - ✅ 按照实际 Schema 构造返回对象（基于 `app/schemas/xxx.py`）
> - ✅ 业务数据在嵌套结构中：`data={"field": value}`
> - ✅ 标准字段完整：code, message, data, timestamp
> ```
>
> **关键要点**：
> - ✅ 动态读取：必须使用 `read_file()` 读取实际代码，而非猜测
> - ✅ 提取摘要：提示词文档包含"关键信息摘要"，而非完整定义
> - ✅ 一致性保证：字段名、函数名、变量名、返回类型结构与实际代码一致
> - ✅ 禁止硬编码：母版中不得硬编码具体 Model 或 Schema 的完整定义
> - ✅ 通用性：适用于所有模块，通过动态读取实现灵活适配
>

**C. 适用范围**：

本节的所有要求**仅适用于**：
||- 生成"具体模块提示词文档"时（如 `xxx-Service层和API层代码生成提示词.md`）
||- **不适用于**：
  - 生成"CRUD/Service/API 层实际代码"时（那是 AI 的执行任务）
  - 生成"测试代码"时（那是测试母版的职责）

**关键要点**：

- ✅ 通过动态读取和抽象指导来说明"应该怎么做"，而不是硬编码具体内容
- ✅ 保持母版的通用性和抽象性，适用于所有模块
- ✅ 让生成的具体提示词文档能够灵活地读取实际代码并提取关键信息
- ✅ 避免在母版中为每个具体模块硬编码详细的 Schema 或 Model 定义

#### **3. 任务目标 (Task Objective)**

你的任务是为"内容来源"文档中的功能（例如 "Tab 和 Message"），生成一套**新的** CRUD 和 Service/API 层代码生成提示词。

#### **4. 核心架构约束 (\!\!\! 关键规则 \!\!\!)**

你**必须**执行一次**架构风格迁移**。

 * 你必须使用"内容来源"文档来识别**需要实现的功能**（例如 API 列表、业务逻辑点如 URL 过滤）。
      * [关键] 你必须识别所有功能点，这既包括"全新创建"的功能（如 create\_message），也包括对"现有功能"的"**增量修改**"（例如在 GET /rooms/{id} 中添加 tabs 字段）。你必须两者都识别出来，不得遗漏。
      * **列表搜索（不得遗漏）**：凡设计文档中定义为「返回列表」的 GET 且需支持搜索（或设计/前端规范要求列表可搜），**必须**识别并实现：Query 参数 `q`、`search_type`；**默认**须支持 **ID 精确查询**（`search_type=id` 时主键精确）与**字符串字段模糊查询**（对可配置的字符串搜索字段做 ILIKE 模糊）。**字符串搜索字段以设计文档为准，禁止在提示词或代码中写死为 name**；字符串搜索字段即该列表的「可配置字符串搜索字段列表」，由设计文档写明或明确配置（如 name、title、displayName 等）。若设计文档未写明，则从 Model 的字符串类型列中选取业务语义最合适的一列（如 name、title）并在注释中注明。**若设计文档明确要求支持搜索但未写明该列表的字符串搜索字段，应在实现前回溯设计文档补充该配置**，不得长期仅依赖「选一列+注释」而不更新设计。
 * 你必须**严格**使用下文的"**5. 架构约束与实现规范**"来定义**如何实现**这些功能（即代码风格、分层、规范）。

-----

#### **5. 架构约束与实现规范 (\!\!\! 必须遵守 \!\!\!)**

##### 5.0 【统一规范：用户身份解析与参数传递】

**📌（标准）API 层用户提取规范（JWT→UUID+String）**
**`current_user` 永远是一个 JWT payload `dict`，而不是 ORM `User` 模型**。

**JWT Payload 结构**（参考用户模块设计文档 Section 7.1.4）：
|- `user_id`: string（UUID 字符串）
|- `role`: string（用户角色，例如 `'REGULAR'`, `'ADMIN'`）

**API 层必须使用以下模式解析**：

```python
current_user: Dict = Depends(get_current_user)  # 或 get_current_user_optional

user_id = uuid.UUID(current_user["user_id"])  # 使用 user_id 而非 sub
user_role = current_user.get("role", "REGULAR").upper()  # ← 直接使用字符串，无需转换
```

**🚨 强制要求（最高优先级）**：
- **必须**调用 `.upper()` 转换role为大写：`role = current_user.get("role", "REGULAR").upper()`
- **禁止**直接使用：`role = current_user.get("role")`  ❌
- **原因**：JWT中的role可能是小写或大小写混合，必须统一转换为大写后再传递给Service层，与设计文档保持一致（REGULAR/ADMIN/SUPERADMIN）

**⚠️ 重要说明**：
1. JWT Payload 中的 `role` 字段已经是 **string** 类型，无需转换为枚举
2. 本项目**统一使用字符串**进行角色判断（参考用户模块设计文档）
3. 只有 `live_features` 模块使用 `LiveRoomMessageUserRole` 枚举（这是该模块的特殊需求）
4. 其他模块（topic, room, content_management, experts 等）都应该使用字符串

**📌（标准）Service 层用户参数规范**
Service 层方法**不得**接受实体类 `User`，**必须**统一为：

```python
async def some_action(
    self,
    user_id: UUID,
    user_role: str,  # ← 使用字符串类型（来自 JWT role 字段）
    ...
):
```

**权限检查实现**：
```python
# 使用字符串比较
if user_role not in ['ADMIN', 'SUPERADMIN']:
    raise PermissionDeniedException("权限不足，需要管理员权限")
```

**🚨 强制要求（最高优先级）**：
- **必须**使用大写进行角色比较：`if role not in ['ADMIN', 'SUPERADMIN']:`
- **禁止**使用小写：`if role not in ['admin', 'superadmin']:`  ❌
- **禁止**使用混合大小写：`if role not in ['Admin', 'SuperAdmin']:`  ❌
- **禁止**使用其他值：`if role not in ['user', 'admin', 'superadmin']:`  ❌（应使用REGULAR而非user）
- **原因**：与设计文档保持一致，JWT role字段统一使用大写（REGULAR/ADMIN/SUPERADMIN）

**❌ 错误示例（禁止使用）**：
```python
# Service层错误
if role not in ['admin', 'superadmin']:  # ❌ 使用小写
if role not in ['Admin', 'SuperAdmin']:  # ❌ 使用混合大小写
if role not in ['user', 'admin', 'superadmin']:  # ❌ 使用小写且值错误（应使用REGULAR）
```

**✅ 正确示例（必须使用）**：
```python
# Service层正确
if role not in ['ADMIN', 'SUPERADMIN']:  # ✅ 使用大写
if role not in ['REGULAR', 'ADMIN', 'SUPERADMIN']:  # ✅ 使用大写（如果需要检查REGULAR）
```

**💡 为什么使用字符串而不是枚举**：
1. **符合设计**：用户模块设计文档明确 JWT Payload 的 `role` 是 string 类型
2. **符合实践**：项目 90% 的模块都使用字符串（topic, room, content_management 等）
3. **简单高效**：无需类型转换，直接比较
4. **避免引入**：不需要创建 `app/core/enums.py` 文件

**⚠️ 重要提示**：本系统统一使用 `user_id` 字段，而非 JWT 标准的 `sub` 字段。这是一个有意识的设计决策，已在所有文档中统一执行。

**代码提取方式对比**：
```python
# ✅ 正确做法（与v6主文档一致）
current_user: Dict = Depends(get_current_user)  # 或 get_current_user_optional
user_id = UUID(current_user["user_id"])  # 使用 user_id 而非 sub
user_role = current_user.get("role", "REGULAR").upper()  # ✅ 必须调用.upper()

# ❌ 错误做法（禁止使用）
# user_id = UUID(current_user["sub"])  # 系统中不存在此字段
# role = current_user.get("role")  # ❌ 缺少.upper()调用
# role = current_user.get("role", "regular")  # ❌ 默认值应使用大写REGULAR
```

---

##### 5.0.5 【新增】权限管理策略（通用权限体系）

本节提供一套通用的权限管理策略，适用于所有模块（Topic, Room, Expert, Content 等）。核心思想是：
- **双轨鉴权模式**：Strict Auth（写操作）+ Optional Auth（读操作）
- **三层职责分工**：API 层负责 Authentication（认证），Service 层负责 Authorization（鉴权），CRUD 层负责 SQL 层权限过滤
- **权限守卫函数**：Service 层实现统一的权限检查函数

**📌 三层权限职责分工（完整版）**：

1. **API 层 (Endpoint)**：负责 **Authentication (认证)** —— 解析"你是谁"（User 还是 Anonymous）
   - 使用 `get_current_user` 或 `get_current_user_optional` 获取用户信息
   - 从 JWT Payload 中提取 `user_id` (UUID) 和 `role` (str)
   - 将用户身份传递给 Service 层
   - **不做权限判断**，不直接拒绝请求

2. **Service 层**：全权负责 **Authorization (鉴权)** —— 判定"你能看吗/你能改吗"
   - 接收 `user_id: UUID` 和 `user_role: str` 参数
   - 调用权限守卫函数（如 `_check_resource_visibility`, `_check_write_permission`）
   - 根据权限检查结果决定是否允许访问
   - 对于需要权限过滤的列表查询，将 `current_user_id` 和 `role` 传递给 CRUD 层

3. **CRUD 层**：负责在 **SQL 层面应用权限过滤**
   - **关键职责**：在查询语句（WHERE 条件）中直接应用权限过滤逻辑
   - **接收参数**：`current_user_id: Optional[UUID]` 和 `role: Optional[str]`
   - **Admin查询**：无权限过滤，可查看所有状态的资源
   - **Regular User查询**：应用 `WHERE (status='published' OR (status IN ('draft', 'archived') AND user_id=current_user_id))`
   - **Anonymous查询**：应用 `WHERE status='published'`
   - **业务筛选与权限过滤**：使用 AND 关系组合，确保权限过滤决定可见范围，业务筛选在可见范围内筛选
   - **性能关键**：禁止查出所有数据在内存中再过滤（性能陷阱）

**📌 双轨鉴权模式**

| 模式 | 行为 | 适用场景 | API 层依赖函数 |
|-------|------|---------|-----------------|
| **Strict Auth**（强制鉴权） | 无 Token → 401 Unauthorized<br>Token 无效 → 401 Unauthorized | 所有写操作（创建、修改、删除） | `get_current_user` |
| **Optional Auth**（可选鉴权） | 无 Token → `None`（视为匿名用户）<br>**Token 无效/过期** → 401 Unauthorized | 所有读操作（列表、详情） | `get_current_user_optional` |

**⚠️ 关键原则**：
1. **严禁降级为匿名**：Token 无效时必须报 401，不能返回 `None` 降级为匿名用户。否则已登录用户在 Token 过期时会莫名其妙看不到自己的私有资源，导致前端状态错乱。
2. **职责清晰**：API 层只负责解析"你是谁"（User vs Anonymous），Service 层负责判定"你能看吗/你能改吗"。

**📌 权限守卫函数（Service 层专用）**

Service 层应实现以下通用的权限守卫函数：

**类型 1：管理员权限检查**
```python
def _check_admin_permission(
    self,
    user_role: str  # 当前用户角色（非 None，必须是大写：ADMIN/SUPERADMIN/REGULAR）
) -> None:
    """
    通用的管理员权限校验
    
    权限判断流程：
        1. Admin（role in ['ADMIN', 'SUPERADMIN']）→ 通过
        2. 其他情况 → 403（权限不足）
    
    适用场景：
        - 需要管理员权限的操作（如创建/删除系统级资源、管理配置等）  
        - 系统级配置操作
        - 示例：内容管理模块的标签/分类创建、用户管理、系统设置等
    
    Raises:
        PermissionDeniedException(403): 权限不足，需要管理员权限
    """
    # 🚨 必须使用大写进行比较
    if user_role not in ['ADMIN', 'SUPERADMIN']:
        raise PermissionDeniedException("权限不足，需要管理员权限")
```

**类型 2：资源可见性检查**
```python
def _check_resource_visibility(
    self,
    resource: Any,  # 模型对象（有可见性字段）
    user_id: Optional[UUID],  # 当前用户 ID
    role: Optional[str],  # 当前用户角色
    is_published_field: str = "is_private",  # 可见性字段名（默认 is_private）
    published_value: Any = False  # 公开状态的值（is_private=False）
) -> None:
    """
    通用的资源可见性校验逻辑
    
    参数说明：
        - resource: 资源对象（Room, Topic, Expert 等）
        - user_id: 当前用户的 public_id（匿名时为 None）
        - role: 当前用户的角色（匿名时为 None）
        - is_published_field: 可见性字段名（如 "is_private", "status"）
        - published_value: 公开状态的值（如 False, 'published'）
    
    权限判断流程（以 Room 模块为例）：
        1. 资源是公开状态（is_private=False）→ 直接通过
        2. 资源是私有状态（is_private=True）+ 未登录 → 404
        3. Admin（role in ['ADMIN', 'SUPERADMIN']）→ 通过（上帝视角）
        4. Owner（resource.user_id == user_id）→ 通过
        5. 其他情况 → 404（防止资源探测）
    
    Raises:
        NotFoundException(404): 资源不存在或无权访问（隐藏私有资源的存在性）
    """
    # 获取资源的可见性状态
    is_public = getattr(resource, is_published_field) == published_value
    
    # 1. 公开资源：直接通过
    if is_public:
        return
    
    # 2. 私有资源且未登录：拒绝（返回 404）
    if not user_id:
        raise NotFoundException("Resource not found")
    
    # 3. 管理员：上帝视角通过（🚨 必须使用大写）
    if role in ['ADMIN', 'SUPERADMIN']:
        return
    
    # 4. 资源创建者：通过
    if resource.user_id == user_id:
        return
    
    # 5. 其他用户：拒绝（返回 404 隐藏存在性）
    raise NotFoundException("Resource not found")
```

**类型 3：写权限检查**
```python
def _check_write_permission(
    self,
    resource: Any,  # 模型对象
    user_id: UUID,  # 当前用户 ID
    role: str  # 当前用户角色（非 None）
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
    # 管理员：上帝视角通过（🚨 必须使用大写）
    if role in ['ADMIN', 'SUPERADMIN']:
        return
    
    # 资源创建者：通过
    if resource.user_id == user_id:
        return
    
    # 其他用户：拒绝（返回 403）
    raise PermissionDeniedException(
        "You don't have permission to modify this resource"
    )
```

**⚠️ 关键原则**：

1. **404 伪装机制**：
   - 对于无权访问的私有资源，必须抛出 `NotFoundException`（404），而非 `PermissionDeniedException`（403）
   - **原因**：如果返回 403，攻击者可以通过遍历 ID，根据返回码（404 vs 403）判断哪些 ID 是真实存在的私密资源
   - **实现**：`raise NotFoundException("Resource not found")`

2. **Admin 特权处理**：
   - Admin 角色可以访问所有状态的资源，不受可见性限制
   - **实现**：在权限守卫函数中优先检查 `role in ['ADMIN', 'SUPERADMIN']`

3. **管理员权限检查**：
   - 对于需要管理员权限的操作，必须使用 `_check_admin_permission` 函数
   - **适用场景**：创建/删除系统级资源（如系统配置、用户管理、内容管理等）、系统级配置操作
   - **实现**：在 Service 层方法开始时调用 `self._check_admin_permission(user_role)`
   - **示例**：
     ```python
     # 示例：内容管理模块的标签创建（适用于所有需要管理员权限的创建操作）
     async def create_tag(self, tag_in: TagCreate, user_id: UUID, user_role: str) -> TagItem:
         # 检查管理员权限
         self._check_admin_permission(user_role)
         # ... 后续业务逻辑
     # 注意：此示例使用 Tag 模块，但模式适用于所有需要管理员权限的操作
     ```

4. **模块适配示例**：

**Room 模块**（使用 `is_private` 字段）：
```python
# 调用通用函数（使用默认参数）
self._check_resource_visibility(room, user_id, role, 
    is_published_field="is_private", 
    published_value=False)
```

**Topic 模块**（使用 `status` 字段）：
```python
# Topic 的可见性判断比较复杂，因为 'published' 是一个具体的枚举值
# 这里不使用通用函数，而是直接实现

def _check_topic_visibility(
        self,
        topic: Topic,
        user_id: Optional[UUID],
        role: Optional[str]
) -> None:
    """Topic 专用的可见性校验（基于 status 字段）"""
    # 1. 已发布专题：直接通过（相当于 is_private=false）
    if topic.status == 'published':
        return
    
    # 2. 草稿/已归档专题且未登录：拒绝（返回 404）
    if not user_id:
        raise TopicNotFoundException("Topic not found")
    
    # 3. 管理员：上帝视角通过（🚨 必须使用大写）
    if role in ['ADMIN', 'SUPERADMIN']:
        return
    
    # 4. 资源创建者：通过
    if topic.user_id == user_id:
        return
    
    # 5. 其他已登录用户：拒绝（返回 404 隐藏存在性）
    raise TopicNotFoundException("Topic not found")
```

---

**📌 Repository 层权限过滤（SQL 层过滤）**

**原则**：尽可能下推过滤逻辑到数据库，避免内存过滤（性能陷阱）。

```python
class TopicCRUD:
    async def get_multi(
        self,
        session: AsyncSession,
        current_user_id: Optional[UUID],  # ← 权限参数（当前用户的 public_id）
        role: Optional[str],  # ← 权限参数（当前用户的角色）
        page: int,
        size: int,
        status: Optional[str] = None,  # ← 业务筛选参数
        title: Optional[str] = None  # ← 业务筛选参数
    ) -> Tuple[List[Topic], int]:
        """查询可见的专题列表（带权限过滤和业务筛选）"""
        stmt = select(Topic)
        
        # 1. 先应用业务筛选条件
        business_filters = []
        if title:
            # 专题标题模糊匹配（不区分大小写）
            business_filters.append(Topic.title.ilike(f'%{title}%'))
        if status:
            business_filters.append(Topic.status == status)
        
        # 2. 再应用权限过滤条件（根据用户身份决定可见范围，独立于业务筛选条件）
        permission_filters = []
        if role in ['ADMIN', 'SUPERADMIN']:
            # 管理员：无权限过滤，可查看所有状态的专题
            pass
        elif current_user_id:
            # 普通用户：Published OR (Draft/Archived AND Own)
            # 无论业务筛选条件中是否指定了 status，权限过滤都需要确保用户只能看到自己有权访问的专题
            permission_filters.append(
                or_(
                    Topic.status == 'published',
                    and_(
                        Topic.status.in_(['draft', 'archived']),
                        Topic.user_id == current_user_id
                    )
                )
            )
        else:
            # 匿名用户：Only Published
            permission_filters.append(Topic.status == 'published')
            # 如果业务筛选条件中指定了非 published 状态，与权限过滤条件（Only Published）冲突，结果集自然为空
        
        # 3. 合并业务筛选条件和权限过滤条件（AND 关系）
        all_filters = business_filters + permission_filters
        if all_filters:
            stmt = stmt.where(and_(*all_filters))
        
        # 计算总数（必须应用相同的 WHERE 条件）
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await session.execute(count_stmt)
        total = total_result.scalar_one()
        
        # 应用分页和排序
        stmt = stmt.order_by(Topic.created_at.desc())
        stmt = stmt.offset((page - 1) * size).limit(size)
        
        # 执行查询
        result = await session.execute(stmt)
        topics = result.scalars().all()
        
        return list(topics), total
```

**通用示例 2：使用 `is_active` 字段的权限过滤**（适用于 Tag、Category 等模块）

```python
class TagCRUD:
    async def get_tags(
        self,
        session: AsyncSession,
        current_user_id: Optional[UUID],  # ← 权限参数
        role: Optional[str],  # ← 权限参数
        search: Optional[str] = None,  # ← 业务筛选参数
        limit: int = 100
    ) -> List[Tag]:
        """查询可见的标签列表（带权限过滤和业务筛选）"""
        stmt = select(Tag)
        
        # 1. 先应用业务筛选条件
        business_filters = []
        if search:
            business_filters.append(Tag.name.ilike(f'%{search}%'))
        
        # 2. 再应用权限过滤条件（根据用户身份决定可见范围）
        permission_filters = []
        if role in ['ADMIN', 'SUPERADMIN']:
            # 管理员：无权限过滤，可查看所有状态的标签（包括 is_active=False）
            # 如果业务需要，可以通过参数控制是否包含非激活标签
            pass
        else:
            # Regular User / Anonymous：仅查看激活标签
            permission_filters.append(Tag.is_active == True)
        
        # 3. 合并业务筛选条件和权限过滤条件（AND关系）
        all_filters = business_filters + permission_filters
        if all_filters:
            stmt = stmt.where(and_(*all_filters))
        
        # 应用排序和限制
        stmt = stmt.order_by(Tag.name).limit(min(limit, 500))
        
        # 执行查询
        result = await session.execute(stmt)
        tags = result.scalars().all()
        
        return list(tags)
```

**⚠️ 关键原则**：
1. **禁止内存过滤**：禁止查出所有数据在内存中再过滤（性能陷阱）
2. **权限与业务筛选 AND 关系**：业务筛选条件和权限过滤条件使用 AND 关系组合
3. **权限过滤优先级明确**：权限过滤决定可见范围，业务筛选在可见范围内筛选
4. **字段类型适配**：
   - **使用 `is_active` 字段**：适用于简单的激活/非激活状态（如 Tag、Category）
   - **使用 `status` 字段**：适用于复杂的状态枚举（如 Topic 的 published/draft/archived）
   - **使用 `is_private` 字段**：适用于公开/私有资源（如 Room）
5. **Admin 查询策略**：
   - 管理员通常可以查看所有状态的资源（包括非激活、草稿等）
   - 可以通过业务参数（如 `include_inactive`）控制是否包含非激活资源

**📌 API端点完整实现示例（包含角色转换和异常处理）**：

**示例1：需要管理员权限的写操作端点**：
```python
@router.post("/tags", response_model=TagItem, status_code=201)
async def create_tag(
    tag_data: TagCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> TagItem:
    """创建标签（Strict Auth + Admin）"""
    try:
        # 🚨 必须：提取并转换role
        current_user_id = UUID(current_user["user_id"])
        role = current_user.get("role", "REGULAR").upper()  # ✅ 必须调用.upper()
        
        # 调用Service层
        return await service.create_tag(db, tag_data, current_user_id, role)
    except PermissionDeniedException as e:
        raise HTTPException(status_code=403, detail=str(e))
    except InvalidParameterException as e:
        raise HTTPException(status_code=400, detail=str(e))
```

**示例2：公开接口（Optional Auth）**：
```python
@router.get("/tags", response_model=TagListResponse)
async def get_tags(
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
) -> TagListResponse:
    """获取标签列表（Public + Optional Auth）"""
    try:
        # 🚨 必须：提取并转换role（即使为None也要处理）
        current_user_id = UUID(current_user["user_id"]) if current_user else None
        role = current_user.get("role", "REGULAR").upper() if current_user else None  # ✅ 必须调用.upper()
        
        # 调用Service层
        return await service.get_tags_list(db, current_user_id, role)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
```

**示例3：需要写权限的操作**：
```python
@router.post("/sessions/{session_id}/tags", ...)
async def set_session_tags(
    session_id: UUID = Path(...),
    request_data: SessionTagsSetRequest = ...,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> SessionTagsSetResponse:
    """为场次设置标签（Strict Auth + Write）"""
    try:
        # 🚨 必须：提取并转换role
        current_user_id = UUID(current_user["user_id"])
        role = current_user.get("role", "REGULAR").upper()  # ✅ 必须调用.upper()
        
        # 调用Service层
        return await service.set_session_tags(db, session_id, request_data, current_user_id, role)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionDeniedException as e:
        raise HTTPException(status_code=403, detail=str(e))
    except InvalidParameterException as e:
        raise HTTPException(status_code=400, detail=str(e))
```

**🚨 关键原则**：
1. **所有端点必须**在try块之前提取并转换role
2. **所有端点必须**添加完整的异常处理（至少包含PermissionDeniedException、NotFoundException、InvalidParameterException）
3. **所有端点必须**将异常转换为正确的HTTP状态码

---

##### 5.1 核心架构原则 (学院派)

**如果"内容来源"文档中的架构描述与本节规范冲突，本节规范（学院派）永远是最高优先级。**

* **事务处理 (Transaction)**:

   * **设计文档可能说**："Service 层处理事务"。
   * **你必须遵循 (学院派)**："**CRUD 层**必须处理 `db.commit()`, `db.rollback()`, 和 `try/except IntegrityError`"。

   * **[关键] Service 层事务管理策略（默认：依赖 API 层事务）**：
          * **默认策略（推荐）**：依赖 API 层事务
              - Service 层**不使用** `async with self.db.begin():`
              - FastAPI 的依赖注入已经为每个请求创建了事务
              - Service 层直接使用 `self.db` 进行数据库操作
              - **适用场景**：大多数 CRUD 操作、单个资源操作
          * **特殊情况**：需要手动事务管理
              - Service 层**必须使用** `async with self.db.begin():`
              - **适用场景**：批量操作、复杂的业务逻辑、需要原子性执行多个操作
              - **必须包含**：异常处理和回滚
          * **事务一致性要求**：
              - Service 层的所有数据库操作应该在同一个事务中
              - 避免部分操作在事务中，部分操作在事务外
              - 异常必须触发回滚（手动事务管理时）
   *   **[关键] Service 层在 commit 前序列化 ORM（异步 SQLAlchemy 避免 MissingGreenlet）**：
          * **问题**：Service 内若先 `await db.commit()`，再对 CRUD 返回的 ORM 对象做 `Schema.model_validate(orm_obj)` 或访问属性构造响应，SQLAlchemy 会使会话中的对象过期，访问属性触发懒加载；在异步环境下懒加载需 await，导致 `MissingGreenlet: greenlet_spawn has not been called` 及类似 "Error extracting attribute ... (for XxxItem validation from Xxx object)" 的报错，接口 500。数据库写入已成功，失败发生在构建响应时。
          * **正确做法**：在调用 `await db.commit()` **之前**，先将 CRUD 返回的 ORM 列表/对象序列化为 Pydantic（如 `payload = [ResponseSchema.model_validate(orm_obj) for orm_obj in items]`），再 `await db.commit()`，最后用 `payload` 构造响应返回。
          * **适用**：任何 Service 方法中「先调 CRUD 得到 ORM 列表/对象 → commit → 再根据 ORM 构造响应」的流程，均须先序列化再 commit。
   *   **[关键] CRUD 层批量操作与事务边界管理（2024-01 新增）**：
      *     - **批量操作的定义**：当 CRUD 层方法需要在一个方法内执行多个相关数据库操作（如 INSERT + UPDATE）时，这些操作必须确保原子性。
      *     - **常见场景**：
      *       - 场景 1：插入新记录并更新旧记录（如创建观看历史时，需要将同一用户和场次的旧记录的 `is_latest` 设为 `False`）
      *       - 场景 2：批量插入或批量更新
      *       - 场景 3：删除操作后更新关联数据
      *     - **事务边界管理规范**：
      *       - **规则 1：显式事务控制（推荐）**：使用 `async with db.begin():` 显式定义事务边界，确保所有相关操作在一个事务中。
      *         - 优点：事务边界清晰，不会互相干扰，适合复杂业务逻辑。
      *         - 适用场景：批量操作、需要原子性的多个操作。
      *       -         - 实现示例：
      *           ```python
      *           async def create_watch_history(...):
      *               db.add(history)
      *               async with db.begin():  # 显式事务
      *                   # 先 UPDATE 旧记录
      *                   stmt = update(...).where(...).values(is_latest=False)
      *                   await db.execute(stmt)
      *                   # 再 INSERT 新记录
      *                   await db.flush()  # 放入缓冲区但不提交
      *                   await db.commit()  # 统一提交
      *               # async with 块退出时自动 commit
      *               await db.refresh(history)
      *               return history
      *           ```
      *       - **规则 2：单次提交模式（简单场景）**：对于简单的单个 CRUD 操作（如 create、get、delete），可以使用单次 `db.commit()`。
      *         - 优点：简单直接，适合标准 CRUD 操作。
      *         - 适用场景：不涉及批量操作或复杂业务逻辑的单个操作。
      *         - 注意：如果需要后续操作（如 INSERT 后再 UPDATE），必须使用显式事务或确保执行顺序。
      *       - **规则 3：禁止混合模式**：严禁在同一个方法中混合使用显式提交和隐式提交，避免事务边界不清晰。
      *         - 例如：不能既使用 `await db.commit()` 又使用 `async with db.begin():` 而没有明确的边界。
      *         - 例如：不能在 try 块中部分提交、部分不提交。
      *       - **规则 4：UPDATE 的执行顺序（关键）**：当需要先 UPDATE 再 INSERT 时（如创建观看历史）：
      *         - 必须确保 UPDATE 语句的 WHERE 条件在 INSERT 前是有效的。
      *         - 如果使用 `WHERE is_latest=True AND id != new_history_id`，必须在 INSERT 后执行 UPDATE。
      *         - 或者在同一个事务中先执行 UPDATE，再执行 INSERT。
      *         - 禁止在 INSERT 还未提交时执行 UPDATE，否则可能找不到记录（rowcount = False）。
      *       - **规则 5：异常处理**：无论使用哪种事务模式，都必须在 try/except 中处理异常并回滚。
      *         - 必须捕获 `IntegrityError` 并调用 `await db.rollback()`。
      *         - 必须包含完整的异常处理逻辑，避免事务泄漏。
      *       - **推荐实践总结**：
      *         1. 批量操作：使用显式事务（`async with db.begin():`）。
      *         2. 简单操作：可以使用单次 `db.commit()`。
      *         3. 避免：混合使用显式提交和隐式提交。
      *         4. 异常处理：必须包含完整的 try/except/rollback 逻辑。
      *       - **注意事项**：
      *         - 事务隔离级别（Isolation Level）：确保数据库配置的事务隔离级别符合业务需求（如 READ COMMITTED, REPEATABLE READ）。
      *         - 对于并发高的场景，可能需要更高的事务隔离级别来避免幻读问题。
      *         - 连接池管理：确保正确使用连接池，避免连接泄漏。
      *         - 避免长时间运行的事务，及时提交或回滚。
      *     - **关键要点**：
      *       - 批量操作必须确保原子性（要么全部成功，要么全部失败）。
      *       - 必须明确事务边界（使用 `async with db.begin():` 或单次 `db.commit()`）。
      *       - 必须包含完整的异常处理和回滚逻辑。
      *       - UPDATE + INSERT 场景必须注意执行顺序。
      *       - 事务隔离级别和连接池管理要正确配置。
      *       - **验证方法**：在测试批量操作的代码中，应该验证事务的原子性和一致性。
      *       - 使用增量验证（测试前后的记录数量变化）来确保操作正确。
      *       - **与设计文档的关系**：
      *       - 如果设计文档提到"每次创建观看历史时，将旧记录的 is_latest 设为 false，新记录设为 true"，CRUD 层必须实现这一逻辑。
      *       - CRUD 层可以通过在同一个事务中执行 UPDATE 和 INSERT 来实现这一逻辑。
      *       - Service 层（如果存在）可以调用单个 CRUD 方法来简化事务管理。
      *     - **禁止**：在 CRUD 层实现中，禁止以下行为：
      *       - 禁止在依赖 API 层事务的 CRUD 方法中使用 `async with db.begin():` 手动开启新事务（可能导致嵌套事务问题）。
      *       - 禁止在 CRUD 方法中混合使用多种事务管理模式（部分使用 `db.commit()`，部分使用 `db.begin():`）。
      *       - 禁止在事务边界外执行数据库写入操作。

  * **异常处理 (Exception)**:

      * **设计文档可能说**："Service 层抛出 404/4004 错误"。
      * **你必须遵循 (学院派)**："**Service 层**必须抛出**自定义异常** (例如 `MessageNotFoundException(Exception)`)。**API (Endpoint) 层**必须使用 `try/except` 捕获这些自定义异常，并将其转换为 `JSONResponse`。"

  * **日志记录 (Logging)**:

      * **设计文档可能说**："Service 层记录错误日志"。
      * **你必须遵循 (学院派)**："**CRUD 层**负责记录数据库错误日志。**API (Endpoint) 层**负责记录业务异常日志和未捕获的 500 错误日志。"
      * **补充**：API 层在捕获未预期异常并返回 500 时，须使用 `logger.exception` 等输出**完整 traceback**，便于区分类型错误与数据库错误；业务/参数错误须返回 4xx，禁止以笼统「数据库操作错误」替代。

  * **入参类型与校验 (Request Body / Query)**:

      * 请求体或 Query 中的 UUID、枚举等须在 Service 或 Endpoint 层**显式转换**（如 `uuid.UUID(str(x))`）并校验，失败即抛 `InvalidParameterException`（4xx）；**禁止**将 JSON 原始类型直接传入 CRUD/ORM。
      * *示例*：列表项中的 `expert_id` 为字符串时，须在 Service 层归一化为 `uuid.UUID` 后再传 CRUD；转换失败返回 400 而非 500。

  * **安全异步异常处理 (Safe Async Exception Handling)**:

      * **规则**：在任何 `try...except` 块中，如果需要使用来自 ORM 对象（如 `current_user`）的属性（如 `current_user.id`）进行日志记录，这些属性**必须在进入 `try` 块之前**被提取并存储到局部变量中。
      * **指令**：**严禁**在捕获了数据库相关异常的 `except` 块中访问可能已失效会话的 ORM 对象的属性。
      * **指令**：**严禁**在 `db.commit()` 之后为构建 HTTP 响应而访问 ORM 对象属性；否则易触发懒加载，在异步上下文中导致 `MissingGreenlet`。应使用请求校验阶段构建的数据结构（如归一化后的 `normalized` 列表）构造响应。*示例*：Service 层「设置场次专家」在 `commit` 后以 `normalized` 而非 `session_experts` 构建 `result["experts"]`。

  * **响应处理规范 (Response Handling)**:

      * **成功响应**: 所有成功返回**必须**调用 `success_response(data=...)` 函数。
      * **错误响应**: 所有业务错误必须返回 `fastapi.responses.JSONResponse`，其 `content` 由 `error_response(...)` 构建。

  * **配置规范 (Configuration)**:

      * **环境变量驱动配置**: 所有外部服务（如 Redis、数据库）的连接信息**必须**通过环境变量读取，**严禁**硬编码。

-----

##### 5.2 全项目通用安全与一致性规范（最高优先级）

 * **内部 ID 不得对外暴露**:

      * 所有对外 API 的 Response Schema 中，**禁止**直接暴露数据库内部主键（如 `id`, `user_id`）。
      * 对外唯一标识统一使用 `public_id` 或业务编号。

 * **严格区分 API Schema 与 内部 CRUD Schema**:

    1. **API 输入/输出 Schema** (对外边界，安全优先):
          * **不得包含**任何内部控制字段或敏感字段（如 `role`, `is_admin`, `password_hash`, `user_id` 等）。
          * 列表/筛选类接口的 Query 参数（如 `is_featured`、`is_active`）须在 Schema 或设计文档中明确，并注明何时必传，以便调用方按业务语义传参。
    2. **内部 CRUD Schema** (仅服务内部使用):
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

 * **环境变量配置安全规范**（适用于所有模块）:

      * **CORS 配置规范**:
          - **禁止**在代码中硬编码 CORS 配置（如 `allow_origins=["*"]`）
          - **必须**从环境变量读取 CORS 配置
          - **配置格式**: 支持逗号分隔的多个域名（如 `http://localhost:5175,https://example.com`）
          - **实现示例**:
            ```python
            # config.py
            CORS_ORIGINS_STR: str = os.getenv("CORS_ORIGINS", "*")
            BACKEND_CORS_ORIGINS: List[str] = [
                origin.strip() 
                for origin in CORS_ORIGINS_STR.split(",") 
                if origin.strip()
            ]
            
            # main.py
            app.add_middleware(
                CORSMiddleware,
                allow_origins=settings.BACKEND_CORS_ORIGINS,  # 从配置读取
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
            ```
          - **生产环境要求**: CORS 配置**必须**为具体域名，**严禁**使用 `["*"]`

      * **敏感信息配置规范**:
          - **禁止**在代码中硬编码以下敏感信息:
            - 数据库密码、用户名
            - JWT 密钥（`JWT_SECRET_KEY`）
            - 第三方服务密钥（如 Redis、Celery broker）
          - **必须**通过环境变量读取所有敏感配置
          - **禁止**为敏感信息设置不安全的默认值:
            - ❌ 错误: `POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "324zq999")`
            - ❌ 错误: `JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "my-key")`
            - ✅ 正确: `POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")`
          - **必需环境变量清单**（生产环境必须设置）：
            - `POSTGRES_PASSWORD`：数据库密码（生产环境必须设置）
            - `JWT_SECRET_KEY`：JWT密钥（生产环境必须设置，至少32字符）
            - `CORS_ORIGINS`：CORS允许的域名（生产环境必须设置具体域名，不能为 `*`）
            - 其他模块特定环境变量（根据实际需求）

      * **配置验证规范**:
          - **必须**在应用启动时验证必需的敏感配置
          - **缺失配置**必须抛出明确的异常，而非使用不安全的默认值
          - **实现示例**:
            ```python
            class Settings(BaseSettings):
                # 数据库配置
                POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "")
                
                # JWT 配置
                JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
                
                def __init__(self, **kwargs):
                    super().__init__(**kwargs)
                    self._validate_required_configs()
                
                def _validate_required_configs(self):
                    """验证必需的敏感配置"""
                    if not self.POSTGRES_PASSWORD:
                        raise ValueError(
                            "POSTGRES_PASSWORD 环境变量未设置。"
                            "生产环境必须设置此变量，不允许使用默认值。"
                        )
                    if not self.JWT_SECRET_KEY:
                        raise ValueError(
                            "JWT_SECRET_KEY 环境变量未设置。"
                            "生产环境必须设置此变量，且长度应至少32个字符。"
                        )
                    if len(self.JWT_SECRET_KEY) < 32:
                        raise ValueError(
                            "JWT_SECRET_KEY 长度不足32个字符，存在安全风险。"
                            "请使用更长的密钥（推荐64字符以上）。"
                        )
            ```

 * **日志安全规范**（适用于所有模块）:

      * **禁止在日志中打印敏感信息**:
          - ❌ **禁止**: 打印完整的数据库连接 URL（包含密码）
            ```python
            # 错误示例
            logger.info(f"尝试连接数据库: {DATABASE_URL}")
            ```
          - ✅ **必须**: 只打印非敏感的连接信息
            ```python
            # 正确示例
            logger.info(
                f"尝试连接数据库: "
                f"server={settings.POSTGRES_SERVER}, "
                f"port={settings.POSTGRES_PORT}, "
                f"database={settings.POSTGRES_DB}, "
                f"user={settings.POSTGRES_USER}"
                # 不打印密码
            )
            ```

      * **日志脱敏规范**（推荐实现）:
          - 创建日志脱敏工具函数 `app/core/logging_utils.py`
          - **实现示例**:
            ```python
            import re
            import logging
            
            def sanitize_log_message(message: str) -> str:
                """对日志消息进行脱敏处理"""
                # 移除数据库连接 URL 中的密码
                message = re.sub(
                    r'postgresql[+a-z]*://[^:]+:([^@]+)@',
                    r'postgresql://***:***@',
                    message,
                    flags=re.IGNORECASE
                )
                
                # 移除 JWT 密钥（如果意外出现在日志中）
                message = re.sub(
                    r'JWT_SECRET_KEY["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
                    r'JWT_SECRET_KEY="***"',
                    message,
                    flags=re.IGNORECASE
                )
                
                return message
            
            class SanitizedFormatter(logging.Formatter):
                """脱敏日志格式化器"""
                def format(self, record):
                    record.msg = sanitize_log_message(str(record.msg))
                    return super().format(record)
            ```

      * **日志脱敏实现载体要求**：
          - **日志脱敏工具函数**：
            - 提供统一的脱敏工具函数（如 `sanitize_log(data)`），用于对日志内容中的敏感字段进行处理
            - 业务代码禁止自行实现零散的脱敏逻辑，必须复用统一工具函数
          - **敏感信息识别规则**：
            - 基于字段名与内容模式进行识别，包括但不限于：
              - `password`、`secret`、`token`、`authorization`、`api_key`
            - 对匹配到的敏感信息进行掩码或移除处理，而非原样输出
          - **统一接入位置**：
            - 日志脱敏逻辑应在日志格式化器（logging formatter）或中间件层统一接入
            - 禁止在各业务模块中分散处理，以避免遗漏和实现不一致

      * **错误消息脱敏**:
          - **禁止**在异常处理中暴露敏感信息
          - **必须**只返回通用的错误消息给客户端
          - **实现示例**:
            ```python
            try:
                # 数据库操作
                pass
            except Exception as e:
                logger.error(f"数据库操作失败: {type(e).__name__}")
                # 不要打印完整的异常信息（可能包含连接字符串）
                raise HTTPException(status_code=500, detail="内部服务器错误")
            ```

 * **环境变量文件管理规范**（适用于所有模块）:

      * **`.env.example` 模板文件**:
          - **必须**提供 `.env.example` 模板文件
          - **必须**包含所有必需的环境变量（包括说明和示例）
          - **模板文件结构示例**:
            ```bash
            # ============================================
            # LiveCore Service 环境变量配置模板
            # ============================================
            # 
            # 使用说明:
            # 1. 复制此文件为 .env: cp .env.example .env
            # 2. 根据实际环境填写配置值
            # 3. 生产环境必须设置所有必需变量
            # 4. 不要将 .env 文件提交到版本控制系统
            #
            # ============================================
            
            # ========== 数据库配置 ==========
            POSTGRES_SERVER=localhost
            POSTGRES_PORT=5432
            POSTGRES_DB=live_core_test
            POSTGRES_USER=postgres
            # ⚠️ 生产环境必须设置强密码
            POSTGRES_PASSWORD=your_secure_password_here
            
            # ========== CORS配置 ==========
            # 开发环境示例: CORS_ORIGINS=http://localhost:5175,http://localhost:3000
            # 生产环境示例: CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
            CORS_ORIGINS=*
            
            # ========== JWT配置 ==========
            # ⚠️ 生产环境必须设置强密钥（推荐64字符以上）
            # 生成方式: openssl rand -hex 32
            JWT_SECRET_KEY=your_jwt_secret_key_here_min_32_chars
            JWT_ALGORITHM=HS256
            
            # ========== Celery配置 ==========
            CELERY_BROKER_URL=redis://redis:6379/0
            CELERY_RESULT_BACKEND=redis://redis:6379/0
            ```

      * **`.gitignore` 规范**:
          - **必须**在 `.gitignore` 中忽略所有环境变量文件
          - **必须**保留 `.env.example` 模板文件
          - **配置示例**:
            ```gitignore
            # 环境变量文件（包含敏感信息）
            .env
            .env.local
            .env.production
            .env.staging
            .env.*.local
            
            # 但保留模板文件
            !.env.example
            ```

 * **生产环境安全规范**（适用于所有模块）:

      * **密钥管理服务**（推荐）:
          - 生产环境**强烈建议**使用密钥管理服务，而非环境变量
          - **支持的密钥管理服务**:
            - AWS: AWS Secrets Manager / Parameter Store
            - Azure: Azure Key Vault
            - GCP: Secret Manager
            - HashiCorp: Vault
          - **AWS Secrets Manager 集成示例**:
            ```python
            # app/core/secrets_manager.py (可选)
            import boto3
            import json
            
            def get_secret(secret_name: str) -> dict:
                """从 AWS Secrets Manager 获取密钥"""
                client = boto3.client('secretsmanager')
                response = client.get_secret_value(SecretId=secret_name)
                return json.loads(response['SecretString'])
            
            # 在 config.py 中使用
            # secrets = get_secret("livecore/production")
            # POSTGRES_PASSWORD = secrets.get("POSTGRES_PASSWORD")
            ```

      * **环境变量注入**（Docker/K8s）:
          - 使用环境变量注入或密钥管理服务，而非在镜像中包含 `.env` 文件
          - **Docker Compose 示例**:
            ```yaml
            services:
              live_core_service:
                environment:
                  - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}  # 从宿主机环境变量读取
                  - JWT_SECRET_KEY=${JWT_SECRET_KEY}
                  - CORS_ORIGINS=${CORS_ORIGINS}
            ```

      * **文件权限控制**（Linux/Unix）:
          - **必须**设置环境变量文件的权限，防止未授权访问
          - **命令示例**:
            ```bash
            # 设置文件权限（仅所有者可读写）
            chmod 600 .env
            
            # 设置目录权限（防止其他用户访问）
            chmod 700 .
            ```

 * **密钥生成最佳实践**（适用于所有模块）:

      * **JWT 密钥生成**:
          - **推荐长度**: 64 字符（128位加密强度）
          - **生成方式**:
            ```bash
            # 使用 openssl（推荐）
            openssl rand -hex 32
            
            # 使用 Python
            python -c "import secrets; print(secrets.token_hex(32))"
            ```

      * **数据库密码生成**:
          - **推荐长度**: 16-32 字符
          - **生成方式**:
            ```bash
            # 使用 openssl
            openssl rand -base64 16
            
            # 使用密码生成工具
            pwgen -s 16 1
            ```

      * **密钥命名规范**:
          - 使用大写字母和下划线：`POSTGRES_PASSWORD`, `JWT_SECRET_KEY`
          - 使用有意义的名称：`CORS_ORIGINS` 而非 `CORS`
          - 分组前缀：`POSTGRES_*`, `JWT_*`, `CELERY_*`

-----

##### 5.3 详细实现模式与工程规范 (学院派)

**你必须同时遵循以下来自项目模板的详细工程规范：**

#### A. CRUD 层实现规范

 * **事务处理**: (见 5.1) CRUD 层的"写"操作（create, update, remove, batch\_add）**必须**包含完整的 `try/except IntegrityError/finally` 块，并处理 `db.commit()` 和 `db.rollback()`。
 * **N+1 防治**: 对于需要加载关系的查询（如 `get_with_categories`），**必须**使用 `selectinload` 或 `joinedload` 预加载关系。
      * **[关键] joinedload 与 unique() 规范**（2024-01 新增）：
        * **场景 1**：使用 `joinedload` 加载**一对多关系**（如 `Expert.live_session_experts`）
          - **问题**：JOIN 会导致主表（Expert）的行被重复（如果一个 Expert 有多个 SessionExpert）
          - **解决方案**：**必须**在 `.scalars()` 后调用 `.unique()` 去重
          - **示例**：
            ```python
            stmt = select(Expert).options(
                joinedload(Expert.live_session_experts).joinedload(LiveSessionExpert.session)
            ).where(Expert.is_featured == True)
            result = await db.execute(stmt)
            experts = result.scalars().unique().all()  # ← 必须使用 .unique()
            ```
        * **场景 2**：使用 `joinedload` 加载**多对一关系**（如 `UserExpertSubscription.expert`）
          - **不会导致重复**，**不需要** `.unique()`
        * **场景 3**：使用 `selectinload` 预加载关系
          - 使用单独的查询加载，**不会导致重复**，**不需要** `.unique()`
        * **关键区别表**：
          | 加载策略 | 关系类型 | 是否导致重复 | 是否需要 .unique() |
          |-----------|---------|-------------|------------------|
          | `joinedload` | 一对多 | ✅ 导致重复 | ✅ 必须 |
          | `joinedload` | 多对一 | ❌ 不重复 | ❌ 不需要 |
          | `selectinload` | 任意 | ❌ 不重复 | ❌ 不需要 |
 * **分页模式**: 分页查询（如 `get_multi_and_total`）**必须**通过两次查询实现：
    1. `select(func.count()).where(...)` 获取总数。
    2. `select(...).where(...).offset(skip).limit(limit)` 获取数据列表。
 * **列表类接口必须分页**：凡设计文档中定义为「返回列表」的 GET 接口（如管理端列表、用户关注列表、某资源下的子资源列表），**必须**实现分页，不得全量返回。**API 层**：Query 参数 `page: int = Query(1, ge=1)`、`size: int = Query(10, ge=1, le=100)`；响应 `data` 中须包含 `items`、`total`、`page`、`size`。**Service 层**：接收 page、size，计算 skip=(page-1)*size，调用 CRUD 的「总数查询」与「分页列表查询」，组装返回。**CRUD 层**：提供返回 (list, total) 或分别提供 count 与 list；WHERE 条件在 count 与 list 中一致。
 * **列表搜索规范（与前端《列表筛选与搜索规范》对齐）**：当设计文档或前端要求管理端列表支持关键词/ID 搜索时，须遵守：
      * **API 层**：列表接口增加 Query 参数 `q: Optional[str]`、`search_type: Optional[str]`（如 `id` | `keyword` 或未传表示关键词）。当 `search_type == 'id'` 且 `q` 非空时，须校验 `q` 为合法 UUID，非法则返回 400。
      * **CRUD 层**：根据 `q` 与 `search_type` 构建同一套 WHERE 条件，用于**总数查询**与**列表查询**（不得仅对列表施加条件）。当 `search_type == 'id'` 且 `q` 为合法 UUID 时使用 `WHERE id = :id`；否则当 `q` 非空时对**设计文档该列表 API 说明中写明的「字符串搜索字段」**（如 name、title、slug）做模糊匹配（如 `ilike`）；`q` 为空则不施加关键词/ID 条件。**通用性**：字符串搜索字段须从设计文档读取，**禁止在代码或提示词中写死为 name**；字符串搜索字段即该列表的「可配置字符串搜索字段列表」，可为 name、title、displayName 等。若设计文档未写明，则从 Model 的字符串类型列中选取业务语义最合适的一列（如 name、title）并在生成的代码注释中注明。**若设计文档明确要求该列表支持搜索却未写明字符串搜索字段，应在实现前要求设计文档补充该配置**，避免与设计文档母版不一致。
      * **排序**：排序规则（如 `sort_order ASC, created_at DESC`）在设计文档或接口说明中明确，列表查询与分页一致应用。
 * **复杂查询**: 允许使用 `join` 并返回 `List[Dict]`，但业务逻辑（如计算 `heat` 值）**禁止**在 CRUD 层进行。
 * **🚨 SQL级权限过滤中的角色检查（最高优先级）**：
      * **必须**使用大写进行角色检查：`if role not in ['ADMIN', 'SUPERADMIN']:`
      * **禁止**使用小写：`if role not in ['admin', 'superadmin']:`  ❌
      * **原因**：API层已经调用`.upper()`转换role为大写，CRUD层必须使用大写进行比较
      
      **❌ 错误示例（禁止使用）**：
      ```python
      # CRUD层错误
      if role not in ['admin', 'superadmin']:  # ❌ 使用小写
          conditions.append(Category.is_active == True)
      ```
      
      **✅ 正确示例（必须使用）**：
      ```python
      # CRUD层正确
      if role not in ['ADMIN', 'SUPERADMIN']:  # ✅ 使用大写
          conditions.append(Category.is_active == True)
      ```
      
      **🚨 强制检查清单（每个CRUD函数必须验证）**：
      - [ ] 是否使用大写`['ADMIN', 'SUPERADMIN']`进行角色检查？
      - [ ] 是否避免了小写`['admin', 'superadmin']`？
      - [ ] 是否与API层传递的大写role保持一致？
      - [ ] **分页（仅列表类接口）**：若为列表类接口，CRUD 是否先 count 再 offset/limit 查询？总数与列表是否使用相同 WHERE 条件？
      - [ ] **分页响应（仅列表类接口）**：若为列表类接口，API 是否暴露 page、size？响应是否包含 total 与 items？Service 是否传递 skip/limit 并组装分页结构？
      - [ ] **列表搜索（仅列表且支持搜索时）**：若设计文档要求列表支持搜索，API 是否暴露 `q`、`search_type`？`search_type=id` 时是否对 `q` 做 UUID 校验？CRUD 是否按**设计文档写明的字符串搜索字段**做模糊（未写死为 name）？若设计未写明，是否在注释中注明所选字段？

#### D. 数据库初始化脚本更新规范（必须执行）

**🚨（关键）数据库表创建前提**

当你生成新的 SQLAlchemy 模型代码（如 `app/models/expert.py`）时，**必须同时**更新数据库初始化脚本，否则新表不会被创建。

**两种更新方式（选择其一或两者都更新）**：

##### 方式1：更新 `models/__init__.py`（推荐，适用于 `init_db.py`）

如果项目使用 `app/init_db.py` 并通过 `import app.models` 自动导入所有模型，**必须**在生成CRUD层代码时，同时更新 `app/models/__init__.py`：

```python
# 在 app/models/__init__.py 中添加导入语句
# 专家模块模型（新增）
from .expert import Expert, UserExpertSubscription
```

**操作指令**（最小幅度修改要求）：
|- **必须**识别新生成的所有模型类名称
|- **必须**先检查文件末尾是否已有相同的导入语句（避免重复添加）
|- **必须**在文件末尾追加新导入（保持空行和注释格式一致）
|- **必须**添加注释说明这是新增模块
|- **严禁**修改、删除或重新排序任何现有导入语句
|- **严禁**修改文件中的任何其他代码

##### 方式2：更新 `app/scripts/create_tables.py`（适用于显式导入方式）

如果项目使用 `app/scripts/create_tables.py` 并显式导入每个模型，**必须**在生成CRUD层代码时，同时更新该脚本：

```python
# 在 app/scripts/create_tables.py 的 init_db() 函数中添加导入
        # 导入专家模块模型（新增）
        from ..models.expert import Expert, UserExpertSubscription
```

**操作指令**（最小幅度修改要求）：
|- **必须**识别新生成的所有模型类名称
|- **必须**先检查 `init_db()` 函数中是否已有相同的导入语句（避免重复添加）
|- **必须**在现有模型导入区域之后追加新导入（保持相同的缩进级别）
|- **必须**在 `init_db()` 函数中，在导入Base之后添加新模型的导入语句
|- **必须**添加注释说明这是新增模块（例如：`# 导入专家模块模型（新增）`）
|- **严禁**修改、删除或重新排序任何现有导入语句
|- **严禁**修改函数中的任何其他代码或逻辑

##### 验证要求

在生成CRUD层代码生成提示词文档时，**必须**明确包含以下内容：

1. **模型类清单**：列出所有新生成的模型类名称
2. **更新指令**：明确指出需要更新哪个初始化脚本文件
3. **导入语句模板**：提供准确的导入语句代码片段

**示例（在CRUD层提示词文档中的交付物部分）**：

```markdown
#### 9. 数据库初始化脚本更新（必须执行）

在生成 `app/models/expert.py` 模型代码后，**必须同时**执行以下操作：

**⚠️ 关键要求：最小幅度修改**
|- **只添加新导入语句，不修改任何现有代码**
|- **在现有导入语句之后追加新导入**
|- **如果导入已存在，跳过此步骤**

**需要更新的模型类**：
|- `Expert`
|- `UserExpertSubscription`

**更新 `app/models/__init__.py`**（如果使用 `init_db.py`）：

**操作步骤**：
1. 检查文件末尾是否已有 `from .expert import ...` 导入
2. 如果不存在，在文件末尾追加（保持空行和注释格式）：
```python
# 专家模块模型（新增）
from .expert import Expert, UserExpertSubscription
```
3. **不要修改**文件中的任何现有导入语句

**或更新 `app/scripts/create_tables.py`**（如果使用显式导入方式）：

**操作步骤**：
1. 在 `init_db()` 函数中找到现有的模型导入区域（通常在 `from ..models.live_core import ...` 之后）
2. 检查是否已有 `from ..models.expert import ...` 导入
3. 如果不存在，在现有导入语句之后追加：
```python
        # 导入专家模块模型（新增）
        from ..models.expert import Expert, UserExpertSubscription
```
4. **保持相同的缩进级别**（与现有导入一致）
5. **不要修改**函数中的任何现有的导入语句或代码

**验证方法**：
运行数据库初始化脚本后，检查日志输出，确认新表出现在创建列表中。
```

#### B. Service 层实现规范

 * **业务编排**: Service 层负责编排一个或多个 CRUD 调用，并组合业务逻辑（例如，`get_topic_detail` 调用 `crud.get_with_categories` 和 `crud.get_rooms_by_category`，并执行 `heat` 值的计算）。
 * **批量验证**: Service 层负责对输入列表（如 `room_ids`）进行业务验证（例如检查列表长度 `len(room_ids) > 100`）。
 * **[关键] 权限模式（字符串比较）**:
      * **必须**遵循 `5.0` 规范。Service 层的**所有**需要权限检查的方法，**必须**接收 `user_id: UUID` 和 `user_role: str` 作为参数。
      * **必须**在函数内部执行业务逻辑检查（例如 `if topic.user_id != user_id_from_db:` 或 `if user_role not in ['ADMIN', 'SUPERADMIN']:`）。
      * 如果检查失败，**必须** `raise PermissionDeniedException("权限不足...")`。
      * **🚨 角色值大小写检查清单**：
        - [ ] API层是否调用了 `.upper()` 转换role为大写？
        - [ ] Service层是否使用大写 `['ADMIN', 'SUPERADMIN']` 或 `['REGULAR', 'ADMIN', 'SUPERADMIN']`？
        - [ ] 是否与设计文档中的角色值（REGULAR/ADMIN/SUPERADMIN）完全一致？
        - [ ] 是否避免了小写（如 `'admin'`, `'superadmin'`）和混合大小写（如 `'Admin'`, `'SuperAdmin'`）？

 * **🚨 Service层角色检查强制要求（最高优先级）**：
      * **必须**使用大写进行角色比较：`if role not in ['ADMIN', 'SUPERADMIN']:`
      * **禁止**使用小写：`if role not in ['admin', 'superadmin']:`  ❌
      * **禁止**使用混合大小写：`if role not in ['Admin', 'SuperAdmin']:`  ❌
      * **禁止**使用错误值：`if role not in ['user', 'admin', 'superadmin']:`  ❌（应使用REGULAR而非user）
      * **原因**：API层已经调用`.upper()`转换role为大写，Service层必须使用大写进行比较
      
      **❌ 错误示例（禁止使用）**：
      ```python
      # Service层错误
      if role not in ['admin', 'superadmin']:  # ❌ 使用小写
      if role not in ['user', 'admin', 'superadmin']:  # ❌ 使用小写且值错误（应使用REGULAR）
      ```
      
      **✅ 正确示例（必须使用）**：
      ```python
      # Service层正确
      if role not in ['ADMIN', 'SUPERADMIN']:  # ✅ 使用大写
      if role not in ['REGULAR', 'ADMIN', 'SUPERADMIN']:  # ✅ 使用大写（如果需要检查REGULAR）
      ```
      
      **🚨 强制检查清单（每个Service方法必须验证）**：
      - [ ] 是否使用大写`['ADMIN', 'SUPERADMIN']`或`['REGULAR', 'ADMIN', 'SUPERADMIN']`？
      - [ ] 是否避免了小写和混合大小写？
      - [ ] 是否与设计文档中的角色值（REGULAR/ADMIN/SUPERADMIN）完全一致？
      - [ ] 若方法返回含 ORM 转 Pydantic 的响应：是否在 `await db.commit()` 之前完成序列化再 commit、再 return？（避免 MissingGreenlet/500）

##### C.0 RESTful API设计原则（必须遵守）

**如果设计文档中的API路径设计与本节规范冲突，本节规范（RESTful原则）永远是最高优先级。**

 * **资源导向 (Resource-Oriented)**:
      * **规则**：URL必须是**资源（名词）**，而不是**动作（动词）**。
      * **指令**：
        - ✅ 正确：`GET /api/v1/users/me/followed-experts`（资源是`followed-experts`）
        - ❌ 错误：`GET /api/v1/users/me/follow-expert`（`follow-expert`是动作，不是标准的名词资源）
        - ❌ 错误：`GET /api/v1/experts/followed`（`followed`是形容词，不是标准的名词资源）

 * **层次结构 (Hierarchical Structure)**:
      * **规则**：URL应该有清晰的**父子关系**，反映资源的层次关系。
      * **指令**：
        - ✅ 正确：`GET /api/v1/experts/{expert_id}/sessions`（专家→场次，清晰的父子关系）
        - ✅ 正确：`GET /api/v1/users/me/followed-experts`（用户→当前用户→关注专家，清晰的层次）

 * **HTTP方法表示操作 (HTTP Methods Represent Actions)**:
      * **规则**：HTTP方法应该表示对资源的操作。
      * **指令**：
        - `GET`: 获取资源（如`GET /api/v1/experts`）
        - `POST`: 创建资源（如`POST /api/v1/experts`）
        - `PATCH`: 部分更新资源（如`PATCH /api/v1/experts/{expert_id}`）
        - `PUT`: 完整替换资源（如`PUT /api/v1/experts/{expert_id}`）
        - `DELETE`: 删除资源（如`DELETE /api/v1/experts/{expert_id}`）

 * **统一接口 (Uniform Interface)**:
      * **规则**：所有资源应该遵循**相同的命名和结构规则。
      * **指令**：
        - **用户相关的操作**：统一在 `/api/v1/users/me/` 命名空间下
          - ✅ 正确：`GET /api/v1/users/me/followed-experts`
          - ✅ 正确：`POST /api/v1/users/me/followed-experts`
          - ✅ 正确：`DELETE /api/v1/users/me/followed-experts/{expert_id}`
        - **管理员相关的操作**：统一在 `/api/v1/admin/` 命名空间下
          - ✅ 正确：`GET /api/v1/admin/experts`
          - ✅ 正确：`POST /api/v1/admin/experts`
          - ✅ 正确：`DELETE /api/v1/admin/experts/{expert_id}`
        - **资源相关的操作**：统一在 `/api/v1/{resource}/` 命名空间下
          - ✅ 正确：`GET /api/v1/experts/{expert_id}`
          - ✅ 正确：`PATCH /api/v1/experts/{expert_id}`
          - ✅ 正确：`GET /api/v1/experts/{expert_id}/sessions`

 * **语义化 (Semantic Clarity)**:
      * **规则**：URL路径应该**清楚表示操作意图**和**资源上下文**。
      * **指令**：
        - ✅ 正确：`GET /api/v1/users/me/followed-experts`（清楚表示"当前用户的关注专家列表"）
        - ⚠️ 可接受：`GET /api/v1/experts/followed`（简洁但语义不够明确）
        - ❌ 错误：`GET /api/v1/get-followed-experts`（包含动词，违反资源导向原则）

 * **⚠️ 设计文档优先级说明**：
      * **规则**：如果设计文档中的API路径设计与RESTful规范冲突，且设计文档的设计更符合业务场景，则遵循设计文档。
      * **指令**：
        - 设计文档路径更符合RESTful规范（如 `GET /api/v1/users/me/followed-experts`）：优先遵循设计文档
        - 设计文档路径不够RESTful规范（如 `GET /api/v1/get-followed-experts`）：遵循本节RESTful规范
        - 设计文档路径与提示词文档路径冲突：优先选择更符合RESTful规范的路径
        - **关键**：确保API路径的**一致性和可维护性**，避免前后端开发时的混乱

#### C. API (FastAPI) 层实现规范

 * **[关键] 权限模式（字符串比较）**:

      * **必须**遵循 `5.0` 规范。API 端点**必须**依赖 `Depends(get_current_user)` 来获取 `Dict` (JWT Payload)。
      * **必须**在 `try` 块**之前**安全地解析出 `user_id: UUID` 和 `user_role: str`（见 `5.0` 示例代码）。
      * **严禁**使用 `Depends(get_current_admin_user)` 这类会直接抛出 `HTTPException` 的依赖。
      * **必须**在 `try/except` 块中捕获 Service 层抛出的 `PermissionDeniedException`，并返回 `JSONResponse(status_code=403, content=error_response(code=3002, ...))`。

 * **🚨 API端点实现强制模板（最高优先级）**：

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
              service = TagService(db)
              result = await service.create_tag(tag_data, current_user_id, role)
              return success_response(data=result)
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
      ```

      **✅ 正确示例（必须使用）**：
      ```python
      # ✅ 正确：完整的端点实现
      from fastapi.responses import JSONResponse
      from app.core.response import success_response, error_response
      import logging

      logger = logging.getLogger(__name__)

      async def create_tag(...):
          # 🚨 必须在try之前提取user_id和role
          current_user_id = UUID(current_user["user_id"])
          role = current_user.get("role", "REGULAR").upper()  # ✅
          user_id_for_logging = str(current_user_id)[:8]
          
          try:
              service = TagService(db)
              result = await service.create_tag(tag_data, current_user_id, role)
              return success_response(data=result)
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
      - [ ] 是否添加了try-except异常处理？
      - [ ] 是否捕获了`PermissionDeniedException`并使用`JSONResponse`+`error_response()`返回403？
      - [ ] 是否捕获了`NotFoundException`并使用`JSONResponse`+`error_response()`返回404？
      - [ ] 是否捕获了`InvalidParameterException`并使用`JSONResponse`+`error_response()`返回400？
      - [ ] 是否捕获了通用`Exception`并使用`JSONResponse`+`error_response()`返回500？
      - [ ] 是否导入了`JSONResponse`和`error_response`？
      - [ ] 是否禁止使用`raise HTTPException`？

 * **🚨 API层导入规范（强制要求）**：
      * **必须**导入以下异常类、JSONResponse和响应函数：
      ```python
      from fastapi import APIRouter, Depends, Query, Path
      from fastapi.responses import JSONResponse
      from app.exceptions import (
          PermissionDeniedException,
          NotFoundException,
          InvalidParameterException
      )
      from app.core.response import success_response, error_response
      import logging

      logger = logging.getLogger(__name__)
      ```
      * **禁止**遗漏任何异常类的导入
      * **禁止**使用 `raise HTTPException`，**必须**使用 `JSONResponse` + `error_response()`
      * **原因**：所有端点都需要异常处理，必须导入这些异常类和响应函数

 * **[关键] 路由定义**:
    
    **⚠️ 重要：生成模块特定母版时必须完整包含本节所有内容（包括避免重复前缀、路由前缀层级示例、路由前缀命名规范），不得只提取简洁版本。**
    
    1. **APIRouter 定义**: 必须在 `endpoints/xxx.py` 文件中定义 `APIRouter(tags=["..."])`，**严禁**在此时指定 `prefix`。
    2. **Prefix 挂载**: `prefix` **必须**在顶层 `api/v1/api.py` 文件的 `api_router.include_router(...)` 中统一指定。
    3. **[关键] 避免重复前缀**：
          * **全局路由前缀**：`main.py` 中已经配置了全局前缀 `/api/v1`（通过 `settings.API_V1_STR`）
          * **子路由前缀**：子路由前缀**不应该**包含 `/api/v1`，只包含模块路径（如 `/content`, `/experts`）
          * **最终路径**：`{全局前缀}/{子路由前缀}/{端点路径}`（如 `/api/v1/content/tags`）
          * **避免**：子路由前缀包含 `/api/v1`（如 `/api/v1/content`），导致最终路径为 `/api/v1/api/v1/content/tags`
    4. **端点路径**:
          * 集合端点 (如 `POST /items`, `GET /items`) **必须**使用 `path=""`（或 `/`）。
          * 资源端点 (如 `GET /items/{id}`) **必须**使用 `path="/{item_id}"`。
          * 嵌套资源 (如 `GET /items/{id}/sub_items`) **必须**使用 `path="/{item_id}/sub_items"`。

      * **[关键] 路由前缀层级示例**：
          ```
          # 层级 1：main.py（全局前缀）
          app.include_router(api_router, prefix="/api/v1")

          # 层级 2：api.py（子路由前缀）
          api_router.include_router(
              content_management.router,
              prefix="/content",  # ✅ 正确：只包含模块路径
          )
          # 最终路径：/api/v1/content/tags

          # ❌ 错误：子路由前缀包含 /api/v1
          api_router.include_router(
              content_management.router,
              prefix="/api/v1/content",  # ❌ 错误：重复 /api/v1
          )
          # 最终路径：/api/v1/api/v1/content/tags
          ```

      * **[关键] 路由前缀命名规范**：
          * 使用明确的模块路径（如 `/content`, `/experts`, `/rooms`, `/sessions`, `/categories`）
          * 避免使用模糊或重复的路径
          * 保持路由前缀与模块名称一致

 * **[关键] URL 拼接**:

      * 数据库**必须**只存储相对路径（例如 `/media/topics/.../banner.png`）。
      * 如果 API 响应需要返回完整 URL（如 `banner_url`），**必须**注入 `request: Request` 依赖，获取 `base_url = str(request.base_url).rstrip('/')`，并返回拼接后的**完整 URL**。

 * **响应格式化**:
      * 推荐使用 `format_..._response(orm_obj)` 辅助函数来标准化 ORM 对象到字典的转换，**然后再**进行 URL 拼接。

-----

#### 6. 交付物 (Deliverable)

请根据以上所有规则（5.0, 5.1, 5.2, 5.3），为"内容来源"文档（文件 2）文档中的功能（比如：Tab 和 Message）生成两个新的、完全符合"学院派"风格的提示词文档：

1.  `CRUD 层函数代码生成提示词文档`
2.  `Service 层和 API 层函数代码生成提示词文档`

**生成要求**:
|- **必须包含项目结构与上下文信息**：从"2. 核心上下文"部分提取项目结构信息，包含在生成的提示词文档中
|- **必须明确模型定义来源**：在生成的CRUD层代码生成提示词文档中，明确标注模型定义是从设计文档提取的，还是引用已生成的代码
|- **优先使用已有代码**：**必须首先检查** `app/models/{module_name}.py` 和 `app/schemas/{module_name}.py` 是否存在，如果存在，优先引用已有代码，而不是从设计文档提取
|- **必须包含文件路径信息**：明确说明生成的代码文件应该放在哪里（如 `app/crud/{module_name}.py`）
|- **必须包含导入路径规范**：明确说明如何导入依赖的模块（如 `from app.models.{module_name} import {ModelName}`）
|- **必须包含现有代码参考**：列出类似模块的现有代码文件路径，作为代码风格和结构参考
|- **必须读取项目目录结构**：在生成提示词文档时，**必须**读取实际的项目目录结构，确认文件路径和命名规范

**🚨 [强制要求] 全项目通用安全与一致性规范完整传递（最高优先级）**：

生成模块特定提示词文档时，**必须**完整传递母版的"5.2 全项目通用安全与一致性规范"章节，不得省略或简化：

1. **安全异步异常处理规范**：
   - **必须**在模块特定提示词文档中明确说明：在进入 `try` 块之前提取 ORM 对象属性
   - **必须**在示例代码中展示正确的变量提取方式（如 `user_id_for_logging = str(user_id)[:8]`）

2. **内部 ID 不得对外暴露规范**：
   - **必须**在模块特定提示词文档中明确说明：禁止在 API Schema 中暴露内部主键
   - **必须**明确要求使用 `public_id` 或业务编号

3. **API Schema 与内部 CRUD Schema 严格区分规范**：
   - **必须**在模块特定提示词文档中明确说明：API Schema 不得包含敏感字段
   - **必须**明确要求定义内部 CRUD Schema（如 `XXXCreateInternal`）

4. **Enum 字段声明规范**：
   - **必须**在模块特定提示词文档中明确说明：使用 `native_enum=False`
   - **必须**在示例代码中展示正确的 Enum 定义方式

5. **环境变量驱动配置规范**：
   - **必须**在模块特定提示词文档中明确说明：禁止硬编码敏感信息
   - **必须**明确要求通过环境变量读取配置

6. **RESTful API 设计原则**：
   - **必须**在模块特定提示词文档中包含完整的 RESTful 规范（资源导向、层次结构、HTTP 方法等）
   - **必须**明确要求遵循 RESTful 设计原则

**🚨 [强制要求] 异常处理规范完整传递（最高优先级）**：

生成模块特定提示词文档时，**必须**完整传递母版的异常处理规范，不得省略或简化：

1. **CRUD层提示词文档必须包含**：
   - **必须**明确要求所有写操作（create, update, remove, batch_add）**必须**包含完整的 `try/except IntegrityError/finally` 块（见母版第1222行）
   - **必须**明确要求 UPDATE + INSERT 操作（如 `record_watch_history`）**必须**有异常处理，因为可能遇到外键约束、数据库连接错误等
   - **必须**明确要求捕获 `IntegrityError` 时，构造 `DatabaseIntegrityException`，并执行 `await db.rollback()`
   - **必须**明确要求捕获通用 `Exception` 时，执行 `await db.rollback()` 并记录错误日志
   - **必须**在"日志与错误处理规范"章节中明确说明这些要求

2. **Service层和API层提示词文档必须包含**：
   - **必须**明确要求所有API端点**必须**遵循母版的API端点实现强制模板（见母版第1477-1540行）
   - **必须**明确要求所有API端点**必须**包含完整的 try-except 异常处理
   - **必须**明确要求示例代码**必须**包含完整的异常处理（不得省略）
   - **必须**明确要求所有端点**必须**捕获 `PermissionDeniedException`, `NotFoundException`, `InvalidParameterException` 等自定义异常
   - **必须**明确要求所有端点**必须**将异常转换为 `JSONResponse`，使用 `error_response()` 构建错误响应
   - **必须**在示例代码中展示完整的异常处理模式（包括 try-except 块、异常捕获和转换）

3. **示例代码完整性要求**：
   - **禁止**在示例代码中省略异常处理
   - **必须**在示例代码中包含完整的 try-except 块
   - **必须**在示例代码中展示如何捕获和转换异常
   - **必须**在示例代码中展示如何提取 `user_id` 和 `role`（在 try 块之前）

4. **引用母版规范要求**：
   - **必须**在生成的模块特定提示词文档中明确引用母版的异常处理规范章节
   - **必须**在生成的模块特定提示词文档中包含母版异常处理规范的摘要或说明
   - **禁止**在生成的模块特定提示词文档中省略或简化异常处理规范

**🚨 [强制要求] CRUD层实现规范完整传递（最高优先级）**：

生成模块特定CRUD层提示词文档时，**必须**完整传递母版的"5.3 A. CRUD层实现规范"章节，不得省略或简化：

1. **N+1防治规范**：
   - **必须**在模块特定提示词文档中明确说明：对于需要加载关系的查询，**必须**使用`selectinload`或`joinedload`预加载关系
   - **必须**明确说明`joinedload`与`unique()`的使用规范（一对多关系必须使用`.unique()`，多对一关系不需要）
   - **必须**在示例代码中展示正确的`joinedload`和`selectinload`使用方式

2. **分页模式规范**：
   - **必须**在模块特定提示词文档中明确说明：分页查询**必须**通过两次查询实现（总数查询 + 数据列表查询）
   - **必须**在示例代码中展示正确的分页实现方式

3. **列表搜索规范（若模块需支持管理端列表筛选）**：
   - 当设计文档或前端要求列表搜索时，**必须**在模块特定提示词中约定：API 层增加 `q`、`search_type` 等 Query 参数；CRUD 层实现「按 ID 精确」与「按关键词模糊」两种条件分支；总数与列表使用相同 WHERE 条件；并与前端《列表筛选与搜索规范》对齐。字符串搜索字段以设计文档写明的「可配置字符串搜索字段列表」为准（可为 name、title、displayName 等），不限定为 name。

4. **SQL级权限过滤规范**：
   - **必须**在模块特定提示词文档中明确说明：**必须**使用大写进行角色检查（`['ADMIN', 'SUPERADMIN']`）
   - **必须**明确禁止使用小写或混合大小写
   - **必须**在示例代码中展示正确的权限过滤实现方式

5. **数据库初始化脚本更新规范**：
   - **必须**在模块特定提示词文档中明确说明：生成模型代码后，**必须同时**更新数据库初始化脚本
   - **必须**明确说明需要更新的文件（`app/models/__init__.py`或`app/scripts/create_tables.py`）
   - **必须**提供准确的导入语句模板和操作步骤

6. **事务处理规范**：
   - **必须**在模块特定提示词文档中明确说明：所有写操作**必须**包含完整的`try/except IntegrityError`块
   - **必须**明确说明UPDATE + INSERT操作**必须**有异常处理
   - **必须**在示例代码中展示正确的异常处理方式

**🚨 [强制要求] Service层实现规范完整传递（最高优先级）**：

生成模块特定Service层提示词文档时，**必须**完整传递母版的"5.3 B. Service层实现规范"章节，不得省略或简化：

1. **业务编排规范**：
   - **必须**在模块特定提示词文档中明确说明：Service层负责编排一个或多个CRUD调用，并组合业务逻辑
   - **必须**在示例代码中展示正确的业务编排方式

2. **批量验证规范**：
   - **必须**在模块特定提示词文档中明确说明：Service层负责对输入列表进行业务验证
   - **必须**在示例代码中展示正确的批量验证方式

3. **权限模式规范**：
   - **必须**在模块特定提示词文档中明确说明：**必须**使用大写进行角色比较（`['ADMIN', 'SUPERADMIN']`或`['REGULAR', 'ADMIN', 'SUPERADMIN']`）
   - **必须**明确禁止使用小写、混合大小写或错误值（如`'user'`应使用`'REGULAR'`）
   - **必须**在示例代码中展示正确的权限检查方式

4. **角色检查强制要求**：
   - **必须**在模块特定提示词文档中明确说明：**必须**使用大写进行角色比较
   - **必须**明确禁止使用小写、混合大小写或错误值
   - **必须**在示例代码中展示正确的角色检查方式

**🚨 [强制要求] API层实现规范完整传递（最高优先级）**：

生成模块特定API层提示词文档时，**必须**完整传递母版的"5.3 C. API层实现规范"章节，不得省略或简化：

1. **API端点实现强制模板**：
   - **必须**在模块特定提示词文档中完整复制母版的API端点实现强制模板（见母版第1477-1540行）
   - **必须**明确要求所有API端点**必须**遵循此模板
   - **必须**在示例代码中展示完整的端点实现（包括try-except块、异常捕获和转换）

2. **API层导入规范**：
   - **必须**在模块特定提示词文档中明确说明：**必须**导入`JSONResponse`、`error_response`、`success_response`和所有异常类
   - **必须**明确禁止使用`raise HTTPException`
   - **必须**在示例代码中展示正确的导入语句

3. **路由定义规范**：
   - **必须**在模块特定提示词文档中完整包含母版的"路由定义"章节（包括避免重复前缀、路由前缀层级示例、路由前缀命名规范）
   - **必须**明确说明：APIRouter定义**严禁**指定`prefix`，`prefix`**必须**在顶层`api/v1/api.py`中统一指定
   - **必须**在示例代码中展示正确的路由定义方式

4. **URL拼接规范**：
   - **必须**在模块特定提示词文档中明确说明：数据库**必须**只存储相对路径，API响应需要返回完整URL时**必须**注入`request: Request`依赖
   - **必须**在示例代码中展示正确的URL拼接方式

5. **响应格式化规范**：
   - **必须**在模块特定提示词文档中明确说明：推荐使用`format_..._response(orm_obj)`辅助函数来标准化ORM对象到字典的转换
   - **必须**在示例代码中展示正确的响应格式化方式

**🚨 代码生成后必须验证的检查清单**：

**API层检查清单**：
- [ ] 所有端点是否在try块之前提取了`user_id`和`role`？
- [ ] 所有端点是否调用了`.upper()`转换role为大写？
- [ ] 所有端点是否添加了完整的异常处理（try-except）？
- [ ] 是否导入了必要的异常类（`PermissionDeniedException`, `NotFoundException`, `InvalidParameterException`）？
- [ ] 是否导入了`JSONResponse`和`error_response`？
- [ ] 是否禁止使用`raise HTTPException`，改为使用`JSONResponse`+`error_response()`？
- [ ] 所有异常是否都转换为`JSONResponse`，使用`error_response()`构建错误响应？
- [ ] 是否捕获了通用`Exception`并返回500错误？
- [ ] APIRouter定义是否**严禁**指定`prefix`？
- [ ] 是否在示例代码中展示了完整的端点实现？

**Service层检查清单**：
- [ ] 所有权限检查是否使用大写`['ADMIN', 'SUPERADMIN']`或`['REGULAR', 'ADMIN', 'SUPERADMIN']`？
- [ ] 是否避免了小写和混合大小写？
- [ ] 是否避免了错误值（如`'user'`应使用`'REGULAR'`）？
- [ ] 是否与设计文档中的角色值（REGULAR/ADMIN/SUPERADMIN）完全一致？
- [ ] 若返回数据含 ORM 转 Pydantic（如 `model_validate(orm_obj)`），是否在 `await db.commit()` **之前**完成序列化，再 commit、再 return？（避免 commit 后 ORM 过期触发懒加载导致 MissingGreenlet/500）
- [ ] 是否在示例代码中展示了正确的业务编排和批量验证方式？

**CRUD层检查清单**：
- [ ] SQL级权限过滤是否使用大写`['ADMIN', 'SUPERADMIN']`？
- [ ] 是否避免了小写`['admin', 'superadmin']`？
- [ ] 是否与API层传递的大写role保持一致？
- [ ] 是否在示例代码中展示了正确的N+1防治和分页模式？
- [ ] 若模块需支持列表搜索，是否约定了 q/search_type、ID 精确与模糊条件及与前端《列表筛选与搜索规范》对齐？
- [ ] 是否在提示词文档中明确说明了数据库初始化脚本更新要求？

**一致性检查**：
- [ ] API层、Service层、CRUD层的角色值是否全部使用大写？
- [ ] 是否与设计文档中的角色值（REGULAR/ADMIN/SUPERADMIN）完全一致？
- [ ] 模块特定提示词文档是否完整包含了母版的所有实现规范？