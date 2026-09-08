---
# SQLAlchemy模型 (`models`) 与Pydantic模型 (`schemas`) 一致性验证指令

## 一、验证目标与核心原则

### 1.1. 验证目标
本次任务的目标是，验证 `schemas/download.py` (API数据契约层) 和 `models/download.py` (数据库持久化层) 之间的**逻辑等价性与兼容性**。找出两者之间真正存在冲突或遗漏的“不合理”的不一致之处。

### 1.2. 核心映射原则 (重要)
由于 SQLAlchemy 和 Pydantic 的用途和语法不同，以下差异是**合理且预期的**，不应被报告为错误：

-   **类型映射**:
    -   `Column(String(x))` (models) **等价于** `str` 类型和 `Field(max_length=x)` (schemas)。
    -   `Column(Integer)` / `Column(BigInteger)` **等价于** `int`。
    -   `Column(Float)` **等价于** `float`。
    -   `Column(Text)` **等价于** `str` (无长度限制)。
    -   `Column(UUID(...))` **等价于** `pydantic.UUID4`。
    -   `Column(..., nullable=True)` **等价于** `Optional[...]` 或 `| None`。
    -   `Column(..., nullable=False)` **等价于** 必填字段 (非`Optional`)。
-   **约束映射**:
    -   数据库的 `CheckConstraint` 在 Pydantic 中通常通过 `Enum` 或自定义的 `@validator` 来实现。
-   **关系映射**:
    -   SQLAlchemy 的 `relationship()` 在 Pydantic 中没有直接对应。在用于API输出的`schema`中，它通常被定义为一个**嵌套的Pydantic模型**；在用于输入的`schema`中，它可能只是一个外键ID字段 (如 `task_id: UUID4`)。验证时应关注其逻辑表达是否正确，而非语法一致。

---

## 二、待验证文件内容
*(此部分用于粘贴您的代码)*

### 2.1. `models/download.py` (SQLAlchemy 模型)
```python
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
    video_id = Column(UUID(as_uuid=True), nullable=False)
    liveroom_id = Column(String(20), nullable=False, comment="直播间ID")
    liveroom_title = Column(String(255), nullable=True, comment="直播间标题")
    liveroom_url = Column(String(255), nullable=True, comment="直播间URL")
    video_url = Column(String(255), nullable=False, comment="视频播放URL")
    video_type = Column(String(20), nullable=False, comment="hls, mp4")
    status = Column(
        String(20),
        nullable=False,
        default='pending',
        comment="pending, processing, completed, failed"
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
        Index("idx_download_tasks_created_at", "created_at")
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
    resource_type = Column(
        String(20),
        nullable=False,
        default='ts',
        comment="枚举值: 'ts', 'mp4', 'image'"
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
            "resource_type IN ('ts', 'mp4', 'image')",
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
    video_id = Column(UUID(as_uuid=True), nullable=False)
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
    download_task_id = Column(
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
        UniqueConstraint('video_id', 'liveroom_id', name='uq_video_id_liveroom_id'),

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
        Index("idx_downloaded_videos_download_task_id", "download_task_id"),
        Index("idx_downloaded_videos_created_at", "created_at")
    )

    def __repr__(self):
        return f"<DownloadedVideo(id={self.id}, video_id={self.video_id})>" 
```

