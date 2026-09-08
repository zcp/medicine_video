
# 直播核心服务增加JWT认证的代码生成提示词

## 一、角色定义 (Role Definition)

你是一名资深的 Python 后端工程师，精通 FastAPI、SQLAlchemy 2.0 (异步模式) 和现代 API 设计原则。你擅长在现有代码库上进行**增量式开发**，能够根据详尽的设计文档、数据模型和代码上下文，精确地添加JWT认证功能，同时最大限度地减少对现有稳定代码的改动。

## 二、任务目标 (Task Objective)

你的任务是为现有的直播核心服务添加 **JWT Token 认证功能**，使所有需要用户身份验证的API接口都能正确验证用户身份。此外，后端查询结果没有执行过滤，由于可以从jwt token中获取user id， 因此后端可以支持基于user id的查询过滤。

**核心约束 (Primary Constraint):** 你的首要原则是**最小化对现有代码的修改**。当前代码库已经过测试。你必须优先选择添加新函数、新方法和新类，而不是重构现有代码。只有在支持新功能绝对必要时，才允许进行微小的修改。

**重要提醒：** 你的任务**仅限**于添加JWT Token认证功能，**严禁**修改任何现有的业务逻辑、API响应格式、错误处理逻辑或其他功能。你只需要：
1. 在API端点中添加认证参数
2. 在数据模型中添加用户关联字段
3. 在业务逻辑中添加用户ID过滤
4. 创建JWT验证模块

## 三、核心上下文信息 (Core Context Information)

### 3.1. 项目结构与待修改文件

你将要修改以下文件，请严格按照其在项目中的路径进行操作：

```
backend/live_core_service/
├── 📄 requirements.txt                    # Python 依赖包列表
├── 📄 .env                                # 环境变量配置
├── 📄 run.py                              # 服务启动入口文件
├── 📁 app/                                # 主应用目录
│   ├── 📄 main.py                         # FastAPI 应用主文件
│   ├── 📁 api/                            # API 路由层
│   │   └── 📁 v1/
│   │       └── 📁 endpoints/
│   │           ├── 📄 room.py             # 房间管理 API 端点 ⚠️ 需修改
│   │           └── 📄 session.py          # 场次管理 API 端点 ⚠️ 需修改
│   ├── 📁 core/                           # 核心配置和工具
│   │   ├── 📄 config.py                   # 应用配置 ⚠️ 需修改
│   │   ├── 📄 responses.py                # 响应处理工具
│   │   └── 📄 file_handler.py             # 文件处理工具 🆕 需创建
│   ├── 📁 models/                         # 数据模型层
│   │   └── 📄 live_core.py                # 数据模型 (无需修改)
│   ├── 📁 schemas/                        # 数据验证模式
│   │   └── 📄 live_core.py                # 数据模式 (无需修改)
│   ├── 📁 crud/                           # 数据操作层
│   │   └── 📄 room.py                     # 房间CRUD ⚠️ 需修改
│   └── 📁 services/                       # 业务逻辑服务层
│       └── 📄 room_service.py             # 房间服务 ⚠️ 需修改
├── 📁 media/                              # 媒体文件存储目录
│   └── 📁 rooms/                          # 直播间相关文件 🆕
└── 📁 tests/                              # 测试目录
```

### 3.2. 需要JWT认证的API接口列表

**所有以下API接口都需要添加JWT Token认证：**

#### **房间管理API (live_rooms)**
1. `POST /api/v1/rooms` - 创建直播房间
2. `GET /api/v1/rooms` - 获取房间列表
3. `GET /api/v1/rooms/{room_id}` - 获取房间详情
4. `PATCH /api/v1/rooms/{room_id}` - 更新房间信息
5. `DELETE /api/v1/rooms/{room_id}` - 删除房间
6. `GET /api/v1/rooms/{room_id}/sub-venues` - 获取分会场列表
7. `POST /api/v1/rooms/{room_id}/sessions` - 为指定房间创建计划场次
8. `GET /api/v1/rooms/{room_id}/sessions` - 获取指定房间的场次列表

#### **场次管理API (live_sessions)**
9. `POST /api/v1/rooms/{room_id}/sessions` - 创建计划场次
10. `GET /api/v1/rooms/{room_id}/sessions` - 获取场次列表
11. `GET /api/v1/sessions/{session_id}` - 获取场次详情
12. `PATCH /api/v1/sessions/{session_id}` - 更新场次信息
13. `DELETE /api/v1/sessions/{session_id}` - 删除场次

**重要说明：以下内部API不需要JWT认证：**
- `GET /internal/srs/on_publish` - SRS推流预检请求（系统内部调用）
- `POST /internal/srs/on_publish` - SRS推流开始回调（系统内部调用）
- `GET /internal/srs/on_unpublish` - SRS断流预检请求（系统内部调用）
- `POST /internal/srs/on_unpublish` - SRS断流结束回调（系统内部调用）

