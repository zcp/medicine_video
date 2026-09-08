
---

# SQLAlchemy 模型与设计文档一致性验证指令

## 一、验证目标 (Validation Goal)

本次任务的核心目标是，**严格、逐一地比对** `app/models/download.py` 文件中定义的 SQLAlchemy 模型与 `@媒体下载服务设计文档v2.md` 第四章中定义的数据库 DDL，并报告两者之间是否存在任何不一致之处。

验证必须做到100%精确，覆盖表名、字段、类型、约束和索引等所有细节。

## 二、输入文件 (Input Files)

### 2.1. 数据库设计规范 (源文档)
- **源文件**: `@媒体下载服务设计文档v2.md`
- **对标章节**: 第四章、数据库设计

```sql
CREATE TABLE download_tasks (
    id UUID PRIMARY KEY,
    video_id UUID NOT NULL,          -- 视频ID，格式：uuid
    liveroom_id VARCHAR(20) NOT NULL,       -- 直播间ID
    liveroom_title VARCHAR(255),            -- 直播间标题
    liveroom_url VARCHAR(255),              -- 直播间URL
    video_url VARCHAR(255) NOT NULL,        -- 视频播放URL
    video_type VARCHAR(20) NOT NULL,        -- hls, mp4
    status VARCHAR(20) DEFAULT 'pending',   -- pending, processing, completed, failed
    progress FLOAT DEFAULT 0,               -- 下载进度（0-1）
    retry_count INT DEFAULT 0,              -- 重试次数
    last_error TEXT,                        -- 最后错误信息
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    -- CONSTRAINT video_id_format CHECK (video_id ~ '^[0-9]{10,16}_[a-f0-9]{4}$'),  -- 确保video_id符合命名规范
    CONSTRAINT check_status CHECK (status IN ('pending', 'processing', 'completed', 'partial_completed', 'failed', 'cancelled')),
    CONSTRAINT check_progress_range CHECK (progress >= 0 AND progress <= 1)
);

-- 索引设计
CREATE INDEX idx_download_tasks_video_id ON download_tasks(video_id);
CREATE INDEX idx_download_tasks_liveroom_id ON download_tasks(liveroom_id);
CREATE INDEX idx_download_tasks_status ON download_tasks(status);
CREATE INDEX idx_download_tasks_created_at ON download_tasks(created_at);
```

### 4.2 下载失败记录表（download_failures）
```sql
CREATE TABLE download_failures (
    id UUID PRIMARY KEY,
    task_id UUID REFERENCES download_tasks(id) ON DELETE CASCADE,
    resource_url TEXT NOT NULL,             -- 原始资源地址（URL）
    expected_path TEXT NOT NULL,            -- 希望保存的路径（用于重试时定位）
    resource_type VARCHAR(20) NOT NULL DEFAULT 'ts',  -- 枚举值: 'ts', 'mp4', 'image' 
    failure_type VARCHAR(50) NOT NULL,      -- network_error, timeout, invalid_content, storage_error, permission_error
    error_message TEXT NOT NULL,
    retry_count INT DEFAULT 0,
    next_retry_time TIMESTAMP,              -- 下次重试时间
    status VARCHAR(20) DEFAULT 'pending',   -- pending, retrying, abandoned
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_retry_count_range CHECK (retry_count >= 0 AND retry_count <= 3),
    CONSTRAINT check_resource_type CHECK (resource_type IN ('ts', 'mp4', 'image')),
    CONSTRAINT check_failure_type CHECK (failure_type IN ('network_error', 'timeout', 'invalid_content', 'storage_error', 'permission_error')),
    CONSTRAINT check_failure_status CHECK (status IN ('pending', 'retrying', 'abandoned'))
);

-- 索引设计
CREATE INDEX idx_download_failures_task_id ON download_failures(task_id);
CREATE INDEX idx_download_failures_status ON download_failures(status);
CREATE INDEX idx_download_failures_next_retry_time ON download_failures(next_retry_time);
```

