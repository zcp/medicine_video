
-----

### **最终版：高效 AI 代码生成提示词 (阶段一: 数据访问层与基础端点)**

#### **1. 角色定义 (Role Definition)**

1. 角色定义 (Role Definition)
你是一名资深的 Python 测试开发工程师（SDET），精通使用 pytest, pytest-asyncio, httpx 和 pytest-mock 对 FastAPI 应用进行健壮、全面的自动化测试。你擅长编写遵循 "Arrange-Act-Assert" 模式的、清晰可读的测试用例。

2. 任务目标 (Task Objective)
#### **2. 任务目标 (Task Objective)**

为 LiveCore 服务的 SRS 内部回调接口 (/internal/srs/on_publish, /internal/srs/on_unpublish) 及其触发的后台 Celery 任务编写一套完整的集成测试。测试需要验证 API 响应、数据库状态的完整生命周期变化，以及对异常情况的处理。


#### **3. 核心上下文信息 (Core Context Information)**

**3.1. 项目结构**

你将要生成以下两个文件，请严格按照此路径：

```
live_core_service/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/
│   │           └── session.py       # <-- 存放API路由 (代码如下)
│   │           └── room.py       # <-- 存放API路由  (代码如下)
│   │           └── internal.py       # <-- 新曾存放给SRS回调的内部API
│   ├── crud/
│   │   └── room.py         # <-- 存放数据库交互函数
│   │   └── session.py         # <-- 存放数据库交互函数
│   ├── models/
│   │   └── live_core.py    # <-- 已存在 (代码如下)
│   ├── schemas/
│   │   └── live_core.py    # <-- 已存在 (代码如下)
│   ├── services/
│   │   └── room_service.py    # <-- 已存在 
│   │   └── session_service.py    # <-- 已存在 
│   │   └── srs_callback_service.py    # <-- 新增专门处理SRS回调的业务逻辑
│   └── tasks/
│       └── session_processing.py # <-- 新增：存放Celery异步任务
│   └── database.py         # <-- 已存在
```

**3.2. 技术栈 **

| 分类               | 技术选型            | 用途说明                                                                                                                       |
|:-----------------|:----------------|:---------------------------------------------------------------------------------------------------------------------------|
| **服务端框架**        | FastAPI         | 构建高性能、异步的 RESTful API。                                                                                                     |
| **ORM**          | SQLAlchemy (异步) | 与 PostgreSQL 数据库进行交互，管理数据模型。                                                                                               |
| **数据模型**         | Pydantic        | 定义 API 的数据结构、请求体验证和响应序列化。                                                                                                  |
| **数据库**          | PostgreSQL      | 持久化存储直播房间、场次、统计等核心数据。                                                                                                      |
| **媒体服务器**        | SRS             | 接收 RTMP 推流，生成 HLS 流，并通过 HTTP 回调通知后端。                                                                                       |
| **Web 服务器**      | Nginx           | 作为反向代理、SSL 终止、负载均衡和静态资源服务。                                                                                                 |
| **前端播放器**        | Video.js        | 在网页端嵌入，用于播放 SRS 生成的 HLS 直播流。                                                                                               |
| **后台任务队列**       | celery          | 执行耗时的后台异步任务，以避免主应用（FastAPI）在处理长时间操作时被阻塞。主要用于直播结束后，在 on_unpublish 回调触发下，处理视频转码、生成封面、数据归档等任务。通过独立的 Worker 进程，实现任务处理的解耦与水平扩展。 |
| **消息中间件 / 缓存**   | Redis           | 主要职责：作为 Celery 的消息中间件（Broker），负责高效、可靠地存储和分发从主应用发布的后台任务消息。。                                                                                                                          |


**3.3. 已存在的代码全文 (Full Text of Existing Code)**

以下是项目已存在的、你需要依赖的核心代码。你必须严格依据这些代码的字段名、类型和关系来生成新代码。

**`app/models/live_core.py`:**

```python
"""
LiveCore Service - SQLAlchemy ORM Models

This module contains all SQLAlchemy ORM models for the LiveCore Service,
corresponding to the database tables defined in the schema.
"""

import uuid
from datetime import datetime
from typing import Optional, List
import enum
from sqlalchemy import Column, String, Text, Boolean, Integer, BigInteger, TIMESTAMP, ForeignKey, Enum as SAEnum  # 关键：将SQLAlchemy的Enum重命名，以避免和Python内置的enum冲突
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# 从数据库配置导入Base
from app.database import Base


class LiveSessionStatus(str, enum.Enum):
    """直播会话状态枚举"""
    SCHEDULED = "scheduled"
    LIVE = "live"
    FINISHED = "finished"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


class LiveRoom(Base):
    """
    直播房间模型 - 对应 live_rooms 表
    持久化容器，存储直播房间的基本信息
    """
    __tablename__ = "live_rooms"

    # 主键 - UUID类型，应用层生成
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 外键 - 父房间ID，自引用关系
    parent_room_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("live_rooms.id", ondelete="SET NULL"), 
        nullable=True
    )
    
    # 用户ID
    user_id = Column(UUID(as_uuid=True), nullable=True)
    
    # 基本信息
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    cover_url = Column(String(255), nullable=True)
    stream_key = Column(String(255), nullable=False, unique=True)
    
    # 设置选项
    is_private = Column(Boolean, default=False)
    record_by_default = Column(Boolean, default=True)
    
    # 分类ID
    category_id = Column(UUID(as_uuid=True), nullable=True)
    
    # 时间戳
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # 关系定义
    # 自引用关系：父房间 -> 子房间
    parent_room = relationship("LiveRoom", remote_side=[id], back_populates="child_rooms")
    child_rooms = relationship("LiveRoom", back_populates="parent_room")
    
    # 一对多关系：房间 -> 直播会话
    live_sessions = relationship("LiveSession", back_populates="room", cascade="all, delete-orphan")


class LiveSession(Base):
    """
    直播会话模型 - 对应 live_sessions 表
    瞬时事件，记录每次直播会话的信息
    """
    __tablename__ = "live_sessions"

    # 主键 - UUID类型，应用层生成
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 外键 - 房间ID
    room_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("live_rooms.id", ondelete="CASCADE"), 
        nullable=False
    )
    
    # 会话状态
    status = Column(SAEnum(LiveSessionStatus, values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    
    # 时间信息
    start_time = Column(TIMESTAMP(timezone=True), nullable=False)
    end_time = Column(TIMESTAMP(timezone=True), nullable=True)
    
    # 视频ID（录制文件）
    video_id = Column(UUID(as_uuid=True), nullable=True, unique=True)
    
    # 时间戳
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # 关系定义
    # 多对一关系：会话 -> 房间
    room = relationship("LiveRoom", back_populates="live_sessions")
    
    # 一对一关系：会话 -> 统计信息
    statistics = relationship("SessionStatistics", back_populates="session", uselist=False, cascade="all, delete-orphan")


class SessionStatistics(Base):
    """
    会话统计模型 - 对应 session_statistics 表
    存储直播会话的统计数据
    """
    __tablename__ = "session_statistics"

    # 主键 - UUID类型，应用层生成
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 外键 - 会话ID，一对一关系
    session_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("live_sessions.id", ondelete="CASCADE"), 
        nullable=False, 
        unique=True
    )
    
    # 统计数据
    peak_viewer_count = Column(Integer, default=0)
    total_viewer_count = Column(BigInteger, default=0)
    total_like_count = Column(BigInteger, default=0)
    total_share_count = Column(BigInteger, default=0)
    
    # 时间戳
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # 关系定义
    # 一对一关系：统计信息 -> 会话
    session = relationship("LiveSession", back_populates="statistics") 
```

**`app/schemas/live_core.py`:**

