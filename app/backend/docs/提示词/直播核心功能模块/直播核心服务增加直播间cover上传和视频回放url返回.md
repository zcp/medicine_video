# 直播核心服务增加封面上传和回放地址功能的代码生成提示词

## 一、角色定义 (Role Definition)

你是一名资深的 Python 后端工程师，精通 FastAPI、SQLAlchemy 2.0 (异步模式)、文件上传处理和媒体资源管理。你擅长在现有代码库上进行**增量式开发**，能够根据详尽的设计文档、数据模型和代码上下文，精确地添加文件上传和媒体回放功能，同时最大限度地减少对现有稳定代码的改动。

## 二、任务目标 (Task Objective)

你的任务是为现有的直播核心服务添加两个新功能：

**功能一：直播间封面上传**
- 新增API端点，支持用户为自己创建的直播间上传/更新封面图片
- 实现文件类型、大小验证和存储管理
- 自动更新数据库中的 `cover_url` 字段

**功能二：视频回放地址返回**
- 修改现有的"获取场次详情"API，动态生成 `playback_url` 字段
- 仅在场次状态为 `ready` 且 `video_id` 存在时返回回放地址

**核心约束 (Primary Constraint):** 你的首要原则是**最小化对现有代码的修改**。当前代码库已经过测试并正常运行。你必须优先选择添加新函数、新方法和新类，而不是重构现有代码。只有在支持新功能绝对必要时，才允许进行微小的修改。

**重要提醒：** 你的任务**仅限**于添加封面上传和回放地址功能，**严禁**修改任何现有的业务逻辑、API响应格式（除了明确指定的新增字段）、错误处理逻辑或其他功能。

## 三、核心上下文信息 (Core Context Information)

### 3.1. 项目结构与待修改文件

你将要修改以下文件，请严格按照其在项目中的路径进行操作：
backend/live_core_service/
├── 📄 requirements.txt # Python 依赖包列表
├── 📄 .env # 环境变量配置
├── 📄 run.py # 服务启动入口文件
├── 📁 app/ # 主应用目录
│ ├── 📄 main.py # FastAPI 应用主文件
│ ├── 📁 api/ # API 路由层
│ │ └── 📁 v1/
│ │ └── 📁 endpoints/
│ │ ├── 📄 room.py # 房间管理 API 端点 ⚠️ 需修改
│ │ └── 📄 session.py # 场次管理 API 端点 ⚠️ 需修改
│ ├── 📁 core/ # 核心配置和工具
│ │ ├── 📄 config.py # 应用配置 ⚠️ 需修改
│ │ ├── 📄 responses.py # 响应处理工具
│ │ └── 📄 file_handler.py # 文件处理工具 🆕 需创建
│ ├── 📁 models/ # 数据模型层
│ │ └── 📄 live_core.py # 数据模型 (无需修改)
│ ├── 📁 schemas/ # 数据验证模式
│ │ └── 📄 live_core.py # 数据模式 (无需修改)
│ ├── 📁 crud/ # 数据操作层
│ │ └── 📄 room.py # 房间CRUD ⚠️ 需修改
│ └── 📁 services/ # 业务逻辑服务层
│ └── 📄 room_service.py # 房间服务 ⚠️ 需修改
├── 📁 media/ # 媒体文件存储目录
│ └── 📁 rooms/ # 直播间相关文件 🆕
└── 📁 tests/ # 测试目录




### 3.2. 需要修改的API接口列表

#### **新增API接口**
1. `POST /api/v1/rooms/{room_id}/cover` - 上传/更新直播间封面 🆕

#### **修改API接口（仅修改响应结构）**
1. `GET /api/v1/rooms` - 获取房间列表（响应中增加 `cover_url` 字段）
2. `GET /api/v1/rooms/{room_id}` - 获取房间详情（响应中增加 `cover_url` 字段）
3. `GET /api/v1/sessions/{session_id}` - 获取场次详情（响应中增加 `playback_url` 字段）

### 3.3. 环境变量配置

**在 `backend/live_core_service/.env` 文件中添加：**