**认证要求：**
- 所有接口都需要在请求头中包含 `Authorization: Bearer <JWT_TOKEN>`
- 查看操作：登录用户可以查看所有数据，支持可选的用户过滤
- 修改/删除操作：用户只能修改/删除自己创建的资源
- 未认证的请求应返回 401 状态码

### 3.3. 环境变量配置

**在 `backend/live_core_service/.env` 文件中添加：**

```bash
# ===== JWT 认证配置 =====
# 必须与用户服务使用相同的JWT密钥和算法
JWT_SECRET_KEY=your-super-secret-key-here  # 与用户服务保持一致
JWT_ALGORITHM=HS256                        # 与用户服务保持一致
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30         # JWT Token 过期时间（分钟）

# ===== 用户服务配置 =====
# 用于验证JWT Token的发行者信息
USERS_SERVICE_ISSUER=https://your-domain.authing.cn/oidc  # 可选，用于额外验证
```

**环境变量加载方式：**
在服务启动时（如 `run.py` 或 `main.py` 文件顶部），必须添加以下代码来加载环境变量：

```python
from dotenv import load_dotenv
import os

# 加载当前目录的 .env 文件
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

# 或者更明确地指定路径
load_dotenv('.env')
```

> **重要**：确保在任何使用 `os.getenv()` 的代码执行之前调用 `load_dotenv()`。

### 3.4. 依赖的文件
本次增量修改需要依赖以下文件：

**核心模型定义：**
- `app/models/live_core.py` - 包含 LiveRoom、LiveSession、SessionStatistics 模型定义
- `app/schemas/live_core.py` - 包含对应的 Pydantic Schema 定义

**数据库操作：**
- `app/crud/room_service.py` - 包含所有房间管理相关的数据库操作方法
- `app/crud/session_service.py` - 包含所有直播session相关的数据库操作方法

**业务逻辑：**
- `app/services/room_service.py` - 包含所有房间管理相关的业务逻辑方法
- `app/services/session_service.py` - 包含所有直播session相关的业务逻辑方法
- 
**API端点：**
- `app/api/v1/endpoints/room.py` - 包含所有房间管理相关的API端点实现
- 
- `app/api/v1/endpoints/session.py` - 包含所有场次管理相关的API端点实现

**核心配置：**
- `app/core/responses.py` - 包含 create_response 和 create_error_response 函数

## 四、技术实现要求

### 4.1. JWT验证原理

**JWT验证通过共享密钥实现：**
- 用户服务使用 `JWT_SECRET_KEY` 签名JWT Token
- 直播核心服务使用相同的 `JWT_SECRET_KEY` 验证JWT Token
- 验证成功后，从Token payload中获取用户信息（如 `user_id`）

### 4.2. 用户数据隔离

**所有直播房间和场次必须与用户关联：**
#### **数据模型修改要求：**

**1. LiveRoom模型修改 (`app/models/live_core.py`)**
- **字段修改**：将现有的 `user_id` 字段从 `nullable=True` 改为 `nullable=False`
- **数据完整性**: 使用 `UNIQUE`, `ENUM` 保证数据准确，`user_id` 可以通过jwt token 保证引用完整性。
- **外键约束**: 由于微服务架构，`user_id` 无外键约束，通过JWT Token验证用户存在性
- **索引优化**：确保存在用户ID索引 `Index("idx_live_rooms_user_id", "user_id")`

**2. Schema验证修改 (`app/schemas/live_core.py`)**
- **RoomCreate Schema**：不需要添加user_id字段，从JWT Token获取
- **Room Response Schema**：包含 `user_id` 字段用于响应

**3. 实际需求**：
- 所有操作都需要JWT认证（支持登录用户）
- 直播间和直播session是所有登录用户都可以访问的
- 用户可以选择显示只属于自己的直播间和直播session（可选过滤）
- 如果前端没有明确要求，后端就显示所有数据
- 用户只能修改/删除自己创建的资源（权限控制）

**4. 实现方式**：
- 所有查询接口都支持可选的 `user_id` 参数
- 如果提供 `user_id`，则只返回该用户的资源
- 如果不提供 `user_id`，则返回所有资源
- 修改/删除操作必须验证资源所有权


### 4.3. 应用层验证机制

#### 4.3.1 user_id引用完整性保证

**设计原理：**
- JWT Token由用户服务颁发，包含真实用户的public_id
- Token有效即证明用户存在，无需跨服务验证
- 通过Token提取的user_id直接用于数据库操作

**实现流程：**
1. 用户登录 → 用户服务验证 → 颁发JWT Token
2. LiveCore Service验证Token → 提取user_id
3. 使用user_id创建/查询数据 → 保证引用完整性

**优势：**
- 无需跨服务查询验证用户存在性
- 性能优异，减少网络调用
- 符合微服务架构最佳实践

