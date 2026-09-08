"""
直播间 Tab 和留言功能的数据库模型
"""
import uuid
from datetime import datetime
import enum

# SQLAlchemy 核心导入
from sqlalchemy import Column, String, Text, Integer, ForeignKey, Enum as SAEnum, Index, TIMESTAMP, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


# ==================== 枚举类型定义 ====================
# 对应 DDL: CREATE TYPE live_room_message_user_role
class LiveRoomMessageUserRole(str, enum.Enum):
    """留言用户角色枚举"""
    REGULAR = 'REGULAR'
    MODERATOR = 'MODERATOR'
    ADMIN = 'ADMIN'
    SUPERADMIN = 'SUPERADMIN'


# 对应 DDL: CREATE TYPE live_room_tab_content_type
class LiveRoomTabContentType(str, enum.Enum):
    """Tab内容类型枚举"""
    TEXT = 'text'
    IMAGE = 'image'
    MIXED = 'mixed'


# ==================== 模型类定义 ====================

class LiveRoomMessage(Base):
    """直播间留言表"""
    __tablename__ = "live_room_messages"
    
    # 主键
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 外键
    room_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("live_rooms.id", ondelete="CASCADE"), 
        nullable=False
    )
    session_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("live_sessions.id", ondelete="SET NULL"), 
        nullable=True
    )
    
    # 用户信息
    user_id = Column(
        UUID(as_uuid=True), 
        nullable=False, 
        comment='存储 users.public_id'
    )
    user_role = Column(
        SAEnum(LiveRoomMessageUserRole, name='live_room_message_user_role', create_type=False), 
        nullable=False, 
        comment='用户角色快照'
    )
    
    # 留言内容
    content = Column(Text, nullable=False)
    
    # 状态与扩展
    is_deleted = Column(Boolean, nullable=False, default=False)
    extra = Column(JSONB, nullable=True)
    
    # 时间戳
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    
    # 索引定义
    __table_args__ = (
        Index('idx_live_room_messages_room_created', 'room_id', 'created_at'),
        Index('idx_live_room_messages_session_created', 'session_id', 'created_at'),
    )
    
    # 关联关系（单向）
    room = relationship("LiveRoom")
    session = relationship("LiveSession")
    
    def __repr__(self):
        return f"<LiveRoomMessage(id={self.id}, user_id={self.user_id})>"


class LiveRoomTab(Base):
    """直播间 Tab 表"""
    __tablename__ = "live_room_tabs"
    
    # 主键
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 外键
    room_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("live_rooms.id", ondelete="CASCADE"), 
        nullable=False
    )
    
    # Tab 基本信息
    tab_key = Column(
        String(64), 
        nullable=False, 
        comment='系统级 key，用于逻辑识别'
    )
    title = Column(
        String(128), 
        nullable=False, 
        comment='展示名称'
    )
    
    # 内容类型与内容
    content_type = Column(
        SAEnum(LiveRoomTabContentType, name='live_room_tab_content_type', create_type=False), 
        nullable=False, 
        comment="'text' | 'image' | 'mixed'"
    )
    text_content = Column(Text, nullable=True)
    image_url = Column(Text, nullable=True)
    
    # 排序与状态
    sort_order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    
    # 时间戳
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # 索引定义
    __table_args__ = (
        Index('idx_live_room_tabs_room_sort', 'room_id', 'sort_order'),
    )
    
    # 关联关系（单向）
    room = relationship("LiveRoom")
    
    def __repr__(self):
        return f"<LiveRoomTab(id={self.id}, title={self.title}, room_id={self.room_id})>"

