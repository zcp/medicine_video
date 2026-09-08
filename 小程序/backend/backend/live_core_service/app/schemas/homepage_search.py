"""
首页与搜索模块的 Pydantic Schemas

本模块包含首页与搜索模块所需的所有 Pydantic Schema 模型，用于API数据验证和序列化。
"""
import uuid
import datetime
import re
from typing import Optional, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict, field_validator

# 导入通用分页Schema
from app.schemas.content_management import PaginatedData


# ==================== image_url 安全校验 ====================

# 需要拒绝的模式（本地临时路径）
REJECTED_IMAGE_URL_PATTERNS = [
    re.compile(r'^https?://tmp/', re.IGNORECASE),
    re.compile(r'^file://', re.IGNORECASE),
    re.compile(r'^wxfile://', re.IGNORECASE),
]

# 合法的 image_url 白名单模式
VALID_IMAGE_URL_PATTERN = re.compile(
    r'^('
    r'/media/featured/[a-f0-9\-]+\.(jpg|jpeg|png|webp)'  # 上传后的服务器路径
    r'|/static/images/banners/.*'                           # 占位SVG
    r'|https?://[^\s]+'                                     # 外部CDN URL
    r')$',
    re.IGNORECASE
)


def validate_image_url(v: str) -> str:
    """
    校验 image_url 格式，拒绝本地临时路径。

    校验逻辑：
    1. 匹配 REJECTED_IMAGE_URL_PATTERNS → 拒绝
    2. 不匹配 VALID_IMAGE_URL_PATTERN → 拒绝
    3. 通过 → 正常返回
    """
    v = v.strip()
    for pattern in REJECTED_IMAGE_URL_PATTERNS:
        if pattern.match(v):
            raise ValueError(
                "image_url 不接受本地临时路径，请先通过图片上传接口获取服务器URL"
            )
    if not VALID_IMAGE_URL_PATTERN.match(v):
        raise ValueError(
            "image_url 格式不合法，需为 /media/featured/ 开头的服务器路径或合法的外部URL"
        )
    return v


# ==================== 焦点图管理 Schemas ====================

class FeaturedContentBase(BaseModel):
    """焦点图基础Schema"""
    title: str = Field(..., min_length=1, max_length=255, description="焦点图标题")
    subtitle: Optional[str] = Field(None, max_length=512, description="焦点图副标题")
    image_url: str = Field(..., max_length=512, description="焦点图图片URL")
    target_type: Optional[str] = Field(None, max_length=50, description="目标类型")
    target_id: Optional[uuid.UUID] = Field(None, description="目标资源ID")
    target_url: Optional[str] = Field(None, max_length=512, description="外部链接")
    
    @field_validator('image_url')
    @classmethod
    def validate_image_url_field(cls, v: str) -> str:
        """校验 image_url 格式（白名单+黑名单）"""
        return validate_image_url(v)

    @field_validator('target_url')
    @classmethod
    def validate_target_url(cls, v: Optional[str]) -> Optional[str]:
        """验证 target_url 格式"""
        if v is not None:
            v = v.strip()
            if not re.match(r'^https?://', v) and not v.startswith('/'):
                raise ValueError('URL必须以http://、https://或/开头')
        return v


class FeaturedContentCreate(FeaturedContentBase):
    """创建焦点图请求Schema"""
    sort_order: Optional[int] = Field(0, ge=0, description="排序权重")
    is_active: Optional[bool] = Field(True, description="是否启用")
    start_at: Optional[datetime.datetime] = Field(None, description="上线时间")
    end_at: Optional[datetime.datetime] = Field(None, description="下线时间")


class FeaturedContentUpdate(BaseModel):
    """更新焦点图请求Schema（部分更新）"""
    model_config = ConfigDict(from_attributes=True)
    
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="焦点图标题")
    subtitle: Optional[str] = Field(None, max_length=512, description="焦点图副标题")
    image_url: Optional[str] = Field(None, max_length=512, description="焦点图图片URL")
    target_type: Optional[str] = Field(None, max_length=50, description="目标类型")
    target_id: Optional[uuid.UUID] = Field(None, description="目标资源ID")
    target_url: Optional[str] = Field(None, max_length=512, description="外部链接")
    sort_order: Optional[int] = Field(None, ge=0, description="排序权重")
    is_active: Optional[bool] = Field(None, description="是否启用")
    start_at: Optional[datetime.datetime] = Field(None, description="上线时间")
    end_at: Optional[datetime.datetime] = Field(None, description="下线时间")
    
    @field_validator('image_url')
    @classmethod
    def validate_image_url_field(cls, v: Optional[str]) -> Optional[str]:
        """校验 image_url 格式（白名单+黑名单）"""
        if v is not None:
            return validate_image_url(v)
        return v

    @field_validator('target_url')
    @classmethod
    def validate_target_url(cls, v: Optional[str]) -> Optional[str]:
        """验证 target_url 格式"""
        if v is not None:
            v = v.strip()
            if not re.match(r'^https?://', v) and not v.startswith('/'):
                raise ValueError('URL必须以http://、https://或/开头')
        return v


class FeaturedContentItem(FeaturedContentBase):
    """焦点图响应Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    sort_order: int
    is_active: bool
    start_at: Optional[datetime.datetime] = None
    end_at: Optional[datetime.datetime] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime


# ==================== 首页API Schemas ====================

class LiveStatusEnum(str, Enum):
    """直播状态枚举"""
    LIVE = 'live'
    SCHEDULED = 'scheduled'
    REPLAY = 'replay'


class HomepageHostInfo(BaseModel):
    """首页主讲人信息Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    expert_id: Optional[uuid.UUID] = None
    user_id: Optional[uuid.UUID] = None
    name: str
    title: Optional[str] = None
    hospital: Optional[str] = None
    avatar_url: Optional[str] = None


class HomepageStatusData(BaseModel):
    """首页状态数据Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    viewer_count: Optional[int] = None  # 正在直播的观看人数
    start_time: Optional[datetime.datetime] = None  # 计划开始时间
    duration_seconds: Optional[int] = None  # 回放时长（秒）
    play_count: Optional[int] = None  # 回放播放次数


class HomepageRoomItem(BaseModel):
    """首页直播间信息Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    title: str
    cover_url: Optional[str] = None
    summary: Optional[str] = None
    live_status: LiveStatusEnum
    host: Optional[HomepageHostInfo] = None
    status_data: HomepageStatusData
    heat: Optional[int] = None
    primary_category_name: Optional[str] = None


class HomepageRoomsResponse(BaseModel):
    """首页直播间列表响应Schema"""
    code: int = 200
    message: str = "success"
    data: PaginatedData[HomepageRoomItem]
    timestamp: datetime.datetime


# ==================== 搜索API Schemas ====================

class SearchResultType(str, Enum):
    """搜索结果类型枚举"""
    ROOM = 'room'
    EXPERT = 'expert'
    TOPIC = 'topic'
    BRAND = 'brand'


class SearchResultItem(BaseModel):
    """搜索结果项Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    type: SearchResultType
    id: uuid.UUID
    title: str
    summary: Optional[str] = None
    cover_url: Optional[str] = None
    match_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="匹配分数（0-1）")
    highlight: Optional[str] = Field(None, description="高亮后的文本片段")
    metadata: Optional[Dict[str, Any]] = Field(None, description="类型特定的元数据")


class SearchResponse(BaseModel):
    """搜索响应Schema"""
    code: int = 200
    message: str = "success"
    data: PaginatedData[SearchResultItem]
    timestamp: datetime.datetime
