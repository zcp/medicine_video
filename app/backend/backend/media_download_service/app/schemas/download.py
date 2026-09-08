from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, HttpUrl, constr, validator, ConfigDict, StringConstraints
from enum import Enum
from pydantic.functional_validators import BeforeValidator
from typing_extensions import Annotated

class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    PARTIAL_COMPLETED = "partial_completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

# 1. 定义一个新的、清晰的枚举类
class DownloadedVideoStatus(str, Enum):
    """已下载视频的状态枚举"""
    COMPLETED = "completed"
    PARTIAL_COMPLETED = "partial_completed"
    FAILED = "failed"

class ResourceTypeEnum(str, Enum):
    M3U8 = "m3u8"
    TS = 'ts'
    MP4 = 'mp4'
    IMAGE = 'image'

class FailureTypeEnum(str, Enum):
    NETWORK_ERROR = 'network_error'
    TIMEOUT = 'timeout'
    INVALID_CONTENT = 'invalid_content'
    STORAGE_ERROR = 'storage_error'
    PERMISSION_ERROR = 'permission_error'

class FailureStatusEnum(str, Enum):
    PENDING = 'pending'
    RETRYING = 'retrying'
    ABANDONED = 'abandoned'


# 直播间ID验证器
def validate_liveroom_id(v: str) -> str:
    if not (5 <= len(v) <= 20):
        raise ValueError('直播间ID长度必须在5-20之间')
    return v

# 视频类型验证器
def validate_video_type(v: str) -> str:
    if v not in ['hls', 'mp4', 'image']:
        raise ValueError('视频类型必须是hls、mp4或image')
    return v

LiveroomId = Annotated[str, BeforeValidator(validate_liveroom_id)]
VideoType = Annotated[str, BeforeValidator(validate_video_type)]

class DownloadTaskBase(BaseModel):
    """下载任务基础模型"""
    #user_id: UUID = Field(..., description="用户ID，关联到用户服务")
    video_id: UUID = Field(..., description="视频ID，格式：UUID")
    liveroom_id: LiveroomId = Field(..., description="直播间ID")
    liveroom_title: Optional[str] = Field(None, max_length=255, description="直播间标题")
    liveroom_url: Optional[HttpUrl] = Field(None, description="直播间URL")
    resource_url: HttpUrl = Field(..., description="视频播放URL或图片URL")
    resource_type: VideoType = Field(..., description="hls, mp4, image")

class DownloadTaskCreate(DownloadTaskBase):
    """创建下载任务请求模型"""
    pass

class DownloadTaskUpdate(BaseModel):
    """更新下载任务请求模型"""
    max_retries: Optional[int] = Field(None, ge=1, le=10, description="最大重试次数")
    priority: Optional[int] = Field(None, ge=0, le=100, description="下载优先级")
    status: Optional[TaskStatus] = Field(None, description="任务状态")

class DownloadFailureBase(BaseModel):
    """下载失败记录基础模型"""
    task_id: UUID = Field(..., description="关联的下载任务ID")
    resource_url: Optional[HttpUrl] = Field(None, description="直播间URL")
    resource_type: ResourceTypeEnum = Field(
        default=ResourceTypeEnum.TS,
        description="资源类型"
    )
    status: FailureStatusEnum = Field(
        default=FailureStatusEnum.PENDING,
        description="失败记录状态"
    )
    expected_path: str = Field(..., max_length=255, description="文件保存路径")
    standard_name: str = Field(..., max_length=255, description="ts/MP4的标准名字，符合指定的存储规范")
    failure_type: str = Field(..., max_length=50, description="错误类型")
    error_message: str = Field(..., max_length=1000, description="错误信息")
    retry_count: int = Field(..., ge=0, description="当前重试次数")

class DownloadFailureCreate(DownloadFailureBase):
    """创建下载失败记录请求模型"""
    pass

