"""
内容管理模块的数据库模型
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, ForeignKey, Boolean, Index, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, text

from app.database import Base  # 注意：Base 在 database.py 中，不是 models/base.py


class Tag(Base):
    """
    内容标签表

    用于标记直播内容，支持多对多关联到直播场次。
    使用软删除策略（is_active字段）。
    """
    __tablename__ = "tags"

    # 核心标识 (在应用层通过 uuid.uuid4() 生成)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 业务字段
    name = Column(String(80), nullable=False, unique=True, comment='标签名称，全局唯一')
    slug = Column(String(100), nullable=True, comment='URL友好的标识符，用于前端路由')
    description = Column(Text, nullable=True, comment='标签描述')
    is_active = Column(Boolean, nullable=False, default=True, comment='是否启用：true=可用，false=已隐藏（软删除）')

    # 【V2】用户自建溯源：区分运营词与用户 resolve 自建词，便于治理与审计
    created_by = Column(UUID(as_uuid=True), nullable=True, comment='创建者 public_id；Admin 手工创建可为 NULL')
    source = Column(
        String(16),
        nullable=False,
        default='admin',
        server_default='admin',
        comment='来源：admin=运营创建；user=用户 resolve 创建',
    )

    # 时间戳 - 使用 server_default 和 func.now()
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # 索引定义
    __table_args__ = (
        Index('idx_tags_name', 'name'),
        Index('idx_tags_is_active', 'is_active'),
        Index('idx_tags_source', 'source'),
        Index('idx_tags_created_by', 'created_by'),
    )

    # 关联关系
    session_tags = relationship("SessionTag", back_populates="tag", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Tag(id={self.id}, name={self.name})>"


class Category(Base):
    """
    全局医学科室/专业方向分类表

    用于提供结构化的医学科室/专业方向分类体系，供专家主分类和直播间医学方向分类共用。
    使用软删除策略（is_active字段）。
    """
    __tablename__ = "categories"

    # 核心标识 (在应用层通过 uuid.uuid4() 生成)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 业务字段
    name = Column(String(100), nullable=False,
                  comment='分类名称。唯一性由 V5 部分唯一索引保障：'
                         'uq_root_category_name (parent_id IS NULL) '
                         '+ uq_sub_category_name (parent_id IS NOT NULL, name)')
    display_name = Column(String(100), nullable=True,
                          comment='口语名（C端展示用，阶段6A V13 迁移新增）；NULL 回退 name')
    standard = Column(Boolean, nullable=False, default=True,
                      comment='标准科目标记（阶段6B V14 迁移新增）：true=name 须命中名录标准名；false=扩展科目')
    slug = Column(String(120), nullable=True, comment='URL友好的标识符')
    icon = Column(String(255), nullable=True, comment='分类图标名称或URL')
    description = Column(Text, nullable=True, comment='分类描述')
    sort_order = Column(Integer, nullable=False, default=0, comment='排序权重，数字越小越靠前，用于前端展示顺序')
    is_active = Column(Boolean, nullable=False, default=True, comment='是否启用：true=前端可见，false=已下线')

    # 层级关系（V5 迁移在数据库层创建列，P1 设计在 ORM 层映射）
    parent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=True,
        comment='父分类ID。NULL=根分类（一级科目）；非NULL=子分类（二级科目）'
    )

    # 时间戳 - 使用 server_default 和 func.now()
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # 自引用关系
    parent = relationship("Category", remote_side="Category.id", backref="children")

    # 索引定义
    __table_args__ = (
        Index('idx_categories_sort_order', 'sort_order'),
        Index('idx_categories_is_active', 'is_active'),
        Index('idx_categories_parent_id', 'parent_id'),
        # 部分唯一索引：同层分类名唯一（V5 迁移在 DB 层创建，此处 ORM 仅做映射）
        # uq_root_category_name: 根分类名全局唯一
        Index('uq_root_category_name', 'name', unique=True,
              postgresql_where=text("parent_id IS NULL")),
        # uq_sub_category_name: 同一父分类下子分类名唯一
        Index('uq_sub_category_name', 'parent_id', 'name', unique=True,
              postgresql_where=text("parent_id IS NOT NULL")),
    )

    # non-persistent helpers（CRUD 层动态填充）
    expert_count = 0
    room_count = 0

    def __repr__(self):
        return f"<Category(id={self.id}, name={self.name}, sort_order={self.sort_order})>"


class SessionTag(Base):
    """
    直播场次与标签的多对多关联表

    用于定义直播场次与标签的多对多关联关系。
    使用硬删除策略（直接DELETE）。
    """
    __tablename__ = "session_tags"

    # 复合主键
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("live_sessions.id", ondelete="CASCADE"),
        primary_key=True,
        comment='场次ID，关联live_sessions表'
    )
    tag_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
        comment='标签ID，关联tags表'
    )

    # 时间戳
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    # 索引定义
    __table_args__ = (
        Index('idx_session_tags_session_id', 'session_id'),
        Index('idx_session_tags_tag_id', 'tag_id'),
    )

    # 关联关系
    tag = relationship("Tag", back_populates="session_tags")
    session = relationship("LiveSession", foreign_keys=[session_id])

    def __repr__(self):
        return f"<SessionTag(session_id={self.session_id}, tag_id={self.tag_id})>"


class LiveRoomCategory(Base):
    """
    直播间与分类的多对多关联表

    用于定义直播间（live_rooms）与全局医学分类（categories）的多对多关联，是直播间分类的唯一业务来源。
    使用硬删除策略（直接 DELETE）。外键 ON DELETE CASCADE。
    """
    __tablename__ = "live_room_categories"

    # 复合主键
    room_id = Column(
        UUID(as_uuid=True),
        ForeignKey("live_rooms.id", ondelete="CASCADE"),
        primary_key=True,
        comment="直播间ID，关联 live_rooms 表",
    )
    category_id = Column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="CASCADE"),
        primary_key=True,
        comment="分类ID，关联 categories 表",
    )
    is_primary = Column(Boolean, nullable=False, default=False, comment="是否为主分类（规则尚未启用；启用前不得依赖该字段做业务判断）")
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        Index("idx_live_room_categories_room_id", "room_id"),
        Index("idx_live_room_categories_category_id", "category_id"),
    )

    category = relationship("Category", backref="live_room_categories")

    def __repr__(self):
        return f"<LiveRoomCategory(room_id={self.room_id}, category_id={self.category_id})>"
