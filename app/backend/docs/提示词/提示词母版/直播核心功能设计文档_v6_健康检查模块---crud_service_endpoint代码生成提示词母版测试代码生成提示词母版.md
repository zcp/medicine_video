-----

### 【元提示词】测试代码生成 *指令文档* 母版 (v6.0 - 支持增量测试版)

**[使用说明：** 在 Cursor 聊天框中，首先 `@` 引用您想测试的核心文件（例如 `@app/api/endpoints/topics.py` 和 `@app/services/topic.py`），然后粘贴下面的所有内容并运行。]

**[测试模式说明]**: 本母版支持两种测试生成模式：
- **全新测试生成模式**：生成全新的测试代码，可以修改 `conftest.py`，测试环境是干净的。
- **增量测试生成模式**：在已有测试基础上增量生成，**不能修改**已通过的测试，**可以修改 `conftest.py` 但只能增加新内容**，必须使用增量判断方式验证数据库操作。

-----

#### 1\. 角色定义 (Role Definition - 规划师)

你是一名顶级的**测试架构师**兼**提示词工程师 (Prompt Engineer)**，你正在 **Cursor IDE** 中运行。

你的**唯一任务**是：

1.  **分析上下文**：用户已经在提示词的开头使用了 Cursor 的 `@` 标记引用了几个**核心目标文件**。
   - **⚠️ 关键判断规则**：
     - 如果用户引用了**已有测试文件**（如 `@tests/test_*.py`、`@tests/conftest.py`），则**明确判定**为**增量测试生成模式**。
     - 如果用户只引用了**核心目标文件**（如 `@app/api/endpoints/...`），需要进一步判断：
       - **检查项目是否已有测试文件**：**必须**检查项目中是否存在 `tests/conftest.py` 或任何 `tests/test_*.py` 文件。
       - **如果项目已存在测试文件**（如 `tests/conftest.py`），则**默认判定为增量测试生成模式**（因为这是新增模块的测试，应在已有测试基础上增量生成）。
       - **如果项目不存在测试文件**（全新项目），则判定为**全新测试生成模式**。
   - **⚠️ 重要**：除非用户**明确指定**"全新测试"、"clean test"或"全新测试生成模式"，否则当项目已存在测试文件时，**必须**使用增量测试生成模式。
2.  **自动发现依赖**：**读取**这些 `@` 文件的内容，分析它们的 `import` 语句，**自动**在用户的项目中找到并**读取**所有相关的**本地依赖项**（例如，`app.crud`、`app.models`、`app.schemas`、`app.core` 等）。
   - **增量模式（MANDATORY）**：
     - **必须主动读取** `tests/conftest.py`（即使未被明确引用），了解现有Fixture定义、代码风格和命名约定
     - **必须主动检测**项目中已存在的测试文件（`tests/test_*.py`），了解现有测试结构、命名约定和代码风格
     - 如果用户明确引用了测试文件，也需要读取并分析其内容
3.  **生成指令文档**：根据你读取到的**所有**文件内容（`@` 目标文件 + 自动发现的依赖文件 + `tests/conftest.py`和现有测试文件（如果是增量模式）），生成一个全新的、独立的 Markdown 提示词文档，命名为 `最终测试代码生成提示词.md`。
   - **必须**在生成的文档中明确标注测试模式（全新/增量）。

你的工作是**创建这份详细的指令文档**，而不是自己执行它（即**不要生成 .py 代码**）。

-----

#### 2\. 交付物结构 (Deliverable Structure)

你生成的 `最终测试代码生成提示词.md` 文件**必须**严格遵循以下结构。你必须**完整地复制** 1-5 节和 8 节的*静态内容*，并**动态生成** `Section 6` 和 `Section 7`。

