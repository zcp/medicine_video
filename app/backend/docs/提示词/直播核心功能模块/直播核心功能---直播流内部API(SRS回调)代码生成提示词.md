
-----

### **最终版：高效 AI 代码生成提示词 (阶段一: 数据访问层与基础端点)**

#### **1. 角色定义 (Role Definition)**

你是一名资深的 Python 后端工程师，精通 FastAPI，异步 SQLAlchemy， Pydantic 和 Celery。并擅长根据详细的设计文档和代码上下文，编写出精确、健壮且符合规范的代码。

#### **2. 任务目标 (Task Objective)**

请根据以下提供的技术栈、数据模型和详细的功能描述，为我的直播核心服务（LiveCore Service）实现由媒体服务器（SRS）回调的内部 API 接口。你需要编写出符合 Python 3.8+ 类型提示规范的、生产级的代码。

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
│   │           └── internal.py       # <-- 新曾：存放给SRS回调的内部API
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
│   │   └── srs_callback_service.py    # <-- 新增：专门处理SRS回调的业务逻辑
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
| **协程/并发库**   |gevent          | 作为 Celery 的执行池（Execution Pool），使其 Worker 能够原生、高并发地执行 async def 异步任务。这统一了整个项目的异步技术模型，并提供了卓越的 I/O 并发性能。                                                                                                                       |


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
    stream_key = f"streamkey_{secrets.token_hex(16)}"
    
    # 确保stream_key唯一性
    while True:
        existing = await db.execute(
            select(LiveRoom).where(LiveRoom.stream_key == stream_key)
        )
        if existing.scalar_one_or_none() is None:
            break
        stream_key = f"streamkey_{secrets.token_hex(16)}"
    
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


### **5. 功能实现指令 (重构版)**

请严格遵循 **Endpoint -\> Service -\> CRUD** 的分层架构模式，为以下功能生成代码。

#### **前提：新增必要的 Pydantic Schemas**

在 `app/schemas/live_core.py` 中，请先补充 SRS 回调所需的 Pydantic 模型：

```python
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

#### **功能一: 为 `on_publish` 和 `on_unpublish` 创建服务层和 CRUD 函数**

**1. 在 `app/crud/room.py` 中，新增以下函数:**

```python
# app/crud/room.py

async def get_by_stream_key(db: AsyncSession, stream_key: str) -> Optional[LiveRoom]:
    """根据 stream_key 获取单个房间"""
    result = await db.execute(
        select(LiveRoom).where(LiveRoom.stream_key == stream_key)
    )
    return result.scalar_one_or_none()
```

**2. 在 `app/crud/session.py` 中，新增以下函数:**

```python
# app/crud/session.py

async def get_latest_scheduled_session(db: AsyncSession, room_id: uuid.UUID) -> Optional[LiveSession]:
    """获取指定房间最新的、状态为'scheduled'的会话"""
    result = await db.execute(
        select(LiveSession)
        .where(
            LiveSession.room_id == room_id,
            LiveSession.status == LiveSessionStatus.SCHEDULED
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
            LiveSession.room_id == room_id,
            LiveSession.status == LiveSessionStatus.LIVE
        )
    )
    return result.scalar_one_or_none()
