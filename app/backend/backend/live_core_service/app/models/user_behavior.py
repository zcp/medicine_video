"""
用户行为模块的数据库模型

包括：
- 用户收藏表 user_favorites
- 观看历史表 watch_history
- 用户订阅提醒表 user_subscriptions
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import Enum as SAEnum, TIMESTAMP

from app.database import Base


class SubscriptionTargetType(str, enum.Enum):
    """订阅目标类型枚举"""

    ROOM = "room"      # 订阅房间
    SESSION = "session"  # 订阅单场次


class UserFavorite(Base):
    """
    用户收藏表

    用于记录用户收藏的直播间，使用软删除策略（is_active 字段）。
    """

    __tablename__ = "user_favorites"

    # 核心标识 (在应用层通过 uuid.uuid4() 生成)
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 用户ID（跨服务引用，应用层验证，不添加数据库外键）
    user_id = Column(
        PG_UUID(as_uuid=True),
        nullable=False,
        comment="用户公开ID（users.public_id），应用层验证，JWT Token的user_id字段值",
    )

    # 直播间ID（本服务内部表，使用外键）
    room_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            "live_rooms.id",
            name="fk_user_favorites_room_id",
            ondelete="CASCADE",
        ),
        nullable=False,
        comment="直播间ID，关联 live_rooms.id",
    )

    # 是否有效：true=已收藏，false=已取消（软删除）
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        comment="是否有效：true=已收藏，false=已取消（软删除）",
    )

    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="创建时间",
    )

    __table_args__ = (
        # 同一用户不能重复收藏同一房间
        UniqueConstraint(
            "user_id",
            "room_id",
            name="uq_user_favorites_user_room",
        ),
        Index("idx_user_favorites_user_id", "user_id"),
        Index("idx_user_favorites_room_id", "room_id"),
    )


class WatchHistory(Base):
    """
    观看历史表

    记录用户观看某个直播场次的进度和时间，仅关联 session_id。
    """

    __tablename__ = "watch_history"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(
        PG_UUID(as_uuid=True),
        nullable=False,
        comment="用户公开ID（users.public_id），应用层验证，JWT Token的user_id字段值",
    )

    # 直播场次 ID，关联 live_sessions.id
    session_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            "live_sessions.id",
            name="fk_watch_history_session_id",
            ondelete="CASCADE",
        ),
        nullable=False,
        comment="直播场次ID，关联 live_sessions.id",
    )

    # 观看进度（秒）
    progress = Column(
        Integer,
        nullable=True,
        comment="观看进度（秒），可为空表示仅记录打开行为",
    )

    watched_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="观看时间",
    )

    # 是否为该用户对该场次的最新观看记录
    is_latest = Column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        comment="是否为该用户该场次的最新观看记录",
    )

    __table_args__ = (
        Index("idx_watch_history_user_session", "user_id", "session_id"),
        Index("idx_watch_history_is_latest", "user_id", "is_latest"),
    )


class UserSubscription(Base):
    """
    用户订阅提醒表

    记录用户对房间或场次的订阅，用于开播提醒等功能。
    """

    __tablename__ = "user_subscriptions"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(
        PG_UUID(as_uuid=True),
        nullable=False,
        comment="用户公开ID（users.public_id），应用层验证，JWT Token的user_id字段值",
    )

    target_type = Column(
        SAEnum(SubscriptionTargetType, values_callable=lambda obj: [e.value for e in obj], name="subscription_target_type"),
        nullable=False,
        comment="订阅目标类型：room 或 session",
    )

    # 订阅目标ID（根据 target_type 指向 live_rooms.id 或 live_sessions.id）
    target_id = Column(
        PG_UUID(as_uuid=True),
        nullable=False,
        comment="目标ID，根据target_type指向live_rooms.id或live_sessions.id（应用层验证，不添加数据库外键）",
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        comment="是否仍然订阅：true=有效，false=取消（软删除）",
    )

    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="订阅创建时间",
    )

    __table_args__ = (
        # 唯一约束：同一用户对同一目标只能订阅一次
        UniqueConstraint(
            "user_id",
            "target_id",
            "target_type",
            name="uq_user_subscriptions_user_target",
        ),
        Index("idx_user_subscriptions_user_id", "user_id"),
    )

