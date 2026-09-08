您说得非常对！我来参考用户功能服务的提示词文档，对媒体下载服务的JWT认证提示词进行完善和改进。

## 改进后的提示词文档

```markdown
# 媒体下载服务增加JWT认证的代码生成提示词

**重要技术说明：**
- 本项目使用 SQLAlchemy 同步模式，不是异步模式
- API端点使用同步函数，不是async函数  
- 数据库Session使用 sqlalchemy.orm.Session，不是AsyncSession
- 所有示例代码中的 db: Session = Depends(get_db)  # 正确

## 一、角色定义 (Role Definition)

你是一名资深的 Python 后端工程师，精通 FastAPI、SQLAlchemy 2.0 (同步模式) 和现代 API 设计原则。你擅长在现有代码库上进行**增量式开发**，能够根据详尽的设计文档、数据模型和代码上下文，精确地添加JWT认证功能，同时最大限度地减少对现有稳定代码的改动。

## 二、任务目标 (Task Objective)

你的任务是为现有的媒体下载服务添加 **JWT Token 认证功能**，使所有需要用户身份验证的API接口都能正确验证用户身份。

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
backend/media_download_service/
├── 📄 requirements.txt                    # Python 依赖包列表
├── 📄 pytest.ini                         # pytest 测试配置
├── 📄 Dockerfile                          # Docker 容器构建文件
├── 📄 run.py                              # 服务启动入口文件
├── 📁 app/                                # 主应用目录
│   ├── 📄 main.py                         # FastAPI 应用主文件
│   ├── 📄 init_db.py                      # 数据库初始化脚本
│   ├── 📄 database.py                     # 数据库连接配置
│   ├── 📁 api/                            # API 路由层
│   │   └── 📁 v1/                         # API 版本 1
│   │       ├── 📄 api.py                  # API 路由注册
│   │       └── 📁 endpoints/              # API 端点实现
│   │           ├── 📄 __init__.py
│   │           └── 📄 download.py         # 下载相关 API 端点
│   ├── 📁 core/                           # 核心配置和工具
│   │   ├── 📄 __init__.py
│   │   ├── 📄 config.py                   # 应用配置
│   │   ├── 📄 config_backup.py            # 配置备份文件
│   │   ├── 📄 deps.py                     # 依赖注入
│   │   ├── 📄 exceptions.py               # 自定义异常类
│   │   └── 📄 response.py                 # 响应处理工具
│   ├── 📁 models/                         # 数据模型层
│   │   └── 📄 download.py                 # 下载相关数据模型
│   ├── 📁 schemas/                        # 数据验证模式
│   │   ├── 📄 common.py                   # 通用数据模式
│   │   └── 📄 download.py                 # 下载相关数据模式
│   └── 📁 services/                       # 业务逻辑服务层
│       └── 📄 download_service.py         # 下载业务逻辑服务
├── 📁 tests/                              # 测试目录
├── 📁 storage/                            # 存储目录
│   └── 📁 hls/                           # HLS 流媒体存储
│       └── 📁 ts/                         # TS 分片文件存储
```

### 3.2. 需要JWT认证的API接口列表

**所有以下API接口都需要添加JWT Token认证：**

### 3.2. 需要JWT认证的API接口列表

**所有以下API接口都需要添加JWT Token认证：**

1. `POST /api/v1/download/tasks` - 创建下载任务
2. `GET /api/v1/download/tasks` - 获取任务列表
3. `GET /api/v1/download/tasks/{task_id}` - 获取任务详情
4. `PUT /api/v1/download/tasks/{task_id}` - 更新任务
5. `DELETE /api/v1/download/tasks/{task_id}` - 删除任务
6. `POST /api/v1/download/tasks/{task_id}/start` - 开始任务
7. `POST /api/v1/download/tasks/{task_id}/retry` - 重试任务
8. `POST /api/v1/download/tasks/{task_id}/failures` - 创建失败记录
9. `GET /api/v1/download/tasks/{task_id}/failures` - 查询失败记录
10. `POST /api/v1/download/tasks/{task_id}/videos` - 创建已下载视频记录
11. `GET /api/v1/download/tasks/{task_id}/videos` - 获取已下载视频列表
12. `POST /api/v1/download/tasks/{task_id}/failures/{failure_id}/retry` - 重试特定任务的失败记录
13. `POST /api/v1/download/tasks/{task_id}/failures/{failure_id}/abandon` - 放弃特定任务的失败记录
14. `POST /api/v1/download/failures/{failure_id}/retry` - 重试失败记录（全局）
15. `POST /api/v1/download/failures/{failure_id}/abandon` - 放弃失败记录（全局）
16. `GET /api/v1/download/videos/{video_id}` - 获取已下载视频详情
17. `GET /api/v1/download/failures` - 获取全局失败记录列表
18. `GET /api/v1/download/failures/{failure_id}` - 获取失败记录详情

