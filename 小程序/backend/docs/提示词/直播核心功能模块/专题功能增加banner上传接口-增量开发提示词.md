# 专题功能增加banner上传接口的增量代码生成提示词

## 一、角色定义 (Role Definition)

你是一名资深的 Python 后端工程师，精通 FastAPI、SQLAlchemy 2.0 (异步模式)、文件上传处理和媒体资源管理。你擅长在现有代码库上进行**增量式开发**，能够根据详尽的设计文档和代码上下文，精确地添加文件上传功能，同时最大限度地减少对现有稳定代码的改动。

## 二、任务目标 (Task Objective)

你的任务是为现有的专题聚合功能添加**专题横幅上传**功能：

**功能描述：**
- 新增API端点，支持用户为自己创建的专题上传/更新横幅图片
- 实现文件类型、大小验证和存储管理
- 自动更新数据库中的 `banner_url` 字段
- 修改专题创建和更新接口，使 `banner_url` 字段通过专门的上传接口设置

**核心约束 (Primary Constraint):** 你的首要原则是**最小化对现有代码的修改**。当前专题功能的代码库已经过测试并正常运行。你必须优先选择添加新函数、新方法，而不是重构现有代码。只有在支持新功能绝对必要时，才允许进行微小的修改。

**重要提醒：** 你的任务**仅限**于添加横幅上传功能和调整 Schema 定义，**严禁**修改任何现有的业务逻辑、已有API端点的核心逻辑、错误处理逻辑或其他功能。

**架构复用原则：** 本功能应**完全复用**直播间封面上传（`upload_room_cover`）的实现逻辑，只需调整：
- 存储路径：从 `/media/rooms/` 改为 `/media/topics/`
- 文件前缀：从 `cover_` 改为 `banner_`
- 数据库字段：从 `room.cover_url` 改为 `topic.banner_url`

## 三、核心上下文信息 (Core Context Information)

### 3.1. 项目结构与待修改文件

你将要修改以下文件，请严格按照其在项目中的路径进行操作：

```
backend/live_core_service/
├── app/
│   ├── schemas/
│   │   └── topic.py              # ⚠️ 需修改 - 调整Schema定义
│   ├── crud/
│   │   └── topic.py              # ⚠️ 需修改 - 添加 update_banner_url 方法
│   ├── services/
│   │   └── topic_service.py      # ⚠️ 需修改 - 添加 upload_topic_banner 方法
│   ├── api/v1/endpoints/
│   │   └── topic.py              # ⚠️ 需修改 - 添加横幅上传端点
│   └── core/
│       └── file_handler.py       # 🔍 已存在 - 复用文件处理工具
```

### 3.2. 需要修改的接口和Schema

#### **Schema调整（非破坏性修改）**
1. `TopicBase` - 移除 `banner_url` 字段
2. `TopicCreate` - 添加注释说明 `banner_url` 默认为 NULL
3. `TopicUpdate` - 移除 `banner_url` 字段，添加注释说明通过专门接口更新
4. `TopicInDB` - 显式添加 `banner_url: Optional[str] = None` 字段

#### **新增API接口**
1. `POST /api/v1/topics/{topic_id}/banner` - 上传/更新专题横幅 🆕

#### **不修改的接口**
- `POST /api/v1/topics` - 创建专题（行为保持不变，`banner_url` 默认为 NULL）
- `GET /api/v1/topics` - 获取专题列表（响应中 `banner_url` 可能为 null）
- `GET /api/v1/topics/{topic_id}` - 获取专题详情（响应中 `banner_url` 可能为 null）
- `PATCH /api/v1/topics/{topic_id}` - 更新专题（不再接受 `banner_url` 字段）

### 3.3. 依赖的现有代码

**假设以下代码已存在且可用：**

#### `app/core/file_handler.py` - 文件处理工具类（已存在）

**现有方法（已实现，可直接使用）：**