```bash
# ===== 文件上传配置 =====
# 媒体文件存储根目录
MEDIA_ROOT_PATH=./media

# 封面上传配置
UPLOAD_MAX_SIZE=5242880                    # 最大文件大小 5MB (字节)
UPLOAD_ALLOWED_EXTENSIONS=jpg,jpeg,png,gif # 允许的文件扩展名（逗号分隔）

# ===== 视频回放配置 =====
# 回放地址Base URL（可以是CDN域名或本地路径）
PLAYBACK_BASE_URL=https://your-cdn-domain.com  # 生产环境使用CDN
# PLAYBACK_BASE_URL=http://localhost:8000       # 开发环境使用本地
```

**环境变量说明：**
- `MEDIA_ROOT_PATH`: 媒体文件在服务器上的存储根目录
- `UPLOAD_MAX_SIZE`: 上传文件的最大字节数
- `UPLOAD_ALLOWED_EXTENSIONS`: 允许上传的图片格式
- `PLAYBACK_BASE_URL`: 视频回放地址的基础URL，拼接存储路径后形成完整的回放地址

### 3.4. 依赖的现有文件

本次增量修改需要依赖以下文件：

**核心模型定义：**
- `app/models/live_core.py` - 包含 LiveRoom、LiveSession 模型定义（已包含 `cover_url` 和 `video_id` 字段）
- `app/schemas/live_core.py` - 包含对应的 Pydantic Schema 定义

**数据库操作：**
- `app/crud/room.py` - 包含所有房间管理相关的数据库操作方法

**业务逻辑：**
- `app/services/room_service.py` - 包含所有房间管理相关的业务逻辑方法
- `app/services/session_service.py` - 包含所有场次管理相关的业务逻辑方法

**API端点：**
- `app/api/v1/endpoints/room.py` - 包含所有房间管理相关的API端点实现
- `app/api/v1/endpoints/session.py` - 包含所有场次管理相关的API端点实现

**核心配置：**
- `app/core/responses.py` - 包含 success_response 和 error_response 函数

## 四、技术实现要求

### 4.1. 封面上传功能技术要求

#### 4.1.1. 文件验证规范

**文件类型验证：**
- 允许的MIME类型：`image/jpeg`, `image/png`, `image/gif`
- 允许的文件扩展名：`.jpg`, `.jpeg`, `.png`, `.gif`
- 验证方法：同时验证MIME类型和文件扩展名

**文件大小限制：**
- 最大文件大小：5MB (5,242,880 字节)
- 超出限制返回：`400 Bad Request`，错误信息"文件大小超出限制"

**文件安全性：**
- 使用UUID生成唯一文件名，避免文件名冲突
- 添加时间戳，防止浏览器缓存问题
- 移除原始文件名中的危险字符

#### 4.1.2. 存储路径规范

**存储路径结构：**

/media/rooms/{room_id}/cover_{timestamp}.{ext}

**路径组成说明：**
- `/media/rooms/`: 固定的存储根路径
- `{room_id}`: 直播间的UUID（格式：xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx）
- `cover_`: 固定前缀，标识文件类型
- `{timestamp}`: Unix时间戳（10位整数），防止缓存问题
- `.{ext}`: 原始文件的扩展名（jpg/jpeg/png/gif）

**示例路径：**
/media/rooms/a1b2c3d4-e5f6-7890-abcd-ef1234567890/cover_1710912345.jpg

**URL访问形式：**
http://localhost:8000/media/rooms/a1b2c3d4-e5f6-7890-abcd-ef1234567890/cover_1710912345.jpg


#### 4.1.3. 文件覆盖策略

**新上传文件处理：**
1. 检查 `live_rooms.cover_url` 字段是否已存在值
2. 如果存在旧封面文件，删除旧文件（物理删除）
3. 保存新文件到标准路径
4. 更新数据库 `cover_url` 字段为新文件路径

**旧文件清理：**
- 在保存新文件之前，先删除旧文件
- 使用 `os.path.exists()` 检查文件是否存在
- 使用 `os.remove()` 删除旧文件
- 删除失败时记录警告日志，但不中断上传流程

### 4.2. 视频回放地址生成规范

#### 4.2.1. URL生成条件