> **[你生成的 `.md` 文件的内容应从这里开始]**
>
> ### 【最终完整版】高效 AI 测试代码生成提示词 (混合策略执行版)
>
> #### 1\. 角色定义与测试模式 (Role Definition & Test Mode - 执行者)
>
> 你是一名资深的 Python 测试架构师。你精通使用 `pytest`、`pytest-asyncio`、`httpx` 和 `pytest-mock`，并且是"混合测试策略"的专家。
>
> **⚠️ 测试模式说明**：
> - **测试模式**：**[根据规划师判断，明确标注为"增量测试生成模式"或"全新测试生成模式"]**
> - **说明**：**[如果是增量模式]**为XXX模块**新增**测试代码，在已有测试基础上增量生成。**严禁修改**已存在的测试文件。
> - **说明**：**[如果是全新模式]**生成全新的测试代码，测试环境是干净的。
>
> 你的任务是**读取**下面 `Section 6` 中提供的应用程序源代码（以及已存在的测试文件，如果是增量模式），并**严格按照** `Section 2-5` 的"核心规则"和 `Section 7` 的"具体任务列表"，为它们生成一个**完整、健壮、可运行的 `pytest` 测试文件**。
>
> **⚠️ 增量测试模式的特殊要求**：
> - **严禁修改**已存在的测试函数（即使是修复错误也不行，除非用户明确要求）。
> - **允许修改 `conftest.py`**（仅限添加新内容）：
>   - ✅ **只增加**新的Fixture、函数、变量、导入等。
>   - ❌ **严禁修改**已有的Fixture、函数、变量等。
>   - ❌ **严禁删除**任何现有内容。
>   - ✅ **必须检查冲突**：新增的内容必须与已有的内容没有冲突（函数名、变量名、Fixture名等不重复）。
> - **必须使用增量判断方式**验证数据库操作（记录测试前状态，只验证增量变化）。
>
> -----
>
> #### 2\. 核心测试哲学 (The Hybrid Testing Strategy - MANDATORY)
>
> 你**必须**根据被测试代码的层级，严格遵循以下混合测试策略。这是最高优先级指令。
>
> | 测试目标层级 | 强制测试风格 | 核心工具 | 测试目标 (你必须验证什么？) |
> | :--- | :--- | :--- | :--- |
> | **API / Endpoint 层** | **实用派 (Pragmatic)** | `httpx.AsyncClient` + `db_session` + `async_session_factory` | **验证完整链路**：... JSON 响应... 以及*真实*的数据库状态变化（**注意**：必须使用**新会话**查询以避免缓存陷阱）。 |
> | **Service (服务) 层** | **学院派 (Academic)** | `mocker` (Mock 掉 CRUD/I/O) | **验证业务逻辑**：*隔离地*测试权限检查、数据编排、以及自定义异常（`pytest.raises`）的抛出。 |
> | **CRUD (数据) 层** | **实用派 (Pragmatic)** | `db_session` (真实数据库) | **验证数据库状态**：*必须*通过 `db.refresh()` 或**再次查询**来“证明”数据已被正确创建、更新或删除。 |
>
> -----
>
> #### 3\. 核心实现规范 (Core Implementation Requirements - MANDATORY)
>
> 所有生成的测试代码**必须**无条件遵守以下规范。
>
> ##### 3.1. 测试环境配置 (`conftest.py`)
>
>   * 你必须假设 `conftest.py`（或 `app.db.session`）已经按如下方式配置好：
>     1.  `setup_database` (scope="session", autouse=True): 自动创建和删除表。
>     2.  `db_session` (scope="function"): 提供用于**测试准备 (Arrange)** 和 **CRUD 测试**的会话。
>     3.  `async_client` (scope="function"): 提供 `httpx.AsyncClient`。
>     4.  **`async_session_factory`**: (来自 `app.db.session` 或 `tests.conftest`) 提供了创建**全新独立会话**的能力，专用于在 API 测试的断言阶段验证数据库状态，以规避身份映射缓存。
>
>   * **⚠️ 增量测试模式特殊约束**：
>     - **允许修改 `conftest.py`**（仅限添加新内容）：可以添加新的Fixture、函数或变量，但**必须严格遵守以下规则**：
>       - ✅ **只增加新的内容**：只能添加新的Fixture、函数、变量、导入等。
>       - ❌ **严禁修改已有的内容**：不能修改、删除或重命名现有的Fixture、函数、变量等。
>       - ✅ **必须检查冲突**：新增的内容必须与已有的内容没有冲突（函数名、变量名、Fixture名等不重复）。
>       - ✅ **保持代码风格一致**：新增的内容必须遵循现有代码的格式、命名约定和代码风格。
>     - **必须复用现有Fixture**：优先使用 `conftest.py` 中已定义的Fixture，避免重复创建。
>     - **新增Fixture的位置**：
>       - **优先**：在 `conftest.py` 中添加新Fixture（如果没有命名冲突或功能重复）。
>       - **备选**：如果存在命名冲突或功能重复，在测试文件内部定义（使用 `@pytest.fixture`）。
>
> ##### 3.2. 结构化测试 (Arrange, Act, Assert)
>
>   * 所有测试用例**必须**遵循“准备 (Arrange)”、“执行 (Act)”、“断言 (Assert)”的逻辑结构，并使用注释将其清晰分开。
>
> ##### 3.3. 严格的异步测试语法 (MANDATORY `async for` Syntax)
>
>   * 所有使用异步 `pytest` Fixture (如 `db_session`, `async_client`) 的测试函数**必须**使用 `async for` 语法来解包。
>   * **⚠️ 禁止的写法**：
>       * 不得在 `async for` 外部调用数据库操作。
>       * 不得直接使用 fixture 参数而不解包。
>       * 不得在函数参数中添加类型提示（`db_session: AsyncSession`）。
>
> <!-- end list -->

> ```python
> # ✅ 正确的 CRUD 测试模板
> @pytest.mark.asyncio
> async def test_crud_operation(self, db_session):
>     """测试描述"""
>     async for db in db_session:
>         # ...所有数据库逻辑必须在此块内...
>         pass
> ```

> # ✅ 正确的 API + DB 组合测试模板
>
> @pytest.mark.asyncio
> async def test\_api\_with\_db(self, async\_client, db\_session):
> """API 和数据库组合测试"""
> async for client in async\_client:
> async for db in db\_session:
> \# ...所有组合测试逻辑必须在此嵌套块内...
> pass
>
> ````
> 
> ##### 3.4. 测试数据隔离 (MANDATORY for Pragmatic Tests)

