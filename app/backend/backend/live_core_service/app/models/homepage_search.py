"""
首页与搜索模块的数据库模型

本模块包含首页与搜索模块所需的 SQLAlchemy 模型类：
- FeaturedContent: 首页精选/焦点图表
"""
import uuid
from datetime import datetime

# SQLAlchemy 核心导入
from sqlalchemy import Column, String, Integer, Boolean, Index, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database import Base  # 注意：Base 在 database.py 中，不是 models/base.py


class FeaturedContent(Base):
    """
    首页精选/焦点图内容配置表
    
    用于首页轮播Banner展示，支持运营配置和定时上下线
    """
    __tablename__ = "featured_content"
    
    # 核心标识 (在应用层通过 uuid.uuid4() 生成)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 业务字段
    title = Column(String(255), nullable=False, comment='焦点图标题')
    subtitle = Column(String(512), nullable=True, comment='焦点图副标题（可选）')
    image_url = Column(String(512), nullable=False, comment='焦点图图片URL')
    target_type = Column(String(50), nullable=True, comment='目标类型：room/session/topic/brand/external等')
    target_id = Column(UUID(as_uuid=True), nullable=True, comment='目标ID，根据target_type指向对应表的id（应用层关联，不设置外键）')
    target_url = Column(String(512), nullable=True, comment='外部链接，优先级高于target_id')
    sort_order = Column(Integer, default=0, nullable=False, comment='排序权重，数字越小越靠前')
    is_active = Column(Boolean, default=True, nullable=False, comment='是否启用：true=可见，false=已下线')
    start_at = Column(TIMESTAMP(timezone=True), nullable=True, comment='上线时间，为空表示立即上线')
    end_at = Column(TIMESTAMP(timezone=True), nullable=True, comment='下线时间，为空表示永久有效')
    
    # 时间戳 - 使用 server_default 和 func.now()
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # 索引定义
    __table_args__ = (
        Index('idx_featured_content_active_sort', 'is_active', 'sort_order'),
        Index('idx_featured_content_schedule', 'start_at', 'end_at'),
    )
    
    def __repr__(self):
        return f"<FeaturedContent(id={self.id}, title={self.title})>"