**必须同时满足以下条件：**
1. 场次状态 (`status`) 必须为 `'ready'`
2. 视频ID (`video_id`) 不能为 `NULL`

**不满足条件时：**
- `playback_url` 字段返回 `null`

#### 4.2.2. URL生成规则

**URL格式：**
{PLAYBACK_BASE_URL}/media/videos/{video_id}/playlist.m3u8

**URL组成说明：**
- `{PLAYBACK_BASE_URL}`: 从环境变量读取的基础URL
- `/media/videos/`: 固定的视频存储路径
- `{video_id}`: 场次对应的视频UUID
- `/playlist.m3u8`: 固定的HLS播放列表文件名

**示例URL：**
https://your-cdn-domain.com/media/videos/f9e8d7c6-b5a4-3210-fedc-ba9876543210/playlist.m3u8


#### 4.2.3. 动态生成逻辑

**实现位置：**
- 在 `GET /api/v1/sessions/{session_id}` 端点的响应构建阶段
- 不在数据库存储 `playback_url`，而是动态生成

**生成流程：**
```python
playback_url = None
if session.status == LiveSessionStatus.READY and session.video_id:
    playback_url = f"{PLAYBACK_BASE_URL}/media/videos/{session.video_id}/playlist.m3u8"
```

## 五、通用规范与 API 定义

### 5.1. 权威设计文档
**所有实现细节必须严格遵循【直播核心功能设计文档v3-在增加jwt token和sso基础上增加直播间封面上传和返回回放地址】。**

### 5.2. 日志记录规范
**在每个端点函数的入口处，应使用 logger.info() 记录请求的开始。在成功完成操作后，也应记录成功的消息。在 return JSONResponse 之前，应使用 logger.warning() 记录下具体的业务错误原因。**

### 5.3. 代码规范
* 遵循 `rules.md` 中定义的团队代码规范。
* **开发语言**: 使用 Python 3.8 或更高版本。
* **代码风格**: 严格遵循 PEP 8 规范。
* **异步模式**: 所有API端点必须使用 `async def` 函数，文件I/O操作使用异步库或在线程池中执行。