>   * **指令**: 为了防止测试之间因违反数据库 `UNIQUE` 约束而产生冲突，所有唯一性字段（如 `username`, `email`, `product_code`）**必须**是随机生成的。
>   * **实现**: **必须**导入 `Faker` 和 `uuid` (以及 `random` 和 `string`，如果需要)。
>   * **具体要求 (Faker 范例)**:
>       * **`username`**: `f"{fake.user_name()}_{uuid.uuid4().hex[:6]}"`
>       * **`email`**: `fake.email()`
>       * **`product_code`**: `f"PROD_{''.join(random.choices(string.ascii_uppercase + string.digits, k=10))}"`
>   * **禁止硬编码**: **严禁**使用硬编码的字符串（如 `'usera'`）作为唯一性字段的值，除非测试目的就是为了验证重复性。
>
> ##### 3.6. [关键] 增量测试模式规范 (MANDATORY for Incremental Test Mode)
>
> **⚠️ 重要**：只有在**增量测试生成模式**下才需要遵循本节规范。全新测试生成模式可以忽略本节。
>
> ##### 3.6.1. 最小幅度修改原则 (MANDATORY)
>
> - ✅ **只增加**新的测试函数，不修改、不删除、不重命名已存在的测试函数。
> - ✅ **保持现有测试的命名约定**：新测试函数必须遵循现有测试的命名风格。
> - ✅ **复用现有Fixture**：优先使用 `conftest.py` 中已定义的Fixture。
> - ✅ **允许修改 `conftest.py`**（仅限添加新内容）：
>   - ✅ **只增加**新的Fixture、函数、变量、导入等。
>   - ❌ **严禁修改**已有的Fixture、函数、变量等。
>   - ❌ **严禁删除**任何现有内容。
>   - ✅ **必须检查冲突**：新增的内容必须与已有的内容没有冲突（函数名、变量名、Fixture名等不重复）。
>   - ✅ **保持代码风格一致**：新增的内容必须遵循现有代码的格式、命名约定和代码风格。
> - ❌ **禁止修改**已存在的测试函数（即使是修复错误也不行）。
> - ❌ **禁止删除**任何现有测试函数或代码。
>
> ##### 3.6.1.1. conftest.py 修改的冲突检查规范 (MANDATORY)
>
> **⚠️ 关键**：在增量测试模式下，如果要修改 `conftest.py`，**必须**进行冲突检查。
>
> **✅ 冲突检查步骤**：
>
> 1. **读取现有 `conftest.py`**：
>    - **必须**完整读取 `conftest.py` 的所有内容。
>    - **必须**识别所有已定义的Fixture、函数、变量、导入等。
>
> 2. **检查命名冲突**：
>    - **检查Fixture名称**：新增的Fixture名称不能与现有的Fixture名称重复。
>    - **检查函数名称**：新增的函数名称不能与现有的函数名称重复。
>    - **检查变量名称**：新增的变量名称不能与现有的变量名称重复（除非是模块级常量且用途相同）。
>    - **检查导入冲突**：新增的导入不能与现有的导入冲突（如导入相同的模块使用不同的别名）。
>
> 3. **检查功能重复**：
>    - **检查Fixture功能**：如果已有Fixture提供相同功能，优先复用现有Fixture，而不是创建新的。
>    - **检查辅助函数功能**：如果已有辅助函数提供相同功能，优先复用现有函数，而不是创建新的。
>
> 4. **验证代码风格一致性**：
>    - **命名约定**：新增内容的命名必须遵循现有代码的命名风格（如 `snake_case`、`camelCase` 等）。
>    - **代码格式**：新增内容的格式（缩进、空行、注释风格等）必须与现有代码一致。
>    - **导入顺序**：新增的导入必须按照现有代码的导入顺序添加（标准库、第三方库、本地模块）。
>
> **✅ 正确的添加方式**：
>
> ```python
> # conftest.py (现有内容)
> import pytest
> from sqlalchemy.ext.asyncio import AsyncSession
>
> @pytest.fixture
> async def db_session():
>     """数据库会话"""
>     ...
>
> @pytest.fixture
> def regular_user_id():
>     """普通用户ID"""
>     ...
>
> # [新增内容] - ✅ 正确：添加新的Fixture，没有命名冲突
> @pytest.fixture
> def admin_user_id():
>     """管理员用户ID"""
>     ...
>
> @pytest.fixture
> def regular_user_token(regular_user_id):
>     """普通用户Token"""
>     ...
> ```
>
> **❌ 错误的添加方式**：
>
> ```python
> # ❌ 错误：Fixture名称与现有Fixture重复
> @pytest.fixture
> def regular_user_id():  # 已存在，不能重复定义
>     ...
>
> # ❌ 错误：修改了现有Fixture的定义
> @pytest.fixture
> async def db_session():  # 已存在，不能修改
>     # 添加了新的参数 - 这是修改，不是增加
>     async def _session(param):  # ❌ 错误
>         ...
> ```
>
> **⚠️ 注意事项**：
> - **如果存在命名冲突**：在测试文件内部定义新Fixture，而不是添加到 `conftest.py`。
> - **如果存在功能重复**：优先复用现有Fixture或函数，而不是创建新的。
> - **如果无法判断**：在测试文件内部定义新Fixture，确保不影响其他测试。
>
> ##### 3.6.2. 增量数据库验证规范 (MANDATORY)
>
> **🚨 关键原则**：在增量测试模式下，数据库中可能已经包含数据，因此**必须使用增量判断方式**验证数据库操作，而不是基于数据库总数判断。
>
> **✅ 正确的增量验证模式**：
>
> ```python
> @pytest.mark.asyncio
> async def test_create_topic_success(db_session):
>     """测试创建专题（增量验证）"""
>     async for db in db_session:
>         # ===== Arrange (准备) =====
>         # [关键] 记录测试前的记录数量（基线）
>         from sqlalchemy import select, func
>         from app.models.topic import Topic
>         
>         # 查询测试前的记录总数
>         count_stmt = select(func.count(Topic.id))
>         result = await db.execute(count_stmt)
>         initial_count = result.scalar()
>         
>         # 准备测试数据
>         topic_data = TopicCreate(
>             title=f"测试专题_{uuid.uuid4().hex[:6]}",
>             description="测试描述"
>         )
>         
>         # ===== Act (执行) =====
>         topic = await crud_topic.create(db, obj_in=topic_data)
>         await db.commit()
>         await db.refresh(topic)
>         
>         # ===== Assert (断言) =====
>         # [关键] 验证增量：记录数应该增加1
>         final_count_stmt = select(func.count(Topic.id))
>         final_result = await db.execute(final_count_stmt)
>         final_count = final_result.scalar()
>         
>         assert final_count == initial_count + 1, f"记录数应该增加1，但实际增加了{final_count - initial_count}"
>         assert topic.title == topic_data.title
>         assert topic.id is not None
> ```
>
> **✅ 删除操作的增量验证模式**：
>
> ```python
> @pytest.mark.asyncio
> async def test_remove_topic_success(db_session, created_topic):
>     """测试删除专题（增量验证）"""
>     async for db in db_session:
>         # ===== Arrange (准备) =====
>         # [关键] 记录测试前的记录数量（基线）
>         from sqlalchemy import select, func
>         from app.models.topic import Topic
>         
>         count_stmt = select(func.count(Topic.id))
>         result = await db.execute(count_stmt)
>         initial_count = result.scalar()
>         
>         topic_id = created_topic.id
>         
>         # ===== Act (执行) =====
>         await crud_topic.remove(db, id=topic_id)
>         await db.commit()
>         
>         # ===== Assert (断言) =====
>         # [关键] 验证增量：记录数应该减少1
>         final_count_stmt = select(func.count(Topic.id))
>         final_result = await db.execute(final_count_stmt)
>         final_count = final_result.scalar()
>         
>         assert final_count == initial_count - 1, f"记录数应该减少1，但实际减少了{initial_count - final_count}"
>         
>         # 验证对象已被删除
>         deleted_topic = await crud_topic.get(db, id=topic_id)
>         assert deleted_topic is None
> ```
>
> **✅ 列表查询的增量验证模式**：
>
> ```python
> @pytest.mark.asyncio
> async def test_get_multi_topics_incremental(db_session):
>     """测试获取专题列表（增量验证）"""
>     async for db in db_session:
>         # ===== Arrange (准备) =====
>         # [关键] 记录测试前的记录数量和ID集合（基线）
>         from sqlalchemy import select
>         from app.models.topic import Topic
>         
>         initial_stmt = select(Topic.id)
>         initial_result = await db.execute(initial_stmt)
>         initial_ids = set(row[0] for row in initial_result.all())
>         initial_count = len(initial_ids)
>         
>         # 创建新的测试数据
>         new_topic = await crud_topic.create(db, obj_in=TopicCreate(
>             title=f"新专题_{uuid.uuid4().hex[:6]}",
>             description="测试"
>         ))
>         await db.commit()
>         
>         # ===== Act (执行) =====
>         topics, total = await crud_topic.get_multi(db, page=1, size=100)
>         
>         # ===== Assert (断言) =====
>         # [关键] 验证增量：新创建的记录应该出现在列表中
>         current_ids = set(topic.id for topic in topics)
>         
>         assert new_topic.id in current_ids, "新创建的专题应该出现在列表中"
>         assert total >= initial_count + 1, f"总数应该至少增加1，但实际为{total}，基线为{initial_count}"
> ```
>
> **❌ 错误的验证方式（禁止在增量模式下使用）**：
>
> ```python
> # ❌ 错误：基于固定总数判断
> topics, total = await crud_topic.get_multi(db, page=1, size=10)
> assert total == 5  # 禁止！数据库中可能已经有其他数据
>
> # ❌ 错误：基于固定数量判断
> assert len(topics) == 10  # 禁止！可能已经有其他测试数据
>
> # ✅ 正确：基于增量判断
> initial_count = await get_count_before_test(db)
> topics, total = await crud_topic.get_multi(db, page=1, size=10)
> assert total >= initial_count  # 只验证数量增加了（或保持不变）
> assert new_topic.id in [t.id for t in topics]  # 验证新创建的数据存在
> ```
>
> **⚠️ 注意事项**：
> - 增量验证适用于**所有涉及数据库计数或列表查询的测试**。
> - 对于**创建/更新/删除单个对象**的测试，除了验证增量外，还应验证对象的属性是否正确。
> - 对于**查询单个对象**的测试，不需要增量验证（直接验证对象属性即可）。

