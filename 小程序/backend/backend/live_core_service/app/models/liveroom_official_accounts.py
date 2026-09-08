"""
直播间与公众号关联模块的数据库模型
"""
import uuid
from sqlalchemy import Column, String, Text, Boolean, ForeignKey, Index, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base  # 注意：Base 在 database.py 中，不是 models/base.py


class OfficialAccount(Base):
    """
    公众号主表（CSM 维度）

    用于 CSM 场景下的租户/客户维度，与直播间多对多关联。
    使用软删除策略（is_active 字段）。
    """
    __tablename__ = "official_accounts"

    # 核心标识（应用层通过 uuid.uuid4() 生成）
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 业务字段
    name = Column(String(100), nullable=False, unique=True, comment="公众号名称，全局唯一")
    slug = Column(String(120), nullable=True, comment="URL 友好标识")
    app_id = Column(String(255), nullable=True, comment="预留：外部系统标识（如微信 app_id）")
    description = Column(String(500), nullable=True, comment="公众号描述")
    is_active = Column(Boolean, nullable=False, default=True, comment="是否启用；false 表示软删除")

    # 时间戳
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # 索引
    __table_args__ = (
        Index("idx_official_accounts_name", "name"),
        Index("idx_official_accounts_is_active", "is_active"),
    )

    # 关联关系
    live_room_official_accounts = relationship(
        "LiveRoomOfficialAccount",
        back_populates="official_account",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<OfficialAccount(id={self.id}, name={self.name})>"


class LiveRoomOfficialAccount(Base):
    """
    直播间与公众号的多对多关联表（CSM 维度）

    用于定义直播间（live_rooms）与公众号（official_accounts）的多对多关联。
    使用硬删除策略（直接 DELETE）。外键 ON DELETE CASCADE。
    """
    __tablename__ = "live_room_official_accounts"

    # 复合主键
    room_id = Column(
        UUID(as_uuid=True),
        ForeignKey("live_rooms.id", ondelete="CASCADE"),
        primary_key=True,
        comment="直播间 ID，关联 live_rooms 表",
    )
    account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("official_accounts.id", ondelete="CASCADE"),
        primary_key=True,
        comment="公众号 ID，关联 official_accounts 表",
    )
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        Index("idx_live_room_official_accounts_room_id", "room_id"),
        Index("idx_live_room_official_accounts_account_id", "account_id"),
    )

    official_account = relationship("OfficialAccount", back_populates="live_room_official_accounts")
    room = relationship("LiveRoom", backref="official_accounts")
