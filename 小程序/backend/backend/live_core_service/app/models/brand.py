"""
品牌模块的数据库模型

本模块包含品牌模块所需的三个 SQLAlchemy 模型类：
- Brand: 品牌/合作伙伴表
- BrandTopic: 品牌-专题关联表
- BrandRoom: 品牌-直播间关联表
"""
import uuid

# SQLAlchemy 核心导入
from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey, Index, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, text

from app.database import Base  # 注意：Base 在 database.py 中，不是 models/base.py


class Brand(Base):
    """
    品牌/合作伙伴信息表
    
    用于存储合作品牌信息（如：迈瑞医疗、威克·微课等）
    """
    __tablename__ = "brands"
    
    # 核心标识 (在应用层通过 uuid.uuid4() 生成)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 业务字段
    name = Column(String(150), nullable=False, unique=True, comment='品牌名称')
    slug = Column(String(150), nullable=True, comment='URL友好标识符，用于生成品牌详情页链接')
    logo_url = Column(String(512), nullable=True, comment='品牌Logo图片URL')
    description = Column(Text, nullable=True, comment='品牌描述')
    website_url = Column(String(255), nullable=True, comment='品牌官网链接')
    sort_order = Column(Integer, default=0, nullable=False, comment='排序权重，用于品牌栏展示顺序，值越小越靠前')
    is_active = Column(Boolean, default=True, nullable=False, comment='软删除标识，false表示已删除')
    
    # 时间戳 - 使用 server_default 和 func.now()
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # 索引定义
    __table_args__ = (
        Index('idx_brands_sort_order', 'sort_order'),
        Index('idx_brands_is_active', 'is_active'),
        # 部分索引：仅对 is_active = true 的记录创建索引
        Index('idx_brands_active_sort', 'is_active', 'sort_order', postgresql_where=text("is_active = true")),
    )
    
    # 关联关系
    topics = relationship("BrandTopic", back_populates="brand", cascade="all, delete-orphan")
    rooms = relationship("BrandRoom", back_populates="brand", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Brand(id={self.id}, name={self.name})>"


class BrandTopic(Base):
    """
    品牌与专题的多对多关联表
    
    关联brands表和topics表（topics表定义见专题功能文档）
    用于建立品牌与专题的关联关系
    """
    __tablename__ = "brand_topics"
    
    # 外键字段
    brand_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("brands.id", ondelete="CASCADE"), 
        nullable=False,
        primary_key=True,
        comment='品牌ID，关联brands表'
    )
    topic_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("topics.id", ondelete="CASCADE"), 
        nullable=False,
        primary_key=True,
        comment='专题ID，关联topics表（topics表定义见专题功能文档）'
    )
    
    # 时间戳
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    
    # 索引定义
    __table_args__ = (
        Index('idx_brand_topics_brand_id', 'brand_id'),
        Index('idx_brand_topics_topic_id', 'topic_id'),
    )
    
    # 关联关系
    brand = relationship("Brand", back_populates="topics")
    # 注意：Topic模型由专题功能模块定义，这里不定义relationship，避免循环导入
    
    def __repr__(self):
        return f"<BrandTopic(brand_id={self.brand_id}, topic_id={self.topic_id})>"


class BrandRoom(Base):
    """
    品牌与直播间的多对多关联表
    
    用于直播间页品牌Tab展示 room 绑定品牌
    关联brands表和live_rooms表（live_rooms表定义见v6主文档）
    """
    __tablename__ = "brand_rooms"
    
    # 外键字段
    brand_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("brands.id", ondelete="CASCADE"), 
        nullable=False,
        primary_key=True,
        comment='品牌ID，关联brands表'
    )
    room_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("live_rooms.id", ondelete="CASCADE"), 
        nullable=False,
        primary_key=True,
        comment='直播间ID，关联live_rooms表（live_rooms表定义见v6主文档）'
    )
    
    # 时间戳
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    
    # 索引定义
    __table_args__ = (
        Index('idx_brand_rooms_brand_id', 'brand_id'),
        Index('idx_brand_rooms_room_id', 'room_id'),
    )
    
    # 关联关系
    brand = relationship("Brand", back_populates="rooms")
    # 注意：LiveRoom模型由v6主文档定义，这里不定义relationship，避免循环导入
    
    def __repr__(self):
        return f"<BrandRoom(brand_id={self.brand_id}, room_id={self.room_id})>"