```python
# 环境变量配置
ROOM_MEDIA_ROOT_PATH = os.getenv("ROOM_MEDIA_ROOT_PATH", "./media")
UPLOAD_MAX_SIZE = int(os.getenv("UPLOAD_MAX_SIZE", "5242880"))
UPLOAD_ALLOWED_EXTENSIONS = os.getenv("UPLOAD_ALLOWED_EXTENSIONS", "jpg,jpeg,png,gif").split(",")
ALLOWED_MIME_TYPES = ["image/jpeg", "image/png", "image/gif"]

class FileHandler:
    """文件上传处理工具类"""
    
    @staticmethod
    def validate_image_file(file: UploadFile) -> bool:
        """
        验证文件类型和大小
        
        Args:
            file: 上传的文件对象
            
        Returns:
            验证通过返回True
            
        Raises:
            HTTPException: 验证失败时抛出异常
        """
        # 检查文件扩展名
        if file.filename:
            file_ext = file.filename.rsplit(".", 1)[-1].lower()
            if file_ext not in UPLOAD_ALLOWED_EXTENSIONS:
                raise HTTPException(status_code=400, detail=f"不支持的文件类型...")
        
        # 检查MIME类型
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(status_code=400, detail=f"不支持的MIME类型...")
        
        return True
    
    @staticmethod
    def generate_cover_path(room_id: uuid.UUID, extension: str) -> Tuple[str, str]:
        """
        生成封面存储路径
        
        Args:
            room_id: 房间ID
            extension: 文件扩展名
            
        Returns:
            (文件系统路径, URL路径)的元组
        """
        timestamp = int(time.time())
        relative_dir = f"rooms/{room_id}"
        filename = f"cover_{timestamp}.{extension}"
        
        fs_dir = os.path.join(ROOM_MEDIA_ROOT_PATH, relative_dir)
        fs_path = os.path.join(fs_dir, filename)
        url_path = f"/media/{relative_dir}/{filename}"
        
        os.makedirs(fs_dir, exist_ok=True)
        return fs_path, url_path
    
    @staticmethod
    async def save_cover_file(file: UploadFile, room_id: uuid.UUID) -> str:
        """
        保存封面文件并返回URL
        
        Returns:
            str: 封面URL路径
        """
        FileHandler.validate_image_file(file)
        file_ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename else "jpg"
        fs_path, url_path = FileHandler.generate_cover_path(room_id, file_ext)
        
        # 读取文件内容并检查大小
        contents = await file.read()
        if len(contents) > UPLOAD_MAX_SIZE:
            raise HTTPException(status_code=400, detail="文件大小超出限制...")
        
        # 同步保存文件
        with open(fs_path, "wb") as f:
            f.write(contents)
        
        return url_path
    
    @staticmethod
    def delete_old_cover(cover_url: str) -> None:
        """
        删除旧的封面文件
        
        Args:
            cover_url: 封面URL路径
        """
        if not cover_url:
            return
        
        try:
            # URL格式: /media/rooms/{room_id}/cover_{timestamp}.{ext}
            relative_path = cover_url.replace("/media/", "")
            fs_path = os.path.join(ROOM_MEDIA_ROOT_PATH, relative_path)
            
            if os.path.exists(fs_path):
                os.remove(fs_path)
            
        except Exception as e:
            logger.warning(f"删除旧封面文件失败: cover_url={cover_url}, error={str(e)}")
```

**需要新增的方法（用于专题横幅）：**

```python
    @staticmethod
    def generate_banner_path(topic_id: uuid.UUID, extension: str) -> Tuple[str, str]:
        """
        生成横幅存储路径（新增方法，需要添加）
        
        完全复用 generate_cover_path 的逻辑，只调整路径。
        
        Args:
            topic_id: 专题ID
            extension: 文件扩展名
            
        Returns:
            (文件系统路径, URL路径)的元组
        """
        timestamp = int(time.time())
        relative_dir = f"topics/{topic_id}"  # 改为 topics
        filename = f"banner_{timestamp}.{extension}"  # 改为 banner
        
        fs_dir = os.path.join(ROOM_MEDIA_ROOT_PATH, relative_dir)
        fs_path = os.path.join(fs_dir, filename)
        url_path = f"/media/{relative_dir}/{filename}"
        
        os.makedirs(fs_dir, exist_ok=True)
        return fs_path, url_path
    
    @staticmethod
    async def save_banner_file(file: UploadFile, topic_id: uuid.UUID) -> str:
        """
        保存专题横幅文件（新增方法，需要添加）
        
        完全复用 save_cover_file 的逻辑，只调整路径。
        
        Args:
            file: 上传的文件对象
            topic_id: 专题UUID
            
        Returns:
            str: 横幅URL路径 (/media/topics/{topic_id}/banner_{timestamp}.{ext})
            
        Raises:
            HTTPException: 文件验证失败或保存失败
        """
        FileHandler.validate_image_file(file)
        file_ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename else "jpg"
        fs_path, url_path = FileHandler.generate_banner_path(topic_id, file_ext)
        
        # 读取文件内容并检查大小
        contents = await file.read()
        if len(contents) > UPLOAD_MAX_SIZE:
            raise HTTPException(status_code=400, detail="文件大小超出限制...")
        
        # 同步保存文件
        with open(fs_path, "wb") as f:
            f.write(contents)
        
        return url_path
    
    @staticmethod
    def delete_old_banner(banner_url: str) -> None:
        """
        删除旧的专题横幅文件（新增方法，需要添加）
        
        完全复用 delete_old_cover 的逻辑，只调整路径。
        
        Args:
            banner_url: 横幅URL路径
        """
        if not banner_url:
            return
        
        try:
            # URL格式: /media/topics/{topic_id}/banner_{timestamp}.{ext}
            relative_path = banner_url.replace("/media/", "")
            fs_path = os.path.join(ROOM_MEDIA_ROOT_PATH, relative_path)
            
            if os.path.exists(fs_path):
                os.remove(fs_path)
            
        except Exception as e:
            logger.warning(f"删除旧横幅文件失败: banner_url={banner_url}, error={str(e)}")
```

#### `app/services/room_service.py` - 参考实现