```

### **已修正的 `srs_callback_service.py` 代码生成提示词**

以下是为您重写后的指令，您可以直接用它来替换您提示词中的对应部分。我在关键的修改点添加了**（关键修改）**的注释。

---
**3. 创建一个新的服务层文件 `app/services/srs_callback_service.py`，内容如下:**

* 创建一个 `SrsCallbackService` 类，它在初始化时接收 `db: AsyncSession`。

* 在该 Service 中实现一个 **`async def handle_on_publish(self, stream_key: str)`** 方法：**(关键修改：方法变为异步)**
    * `await` 调用 `crud.room.get_by_stream_key` 获取房间。如果不存在，则抛出异常。
    * （新增逻辑）先 `await` 调用 `crud.session.get_live_session_by_room` 检查是否已有 `live` 状态的会话。如果存在，则直接返回该会话，不做任何更改。
    * 如果不存在 `live` 的会话，再 `await` 调用 `crud.session.get_latest_scheduled_session` 查找计划中会话。
    * 如果找到计划中会话，则 `await` 调用 `crud.session.update` 将其状态更新为 `live`。
    * 如果没找到计划中会话，则 `await` 调用已存在的 `crud.session.create_with_stats` 来创建一个状态为 `live` 的新会话。
    * 返回最终被激活或创建的 `LiveSession` 对象。

* 在该 Service 中实现一个 **`async def handle_on_unpublish(self, stream_key: str)`** 方法：**(关键修改：方法变为异步)**
    * `await` 调用 `crud.room.get_by_stream_key` 获取房间。
    * `await` 调用 `crud.session.get_live_session_by_room` 获取直播中会话。
    * 如果找到，则 `await` 调用 `crud.session.update` 将其状态更新为 `finished`，并记录 `end_time`。
    * **（重要说明）** 调用 Celery 任务 `post_stream_processing_task.delay()`。**注意：`.delay()` 本身是一个同步调用**，它只是负责将任务消息发送到 Redis，这个动作是瞬间完成的，所以**此处不需要 `await`**。
    * 返回被更新的 `LiveSession` 对象。

---

#### **功能二: 创建或更新内部 API 端点文件**

**在 `app/api/v1/endpoints/internal.py` (建议新建此文件) 中，创建以下端点:**

  * **`POST /on_publish`**:
      * 接收 `SrsOnPublishPayload`。
      * 实例化 `SrsCallbackService`。
      * await 调用 service.handle_on_publish 方法，并处理可能发生的异常。
      * 成功后向 SRS 返回 `{"code": 0}`，状态码 `200`。失败则根据异常返回 `403`。
      * 此内部接口无需遵循 ** 4.2 中定义的通用响应结构**。
    
  * **`POST /on_unpublish`**:
      * 接收 `SrsOnUnpublishPayload`。
      * 实例化 `SrsCallbackService`。
      * await 调用 service.handle_on_unpublish 方法。
      * 该方法会立即将任务派发至 Redis，并返回。
      * 成功派发后，立即向 SRS 返回 `{"code": 0}`，状态码 `200`。**此内部接口无需遵循 4.2 中定义的通用响应结构**。

#### **功能三: 实现可测试的、原生异步的 Celery 任务**

本功能分为两个部分：首先定义一个包含核心业务逻辑的、纯粹的异步函数；然后创建一个 Celery 任务作为“包装器”，负责管理数据库会话并调用该逻辑函数。

**1. 在 `app/tasks/session_processing.py` 中，实现核心业务逻辑函数:**

* **定义**: 创建一个**不带 `@celery_app.task` 装饰器**的、普通的内部异步函数，命名为 `_process_session_logic`。
* **函数签名**: 其签名**必须**是 `async def _process_session_logic(db: AsyncSession, session_id: str):`。它的第一个参数必须是 `AsyncSession`，用于接收外部传入的数据库会话。
* **核心逻辑**:
    1.  使用**传入的 `db` 对象**，`await` 调用 `crud.session.get` 获取会话对象。如果找不到，记录错误并返回。
    2.  使用**传入的 `db` 对象**，`await` 调用 `crud.session.update` 将状态更新为 `processing`。
    3.  在一个 `try...except` 块中，执行核心的耗时任务：
        * 在 `try` 块中，留出核心任务的占位符（例如 `await asyncio.sleep(5)`）。
        * 任务成功后，使用**传入的 `db` 对象**，`await` 调用 `crud.session.update` 将状态更新为 `ready`。
        * 在 `except` 块中，捕获异常，并使用**传入的 `db` 对象**，`await` 调用 `crud.session.update` 将状态更新为 `error`。

**2. 在 `app/tasks/session_processing.py` 中，实现 Celery 任务包装器:**

* **定义**: 创建一个名为 `post_stream_processing_task` 的、真正的 Celery 任务。它是一个 `async def` 函数。
* **职责**: 这个函数非常“薄”，它唯一的职责就是**创建并管理数据库会话的生命周期**，然后调用上面的 `_process_session_logic` 函数。
* **实现步骤**:
    1.  定义 `@celery_app.task(...) async def post_stream_processing_task(self, session_id: str):`。
    2.  在函数内部，使用 `app.database.get_db` 异步生成器来获取一个数据库会话 `db`。
    3.  使用 `try...finally` 结构来确保数据库会话最终被关闭。
    4.  在 `try` 块中，`await` 调用我们上面定义的核心逻辑函数 `_process_session_logic(db, session_id)`。
    5.  在 `finally` 块中，调用 `await db.close()`。

-----


### **6. 最终交付 (Final Deliverable)**

请根据以上所有要求，生成或修改以下文件。请将每个文件的完整代码放在独立的、有明确文件路径标记的代码块中。

#### **需要新增的文件 (New Files to Generate):**

1.  **`app/services/srs_callback_service.py`**
    * **内容**: 包含 `SrsCallbackService` 类的完整实现，其中应有 `handle_on_publish` 和 `handle_on_unpublish` 这两个核心业务方法。

2.  **`app/api/v1/endpoints/internal.py`**
    * **内容**: 包含一个新的 `APIRouter`，并定义 `/on_publish` 和 `/on_unpublish` 这两个内部 API 端点。此文件应遵循分层原则，调用 `SrsCallbackService` 来处理逻辑。

3.  **`app/tasks/session_processing.py`**
    * **内容**: 包含 `post_stream_processing_task` 这个 Celery 任务的完整定义和实现逻辑。

#### **需要修改的文件 (Files to Modify):**

1.  **`app/crud/room.py`**
    * **修改内容**: 在您已提供的现有代码基础上，**新增** `get_by_stream_key` 函数。

2.  **`app/crud/session.py`**
    * **修改内容**: 在您已提供的现有代码基础上，**新增** `get_latest_scheduled_session` 和 `get_live_session_by_room` 这两个函数。

3.  **`app/schemas/live_core.py`**
    * **修改内容**: 在您已提供的现有代码基础上，**新增** `SrsOnPublishPayload` 和 `SrsOnUnpublishPayload` 这两个 Pydantic 模型。

---