#### 4.3.2 JWT Token验证用户存在性

**验证逻辑：**
```python
def verify_user_authentication(token: str) -> Dict:
    """
    验证用户JWT Token
    JWT Token有效即证明用户存在，无需额外验证
    """
    try:
        # 1. 验证Token签名和格式
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        # 2. 检查Token过期时间
        if payload.get('exp') and time.time() > payload['exp']:
            raise HTTPException(status_code=401, detail="认证凭证已过期")
        
        # 3. 提取用户信息
        user_info = {
            "user_id": payload.get("user_id"),
            "username": payload.get("username"),
            "role": payload.get("role", "user")
        }
        
        # 4. 验证必要字段
        if not user_info["user_id"]:
            raise HTTPException(status_code=401, detail="Token中缺少用户ID")
        
        # 5. 【关键】JWT Token有效即证明用户存在，无需额外验证
        #    用户服务在颁发Token时已确保用户存在性
        #    这保证了user_id的引用完整性
        
        return user_info
        
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="认证凭证无效")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"认证验证失败: {str(e)}")
```


## 五、通用规范与 API 定义

### 5.1. 权威设计文档
**所有实现细节必须严格遵循【直播核心功能设计文档v2-增加jwt token身份认证支持sso】。**

### 5.2. 日志记录规范
**在每个端点函数的入口处，应使用 logger.info() 记录请求的开始。在成功完成数据库操作后，也应记录成功的消息。在 raise HTTPException 之前，应使用 logger.warning() 记录下具体的业务错误原因。**

### 5.3. 代码规范
* 遵循 `rules.md` 中定义的团队代码规范。
* **开发语言**: 使用 Python 3.8 或更高版本。
* **代码风格**: 严格遵循 PEP 8 规范。
* **异步模式**: 所有API端点必须使用 `async def` 函数，数据库操作使用 `await`。

### 5.4. 命名规范
* **类名 (Class)**: 使用大驼峰命名法 (PascalCase)，例如 `LiveRoom`。
* **函数与方法 (Function/Method)**: 使用下划线命名法 (snake_case)，例如 `create_room`。
* **变量 (Variable)**: 使用下划线命名法 (snake_case)，例如 `room_id`。
* **常量 (Constant)**: 使用全大写下划线命名法 (UPPER_SNAKE_CASE)，例如 `MAX_ROOM_COUNT`。

### 5.5. 通用响应结构
**所有 API 响应都必须遵循以下结构：**

```json
{
  "code": int,
  "message": str,
  "data": object | null,
  "timestamp": str  // ISO 8601 格式
}
```

**响应函数使用：**
### ✅ 成功响应

- 所有成功返回**必须**调用 `success_response(data=...)` 函数构建响应内容。
- 示例：
  ```python
  return success_response(data=user_info)
  ```

### ❌ 错误响应

- 所有业务错误必须返回 `fastapi.responses.JSONResponse`，其 `content` 由 `error_response(...)` 构建。
- 示例：
  ```python
  return JSONResponse(
      status_code=400,
      content=error_response(code=1001, message='参数错误')
  )
  ```

> 假设 `success_response()` 和 `error_response()` 已定义在 `app/core/responses.py` 中。

### 5.6. 异步编程规范

* **函数定义**: 所有API端点函数必须使用 `async def` 定义
* **数据库操作**: 所有数据库操作必须使用 `await` 关键字
* **依赖注入**: 使用 `Depends()` 进行异步依赖注入
* **错误处理**: 异步函数中的异常处理必须使用 `try...except` 块

## 六、日志与异常处理规范

### 6.1. 日志规范

#### 6.1.1. 日志级别
* `ERROR`: 关键系统错误、导致业务失败的异常。必须立即关注。
* `WARNING`: 潜在的问题或警告信息，不影响当前流程但需关注。
* `INFO`: 记录重要的业务操作节点，如用户登录、创建直播间等。
* `DEBUG`: 用于开发和调试阶段，记录详细的程序运行信息。

#### 6.1.2. 日志格式
每一条日志记录都应包含以下标准字段：
* 时间戳 (ISO 8601 格式)
* 日志级别 (如: INFO)
* 模块名 (如: `endpoints.room`)
* 函数名
* 行号
* 消息内容
* 异常堆栈 (仅在记录异常时包含)

#### 6.1.3. 日志内容
应记录但不限于以下关键信息：
* 系统启动与关闭事件。
* 用户认证操作（JWT验证成功/失败），需注意脱敏。
* 核心业务操作的入口和结果（如创建/更新/删除房间）。
* 所有捕获到的异常信息。
* 关键性能监控数据（如 API 耗时）。

### 6.2. 异常处理规范