```python
class RoomService:
    async def upload_room_cover(
        self, 
        room_id: uuid.UUID, 
        file: UploadFile,
        user_id: uuid.UUID
    ) -> LiveRoom:
        """
        为指定房间上传封面图片
        
        这是横幅上传的参考实现，需要复用此逻辑。
        """
        logger.info(f"开始上传封面: room_id={room_id}, user_id={user_id}")
        
        try:
            # 1. 验证房间存在性和用户权限
            room = await self.get_room_details(room_id=room_id, user_id=user_id)
            
            # 2. 如果房间已有封面，删除旧文件
            if room.cover_url:
                FileHandler.delete_old_cover(room.cover_url)
            
            # 3. 保存新文件
            cover_url = await FileHandler.save_cover_file(file=file, room_id=room_id)
            
            # 4. 更新数据库 cover_url
            updated_room = await crud_room.update_cover_url(
                db=self.db, 
                room_id=room_id, 
                cover_url=cover_url
            )
            
            logger.info(f"封面上传成功: room_id={room_id}, cover_url={cover_url}")
            return updated_room
            
        except (RoomNotFoundException, ActionForbiddenException):
            raise
        except Exception as e:
            logger.error(f"上传房间封面失败: room_id={room_id}, error={str(e)}")
            raise
```

## 四、技术实现要求

### 4.1. 横幅上传功能技术要求

#### 4.1.1. 文件验证规范（复用直播间封面规范）

**文件类型验证：**
- 允许的MIME类型：`image/jpeg`, `image/png`
- 允许的文件扩展名：`.jpg`, `.jpeg`, `.png`
- 验证方法：调用 `FileHandler.validate_image_file()`

**文件大小限制：**
- 最大文件大小：10MB (10,485,760 字节)
- 超出限制返回：`400 Bad Request`，错误信息"文件大小超出限制"

**文件安全性：**
- 使用UUID和时间戳生成唯一文件名
- 由 `FileHandler` 统一处理

#### 4.1.2. 存储路径规范

**存储路径结构：**
```
/media/topics/{topic_id}/banner_{timestamp}.{ext}
```

**路径组成说明：**
- `/media/topics/`: 固定的存储根路径
- `{topic_id}`: 专题的UUID（格式：xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx）
- `banner_`: 固定前缀，标识文件类型
- `{timestamp}`: Unix时间戳（10位整数），防止缓存问题
- `.{ext}`: 原始文件的扩展名（jpg/jpeg/png）

**示例路径：**
```
/media/topics/a1b2c3d4-e5f6-7890-abcd-ef1234567890/banner_1729500605.jpg
```

**URL访问形式：**
```
http://localhost:8000/media/topics/a1b2c3d4-e5f6-7890-abcd-ef1234567890/banner_1729500605.jpg
```

#### 4.1.3. 文件覆盖策略（与直播间封面一致）

**新上传文件处理：**
1. 检查 `topics.banner_url` 字段是否已存在值
2. 如果存在旧横幅文件，删除旧文件（物理删除）
3. 保存新文件到标准路径
4. 更新数据库 `banner_url` 字段为新文件路径

**旧文件清理：**
- 在保存新文件之前，先删除旧文件
- 使用 `FileHandler.delete_old_banner()` 方法
- 删除失败时记录警告日志，但不中断上传流程

## 五、通用规范与 API 定义

### 5.1. 权威设计文档

**所有实现细节必须严格遵循以下文档：**
1. 【专题功能完整设计文档-修正版】 - 横幅上传接口定义（第526-580行）
2. 【直播核心功能设计文档v3】 - 文件上传实现参考

### 5.2. 日志记录规范

**在每个关键步骤记录日志：**
- Service层入口：`logger.info(f"开始上传专题横幅: topic_id={topic_id}, user_id={user_id}")`
- 文件删除：`logger.info(f"删除旧横幅文件: banner_url={banner_url}")`
- 文件保存：`logger.info(f"新横幅文件保存成功: banner_url={banner_url}")`
- 数据库更新：`logger.info(f"横幅上传成功: topic_id={topic_id}, banner_url={banner_url}")`
- 异常处理：`logger.error(f"上传专题横幅失败: topic_id={topic_id}, error={str(e)}", exc_info=True)`

### 5.3. 代码规范

* 遵循 `rules.md` 中定义的团队代码规范
* **开发语言**: 使用 Python 3.8 或更高版本
* **代码风格**: 严格遵循 PEP 8 规范
* **异步模式**: 所有API端点必须使用 `async def` 函数
* **安全异步异常处理**: 提前提取变量，避免在 `except` 块中访问ORM对象

### 5.4. 通用响应结构

**成功响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "topic_id": "uuid...",
    "banner_url": "/media/topics/.../banner_1729500605.jpg"
  },
  "timestamp": "2025-10-21T18:30:05Z"
}
```

**错误响应：**
```json
{
  "code": 4002,
  "message": "参数校验失败",
  "data": {
    "file": "仅支持 PNG, JPG 格式"
  },
  "timestamp": "2025-10-21T18:30:05Z"
}
```

## 六、具体代码修改指令

### 6.1. 第一部分：修改 Pydantic Schema 定义

**文件**: `app/schemas/topic.py`

**任务**: 调整专题Schema，移除创建/更新接口中的 `banner_url` 字段，在 `TopicInDB` 中显式声明。

#### **修改步骤**：

**步骤1：修改 TopicBase（第435-459行）**

定位到 `class TopicBase(BaseModel):` 定义，执行以下修改：

```python
# ❌ 删除以下3行：
    banner_url: Optional[str] = Field(
        None, 
        max_length=255, 
        description="横幅图 URL，可选，最大 255 字符"
    )