### 4.3 下载视频数据表（downloaded_videos）
```sql
CREATE TABLE downloaded_videos (
    id UUID PRIMARY KEY,
    video_id UUID NOT NULL,          -- 视频ID，格式：uuid
    liveroom_id VARCHAR(20) NOT NULL,       -- 直播间ID
    liveroom_title VARCHAR(255),            -- 直播间标题
    liveroom_url VARCHAR(255),              -- 直播间URL
    video_type VARCHAR(20) NOT NULL,        -- hls, mp4
    video_url VARCHAR(255) NOT NULL,        -- 原始视频URL
    storage_path VARCHAR(255) NOT NULL,     -- 存储路径，遵循存储目录结构规范
    file_size BIGINT,                       -- 文件大小（字节）
    duration INT,                           -- 视频时长（秒）
    resolution VARCHAR(20),                 -- 视频分辨率
    format VARCHAR(20),                     -- 视频格式
    cover_url VARCHAR(255),                 -- 封面图片URL
    cover_path VARCHAR(255),                -- 封面图片存储路径
    download_task_id UUID REFERENCES download_tasks(id) ON DELETE SET NULL,  -- 关联的下载任务ID
    status VARCHAR(20) NOT NULL,            -- 状态：completed, partial_completed, failed
    download_start_time TIMESTAMP,          -- 开始下载时间
    download_end_time TIMESTAMP,            -- 完成下载时间
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(video_id, liveroom_id),          -- 确保同一视频在同一直播间只下载一次
    -- CONSTRAINT video_id_format CHECK (video_id ~ '^[0-9]{10,16}_[a-f0-9]{4}$'),  -- 确保video_id符合命名规范
    CONSTRAINT check_video_type CHECK (video_type IN ('hls', 'mp4')),
    CONSTRAINT check_video_status CHECK (status IN ('completed', 'partial_completed', 'failed'))
);

-- 索引设计
CREATE INDEX idx_downloaded_videos_video_id ON downloaded_videos(video_id);
CREATE INDEX idx_downloaded_videos_liveroom_id ON downloaded_videos(liveroom_id);
CREATE INDEX idx_downloaded_videos_status ON downloaded_videos(status);
CREATE INDEX idx_downloaded_videos_download_task_id ON downloaded_videos(download_task_id);
CREATE INDEX idx_downloaded_videos_created_at ON downloaded_videos(created_at);
```


### 2.2. 待验证的SQLAlchemy模型代码
- **源文件**: `app/models/download.py`