#### 6.2.1. 异常分类
* **系统异常**: 系统级错误（如数据库连接失败、中间件故障）。
* **业务异常**: 不符合业务规则的正常操作（如房间不存在、权限不足）。
* **参数异常**: 用户输入参数不符合格式或校验规则。
* **权限异常**: 用户无权访问特定资源或执行特定操作。

#### 6.2.2. 异常处理原则
* **统一处理**: 实现统一的异常处理中间件来捕获所有未处理的异常，避免程序崩溃。
* **明确类型**: 使用自定义的、继承自 `Exception` 的异常类来区分不同的异常情况。
* **详细日志**: 捕获到任何异常时，都必须记录详细的错误日志，包含完整的异常堆栈。
* **格式统一**: 返回给客户端的错误响应必须遵循 `5.5. 通用响应结构` 的格式。
* **避免吞没**: 严禁捕获异常后不做任何处理（`except: pass`）。

## 七、具体代码修改指令

### 7.1. 第一部分：创建JWT认证模块

**文件**: `app/core/auth.py`

**任务**: 创建JWT Token验证功能。

**执行流程**:
1. 创建新文件 `app/core/auth.py`
2. 在文件顶部导入必要的模块：
   ```python
   import jwt
   from fastapi import HTTPException, Depends, Request
   from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
   from typing import Optional, Dict
   import os
   import logging
   ```
3. 创建 `logger` 实例：`logger = logging.getLogger(__name__)`
4. 定义JWT配置常量：
   ```python
   JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
   JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
   ```
5. 创建 `security` 实例：`security = HTTPBearer(auto_error=False)`
6. 实现 `JWTAuth` 类，包含两个静态方法：
   - `verify_token(token: str) -> Dict`: 验证JWT Token并返回payload
   - `get_current_user(token: str = Depends(security)) -> Dict`: 获取当前认证用户信息
7. 在 `verify_token` 方法中添加完整的JWT验证逻辑，包括签名验证、过期检查等
8. 在 `get_current_user` 方法中添加用户信息提取和权限验证逻辑

### 7.2. 第二部分：修改依赖注入

**文件**: `app/core/deps.py`

**任务**: 添加JWT认证依赖。

**执行流程**:
1. 在文件顶部导入JWT认证相关函数：
   ```python
   from app.core.auth import JWTAuth
   ```
2. 在现有依赖函数列表中添加新的依赖函数：
   ```python
   async def get_current_user(token: str = Depends(JWTAuth.get_current_user)) -> Dict:
       """获取当前认证用户"""
       return token
   ```
3. 确保不影响现有的其他依赖函数
4. 保持现有代码的格式和结构不变

### 7.3. 第三部分：修改数据模型

**文件**: `app/models/live_core.py`

**任务**: 在LiveRoom模型中添加用户关联字段。

**执行流程**:
1. 在 `LiveRoom` 类中添加 `user_id` 字段：
   ```python
   user_id = Column(
    UUID(as_uuid=True),
    nullable=False, 
    comment="用户ID，关联到用户服务的public_id（应用层验证）"
)
   ```
2. 在 `__table_args__` 中添加相应的索引：
   ```python
   Index("idx_live_rooms_user_id", "user_id")
   ```
3. 保持现有字段、关系、约束和索引不变
4. 确保新字段的添加不影响现有的表结构
5. **重要说明**：由于采用微服务架构，`user_id` 字段无法通过数据库外键约束保证引用完整性，需要通过JWT Token应用层验证保证数据一致性

### 7.4. 第四部分：修改数据验证模式

**文件**: `app/schemas/live_core.py`

**任务**: 在直播房间相关的Schema中添加用户ID字段。

**执行流程**:
1. **RoomCreate Schema**：不需要添加user_id字段，从JWT Token获取
2. **Room Response Schema**：包含 `user_id` 字段用于响应：
   ```python
   user_id: UUID = Field(..., description="用户ID")
   ```
3. 保持现有字段和验证规则不变
4. 确保新字段的添加不影响现有的数据验证逻辑

### 7.5. 第五部分：修改API端点

**重要说明：所有公共API都需要JWT认证，支持登录用户访问**

**Endpoint层修改：**
- 在所有公共API端点函数中添加 `current_user: dict = Depends(get_current_user)` 参数
- 从JWT Token中提取用户ID
- 将用户ID传递给Service层

**Service层修改：**
- 支持可选的用户过滤
- 不强制限制用户只能看到自己的数据
- 提供灵活的查询选项

**CRUD层修改：**
- 不需要JWT认证相关修改
- 支持可选的用户过滤
- 不强制限制数据访问
- 提供灵活的查询选项

**文件**: `app/api/v1/endpoints/room.py` 和 `app/api/v1/endpoints/session.py`

**任务**: 在所有需要认证的API端点中添加JWT认证。

**执行流程**:
1. 在文件顶部导入JWT认证依赖：
   ```python
   from app.core.deps import get_current_user
   ```