**认证要求：**
- 所有接口都需要在请求头中包含 `Authorization: Bearer <JWT_TOKEN>`
- 用户只能访问和操作自己创建的下载任务
- 未认证的请求应返回 401 状态码

### 3.3. 环境变量配置

**在 `backend/media_download_service/.env` 文件中添加：**

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

>    **重要**：确保在任何使用 `os.getenv()` 的代码执行之前调用 `load_dotenv()`。

### 3.4. 依赖的文件
本次增量修改需要依赖以下文件：

**核心模型定义：**
- `app/models/download.py` - 包含 DownloadTask、DownloadFailure、DownloadedVideo 模型定义
- `app/schemas/download.py` - 包含对应的 Pydantic Schema 定义

**业务逻辑：**
- `app/services/download_service.py` - 包含所有下载相关的业务逻辑方法

**API端点：**
- `app/api/v1/endpoints/download.py` - 包含所有下载相关的API端点实现

**核心配置：**
- `app/core/response.py` - 包含 create_response 和 create_error_response 函数
- `app/core/exceptions.py` - 包含自定义异常类定义
**DownloadTask 模型结构：**
```python
class DownloadTask(Base):
    """下载任务表"""
    __tablename__ = "download_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    video_id = Column(UUID(as_uuid=True), nullable=False, comment="视频ID，格式：UUID")
    liveroom_id = Column(String(20), nullable=False, comment="直播间ID")
    liveroom_title = Column(String(255), nullable=True, comment="直播间标题")
    liveroom_url = Column(String(255), nullable=True, comment="直播间URL")
    resource_url = Column(String(255), nullable=False, comment="视频播放URL或图片URL")
    resource_type = Column(String(20), nullable=False, comment="image,hls, mp4")
    status = Column(
        String(20),
        nullable=False,
        default='pending',
        comment="pending, processing, completed, partial_completed,failed, cancelled"
    )
    progress = Column(Float, nullable=False, default=0, comment="下载进度（0-1）")
    retry_count = Column(Integer, nullable=False, default=0, comment="重试次数")
    last_error = Column(Text, nullable=True, comment="最后错误信息")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    completed_at = Column(DateTime, nullable=True, comment="完成下载时间")

    # 关系
    failures = relationship("DownloadFailure", back_populates="task", cascade="all, delete-orphan")
    video = relationship("DownloadedVideo", back_populates="task", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        # 约束
        CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'partial_completed', 'failed', 'cancelled')",
            name="check_status"
        ),
        CheckConstraint(
            "progress >= 0 AND progress <= 1",
            name="check_progress_range"
        ),
        # 索引
        Index("idx_download_tasks_video_id", "video_id"),
        Index("idx_download_tasks_liveroom_id", "liveroom_id"),
        Index("idx_download_tasks_status", "status"),
        Index("idx_download_tasks_created_at", "created_at")
    )

    def __repr__(self):
        return f"<DownloadTask(id={self.id}, status={self.status})>"

    # 需要添加：
    # user_id = Column(UUID(as_uuid=True), nullable=False)
```

## 四、技术实现要求

### 4.1. JWT验证原理

**JWT验证通过共享密钥实现：**
- 用户服务使用 `JWT_SECRET_KEY` 签名JWT Token
- 媒体下载服务使用相同的 `JWT_SECRET_KEY` 验证JWT Token
- 验证成功后，从Token payload中获取用户信息（如 `user_id`）

### 4.2. 用户数据隔离

**所有下载任务必须与用户关联：**
- 在 @app/models/download.py 中的`DownloadTask` 模型中添加 `user_id` 字段
- 在 @app/schema/download.py 中的`DownloadTaskBase` 和 `DownloadTask` Schema中添加 `user_id` 字段
- 创建任务时，从JWT Token中获取 `user_id` 并保存
- 查询任务时，只能返回当前用户的任务
- 修改/删除任务时，验证任务是否属于当前用户

## 五、通用规范与 API 定义