# ✅ 在 description 字段之后，status 字段之前添加注释：
    # banner_url 已移除，通过 POST /api/v1/topics/{topic_id}/banner 接口上传
```

修改后的完整定义：
```python
class TopicBase(BaseModel):
    """
    专题基础 Schema
    
    包含专题的核心业务字段，用于创建和更新操作的基类。
    注意：banner_url 不在此基类中，通过专门的上传接口设置。
    """
    title: str = Field(
        ..., 
        min_length=1, 
        max_length=100, 
        description="专题标题，必填，长度 1-100 字符"
    )
    description: Optional[str] = Field(
        None, 
        description="专题描述，可选，支持 Markdown 格式"
    )
    # banner_url 已移除，通过 POST /api/v1/topics/{topic_id}/banner 接口上传
    status: TopicStatus = Field(
        default=TopicStatus.DRAFT, 
        description="专题状态，默认为草稿"
    )
```

**步骤2：修改 TopicCreate 文档字符串（第462-469行）**

```python
class TopicCreate(TopicBase):
    """
    创建专题请求 Schema
    
    用于 POST /api/v1/topics 接口的请求体。
    user_id 从 JWT Token 中提取，不在请求体中。
    banner_url 默认为 NULL，需通过 POST /api/v1/topics/{topic_id}/banner 接口上传。
    """
    pass  # 继承 TopicBase 的所有字段（不包含 banner_url）
```

**步骤3：修改 TopicUpdate（第472-497行）**

```python
# ❌ 删除以下4行：
    banner_url: Optional[str] = Field(
        None, 
        max_length=255,
        description="横幅图 URL"
    )

# ✅ 添加注释和文档字符串更新
```

修改后的完整定义：
```python
class TopicUpdate(BaseModel):
    """
    更新专题请求 Schema
    
    用于 PATCH /api/v1/topics/{topic_id} 接口的请求体。
    所有字段都是可选的，允许部分更新（PATCH 语义）。
    注意：banner_url 不能通过此接口更新，需使用专门的上传接口。
    """
    title: Optional[str] = Field(
        None, 
        min_length=1, 
        max_length=100,
        description="专题标题"
    )
    description: Optional[str] = Field(
        None,
        description="专题描述"
    )
    # banner_url 已移除，通过 POST /api/v1/topics/{topic_id}/banner 接口更新
    status: Optional[TopicStatus] = Field(
        None,
        description="专题状态"
    )
```

**步骤4：修改 TopicInDB（第500-512行）**

```python
# ✅ 在 user_id 字段之后，created_at 字段之前添加：
    banner_url: Optional[str] = Field(
        None, 
        description="横幅图URL，通过上传接口设置，默认为null"
    )
```

修改后的完整定义：
```python
class TopicInDB(TopicBase):
    """
    数据库中的专题 Schema
    
    包含所有数据库字段，包括系统生成的 id 和时间戳。
    支持从 SQLAlchemy ORM 对象转换。
    注意：banner_url 在此显式声明，因为 TopicBase 中已移除。
    """
    id: uuid.UUID = Field(..., description="专题唯一标识")
    user_id: uuid.UUID = Field(..., description="创建者用户ID")
    banner_url: Optional[str] = Field(
        None, 
        description="横幅图URL，通过上传接口设置，默认为null"
    )
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    model_config = ConfigDict(from_attributes=True)
```

### 6.2. 第二部分：修改CRUD层

**文件**: `app/crud/topic.py`

**任务**: 添加更新专题横幅URL的方法。

**执行流程**:
1. 在文件末尾（`get_topics_by_room` 方法之后）添加新方法：

```python
async def update_banner_url(
    db: AsyncSession, 
    topic_id: uuid.UUID, 
    banner_url: str
) -> Optional[Topic]:
    """
    更新专题横幅URL
    
    Args:
        db: 数据库会话
        topic_id: 专题ID
        banner_url: 新的横幅URL
        
    Returns:
        更新后的Topic对象或None
        
    Raises:
        Exception: 数据库操作失败
    """
    # 提前提取用于日志的变量
    topic_id_for_logging = topic_id
    
    logger.debug(f"更新专题横幅URL: topic_id={topic_id_for_logging}")
    
    try:
        # 查询专题对象
        stmt = select(Topic).where(Topic.id == topic_id)
        result = await db.execute(stmt)
        topic = result.scalar_one_or_none()
        
        if not topic:
            logger.warning(f"专题不存在: topic_id={topic_id_for_logging}")
            return None
        
        # 更新 banner_url 字段
        topic.banner_url = banner_url
        
        # 提交事务
        await db.commit()
        await db.refresh(topic)
        
        logger.debug(f"横幅URL更新成功: topic_id={topic_id_for_logging}, banner_url={banner_url}")
        return topic
        
    except Exception as e:
        await db.rollback()
        logger.error(
            f"更新横幅URL失败: topic_id={topic_id_for_logging}, error={str(e)}"
        )
        raise
