"""
专家模块模型定义
包含专家信息、用户关注、场次专家关联的模型
"""

import uuid
import enum
from sqlalchemy import Column, String, Integer, Boolean, Text, ForeignKey, UniqueConstraint, Index, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class SessionExpertRole(str, enum.Enum):
    """专家角色枚举"""
    MAIN_SPEAKER = "主讲"
    HOST = "主持"
    GUEST = "嘉宾"


class Expert(Base):
    """
    平台专家信息表（外部专家+内部用户专家）
    """
    __tablename__ = "experts"
    
    # 核心标识 (在应用层通过 uuid.uuid4() 生成)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment='主键UUID，在应用层通过uuid.uuid4()生成')
    
    # user_id为可选关联，关联平台用户
    user_id = Column(
        UUID(as_uuid=True), 
        nullable=True, 
        unique=True, 
        comment='关联平台用户公开ID（users.public_id），可为空表示外部专家（未绑定平台账号），应用层验证'
    )
    
    # 基本信息
    name = Column(String(120), nullable=False, comment='专家姓名')
    title = Column(String(120), nullable=True, comment='职称（如：主任医师、教授）')
    hospital = Column(String(200), nullable=True, comment='所属医院')
    # 过渡期保留文本列；权威为 department_id + expert_departments
    department = Column(String(120), nullable=True, comment='科室（过渡兼容字段，优先回填词表名）')
    department_id = Column(
        UUID(as_uuid=True),
        ForeignKey("expert_departments.id", ondelete="SET NULL"),
        nullable=True,
        comment='关联 expert_departments.id，标准化科室',
    )
    expertise_areas = Column(Text, nullable=True, comment='擅长领域，逗号分隔或JSON字符串')
    bio = Column(Text, nullable=True, comment='个人简介')
    avatar_url = Column(String(512), nullable=True, comment='头像URL')
    # 过渡期可空；由科室词表推导缓存
    category_id = Column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        comment='专家主专业分类缓存列，关联 categories.id',
    )
    
    # 业务字段
    is_featured = Column(Boolean, default=False, nullable=False, comment='是否为首页推荐专家')
    is_active = Column(Boolean, default=True, nullable=False, comment='是否启用（false 表示软删除/下架）')
    sort_order = Column(Integer, default=0, nullable=False, comment='排序顺序')
    contact_info = Column(JSONB, nullable=True, comment='JSONB格式存储联系方式：{phone, email, office}')
    
    # 时间戳
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), comment='创建时间')
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now(), comment='更新时间')
    
    # 索引定义
    __table_args__ = (
        Index('idx_experts_is_featured', 'is_featured', 'sort_order'),
        Index('idx_experts_is_active', 'is_active'),
        Index('idx_experts_user_id', 'user_id'),
        Index('idx_experts_department_id', 'department_id'),
        Index('idx_experts_category_id', 'category_id'),
    )
    
    # 关系定义
    # 一对多关系：专家 -> 用户关注记录
    user_expert_subscriptions = relationship("UserExpertSubscription", back_populates="expert", cascade="all, delete-orphan")
    # 一对多关系：专家 -> 场次专家关联记录
    live_session_experts = relationship("LiveSessionExpert", back_populates="expert", cascade="all, delete-orphan")
    category = relationship("Category", lazy="select")
    department_ref = relationship("ExpertDepartment", foreign_keys=[department_id], lazy="select")

    @property
    def department_name(self):
        """词表科室名（优先）；否则回退文本列"""
        if self.department_ref is not None:
            return self.department_ref.name
        return self.department

    @property
    def category_name(self):
        return self.category.name if self.category is not None else None
    
    def __repr__(self):
        return f"<Expert(id={self.id}, name={self.name})>"


class UserExpertSubscription(Base):
    """
    用户关注专家表（支持"我的关注"功能）
    """
    __tablename__ = "user_expert_subscriptions"
    
    # 核心标识 (在应用层通过 uuid.uuid4() 生成)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment='主键UUID，在应用层通过uuid.uuid4()生成')
    
    # 外键字段
    user_id = Column(
        UUID(as_uuid=True), 
        nullable=False, 
        comment='用户公开ID（users.public_id），应用层验证，JWT Token的user_id字段值'
    )
    expert_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("experts.id", ondelete="CASCADE"), 
        nullable=False, 
        comment='专家ID，关联experts表'
    )
    
    # 时间戳
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), comment='关注时间')
    
    # 关系定义
    expert = relationship("Expert", back_populates="user_expert_subscriptions")
    
    # 约束和索引定义
    __table_args__ = (
        UniqueConstraint('user_id', 'expert_id', name='uq_user_expert_subscriptions_user_expert'),
        Index('idx_user_expert_subscriptions_user_id', 'user_id'),
        Index('idx_user_expert_subscriptions_expert_id', 'expert_id'),
        Index('idx_user_expert_subscriptions_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<UserExpertSubscription(id={self.id}, user_id={self.user_id}, expert_id={self.expert_id})>"


class LiveSessionExpert(Base):
    """
    直播场次专家关联表（多对多关系），支持一个场次有多个专家（主讲、主持、嘉宾）
    """
    __tablename__ = "live_session_experts"
    
    # 核心标识 (在应用层通过 uuid.uuid4() 生成)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment='主键UUID，在应用层通过uuid.uuid4()生成')
    
    # 外键字段
    session_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("live_sessions.id", ondelete="CASCADE"), 
        nullable=False, 
        comment='直播场次ID，关联live_sessions表'
    )
    expert_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("experts.id", ondelete="CASCADE"), 
        nullable=False, 
        comment='专家ID，关联experts表'
    )
    
    # 业务字段
    role = Column(
        String(50), 
        nullable=False, 
        default=SessionExpertRole.MAIN_SPEAKER.value, 
        comment='专家角色：主讲、主持、嘉宾'
    )
    sort_order = Column(
        Integer, 
        nullable=False, 
        default=0, 
        comment='显示顺序（数值越大越靠前）'
    )
    
    # 时间戳
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), comment='关联创建时间')
    
    # 关系定义
    session = relationship("LiveSession", backref="live_session_experts")
    expert = relationship("Expert", back_populates="live_session_experts")
    
    # 约束和索引定义
    __table_args__ = (
        UniqueConstraint('session_id', 'expert_id', 'role', name='uq_live_session_experts_session_expert_role'),
        Index('idx_live_session_experts_session', 'session_id'),
        Index('idx_live_session_experts_expert', 'expert_id'),
        Index('idx_live_session_experts_role', 'session_id', 'role'),
    )
    
    def __repr__(self):
        return f"<LiveSessionExpert(id={self.id}, session_id={self.session_id}, expert_id={self.expert_id}, role={self.role})>"