```python
"""
LiveCore Service - Pydantic Schemas

This module contains all Pydantic schemas for the LiveCore Service,
used for API data validation and serialization.
"""

import uuid
from datetime import datetime
from typing import Optional, List
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


class LiveSessionStatus(str, Enum):
    """直播会话状态枚举"""
    SCHEDULED = "scheduled"
    LIVE = "live"
    FINISHED = "finished"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


# ==================== LiveRoom Schemas ====================

class LiveRoomBase(BaseModel):
    """直播房间基础Schema"""
    title: str = Field(..., max_length=100, description="房间标题")
    description: Optional[str] = Field(None, description="房间描述")
    cover_url: Optional[str] = Field(None, max_length=255, description="封面图片URL")
    is_private: bool = Field(False, description="是否为私密房间")
    record_by_default: bool = Field(True, description="是否默认录制")
    category_id: Optional[uuid.UUID] = Field(None, description="分类ID")


class LiveRoomCreate(LiveRoomBase):
    """创建直播房间请求Schema"""
    parent_room_id: Optional[uuid.UUID] = Field(None, description="父房间ID")
    user_id: Optional[uuid.UUID] = Field(None, description="用户ID")


class LiveRoomUpdate(BaseModel):
    """更新直播房间请求Schema"""
    title: Optional[str] = Field(None, max_length=100, description="房间标题")
    description: Optional[str] = Field(None, description="房间描述")
    cover_url: Optional[str] = Field(None, max_length=255, description="封面图片URL")
    is_private: Optional[bool] = Field(None, description="是否为私密房间")
    record_by_default: Optional[bool] = Field(None, description="是否默认录制")
    category_id: Optional[uuid.UUID] = Field(None, description="分类ID")
    parent_room_id: Optional[uuid.UUID] = Field(None, description="父房间ID")


class LiveRoomResponse(LiveRoomBase):
    """直播房间响应Schema"""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., description="房间ID")
    parent_room_id: Optional[uuid.UUID] = Field(None, description="父房间ID")
    user_id: Optional[uuid.UUID] = Field(None, description="用户ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    stream_key: Optional[str] = Field(None, max_length=255, description="推流密钥（仅在需要时返回）")

# ==================== LiveSession Schemas ====================

class LiveSessionBase(BaseModel):
    """直播会话基础Schema"""
    room_id: uuid.UUID = Field(..., description="房间ID")
    status: LiveSessionStatus = Field(..., description="会话状态")
    start_time: datetime = Field(..., description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    video_id: Optional[uuid.UUID] = Field(None, description="视频ID")


class LiveSessionCreate(LiveSessionBase):
    """创建直播会话请求Schema"""
    pass


class LiveSessionUpdate(BaseModel):
    """更新直播会话请求Schema"""
    status: Optional[LiveSessionStatus] = Field(None, description="会话状态")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    video_id: Optional[uuid.UUID] = Field(None, description="视频ID")


class LiveSessionResponse(LiveSessionBase):
    """直播会话响应Schema"""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., description="会话ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


# ==================== SessionStatistics Schemas ====================

class SessionStatisticsBase(BaseModel):
    """会话统计基础Schema"""
    session_id: uuid.UUID = Field(..., description="会话ID")
    peak_viewer_count: int = Field(0, ge=0, description="峰值观众数")
    total_viewer_count: int = Field(0, ge=0, description="总观众数")
    total_like_count: int = Field(0, ge=0, description="总点赞数")
    total_share_count: int = Field(0, ge=0, description="总分享数")


class SessionStatisticsCreate(SessionStatisticsBase):
    """创建会话统计请求Schema"""
    pass


class SessionStatisticsUpdate(BaseModel):
    """更新会话统计请求Schema"""
    peak_viewer_count: Optional[int] = Field(None, ge=0, description="峰值观众数")
    total_viewer_count: Optional[int] = Field(None, ge=0, description="总观众数")
    total_like_count: Optional[int] = Field(None, ge=0, description="总点赞数")
    total_share_count: Optional[int] = Field(None, ge=0, description="总分享数")


class SessionStatisticsResponse(SessionStatisticsBase):
    """会话统计响应Schema"""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., description="统计记录ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


# ==================== 复合响应Schemas ====================

class LiveSessionWithStatistics(LiveSessionResponse):
    """包含统计信息的直播会话响应Schema"""
    statistics: Optional[SessionStatisticsResponse] = Field(None, description="统计信息")


class LiveRoomWithSessions(LiveRoomResponse):
    """包含会话列表的直播房间响应Schema"""
    live_sessions: List[LiveSessionResponse] = Field(default_factory=list, description="直播会话列表")


class LiveRoomWithSessionsAndStatistics(LiveRoomResponse):
    """包含会话和统计信息的直播房间响应Schema"""
    live_sessions: List[LiveSessionWithStatistics] = Field(default_factory=list, description="直播会话列表")


# ==================== 列表响应Schemas ====================

class LiveRoomListResponse(BaseModel):
    """直播房间列表响应Schema"""
    items: List[LiveRoomResponse] = Field(..., description="房间列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")


class LiveSessionListResponse(BaseModel):
    """直播会话列表响应Schema"""
    items: List[LiveSessionResponse] = Field(..., description="会话列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")


class SessionStatisticsListResponse(BaseModel):
    """会话统计列表响应Schema"""
    items: List[SessionStatisticsResponse] = Field(..., description="统计记录列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")


# ==================== SRS回调Schemas ====================

class SrsOnPublishPayload(BaseModel):
    """SRS on_publish 回调的请求体"""
    action: str
    client_id: str
    ip: str
    vhost: str
    app: str
    stream: str = Field(..., description="推流密钥，即 LiveRoom 的 stream_key")


class SrsOnUnpublishPayload(BaseModel):
    """SRS on_unpublish 回调的请求体"""
    action: str
    client_id: str
    ip: str
    vhost: str
    app: str
    stream: str = Field(..., description="推流密钥，即 LiveRoom 的 stream_key")

```

**`app/crud/room.py`:**

