from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


class SubscriptionTargetType(str, Enum):
    """订阅目标类型枚举，与模型层保持一致。"""

    ROOM = "room"
    SESSION = "session"


# ==================== 收藏相关 Schema ====================


class FavoriteCreate(BaseModel):
    """创建收藏请求体（用户收藏直播间）"""

    room_id: uuid.UUID = Field(..., description="直播间ID")


class FavoriteItem(BaseModel):
    """单条收藏记录"""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    room_id: uuid.UUID
    is_active: bool = Field(..., description="是否有效：true=已收藏，false=已取消")
    created_at: datetime


class FavoriteListResponse(BaseModel):
    """收藏列表响应（分页）"""

    total: int = Field(..., description="总条数")
    page: int = Field(..., ge=1, description="当前页码")
    size: int = Field(..., ge=1, description="每页条数")
    items: List[FavoriteItem]


# ==================== 观看历史相关 Schema ====================


class WatchEventRequest(BaseModel):
    """记录观看事件的请求体"""

    session_id: uuid.UUID = Field(..., description="直播场次ID")
    progress: Optional[int] = Field(
        None,
        ge=0,
        description="观看进度（秒），可选；为空表示仅记录打开行为",
    )


class WatchHistoryItem(BaseModel):
    """单条观看历史记录"""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    progress: Optional[int] = Field(
        None,
        description="观看进度（秒），可为空",
    )
    watched_at: datetime
    is_latest: bool = Field(
        ...,
        description="是否为该用户该场次的最新观看记录",
    )


class WatchHistoryListResponse(BaseModel):
    """观看历史列表响应（分页）"""

    total: int = Field(..., description="总条数")
    page: int = Field(..., ge=1, description="当前页码")
    size: int = Field(..., ge=1, description="每页条数")
    items: List[WatchHistoryItem]


# ==================== 订阅提醒相关 Schema ====================


class SubscriptionCreate(BaseModel):
    """创建订阅请求体"""

    target_id: uuid.UUID = Field(
        ...,
        description="目标ID，根据target_type指向live_rooms.id或live_sessions.id",
    )
    target_type: SubscriptionTargetType = Field(
        ...,
        description="订阅目标类型：room 或 session",
    )


class SubscriptionItem(BaseModel):
    """单条订阅记录"""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    target_id: uuid.UUID
    target_type: SubscriptionTargetType
    is_active: bool = Field(..., description="是否仍然订阅：true=有效，false=取消")
    created_at: datetime


class SubscriptionListResponse(BaseModel):
    """订阅列表响应（分页）"""

    total: int = Field(..., description="总条数")
    page: int = Field(..., ge=1, description="当前页码")
    size: int = Field(..., ge=1, description="每页条数")
    items: List[SubscriptionItem]