### 2.2. `schemas/download.py` (Pydantic 模型)
```python
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, HttpUrl, constr, validator
from enum import Enum

class DownloadStatus(str, Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"

class DownloadTaskBase(BaseModel):
    """下载任务基础模型"""
    video_id: UUID = Field(..., description="视频的唯一标识ID (UUID)")
    liveroom_id: constr(min_length=10, max_length=20) = Field(..., description="直播间ID")
    liveroom_title: Optional[str] = Field(None, max_length=255, description="直播间标题")
    liveroom_url: Optional[HttpUrl] = Field(None, description="直播间URL")
    video_url: HttpUrl = Field(..., description="视频播放URL")
    video_type: constr(regex=r'^(hls|mp4)$') = Field(..., description="hls, mp4")

class DownloadTaskCreate(DownloadTaskBase):
    """创建下载任务请求模型"""
    pass

class DownloadTaskUpdate(BaseModel):
    """更新下载任务请求模型"""
    status: Optional[constr(regex=r'^(pending|processing|completed|partial_completed|failed|cancelled)$')] = None
    progress: Optional[float] = Field(None, ge=0, le=1)
    retry_count: Optional[int] = Field(None, ge=0)
    last_error: Optional[str] = None
    completed_at: Optional[datetime] = None

class DownloadFailureBase(BaseModel):
    """下载失败记录基础模型"""
    resource_url: HttpUrl = Field(..., description="原始资源地址（URL）")
    expected_path: str = Field(..., description="希望保存的路径（用于重试时定位）")
    resource_type: constr(regex=r'^(ts|mp4|image)$') = Field('ts', description="枚举值: 'ts', 'mp4', 'image'")
    failure_type: constr(regex=r'^(network_error|timeout|invalid_content|storage_error|permission_error)$') = Field(
        ..., description="network_error, timeout, invalid_content, storage_error, permission_error"
    )
    error_message: str = Field(..., description="错误信息")
    retry_count: int = Field(0, ge=0, le=3, description="重试次数")
    next_retry_time: Optional[datetime] = Field(None, description="下次重试时间")
    status: constr(regex=r'^(pending|retrying|abandoned)$') = Field('pending', description="pending, retrying, abandoned")

class DownloadFailureCreate(DownloadFailureBase):
    """创建下载失败记录请求模型"""
    task_id: UUID = Field(..., description="关联的下载任务ID")

class DownloadedVideoBase(BaseModel):
    """已下载视频基础模型"""
    video_id: UUID = Field(..., description="视频的唯一标识ID (UUID)")
    liveroom_id: constr(min_length=10, max_length=20) = Field(..., description="直播间ID")
    liveroom_title: Optional[str] = Field(None, max_length=255, description="直播间标题")
    liveroom_url: Optional[HttpUrl] = Field(None, description="直播间URL")
    video_type: constr(regex=r'^(hls|mp4)$') = Field(..., description="hls, mp4")
    video_url: HttpUrl = Field(..., description="原始视频URL")
    storage_path: str = Field(..., max_length=255, description="存储路径，遵循存储目录结构规范")
    file_size: Optional[int] = Field(None, ge=0, description="文件大小（字节）")
    duration: Optional[int] = Field(None, ge=0, description="视频时长（秒）")
    resolution: Optional[str] = Field(None, max_length=20, description="视频分辨率")
    format: Optional[str] = Field(None, max_length=20, description="视频格式")
    cover_url: Optional[HttpUrl] = Field(None, description="封面图片URL")
    cover_path: Optional[str] = Field(None, max_length=255, description="封面图片存储路径")
    status: constr(regex=r'^(completed|partial_completed|failed)$') = Field(..., description="状态：completed, partial_completed, failed")
    download_start_time: Optional[datetime] = Field(None, description="开始下载时间")
    download_end_time: Optional[datetime] = Field(None, description="完成下载时间")

class DownloadedVideoCreate(DownloadedVideoBase):
    """创建已下载视频记录请求模型"""
    download_task_id: Optional[UUID] = Field(None, description="关联的下载任务ID")

class DownloadTaskResponse(DownloadTaskBase):
    """下载任务响应模型"""
    id: UUID
    status: constr(regex=r'^(pending|processing|completed|partial_completed|failed|cancelled)$')
    progress: float = Field(0, ge=0, le=1)
    retry_count: int = Field(0, ge=0)
    last_error: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class DownloadFailureResponse(DownloadFailureBase):
    """下载失败记录响应模型"""
    id: UUID
    task_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class DownloadedVideoResponse(DownloadedVideoBase):
    """已下载视频响应模型"""
    id: UUID
    download_task_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class DownloadTaskDetail(DownloadTaskResponse):
    """下载任务详情响应模型"""
    failures: List[DownloadFailureResponse] = []
    video: Optional[DownloadedVideoResponse] = None

    class Config:
        orm_mode = True

class DownloadTaskList(BaseModel):
    """下载任务列表响应模型"""
    total: int
    items: List[DownloadTaskResponse]

class DownloadFailureList(BaseModel):
    """下载失败记录列表响应模型"""
    total: int
    items: List[DownloadFailureResponse]

class DownloadedVideoList(BaseModel):
    """已下载视频列表响应模型"""
    total: int
    items: List[DownloadedVideoResponse]

class DownloadFailureUpdate(BaseModel):
    """更新下载失败记录请求模型"""
    retry_count: Optional[int] = Field(None, ge=0, le=3)
    next_retry_time: Optional[datetime] = None
    status: Optional[constr(regex=r'^(pending|retrying|abandoned)$')] = None

class DownloadedVideoUpdate(BaseModel):
    """更新已下载视频记录请求模型"""
    file_size: Optional[int] = Field(None, ge=0)
    duration: Optional[int] = Field(None, ge=0)
    resolution: Optional[str] = Field(None, max_length=20)
    format: Optional[str] = Field(None, max_length=20)
    cover_url: Optional[HttpUrl] = None
    cover_path: Optional[str] = Field(None, max_length=255)
    status: Optional[constr(regex=r'^(completed|partial_completed|failed)$')] = None
    download_end_time: Optional[datetime] = None 
```

---

## 三、详细验证清单

请根据 **1.2节的核心映射原则**，检查以下各项的一致性：

### 3.1. 枚举类型一致性：
-   检查所有在两个文件中都存在的枚举类（如 `TaskStatus` 等）其成员和值是否完全相同。

### 3.2. 字段定义一致性：
-   检查共享的核心字段名是否完全一致（忽略仅存在于某一层的字段，如 `relationship`）。
-   检查字段类型是否**遵循映射规则**。
-   检查 Pydantic 模型中的字段 `default` 值是否与 `models` 中的 `default` 逻辑等价。
-   检查 Pydantic `Field` 的约束（如`max_length`）是否与 `Column` 的类型参数（如`String(50)`）匹配。

### 3.3. 关系定义一致性：
-   检查在`schemas`中代表外键关系的字段（如`task_id: UUID4`）其类型是否与`models`中主键的类型匹配。
-   检查在用于API响应的`schemas`中，代表嵌套资源的字段是否正确地使用了另一个Pydantic模型来表达`relationship`。

### 3.4. 验证规则一致性：
-   检查 Pydantic 中的 `@validator` 或 `Enum` 是否正确地反映了数据库中的 `CheckConstraint` 逻辑。

### 3.5. 模型结构一致性：
-   检查 Pydantic 模型的 `Config` 或 `model_config` 中 `from_attributes` (或`orm_mode`) 是否为 `True`，以确保与SQLAlchemy模型的兼容性。

---

## 四、输出格式要求

请详细列出所有**不符合映射原则或逻辑上不匹配**的地方，包括：
1.  **具体模型/枚举**: 指出不一致发生的类名。
2.  **具体字段/值**: 指出不一致的字段名。
3.  **差异描述**: 清晰地描述 `models.py` 和 `schemas.py` 中的差异所在。
4.  **修正建议**: 基于逻辑等价的原则，提出具体的修改方案。

如果所有内容均逻辑等价且兼容，请明确指出：“经详细比对，`schemas/download.py` 和 `models/download.py` 在核心功能上保持了良好的逻辑一致性和兼容性，未发现关键冲突。”