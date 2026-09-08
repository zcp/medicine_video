from datetime import datetime
from uuid import uuid4
from sqlalchemy import (
    Column, String, Integer, DateTime, ForeignKey, Enum, 
    Text, Float, BigInteger, CheckConstraint, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class DownloadTask(Base):
    """下载任务表"""
    __tablename__ = "download_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, comment="用户ID，关联到用户服务")
    video_id = Column(UUID(as_uuid=True), nullable=False, comment="视频ID，格式：UUID")
    liveroom_id = Column(String(20), nullable=False, comment="直播间ID")
    liveroom_title = Column(String(255), nullable=True, comment="直播间标题")
    liveroom_url = Column(String(255), nullable=True, comment="直播间URL")
    resource_url = Column(String(255), nullable=False, comment="视频播放URL或图片URL")
    resource_type = Column(String(20), nullable=False, comment="image,hls, mp4")
    status = Column(
        String(20),
        nullable=False,
        default='pending',
        comment="pending, processing, completed, partial_completed,failed, cancelled"
    )
    progress = Column(Float, nullable=False, default=0, comment="下载进度（0-1）")
    retry_count = Column(Integer, nullable=False, default=0, comment="重试次数")
    last_error = Column(Text, nullable=True, comment="最后错误信息")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    completed_at = Column(DateTime, nullable=True, comment="完成下载时间")

    # 关系
    failures = relationship("DownloadFailure", back_populates="task", cascade="all, delete-orphan")
    video = relationship("DownloadedVideo", back_populates="task", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        # 约束
        CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'partial_completed', 'failed', 'cancelled')",
            name="check_status"
        ),
        CheckConstraint(
            "progress >= 0 AND progress <= 1",
            name="check_progress_range"
        ),
        # 索引
        Index("idx_download_tasks_video_id", "video_id"),
        Index("idx_download_tasks_liveroom_id", "liveroom_id"),
        Index("idx_download_tasks_status", "status"),
        Index("idx_download_tasks_created_at", "created_at"),
        Index("idx_download_tasks_user_id", "user_id")
    )

    def __repr__(self):
        return f"<DownloadTask(id={self.id}, status={self.status})>"

class DownloadFailure(Base):
    """下载失败记录表"""
    __tablename__ = "download_failures"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("download_tasks.id", ondelete="CASCADE"), nullable=False)
    resource_url = Column(Text, nullable=False, comment="原始资源地址（URL）")
    expected_path = Column(Text, nullable=False, comment="希望保存的路径（用于重试时定位）")
    standard_name = Column(Text, nullable=False, comment="下载ts或mp4的标准名字，符合指定存储规范")
    resource_type = Column(
        String(20),
        nullable=False,
        default='ts',
        comment="枚举值: 'm3u8', 'ts', 'mp4', 'image'"
    )
    failure_type = Column(
        String(50),
        nullable=False,
        comment="network_error, timeout, invalid_content, storage_error, permission_error"
    )
    error_message = Column(Text, nullable=False, comment="错误信息")
    retry_count = Column(Integer, nullable=False, default=0, comment="重试次数")
    next_retry_time = Column(DateTime, nullable=True, comment="下次重试时间")
    status = Column(
        String(20),
        nullable=False,
        default='pending',
        comment="pending, retrying, abandoned"
    )
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关系
    task = relationship("DownloadTask", back_populates="failures")

    __table_args__ = (
        # 约束
        CheckConstraint(
            "retry_count >= 0 AND retry_count <= 3",
            name="check_retry_count_range"
        ),
        CheckConstraint(
            "resource_type IN ('m3u8', 'ts', 'mp4', 'image')",
            name="check_resource_type"
        ),
        CheckConstraint(
            "failure_type IN ('network_error', 'timeout', 'invalid_content', 'storage_error', 'permission_error')",
            name="check_failure_type"
        ),
        CheckConstraint(
            "status IN ('pending', 'retrying', 'abandoned')",
            name="check_failure_status"
        ),
        # 索引
        Index("idx_download_failures_task_id", "task_id"),
        Index("idx_download_failures_status", "status"),
        Index("idx_download_failures_next_retry_time", "next_retry_time")
    )

    def __repr__(self):
        return f"<DownloadFailure(id={self.id}, failure_type={self.failure_type})>"

class DownloadedVideo(Base):
    """已下载视频表"""
    __tablename__ = "downloaded_videos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    video_id = Column(UUID(as_uuid=True), nullable=False, comment="视频ID，格式：{liveroom_id}_{uuid4后缀}")
    liveroom_id = Column(String(20), nullable=False, comment="直播间ID")
    liveroom_title = Column(String(255), nullable=True, comment="直播间标题")
    liveroom_url = Column(String(255), nullable=True, comment="直播间URL")
    video_type = Column(String(20), nullable=False, comment="hls, mp4")
    video_url = Column(String(255), nullable=False, comment="原始视频URL")
    storage_path = Column(String(255), nullable=False, comment="存储路径，遵循存储目录结构规范")
    file_size = Column(BigInteger, nullable=True, comment="文件大小（字节）")
    duration = Column(Integer, nullable=True, comment="视频时长（秒）")
    resolution = Column(String(20), nullable=True, comment="视频分辨率")
    format = Column(String(20), nullable=True, comment="视频格式")
    cover_url = Column(String(255), nullable=True, comment="封面图片URL")
    cover_path = Column(String(255), nullable=True, comment="封面图片存储路径")
    task_id = Column(
        UUID(as_uuid=True),
        ForeignKey("download_tasks.id", ondelete="SET NULL"),
        nullable=True,
        comment="关联的下载任务ID"
    )
    status = Column(
        String(20),
        nullable=False,
        comment="状态：completed, partial_completed, failed"
    )
    download_start_time = Column(DateTime, nullable=True, comment="开始下载时间")
    download_end_time = Column(DateTime, nullable=True, comment="完成下载时间")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关系
    task = relationship("DownloadTask", back_populates="video")

    __table_args__ = (
        # 约束
        UniqueConstraint('video_id', 'storage_path', name='uq_video_id_storage_path'),
        CheckConstraint(
            "video_type IN ('hls', 'mp4')",
            name="check_video_type"
        ),
        CheckConstraint(
            "status IN ('completed', 'partial_completed', 'failed')",
            name="check_video_status"
        ),
        # 索引
        Index("idx_downloaded_videos_video_id", "video_id"),
        Index("idx_downloaded_videos_liveroom_id", "liveroom_id"),
        Index("idx_downloaded_videos_status", "status"),
        Index("idx_downloaded_videos_task_id", "task_id"),
        Index("idx_downloaded_videos_created_at", "created_at")
    )

    def __repr__(self):
        return f"<DownloadedVideo(id={self.id}, video_id={self.video_id})>" 