class DownloadedVideoBase(BaseModel):
    """已下载视频记录基础模型"""
    video_id: UUID = Field(..., description="vidoeID")
    task_id: UUID = Field(..., description="关联的下载任务ID")
    liveroom_id: str = Field(..., max_length=50,  description="直播间id")
    liveroom_title: str = Field(..., max_length=255,  description="直播间title")
    liveroom_url:str =Field(..., max_length=255,  description="直播间url")
    video_type:str = Field(..., max_length=20, description="视频类型")
    video_url:str =Field(..., max_length=255,  description="视频url")
    format: str = Field(..., max_length=20, description="文件格式")



class DownloadedVideoCreate(DownloadedVideoBase):
    """创建已下载视频记录请求模型"""
    pass

# 响应模型
class DownloadTask(DownloadTaskBase):
    """下载任务响应模型"""
    id: UUID = Field(..., description="任务ID")
    user_id: UUID = Field(..., description="用户ID")
    status: TaskStatus = Field(..., description="任务状态")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    #started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    retry_count: int = Field(..., ge=0, description="当前重试次数")
    last_error: Optional[str] = Field(None, max_length=1000, description="错误信息")

    model_config = ConfigDict(from_attributes=True)

class DownloadFailure(DownloadFailureBase):
    """下载失败记录响应模型"""
    id: UUID = Field(..., description="记录ID")
    created_at: datetime = Field(..., description="创建时间")

    model_config = ConfigDict(from_attributes=True)

class DownloadedVideo(DownloadedVideoBase):
    """已下载视频记录响应模型"""
    id: UUID = Field(..., description="记录ID")
    storage_path: str = Field(..., max_length=255, description="文件保存路径")
    file_size: Optional[int] = Field(..., ge=0, description="文件大小（字节）")
    duration: Optional[int] = Field(None, ge=0, description="视频时长（秒）")
    resolution: Optional[str] = Field(None, max_length=20, description="视频分辨率")
    bitrate: Optional[int] = Field(None, ge=0, description="视频码率（bps）")
    status: DownloadedVideoStatus = Field(..., description="视频的最终下载状态")

    created_at: datetime = Field(..., description="创建时间")

    model_config = ConfigDict(from_attributes=True)

# 列表响应模型
class DownloadTaskList(BaseModel):
    """下载任务列表响应模型"""
    total: int = Field(..., description="总记录数")
    items: List[DownloadTask] = Field(..., description="任务列表")

class DownloadFailureList(BaseModel):
    """下载失败记录列表响应模型"""
    total: int = Field(..., description="总记录数")
    items: List[DownloadFailure] = Field(..., description="失败记录列表")

class DownloadedVideoList(BaseModel):
    """已下载视频记录列表响应模型"""
    total: int = Field(..., description="总记录数")
    items: List[DownloadedVideo] = Field(..., description="视频记录列表")

class DownloadFailureUpdate(BaseModel):
    """更新下载失败记录请求模型"""
    retry_count: Optional[int] = Field(None, ge=0, le=3)
    next_retry_time: Optional[datetime] = None
    status: Optional[TaskStatus] = Field(None, description="任务状态")


class DownloadedVideoUpdate(BaseModel):
    """更新已下载视频记录请求模型"""
    file_size: Optional[int] = Field(None, ge=0)
    duration: Optional[int] = Field(None, ge=0)
    resolution: Optional[str] = Field(None, max_length=20)
    format: Optional[str] = Field(None, max_length=20)
    cover_url: Optional[HttpUrl] = None
    cover_path: Optional[str] = Field(None, max_length=255)
    status: Optional[TaskStatus] = Field(None, description="任务状态")
    download_end_time: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ==================== CSV批量导入相关Schema ====================