```python
"""
LiveCore Service - Room CRUD Operations

This module contains all CRUD operations for LiveRoom model,
providing data access layer functionality.
"""

import secrets
import uuid
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.live_core import LiveRoom, LiveSession, LiveSessionStatus
from app.schemas.live_core import LiveRoomCreate, LiveRoomUpdate


async def get(db: AsyncSession, room_id: uuid.UUID) -> Optional[LiveRoom]:
    """根据ID获取单个房间"""
    result = await db.execute(
        select(LiveRoom).where(LiveRoom.id == room_id)
    )
    return result.scalar_one_or_none()


async def get_by_stream_key(db: AsyncSession, stream_key: str) -> Optional[LiveRoom]:
    """根据 stream_key 获取单个房间"""
    result = await db.execute(
        select(LiveRoom).where(LiveRoom.stream_key == stream_key)
    )
    return result.scalar_one_or_none()


async def get_multi_and_total(
    db: AsyncSession, 
    skip: int = 0, 
    limit: int = 10
) -> Tuple[List[LiveRoom], int]:
    """分页获取房间列表，同时返回总数"""
    # 获取总数
    count_result = await db.execute(
        select(func.count(LiveRoom.id))
    )
    total = count_result.scalar()
    
    # 获取分页数据
    result = await db.execute(
        select(LiveRoom)
        .order_by(LiveRoom.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    rooms = result.scalars().all()
    
    return list(rooms), total


async def create(db: AsyncSession, obj_in: LiveRoomCreate) -> LiveRoom:
    """创建新房间，内部生成唯一的stream_key"""
    # 生成唯一的推流密钥
    stream_key = f"sk_live_{secrets.token_hex(16)}"
    
    # 确保stream_key唯一性
    while True:
        existing = await db.execute(
            select(LiveRoom).where(LiveRoom.stream_key == stream_key)
        )
        if existing.scalar_one_or_none() is None:
            break
        stream_key = f"sk_live_{secrets.token_hex(16)}"
    
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
        user_id=obj_in.user_id
    )
    
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    
    return db_obj


async def update(
    db: AsyncSession, 
    db_obj: LiveRoom, 
    obj_in: LiveRoomUpdate
) -> LiveRoom:
    """更新房间信息"""
    # 获取更新数据，排除None值
    update_data = obj_in.model_dump(exclude_unset=True)
    
    # 更新对象属性
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    
    await db.commit()
    await db.refresh(db_obj)
    
    return db_obj


async def remove(db: AsyncSession, db_obj: LiveRoom) -> LiveRoom:
    """删除房间"""
    await db.delete(db_obj)
    await db.commit()
    
    return db_obj


async def is_live(db: AsyncSession, room_id: uuid.UUID) -> bool:
    """检查指定房间当前是否有状态为'live'的LiveSession记录"""
    result = await db.execute(
        select(LiveSession)
        .where(
            and_(
                LiveSession.room_id == room_id,
                LiveSession.status == LiveSessionStatus.LIVE
            )
        )
    )
    return result.scalar_one_or_none() is not None


async def get_sub_venues_with_live_status(
    db: AsyncSession, 
    parent_room_id: uuid.UUID, 
    skip: int = 0, 
    limit: int = 10
) -> Tuple[List[Dict[str, Any]], int]:
    """
    获取指定主会场下的所有分会场，并包含其实时直播状态
    使用LEFT OUTER JOIN关联LiveSession表
    """
    # 获取总数
    count_result = await db.execute(
        select(func.count(LiveRoom.id))
        .where(LiveRoom.parent_room_id == parent_room_id)
    )
    total = count_result.scalar()
    
    # 获取分会场数据和直播状态
    result = await db.execute(
        select(
            LiveRoom.id,
            LiveRoom.title,
            LiveRoom.description,
            LiveRoom.cover_url,
            LiveRoom.is_private,
            LiveRoom.record_by_default,
            LiveRoom.category_id,
            LiveRoom.user_id,
            LiveRoom.created_at,
            LiveRoom.updated_at,
            LiveSession.status.label('live_status'),
            LiveSession.id.label('current_session_id')
        )
        .select_from(LiveRoom)
        .outerjoin(
            LiveSession,
            and_(
                LiveSession.room_id == LiveRoom.id,
                LiveSession.status == LiveSessionStatus.LIVE
            )
        )
        .where(LiveRoom.parent_room_id == parent_room_id)
        .order_by(LiveRoom.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    
    # 转换为字典列表
    sub_venues = []
    for row in result:
        sub_venue = {
            'id': row.id,
            'title': row.title,
            'description': row.description,
            'cover_url': row.cover_url,
            'is_private': row.is_private,
            'record_by_default': row.record_by_default,
            'category_id': row.category_id,
            'user_id': row.user_id,
            'created_at': row.created_at,
            'updated_at': row.updated_at,
            'live_status': row.live_status,
            'current_session_id': row.current_session_id
        }
        sub_venues.append(sub_venue)
    
    return sub_venues, total 

**`app/crud/session.py`:**

```python
"""
LiveCore Service - Session CRUD Operations

This module contains all CRUD operations for LiveSession and SessionStatistics models,
providing data access layer functionality.
"""

import uuid
import logging
from typing import Optional, List, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.live_core import LiveSession, SessionStatistics
from app.schemas.live_core import LiveSessionCreate, LiveSessionUpdate

# 设置日志
logger = logging.getLogger(__name__)


async def create_with_stats(db: AsyncSession, obj_in: LiveSessionCreate) -> LiveSession:
    """
    创建一个新的LiveSession记录，并同时创建一个与之关联的、空的SessionStatistics记录
    
    Args:
        db: 数据库会话
        obj_in: LiveSession创建数据
        
    Returns:
        创建的LiveSession对象（包含关联的统计信息）
    """
    logger.info(f"开始创建直播会话: room_id={obj_in.room_id}")
    
    # 创建LiveSession对象
    db_obj = LiveSession(
        room_id=obj_in.room_id,
        status=obj_in.status,
        start_time=obj_in.start_time,
        end_time=obj_in.end_time,
        video_id=obj_in.video_id
    )
    
    # 添加到数据库
    db.add(db_obj)
    await db.flush()  # 刷新以获取生成的ID
    
    # 创建关联的空统计记录
    stats_obj = SessionStatistics(
        session_id=db_obj.id,
        peak_viewer_count=0,
        total_viewer_count=0,
        total_like_count=0,
        total_share_count=0
    )
    
    # 添加统计记录到数据库
    db.add(stats_obj)
    await db.commit()
    await db.refresh(db_obj)
    
    logger.info(f"成功创建直播会话: session_id={db_obj.id}")
    return db_obj


async def get(db: AsyncSession, session_id: uuid.UUID) -> Optional[LiveSession]:
    """
    根据ID获取单个会话
    
    Args:
        db: 数据库会话
        session_id: 会话ID
        
    Returns:
        LiveSession对象或None
    """
    result = await db.execute(
        select(LiveSession).where(LiveSession.id == session_id)
    )
    return result.scalar_one_or_none()


async def get_with_stats(db: AsyncSession, session_id: uuid.UUID) -> Optional[LiveSession]:
    """
    根据ID获取单个场次，并预加载关联的统计数据
    
    Args:
        db: 数据库会话
        session_id: 会话ID
        
    Returns:
        包含统计信息的LiveSession对象或None
    """
    result = await db.execute(
        select(LiveSession)
        .options(selectinload(LiveSession.statistics))
        .where(LiveSession.id == session_id)
    )
    return result.scalar_one_or_none()