2. 在每个API端点函数中添加认证参数，**严格按照以下格式**：
   ```python
   @router.post("/rooms")
   async def create_room(
       room_data: RoomCreate,
       current_user: dict = Depends(get_current_user),  # 新增认证参数
       db: AsyncSession = Depends(get_db)
   ):
       # 在业务逻辑开始前记录日志
       logger.info(f"开始处理创建房间请求: user_id={current_user['user_id']}")
       
       # 在创建房间时使用 current_user["user_id"]
       # 其他业务逻辑保持不变
   ```

3. **逐个修改以下API端点**：

#### **房间管理API (room.py)**
- `POST /api/v1/rooms` - 创建直播房间
- `GET /api/v1/rooms` - 获取房间列表
- `GET /api/v1/rooms/{room_id}` - 获取房间详情
- `PATCH /api/v1/rooms/{room_id}` - 更新房间信息
- `DELETE /api/v1/rooms/{room_id}` - 删除房间
- `GET /api/v1/rooms/{room_id}/sub-venues` - 获取分会场列表
- `POST /api/v1/rooms/{room_id}/sessions` - 为指定房间创建计划场次
- `GET /api/v1/rooms/{room_id}/sessions` - 获取指定房间的场次列表

#### **场次管理API (session.py)**
- `POST /api/v1/rooms/{room_id}/sessions` - 创建计划场次
- `GET /api/v1/rooms/{room_id}/sessions` - 获取场次列表
- `GET /api/v1/sessions/{session_id}` - 获取场次详情
- `PATCH /api/v1/sessions/{session_id}` - 更新场次信息
- `DELETE /api/v1/sessions/{session_id}` - 删除场次

4. 在每个函数中添加日志记录：
   - 函数开始时记录：`logger.info(f"开始处理...请求: user_id={current_user['user_id']}")`
   - 成功时记录：`logger.info("成功处理...请求")`
   - 失败时记录：`logger.warning(f"...失败: {e}")`
5. 保持现有的业务逻辑、响应格式、错误处理完全不变

### 7.6. 第六部分：修改业务服务

**文件**: `app/services/room_service.py` 和 `app/services/session_service.py`

**任务**: 在Service层添加用户权限验证和可选的用户过滤功能。

#### **room_service.py 修改要求**

##### **1. 修改 `get_room_list` 方法**
- **方法签名修改**: 在 `get_room_list` 方法中添加可选的 `user_id: Optional[uuid.UUID] = None` 参数
- **参数传递**: 将 `user_id` 参数传递给CRUD层：
  ```python
  rooms, total = await crud_room.get_multi_and_total(
      db=self.db, skip=skip, limit=size, user_id=user_id
  )
  ```
- **保持现有逻辑**: 分页计算、CRUD调用逻辑完全不变

##### **2. 修改 `get_room_details` 方法**
- **方法签名修改**: 在 `get_room_details` 方法中添加可选的 `user_id: Optional[uuid.UUID] = None` 参数
- **权限验证**: 如果提供user_id，在调用CRUD层时传递用户ID进行权限验证：
  ```python
  room = await crud_room.get(db=self.db, room_id=room_id, user_id=user_id)
  ```
- **保持现有逻辑**: 异常处理逻辑完全不变

##### **3. 修改 `update_room_info` 方法**
- **方法签名修改**: 在 `update_room_info` 方法中添加 `user_id: uuid.UUID` 参数
- **权限验证**: 在调用 `self.get_room_details(room_id, user_id=user_id)` 时传递 `user_id` 参数
- **保持现有逻辑**: 直播状态检查、更新逻辑完全不变

##### **4. 修改 `delete_room` 方法**
- **方法签名修改**: 在 `delete_room` 方法中添加 `user_id: uuid.UUID` 参数
- **权限验证**: 在调用 `self.get_room_details(room_id, user_id=user_id)` 时传递 `user_id` 参数
- **保持现有逻辑**: 直播状态检查、删除逻辑完全不变

##### **5. 修改 `get_sub_venue_list` 方法**
- **方法签名修改**: 在 `get_sub_venue_list` 方法中添加可选的 `user_id: Optional[uuid.UUID] = None` 参数
- **权限验证**: 如果提供user_id，在调用 `self.get_room_details(parent_room_id, user_id=user_id)` 时传递 `user_id` 参数
- **保持现有逻辑**: 分页计算、CRUD调用逻辑完全不变

##### **6. 修改 `create_new_room` 方法**
- **方法签名修改**: 在 `create_new_room` 方法中添加 `user_id: uuid.UUID` 参数
- **权限验证**: 在创建房间时，将user_id传递给CRUD层：
  ```python
  # 创建新房间
  room = await crud_room.create(db=self.db, obj_in=room_in, user_id=user_id)
  ```
- **保持现有逻辑**: 父房间验证逻辑完全不变
- 
#### **session_service.py 修改要求**