### 5.1. 权威设计文档
**所有实现细节必须严格遵循【媒体下载服务设计文档v2】。**

### 5.2. 日志记录规范
**在每个端点函数的入口处，应使用 logger.info() 记录请求的开始。在成功完成数据库操作后，也应记录成功的消息。在 raise HTTPException 之前，应使用 logger.warning() 记录下具体的业务错误原因。**

### 5.3. 代码规范
* 遵循 `rules.md` 中定义的团队代码规范。
* **开发语言**: 使用 Python 3.8 或更高版本。
* **代码风格**: 严格遵循 PEP 8 规范。
* **格式化**:
    * 使用 4 个空格作为缩进。
    * 所有代码文件必须使用 UTF-8 编码。

### 5.4. 命名规范
* **类名 (Class)**: 使用大驼峰命名法 (PascalCase)，例如 `DownloadTask`。
* **函数与方法 (Function/Method)**: 使用下划线命名法 (snake_case)，例如 `create_download_task`。
* **变量 (Variable)**: 使用下划线命名法 (snake_case)，例如 `task_id`。
* **常量 (Constant)**: 使用全大写下划线命名法 (UPPER_SNAKE_CASE)，例如 `MAX_RETRY_COUNT`。

### 5.5. 通用响应结构
**所有 API 响应都必须遵循以下结构：**

```json
{
  "code": int,
  "message": str,
  "data": object | None,
  "timestamp": str  // ISO 8601 格式
}
```

**响应函数使用：**
- **成功响应**: 所有成功的端点返回**必须**调用 `create_response(data=...)` 函数来构建
- **错误响应**: 所有业务错误必须返回 `create_error_response(...)` 函数构建的响应

### 5.6. 环境变量管理规范

* **加载时机**: 在应用启动的最早阶段（如 `run.py` 或 `main.py` 文件顶部）使用 `python-dotenv` 加载环境变量文件。
* **文件位置**: 环境变量文件应放置在各功能模块的根目录下（如 `backend/media_download_service/.env`）。
* **验证机制**: 在使用环境变量的关键业务逻辑中，必须验证环境变量是否存在，缺失时抛出明确的异常。
* **动态构建**: 对于需要动态构建的配置（如 `issuer` URL），应基于基础环境变量进行构建，并提供合理的默认值。
* **日志记录**: 在读取环境变量后，应记录配置信息（注意脱敏处理敏感信息）。

## 六、日志与异常处理规范

### 6.1. 日志规范

#### 6.1.1. 日志级别
* `ERROR`: 关键系统错误、导致业务失败的异常。必须立即关注。
* `WARNING`: 潜在的问题或警告信息，不影响当前流程但需关注。
* `INFO`: 记录重要的业务操作节点，如创建下载任务、开始下载等。
* `DEBUG`: 用于开发和调试阶段，记录详细的程序运行信息。

#### 6.1.2. 日志格式
每一条日志记录都应包含以下标准字段：
* 时间戳 (ISO 8601 格式)
* 日志级别 (如: INFO)
* 模块名 (如: `endpoints.download`)
* 函数名
* 行号
* 消息内容
* 异常堆栈 (仅在记录异常时包含)

#### 6.1.3. 日志内容
应记录但不限于以下关键信息：
* 系统启动与关闭事件。
* 用户认证操作（JWT验证成功/失败），需注意脱敏。
* 核心业务操作的入口和结果（如创建/更新/删除下载任务）。
* 所有捕获到的异常信息。
* 关键性能监控数据（如 API 耗时）。

#### 6.1.4. 日志管理与存储
* **集中管理**: 使用 ELK Stack (Elasticsearch, Logstash, Kibana) 进行日志的统一收集、存储和查询。
* **存储策略**:
    * 日志文件按日期进行分割和归档。
    * 对用户密码、密钥等所有敏感信息必须进行脱敏处理。

### 6.2. 异常处理规范

#### 6.2.1. 异常分类
* **系统异常**: 系统级错误（如数据库连接失败、中间件故障）。
* **业务异常**: 不符合业务规则的正常操作（如任务不存在、权限不足）。
* **参数异常**: 用户输入参数不符合格式或校验规则。
* **权限异常**: 用户无权访问特定资源或执行特定操作。