```python

class DownloadTask(Base):
    """下载任务表"""
    __tablename__ = "download_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    video_id = Column(UUID(as_uuid=True), nullable=False, comment="视频ID，格式：{liveroom_id}_{uuid4后缀}")
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
        #CheckConstraint(
        #    "video_id ~ '^[0-9]{10,16}_[a-f0-9]{4}$'",
        #    name="video_id_format"
        #),
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
        #CheckConstraint(
        #    "video_id ~ '^[0-9]{10,16}_[a-f0-9]{4}$'",
        #    name="video_id_format"
        #),
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

## 三、核心验证清单 (Core Validation Checklist)

请根据以下清单，对上述两个输入文件进行详细比对。

### 3.1. `download_tasks` 表 (`DownloadTask` 模型)
- **[ ] 表名**: `__tablename__` 是否为 `"download_tasks"`？
- **[ ] 字段一致性**:
    - `id`: 是否为 `Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)`？
    - `video_id`: 是否为 `Column(UUID(as_uuid=True), nullable=False)`？
    - `liveroom_id`: 是否为 `Column(String(20), nullable=False)`？
    - `liveroom_title`: 是否为 `Column(String(255), nullable=True)`？
    - `liveroom_url`: 是否为 `Column(String(255), nullable=True)`？
    - `video_url`: 是否为 `Column(String(255), nullable=False)`？
    - `video_type`: 是否为 `Column(String(20), nullable=False)`？
    - `status`: 是否为 `Column(String(20), nullable=False, default='pending')`？
    - `progress`: 是否为 `Column(Float, nullable=False, default=0.0)`？
    - `retry_count`: 是否为 `Column(Integer, nullable=False, default=0)`？
    - `last_error`: 是否为 `Column(Text, nullable=True)`？
    - `created_at`: `default` 是否设置为 `func.now()` 或类似功能？
    - `updated_at`: `default` 和 `onupdate` 是否设置为 `func.now()` 或类似功能？
    - `completed_at`: 是否为 `Column(TIMESTAMP, nullable=True)`？
- **[ ] 约束一致性**:
    - `check_status`: 是否有名为 `check_status` 的 `CheckConstraint`，其内容与SQL中的 `status IN (...)` 完全一致？
    - `check_progress_range`: 是否有名为 `check_progress_range` 的 `CheckConstraint`，其内容与SQL中的 `progress >= 0 AND progress <= 1` 完全一致？
    - `video_id_format`: **注意**: SQL中的 `~` 正则匹配在SQLAlchemy CheckConstraint中可能需要特殊处理或确认。请验证是否存在相应的约束。
- **[ ] 索引一致性**:
    - `__table_args__` 中是否定义了名为 `idx_download_tasks_video_id`, `idx_download_tasks_liveroom_id`, `idx_download_tasks_status`, `idx_download_tasks_created_at` 的四个索引？

### 3.2. `download_failures` 表 (`DownloadFailure` 模型)
- **[ ] 表名**: `__tablename__` 是否为 `"download_failures"`？
- **[ ] 字段一致性**: 逐一检查所有字段的类型、长度、`nullable`、`default` 设置。
- **[ ] 外键关系**: `task_id` 字段是否正确定义了 `ForeignKey("download_tasks.id", ondelete="CASCADE")`？
- **[ ] 约束一致性**: 是否有名为 `check_retry_count_range`, `check_resource_type`, `check_failure_type`, `check_failure_status` 的四个 `CheckConstraint`，且内容与SQL完全一致？
- **[ ] 索引一致性**: `__table_args__` 中是否定义了所有必要的索引？

### 3.3. `downloaded_videos` 表 (`DownloadedVideo` 模型)
- **[ ] 表名**: `__tablename__` 是否为 `"downloaded_videos"`？
- **[ ] 字段一致性**: 逐一检查所有字段的类型（特别是`BIGINT` -> `BigInteger`）、`nullable` 设置。
- **[ ] 外键关系**: `download_task_id` 字段是否正确定义了 `ForeignKey("download_tasks.id", ondelete="SET NULL")`？
- **[ ] 约束一致性**:
    - 是否有名为 `check_video_type`, `check_video_status`2个 `CheckConstraint`？
    - `__table_args__` 中是否定义了 `UniqueConstraint('video_id', 'liveroom_id', name='uq_video_id_liveroom_id')`？
- **[ ] 索引一致性**: `__table_args__` 中是否定义了所有必要的索引？

## 四、输出要求 (Output Requirements)

1.  **总结**: 在报告开头，给出一个明确的总体结论。
    - **如果完全一致**: "经详细比对，`app/models/download.py` 文件与设计文档中的数据库定义 **完全一致**。"
    - **如果存在不一致**: "经详细比对，`app/models/download.py` 文件与设计文档存在以下 **X** 处不一致："

2.  **不一致项列表 (仅在存在不一致时提供)**:
    - 以列表形式清晰地列出每一个差异点。
    - 每个差异点应包含以下信息：
        - **位置**: 表名和字段名（或约束名/索引名）。
        - **预期定义 (源自SQL)**: 设计文档中要求的定义。
        - **实际定义 (源自Python)**: `models.py` 文件中的实际代码。
        - **修正建议**: 应该如何修改Python代码以达到一致。

**示例差异报告：**
> - **位置**: `download_tasks` 表, `status` 字段
> - **预期定义 (源自SQL)**: `VARCHAR(20) DEFAULT 'pending'`
> - **实际定义 (源自Python)**: `Column(String(30), default='waiting')`
> - **修正建议**: 应将 `String(30)` 修改为 `String(20)`，并将 `default` 值从 `'waiting'` 修改为 `'pending'`。