### 5.4. 命名规范
* **类名 (Class)**: 使用大驼峰命名法 (PascalCase)，例如 `FileHandler`。
* **函数与方法 (Function/Method)**: 使用下划线命名法 (snake_case)，例如 `upload_cover`。
* **变量 (Variable)**: 使用下划线命名法 (snake_case)，例如 `cover_url`。
* **常量 (Constant)**: 使用全大写下划线命名法 (UPPER_SNAKE_CASE)，例如 `UPLOAD_MAX_SIZE`。

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
  return success_response(data=room_data)
  ```

### ❌ 错误响应

- 所有业务错误必须返回 `fastapi.responses.JSONResponse`，其 `content` 由 `error_response(...)` 构建。
- 示例：
  ```python
  return JSONResponse(
      status_code=400,
      content=error_response(code=2001, message='文件类型不允许')
  )
  ```

> 假设 `success_response()` 和 `error_response()` 已定义在 `app/core/responses.py` 中。

### 5.6. 异步编程规范

* **函数定义**: 所有API端点函数必须使用 `async def` 定义
* **文件操作**: 文件I/O操作建议使用 `aiofiles` 库或在 `asyncio` 线程池中执行
* **依赖注入**: 使用 `Depends()` 进行异步依赖注入
* **错误处理**: 异步函数中的异常处理必须使用 `try...except` 块

## 六、日志与异常处理规范

### 6.1. 日志规范

#### 6.1.1. 日志级别
* `ERROR`: 文件系统错误、数据库错误等关键问题
* `WARNING`: 文件格式不符合要求、旧文件删除失败等警告
* `INFO`: 文件上传开始、上传成功、封面更新等重要操作节点
* `DEBUG`: 文件路径、文件大小等详细调试信息

#### 6.1.2. 日志内容示例
应记录但不限于以下关键信息：
* 文件上传操作的开始和结束
* 文件验证结果（类型、大小）
* 文件保存路径
* 数据库更新结果
* 所有捕获到的异常信息

**示例日志：**
```python
logger.info(f"开始上传封面: room_id={room_id}, user_id={current_user['user_id']}")
logger.info(f"文件验证通过: filename={file.filename}, size={file.size}")
logger.info(f"封面保存成功: path={file_path}")
logger.info(f"数据库更新成功: room_id={room_id}, cover_url={cover_url}")
```

### 6.2. 异常处理规范

#### 6.2.1. 文件上传相关异常

* **文件类型错误**: 返回 `400 Bad Request`，错误码 `2001`，消息"不支持的文件类型"
* **文件大小超限**: 返回 `400 Bad Request`，错误码 `2002`，消息"文件大小超出限制"
* **文件保存失败**: 返回 `500 Internal Server Error`，错误码 `5001`，消息"文件保存失败"
* **权限不足**: 返回 `403 Forbidden`，错误码 `2003`，消息"无权修改此房间"

#### 6.2.2. 异常处理原则
* **统一格式**: 所有错误响应都必须使用 `error_response()` 函数构建
* **详细日志**: 捕获异常时，记录完整的错误堆栈到日志
* **用户友好**: 返回给客户端的错误信息应清晰、易懂，但不暴露敏感信息
* **资源清理**: 文件操作失败时，确保临时文件被清理

## 七、具体代码修改指令

### 7.1. 第一部分：创建文件处理工具模块

**文件**: `app/core/file_handler.py` 🆕

**任务**: 创建文件验证、保存和管理的工具类。

**执行流程**:
1. 创建新文件 `app/core/file_handler.py`
2. 在文件顶部导入必要的模块：
   ```python
   import os
   import uuid
   import time
   import logging
   from pathlib import Path
   from typing import Optional, Tuple
   from fastapi import UploadFile, HTTPException
   ```
3. 创建 `logger` 实例：`logger = logging.getLogger(__name__)`
4. 从环境变量读取配置：
   ```python
   MEDIA_ROOT_PATH = os.getenv("MEDIA_ROOT_PATH", "./media")
   UPLOAD_MAX_SIZE = int(os.getenv("UPLOAD_MAX_SIZE", "5242880"))
   UPLOAD_ALLOWED_EXTENSIONS = os.getenv("UPLOAD_ALLOWED_EXTENSIONS", "jpg,jpeg,png,gif").split(",")
   ```
5. 实现 `FileHandler` 类，包含以下静态方法：
   - `validate_image_file(file: UploadFile) -> bool`: 验证文件类型和大小
   - `generate_cover_path(room_id: uuid.UUID, extension: str) -> Tuple[str, str]`: 生成封面存储路径
   - `save_cover_file(file: UploadFile, room_id: uuid.UUID) -> str`: 保存封面文件并返回URL
   - `delete_old_cover(cover_url: str) -> None`: 删除旧的封面文件

**方法实现要求：**

#### **`validate_image_file` 方法**
- 检查文件扩展名是否在允许列表中
- 检查文件MIME类型是否为 `image/*`
- 检查文件大小是否超过限制
- 验证失败时抛出 `HTTPException`

#### **`generate_cover_path` 方法**
- 生成符合规范的文件路径：`/media/rooms/{room_id}/cover_{timestamp}.{ext}`
- 返回两个值：文件系统路径和URL路径
- 确保目录存在，不存在则创建

#### **`save_cover_file` 方法**
- 调用 `validate_image_file` 验证文件
- 调用 `generate_cover_path` 生成路径
- 保存文件到目标路径
- 返回URL路径（用于存入数据库）

#### **`delete_old_cover` 方法**
- 检查文件是否存在
- 如果存在，删除文件
- 删除失败时记录警告日志，但不抛出异常

### 7.2. 第二部分：修改应用配置

**文件**: `app/core/config.py`

**任务**: 添加文件上传和回放地址相关的配置。

**执行流程**:
1. 在配置类中添加新的配置项：
   ```python
   # 文件上传配置
   MEDIA_ROOT_PATH: str = os.getenv("MEDIA_ROOT_PATH", "./media")
   UPLOAD_MAX_SIZE: int = int(os.getenv("UPLOAD_MAX_SIZE", "5242880"))
   UPLOAD_ALLOWED_EXTENSIONS: str = os.getenv("UPLOAD_ALLOWED_EXTENSIONS", "jpg,jpeg,png,gif")
   
   # 视频回放配置
   PLAYBACK_BASE_URL: str = os.getenv("PLAYBACK_BASE_URL", "http://localhost:8000")
   ```
2. 保持现有配置项和结构不变
3. 确保新配置项在类定义的末尾添加

### 7.3. 第三部分：修改CRUD层

**文件**: `app/crud/room.py`

**任务**: 添加更新房间封面URL的方法。

**执行流程**:
1. 在文件末尾添加新方法（在现有方法之后）：
   ```python
   async def update_cover_url(
       db: AsyncSession, 
       room_id: uuid.UUID, 
       cover_url: str
   ) -> Optional[LiveRoom]:
       """
       更新房间封面URL
       
       Args:
           db: 数据库会话
           room_id: 房间ID
           cover_url: 新的封面URL
           
       Returns:
           更新后的LiveRoom对象或None
       """
       # 实现逻辑：
       # 1. 查询房间对象
       # 2. 更新 cover_url 字段
       # 3. 提交事务
       # 4. 刷新对象并返回
   ```
2. 保持现有方法完全不变
3. 确保新方法使用 `async def` 和 `await`

### 7.4. 第四部分：修改Service层

**文件**: `app/services/room_service.py`

**任务**: 添加封面上传的业务逻辑方法。

**执行流程**:
1. 在 `RoomService` 类中添加新方法（在现有方法之后）：
   ```python
   async def upload_room_cover(
       self, 
       room_id: uuid.UUID, 
       file: UploadFile,
       user_id: uuid.UUID
   ) -> LiveRoom:
       """
       为指定房间上传封面图片
       
       Args:
           room_id: 房间ID
           file: 上传的文件对象
           user_id: 当前用户ID
           
       Returns:
           更新后的LiveRoom对象
           
       Raises:
           RoomNotFoundException: 房间不存在
           ActionForbiddenException: 用户无权修改此房间
       """
       # 实现逻辑：
        # 1. 记录日志：logger.info(f"开始上传封面: room_id={room_id}, user_id={user_id}")
        # 2. 验证房间存在性和用户权限
        # 3. 如果房间已有封面，删除旧文件
        # 4. 保存新文件
        # 5. 更新数据库 cover_url
        # 6. 记录日志：logger.info(f"封面上传成功: room_id={room_id}, cover_url={cover_url}")
        # 7. 返回更新后的房间对象
   ```
2. 在方法中调用 `FileHandler` 的相关方法
3. 保持现有方法完全不变

### 7.5. 第五部分：修改API端点层 - 房间管理

**文件**: `app/api/v1/endpoints/room.py`

**任务**: 添加封面上传端点，并在现有端点响应中添加 `cover_url` 字段。

#### **7.5.1. 新增封面上传端点**

**执行流程**:
1. 在文件顶部添加新的导入：
   ```python
   from fastapi import File, UploadFile
   from app.core.file_handler import FileHandler
   ```
2. 在文件末尾（在现有路由之后）添加新的路由：
   ```python
   @router.post("/{room_id}/cover", response_model=Dict[str, Any])
   async def upload_room_cover(
       room_id: uuid.UUID,
       file: UploadFile = File(...),
       current_user: dict = Depends(get_current_user),
       db: AsyncSession = Depends(get_db)
   ) -> Dict[str, Any]:
       """为指定房间上传封面图片"""
       logger.info(f"开始上传封面: room_id={room_id}, user_id={current_user['user_id']}")
       
       # 实例化服务层
       service = RoomService(db=db)
       
       try:
           # 调用服务层上传封面
           updated_room = await service.upload_room_cover(
               room_id=room_id,
               file=file,
               user_id=current_user["user_id"]
           )
           
           logger.info(f"封面上传成功: room_id={room_id}")
           
           # 构建响应数据
           response_data = {
               "room_id": str(updated_room.id),
               "cover_url": updated_room.cover_url
           }
           
           return success_response(data=response_data)
           
       except RoomNotFoundException:
           logger.warning(f"房间不存在: room_id={room_id}")
           return JSONResponse(
               status_code=404,
               content=error_response(
                   code=2001,
                   message="资源不存在",
                   data={"resource": "Room", "id": str(room_id)}
               )
           )
       except ActionForbiddenException as e:
           logger.warning(f"无权上传封面: room_id={room_id}, user_id={current_user['user_id']}")
           return JSONResponse(
               status_code=403,
               content=error_response(
                   code=2003,
                   message="业务逻辑错误",
                   data={"error": str(e)}
               )
           )
       except HTTPException as e:
           logger.warning(f"文件验证失败: {e.detail}")
           return JSONResponse(
               status_code=e.status_code,
               content=error_response(
                   code=2001,
                   message="文件验证失败",
                   data={"error": e.detail}
               )
           )
       except Exception as e:
           logger.error(f"封面上传失败: {str(e)}", exc_info=True)
           return JSONResponse(
               status_code=500,
               content=error_response(
                   code=5001,
                   message="文件上传失败",
                   data={"error": "服务器内部错误"}
               )
           )
   ```

#### **7.5.2. 修改现有端点响应**

**`GET /api/v1/rooms` (获取房间列表) - 最小修改**

**执行流程**:
1. 定位到 `get_rooms` 函数中构建响应数据的部分（循环构建 `items` 的代码块）
2. 在现有的 `item` 字典中**仅添加一个新字段**：
   ```python
   # 找到类似以下的代码块：
   for room in rooms:
       item = {
           "id": str(room.id),
           "title": room.title,
           "cover_url": room.cover_url,  # 🆕 仅添加此行
           "created_at": room.created_at.isoformat() + "Z"
       }
       items.append(item)
   ```
3. **保持其他代码完全不变**

**`GET /api/v1/rooms/{room_id}` (获取房间详情) - 最小修改**

**执行流程**:
1. 定位到 `get_room` 函数中构建 `response_data` 字典的部分
2. 在现有字典中**仅添加一个新字段**：
   ```python
   # 找到类似以下的代码块：
   response_data = {
       "id": str(room.id),
       "title": room.title,
       "description": room.description,
       "cover_url": room.cover_url,  # 🆕 仅添加此行
       "stream_key": room.stream_key,
       "is_private": room.is_private,
       "record_by_default": room.record_by_default,
       "created_at": room.created_at.isoformat() + "Z"
   }
   ```
3. **保持其他代码完全不变**

### 7.6. 第六部分：修改API端点层 - 场次管理

**文件**: `app/api/v1/endpoints/session.py`

**任务**: 在获取场次详情端点的响应中添加 `playback_url` 字段。

**`GET /api/v1/sessions/{session_id}` (获取场次详情) - 最小修改**

**执行流程**:
1. 在文件顶部添加新的导入：
   ```python
   import os
   ```
2. 在文件顶部（logger定义之后，所有函数定义之前）添加环境变量读取：
   ```python
   # 读取回放Base URL配置（模块级常量，避免重复读取）
   PLAYBACK_BASE_URL = os.getenv("PLAYBACK_BASE_URL", "http://localhost:8000")
   ```
3. 定位到 `get_session_details` 函数中直接使用 `PLAYBACK_BASE_URL` 常量，构建 `response_data` 字典的部分
4. 在现有字典中**仅添加一个新字段**，并在字典末尾添加动态生成逻辑：
   ```python
   # 找到类似以下的代码块：
   response_data = {
       "id": str(session.id),
       "room_id": str(session.room_id),
       "status": session.status.value,
       "start_time": session.start_time.isoformat() + "Z",
       "end_time": session.end_time.isoformat() + "Z" if session.end_time else None,
       "video_id": str(session.video_id) if session.video_id else None,
       "created_at": session.created_at.isoformat() + "Z",
       "updated_at": session.updated_at.isoformat() + "Z",
       "statistics": None  # 如果存在统计信息，会在后续代码中更新
   }
   
   # 🆕 在添加统计信息的代码块之后，添加以下代码：
   # 动态生成回放地址
   playback_url = None
   if session.status.value == "ready" and session.video_id:
       playback_url = f"{PLAYBACK_BASE_URL}/media/videos/{session.video_id}/playlist.m3u8"
       logger.debug(f"生成回放地址: session_id={session_id}, playback_url={playback_url}")
   
   response_data["playback_url"] = playback_url
   ```
5. **保持其他代码完全不变**
6. **注意**：动态生成逻辑应在构建完整的 `response_data` 之后、返回响应之前执行

### 7.7. 第七部分：更新依赖包

**文件**: `requirements.txt`

**任务**: 添加文件处理相关的依赖包。

**执行流程**:
1. 在文件末尾添加以下依赖（如果尚未安装）：
   ```
   # 文件上传和处理
   python-multipart>=0.0.6  # FastAPI 文件上传支持
   aiofiles>=23.2.1         # 异步文件I/O（可选，建议使用）
   Pillow>=10.0.0           # 图片处理（可选，用于验证和优化）
   ```
2. 保持现有依赖包版本不变
3. 确保新增依赖不与现有依赖冲突

### 7.8. 第八部分：配置静态文件服务

**文件**: `app/main.py`

**任务**: 配置FastAPI静态文件路由，使上传的文件可以通过HTTP访问。

**执行流程**:
1. 在文件顶部添加导入：
   ```python
   from fastapi.staticfiles import StaticFiles
   import os
   ```
2. 在创建 `app` 实例之后，路由注册之前，添加静态文件挂载：
   ```python
   # 配置媒体文件静态访问
   MEDIA_ROOT_PATH = os.getenv("MEDIA_ROOT_PATH", "./media")
   
   # 确保media目录存在
   os.makedirs(MEDIA_ROOT_PATH, exist_ok=True)
   
   # 挂载静态文件目录
   app.mount("/media", StaticFiles(directory=MEDIA_ROOT_PATH), name="media")
   ```
3. 保持现有代码完全不变

## 八、架构设计原则

### 8.1. 文件管理架构

**设计原则：**
- **统一管理**: 所有文件操作集中在 `FileHandler` 工具类中
- **路径规范**: 严格遵循 `/media/rooms/{room_id}/cover_{timestamp}.{ext}` 格式
- **安全性**: 验证文件类型、大小，防止恶意文件上传
- **清理机制**: 更新封面时自动删除旧文件，避免磁盘空间浪费

**实现策略：**
1. **API层**: 接收文件上传请求，验证JWT权限
2. **Service层**: 执行业务逻辑，调用CRUD层更新数据库
3. **FileHandler**: 处理文件验证、保存、删除等文件系统操作
4. **CRUD层**: 更新数据库中的 `cover_url` 字段

### 8.2. 动态URL生成架构

**设计原则：**
- **实时生成**: 不在数据库存储 `playback_url`，而是根据场次状态动态生成
- **灵活配置**: 通过环境变量配置 `PLAYBACK_BASE_URL`，支持开发/生产环境切换
- **条件判断**: 只有满足条件（status=ready且video_id存在）才生成URL
- **无状态**: 生成逻辑完全基于现有数据，不依赖外部状态

**实现策略：**
1. **配置层**: 从环境变量读取 `PLAYBACK_BASE_URL`
2. **API层**: 在构建响应时，检查场次状态和video_id
3. **URL拼接**: 按照规范格式拼接完整的回放地址
4. **返回响应**: 将生成的URL作为响应字段返回给客户端

## 九、安全要求

### 9.1. 文件上传安全

**类型验证：**
- 同时验证文件扩展名和MIME类型
- 拒绝可执行文件（.exe, .sh, .bat等）
- 只允许图片格式（jpg, jpeg, png, gif）

**大小限制：**
- 强制执行5MB文件大小限制
- 超出限制立即返回错误，不进行处理

**路径安全：**
- 使用UUID生成文件名，避免路径遍历攻击
- 限制文件只能保存在 `/media/rooms/` 目录下
- 不接受用户提供的文件名作为保存路径

**权限控制：**
- 用户只能为自己创建的房间上传封面
- 在Service层进行权限验证
- 验证失败返回 `403 Forbidden`

### 9.2. 回放地址安全

**URL生成安全：**
- 不暴露服务器文件系统路径
- 使用环境变量配置Base URL，避免硬编码
- 生成的URL不包含敏感信息

**访问控制：**
- 回放地址仅在场次状态为 `ready` 时生成
- 未就绪的场次不提供回放地址
- 支持后续集成CDN加速和访问控制

### 9.3. 错误响应格式

**文件上传错误响应：**
```json
{
  "code": 2001,
  "message": "文件验证失败",
  "data": {
    "error": "不支持的文件类型"
  },
  "timestamp": "2024-03-20T10:00:00Z"
}
```

**权限不足错误响应：**
```json
{
  "code": 2003,
  "message": "业务逻辑错误",
  "data": {
    "error": "无权修改此房间"
  },
  "timestamp": "2024-03-20T10:00:00Z"
}
```

## 十、Nginx配置建议（附录）

为支持文件上传功能，需要在Nginx配置中调整上传大小限制：

**配置文件**: `nginx.conf` 或站点配置文件

**添加配置：**
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # 设置客户端请求体最大大小（支持5MB文件上传）
    client_max_body_size 10M;  # 设置稍大于应用限制，避免边界问题
    
    # 设置超时时间
    client_body_timeout 60s;
    
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # 文件上传相关配置
        proxy_request_buffering off;  # 禁用请求缓冲，减少内存占用
        proxy_http_version 1.1;
    }
    
    location /media/ {
        alias /path/to/media/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

## 十一、最终交付

请根据以上所有要求和核心约束，特别是**在生成这些文件时，必须严格遵守以下原则：只应用前面指令中明确描述的增量添加和最小修改。对于指令中未提及的任何已有代码，必须保持其原始样貌，不得进行任何形式的重构、格式化调整或逻辑变更**，为我生成以下文件的完整实现：

### 新增文件：
1. `app/core/file_handler.py` - 文件处理工具类（新文件）

### 修改文件：
2. `app/core/config.py` - 应用配置（添加文件上传和回放地址配置）
3. `app/main.py` - FastAPI应用主文件（添加静态文件挂载）
4. `app/crud/room.py` - 房间CRUD操作（添加 `update_cover_url` 方法）
5. `app/services/room_service.py` - 房间业务服务（添加 `upload_room_cover` 方法）
6. `app/api/v1/endpoints/room.py` - 房间API端点（添加封面上传端点，修改响应字段）
7. `app/api/v1/endpoints/session.py` - 场次API端点（修改响应字段，添加回放地址生成逻辑）
8. `requirements.txt` - 依赖包（添加文件处理相关依赖）
9. `.env` - 环境变量配置文件（添加新的配置项）

## 十二、注意事项

1. **最小化修改原则**：
   - 只在必要位置添加新字段
   - 不重构现有代码结构
   - 保持现有命名和格式风格

2. **文件管理注意事项**：
   - 确保 `/media/rooms/` 目录有正确的读写权限
   - 上传失败时清理临时文件
   - 定期清理无关联的孤立文件

3. **回放地址生成注意事项**：
   - 只修改响应构建部分，不改变业务逻辑
   - URL生成逻辑简单清晰，易于维护
   - 支持后续扩展（如CDN集成、Token签名等）

4. **测试建议**：
   - 测试不同文件类型的上传（正常和异常情况）
   - 测试文件大小限制
   - 测试权限控制（用户只能修改自己的房间）
   - 测试回放地址在不同场次状态下的返回值

5. **部署注意事项**：
   - 确保生产环境配置正确的 `PLAYBACK_BASE_URL`（CDN域名）
   - 配置Nginx的 `client_max_body_size`
   - 确保媒体文件目录有足够的磁盘空间
   - 建议配置CDN加速媒体文件访问

6. **错误处理**：
   - 所有文件操作都包含完整的异常处理
   - 记录详细的错误日志便于排查问题
   - 返回用户友好的错误信息

7. **性能优化**：
   - 使用 `aiofiles` 进行异步文件I/O
   - 大文件上传时考虑分块处理
   - 静态文件配置适当的缓存策略

8. **保持一致性**：
   - 新增代码的风格必须与现有代码完全一致
   - 使用相同的日志记录模式
   - 使用相同的错误处理模式
   - 使用相同的响应构建方式