#### 6.2.2. 异常处理原则
* **统一处理**: 实现统一的异常处理中间件 (Exception Handling Middleware) 来捕获所有未处理的异常，避免程序崩溃。
* **明确类型**: 使用自定义的、继承自 `Exception` 的异常类来区分不同的异常情况。
* **详细日志**: 捕获到任何异常时，都必须记录详细的错误日志，包含完整的异常堆栈。
* **格式统一**: 返回给客户端的错误响应必须遵循 `5.5. 通用响应结构` 的格式。
* **避免吞没**: 严禁捕获异常后不做任何处理（`except: pass`）。
* **优雅降级**: 在可能的情况下，对系统异常进行优雅降级处理，保证核心功能的可用性。

#### 6.2.3. 异常处理流程
1. 在业务代码中**捕获**可预见的异常。
2. 将原始异常**记录**到日志系统。
3. 将原始异常**转换**为对应的自定义业务异常类型。
4. 由统一的异常处理中间件捕获所有异常，并**返回**统一格式的错误响应。
5. 在必要时（如文件句柄、数据库连接），使用 `finally` 块**清理**资源。

### 6.3. 响应与异常处理规范

* **成功响应**: 所有成功的端点返回**必须**调用 `success_response(data=...)` 函数来构建。
* **错误响应**: 所有业务错误必须返回 `fastapi.responses.JSONResponse`，其 `content` 由 `error_response(...)` 函数构建。
* **安全异步异常处理**: 在 `try...except` 块中，**严禁**在捕获数据库异常后访问失效的ORM对象属性。必须在 `try` 块之前将所需属性（如`current_user["user_id"]`）提取到局部变量中。

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
   def get_current_user(token: str = Depends(JWTAuth.get_current_user)) -> Dict:
       """获取当前认证用户"""
       return token
   ```
3. 确保不影响现有的其他依赖函数
4. 保持现有代码的格式和结构不变

### 7.3. 第三部分：修改数据模型

**文件**: `app/models/download.py`

**任务**: 在DownloadTask模型中添加用户关联字段。

**执行流程**:
1. 在 `DownloadTask` 类中添加 `user_id` 字段：
   ```python
   user_id = Column(UUID(as_uuid=True), nullable=False, comment="用户ID，关联到用户服务")
   ```
2. 在 `__table_args__` 中添加相应的索引：
   ```python
   Index("idx_download_tasks_user_id", "user_id")
   ```
3. 保持现有字段、关系、约束和索引不变
4. 确保新字段的添加不影响现有的表结构

### 7.4. 第四部分：修改数据验证模式

**文件**: `app/schemas/download.py`

**任务**: 在下载任务相关的Schema中添加用户ID字段。

**执行流程**:
1. 在 `DownloadTaskBase` 类中添加 `user_id` 字段：
   ```python
   user_id: UUID = Field(..., description="用户ID，关联到用户服务")
   ```
2. 在 `DownloadTask` 响应模型中添加 `user_id` 字段：
   ```python
   user_id: UUID = Field(..., description="用户ID")
   ```
3. 保持现有字段和验证规则不变
4. 确保新字段的添加不影响现有的数据验证逻辑

**重要说明**：
- 只在 `DownloadTaskBase` 和 `DownloadTask` 中添加 `user_id` 字段
- `DownloadFailureBase`、`DownloadedVideoBase` 等Schema类不需要修改
- 这些类通过 `task_id` 字段间接关联到用户信息
- 避免Schema层面的数据冗余

### 7.5. 第四部分：修改API端点

**文件**: `app/api/v1/endpoints/download.py`

**任务**: 在所有需要认证的API端点中添加JWT认证。

**执行流程**:
1. 在文件顶部导入JWT认证依赖：
   ```python
   from app.core.deps import get_current_user
   ```
2. 在每个API端点函数中添加认证参数，**严格按照以下格式**：
   * ** 在每个API端点函数中添加 `current_user: dict = Depends(get_current_user)` 参数
   * **从JWT Token中提取 `user_id` 并传递给服务层
   * **在业务逻辑中使用 `current_user["user_id"]` 进行用户数据隔离
   * **代码示例：
   ```python
   @router.post("/tasks")
   def create_download_task(
       request: DownloadTaskCreate,
       current_user: dict = Depends(get_current_user),  # 新增认证参数
       db: Session = Depends(get_db)
   ):
       # 在业务逻辑开始前记录日志
       logger.info(f"开始处理创建下载任务请求: user_id={current_user['user_id']}")
       
       # 在创建任务时使用 current_user["user_id"]
       # 其他业务逻辑保持不变
   ```

3. **逐个修改以下9个API端点**：
  -`POST /api/v1/download/tasks` - 创建下载任务
  -`GET /api/v1/download/tasks` - 获取任务列表
  -`GET /api/v1/download/tasks/{task_id}` - 获取任务详情
  -`PUT /api/v1/download/tasks/{task_id}` - 更新任务
  -`DELETE /api/v1/download/tasks/{task_id}` - 删除任务
  -`POST /api/v1/download/tasks/{task_id}/start` - 开始任务
  -`POST /api/v1/download/tasks/{task_id}/retry` - 重试任务
  -`POST /api/v1/download/tasks/{task_id}/failures` - 创建失败记录
  -`GET /api/v1/download/tasks/{task_id}/failures` - 查询失败记录
  -`POST /api/v1/download/tasks/{task_id}/videos` - 创建已下载视频记录
  -`GET /api/v1/download/tasks/{task_id}/videos` - 获取已下载视频列表
  -`POST /api/v1/download/tasks/{task_id}/failures/{failure_id}/retry` - 重试特定任务的失败记录
  -`POST /api/v1/download/tasks/{task_id}/failures/{failure_id}/abandon` - 放弃特定任务的失败记录
  -`POST /api/v1/download/failures/{failure_id}/retry` - 重试失败记录（全局）
  -`POST /api/v1/download/failures/{failure_id}/abandon` - 放弃失败记录（全局）
  -`GET /api/v1/download/videos/{video_id}` - 获取已下载视频详情
  -`GET /api/v1/download/failures` - 获取全局失败记录列表
  -`GET /api/v1/download/failures/{failure_id}` - 获取失败记录详情


4. 在每个函数中添加日志记录：
   - 函数开始时记录：`logger.info(f"开始处理...请求: user_id={current_user['user_id']}")`
   - 成功时记录：`logger.info("成功处理...请求")`
   - 失败时记录：`logger.warning(f"...失败: {e}")`
5. 保持现有的业务逻辑、响应格式、错误处理完全不变



### 7.5. 第五部分：修改业务服务
**文件**: `app/services/download_service.py`
**需要修改的函数（按实际代码中的函数名）：**

1. `create_download_task` - 创建下载任务
2. `get_download_task` - 获取下载任务
3. `list_download_tasks` - 获取任务列表
4. `count_download_tasks` - 统计任务数量
5. `update_download_task` - 更新下载任务
6. `delete_download_task` - 删除下载任务
7. `create_download_failure` - 创建失败记录
8. `list_download_failures` - 获取失败记录列表
9. `count_download_failures` - 统计失败记录数量
10. `get_download_failure` - 获取失败记录
11. `retry_download_failure` - 重试失败记录
12. `abandon_download_failure` - 放弃失败记录
13. `pause_download_task` - 暂停下载任务
14. `resume_download_task` - 恢复下载任务
15. `create_downloaded_video` - 创建已下载视频记录
16. `list_downloaded_videos` - 获取已下载视频列表
17. `count_downloaded_videos` - 统计已下载视频数量
18. `start_download_task` - 启动下载任务
19. `retry_download_task` - 重试下载任务
20. `get_downloaded_video` - 获取已下载视频详情
21. `list_failures` - 获取全局失败记录列表
22. `get_failure_details` - 获取失败记录详情

**不需要修改的内部/工具方法：**
- `_parse_sort` - 内部排序解析方法
- `_process_download_*_result` - 内部结果处理方法
- `generate_standard_filename` - 工具方法
- `modify_m3u8_for_local_playback` - 工具方法
- `download_*` - 下载相关工具方法
- `_retry_only_failed_segments` - 内部重试方法



**任务**: 在业务逻辑中添加用户ID处理。

*重要类型处理说明**：
在比较 `user_id` 时，必须进行类型转换以确保比较正确：
- `task.user_id` 是数据库中的 `UUID` 类型
- `user_id` 参数可能是 `str` 类型（从JWT Token中获取）
- **必须使用 `str(task.user_id) != str(user_id)` 进行比较**

**执行流程**:

#### 1. 修改 `create_download_task` 方法
- **方法签名修改**: 在 `create_download_task(self, task_data: DownloadTaskCreate)` 中添加 `user_id: uuid.UUID` 参数
- **数据库保存**: 在创建 `DownloadTask` 实例时，添加 `user_id=user_id` 字段
- **保持现有逻辑**: 其他字段赋值逻辑完全不变，只增加 `user_id` 字段

#### 2. 修改 `get_download_task` 方法
- **方法签名修改**: 在 `get_download_task(self, task_id: uuid.UUID)` 中添加 `user_id: uuid.UUID` 参数
- **权限验证**: 在 `if not task:` 检查之后，添加用户权限验证：

  ```python
  # 验证任务是否属于当前用户 - 统一转换为字符串比较
  if str(task.user_id) != str(user_id):
      logger.info(f"Task {task_id} not found, {task.user_id}, {user_id}")
      raise TaskNotFoundError(f"Task {task_id} not found")  # 使用现有异常类
  ```
- **保持现有逻辑**: 其他查询逻辑完全不变

#### 3. 修改 `list_download_tasks` 方法
- **方法签名修改**: 在 `list_download_tasks` 方法中添加 `user_id: uuid.UUID` 参数
- **查询过滤**: 在现有的 `query = self.db.query(DownloadTask)` 之后，添加用户ID过滤：
  ```python
  # 添加用户ID过滤
  query = query.filter(DownloadTask.user_id == user_id)
  ```
- **保持现有逻辑**: 状态过滤、排序、分页逻辑完全不变

#### 4. 修改 `count_download_tasks` 方法
- **方法签名修改**: 在 `count_download_tasks` 方法中添加 `user_id: uuid.UUID` 参数
- **查询过滤**: 在现有的 `query = self.db.query(func.count(DownloadTask.id))` 之后，添加用户ID过滤：
  ```python
  # 添加用户ID过滤
  query = query.filter(DownloadTask.user_id == user_id)
  ```
- **保持现有逻辑**: 状态过滤逻辑完全不变

#### 5. 修改 `update_download_task` 方法
- **方法签名修改**: 在 `update_download_task` 方法中添加 `user_id: uuid.UUID` 参数
- **权限验证**: 在调用 `self.get_download_task(task_id)` 时，传递 `user_id` 参数
- **保持现有逻辑**: 更新逻辑完全不变

#### 6. 修改 `delete_download_task` 方法
- **方法签名修改**: 在 `delete_download_task` 方法中添加 `user_id: uuid.UUID` 参数
- **权限验证**: 在调用 `self.get_download_task(task_id)` 时，传递 `user_id` 参数
- **保持现有逻辑**: 删除逻辑完全不变

#### 7. 修改 `start_download_task` 方法
- **方法签名修改**: 在 `start_download_task` 方法中添加 `user_id: uuid.UUID` 参数
- **权限验证**: 在调用 `self.get_download_task(task_id)` 时，传递 `user_id` 参数
- **保持现有逻辑**: 下载执行逻辑完全不变

#### 8. 修改 `retry_download_task` 方法
- **方法签名修改**: 在 `retry_download_task` 方法中添加 `user_id: uuid.UUID` 参数
- **权限验证**: 在调用 `self.get_download_task(task_id)` 时，传递 `user_id` 参数
- **保持现有逻辑**: 重试逻辑完全不变

#### 9. 修改 `create_download_failure` 方法
- **方法签名修改**: 在 `create_download_failure` 方法中添加 `user_id: uuid.UUID` 参数
- **权限验证**: 在创建失败记录之前，验证任务是否属于当前用户：
  ```python
  # 验证任务是否属于当前用户
  task = self.get_download_task(task_id, user_id=user_id)
  if not task:
      raise TaskNotFoundError(f"Task {task_id} not found")
  ```
- **保持现有逻辑**: 创建失败记录的逻辑完全不变

#### 10. 修改 `list_download_failures` 方法
- **方法签名修改**: 在 `list_download_failures` 方法中添加 `user_id: uuid.UUID` 参数
- **权限验证**: 在查询失败记录之前，验证任务是否属于当前用户：
  ```python
  # 验证任务是否属于当前用户
  task = self.get_download_task(task_id, user_id=user_id)
  if not task:
      raise TaskNotFoundError(f"Task {task_id} not found")
  ```
- **保持现有逻辑**: 查询失败记录的逻辑完全不变

#### 11. 修改 `count_download_failures` 方法
- **方法签名修改**: 在 `count_download_failures` 方法中添加 `user_id: uuid.UUID` 参数
- **权限验证**: 在计数之前，验证任务是否属于当前用户：
  ```python
  # 验证任务是否属于当前用户
  task = self.get_download_task(task_id, user_id=user_id)
  if not task:
      raise TaskNotFoundError(f"Task {task_id} not found")
  ```
- **保持现有逻辑**: 计数逻辑完全不变

#### 12. 修改 `get_download_failure` 方法
- **方法签名修改**: 在 `get_download_failure` 方法中添加 `user_id: uuid.UUID` 参数
- **权限验证**: 在获取失败记录之前，验证任务是否属于当前用户：
  ```python
    # 先获取失败记录
    failure = self.db.query(DownloadFailure).filter(DownloadFailure.id == failure_id).first()
    if not failure:
        raise FailureRecordNotFoundError(f"Failure {failure_id} not found")
    
    # 然后验证任务是否属于当前用户
    task = self.get_download_task(failure.task_id, user_id=user_id)
    # get_download_task 内部已经包含了权限验证逻辑
    
    return failure
  ```
- **保持现有逻辑**: 获取失败记录的逻辑完全不变

#### 13. 修改 `retry_download_failure` 方法
- **方法签名修改**: 在 `retry_download_failure` 方法中添加 `user_id: uuid.UUID` 参数
- **权限验证**: 在重试失败记录之前，验证任务是否属于当前用户：
  ```python
  # 验证任务是否属于当前用户
  task = self.get_download_task(failure.task_id, user_id=user_id)
  if not task:
      raise TaskNotFoundError(f"Task {failure.task_id} not found")
  ```
- **保持现有逻辑**: 重试逻辑完全不变

#### 14. 修改 `abandon_download_failure` 方法
- **方法签名修改**: 在 `abandon_download_failure` 方法中添加 `user_id: uuid.UUID` 参数
- **权限验证**: 在放弃失败记录之前，验证任务是否属于当前用户：
  ```python
  # 验证任务是否属于当前用户
  task = self.get_download_task(failure.task_id, user_id=user_id)
  if not task:
      raise TaskNotFoundError(f"Task {failure.task_id} not found")
  ```
- **保持现有逻辑**: 放弃逻辑完全不变

#### 15. 修改 `pause_download_task` 方法
- **方法签名修改**: 在 `pause_download_task` 方法中添加 `user_id: uuid.UUID` 参数
- **权限验证**: 在调用 `self.get_download_task(task_id)` 时，传递 `user_id` 参数
- **保持现有逻辑**: 暂停逻辑完全不变

#### 16. 修改 `resume_download_task` 方法
- **方法签名修改**: 在 `resume_download_task` 方法中添加 `user_id: uuid.UUID` 参数
- **权限验证**: 在调用 `self.get_download_task(task_id)` 时，传递 `user_id` 参数
- **保持现有逻辑**: 恢复逻辑完全不变

#### 17. 修改 `create_downloaded_video` 方法
- **方法签名修改**: 在 `create_downloaded_video` 方法中添加 `user_id: uuid.UUID` 参数
- **权限验证**: 在创建视频记录之前，验证任务是否属于当前用户：
  ```python
  # 验证任务是否属于当前用户
  task = self.get_download_task(task_id, user_id=user_id)
  if not task:
      raise TaskNotFoundError(f"Task {task_id} not found")
  ```
- **保持现有逻辑**: 创建视频记录的逻辑完全不变

#### 18. 修改 `list_downloaded_videos` 方法
- **方法签名修改**: 在 `list_downloaded_videos` 方法中添加 `user_id: uuid.UUID` 参数
- **权限验证**: 在查询视频记录之前，验证任务是否属于当前用户：
  ```python
  # 验证任务是否属于当前用户
  task = self.get_download_task(task_id, user_id=user_id)
  if not task:
      raise TaskNotFoundError(f"Task {task_id} not found")
  ```
- **保持现有逻辑**: 查询视频记录的逻辑完全不变

#### 19. 修改 `count_downloaded_videos` 方法
- **方法签名修改**: 在 `count_downloaded_videos` 方法中添加 `user_id: uuid.UUID` 参数
- **权限验证**: 在计数之前，验证任务是否属于当前用户：
  ```python
  # 验证任务是否属于当前用户
  task = self.get_download_task(task_id, user_id=user_id)
  if not task:
      raise TaskNotFoundError(f"Task {task_id} not found")
  ```
- **保持现有逻辑**: 计数逻辑完全不变

#### 20. 修改 `get_downloaded_video` 方法
- **方法签名修改**: 在 `get_downloaded_video` 方法中添加 `user_id: uuid.UUID` 参数
- **权限验证**: 在获取视频记录之前，验证任务是否属于当前用户：

```python
# 先获取视频记录
video = self.db.query(DownloadedVideo).filter(DownloadedVideo.video_id == video_id).first()
if not video:
    raise VideoNotFoundError(f"Video {video_id} not found")