##### **1. 修改 `create_scheduled_session` 方法**
- **方法签名修改**: 在 `create_scheduled_session` 方法中添加 `user_id: uuid.UUID` 参数
- **权限验证**: 在验证房间存在性时，同时验证房间是否属于当前用户：
  ```python
  room = await crud_room.get(db=self.db, room_id=room_id, user_id=user_id)
  ```
- **保持现有逻辑**: 场次创建逻辑完全不变

##### **2. 修改 `get_sessions_by_room` 方法**
- **方法签名修改**: 在 `get_sessions_by_room` 方法中添加可选的 `user_id: Optional[uuid.UUID] = None` 参数
- **权限验证**: 如果提供user_id，在验证房间存在性时，同时验证房间是否属于当前用户：
  ```python
  room = await crud_room.get(db=self.db, room_id=room_id, user_id=user_id)
  ```
- **保持现有逻辑**: 分页计算、CRUD调用逻辑完全不变

##### **3. 修改 `get_session_details` 方法**
- **方法签名修改**: 在 `get_session_details` 方法中添加可选的 `user_id: Optional[uuid.UUID] = None` 参数
- **权限验证**: 如果提供user_id，通过场次获取房间ID，然后验证房间是否属于当前用户：
  ```python
  session = await crud_session.get(db=self.db, session_id=session_id)
  if session and session.room_id and user_id:
      room = await crud_room.get(db=self.db, room_id=session.room_id, user_id=user_id)
      if not room:
          raise SessionNotFoundException()
  ```
- **保持现有逻辑**: 统计信息获取逻辑完全不变

##### **4. 修改 `update_scheduled_session_info` 方法**
- **方法签名修改**: 在 `update_scheduled_session_info` 方法中添加 `user_id: uuid.UUID` 参数
- **权限验证**: 通过场次获取房间ID，然后验证房间是否属于当前用户
- **保持现有逻辑**: 状态检查、更新逻辑完全不变

##### **5. 修改 `delete_session` 方法**
- **方法签名修改**: 在 `delete_session` 方法中添加 `user_id: uuid.UUID` 参数
- **权限验证**: 通过场次获取房间ID，然后验证房间是否属于当前用户
- **保持现有逻辑**: 状态检查、删除逻辑完全不变

### **7.7. 第七部分：修改CRUD层**

**文件**: `app/crud/room.py` 和 `app/crud/session.py`

**任务**: 在CRUD层添加可选的用户过滤功能，但不包含权限验证逻辑。权限验证由Service层负责。

#### **room.py 修改要求**

##### **1. 修改 `get` 方法**
- **方法签名修改**: 在 `get` 方法中添加可选的 `user_id: Optional[uuid.UUID] = None` 参数
- **数据过滤**: 如果提供 `user_id`，添加用户ID过滤（仅用于数据过滤，不用于权限验证）：
  ```python
  query = select(LiveRoom).where(LiveRoom.id == room_id)
  if user_id:
      query = query.where(LiveRoom.user_id == user_id)
  ```
- **保持现有逻辑**: 查询执行、结果返回逻辑完全不变
- **注意**: 此方法不进行权限验证，权限验证由Service层负责

##### **2. 修改 `get_multi_and_total` 方法**
- **方法签名修改**: 在 `get_multi_and_total` 方法中添加可选的 `user_id: Optional[uuid.UUID] = None` 参数
- **数据过滤**: 如果提供 `user_id`，添加用户ID过滤（仅用于数据过滤，不用于权限验证）：
  ```python
  query = select(LiveRoom)
  if user_id:
      query = query.where(LiveRoom.user_id == user_id)
  ```
- **保持现有逻辑**: 排序、分页、计数逻辑完全不变
- **注意**: 此方法不进行权限验证，权限验证由Service层负责

##### **3. 修改 `get_sub_venues_with_live_status` 方法**
- **方法签名修改**: 在 `get_sub_venues_with_live_status` 方法中添加可选的 `user_id: Optional[uuid.UUID] = None` 参数
- **数据过滤**: 如果提供user_id，在查询分会场时，添加主会场用户ID过滤（仅用于数据过滤，不用于权限验证）：
  ```python
  # 如果提供user_id，添加主会场用户ID过滤
  if user_id:
      main_room_query = select(LiveRoom).where(
          and_(LiveRoom.id == parent_room_id, LiveRoom.user_id == user_id)
      )
      main_room = await db.execute(main_room_query)
      if not main_room.scalar_one_or_none():
          # 如果主会场不属于当前用户，返回空结果
          return [], 0
  ```
- **保持现有逻辑**: 分会场查询、状态关联逻辑完全不变
- **注意**: 此方法不进行权限验证，权限验证由Service层负责

