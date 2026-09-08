"""
LiveCore Service - Pydantic Schemas

This module contains all Pydantic schemas for the LiveCore Service,
used for API data validation and serialization.
"""

import uuid
from datetime import datetime
from typing import Optional, List
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


class LiveSessionStatus(str, Enum):
    """直播会话状态枚举"""
    SCHEDULED = "scheduled"
    LIVE = "live"
    FINISHED = "finished"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


# ==================== LiveRoom Schemas ====================

class LiveRoomBase(BaseModel):
    """直播房间基础Schema"""
    title: str = Field(..., max_length=100, description="房间标题")
    description: Optional[str] = Field(None, description="房间描述")
    cover_url: Optional[str] = Field(None, max_length=255, description="封面图片URL")
    is_private: bool = Field(False, description="是否不公开（unlisted，不进发现列表）")
    record_by_default: bool = Field(True, description="是否默认录制")
    category_id: Optional[uuid.UUID] = Field(None, description="分类ID")


class LiveRoomCreate(LiveRoomBase):
    """创建直播房间请求Schema"""
    parent_room_id: Optional[uuid.UUID] = Field(None, description="父房间ID")


class LiveRoomUpdate(BaseModel):
    """更新直播房间请求Schema"""
    title: Optional[str] = Field(None, max_length=100, description="房间标题")
    description: Optional[str] = Field(None, description="房间描述")
    cover_url: Optional[str] = Field(None, max_length=255, description="封面图片URL")
    is_private: Optional[bool] = Field(None, description="是否为私密房间")
    record_by_default: Optional[bool] = Field(None, description="是否默认录制")
    category_id: Optional[uuid.UUID] = Field(None, description="分类ID")
    parent_room_id: Optional[uuid.UUID] = Field(None, description="父房间ID")


class LiveRoomResponse(LiveRoomBase):
    """直播房间响应Schema"""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., description="房间ID")
    parent_room_id: Optional[uuid.UUID] = Field(None, description="父房间ID")
    user_id: uuid.UUID = Field(..., description="用户ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    stream_key: Optional[str] = Field(None, max_length=255, description="推流密钥（仅在需要时返回）")
    primary_category_name: Optional[str] = Field(None, description="主分类名称（is_primary）")

# ==================== LiveSession Schemas ====================

class LiveSessionBase(BaseModel):
    """直播会话基础Schema"""
    room_id: uuid.UUID = Field(..., description="房间ID")
    status: LiveSessionStatus = Field(..., description="会话状态")
    start_time: datetime = Field(..., description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    video_id: Optional[uuid.UUID] = Field(None, description="视频ID")


class ScheduledSessionCreate(BaseModel):
    """创建计划场次请求Schema"""
    start_time: datetime = Field(..., description="计划开始时间")


class LiveSessionCreate(LiveSessionBase):
    """创建直播会话请求Schema"""
    pass


class LiveSessionUpdate(BaseModel):
    """更新直播会话请求Schema"""
    status: Optional[LiveSessionStatus] = Field(None, description="会话状态")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    video_id: Optional[uuid.UUID] = Field(None, description="视频ID")
    playback_url: Optional[str] = Field(None, max_length=1024, description="回放地址")


class LiveSessionResponse(LiveSessionBase):
    """直播会话响应Schema"""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., description="会话ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    playback_url: Optional[str] = Field(None, description="回放地址")


# ==================== SessionStatistics Schemas ====================

class SessionStatisticsBase(BaseModel):
    """会话统计基础Schema"""
    session_id: uuid.UUID = Field(..., description="会话ID")
    peak_viewer_count: int = Field(0, ge=0, description="峰值观众数")
    total_viewer_count: int = Field(0, ge=0, description="总观众数")
    total_like_count: int = Field(0, ge=0, description="总点赞数")
    total_share_count: int = Field(0, ge=0, description="总分享数")


class SessionStatisticsCreate(SessionStatisticsBase):
    """创建会话统计请求Schema"""
    pass


class SessionStatisticsUpdate(BaseModel):
    """更新会话统计请求Schema"""
    peak_viewer_count: Optional[int] = Field(None, ge=0, description="峰值观众数")
    total_viewer_count: Optional[int] = Field(None, ge=0, description="总观众数")
    total_like_count: Optional[int] = Field(None, ge=0, description="总点赞数")
    total_share_count: Optional[int] = Field(None, ge=0, description="总分享数")


class SessionStatisticsResponse(SessionStatisticsBase):
    """会话统计响应Schema"""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., description="统计记录ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


# ==================== 复合响应Schemas ====================

class LiveSessionWithStatistics(LiveSessionResponse):
    """包含统计信息的直播会话响应Schema"""
    statistics: Optional[SessionStatisticsResponse] = Field(None, description="统计信息")


class LiveRoomWithSessions(LiveRoomResponse):
    """包含会话列表的直播房间响应Schema"""
    live_sessions: List[LiveSessionResponse] = Field(default_factory=list, description="直播会话列表")


class LiveRoomWithSessionsAndStatistics(LiveRoomResponse):
    """包含会话和统计信息的直播房间响应Schema"""
    live_sessions: List[LiveSessionWithStatistics] = Field(default_factory=list, description="直播会话列表")


# ==================== 列表响应Schemas ====================

class LiveRoomListResponse(BaseModel):
    """直播房间列表响应Schema"""
    items: List[LiveRoomResponse] = Field(..., description="房间列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")


class LiveSessionListResponse(BaseModel):
    """直播会话列表响应Schema"""
    items: List[LiveSessionResponse] = Field(..., description="会话列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")


class SessionStatisticsListResponse(BaseModel):
    """会话统计列表响应Schema"""
    items: List[SessionStatisticsResponse] = Field(..., description="统计记录列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")


# ==================== SRS回调Schemas ====================

class SrsOnPublishPayload(BaseModel):
    """SRS on_publish 回调的请求体"""
    action: str
    ip: str
    vhost: str
    app: str
    stream: str = Field(..., description="推流密钥，即 LiveRoom 的 stream_key")


class SrsOnUnpublishPayload(BaseModel):
    """SRS on_unpublish 回调的请求体"""
    action: str
    ip: str
    vhost: str
    app: str
    stream: str = Field(..., description="推流密钥，即 LiveRoom 的 stream_key")


# ==================== Admin Room List（17 管播内容 MVP）====================

class AdminRoomListItem(BaseModel):
    """管理端全站房间列表项（不含 stream_key）"""
    id: uuid.UUID
    title: str
    description: Optional[str] = None
    cover_url: Optional[str] = None
    owner_user_id: uuid.UUID
    is_private: bool
    parent_room_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== Test Room（18 私密测播）====================

class TestRoomEnsureRequest(BaseModel):
    """确保测播间请求（可空 body）"""
    title_suffix: Optional[str] = Field(
        None,
        max_length=40,
        description="标题后缀，默认「连接测试」，最终为 正式标题·后缀",
    )


class TestRoomSummary(BaseModel):
    """测播间摘要（含推流密钥，供主播测试连接）"""
    id: uuid.UUID
    title: str
    is_private: bool
    stream_key: str
    cover_url: Optional[str] = None
    source_room_id: Optional[uuid.UUID] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TestRoomEnsureResponse(BaseModel):
    """POST .../test-room 响应 data"""
    source_room_id: uuid.UUID
    test_room: TestRoomSummary
    created: bool