# 然后验证任务是否属于当前用户
task = self.get_download_task(video.task_id, user_id=user_id)
# get_download_task 内部已经包含了权限验证逻辑

return video
```
- **保持现有逻辑**: 获取视频记录的逻辑完全不变

#### 21. 修改 `list_failures` 方法
- **方法签名修改**: 在 `list_failures` 方法中添加 `user_id: uuid.UUID` 参数
- **查询过滤**: 在现有的查询逻辑中添加用户ID过滤：
  ```python
  # 添加用户ID过滤
  query = query.join(DownloadTask).filter(DownloadTask.user_id == user_id)
  ```
- **保持现有逻辑**: 其他筛选、排序、分页逻辑完全不变

#### 22. 修改 `get_failure_details` 方法
- **方法签名修改**: 在 `get_failure_details` 方法中添加 `user_id: uuid.UUID` 参数
- **权限验证**: 在获取失败记录之前，验证任务是否属于当前用户：
  ```python
  # 验证任务是否属于当前用户
  task = self.get_download_task(failure.task_id, user_id=user_id)
  if not task:
      raise TaskNotFoundError(f"Task {failure.task_id} not found")
  ```
- **保持现有逻辑**: 获取失败记录的逻辑完全不变


**重要注意事项**:
1. **类型转换**: 所有 `user_id` 比较都必须使用 `str(task.user_id) != str(user_id)` 格式
2. **异常类使用**: 所有权限验证失败都使用现有的 `TaskNotFoundError` 异常类，不要创建新的异常类
3. **字段名准确性**: 确保使用正确的字段名 `user_id`，不要使用其他名称
4. **方法调用**: 在需要权限验证的地方，调用 `self.get_download_task(task_id, user_id=user_id)` 来验证权限
5. **最小修改**: 只添加必要的参数和权限验证代码，不修改任何现有的业务逻辑、错误处理或日志记录
6. **保持一致性**: 所有方法的修改模式保持一致，确保代码的可维护性


## 八、安全要求

### 8.1. 认证失败处理

- 未提供Token：返回 401 状态码，错误信息 "认证凭证缺失"
- Token无效：返回 401 状态码，错误信息 "认证凭证无效"
- Token过期：返回 401 状态码，错误信息 "认证凭证已过期"

### 8.2. 用户权限验证

- 用户只能访问自己创建的任务
- 用户只能修改/删除自己的任务
- 所有涉及用户数据的操作都必须验证用户权限

### 8.3. 错误响应格式

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

## 九、最终交付

请根据以上所有要求和核心约束，特别是**在生成这些文件时，必须严格遵守以下原则：只应用前面指令中明确描述的增量添加和最小修改。对于指令中未提及的任何已有代码，必须保持其原始样貌，不得进行任何形式的重构、格式化调整或逻辑变更**，为我生成以下文件的完整实现：

1. `app/core/auth.py` - JWT认证模块（新文件）
2. `app/core/deps.py` - 依赖注入（修改现有文件）
3. `app/models/download.py` - 数据模型（修改现有文件）
4. `app/api/v1/endpoints/download.py` - API端点（修改现有文件）
5. `app/services/download_service.py` - 业务服务（修改现有文件）
6. `requirements.txt` - 依赖包（修改现有文件）

## 十、注意事项

1. **不要实现SSO登录功能**：媒体下载服务不需要实现SSO登录，只需要验证用户服务颁发的JWT Token
2. **保持现有功能不变**：所有现有的下载功能必须保持完整，只是增加认证层
3. **最小化修改**：只添加必要的认证代码，不重构现有业务逻辑
4. **用户数据隔离**：确保用户只能访问自己的数据
5. **错误处理**：保持现有的错误处理逻辑，只添加认证相关的错误处理
6. **日志记录**：在每个API端点中添加适当的日志记录，记录用户ID和操作结果
7. **响应格式**：保持现有的响应格式不变，只添加认证相关的错误响应
8. **数据库操作**：保持现有的数据库操作逻辑不变，只添加用户ID过滤和权限验证
```
