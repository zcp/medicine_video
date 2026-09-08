"""
用户偏好与通知模块 - SQLAlchemy ORM模型

本模块包含用户偏好设置和通知系统的数据库模型定义。
"""

import uuid
from sqlalchemy import Column, String, Boolean, Text, Time, TIMESTAMP, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.database import Base


class UserPreferences(Base):
    """用户个性化偏好设置模型"""
    __tablename__ = "user_preferences"
    
    # 核心标识（在应用层生成UUID）
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="主键ID")
    
    # 用户关联（一对一关系）
    user_id = Column(
        UUID(as_uuid=True), 
        nullable=False, 
        unique=True,
        comment="用户公开ID（users.public_id），应用层验证，JWT Token的user_id字段值"
    )
    
    # 昼夜模式设置
    theme_mode = Column(
        String(20), 
        nullable=False, 
        default="auto",
        comment="昼夜模式：auto=跟随系统, light=浅色, dark=深色, scheduled=定时切换"
    )
    theme_scheduled_dark_time = Column(
        Time, 
        nullable=True,
        comment="定时深色模式开始时间（定时切换时使用）"
    )
    theme_scheduled_light_time = Column(
        Time, 
        nullable=True,
        comment="定时浅色模式开始时间（定时切换时使用）"
    )
    
    # 科室星标固定
    pinned_categories = Column(
        JSONB, 
        nullable=True,
        comment='JSONB数组，存储用户固定的科室ID（最多5个），格式：["uuid1", "uuid2", ...]'
    )
    
    # 视图模式
    homepage_view_mode = Column(
        String(20), 
        nullable=False, 
        default="double",
        comment="首页视图模式：double=双列瀑布流, single=单列列表"
    )
    
    # 网络与流量设置
    cellular_warning_enabled = Column(
        Boolean, 
        nullable=False, 
        default=True,
        comment="是否启用流量提醒"
    )
    auto_reduce_quality = Column(
        Boolean, 
        nullable=False, 
        default=True,
        comment="流量下自动降画质"
    )
    auto_play_on_wifi = Column(
        Boolean, 
        nullable=False, 
        default=False,
        comment="WiFi下自动播放"
    )
    
    # 其他偏好设置（可扩展）
    extra = Column(
        JSONB, 
        nullable=True,
        comment="JSONB格式存储其他扩展偏好设置"
    )
    
    # 时间戳（使用TIMESTAMPTZ + server_default）
    created_at = Column(
        TIMESTAMP(timezone=True), 
        nullable=False, 
        server_default=func.now(),
        comment="创建时间"
    )
    updated_at = Column(
        TIMESTAMP(timezone=True), 
        nullable=False, 
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间"
    )
    
    # 索引和约束
    __table_args__ = (
        Index("idx_user_preferences_user_id", "user_id"),
        {"comment": "用户个性化偏好设置表，存储用户的前端偏好配置"}
    )
    
    def __repr__(self) -> str:
        """字符串表示（不暴露敏感信息）"""
        return f"<UserPreferences(id={str(self.id)[:8]}, user_id={str(self.user_id)[:8]}, theme_mode={self.theme_mode})>"


class Notification(Base):
    """用户通知模型"""
    __tablename__ = "notifications"
    
    # 核心标识（在应用层生成UUID）
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="主键ID")
    
    # 用户关联
    user_id = Column(
        UUID(as_uuid=True), 
        nullable=False,
        comment="接收通知的用户ID（users.public_id），应用层验证"
    )
    
    # 通知内容
    title = Column(
        String(255), 
        nullable=False,
        comment="通知标题"
    )
    content = Column(
        Text, 
        nullable=True,
        comment="通知内容"
    )
    notification_type = Column(
        String(50), 
        nullable=False, 
        default="system",
        comment="通知类型：system=系统通知, subscription=订阅通知, interaction=互动通知"
    )
    
    # 关联资源（可选）
    related_id = Column(
        UUID(as_uuid=True), 
        nullable=True,
        comment="关联资源ID（如：room_id, session_id, expert_id等）"
    )
    related_type = Column(
        String(50), 
        nullable=True,
        comment="关联资源类型（如：room, session, expert, brand等）"
    )
    
    # 已读状态
    is_read = Column(
        Boolean, 
        nullable=False, 
        default=False,
        comment="是否已读：false=未读, true=已读"
    )
    
    # 时间戳（仅创建时间，通知不可修改）
    created_at = Column(
        TIMESTAMP(timezone=True), 
        nullable=False, 
        server_default=func.now(),
        comment="创建时间"
    )
    
    # 索引和约束
    __table_args__ = (
        Index("idx_notifications_user_id", "user_id"),
        Index("idx_notifications_user_is_read", "user_id", "is_read"),
        Index("idx_notifications_created_at", "created_at"),
        {"comment": "用户通知表，存储系统通知、订阅提醒、互动通知等"}
    )
    
    def __repr__(self) -> str:
        """字符串表示（不暴露敏感信息）"""
        return f"<Notification(id={str(self.id)[:8]}, user_id={str(self.user_id)[:8]}, type={self.notification_type}, is_read={self.is_read})>"
