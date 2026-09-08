"""
SQLAlchemy 模型定义 - 用户功能服务
对应数据库表: users, membership_products, user_memberships
"""
import uuid
import enum
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, ForeignKey, 
    Integer, Numeric, SmallInteger, String, Text, 
    CheckConstraint, Index, UniqueConstraint, text
)
from sqlalchemy.dialects.postgresql import UUID, ENUM, INET
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


# ============================================================================
# 枚举类型定义 (Python Enums)
# ============================================================================

class UserRole(str, enum.Enum):
    """用户角色枚举"""
    REGULAR = "REGULAR"
    MODERATOR = "MODERATOR"
    ADMIN = "ADMIN"
    SUPERADMIN = "SUPERADMIN"


class EntityStatus(str, enum.Enum):
    """通用实体状态枚举"""
    NORMAL = "NORMAL"
    BANNED = "BANNED"
    DELETED = "DELETED"
    PENDING_REVIEW = "PENDING_REVIEW"
    REJECTED = "REJECTED"


class MembershipProductStatus(str, enum.Enum):
    """会员产品状态枚举"""
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ARCHIVED = "ARCHIVED"


class MembershipStatus(str, enum.Enum):
    """用户会员订阅状态枚举"""
    PENDING_PAYMENT = "PENDING_PAYMENT"
    ACTIVE = "ACTIVE"
    PAST_DUE = "PAST_DUE"
    EXPIRED = "EXPIRED"
    UPGRADED = "UPGRADED"
    REFUNDED = "REFUNDED"


# ============================================================================
# SQLAlchemy 模型定义
# ============================================================================

class User(Base):
    """用户核心表 - 对应数据库表 users"""
    __tablename__ = "users"

    # 主键和唯一标识
    id = Column(BigInteger, primary_key=True, comment="【内部ID】主键，仅用于数据库内部关联")
    public_id = Column(
        UUID(as_uuid=True), 
        nullable=False, 
        unique=True, 
        default=uuid.uuid4,
        comment="【公开ID】对外暴露的唯一标识符，用于API等"
    )
    
    # 登录凭证
    username = Column(String(50), nullable=False, unique=True)
    email = Column(String(255), unique=True)
    phone_number = Column(String(20), unique=True)
    password_hash = Column(String(255))
    
    # 用户信息
    nickname = Column(String(50), nullable=False)
    avatar_url = Column(String(512))
    bio = Column(Text)
    
    # 角色和状态
    role = Column(
        ENUM(UserRole, name="user_role"), 
        nullable=False, 
        default=UserRole.REGULAR,
        comment="用户角色: REGULAR, MODERATOR, ADMIN, SUPERADMIN"
    )
    status = Column(
        ENUM(EntityStatus, name="entity_status"), 
        nullable=False, 
        default=EntityStatus.NORMAL,
        comment="用户状态: NORMAL, BANNED, DELETED, PENDING_REVIEW, REJECTED"
    )

    # PR 1B: 开播资格（与 role 正交；默认允许开播，can_stream=false 表示被管理员禁播）
    can_stream = Column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
        comment="是否拥有开播资格；默认允许，false 表示被管理员禁播；与 role 正交",
    )

    # 验证状态
    is_email_verified = Column(Boolean, nullable=False, default=False)
    is_phone_verified = Column(Boolean, nullable=False, default=False)
    
    # 登录记录
    last_login_at = Column(DateTime(timezone=True))
    last_login_ip = Column(INET)
    
    # 社交登录
    social_provider = Column(String(20))
    social_id = Column(String(255))
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # 关系定义
    memberships = relationship("UserMembership", back_populates="user", cascade="all, delete-orphan")
    
    # 约束定义
    __table_args__ = (
        CheckConstraint(
            "(password_hash IS NOT NULL) OR (social_provider IS NOT NULL AND social_id IS NOT NULL)",
            name="users_login_method_check"
        ),
        Index("idx_users_social_login", "social_provider", "social_id", unique=True),
        Index(
            "idx_users_can_stream",
            "can_stream",
            postgresql_where=text("can_stream = FALSE"),
        ),
    )


class MembershipProduct(Base):
    """可供售卖的会员产品目录表 - 对应数据库表 membership_products"""
    __tablename__ = "membership_products"

    # 主键
    code = Column(
        String(50), 
        primary_key=True,
        comment="产品唯一编码 (e.g., VIDEO_YEARLY), 也是外键"
    )
    
    # 产品信息
    name = Column(String(100), nullable=False)
    description = Column(Text)
    sort_order = Column(Integer, nullable=False, default=0)
    
    # 价格和等级
    price = Column(Numeric(10, 2), nullable=False)
    level = Column(SmallInteger, nullable=False, default=1)
    
    # 时长配置
    duration_unit = Column(String(10), nullable=False)
    duration_value = Column(Integer, nullable=False)
    
    # 状态
    status = Column(
        ENUM(MembershipProductStatus, name="membership_product_status"), 
        nullable=False, 
        default=MembershipProductStatus.DRAFT
    )
    
    # 支付网关
    payment_gateway_price_id = Column(String(255))
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # 关系定义
    user_memberships = relationship("UserMembership", back_populates="product")


class UserMembership(Base):
    """用户会员状态与历史表 - 对应数据库表 user_memberships"""
    __tablename__ = "user_memberships"

    # 主键和唯一标识
    id = Column(BigInteger, primary_key=True)
    public_id = Column(
        UUID(as_uuid=True), 
        nullable=False, 
        unique=True, 
        default=uuid.uuid4,
        comment="【公开ID】对外暴露的唯一标识符，用于API等"
    )
    
    # 外键关联
    user_id = Column(
        BigInteger, 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False
    )
    product_code = Column(
        String(50), 
        ForeignKey("membership_products.code", ondelete="RESTRICT"), 
        nullable=False
    )
    
    # 交易信息
    transaction_id = Column(String(255), unique=True)
    
    # 会员等级和状态
    level = Column(
        SmallInteger, 
        nullable=False, 
        default=1,
        comment="购买时产品的等级快照，用于历史数据不变性"
    )
    status = Column(
        ENUM(MembershipStatus, name="membership_status"), 
        nullable=False, 
        default=MembershipStatus.PENDING_PAYMENT
    )
    
    # 续费设置
    is_auto_renew = Column(Boolean, nullable=False, default=False)
    
    # 管理员备注
    admin_notes = Column(Text, comment="管理员手动操作备注，用于审计")
    
    # 时间范围
    start_date = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # 关系定义
    user = relationship("User", back_populates="memberships")
    product = relationship("MembershipProduct", back_populates="user_memberships")
    
    # 索引和约束定义
    __table_args__ = (
        Index("idx_user_memberships_user_id", "user_id"),
        Index("idx_user_memberships_expires_at", "expires_at"),
        Index(
            "idx_user_memberships_one_active_per_product", 
            "user_id", 
            "product_code", 
            unique=True,
            postgresql_where=text("status IN ('ACTIVE', 'PAST_DUE')")
        ),
    ) 