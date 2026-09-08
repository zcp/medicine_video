"""
用户偏好与通知模块 - Pydantic Schema定义

本模块包含用户偏好设置和通知系统的API数据验证和序列化模型。
"""

import uuid
import datetime

from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from typing import Optional, List, Dict, Any, Literal


# ==================== User Preferences Schemas ====================

class UserPreferencesBase(BaseModel):
    """用户偏好基础Schema"""
    theme_mode: Literal["auto", "light", "dark", "scheduled"] = Field(
        default="auto", 
        description="昼夜模式：auto=跟随系统, light=浅色, dark=深色, scheduled=定时切换"
    )
    theme_scheduled_dark_time: Optional[datetime.time] = Field(
        None, 
        description="定时深色模式开始时间（定时切换时使用）"
    )
    theme_scheduled_light_time: Optional[datetime.time] = Field(
        None, 
        description="定时浅色模式开始时间（定时切换时使用）"
    )
    pinned_categories: Optional[List[uuid.UUID]] = Field(
        None, 
        max_length=5, 
        description="固定的科室ID，最多5个"
    )
    homepage_view_mode: Literal["double", "single"] = Field(
        default="double", 
        description="首页视图模式：double=双列瀑布流, single=单列列表"
    )
    cellular_warning_enabled: Optional[bool] = Field(
        True, 
        description="是否启用流量提醒"
    )
    auto_reduce_quality: Optional[bool] = Field(
        True, 
        description="流量下自动降画质"
    )
    auto_play_on_wifi: Optional[bool] = Field(
        False, 
        description="WiFi下自动播放"
    )
    extra: Optional[Dict[str, Any]] = Field(
        None, 
        description="其他扩展偏好设置"
    )
    
    @field_validator('pinned_categories')
    @classmethod
    def validate_pinned_categories(cls, v: Optional[List[uuid.UUID]]) -> Optional[List[uuid.UUID]]:
        """验证固定科室数量"""
        if v is not None and len(v) > 5:
            raise ValueError('固定科室最多5个')
        return v
    
    @model_validator(mode='after')
    def validate_scheduled_times(self):
        """验证定时切换时间"""
        if self.theme_mode == 'scheduled':
            if not self.theme_scheduled_dark_time or not self.theme_scheduled_light_time:
                raise ValueError('定时切换模式需要设置深色和浅色模式的开始时间')
        return self


class UserPreferencesUpdate(UserPreferencesBase):
    """更新用户偏好请求Schema（部分更新）"""
    theme_mode: Optional[Literal["auto", "light", "dark", "scheduled"]] = None
    homepage_view_mode: Optional[Literal["double", "single"]] = None


class UserPreferencesItem(UserPreferencesBase):
    """用户偏好响应Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime


# ==================== Notifications Schemas ====================

class NotificationBase(BaseModel):
    """通知基础Schema"""
    title: str = Field(
        ..., 
        min_length=1, 
        max_length=255, 
        description="通知标题"
    )
    content: Optional[str] = Field(
        None, 
        description="通知内容"
    )
    notification_type: Literal["system", "subscription", "interaction"] = Field(
        default="system", 
        description="通知类型：system=系统通知, subscription=订阅通知, interaction=互动通知"
    )
    related_id: Optional[uuid.UUID] = Field(
        None, 
        description="关联资源ID"
    )
    related_type: Optional[str] = Field(
        None, 
        max_length=50, 
        description="关联资源类型"
    )


class NotificationItem(NotificationBase):
    """通知响应Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    user_id: uuid.UUID
    is_read: bool
    created_at: datetime.datetime


class NotificationCreateRequest(BaseModel):
    """Admin创建通知请求Schema"""
    user_ids: List[uuid.UUID] = Field(
        ..., 
        description="接收通知的用户ID列表，空列表表示全部用户"
    )
    title: str = Field(..., min_length=1, max_length=255)
    content: Optional[str] = None
    notification_type: Literal["system", "subscription", "interaction"] = Field(default="system")
    related_id: Optional[uuid.UUID] = None
    related_type: Optional[str] = None


class NotificationBatchCreateResponse(BaseModel):
    """批量创建通知响应Schema"""
    total_created: int = Field(..., description="成功创建的通知数量")
    user_ids: List[uuid.UUID] = Field(..., description="接收通知的用户ID列表")


class NotificationUpdateRequest(BaseModel):
    """Admin更新通知请求Schema"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = None


class NotificationBatchDeleteRequest(BaseModel):
    """批量删除通知请求Schema"""
    notification_ids: Optional[List[uuid.UUID]] = Field(
        None, 
        description="通知ID列表"
    )
    delete_before: Optional[datetime.datetime] = Field(
        None, 
        description="删除此日期之前的通知"
    )
    notification_type: Optional[Literal["system", "subscription", "interaction"]] = None
    is_read: Optional[bool] = None

    # 第167-171行：修改验证逻辑
    @model_validator(mode='after')
    def check_params(self):
        """验证至少提供一个删除条件"""
        if not self.notification_ids and not self.delete_before and not self.notification_type:
            raise ValueError("必须提供 notification_ids、delete_before 或 notification_type 参数之一")
        return self

class NotificationListResponse(BaseModel):
    """通知列表响应Schema"""
    items: List[NotificationItem] = Field(..., description="通知列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    has_more: bool = Field(..., description="是否有更多数据")