> ##### 3.5. [关键] 统一的用户身份解析规范 (MANDATORY - V5.1 修复)

> **🚨（新增）API 层用户提取规范（JWT→UUID+Enum）**
> **`current_user` 永远是一个 JWT payload `dict`，而不是 ORM `User` 模型**。

> API 层必须使用以下模式解析：

> ```python
> current_user: Dict = Depends(get_current_user)
> ````

> user\_id = uuid.UUID(current\_user.get("user\_id") or current\_user.get("sub"))
> role\_str = current\_user.get("role", "REGULAR").upper()
> user\_role = LiveRoomMessageUserRole.get(role\_str, LiveRoomMessageUserRole.REGULAR)
>
> ````
> 
> **🚨（新增）Service 层用户参数规范**
> Service 层方法**不得**接受实体类 `User`，**必须**统一为：

> ```python
> async def some_action(
>     self,
>     user_id: UUID,
>     user_role: LiveRoomMessageUserRole,
>     ...
> ):
> ````
>
> -----
>
> #### 4\. 按层级生成的断言规范 (Assertion Rules by Layer)
>
> 你必须根据“核心测试哲学”（第 2 节）生成对应的断言逻辑。
>
> ##### 4.1. 实用派测试 (Pragmatic: CRUD & API)
>
>   * **A. API 响应验证 (针对 API 测试)**:
>
>       * **必须**同时验证 HTTP 状态码和完整的 JSON 响应结构（`code`, `message`, `data`）。
>       * **必须**验证业务状态码（`response.json()["code"]`）和 `"data"` 内部的关键字段。
>       * 对于失败响应，**必须**验证业务错误码（例如 `assert response.json()["code"] == 2001`）。
>
>   * **B. 数据库状态验证 [关键修改]**
>
>       * **(针对 CRUD 层测试)**:
>
>           * 在**同一个** `db_session` 中执行的 `create()`, `update()`, `remove()` 操作，**必须**在操作后立即使用 `await db.refresh(obj)` 或**再次 `get(db, obj.id)`**，来验证数据已正确持久化。
>           * **[增量测试模式]**：对于涉及记录数量或列表查询的测试，**必须使用增量判断方式**（见 `3.6.2` 节）。在测试前记录基线状态（记录数、ID集合等），测试后只验证增量变化。
>
>       * **(针对 API / Endpoint 层测试)**:
>
>           * **[关键禁令]**：在 `await client.patch(...)` 或 `client.post(...)`（它们使用*独立会话*）之后，**严禁**使用*原始的* `db_session`（用于 Arrange 阶段）来 `get()` 或查询对象。这样做**必定**会读取到 SQLAlchemy 身份映射（Identity Map）中的**陈旧缓存**，导致测试失败。
>
>       * **[API 层正确验证方案]**: 要验证 API 调用后的数据库*真实*状态，**必须**选择以下两种方法之一：
>
>         1.  **(首选 - 验证响应)**: **只断言** API 返回的 `response.json()["data"]` 中的内容是否正确（例如 `assert response.json()["data"]["title"] == "新标题"`）。
>         2.  **(次选 - 验证数据库)**: **必须**导入 `async_session_factory`（见 3.1 节），创建一个**全新的、独立的会话**（`async with async_session_factory() as new_db:`），并使用这个 `new_db` 会话执行显式的 `select()` 语句来查询数据库，以获取**最新**数据。
>         - **[增量测试模式]**：如果涉及记录数量验证，**必须使用增量判断方式**。在API调用前记录基线状态，调用后验证增量变化。
>
> ##### 4.2. 学院派测试 (Academic: Service & I/O)
>
>   * **A. 异常逻辑验证**:
>
>       * **必须**使用 `with pytest.raises(TopicPermissionDeniedException):` 来验证在特定条件下是否正确抛出了**自定义业务异常**。
>
>   * **B. 行为验证 (Mocks)**:
>
>       * **必须**使用 `mock_crud.assert_called_once_with(...)` 来验证依赖是否被正确调用。
>       * **[关键] Mock 路径规范 (MANDATORY)**:
>           * 假设 Service 层使用别名导入 (`from app.crud import topic as crud_topic`)。
>           * 测试代码在 `mocker.patch()` 中**必须**使用**原始模块路径** (`"app.crud.topic.create"`)。
>           * **必须**为异步函数使用 `new_callable=AsyncMock`。
>       * **[关键] Mock 断言参数格式规范 (MANDATORY)**:
>           * **断言参数必须与实际调用方式完全一致**：
>             * 如果 Service 层调用时使用**位置参数**（如 `await crud_health.check_database_connection(db)`），则断言必须使用**位置参数**（`mock_check.assert_called_once_with(db)`）。
>             * 如果 Service 层调用时使用**关键字参数**（如 `await crud_topic.create(db=db, obj_in=...)`），则断言可以使用**关键字参数**（`mock_create.assert_called_once_with(db=db, obj_in=...)`）。
>           * **⚠️ 常见错误**：使用关键字参数断言（`db=db`），但实际调用使用位置参数（`db`），会导致断言失败。
>           * **正确做法**：**必须**先检查实际Service层代码的调用方式，然后使用相同格式的断言。
>       * **示例**:
>         ```python
>         # Service 层 (app/services/my_service.py)
>         # from app.crud import topic as crud_topic
>         # await crud_topic.create(...)
>         ```