```

2. **保持现有方法完全不变**
3. 确保新方法使用 `async def` 和 `await`

### 6.3. 第三部分：修改Service层

**文件**: `app/services/topic_service.py`

**任务**: 添加横幅上传的业务逻辑方法。

**执行流程**:
1. 在 `TopicService` 类中，在 `delete_topic` 方法之后、分类管理方法之前，添加新方法：

```python
    # ==================== 专题横幅管理方法 ====================
    
    async def upload_topic_banner(
        self, 
        topic_id: uuid.UUID, 
        file: UploadFile,
        user_id: uuid.UUID
    ) -> Topic:
        """
        为指定专题上传横幅图片
        
        完全复用直播间封面上传的实现逻辑，只需调整：
        - 存储路径：/media/topics/ 而非 /media/rooms/
        - 文件前缀：banner_ 而非 cover_
        - 数据库字段：topic.banner_url 而非 room.cover_url
        
        Args:
            topic_id: 专题ID
            file: 上传的文件对象
            user_id: 当前用户ID
            
        Returns:
            更新后的Topic对象
            
        Raises:
            TopicNotFoundException: 专题不存在
            TopicPermissionDeniedException: 用户无权修改此专题
        """
        # 提前提取用于日志的变量
        topic_id_for_logging = topic_id
        user_id_for_logging = user_id
        
        logger.info(f"开始上传专题横幅: topic_id={topic_id_for_logging}, user_id={user_id_for_logging}")
        
        try:
            # 1. 验证专题存在性和用户权限
            topic = await crud_topic.get(self.db, topic_id)
            if not topic:
                raise TopicNotFoundException(str(topic_id))
            
            # 权限验证
            if topic.user_id != user_id:
                raise TopicPermissionDeniedException("上传横幅")
            
            # 2. 如果专题已有横幅，删除旧文件
            if topic.banner_url:
                logger.info(f"删除旧横幅文件: banner_url={topic.banner_url}")
                FileHandler.delete_old_banner(topic.banner_url)
            
            # 3. 保存新文件（调用FileHandler的banner专用方法）
            banner_url = await FileHandler.save_banner_file(file=file, topic_id=topic_id)
            logger.info(f"新横幅文件保存成功: banner_url={banner_url}")
            
            # 4. 更新数据库 banner_url
            updated_topic = await crud_topic.update_banner_url(
                db=self.db, 
                topic_id=topic_id, 
                banner_url=banner_url
            )
            
            if not updated_topic:
                logger.error(f"更新横幅URL失败: topic_id={topic_id_for_logging}")
                raise Exception("更新横幅URL失败")
            
            logger.info(f"横幅上传成功: topic_id={topic_id_for_logging}, banner_url={banner_url}")
            
            # 5. 返回更新后的专题对象
            return updated_topic
            
        except (TopicNotFoundException, TopicPermissionDeniedException):
            # 重新抛出业务异常，不记录额外日志
            raise
        except Exception as e:
            logger.error(
                f"上传专题横幅失败: topic_id={topic_id_for_logging}, "
                f"user_id={user_id_for_logging}, error={str(e)}", 
                exc_info=True
            )
            raise