async def get_multi_by_room_and_total(
    db: AsyncSession, 
    room_id: uuid.UUID, 
    skip: int = 0, 
    limit: int = 10
) -> Tuple[List[LiveSession], int]:
    """
    分页获取指定room_id的所有场次列表，并返回总数
    
    Args:
        db: 数据库会话
        room_id: 房间ID
        skip: 跳过的记录数
        limit: 限制返回的记录数
        
    Returns:
        (会话列表, 总数)的元组
    """
    # 获取总数
    count_result = await db.execute(
        select(func.count(LiveSession.id)).where(LiveSession.room_id == room_id)
    )
    total = count_result.scalar()
    
    # 获取分页数据
    result = await db.execute(
        select(LiveSession)
        .where(LiveSession.room_id == room_id)
        .order_by(LiveSession.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    sessions = result.scalars().all()
    
    return list(sessions), total


async def update(
    db: AsyncSession, 
    db_obj: LiveSession, 
    obj_in: LiveSessionUpdate
) -> LiveSession:
    """
    更新场次信息
    
    Args:
        db: 数据库会话
        db_obj: 要更新的LiveSession对象
        obj_in: 更新数据
        
    Returns:
        更新后的LiveSession对象
    """
    logger.info(f"开始更新直播会话: session_id={db_obj.id}")
    
    # 获取obj_in的字典表示，排除未设置的字段
    update_data = obj_in.model_dump(exclude_unset=True)
    
    # 更新字段
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    
    # 提交更改
    await db.commit()
    await db.refresh(db_obj)
    
    logger.info(f"成功更新直播会话: session_id={db_obj.id}")
    return db_obj


async def remove(db: AsyncSession, db_obj: LiveSession) -> LiveSession:
    """
    删除场次（由于数据库设置了级联，关联的session_statistics会被自动删除）
    
    Args:
        db: 数据库会话
        db_obj: 要删除的LiveSession对象
        
    Returns:
        被删除的LiveSession对象
    """
    logger.info(f"开始删除直播会话: session_id={db_obj.id}")
    
    await db.delete(db_obj)
    await db.commit()
    
    logger.info(f"成功删除直播会话: session_id={db_obj.id}")
    return db_obj 
```

**`app/api/v1/endpoints/room.py`:**
```python
"""
LiveCore Service - Room API Endpoints

This module contains all API endpoints for LiveRoom resource,
providing REST API interface for room operations.
"""

import uuid
import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.live_core import LiveRoomCreate, LiveRoomUpdate, LiveRoomResponse, ScheduledSessionCreate, LiveSessionCreate
from app.services.room_service import RoomService
from app.services.session_service import SessionService
from app.models.live_core import LiveSessionStatus
from app.crud import room as crud_room
from app.exceptions import (
    RoomNotFoundException,
    ActionForbiddenException,
    ParentRoomNotFoundException
)
from app.core.responses import success_response, error_response

# 设置日志
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter()


@router.post("", response_model=Dict[str, Any])
async def create_room(
    room_in: LiveRoomCreate,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """创建直播房间"""
    logger.info(f"开始创建直播房间: {room_in.title}")
    
    # 实例化服务层
    service = RoomService(db=db)
    
    try:
        # 调用服务层创建房间
        new_room = await service.create_new_room(room_in=room_in)
        logger.info(f"成功创建直播房间: {new_room.id}")
        
        # 构建响应数据
        response_data = {
            "id": str(new_room.id),
            "title": new_room.title,
            "description": new_room.description,
            "stream_key": new_room.stream_key,
            "record_by_default": new_room.record_by_default,
            "created_at": new_room.created_at.isoformat() + "Z"
        }
        
        return success_response(data=response_data)
        
    except ParentRoomNotFoundException:
        logger.warning(f"主会场不存在: {room_in.parent_room_id}")
        return JSONResponse(
            status_code=400,
            content=error_response(
                code=2004,
                message="主会场不存在",
                data={"parent_room_id": str(room_in.parent_room_id)}
            )
        )


@router.get("", response_model=Dict[str, Any])
async def get_rooms(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页大小"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """获取直播房间列表"""
    logger.info(f"获取房间列表: page={page}, size={size}")
    
    # 实例化服务层
    service = RoomService(db=db)
    
    # 调用服务层获取房间列表
    rooms, total = await service.get_room_list(page=page, size=size)
    
    # 构建响应数据
    items = []
    for room in rooms:
        item = {
            "id": str(room.id),
            "title": room.title,
            "cover_url": room.cover_url,
            "created_at": room.created_at.isoformat() + "Z"
        }
        items.append(item)
    
    paginated_data = {
        "total": total,
        "page": page,
        "size": size,
        "items": items
    }
    
    logger.info(f"成功获取房间列表: 总数={total}, 当前页={page}")
    
    return success_response(data=paginated_data)


@router.get("/{room_id}", response_model=Dict[str, Any])
async def get_room(
    room_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """获取单个直播房间详情"""
    logger.info(f"获取房间详情: {room_id}")
    
    # 实例化服务层
    service = RoomService(db=db)
    
    try:
        # 调用服务层获取房间详情
        room = await service.get_room_details(room_id=room_id)
        logger.info(f"成功获取房间详情: {room_id}")
        
        # 构建响应数据
        response_data = {
            "id": str(room.id),
            "title": room.title,
            "description": room.description,
            "stream_key": room.stream_key,
            "is_private": room.is_private,
            "record_by_default": room.record_by_default,
            "created_at": room.created_at.isoformat() + "Z"
        }
        
        return success_response(data=response_data)
        
    except RoomNotFoundException:
        logger.warning(f"房间不存在: {room_id}")
        return JSONResponse(
            status_code=404,
            content=error_response(
                code=2001,
                message="资源不存在",
                data={"resource": "Room", "id": str(room_id)}
            )
        )


@router.patch("/{room_id}", response_model=Dict[str, Any])
async def update_room(
    room_id: uuid.UUID,
    room_update: LiveRoomUpdate,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """更新直播房间信息"""
    logger.info(f"更新房间信息: {room_id}")
    
    # 实例化服务层
    service = RoomService(db=db)
    
    try:
        # 调用服务层更新房间
        updated_room = await service.update_room_info(
            room_id=room_id, 
            room_update=room_update
        )
        logger.info(f"成功更新房间信息: {room_id}")
        
        # 构建响应数据
        response_data = {
            "id": str(updated_room.id),
            "title": updated_room.title,
            "description": updated_room.description,
            "updated_at": updated_room.updated_at.isoformat() + "Z"
        }
        
        return success_response(data=response_data)
        
    except RoomNotFoundException:
        logger.warning(f"房间不存在: {room_id}")
        return JSONResponse(
            status_code=404,
            content=error_response(
                code=2001,
                message="资源不存在",
                data={"resource": "Room", "id": str(room_id)}
            )
        )
    except ActionForbiddenException as e:
        logger.warning(f"房间正在直播，无法修改: {room_id}")
        return JSONResponse(
            status_code=403,
            content=error_response(
                code=2002,
                message="业务逻辑错误",
                data={"error": str(e)}
            )
        )


@router.delete("/{room_id}", response_model=Dict[str, Any])
async def delete_room(
    room_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """删除直播房间"""
    logger.info(f"删除房间: {room_id}")
    
    # 实例化服务层
    service = RoomService(db=db)
    
    try:
        # 调用服务层删除房间
        deleted_room = await service.delete_room(room_id=room_id)
        logger.info(f"成功删除房间: {room_id}")
        
        # 构建响应数据
        response_data = {
            "id": str(deleted_room.id),
            "status": "deleted"
        }
        
        return success_response(data=response_data)
        
    except RoomNotFoundException:
        logger.warning(f"房间不存在: {room_id}")
        return JSONResponse(
            status_code=404,
            content=error_response(
                code=2001,
                message="资源不存在",
                data={"resource": "Room", "id": str(room_id)}
            )
        )
    except ActionForbiddenException as e:
        logger.warning(f"房间正在直播，无法删除: {room_id}")
        return JSONResponse(
            status_code=403,
            content=error_response(
                code=2003,
                message="业务逻辑错误",
                data={"error": str(e)}
            )
        )


@router.get("/{room_id}/sub-venues", response_model=Dict[str, Any])
async def get_sub_venues(
    room_id: uuid.UUID,
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页大小"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """获取分会场列表"""
    logger.info(f"获取分会场列表: parent_room_id={room_id}, page={page}, size={size}")
    
    # 实例化服务层
    service = RoomService(db=db)
    
    try:
        # 调用服务层获取分会场列表
        sub_venues, total = await service.get_sub_venue_list(
            parent_room_id=room_id,
            page=page,
            size=size
        )
        
        # 构建响应数据
        items = []
        for venue in sub_venues:
            item = {
                "id": str(venue['id']),
                "title": venue['title'],
                "live_status": venue['live_status'],
                "current_session_id": str(venue['current_session_id']) if venue['current_session_id'] else None
            }
            items.append(item)
        
        paginated_data = {
            "total": total,
            "page": page,
            "size": size,
            "items": items
        }
        
        logger.info(f"成功获取分会场列表: 总数={total}, 当前页={page}")
        
        return success_response(data=paginated_data)
        
    except RoomNotFoundException:
        logger.warning(f"主会场不存在: {room_id}")
        return JSONResponse(
            status_code=404,
            content=error_response(
                code=2001,
                message="资源不存在",
                data={"resource": "Room", "id": str(room_id)}
            )
        )


@router.post("/{room_id}/sessions", response_model=Dict[str, Any])
async def create_scheduled_session(
    room_id: uuid.UUID,
    scheduled_session_in: ScheduledSessionCreate,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """为指定房间创建一个计划中的直播场次"""
    logger.info(f"为房间创建计划场次: room_id={room_id}")
    
    # 实例化服务层
    service = SessionService(db=db)
    
    try:
        # 调用服务层创建计划场次
        new_session = await service.create_scheduled_session(
            room_id=room_id,
            session_in=scheduled_session_in
        )
        logger.info(f"成功创建计划场次: session_id={new_session.id}")
        
        # 构建响应数据
        response_data = {
            "id": str(new_session.id),
            "room_id": str(new_session.room_id),
            "status": new_session.status.value,
            "start_time": new_session.start_time.isoformat() + "Z",
            "end_time": None,
            "video_id": None,
            "created_at": new_session.created_at.isoformat() + "Z",
            "updated_at": new_session.updated_at.isoformat() + "Z"
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


@router.get("/{room_id}/sessions", response_model=Dict[str, Any])
async def get_room_sessions(
    room_id: uuid.UUID,
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页大小"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """获取指定房间的直播场次列表"""
    logger.info(f"获取房间场次列表: room_id={room_id}, page={page}, size={size}")
    
    # 实例化服务层
    service = SessionService(db=db)
    
    try:
        # 调用服务层获取场次列表
        sessions, total = await service.get_sessions_by_room(
            room_id=room_id,
            page=page,
            size=size
        )
        
        # 构建响应数据
        items = []
        for session in sessions:
            item = {
                "id": str(session.id),
                "room_id": str(session.room_id),
                "status": session.status.value,
                "start_time": session.start_time.isoformat() + "Z",
                "end_time": session.end_time.isoformat() + "Z" if session.end_time else None,
                "video_id": str(session.video_id) if session.video_id else None,
                "created_at": session.created_at.isoformat() + "Z",
                "updated_at": session.updated_at.isoformat() + "Z"
            }
            items.append(item)
        
        paginated_data = {
            "total": total,
            "page": page,
            "size": len(items),
            "items": items
        }
        
        logger.info(f"成功获取房间场次列表: room_id={room_id}, 返回{len(items)}条记录")
        
        return success_response(data=paginated_data)
        
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
```

**`app/crud/session.py`:**
```python
"""
LiveCore Service - Session CRUD Operations

This module contains all CRUD operations for LiveSession and SessionStatistics models,
providing data access layer functionality.
"""

import uuid
import logging
from typing import Optional, List, Tuple
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.live_core import LiveSession, SessionStatistics, LiveSessionStatus
from app.schemas.live_core import LiveSessionCreate, LiveSessionUpdate

# 设置日志
logger = logging.getLogger(__name__)


async def create_with_stats(db: AsyncSession, obj_in: LiveSessionCreate) -> LiveSession:
    """
    创建一个新的LiveSession记录，并同时创建一个与之关联的、空的SessionStatistics记录
    
    Args:
        db: 数据库会话
        obj_in: LiveSession创建数据
        
    Returns:
        创建的LiveSession对象（包含关联的统计信息）
    """
    logger.info(f"开始创建直播会话: room_id={obj_in.room_id}")
    
    # 创建LiveSession对象
    db_obj = LiveSession(
        room_id=obj_in.room_id,
        status=obj_in.status,
        start_time=obj_in.start_time,
        end_time=obj_in.end_time,
        video_id=obj_in.video_id
    )
    
    # 添加到数据库
    db.add(db_obj)
    await db.flush()  # 刷新以获取生成的ID
    
    # 创建关联的空统计记录
    stats_obj = SessionStatistics(
        session_id=db_obj.id,
        peak_viewer_count=0,
        total_viewer_count=0,
        total_like_count=0,
        total_share_count=0
    )
    
    # 添加统计记录到数据库
    db.add(stats_obj)
    await db.commit()
    await db.refresh(db_obj)
    
    logger.info(f"成功创建直播会话: session_id={db_obj.id}")
    return db_obj


async def get(db: AsyncSession, session_id: uuid.UUID) -> Optional[LiveSession]:
    """
    根据ID获取单个会话
    
    Args:
        db: 数据库会话
        session_id: 会话ID
        
    Returns:
        LiveSession对象或None
    """
    result = await db.execute(
        select(LiveSession).where(LiveSession.id == session_id)
    )
    return result.scalar_one_or_none()


async def get_with_stats(db: AsyncSession, session_id: uuid.UUID) -> Optional[LiveSession]:
    """
    根据ID获取单个场次，并预加载关联的统计数据
    
    Args:
        db: 数据库会话
        session_id: 会话ID
        
    Returns:
        包含统计信息的LiveSession对象或None
    """
    result = await db.execute(
        select(LiveSession)
        .options(selectinload(LiveSession.statistics))
        .where(LiveSession.id == session_id)
    )
    return result.scalar_one_or_none()


async def get_latest_scheduled_session(db: AsyncSession, room_id: uuid.UUID) -> Optional[LiveSession]:
    """获取指定房间最新的、状态为'scheduled'的会话"""
    result = await db.execute(
        select(LiveSession)
        .where(
            and_(
                LiveSession.room_id == room_id,
                LiveSession.status == LiveSessionStatus.SCHEDULED
            )
        )
        .order_by(LiveSession.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_live_session_by_room(db: AsyncSession, room_id: uuid.UUID) -> Optional[LiveSession]:
    """获取指定房间内状态为'live'的会话"""
    result = await db.execute(
        select(LiveSession)
        .where(
            and_(
                LiveSession.room_id == room_id,
                LiveSession.status == LiveSessionStatus.LIVE
            )
        )
    )
    return result.scalar_one_or_none()


async def get_multi_by_room_and_total(
    db: AsyncSession, 
    room_id: uuid.UUID, 
    skip: int = 0, 
    limit: int = 10
) -> Tuple[List[LiveSession], int]:
    """
    分页获取指定room_id的所有场次列表，并返回总数
    
    Args:
        db: 数据库会话
        room_id: 房间ID
        skip: 跳过的记录数
        limit: 限制返回的记录数
        
    Returns:
        (会话列表, 总数)的元组
    """
    # 获取总数
    count_result = await db.execute(
        select(func.count(LiveSession.id)).where(LiveSession.room_id == room_id)
    )
    total = count_result.scalar()
    
    # 获取分页数据
    result = await db.execute(
        select(LiveSession)
        .where(LiveSession.room_id == room_id)
        .order_by(LiveSession.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    sessions = result.scalars().all()
    
    return list(sessions), total


async def update(
    db: AsyncSession, 
    db_obj: LiveSession, 
    obj_in: LiveSessionUpdate
) -> LiveSession:
    """
    更新场次信息
    
    Args:
        db: 数据库会话
        db_obj: 要更新的LiveSession对象
        obj_in: 更新数据
        
    Returns:
        更新后的LiveSession对象
    """
    logger.info(f"开始更新直播会话: session_id={db_obj.id}")
    
    # 获取obj_in的字典表示，排除未设置的字段
    update_data = obj_in.model_dump(exclude_unset=True)
    
    # 更新字段
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    
    # 提交更改
    await db.commit()
    await db.refresh(db_obj)
    
    logger.info(f"成功更新直播会话: session_id={db_obj.id}")
    return db_obj


async def remove(db: AsyncSession, db_obj: LiveSession) -> LiveSession:
    """
    删除场次（由于数据库设置了级联，关联的session_statistics会被自动删除）
    
    Args:
        db: 数据库会话
        db_obj: 要删除的LiveSession对象
        
    Returns:
        被删除的LiveSession对象
    """
    logger.info(f"开始删除直播会话: session_id={db_obj.id}")
    
    await db.delete(db_obj)
    await db.commit()
    
    logger.info(f"成功删除直播会话: session_id={db_obj.id}")
    return db_obj 
```


**`app/api/v1/endpoints/session.py`:**
```python
"""
LiveCore Service - Session API Endpoints

This module contains all API endpoints for LiveSession resource,
providing REST API interface for session operations.
"""

import uuid
import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.live_core import LiveSessionUpdate, LiveSessionResponse
from app.models.live_core import LiveSessionStatus
from app.services.session_service import SessionService
from app.exceptions import (
    SessionNotFoundException,
    SessionActionForbiddenException
)
from app.core.responses import success_response, error_response

# 设置日志
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.get("/{session_id}", response_model=Dict[str, Any])
async def get_session_details(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """获取单场直播的详细信息"""
    logger.info(f"获取直播会话详情: session_id={session_id}")
    
    # 实例化服务层
    service = SessionService(db=db)
    
    try:
        # 调用服务层获取会话详情
        session = await service.get_session_details(session_id=session_id)
        logger.info(f"成功获取直播会话详情: session_id={session_id}")
        
        # 构建响应数据
        response_data = {
            "id": str(session.id),
            "room_id": str(session.room_id),
            "status": session.status.value,
            "start_time": session.start_time.isoformat() + "Z",
            "end_time": session.end_time.isoformat() + "Z" if session.end_time else None,
            "video_id": str(session.video_id) if session.video_id else None,
            "created_at": session.created_at.isoformat() + "Z",
            "updated_at": session.updated_at.isoformat() + "Z",
            "statistics": None
        }
        
        # 添加统计信息
        if session.statistics:
            response_data["statistics"] = {
                "id": str(session.statistics.id),
                "session_id": str(session.statistics.session_id),
                "peak_viewer_count": session.statistics.peak_viewer_count,
                "total_viewer_count": session.statistics.total_viewer_count,
                "total_like_count": session.statistics.total_like_count,
                "total_share_count": session.statistics.total_share_count,
                "created_at": session.statistics.created_at.isoformat() + "Z",
                "updated_at": session.statistics.updated_at.isoformat() + "Z"
            }
        
        return success_response(data=response_data)
        
    except SessionNotFoundException:
        logger.warning(f"直播会话不存在: session_id={session_id}")
        return JSONResponse(
            status_code=404,
            content=error_response(
                code=2001,
                message="资源不存在",
                data={"resource": "Session", "id": str(session_id)}
            )
        )


@router.patch("/{session_id}", response_model=Dict[str, Any])
async def update_scheduled_session(
    session_id: uuid.UUID,
    session_update: LiveSessionUpdate,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """更新一个还未开始的计划场次的信息"""
    logger.info(f"更新计划场次: session_id={session_id}")
    
    # 实例化服务层
    service = SessionService(db=db)
    
    try:
        # 调用服务层更新计划场次
        updated_session = await service.update_scheduled_session_info(
            session_id=session_id,
            session_update=session_update
        )
        logger.info(f"成功更新计划场次: session_id={session_id}")
        
        # 构建响应数据
        response_data = {
            "id": str(updated_session.id),
            "room_id": str(updated_session.room_id),
            "status": updated_session.status.value,
            "start_time": updated_session.start_time.isoformat() + "Z",
            "end_time": updated_session.end_time.isoformat() + "Z" if updated_session.end_time else None,
            "video_id": str(updated_session.video_id) if updated_session.video_id else None,
            "created_at": updated_session.created_at.isoformat() + "Z",
            "updated_at": updated_session.updated_at.isoformat() + "Z"
        }
        
        return success_response(data=response_data)
        
    except SessionNotFoundException:
        logger.warning(f"直播会话不存在: session_id={session_id}")
        return JSONResponse(
            status_code=404,
            content=error_response(
                code=2001,
                message="资源不存在",
                data={"resource": "Session", "id": str(session_id)}
            )
        )
    except SessionActionForbiddenException as e:
        logger.warning(f"无法修改非计划状态的场次: session_id={session_id}")
        return JSONResponse(
            status_code=403,
            content=error_response(
                code=2004,
                message="业务逻辑错误",
                data={"error": str(e)}
            )
        )


@router.delete("/{session_id}", response_model=Dict[str, Any])
async def delete_scheduled_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """删除一个指定的直播场次，但不能删除正在直播的场次"""
    logger.info(f"删除计划场次: session_id={session_id}")
    
    # 实例化服务层
    service = SessionService(db=db)
    
    try:
        # 调用服务层删除场次
        deleted_session = await service.delete_session(session_id=session_id)
        logger.info(f"成功删除计划场次: session_id={session_id}")
        
        # 构建响应数据
        response_data = {
            "id": str(deleted_session.id),
            "status": "deleted"
        }
        
        return success_response(data=response_data)
        
    except SessionNotFoundException:
        logger.warning(f"直播会话不存在: session_id={session_id}")
        return JSONResponse(
            status_code=404,
            content=error_response(
                code=2001,
                message="资源不存在",
                data={"resource": "Session", "id": str(session_id)}
            )
        )
    except SessionActionForbiddenException as e:
        logger.warning(f"无法删除正在直播的场次: session_id={session_id}")
        return JSONResponse(
            status_code=403,
            content=error_response(
                code=2005,
                message="业务逻辑错误",
                data={"error": str(e)}
            )
        ) 
```

**`app/services/srs_callback_service.py`:**
```python
"""
LiveCore Service - SRS Callback Service

This module contains the service layer for handling SRS callback events,
providing business logic for on_publish and on_unpublish callbacks.
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import room as crud_room
from app.crud import session as crud_session
from app.models.live_core import LiveRoom, LiveSession, LiveSessionStatus
from app.schemas.live_core import LiveSessionCreate, LiveSessionUpdate
from app.tasks.session_processing import post_stream_processing_task

# 设置日志
logger = logging.getLogger(__name__)


class RoomNotFoundException(Exception):
    """房间不存在异常"""
    pass


class SrsCallbackService:
    """SRS回调服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def handle_on_publish(self, stream_key: str) -> LiveSession:
        """
        处理on_publish回调
        
        Args:
            stream_key: 推流密钥
            
        Returns:
            LiveSession对象
            
        Raises:
            RoomNotFoundException: 房间不存在时抛出
        """
        logger.info(f"处理on_publish回调: stream_key={stream_key}")
        
        # 根据stream_key获取房间
        room = await crud_room.get_by_stream_key(self.db, stream_key=stream_key)
        if not room:
            logger.warning(f"房间不存在: stream_key={stream_key}")
            raise RoomNotFoundException(f"Room with stream_key {stream_key} not found")
        
        logger.info(f"找到房间: room_id={room.id}, title={room.title}")
        
        # 查找计划中的会话
        scheduled_session = await crud_session.get_latest_scheduled_session(
            self.db, room_id=room.id
        )
        
        current_time = datetime.now(timezone.utc)
        
        if scheduled_session:
            # 如果找到计划中的会话，更新其状态为live
            logger.info(f"找到计划中会话: session_id={scheduled_session.id}")
            
            session_update = LiveSessionUpdate(
                status=LiveSessionStatus.LIVE,
                start_time=current_time
            )
            
            updated_session = await crud_session.update(
                self.db, db_obj=scheduled_session, obj_in=session_update
            )
            
            logger.info(f"成功更新会话状态为live: session_id={updated_session.id}")
            return updated_session
            
        else:
            # 如果没有找到计划中的会话，创建新的live会话
            logger.info(f"未找到计划中会话，创建新的live会话: room_id={room.id}")
            
            session_create = LiveSessionCreate(
                room_id=room.id,
                status=LiveSessionStatus.LIVE,
                start_time=current_time,
                end_time=None,
                video_id=None
            )
            
            new_session = await crud_session.create_with_stats(
                self.db, obj_in=session_create
            )
            
            logger.info(f"成功创建新的live会话: session_id={new_session.id}")
            return new_session
    
    async def handle_on_unpublish(self, stream_key: str) -> Optional[LiveSession]:
        """
        处理on_unpublish回调
        
        Args:
            stream_key: 推流密钥
            
        Returns:
            更新后的LiveSession对象，如果没有找到则返回None
            
        Raises:
            RoomNotFoundException: 房间不存在时抛出
        """
        logger.info(f"处理on_unpublish回调: stream_key={stream_key}")
        
        # 根据stream_key获取房间
        room = await crud_room.get_by_stream_key(self.db, stream_key=stream_key)
        if not room:
            logger.warning(f"房间不存在: stream_key={stream_key}")
            raise RoomNotFoundException(f"Room with stream_key {stream_key} not found")
        
        logger.info(f"找到房间: room_id={room.id}, title={room.title}")
        
        # 获取当前正在直播的会话
        live_session = await crud_session.get_live_session_by_room(
            self.db, room_id=room.id
        )
        
        if not live_session:
            logger.warning(f"未找到正在直播的会话: room_id={room.id}")
            return None
        
        logger.info(f"找到正在直播的会话: session_id={live_session.id}")
        
        # 更新会话状态为finished并记录结束时间
        current_time = datetime.now(timezone.utc)
        session_update = LiveSessionUpdate(
            status=LiveSessionStatus.FINISHED,
            end_time=current_time
        )
        
        updated_session = await crud_session.update(
            self.db, db_obj=live_session, obj_in=session_update
        )
        
        logger.info(f"成功更新会话状态为finished: session_id={updated_session.id}")
        
        # 启动后台处理任务
        try:
            post_stream_processing_task.delay(str(updated_session.id))
            logger.info(f"成功启动后台处理任务: session_id={updated_session.id}")
        except Exception as e:
            logger.error(f"启动后台处理任务失败: session_id={updated_session.id}, error={e}")
        
        return updated_session 
```

**`app/api/v1/endpoints/internal.py`:**
```python
"""
LiveCore Service - Internal API Endpoints

This module contains internal API endpoints for SRS callbacks,
providing webhook endpoints for on_publish and on_unpublish events.
"""

import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.live_core import SrsOnPublishPayload, SrsOnUnpublishPayload
from app.services.srs_callback_service import SrsCallbackService, RoomNotFoundException

# 设置日志
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/internal", tags=["Internal"])


@router.post("/on_publish")
async def on_publish(
    payload: SrsOnPublishPayload,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    SRS on_publish 回调端点
    当有推流开始时，SRS会调用此端点
    """
    logger.info(f"收到on_publish回调: action={payload.action}, stream={payload.stream}")
    
    # 实例化服务层
    service = SrsCallbackService(db=db)
    
    try:
        # 调用服务层处理on_publish事件
        session = await service.handle_on_publish(stream_key=payload.stream)
        logger.info(f"成功处理on_publish回调: session_id={session.id}")
        
        # 向SRS返回成功响应
        return {"code": 0}
        
    except RoomNotFoundException as e:
        logger.warning(f"on_publish回调处理失败 - 房间不存在: {e}")
        # 向SRS返回403错误，拒绝推流
        return JSONResponse(
            status_code=403,
            content={"code": 403, "message": "Stream key not found"}
        )
        
    except Exception as e:
        logger.error(f"on_publish回调处理失败 - 系统错误: {e}")
        # 向SRS返回403错误
        return JSONResponse(
            status_code=403,
            content={"code": 403, "message": "Internal server error"}
        )


@router.post("/on_unpublish")
async def on_unpublish(
    payload: SrsOnUnpublishPayload,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    SRS on_unpublish 回调端点
    当推流结束时，SRS会调用此端点
    """
    logger.info(f"收到on_unpublish回调: action={payload.action}, stream={payload.stream}")
    
    # 实例化服务层
    service = SrsCallbackService(db=db)
    
    try:
        # 调用服务层处理on_unpublish事件
        session = await service.handle_on_unpublish(stream_key=payload.stream)
        
        if session:
            logger.info(f"成功处理on_unpublish回调: session_id={session.id}")
        else:
            logger.info("on_unpublish回调处理完成，但未找到对应的直播会话")
        
        # 向SRS返回成功响应
        return {"code": 0}
        
    except RoomNotFoundException as e:
        logger.warning(f"on_unpublish回调处理失败 - 房间不存在: {e}")
        # 即使房间不存在，也返回成功，避免SRS重复回调
        return {"code": 0}
        
    except Exception as e:
        logger.error(f"on_unpublish回调处理失败 - 系统错误: {e}")
        # 即使出现错误，也返回成功，避免SRS重复回调
        return {"code": 0} 
```


**`app/core/response.py`:**
```
"""
LiveCore Service - Response Utilities

This module contains utility functions for constructing standardized API responses.
"""

from datetime import datetime
from typing import Any


def success_response(data: Any, message: str = "success") -> dict:
    """
    构建标准的成功响应体
    
    Args:
        data: 响应数据
        message: 响应消息
        
    Returns:
        标准格式的响应字典
    """
    return {
        "code": 200,
        "message": message,
        "data": data,
        "timestamp": datetime.now().isoformat() + "Z"
    }


def error_response(code: int, message: str, data: Any = None) -> dict:
    """
    构建标准的错误响应体
    
    Args:
        code: 业务错误码
        message: 错误消息
        data: 错误详细数据
        
    Returns:
        标准格式的错误响应字典
    """
    return {
        "code": code,
        "message": message,
        "data": data,
        "timestamp": datetime.now().isoformat() + "Z"
    } 
```


**`app/database.py`:**
你只需假设此文件提供了一个异步依赖函数 `get_db()`，用于获取 `AsyncSession`。

#### **4. 通用规范与 API 定义 (General Specifications & API Definitions)**

**4.1. 权威设计文档**
##### **1. 所有实现细节必须严格遵循【直播核心功能设计文档.md】。

##### **2. 日志记录: 在每个端点函数的入口处，应使用 logger.info() 记录请求的开始。 在成功完成数据库操作后，也应记录成功的消息。在 raise HTTPException 之前，应使用 logger.warning() 记录下具体的业务错误原因。

##### **3. 代码规范**
* 遵循 `rules.md` 中定义的团队代码规范。
* **开发语言**: 使用 Python 3.8 或更高版本。
* **代码风格**: 严格遵循 PEP 8 规范。
* **格式化**:
    * 使用 4 个空格作为缩进。
    * 所有代码文件必须使用 UTF-8 编码。

##### **4. 命名规范**
* **类名 (Class)**: 使用大驼峰命名法 (PascalCase)，例如 `LiveSession`。
* **函数与方法 (Function/Method)**: 使用下划线命名法 (snake\_case)，例如 `get_room_details`。
* **变量 (Variable)**: 使用下划线命名法 (snake\_case)，例如 `session_id`。
* **常量 (Constant)**: 使用全大写下划线命名法 (UPPER\_SNAKE\_CASE)，例如 `MAX_CONNECTIONS`。


**4.2. 通用响应结构**
所有 API 响应都必须遵循以下结构：

```json
{
  "code": int,
  "message": str,
  "data": object | None,
  "timestamp": str  // ISO 8601 格式
}
```

**4.3. 分页与错误码**
必须遵循设计文档中关于分页请求参数、分页响应格式、HTTP 状态码和业务状态码的约定。

#####  **5. 测试框架与环境**

* **测试框架**: `pytest` 和 `pytest-asyncio` (`@pytest.mark.asyncio`)。
* **HTTP 客户端**: 使用一个名为 `async_client` 的 `httpx.AsyncClient` fixture 来发送 API 请求。
* **数据库**: 使用一个名为 `db_session` 的 `AsyncSession` `fixture` 来进行测试前的数据准备和测试后的状态验证。
* **Celery 测试模式**: (关键说明） 尽管生产环境使用 `gevent` 异步 `Worker`，但为了测试的稳定性和可预测性，我们的所有 `pytest `测试都将通过 `conftest.py` 强制 `Celery` 运行在 `task_always_eager=True` 的同步模式下。这使得我们可以在 API 调用返回后，立即验证后台任务执行完毕后的最终数据库状态。
* **测试文件位置**: 所有测试用例都应放在一个新文件 `tests/integration/test_internal_callbacks.py` 中。

**5.2. 依赖的业务代码**

AI 应基于以下已生成的业务代码的逻辑来进行测试：
* `app/api/v1/endpoints/internal.py`: 包含了 `on_publish` 和 `on_unpublish` 端点。
* `app/services/srs_callback_service.py`: 包含了 `handle_on_publish` 和 `handle_on_unpublish` 的核心业务逻辑。
* `app/tasks/session_processing.py`: 包含了 `post_stream_processing_task` 的定义。
* 相关的 `crud` 函数，特别是 `crud.session.get` 和 `crud.room.get_by_stream_key`。

**5.2. 测试辅助函数 (假设)**

请假设存在以下可用的测试辅助函数，你可以在测试用例中直接调用它们：
* `create_test_room(db: AsyncSession) -> models.LiveRoom`: 在数据库中直接创建一个测试用的 `LiveRoom` 并返回其 ORM 对象。
* `create_test_session(db: AsyncSession, room_id: uuid.UUID, status: LiveSessionStatus) -> models.LiveSession`: 在数据库中直接创建一个具有指定状态的 `LiveSession` 并返回其 ORM 对象。

---
**5.4. 关键实现模式：Fixture 的正确使用**
重要: 所有测试用例的函数体必须遵循以下结构，使用 async for 来正确解包 async_client 和 db_session 这两个异步生成器 fixture。所有的业务逻辑（Arrange, Act, Assert）都必须写在 async for 循环的缩进内部。
```python
@pytest.mark.asyncio
async def test_some_scenario(async_client, db_session, ...):
    """测试用例的文档字符串"""
    async for client in async_client:
        async for db in db_session:
            # ----------------------------------------------------
            #  所有的 Arrange, Act, Assert 逻辑都必须在此缩进内
            # ----------------------------------------------------
            
            # 例如:
            # Arrange
            test_room = await create_test_room(db)
            
            # Act
            response = await client.post(...)
            
            # Assert
            assert response.status_code == 200
            db_obj = await get_from_db(db, ...)
            assert db_obj.status == "live"
```

**5.5. 功能实现指令：编写测试用例**

请为以下场景编写具体的 `pytest` 测试用例，每个用例都应包含清晰的文档字符串，描述其测试流程和验证点。

#### **测试一：`on_publish` 回调**

1.  **`test_on_publish_for_scheduled_session`**:
    * **流程**:
        1.  (Arrange) 创建一个测试房间，并为其预先创建一个状态为 `scheduled` 的 `LiveSession`。
        2.  (Act) 使用 `async_client` 调用 `POST /api/v1/internal/srs/on_publish` 端点，`stream_key` 为测试房间的 key。
    * **验证**:
        1.  API 响应的 `status_code` 应为 `200`，响应体 `code` 为 `0`。
        2.  从数据库中重新获取该 `LiveSession`，验证其 `status` 已变为 `live`。
        3.  验证其 `start_time` 已被更新为最近的时间。
        4.  验证数据库中该房间下**仍然只有一条** `LiveSession` 记录。

2.  **`test_on_publish_for_impromptu_session`**:
    * **流程**:
        1.  (Arrange) 只创建一个测试房间，不创建任何 `LiveSession`。
        2.  (Act) 调用 `POST /api/v1/internal/srs/on_publish` 端点。
    * **验证**:
        1.  API 响应 `status_code` 为 `200`，`code` 为 `0`。
        2.  查询数据库，验证**新创建了一条** `LiveSession` 记录，其 `room_id` 正确，且 `status` 为 `live`。
        3.  验证与这条新 `LiveSession` 关联的 `SessionStatistics` 记录也**同时被创建**。

3.  **`test_on_publish_with_invalid_stream_key`**:
    * **流程**:
        1.  (Act) 调用 `POST /api/v1/internal/srs/on_publish` 端点，但使用一个数据库中不存在的 `stream_key`。
    * **验证**:
        1.  API 响应的 `status_code` 应为 `403 Forbidden`。

4. **`test_on_publish_for_already_live_session: (新增的边缘场景测试) `**

    * **流程**:
       1. (Arrange) 创建一个测试房间，并为其创建一个已经是 `live` 状态的 `LiveSession`。记录下这个 `session` 的 `id` 和 `start_time`。
       2. (Act) 再次调用 `POST /api/v1/internal/srs/on_publish` 端点，使用同一个 `stream_key`。
   *  **验证**:
       1.  API 响应的 `status_code` 应为 `200`，响应体 `code` 为 0。
       2.  查询数据库，验证该房间下仍然只有一条 `LiveSession` 记录，其 `id` 与之前记录的 `id` 相同。
       3. 验证该 `LiveSession` 的 `start_time` 没有被改变，与之前记录的 `start_time` 保持一致。

#### **测试二：`on_unpublish` 回调及后续 Celery 任务**

1.  **`test_on_unpublish_and_task_success`**:
    * **流程**:
        1.  (Arrange) 创建一个测试房间，并为其创建一个状态为 `live` 的 `LiveSession`。
        2.  (Act) 使用 `async_client` 调用 `POST /api/v1/internal/srs/on_unpublish` 端点。
    * **验证**:
        1.  API 响应 `status_code` 应为 `200`，响应体 `code` 为 `0`。
        2.  由于 Celery 是同步模式，任务会立即执行。直接从数据库中重新获取该 `LiveSession`。
        3.  验证其 `status` 的**最终状态**应为 `ready`。（由于 `task_always_eager=True`，异步任务会同步执行，我们可以直接验证最终结果）。
        4.  验证其 `end_time` 字段已被成功写入。

2.  **`test_on_unpublish_and_task_failure`**:
    * **流程**:
        1.  (Arrange) 创建一个测试房间和 `live` 状态的 `LiveSession`。
        2.  (关键修改) (Arrange) 由于核心任务是异步的，我们 `patch `一个在任务中被 `await` 的异步操作来模拟失败。使用 `mocker.patch('asyncio.sleep', side_effect=Exception('Simulated async processing error'))`。
        3.  (Act) 调用 `POST /api/v1/internal/srs/on_unpublish` 端点。
    * **验证**:
        1.  API 响应 `status_code` 仍为 `200`，`code` 为 `0`（因为 `on_unpublish` 本身成功了）。
        2.  从数据库中重新获取该 `LiveSession`。
        3.  验证其 `status` 的**最终状态**应为 `error`。

3.  **`test_on_unpublish_with_invalid_stream_key`**: **(新增测试用例)**
    * **流程**:
        1.  (Act) 调用 `POST /api/v1/internal/srs/on_unpublish` 端点，但使用一个数据库中不存在的 `stream_key`。
    * **验证**:
        1.  API 响应的 `status_code` 应为 `200`，响应体 `code` 为 `0`，以确保不会让 SRS 产生不必要的重试。

4.  **`test_on_unpublish_when_no_live_session_exists`**: **(新增测试用例)**
    * **流程**:
        1.  (Arrange) 创建一个测试房间，但**不**为它创建 `live` 状态的会话（可以是 `scheduled` 或 `finished` 状态）。
        2.  (Act) 调用 `POST /api/v1/internal/srs/on_unpublish` 端点，使用该测试房间的 `stream_key`。
    * **验证**:
        1.  API 响应的 `status_code` 应为 `200`，响应体 `code` 为 `0`。
        2.  验证数据库中**没有发生任何状态变化**。

---

### **5. 最终交付 (Final Deliverable)**

请根据以上所有要求，为我生成 `tests/integration/test_internal_callbacks.py` 文件的完整、可直接运行的 Python 代码。