"""
LiveCore Service - SQLAlchemy ORM Models

This module contains all SQLAlchemy ORM models for the LiveCore Service,
corresponding to the database tables defined in the schema.
"""

import uuid
from datetime import datetime
from typing import Optional, List
import enum
from sqlalchemy import Column, String, Text, Boolean, Integer, BigInteger, TIMESTAMP, ForeignKey, Enum as SAEnum, Index  # 关键：将SQLAlchemy的Enum重命名，以避免和Python内置的enum冲突
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, text

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
    user_id = Column(
        UUID(as_uuid=True), 
        nullable=False, 
        comment="用户ID，关联到用户服务的public_id（应用层验证）"
    )
    
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
    
    # V6 新增：外部直播间ID（用于批量导入幂等）
    external_room_id = Column(String(64), nullable=True, comment="外部直播间ID（如第三方平台直播间ID）")

    # 文档 18：测播间关联正式间（仅测播间使用；正式间为 NULL）
    source_room_id = Column(
        UUID(as_uuid=True),
        ForeignKey("live_rooms.id", ondelete="SET NULL"),
        nullable=True,
        comment="测播间关联的正式间 ID",
    )
    
    # 时间戳
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # 索引定义
    __table_args__ = (
        Index("idx_live_rooms_user_id", "user_id"),
        # V6 新增：部分唯一索引（仅对非空 external_room_id 生效）
        Index(
            "uq_live_rooms_user_external_room",
            "user_id",
            "external_room_id",
            unique=True,
            postgresql_where=text("external_room_id IS NOT NULL"),
        ),
        # 文档 18：一正式间至多一测播间
        Index(
            "uq_live_rooms_source_room_id",
            "source_room_id",
            unique=True,
            postgresql_where=text("source_room_id IS NOT NULL"),
        ),
        Index(
            "idx_live_rooms_source_room_id",
            "source_room_id",
            postgresql_where=text("source_room_id IS NOT NULL"),
        ),
    )

    # 关系定义
    # 自引用：分会场（parent_room_id）；测播关联用 source_room_id 列，不挂 relationship 以免歧义
    parent_room = relationship(
        "LiveRoom",
        remote_side=[id],
        back_populates="child_rooms",
        foreign_keys=[parent_room_id],
    )
    child_rooms = relationship(
        "LiveRoom",
        back_populates="parent_room",
        foreign_keys=[parent_room_id],
    )
    
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
    
    # 回放地址（持久化字段）
    playback_url = Column(String(1024), nullable=True)
    
    # V6 新增：playback_url 规范化后的哈希值（用于幂等导入）
    playback_url_hash = Column(String(128), nullable=True, comment="playback_url 规范化后的哈希值")
    
    # 时间戳
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # 索引定义（V6 新增）
    __table_args__ = (
        # V6 新增：部分唯一索引（仅对非空 playback_url_hash 生效）
        Index(
            "uq_live_sessions_room_playback_hash",
            "room_id",
            "playback_url_hash",
            unique=True,
            postgresql_where=text("playback_url_hash IS NOT NULL"),
        ),
    )

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