```

2. 在文件顶部添加必要的导入（如果尚未导入）：
```python
from fastapi import UploadFile
from app.core.file_handler import FileHandler
```

3. **保持现有方法完全不变**

### 6.4. 第四部分：修改API端点层

**文件**: `app/api/v1/endpoints/topic.py`

**任务**: 添加横幅上传端点。

#### **6.4.1. 新增横幅上传端点**

**执行流程**:
1. 在文件顶部添加新的导入（如果尚未导入）：
```python
from fastapi import File, UploadFile
from typing import Dict, Any
```

2. 在主路由器 `router` 上，在 `delete_topic` 端点之后、`create_category` 端点之前，添加新的路由：

```python
@router.post("/{topic_id}/banner", response_model=Dict[str, Any])
async def upload_topic_banner(
    topic_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    为指定专题上传横幅图片
    
    完全复用直播间封面上传的实现逻辑：
    - 文件校验：PNG, JPG 格式，10MB 以内
    - 权限验证：仅创建者可上传
    - 存储路径：/media/topics/{topic_id}/banner_{timestamp}.{ext}
    
    Args:
        topic_id: 专题UUID
        file: 上传的图片文件
        current_user: 当前登录用户信息
        db: 数据库会话
        
    Returns:
        标准成功响应，包含 topic_id 和 banner_url
        
    Raises:
        404: 专题不存在
        403: 权限不足
        400: 文件格式或大小不符合要求
    """
    # 提前提取用于日志的变量
    user_id_for_logging = current_user["user_id"]
    topic_id_for_logging = topic_id
    
    logger.info(f"开始上传横幅: topic_id={topic_id_for_logging}, user_id={user_id_for_logging}")
    
    # 实例化服务层
    service = TopicService(db=db)
    
    try:
        # 调用服务层上传横幅
        updated_topic = await service.upload_topic_banner(
            topic_id=topic_id,
            file=file,
            user_id=uuid.UUID(user_id_for_logging)
        )
        
        logger.info(f"横幅上传成功: topic_id={topic_id_for_logging}")
        
        # 构建响应数据
        response_data = {
            "topic_id": str(updated_topic.id),
            "banner_url": updated_topic.banner_url
        }
        
        return success_response(data=response_data)
        
    except TopicNotFoundException:
        logger.warning(f"专题不存在: topic_id={topic_id_for_logging}")
        return JSONResponse(
            status_code=404,
            content=error_response(
                code=2001,
                message="资源不存在",
                data={"resource": "Topic", "id": str(topic_id_for_logging)}
            )
        )
    except TopicPermissionDeniedException as e:
        logger.warning(
            f"无权上传横幅: topic_id={topic_id_for_logging}, "
            f"user_id={user_id_for_logging}"
        )
        return JSONResponse(
            status_code=403,
            content=error_response(
                code=2003,
                message="操作被禁止",
                data={
                    "error": "权限不足", 
                    "reason": "只有创建者可以上传横幅"
                }
            )
        )
    except HTTPException as e:
        logger.warning(f"文件验证失败: {e.detail}")
        return JSONResponse(
            status_code=e.status_code,
            content=error_response(
                code=4002,
                message="参数校验失败",
                data={"file": e.detail}
            )
        )
    except Exception as e:
        logger.error(
            f"横幅上传失败: topic_id={topic_id_for_logging}, "
            f"user_id={user_id_for_logging}, error={str(e)}", 
            exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content=error_response(
                code=1002,
                message="数据库操作错误",
                data={"error": "服务器内部错误"}
            )
        )
```

3. **保持其他端点完全不变**

#### **6.4.2. 修改响应格式化函数（可选，仅添加注释）**

**定位到** `format_topic_response` 函数，在 `banner_url` 字段行添加注释：

```python
def format_topic_response(topic: Topic) -> dict:
    """
    格式化专题响应数据
    
    注意：banner_url 可能为 None（创建时未上传），前端应处理此情况。
    """
    return {
        "id": str(topic.id),
        "user_id": str(topic.user_id),
        "title": topic.title,
        "description": topic.description,
        "banner_url": topic.banner_url,  # 可能为 None，未上传时返回 null
        "status": topic.status.value,
        "created_at": topic.created_at.isoformat() + "Z",
        "updated_at": topic.updated_at.isoformat() + "Z"
    }
```

### 6.5. 第五部分：扩展 FileHandler

**文件**: `app/core/file_handler.py`

**任务**: 添加专题横幅的文件处理方法（三个新方法）。

**执行流程**（在 FileHandler 类中添加以下三个方法）:

#### **方法1：generate_banner_path（新增）**

在 `generate_cover_path` 方法之后添加：

```python
@staticmethod
def generate_banner_path(topic_id: uuid.UUID, extension: str) -> Tuple[str, str]:
    """
    生成横幅存储路径
    
    完全复用 generate_cover_path 的逻辑，只调整路径前缀和文件名前缀。
    
    Args:
        topic_id: 专题ID
        extension: 文件扩展名
        
    Returns:
        (文件系统路径, URL路径)的元组
    """
    # 生成时间戳
    timestamp = int(time.time())
    
    # 构建路径（改为 topics 和 banner）
    relative_dir = f"topics/{topic_id}"
    filename = f"banner_{timestamp}.{extension}"
    
    # 文件系统路径
    fs_dir = os.path.join(ROOM_MEDIA_ROOT_PATH, relative_dir)
    fs_path = os.path.join(fs_dir, filename)
    
    # URL路径
    url_path = f"/media/{relative_dir}/{filename}"
    
    # 确保目录存在
    os.makedirs(fs_dir, exist_ok=True)
    logger.debug(f"生成横幅路径: fs_path={fs_path}, url_path={url_path}")
    
    return fs_path, url_path
```

#### **方法2：save_banner_file（新增）**

在 `save_cover_file` 方法之后添加：

```python
@staticmethod
async def save_banner_file(file: UploadFile, topic_id: uuid.UUID) -> str:
    """
    保存横幅文件并返回URL
    
    完全复用 save_cover_file 的逻辑，只调整路径（通过调用 generate_banner_path）。
    
    Args:
        file: 上传的文件对象
        topic_id: 专题ID
        
    Returns:
        文件的URL路径
        
    Raises:
        HTTPException: 保存失败时抛出异常
    """
    logger.info(f"开始保存横幅文件: topic_id={topic_id}, filename={file.filename}")
    
    try:
        # 1. 验证文件
        FileHandler.validate_image_file(file)
        
        # 2. 获取文件扩展名
        file_ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename else "jpg"
        
        # 3. 生成存储路径（调用 generate_banner_path）
        fs_path, url_path = FileHandler.generate_banner_path(topic_id, file_ext)
        
        # 4. 读取文件内容并检查大小
        contents = await file.read()
        if len(contents) > UPLOAD_MAX_SIZE:
            logger.warning(f"文件大小超出限制: size={len(contents)}, max={UPLOAD_MAX_SIZE}")
            raise HTTPException(
                status_code=400,
                detail=f"文件大小超出限制。最大允许：{UPLOAD_MAX_SIZE / 1024 / 1024:.1f}MB"
            )
        
        # 5. 同步保存文件
        with open(fs_path, "wb") as f:
            f.write(contents)
        
        logger.info(f"横幅文件保存成功: topic_id={topic_id}, path={url_path}")
        return url_path
        
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        logger.error(f"保存横幅文件失败: topic_id={topic_id}, error={str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="文件保存失败"
        )
```

#### **方法3：delete_old_banner（新增）**

在 `delete_old_cover` 方法之后添加：

```python
@staticmethod
def delete_old_banner(banner_url: str) -> None:
    """
    删除旧的横幅文件
    
    完全复用 delete_old_cover 的逻辑，只调整路径处理。
    
    Args:
        banner_url: 横幅URL路径
    """
    if not banner_url:
        return
    
    try:
        # 从URL路径转换为文件系统路径
        # URL格式: /media/topics/{topic_id}/banner_{timestamp}.{ext}
        # 移除开头的 /media/
        relative_path = banner_url.replace("/media/", "")
        fs_path = os.path.join(ROOM_MEDIA_ROOT_PATH, relative_path)
        
        # 检查文件是否存在
        if os.path.exists(fs_path):
            os.remove(fs_path)
            logger.info(f"成功删除旧横幅文件: path={fs_path}")
        else:
            logger.debug(f"旧横幅文件不存在: path={fs_path}")
            
    except Exception as e:
        # 删除失败时只记录警告，不中断流程
        logger.warning(f"删除旧横幅文件失败: banner_url={banner_url}, error={str(e)}")
```

**重要说明**：
1. 这三个方法完全复用了对应的 cover 方法的逻辑
2. 只需调整路径前缀（`rooms` → `topics`）和文件名前缀（`cover` → `banner`）
3. 文件保存使用**同步写入**（`with open(...)`），不是异步写入
4. 使用相同的环境变量 `ROOM_MEDIA_ROOT_PATH`
5. 使用相同的错误处理模式

## 七、架构设计原则

### 7.1. 代码复用架构

**设计原则：**
- **完全复用**: 横幅上传逻辑100%复用直播间封面上传的实现
- **参数化差异**: 只需调整路径前缀、文件名前缀、数据库字段名
- **统一管理**: 所有文件操作集中在 `FileHandler` 工具类中
- **最小修改**: 专题相关代码只需调用 `FileHandler` 的方法，不重新实现

**实现策略：**
1. **CRUD层**: 添加 `update_banner_url` 方法（类似 `update_cover_url`）
2. **Service层**: 添加 `upload_topic_banner` 方法（参考 `upload_room_cover`）
3. **FileHandler**: 添加 `save_banner_file` 和 `delete_old_banner` 方法（复用 cover 逻辑）
4. **Endpoint层**: 添加 `POST /{topic_id}/banner` 端点（参考 `POST /{room_id}/cover`）

### 7.2. Schema设计架构

**设计原则：**
- **职责分离**: 创建/更新接口不处理文件上传，文件上传由专门接口处理
- **默认值策略**: `banner_url` 默认为 `NULL`，不影响专题创建
- **显式声明**: 在 `TopicInDB` 中显式声明 `banner_url`，确保ORM映射正确
- **向后兼容**: 移除字段后，现有代码不传 `banner_url` 也不会报错

## 八、安全要求

### 8.1. 文件上传安全（复用直播间规范）

**类型验证：**
- 只允许 `image/png` 和 `image/jpeg`
- 拒绝其他所有文件类型

**大小限制：**
- 强制执行10MB文件大小限制
- 超出限制立即返回错误，不进行处理

**路径安全：**
- 使用UUID生成目录名，避免路径遍历攻击
- 使用时间戳生成文件名，避免文件名冲突
- 限制文件只能保存在 `/media/topics/` 目录下

**权限控制：**
- 用户只能为自己创建的专题上传横幅
- 在Service层进行权限验证（`topic.user_id == user_id`）
- 验证失败返回 `403 Forbidden`

### 8.2. 错误响应格式

**文件格式错误：**
```json
{
  "code": 4002,
  "message": "参数校验失败",
  "data": {
    "file": "仅支持 PNG, JPG 格式"
  },
  "timestamp": "2025-10-21T18:30:05Z"
}
```

**文件大小超限：**
```json
{
  "code": 4002,
  "message": "参数校验失败",
  "data": {
    "file": "文件大小不能超过 10MB"
  },
  "timestamp": "2025-10-21T18:30:05Z"
}
```

**权限不足：**
```json
{
  "code": 2003,
  "message": "操作被禁止",
  "data": {
    "error": "权限不足",
    "reason": "只有创建者可以上传横幅"
  },
  "timestamp": "2025-10-21T18:30:05Z"
}
```

**专题不存在：**
```json
{
  "code": 2001,
  "message": "资源不存在",
  "data": {
    "resource": "Topic",
    "id": "uuid..."
  },
  "timestamp": "2025-10-21T18:30:05Z"
}
```

## 九、最终交付

请根据以上所有要求和核心约束，**特别是增量修改原则**，为我生成以下文件的修改内容：

### 修改文件（提供完整修改后的代码）：

1. **`app/schemas/topic.py`** - 修改 TopicBase, TopicCreate, TopicUpdate, TopicInDB 的定义
2. **`app/crud/topic.py`** - 添加 `update_banner_url` 方法（在文件末尾）
3. **`app/services/topic_service.py`** - 添加 `upload_topic_banner` 方法（在删除专题方法之后）
4. **`app/api/v1/endpoints/topic.py`** - 添加 `upload_topic_banner` 端点（在删除专题端点之后）

### 可选文件（如果需要）：

5. **`app/core/file_handler.py`** - 添加 `save_banner_file` 和 `delete_old_banner` 方法

**代码要求**：
- **最小化修改**: 只修改必要的部分，其他代码保持原样
- **完全复用**: 横幅上传逻辑100%参考直播间封面上传
- **完整类型注解**: 所有新增函数包含完整的参数和返回值类型
- **详细文档字符串**: 每个新增函数包含 Args, Returns, Raises 说明
- **安全异常处理**: 提前提取变量，避免在 except 块中访问ORM对象
- **适当的日志**: 记录关键步骤和异常信息

**代码格式**：
- 每个文件放在独立的代码块中，并明确标注文件路径
- 使用清晰的注释说明修改位置和原因
- 确保所有函数签名与规格完全一致

## 十、注意事项

### 10.1. 最小化修改原则

**严格遵守以下原则：**

1. **只修改必要的文件**：
   - ✅ 修改 Schema 定义（移除字段）
   - ✅ 添加新方法到 CRUD、Service、Endpoint
   - ❌ 不修改现有方法的核心逻辑
   - ❌ 不重构现有代码结构

2. **只添加新代码，不删除旧逻辑**：
   - ✅ 在文件末尾添加新方法
   - ✅ 在适当位置插入新端点
   - ❌ 不删除现有端点或方法
   - ❌ 不改变现有API的响应结构（除了 `banner_url` 可能为 `null`）

3. **Schema 修改的向后兼容性**：
   - `TopicBase` 移除 `banner_url` 不影响现有代码（因为可选字段）
   - `TopicCreate` 不再接受 `banner_url`，但旧代码不传此字段也能正常工作
   - `TopicUpdate` 不再接受 `banner_url`，但旧代码不传此字段也能正常工作
   - `TopicInDB` 显式添加 `banner_url`，确保数据库读取正确

### 10.2. 代码复用注意事项

1. **完全参考直播间封面上传**：
   - 查看 `app/services/room_service.py` 中的 `upload_room_cover` 方法
   - 查看 `app/api/v1/endpoints/room.py` 中的封面上传端点
   - 查看 `app/core/file_handler.py` 中的 `save_cover_file` 方法

2. **只需调整的参数**：
   - 存储目录：`/media/rooms/` → `/media/topics/`
   - 文件前缀：`cover_` → `banner_`
   - 数据库字段：`room.cover_url` → `topic.banner_url`
   - CRUD方法：`update_cover_url` → `update_banner_url`

3. **不需要重新实现的逻辑**：
   - 文件验证（调用 `FileHandler.validate_image_file`）
   - 文件保存（调用 `FileHandler.save_banner_file`）
   - 旧文件删除（调用 `FileHandler.delete_old_banner`）

### 10.3. 测试建议

1. **功能测试**：
   - 测试创建专题时 `banner_url` 默认为 `null`
   - 测试上传横幅后 `banner_url` 正确更新
   - 测试更新横幅时旧文件被删除
   - 测试不同文件格式的上传（正常和异常情况）
   - 测试文件大小限制

2. **权限测试**：
   - 测试只有创建者可以上传横幅
   - 测试非创建者上传返回 403

3. **边界测试**：
   - 测试专题不存在时返回 404
   - 测试文件格式不符返回 400
   - 测试文件大小超限返回 400

### 10.4. 部署注意事项

1. **确保媒体目录存在**：
   - 创建 `/media/topics/` 目录
   - 确保目录有正确的读写权限

2. **Nginx 配置**：
   - 确保 Nginx 配置支持 10MB 文件上传（`client_max_body_size`）
   - 确保静态文件路由包含 `/media/topics/`

3. **数据库迁移**：
   - `topics.banner_url` 字段已存在，无需迁移
   - 现有专题的 `banner_url` 为 `NULL` 是正常的

### 10.5. 与现有代码的兼容性

1. **不影响现有端点**：
   - `POST /api/v1/topics` - 创建专题（`banner_url` 默认为 `NULL`）
   - `GET /api/v1/topics` - 获取专题列表（响应中 `banner_url` 可能为 `null`）
   - `GET /api/v1/topics/{topic_id}` - 获取专题详情（响应中 `banner_url` 可能为 `null`）
   - `PATCH /api/v1/topics/{topic_id}` - 更新专题（不再接受 `banner_url` 字段）

2. **前端适配**：
   - 前端需要处理 `banner_url` 为 `null` 的情况
   - 前端需要调用新的横幅上传接口
   - 前端创建专题时不再传递 `banner_url` 字段

---

**现在，请开始生成代码！记住：最小化修改，完全复用现有逻辑！**