##### **4. 修改 `create` 方法**
- **方法签名修改**: 在 `create` 方法中添加 `user_id: uuid.UUID` 参数
- **用户关联**: 在创建房间对象时，设置user_id字段：
  ```python
  # 创建房间对象
  db_obj = LiveRoom(
      title=obj_in.title,
      description=obj_in.description,
      cover_url=obj_in.cover_url,
      stream_key=stream_key,
      is_private=obj_in.is_private,
      record_by_default=obj_in.record_by_default,
      category_id=obj_in.category_id,
      parent_room_id=obj_in.parent_room_id,
      user_id=user_id  # 新增：设置用户ID
  )
  ```
- **保持现有逻辑**: stream_key生成、唯一性检查、数据库操作逻辑完全不变
- **注意**: 此方法不进行权限验证，权限验证由Service层负责

#### **session.py 修改要求**

##### **1. 修改 `get` 方法**
- **方法签名修改**: 在 `get` 方法中添加可选的 `user_id: Optional[uuid.UUID] = None` 参数
- **数据过滤**: 如果提供 `user_id`，通过房间ID添加用户过滤（仅用于数据过滤，不用于权限验证）：
  ```python
  query = select(LiveSession).where(LiveSession.id == session_id)
  if user_id:
      query = query.join(LiveRoom).where(LiveRoom.user_id == user_id)
  ```
- **保持现有逻辑**: 查询执行、结果返回逻辑完全不变
- **注意**: 此方法不进行权限验证，权限验证由Service层负责

##### **2. 修改 `get_multi_by_room_and_total` 方法**
- **方法签名修改**: 在 `get_multi_by_room_and_total` 方法中添加可选的 `user_id: Optional[uuid.UUID] = None` 参数
- **数据过滤**: 如果提供user_id，在查询场次前，添加房间用户ID过滤（仅用于数据过滤，不用于权限验证）：
  ```python
  # 如果提供user_id，添加房间用户ID过滤
  if user_id:
      room_query = select(LiveRoom).where(
          and_(LiveRoom.id == room_id, LiveRoom.user_id == user_id)
      )
      room = await db.execute(room_query)
      if not room.scalar_one_or_none():
          # 如果房间不属于当前用户，返回空结果
          return [], 0
  ```
- **保持现有逻辑**: 分页、排序、计数逻辑完全不变
- **注意**: 此方法不进行权限验证，权限验证由Service层负责

##### **3. 修改 `get_with_stats` 方法（需要修改）**
- **方法签名修改**：在 `get_with_stats` 方法中添加可选的 `user_id: Optional[uuid.UUID] = None` 参数
- **数据过滤**：如果提供 `user_id`，通过 JOIN `LiveRoom` 表添加用户过滤（仅用于数据过滤，不用于权限验证）：
  ```python
  query = select(LiveSession).options(selectinload(LiveSession.statistics))
  if user_id:
      query = query.join(LiveRoom).where(LiveRoom.user_id == user_id)
  query = query.where(LiveSession.id == session_id)
  ```
- **保持现有逻辑**：统计信息预加载、查询执行逻辑完全不变
- **注意**: 此方法不进行权限验证，权限验证由Service层负责

##### **4. 修改 `update` 方法（不需要修改）**
- **注意**: 此方法不进行权限验证，权限验证由Service层负责

##### **5. 修改 `remove` 方法（不要需要修改）**
- **注意**: 此方法不进行权限验证，权限验证由Service层负责


**重要注意事项**:
1. **架构分层**: CRUD层专注于数据访问，不包含权限验证逻辑
2. **权限验证**: 所有权限验证都在Service层进行，避免重复验证
3. **数据过滤**: CRUD层的user_id参数仅用于数据过滤，不用于权限验证
4. **方法简化**: CRUD层的update和remove方法不包含user_id参数，专注于数据操作
5. **异常处理**: 权限验证失败在Service层抛出异常，CRUD层不处理权限异常
6. **最小修改**: 只添加必要的数据过滤代码，不修改现有的业务逻辑、错误处理或日志记录
7. **保持一致性**: 所有方法的修改模式保持一致，确保代码的可维护性

## 八、架构设计原则

### 8.1. 分层权限验证架构

**设计原则：**
- **Service层职责**: 负责业务逻辑和权限验证，确保用户只能访问和操作自己的资源
- **CRUD层职责**: 专注于数据访问操作，提供可选的用户过滤功能，不包含权限验证逻辑
- **避免重复验证**: 权限验证只在Service层进行，避免在CRUD层重复验证

**实现策略：**
1. **API层**: 验证JWT Token，提取用户ID
2. **Service层**: 进行权限验证，调用CRUD层时传递user_id进行数据过滤
3. **CRUD层**: 执行纯粹的数据访问操作，根据user_id进行数据过滤

**示例对比：**

