"""
LiveCore Service - Session Import Schemas

This module contains Pydantic schemas for the session import feature.
"""

from pydantic import BaseModel, Field, validator
from uuid import UUID
from datetime import datetime
from typing import Optional

class SessionImportCreate(BaseModel):
    """导入创建会话的请求体"""
    start_time: datetime = Field(..., description="会话开始时间（必填）")
    end_time: Optional[datetime] = Field(None, description="会话结束时间（建议必填）")
    status: str = Field(..., description="会话状态，限制为 'finished' 或 'ready'")
    playback_url: str = Field(..., max_length=1024, description="回放地址（必填）")
    title: Optional[str] = Field(None, max_length=100, description="会话标题（可选）")
    description: Optional[str] = Field(None, description="会话描述（可选）")
    
    @validator('status')
    def validate_status(cls, v):
        if v not in ['finished', 'ready', 'live']:
            raise ValueError("导入会话的 status 只能为 'finished', 'live', 或 'ready'")
        return v
    
    @validator('playback_url')
    def validate_playback_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError("playback_url 必须以 http:// 或 https:// 开头")
        return v

class SessionImportResponse(BaseModel):
    """导入创建会话的响应体"""
    id: UUID
    room_id: UUID
    status: str
    start_time: datetime
    end_time: Optional[datetime]
    video_id: Optional[UUID]
    playback_url: str
    created_at: datetime
    updated_at: datetime