class BatchImportResult(BaseModel):
    """批量导入结果Schema"""
    total: int = Field(..., description="总行数（不含表头）")
    success: int = Field(..., description="成功导入的任务数")
    failed: int = Field(..., description="失败的行数")
    skipped: int = Field(..., description="跳过的行数（去重）")
    created_task_ids: List[str] = Field(default_factory=list, description="成功创建的任务ID列表（最多前100个）")
    failed_rows: List[dict] = Field(default_factory=list, description="失败行的详细信息")
    skipped_rows: List[dict] = Field(default_factory=list, description="跳过行的详细信息")
    processing_time: float = Field(..., description="处理耗时（秒）")


# ==================== 爬取与导入相关Schema ====================

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class CrawlOptions(BaseModel):
    """爬虫选项"""
    page_size: Optional[int] = Field(
        default=10, 
        ge=1, 
        le=100, 
        description="每页数据量（默认10）"
    )
    max_pages: Optional[int] = Field(
        None, 
        ge=1, 
        description="最大爬取页数（默认全部）"
    )
    
    model_config = ConfigDict(extra='allow')  # 允许扩展字段


class CrawlAndImportRequest(BaseModel):
    """爬取并导入请求模型"""
    crawler_type: str = Field(
        ..., 
        description="爬虫类型（vzan等，微赞爬虫使用固定API地址）"
    )
    skip_duplicates: bool = Field(
        default=True, 
        description="是否跳过重复任务组合（基于resource_url + liveroom_id + liveroom_title）"
    )
    auto_start: bool = Field(
        default=False, 
        description="导入后是否自动启动任务"
    )
    crawl_options: Optional[CrawlOptions] = Field(
        None, 
        description="爬虫特定参数（page_size, max_pages）"
    )

    # 新增：可选的token和cookie字段
    token: Optional[str] = Field(None, description="VZAN Token（可选，不传则使用配置）")
    cookie: Optional[str] = Field(None, description="VZAN Cookie（可选，不传则使用配置）")

    @field_validator('token')
    def validate_token(cls, v):
        if v is not None:
            # Token格式检查：不能为空字符串，长度限制，不能包含特殊字符
            v = v.strip()
            if not v:
                raise ValueError('token不能为空字符串')
            if len(v) < 10 or len(v) > 500:
                raise ValueError('token长度必须在10-500之间')
            # 检查是否包含明显的注入字符
            if any(char in v for char in ['<', '>', '"', "'", ';', '\n', '\r']):
                raise ValueError('token包含非法字符')
        return v

    @field_validator('cookie')
    def validate_cookie(cls, v):
        if v is not None:
            # Cookie格式检查：不能为空字符串，基本格式验证
            v = v.strip()
            if not v:
                raise ValueError('cookie不能为空字符串')
            if len(v) < 10 or len(v) > 2000:
                raise ValueError('cookie长度必须在10-2000之间')
            # 检查是否包含明显的注入字符
            if any(char in v for char in ['<', '>', '\n', '\r']):
                raise ValueError('cookie包含非法字符')
        return v

    @field_validator('crawler_type')
    def validate_crawler_type(cls, v):
        """验证爬虫类型"""
        from app.crawlers import CrawlerFactory
        supported_types = CrawlerFactory.get_supported_types()
        
        if v.lower() not in supported_types:
            raise ValueError(
                f"不支持的爬虫类型: {v}。"
                f"支持的类型: {', '.join(supported_types)}"
            )
        return v.lower()


class CrawlAndImportResponse(BaseModel):
    """爬取并导入响应模型"""
    crawl_status: str = Field(..., description="爬取状态（success/failed）")
    crawl_rows: int = Field(..., description="爬取到的总行数")
    crawl_file: Optional[str] = Field(None, description="主CSV文件路径")
    incremental_file: Optional[str] = Field(None, description="增量CSV文件路径")
    failed_file: Optional[str] = Field(None, description="失败记录文件路径")
    import_result: Optional[BatchImportResult] = Field(
        None, 
        description="导入结果（仅当爬取成功时存在）"
    )
    error_message: Optional[str] = Field(
        None, 
        description="错误信息（仅当失败时存在）"
    )