**❌ 错误做法（重复验证）：**
```python
# Service层
room = await crud_room.get(db=self.db, room_id=room_id, user_id=user_id)  # 第一次验证

# CRUD层
if not room_obj or str(room_obj.user_id) != str(user_id):  # 第二次验证
    raise SessionActionForbiddenException("无权修改此会话")
```

**✅ 正确做法（单一验证）：**
```python
# Service层
room = await crud_room.get(db=self.db, room_id=room_id, user_id=user_id)  # 权限验证
if not room:
    raise RoomNotFoundException()

# CRUD层
# 只进行数据过滤，不进行权限验证
query = select(LiveRoom).where(LiveRoom.id == room_id)
if user_id:
    query = query.where(LiveRoom.user_id == user_id)
```

## 九、安全要求

### 9.1. 认证失败处理

- 未提供Token：返回 401 状态码，错误信息 "认证凭证缺失"
- Token无效：返回 401 状态码，错误信息 "认证凭证无效"
- Token过期：返回 401 状态码，错误信息 "认证凭证已过期"

### 9.2. 用户权限验证
- **查看操作**：登录用户可以查看所有数据，支持可选用户过滤
 **修改/删除操作**：用户只能修改/删除自己创建的房间和场次
- **应用层验证**：所有涉及用户数据的操作都通过JWT Token验证用户存在性
- **数据完整性**：JWT Token有效即证明用户存在，无需跨服务验证
- **权限控制**：所有涉及用户数据的修改/删除操作都必须验证用户权限
- **架构分层**：权限验证在Service层进行，CRUD层专注于数据访问
- 
### 9.3. 错误响应格式

**认证失败响应格式：**
```json
{
  "code": 401,
  "message": "认证失败",
  "data": {
    "error": "具体错误信息"
  },
  "timestamp": "2024-03-20T10:00:00Z"
}
```
### 9.4. 应用层验证配置

```python
# 应用层验证配置
USER_ID_VALIDATION_MODE = "jwt_token"  # 通过JWT Token验证用户存在性
CROSS_SERVICE_VALIDATION = False  # 不进行跨服务用户验证
JWT_USER_EXISTENCE_PROOF = True  # JWT Token有效即证明用户存在
```

**验证策略：**
- **用户存在性验证**：通过JWT Token有效性保证
- **数据引用完整性**：通过应用层验证保证
- **跨服务通信**：无需额外的用户验证API调用

## 十、最终交付

请根据以上所有要求和核心约束，特别是**在生成这些文件时，必须严格遵守以下原则：只应用前面指令中明确描述的增量添加和最小修改。对于指令中未提及的任何已有代码，必须保持其原始样貌，不得进行任何形式的重构、格式化调整或逻辑变更**，为我生成以下文件的完整实现：

1. `app/core/auth.py` - JWT认证模块（新文件）
2. `app/core/deps.py` - 依赖注入（修改现有文件）
3. `app/models/live_core.py` - 数据模型（修改现有文件）
4. `app/schemas/live_core.py` - 数据验证模式（修改现有文件）
5. `app/api/v1/endpoints/room.py` - 房间管理API端点（修改现有文件）
6. `app/api/v1/endpoints/session.py` - 场次管理API端点（修改现有文件）
7. `app/services/room_service.py` - 房间管理业务服务（修改现有文件）
8. `app/services/session_service.py` - 场次管理业务服务（修改现有文件）
9. `app/crud/room.py` - 房间管理CRUD操作（修改现有文件）
10. `app/crud/session.py` - 场次管理CRUD操作（修改现有文件）
11. `requirements.txt` - 依赖包（修改现有文件）

## 十一、注意事项

1. **不要实现SSO登录功能**：直播核心服务不需要实现SSO登录，只需要验证用户服务颁发的JWT Token
2. **保持现有功能不变**：所有现有的直播功能必须保持完整，只是增加认证层
3. **最小化修改**：只添加必要的认证代码，不重构现有业务逻辑
4. **用户数据隔离**：
   - 直播间和直播session是所有登录用户都可以访问的（公开访问）
   - 用户可以选择显示只属于自己的直播间和直播session（可选过滤）
   - 如果前端没有明确要求，后端就显示所有数据
   - 用户只能修改/删除自己创建的资源（权限控制）
5. **应用层验证**：
   - 通过JWT Token验证用户存在性，保证user_id引用完整性
   - 无需跨服务查询验证用户存在性
   - JWT Token有效即证明用户存在，符合微服务架构最佳实践
6. **错误处理**：保持现有的错误处理逻辑，只添加认证相关的错误处理
7. **日志记录**：在每个API端点中添加适当的日志记录，记录用户ID和操作结果
8. **响应格式**：保持现有的响应格式不变，只添加认证相关的错误响应
9. **数据库操作**：保持现有的数据库操作逻辑不变，只添加用户ID过滤和权限验证
10.**异步编程**：确保所有修改都符合异步编程规范，使用 `async/await` 语法

