"""
专题聚合功能的数据库模型

本模块包含专题聚合功能所需的三个 SQLAlchemy 模型类：
- Topic: 专题表（顶层实体）
- TopicCategory: 专题内分类表（中层实体）
- TopicCategoryRoom: 专题分类与直播间的关联表（关系层）
"""
import uuid
from datetime import datetime
import enum

# SQLAlchemy 核心导入
from sqlalchemy import Column, String, Text, Integer, ForeignKey, Enum as SAEnum, UniqueConstraint, Index, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


# ==================== 枚举类型定义 ====================

class TopicStatus(str, enum.Enum):
    """专题状态枚举"""
    DRAFT = "draft"          # 草稿
    PUBLISHED = "published"  # 已发布
    ARCHIVED = "archived"    # 已归档


# ==================== 模型类定义 ====================

class Topic(Base):
    """
    专题活动表
    
    用于聚合多个分类和直播间，实现类似聚合页面的功能。
    一个专题可以包含多个分类，每个分类下可以关联多个直播间。
    """
    __tablename__ = "topics"
    
    # 核心标识 (在应用层通过 uuid.uuid4() 生成)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 用户ID，对应 users 表的 public_id（通过JWT Token应用层验证保证引用完整性）
    # 注意：不使用 ForeignKey，因为 User 服务可能独立部署
    user_id = Column(
        UUID(as_uuid=True), 
        nullable=False, 
        comment='创建者用户ID，对应 users.public_id'
    )
    
    # 业务字段
    title = Column(String(100), nullable=False, comment='专题标题')
    description = Column(Text, nullable=True, comment='专题描述')
    banner_url = Column(String(255), nullable=True, comment='横幅图URL')
    
    # 专题状态
    status = Column(
        SAEnum(TopicStatus, values_callable=lambda obj: [e.value for e in obj]), 
        nullable=False, 
        default=TopicStatus.DRAFT,
        comment='专题状态: draft(草稿), published(已发布), archived(已归档)'
    )
    
    # 时间戳 - 使用 server_default 和 func.now()
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # 索引定义
    __table_args__ = (
        Index('idx_topics_user_id', 'user_id'),
        Index('idx_topics_status', 'status'),
        Index('idx_topics_created_at', 'created_at'),
    )
    
    # 关联关系
    categories = relationship(
        "TopicCategory", 
        back_populates="topic", 
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by = "TopicCategory.sort_order"  # 👈 添加这一行
    )
    
    def __repr__(self):
        return f"<Topic(id={self.id}, title={self.title})>"


class TopicCategory(Base):
    """
    专题内分类表
    
    专题下的分类，如按省份、按科室等。
    一个专题可以包含多个分类，每个分类可以关联多个直播间。
    """
    __tablename__ = "topic_categories"
    
    # 核心标识 (在应用层通过 uuid.uuid4() 生成)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 外键 - 关联到专题
    topic_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("topics.id", ondelete="CASCADE"), 
        nullable=False,
        comment='所属专题ID'
    )
    
    # 业务字段
    name = Column(String(50), nullable=False, comment='分类名称')
    sort_order = Column(Integer, default=0, nullable=False, comment='排序顺序，数值越小越靠前')
    
    # 时间戳 - 使用 server_default 和 func.now()
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # 索引和约束定义
    __table_args__ = (
        Index('idx_topic_categories_topic_id', 'topic_id'),
        Index('idx_topic_categories_topic_sort', 'topic_id', 'sort_order'),
        UniqueConstraint('topic_id', 'name', name='uq_topic_category_name'),
    )
    
    # 关联关系
    topic = relationship("Topic", back_populates="categories")
    rooms = relationship(
        "TopicCategoryRoom", 
        back_populates="category", 
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    def __repr__(self):
        return f"<TopicCategory(id={self.id}, name={self.name}, sort_order={self.sort_order})>"


class TopicCategoryRoom(Base):
    """
    专题分类与直播间的关联表
    
    用于定义专题分类与直播间的多对多关联关系。
    同一个直播间可以被添加到多个不同的专题分类中。
    """
    __tablename__ = "topic_category_rooms"
    
    # 核心标识 (在应用层通过 uuid.uuid4() 生成)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 外键 - 关联到分类
    category_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("topic_categories.id", ondelete="CASCADE"), 
        nullable=False,
        comment='所属分类ID'
    )
    
    # 外键 - 关联到直播间
    room_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("live_rooms.id", ondelete="CASCADE"), 
        nullable=False,
        comment='关联的直播间ID'
    )
    
    # 业务字段
    sort_order = Column(Integer, default=0, nullable=False, comment='在分类下的排序顺序，数值越小越靠前')
    
    # 时间戳 - 使用 server_default 和 func.now()
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # 索引和约束定义
    __table_args__ = (
        Index('idx_tcr_category_id', 'category_id'),
        Index('idx_tcr_room_id', 'room_id'),
        Index('idx_tcr_category_sort', 'category_id', 'sort_order'),
        UniqueConstraint('category_id', 'room_id', name='uq_category_room'),
    )
    
    # 关联关系
    category = relationship("TopicCategory", back_populates="rooms")
    room = relationship("LiveRoom")
    
    def __repr__(self):
        return f"<TopicCategoryRoom(category_id={self.category_id}, room_id={self.room_id}, sort_order={self.sort_order})>"