> ````
>     # 测试层 (tests/unit/test_my_service.py)
>     @pytest.mark.asyncio
>     async def test_service_create(mocker):
>         # 1. 准备 (Arrange)
>         # [关键] Mock 原始路径 "app.crud.topic.create"
>         mock_create = mocker.patch(
>             "app.crud.topic.create",
>             new_callable=AsyncMock,
>             return_value=mock_topic_object
>         )
>         # ...
>         # 3. 断言 (Assert)
>         mock_create.assert_called_once_with(...)
>     ```
> ````
>
> ##### 4.3. [关键] 异步 SQLAlchemy 会话的测试规范 (V5.2 修复)
>
> **🚨（新增）异步 SQLAlchemy Session 的禁止操作**
> 在所有测试中：
>
> **严禁使用**：
>
>   * `db.expire_all()`
>   * `db.expire(obj)`
>
> 因为这会触发 lazy loading，并在异步环境中引发：
>
> `sqlalchemy.exc.MissingGreenlet`
>
> **🚨（新增）避免 Identity Map 缓存污染**
> 若测试创建了对象（会话 A），但 API 在另一会话（B）修改了该对象：
>
>   * 会话 A 再查询该 ID → 会直接命中缓存，无法看到最新值
>
> **⭐ 正确验证最新数据库值的两种模式**
>
>   * **最推荐方式**：完全依赖 API 返回 JSON，测试不访问数据库（见 `4.1.A`）。
>   * **若必须访问数据库**：
>       * 必须使用新的独立会话（见 `4.1.B`）。
>       * `async with async_session_factory() as new_db:`
>       * `stmt = select(Model).where(Model.id == id)`
>       * `result = await new_db.execute(stmt)`
>       * `obj = result.scalar_one_or_none()`
>   * **⚠️ 警告**：不能在**同一个**测试会话中二次查询同一主键，否则会命中身份映射缓存。
>
> -----
>
> #### 5\. 工程与风格规范 (Engineering & Style Norms)
>
>   * **RESTful 路径规范 (MANDATORY)**:
>       * 在 `APIRouter` 中定义 `prefix` 时，**严禁**在末尾添加斜杠 (例如：`prefix="/rooms"`)。
>       * 对于集合端点（`GET /rooms`, `POST /rooms`），**必须**在装饰器中使用 `path="/"`。
>
> -----
>
> #### 6\. [动态生成] 核心上下文与被测试代码 (Context & Code to Test)
>
> > 
>
> ```python
> # [文件路径 1, 例如: app/core/deps.py]
> # ... (粘贴 app/core/deps.py 的全部内容, 特别是 get_current_user) ...
> ```
>
> ```python
> # [文件路径 2, 例如: app/models/user.py]
> # ... (粘贴 app/models/user.py 的全部内容, 包含角色 Enum) ...
> ```
>
> ```python
> # [文件路径 3, 例如: app/models/topic.py]
> # ... (粘贴 app/models/topic.py 的全部内容) ...
> ```
>
> ```python
> # [文件路径 4, 例如: app/schemas/topic.py]
> # ... (粘贴 app/schemas/topic.py 的全部内容) ...
> ```
>
> ```python
> # [文件路径 5, 例如: app/crud/topic.py]
> # ... (粘贴 app/crud/topic.py 的全部内容) ...
> ```
>
> ```python
> # [文件路径 6, 例如: app/services/topic.py]
> # ... (粘贴 app/services/topic.py 的全部内容) ...
> ```
>
> ```python
> # [文件路径 7, 例如: app/api/endpoints/topics.py]
> # ... (粘贴 app/api/endpoints/topics.py 的全部内容) ...
> ```
>
> -----
>
> #### 7\. [动态生成] 具体测试任务列表 (Dynamic-Generated Specific Test Tasks)
>
> **你必须为 `Section 6` 中的代码严格生成以下所有测试用例：**
>
> > 
>
> **A. 针对 `[文件名 1, 例如: app/crud/topic.py]` (实用派 CRUD 测试)**
>
>   * **`async def get(db, id)`**:
>       * (成功) `test_get_success`: 创建一个 `Topic` 对象，调用 `get()`，断言返回的对象字段正确。
>       * (失败) `test_get_not_found`: 调用 `get()` 传入一个不存在的 `id`，断言结果为 `None`。
>   * **`async def create(db, obj_in)`**:
>       * (成功) `test_create_success`: 调用 `create()`，然后**必须**使用 `db.refresh()` 或再次 `get()`，断言数据库中对象的字段与 `obj_in` 匹配。
>       * **[增量测试模式]**：**必须**在测试前记录记录总数（基线），测试后验证记录数增加了1。
>   * **`async def remove(db, id)`**:
>       * (成功) `test_remove_success`: 创建一个对象，调用 `remove()`，然后**必须**再次 `get()`，断言结果为 `None`。
>       * **[增量测试模式]**：**必须**在测试前记录记录总数（基线），测试后验证记录数减少了1。
>
> **B. 针对 `[文件名 2, 例如: app/services/topic.py]` (学院派 Service 测试) [V5.2 修复]**
>
>   * **(示例: 检查签名后发现是 `async def create_topic(db, user_id: UUID, user_role: Enum, topic_in)`)**
>       * (成功) `test_create_topic_success`:
>           * 准备 (Arrange): 定义 `test_user_id` 和 `test_user_role`。Mock `crud_topic.create` (使用 `new_callable=AsyncMock`) 并使其返回一个模拟的 `Topic` 对象。
>           * 执行 (Act): 调用 `service.create_topic(..., user_id=test_user_id, user_role=test_user_role, ...)`。
>           * 断言 (Assert): **必须**断言 `crud_topic.create.assert_called_once_with(db=db, obj_in=...)`，确保 `obj_in` 中已正确包含 `user_id`。
>   * **(示例: 检查签名后发现是 `async def delete_topic(db, user_id: UUID, user_role: Enum, topic_id)`)**
>       * (成功) `test_delete_topic_as_owner_success`:
>           * 准备 (Arrange): 定义 `owner_user_id = uuid.uuid4()` 和 `admin_role`。Mock `crud_topic.get` (返回一个 `user_id` 匹配 `owner_user_id` 的模拟 `Topic`)。Mock `crud_topic.remove`。
>           * 执行 (Act): 调用 `service.delete_topic(..., user_id=owner_user_id, user_role=admin_role, ...)`。
>           * 断言 (Assert): **必须**断言 `crud_topic.remove.assert_called_once_with(db=db, id=topic_id)`。
>       * (失败 - 权限) `test_delete_topic_as_non_owner_raises_exception`:
>           * 准备 (Arrange): 定义 `owner_user_id` 和 `non_owner_user_id` 及 `regular_role`。Mock `crud_topic.get` (返回一个 `user_id` 为 `owner_user_id` 的模拟 `Topic`)。
>           * 执行 & 断言 (Act & Assert): **必须**使用 `with pytest.raises(PermissionDeniedException):` 来包裹 `service.delete_topic(..., user_id=non_owner_user_id, user_role=regular_role, ...)` 的调用。
>       * (失败 - 未找到) `test_delete_topic_not_found_raises_exception`:
>           * 准备 (Arrange): Mock `crud_topic.get` (返回 `None`)。
>           * 执行 & 断言 (Act & Assert): **必须**使用 `with pytest.raises(NotFoundException):` 来包裹调用。
>
> **C. 针对 `[文件名 3, 例如: app/api/endpoints/topics.py]` (实用派 API 测试) [V5.2 修复]**
>
>   * **`@router.post("/", ...)` (create\_topic)**:
>       * (成功) `test_api_create_topic_success`:
>           * 准备 (Arrange): 使用 `async_client` 和 `db_session`。准备一个有效的 `json` payload（唯一字段使用 Faker）。**必须**使用 `async for db in db_session:` 解包 `db_session` fixture。
>           * 执行 (Act): **必须**使用 `async for client in async_client:` 解包 `async_client` fixture，然后在 `async for` 块内执行 `POST "/topics/"`（如 `response = await client.post("/api/v1/topics/", json=payload)`）。
>           * 断言 (Assert): **所有断言必须在 `async for` 块内**：
>               * 断言 `response.status_code == 200` (或 201) 且 `response.json()["code"] == 0`。
>               * **[关键]** 导入 `async_session_factory`，**创建新会话** `new_db`，并用 `new_db` 查询数据库，断言数据已正确持久化。
>   * **`@router.delete("/{topic_id}", ...)` (delete\_topic)**:
>       * (成功) `test_api_delete_topic_success`:
>           * 准备 (Arrange): 在 `db_session` 中创建一个属于当前用户（`current_user`）的 `Topic`。**必须**使用 `async for db in db_session:` 解包 `db_session` fixture。
>           * 执行 (Act): **必须**使用 `async for client in async_client:` 解包 `async_client` fixture，然后在 `async for` 块内执行 `DELETE "/topics/{topic_id}"`（如 `response = await client.delete(f"/api/v1/topics/{topic_id}")`）。
>           * 断言 (Assert): **所有断言必须在 `async for` 块内**：
>               * 断言 `response.status_code == 200` 且 `response.json()["code"] == 0`。
>               * **[关键]** 导入 `async_session_factory`，**创建新会话** `new_db`，并用 `new_db` 查询数据库，断言该 `Topic` 为 `None`。
>       * (失败 - 权限) `test_api_delete_topic_permission_denied`:
>           * 准备 (Arrange): 在 `db_session` 中创建**不**属于当前用户的 `Topic`。**必须**使用 `async for db in db_session:` 解包 `db_session` fixture。
>           * 执行 (Act): **必须**使用 `async for client in async_client:` 解包 `async_client` fixture，然后在 `async for` 块内执行 `DELETE "/topics/{topic_id}"`。
>           * 断言 (Assert): **所有断言必须在 `async for` 块内**：
>               * 断言 `response.status_code == 403` (或 401)。
>               * **必须**断言 `response.json()["code"]` 为对应的业务错误码 (例如 `2001`)。
>       * (失败 - 未找到) `test_api_delete_topic_not_found`:
>           * 准备 (Arrange): 准备一个不存在的 `topic_id`。
>           * 执行 (Act): **必须**使用 `async for client in async_client:` 解包 `async_client` fixture，然后在 `async for` 块内执行 `DELETE "/topics/99999"`。
>           * 断言 (Assert): **所有断言必须在 `async for` 块内**：
>               * 断言 `response.status_code == 404`。
>               * **必须**断言 `response.json()["code"]` 为对应的业务错误码。
>
> -----
>
> #### 8\. 交付物 (Deliverable - 执行者)
>
> 请根据**以上所有规范 (1-7)**，为 `Section 6` 中提供的代码生成**完整的 `pytest` 测试文件**。
>
>   * **交付物**:
>       * `tests/test_crud_[...].py` (如果提供了 `app/crud/...py`)
>       * `tests/test_service_[...].py` (如果提供了 `app/services/...py`)
>       * `tests/test_api_[...].py` (如果提供了 `app/api/endpoints/...py`)
>   * **指令**:
>     1.  **遵循任务列表**: 严格按照 `Section 7` 中的列表生成所有指定的测试用例。
>     2.  **遵循所有规范**: 确保生成的代码 100% 遵循 `Section 2-5` (哲学, 语法, 断言, 风格)。
>     3.  **[增量测试模式]**：
>        - **严禁修改**已存在的测试函数（即使发现错误）。
>        - **允许修改 `conftest.py`**（仅限添加新内容）：
>          - ✅ **只增加**新的Fixture、函数、变量、导入等。
>          - ❌ **严禁修改**已有的Fixture、函数、变量等。
>          - ❌ **严禁删除**任何现有内容。
>          - ✅ **必须检查冲突**：新增的内容必须与已有的内容没有冲突（函数名、变量名、Fixture名等不重复）。
>        - **必须使用增量判断方式**验证数据库操作（见 `3.6.2` 节）。
>        - 新测试函数必须遵循现有测试的命名约定和代码风格。
>
> **[你生成的 `.md` 文件的内容应在这里结束]**

-----

#### 3\. 测试模式判断逻辑 (Test Mode Detection - 规划师)

在生成指令文档时，**必须**根据以下规则判断测试模式：

**⚠️ 关键判断原则**：
- **默认优先使用增量测试模式**：如果项目中已存在测试文件（如 `tests/conftest.py`），**默认应该使用增量测试生成模式**，因为新增模块的测试应该在已有测试基础上增量生成。
- **只有在全新项目时才使用全新测试模式**：只有当项目**完全没有**现有测试文件时，才使用全新测试生成模式。

1. **增量测试生成模式**（如果满足以下任一条件）：
   - ✅ **项目已存在测试文件**（优先判断）：检查项目中是否存在 `tests/conftest.py` 或任何 `tests/test_*.py` 文件，**如果存在，则默认判定为增量测试生成模式**。
   - 用户引用了 `@tests/conftest.py` 或任何 `@tests/test_*.py` 文件（明确指示增量模式）
   - 用户明确说明"增量测试"或"不修改现有测试"
   
2. **全新测试生成模式**（仅在以下情况下使用）：
   - ✅ **项目完全没有测试文件**：检查项目中**不存在** `tests/conftest.py` 和任何 `tests/test_*.py` 文件（全新项目）
   - 用户**明确指定**"全新测试"、"clean test"或"全新测试生成模式"（即使项目有测试文件）

3. **在生成的指令文档中明确标注**：
   - 在 `Section 1` 中添加测试模式说明
   - **必须明确标注**测试模式（增量/全新）
   - 如果为增量模式，必须在 `Section 1` 中明确说明：
     - **测试模式**：增量测试生成模式（新增测试，已有测试文件不能修改）
     - **说明**：为XXX模块**新增**测试代码，在已有测试基础上增量生成
     - **关键约束**：
       - **严禁修改**已存在的测试文件
       - **允许修改 `conftest.py`**（**仅限添加新内容**）
       - **必须检查冲突**：新增的内容必须与已有的内容没有冲突
     - 已引用的测试文件列表（如果用户明确引用了测试文件）
     - 增量测试的特殊约束（不能修改现有测试、可以修改conftest.py但只能增加新内容、必须使用增量判断、必须检查冲突）

#### 4\. 你的交付物 (Your Deliverable - 规划师)

你的**唯一**交付物是**一个 `.md` 文件**（即 `Section 2` 中定义的 `最终测试代码生成提示词.md`）。

  * **必须**包含 `Section 2` 中定义的所有静态部分（规则 1-5 和 8）。
  * **必须**包含一个根据你**自动分析**的代码**动态生成的 `Section 6`（完整的代码上下文）**。
    - **增量模式（MANDATORY）**：
      - `Section 6` **必须包含** `tests/conftest.py` 的完整内容（即使未被明确引用），以便执行者了解现有Fixture定义、代码风格和命名约定
      - `Section 6` **必须包含**已存在的相关测试文件内容（如果存在），以便执行者了解现有测试结构、命名约定和代码风格
      - 所有测试文件内容应标注为"现有测试文件"或"已存在的测试文件"
  * **必须**包含一个根据你**自动分析**的代码**动态生成的 `Section 7`（具体测试任务列表）**。
    - **增量模式（MANDATORY）**：
      - `Section 7` **必须在开头增加**"⚠️ 增量测试模式说明"段落，明确说明：
        - 已存在的测试文件列表（如 `tests/conftest.py`、`tests/test_config_security.py` 等）
        - 需要新增的测试文件列表（如 `tests/test_crud_xxx.py`、`tests/test_service_xxx.py`、`tests/test_api_xxx.py` 等）
        - **不能修改**已存在的测试文件（即使发现错误也不行）
      - 测试用例描述中应强调"复用现有Fixture"（如"使用 `db_session` fixture（复用现有 `db_session` fixture）"）
      - 应说明哪些测试已存在（无需生成），哪些测试需要新增
  * **必须**在生成的文档中明确标注测试模式（全新/增量）。
  * **严禁**生成任何 `.py` 测试代码。你只生成用于指导下一步的 `.md` 提示词文档。